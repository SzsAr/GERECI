const API_BASE = 'http://localhost:8000';

const api = {
  async request(path, { method = 'GET', headers = {}, body = null } = {}) {
    const token = localStorage.getItem('token');

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
      try {
        const errJson = text ? JSON.parse(text) : {};
        const message = errJson.detail || errJson.message || text || 'Request failed';
        
        // Si el usuario está inactivo, redirigir al login
        if (res.status === 403 && message.includes('Usuario inactivo')) {
          localStorage.removeItem('token');
          window.location.href = './index.html';
        }
        
        throw new Error(message);
      } catch (e) {
        // Si no es JSON, usar texto crudo
        if (e instanceof Error && e.message.includes('Usuario inactivo')) {
          localStorage.removeItem('token');
          window.location.href = './index.html';
        }
        throw new Error(text || 'Request failed');
      }
    }

    const text = await res.text();
    try {
      return text ? JSON.parse(text) : null;
    } catch (e) {
      return text;
    }
  },
};
