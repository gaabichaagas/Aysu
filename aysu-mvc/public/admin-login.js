const form = document.getElementById('adminLoginForm');
const message = document.getElementById('adminLoginMessage');
const button = form.querySelector('button[type="submit"]');
let csrf = '';

async function loadSession() {
  const response = await fetch('/api/state');
  if (!response.ok) throw new Error('Não foi possível verificar a sessão. Recarregue a página.');
  const state = await response.json();
  csrf = state.csrf;
  if (state.user?.admin) {
    location.replace('admin.html');
    return;
  }
  message.textContent = '';
  button.disabled = false;
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  button.disabled = true;
  message.textContent = 'Verificando acesso…';
  try {
    const response = await fetch('/api/admin/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf},
      body: JSON.stringify(Object.fromEntries(new FormData(form)))
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível entrar.');
    location.replace('admin.html');
  } catch (error) {
    message.textContent = error.message;
    form.elements.password.value = '';
    button.disabled = false;
  }
});

loadSession().catch(error => { message.textContent = error.message; });
