document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('login-form');
  const errorBox = document.getElementById('login-error');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorBox.classList.add('d-none');

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();

    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const data = await api.request('/auth/token', {
        method: 'POST',
        body: formData,
      });
      localStorage.setItem('token', data.access_token);
      window.location.href = './dashboard.html';
    } catch (err) {
      errorBox.textContent = err.message || 'Login failed';
      errorBox.classList.remove('d-none');
    }
  });
});
