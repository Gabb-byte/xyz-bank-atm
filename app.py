from pathlib import Path
import math
import os
import shutil
import subprocess
import threading

from flask import Flask, jsonify, render_template, request, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "digital-atm-classroom-demo")

BASE_DIR = Path(__file__).resolve().parent
ENGINE = None
ENGINE_LOCK = threading.Lock()


def start_c_engine():
    """Compile the C engine once, then keep it alive to hold ATM balances."""
    global ENGINE
    if ENGINE is not None and ENGINE.poll() is None:
        return

    executable = BASE_DIR / ("atm_engine.exe" if os.name == "nt" else "atm_engine")
    compiler_candidates = []
    configured_compiler = os.environ.get("ATM_GCC")
    if configured_compiler:
        compiler_candidates.append(configured_compiler)
    if os.name == "nt":
        # Prefer common MinGW installs outside user-profile paths with spaces.
        compiler_candidates.extend([r"C:\MinGW\bin\gcc.exe", r"C:\msys64\mingw64\bin\gcc.exe"])
    path_compiler = shutil.which("gcc") or shutil.which("cc")
    if path_compiler:
        compiler_candidates.append(path_compiler)

    compile_errors = []
    for compiler in dict.fromkeys(compiler_candidates):
        if not Path(compiler).is_file():
            continue
        try:
            result = subprocess.run(
                [compiler, str(BASE_DIR / "atm_engine.c"), "-o", str(executable)],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError) as error:
            compile_errors.append(f"{compiler}: {error}")
            continue
        if result.returncode == 0:
            break
        compile_errors.append(f"{compiler}: {result.stderr[:300]}")
    else:
        detail = "\n".join(compile_errors) or "No GCC compiler was found."
        raise RuntimeError(
            "Could not compile atm_engine.c. Install MinGW GCC in a path without spaces "
            "(for example C:\\MinGW), or set ATM_GCC to its gcc.exe path. Details: " + detail
        )

    ENGINE = subprocess.Popen(
        [str(executable)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )


def ask_c_engine(command):
    """Send one command to C and return its single-line reply."""
    with ENGINE_LOCK:
        start_c_engine()
        ENGINE.stdin.write(command + "\n")
        ENGINE.stdin.flush()
        reply = ENGINE.stdout.readline().strip()
    if not reply:
        raise RuntimeError("The C ATM engine stopped unexpectedly. Restart the Flask server.")
    if reply.startswith("ERR|"):
        raise ValueError(reply[4:])
    if not reply.startswith("OK|"):
        raise RuntimeError("The C ATM engine returned an unexpected response.")
    return reply[3:].split("|")


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    account_number = str(data.get("account", "")).strip()
    pin = str(data.get("pin", "")).strip()
    if not account_number.isdigit() or not pin.isdigit() or len(pin) != 4:
        return jsonify({"ok": False, "message": "Enter an account number and a 4-digit PIN."}), 400
    try:
        account, balance_value = ask_c_engine(f"LOGIN {account_number} {pin}")
    except ValueError as error:
        status = 429 if "Too many" in str(error) else 401
        return jsonify({"ok": False, "message": str(error)}), status
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        app.logger.exception("Could not communicate with the C ATM engine")
        return jsonify({"ok": False, "message": str(error)}), 500
    session["account"] = account
    return jsonify({"ok": True, "account": account, "balance": float(balance_value)})


@app.post("/api/logout")
def logout():
    if session.get("account"):
        try:
            ask_c_engine("LOGOUT")
        except (OSError, RuntimeError, subprocess.SubprocessError):
            app.logger.exception("Could not log out from the C ATM engine")
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/balance")
def balance():
    if not session.get("account"):
        return jsonify({"ok": False, "message": "Please sign in again."}), 401
    try:
        values = ask_c_engine("BALANCE")
        return jsonify({"ok": True, "balance": float(values[0])})
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        session.clear()
        return jsonify({"ok": False, "message": str(error)}), 401


@app.post("/api/transaction")
def transaction():
    if not session.get("account"):
        return jsonify({"ok": False, "message": "Please sign in again."}), 401
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        amount = 0.0
    if not math.isfinite(amount) or amount <= 0:
        return jsonify({"ok": False, "message": "Enter an amount greater than zero."}), 400
    if action not in ("deposit", "withdraw"):
        return jsonify({"ok": False, "message": "Choose a valid transaction."}), 400
    try:
        values = ask_c_engine(f"{action.upper()} {amount:.2f}")
        message = f"${amount:,.2f} {'deposited' if action == 'deposit' else 'withdrawn'} successfully."
        return jsonify({"ok": True, "balance": float(values[0]), "message": message})
    except ValueError as error:
        return jsonify({"ok": False, "message": str(error)}), 400
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        app.logger.exception("Could not communicate with the C ATM engine")
        return jsonify({"ok": False, "message": str(error)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
