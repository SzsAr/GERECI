const API_BASE = 'http://localhost:8000';

const api = {
  async request(path, { method = 'GET', headers = {}, body = null } = {}) {
    const token = localStorage.getItem('token');
    const isLoginRequest = path === '/auth/token';

    // Configurar headers básicos
    const finalHeaders = { ...headers };
    if (token) finalHeaders['Authorization'] = `Bearer ${token}`;

    let payload = null;

    // Si es FormData, no establecer Content-Type manualmente
    if (body instanceof FormData) {
      payload = body;
    } else if (body !== null && body !== undefined) {
      finalHeaders['Content-Type'] = 'application/json';
      payload = JSON.stringify(body);
    }

    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers: finalHeaders,
      body: payload,
    });

    if (!res.ok) {
      const text = await res.text();
      let message = text || 'Request failed';

      try {
        const errJson = text ? JSON.parse(text) : {};
        message = errJson.detail || errJson.message || text || 'Request failed';
      } catch (_e) {
        // Si no es JSON, se conserva el texto crudo.
      }

      // Si token expirado o inválido (401), redirigir excepto durante login.
      if (res.status === 401 && !isLoginRequest) {
        localStorage.removeItem('token');
        window.location.href = './index.html';
        return;
      }

      // Si el usuario está inactivo (403), redirigir excepto durante login.
      if (res.status === 403 && message.includes('Usuario inactivo') && !isLoginRequest) {
        localStorage.removeItem('token');
        window.location.href = './index.html';
        return;
      }

      throw new Error(message);
    }

    const text = await res.text();
    try {
      return text ? JSON.parse(text) : null;
    } catch (e) {
      return text;
    }
  },
};
