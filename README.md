# Digital ATM — Flask website connected to C

This folder contains the browser interface and its Flask bridge to the C ATM engine. Flask receives requests from the webpage and passes login and transaction commands to `atm_engine.c`. The C program owns the account arrays, validates PINs and transactions, and retains balances while it is running.

## Run it on Windows

You need Python and GCC (for example, MinGW-w64 GCC) available in PowerShell. From this folder:

```powershell
python -m pip install -r requirements.txt
python app.py
```

The first login request compiles `atm_engine.c` automatically. Open `http://127.0.0.1:5000`. Demo accounts:

| Account | PIN | Starting balance |
| --- | ---: | ---: |
| 10010001 | 1234 | $2,500.00 |
| 10010002 | 2468 | $5,000.00 |
| 10010003 | 1357 | $1,250.50 |

## How the connection works

1. The browser sends a login or transaction request to a Flask route in `app.py`.
2. Flask writes a short command to the running C program's input, such as `LOGIN 10010001 1234` or `DEPOSIT 100.00`.
3. C processes the command, updates its arrays, and prints a one-line response.
4. Flask reads that response and sends the result back to the webpage as JSON.

The C program stays open behind Flask so its account balances remain in memory between website requests. Restarting the Flask server resets balances. The C engine allows three failed PIN attempts before login locks until the server is restarted.

## Files

- `templates/index.html`, `static/style.css`, and `static/app.js` make up the interactive web interface.
- `app.py` serves the site and passes requests to C.
- `atm_engine.c` is the C program that authenticates accounts and performs transactions.
- `../digital_atm.c` is the original standalone C console version.

## Publish a classroom demo on Render

The included `Dockerfile` installs GCC and runs Flask with one Gunicorn worker. The `render.yaml` file asks Render to create a Docker web service and generate a Flask secret key.

1. Create a GitHub repository and upload the **contents of this `atm_web` folder** to its root. Include `Dockerfile`, `render.yaml`, and `atm_engine.c`.
2. In Render, choose **New → Blueprint** and connect that GitHub repository. Render will read `render.yaml` and build the service.
3. When deployment finishes, open the `onrender.com` URL shown in the Render dashboard.

Render supports deploying Docker services from a `Dockerfile`, and each web service gets an `onrender.com` address. See [Render's Docker deployment guide](https://render.com/docs/docker) and [Blueprint reference](https://render.com/docs/blueprint-spec).

This is a classroom demo, **not a production banking system**. The three sample accounts are public demo credentials. Visitors share one C engine and its in-memory balances, so this is suitable for showing the project, not for private or real banking. The balances reset when the service restarts or redeploys. Flask is Python, but the ATM account data, authentication, and balance calculations for the website run in C. The C engine uses a small text command protocol, `sscanf`, and a long-running process, which are extra integration topics beyond the original Units 1–4 restrictions.
