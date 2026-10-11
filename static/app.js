const loginView = document.getElementById('loginView');
const dashboardView = document.getElementById('dashboardView');
const modal = document.getElementById('transactionModal');
const activity = [];
let selectedAction = 'deposit';

function money(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
}

function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.add('show');
  window.setTimeout(() => toast.classList.remove('show'), 2600);
}

function setBalance(value) {
  document.getElementById('balanceAmount').textContent = money(value);
}

async function postJson(url, data) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.message || 'Something went wrong.');
  return result;
}

document.getElementById('loginForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const error = document.getElementById('loginError');
  error.textContent = '';
  try {
    const result = await postJson('/api/login', {
      account: document.getElementById('account').value.trim(),
      pin: document.getElementById('pin').value.trim()
    });
    document.getElementById('accountLabel').textContent = `•••• ${result.account.slice(-4)}`;
    const hour = new Date().getHours();
    document.getElementById('greeting').textContent = `${hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'}`;
    setBalance(result.balance);
    loginView.classList.add('hidden');
    dashboardView.classList.remove('hidden');
  } catch (err) {
    error.textContent = err.message;
  }
});

document.querySelectorAll('[data-action]').forEach((button) => {
  button.addEventListener('click', () => {
    selectedAction = button.dataset.action;
    const deposit = selectedAction === 'deposit';
    document.getElementById('modalIcon').textContent = deposit ? '＋' : '－';
    document.getElementById('modalTitle').textContent = deposit ? 'Deposit cash' : 'Withdraw cash';
    document.getElementById('submitTransaction').innerHTML = `${deposit ? 'Confirm deposit' : 'Confirm withdrawal'} <span>→</span>`;
    document.getElementById('transactionError').textContent = '';
    document.getElementById('amount').value = '';
    modal.classList.remove('hidden');
    document.getElementById('amount').focus();
  });
});

document.querySelectorAll('[data-close="true"]').forEach((button) => {
  button.addEventListener('click', () => modal.classList.add('hidden'));
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') modal.classList.add('hidden');
});

document.getElementById('transactionForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const amount = Number(document.getElementById('amount').value);
  try {
    const result = await postJson('/api/transaction', { action: selectedAction, amount });
    setBalance(result.balance);
    activity.unshift({ action: selectedAction, amount, balance: result.balance, time: new Date() });
    renderActivity();
    modal.classList.add('hidden');
    showToast(result.message);
  } catch (err) {
    document.getElementById('transactionError').textContent = err.message;
  }
});

function renderActivity() {
  document.getElementById('emptyActivity').classList.toggle('hidden', activity.length > 0);
  document.getElementById('activityList').innerHTML = activity.map((item) => {
    const deposit = item.action === 'deposit';
    const time = item.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return `<div class="transaction-row"><span class="action-icon ${deposit ? 'green' : 'blue'}">${deposit ? '＋' : '－'}</span><span><b>${deposit ? 'Cash deposit' : 'Cash withdrawal'}</b><small>Today · ${time}</small></span><strong class="${deposit ? 'positive' : 'negative'}">${deposit ? '+' : '−'}${money(item.amount)}</strong></div>`;
  }).join('');
}

function updateClock() {
  document.getElementById('clock').textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
updateClock();
window.setInterval(updateClock, 30000);

document.getElementById('logoutButton').addEventListener('click', async () => {
  await postJson('/api/logout', {});
  activity.length = 0;
  renderActivity();
  document.getElementById('loginForm').reset();
  loginView.classList.remove('hidden');
  dashboardView.classList.add('hidden');
});
