// Simple guard: redirect to login if no token
(function guardAuth() {
  const token = localStorage.getItem('token');
  if (!token) {
    window.location.href = './index.html';
  }
})();

const state = {
  user: null,
};

async function loadProfile() {
  try {
    // No endpoint de perfil específico, reutilizamos /users/me si existiera
    // Por ahora solo mostrar nombre placeholder si no hay endpoint
    const token = localStorage.getItem('token');
    if (!token) return;
    document.getElementById('user-name').textContent = 'Sesión activa';
  } catch (err) {
    console.error(err);
  }
}

async function loadKPIs() {
  // TODO: reemplazar por endpoints reales
  document.getElementById('kpi-documentos').textContent = '--';
  document.getElementById('kpi-firmas').textContent = '--';
  document.getElementById('kpi-tareas').textContent = '--';
  document.getElementById('kpi-observaciones').textContent = '--';
}

function bindLogout() {
  const btn = document.getElementById('btn-logout');
  if (!btn) return; // Navbar might not be rendered yet
  if (btn.dataset.boundLogout === 'true') return; // avoid duplicate binding
  btn.addEventListener('click', () => {
    localStorage.removeItem('token');
    window.location.href = './index.html';
  });
  btn.dataset.boundLogout = 'true';
}

window.addEventListener('DOMContentLoaded', () => {
  bindLogout();
  loadProfile();
  loadKPIs();
});

// Bind logout once navbar is rendered by layout.js
document.addEventListener('layout:navbarReady', bindLogout);
