// Simple guard: redirect to login if no token
(function guardAuth() {
  const token = localStorage.getItem('token');
  if (!token) {
    window.location.href = './index.html';
  }
})();

const PENDING_SIGNATURE_ACTIONS = new Set(['REVISION_JURIDICA', 'REVISION_GERENCIA']);
const DASHBOARD_STATE_ORDER = [
  'BORRADOR',
  'EN_REVISION_JURIDICA',
  'EN_REVISION_GERENCIAL',
  'APROBADO_JURIDICA',
  'APROBADO_GERENCIA',
  'FIRMADO',
  'PENDIENTE_FINALIZACION',
  'DEVUELTO_JURIDICA',
  'DEVUELTO_GERENCIA',
  'FINALIZADO'
];

const state = {
  user: null,
  documents: [],
  pendingTasks: [],
  observationsCount: 0,
  observationsSource: 'api'
};

function getSessionUser() {
  try {
    const raw = localStorage.getItem('user');
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (err) {
    console.warn('No se pudo leer la sesion de usuario', err);
    return null;
  }
}

function escapeHtml(value) {
  return (value || '').toString()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatDate(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString('es-CO', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function toStateLabel(value) {
  return (value || '').replace(/_/g, ' ');
}

function getStateBadgeClass(estado) {
  return `estado-${(estado || '').toLowerCase().replace(/_/g, '-')}`;
}

function getStateProgressClass(estado) {
  const map = {
    BORRADOR: 'bg-secondary',
    EN_REVISION_JURIDICA: 'bg-warning',
    EN_REVISION_GERENCIAL: 'bg-warning',
    APROBADO_JURIDICA: 'bg-info',
    APROBADO_GERENCIA: 'bg-info',
    FIRMADO: 'bg-success',
    PENDIENTE_FINALIZACION: 'bg-orange',
    DEVUELTO_JURIDICA: 'bg-danger',
    DEVUELTO_GERENCIA: 'bg-danger',
    FINALIZADO: 'bg-dark'
  };

  return map[(estado || '').toUpperCase()] || 'bg-primary';
}

function determinePendingAction(doc, user) {
  if (!doc || !user) return null;

  const idRol = Number(user.id_rol);
  const userId = Number(user.id_usuario);
  const creatorId = Number(doc.usuario_genera);
  const isCreator = userId === creatorId;

  const isSuperAdmin = idRol === 1;
  const isGerencia = idRol === 2;
  const isJuridica = idRol === 3;
  const isUnidad = idRol === 4;

  const estado = (doc.estado || '').toUpperCase();

  if (estado === 'BORRADOR') {
    if (isSuperAdmin || (isUnidad && isCreator)) {
      return {
        accion_codigo: 'ENVIAR_REVISION',
        accion_label: 'Enviar a revision'
      };
    }
    return null;
  }

  if (estado === 'EN_REVISION_JURIDICA') {
    if (isSuperAdmin || isJuridica) {
      return {
        accion_codigo: 'REVISION_JURIDICA',
        accion_label: 'Revision juridica'
      };
    }
    return null;
  }

  if (estado === 'EN_REVISION_GERENCIAL') {
    if (isSuperAdmin || isGerencia) {
      return {
        accion_codigo: 'REVISION_GERENCIA',
        accion_label: 'Revision gerencia'
      };
    }
    return null;
  }

  if (estado === 'DEVUELTO_JURIDICA' || estado === 'DEVUELTO_GERENCIA') {
    if (isSuperAdmin || (isUnidad && isCreator)) {
      return {
        accion_codigo: 'CORREGIR_REENVIAR',
        accion_label: 'Corregir y reenviar'
      };
    }
    return null;
  }

  if (estado === 'FIRMADO' || estado === 'PENDIENTE_FINALIZACION') {
    if (isCreator) {
      return {
        accion_codigo: 'FINALIZAR',
        accion_label: 'Finalizar'
      };
    }
    return null;
  }

  return null;
}

function buildPendingTasks(documents, user) {
  return (documents || [])
    .map((doc) => {
      const action = determinePendingAction(doc, user);
      if (!action) return null;
      return { ...doc, ...action };
    })
    .filter(Boolean);
}

async function loadObservationsCount(user, documents) {
  if (!user || !user.id_usuario) {
    return { count: 0, source: 'fallback' };
  }

  try {
    const response = await api.request(`/observaciones/usuario/${user.id_usuario}`);
    const count = Array.isArray(response) ? response.length : 0;
    return { count, source: 'api' };
  } catch (err) {
    // Fallback: devoluciones del creador actual (se interpretan como observaciones activas)
    const userId = Number(user.id_usuario);
    const fallbackCount = (documents || []).filter((doc) => {
      const estado = (doc.estado || '').toUpperCase();
      return Number(doc.usuario_genera) === userId && (
        estado === 'DEVUELTO_JURIDICA' || estado === 'DEVUELTO_GERENCIA'
      );
    }).length;

    return { count: fallbackCount, source: 'fallback' };
  }
}

function renderKpis() {
  const docs = state.documents;
  const pendingTasks = state.pendingTasks;

  const pendingSignatures = pendingTasks.filter((task) => PENDING_SIGNATURE_ACTIONS.has(task.accion_codigo)).length;

  document.getElementById('kpi-documentos').textContent = String(docs.length);
  document.getElementById('kpi-firmas').textContent = String(pendingSignatures);
  document.getElementById('kpi-tareas').textContent = String(pendingTasks.length);
  document.getElementById('kpi-observaciones').textContent = String(state.observationsCount);

  const subtitle = document.getElementById('dashboard-subtitle');
  const now = new Date().toLocaleString('es-CO', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });

  const sourceNote = state.observationsSource === 'fallback'
    ? 'observaciones estimadas por devoluciones'
    : 'observaciones registradas';

  subtitle.textContent = `Actualizado: ${now} | ${pendingTasks.length} tareas pendientes | ${sourceNote}.`;
}

function renderStateBreakdown() {
  const docs = state.documents;
  const container = document.getElementById('estado-kpis-list');
  const totalLabel = document.getElementById('kpi-total-estados');
  const total = docs.length;

  totalLabel.textContent = `${total} documentos`;

  if (!total) {
    container.innerHTML = '<p class="small text-muted mb-0">Sin documentos para mostrar.</p>';
    return;
  }

  const counts = docs.reduce((acc, doc) => {
    const key = (doc.estado || 'SIN_ESTADO').toUpperCase();
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

  const states = Object.keys(counts).sort((a, b) => {
    const posA = DASHBOARD_STATE_ORDER.indexOf(a);
    const posB = DASHBOARD_STATE_ORDER.indexOf(b);
    const safeA = posA === -1 ? 999 : posA;
    const safeB = posB === -1 ? 999 : posB;
    return safeA - safeB;
  });

  container.innerHTML = states.map((estado) => {
    const count = counts[estado];
    const pct = Math.round((count / total) * 100);

    return `
      <div class="dashboard-state-item">
        <div class="d-flex justify-content-between align-items-center mb-1">
          <span class="badge estado-badge ${getStateBadgeClass(estado)}">${toStateLabel(estado)}</span>
          <span class="small fw-semibold">${count}</span>
        </div>
        <div class="progress dashboard-progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${pct}">
          <div class="progress-bar ${getStateProgressClass(estado)}" style="width:${pct}%">${pct}%</div>
        </div>
      </div>
    `;
  }).join('');
}

function renderFocusSummary() {
  const focusSummary = document.getElementById('focus-summary');
  const focusList = document.getElementById('focus-list');

  const byAction = state.pendingTasks.reduce((acc, task) => {
    acc[task.accion_codigo] = (acc[task.accion_codigo] || 0) + 1;
    return acc;
  }, {});

  if (!state.pendingTasks.length) {
    focusSummary.textContent = 'No tienes tareas pendientes por rol.';
    focusList.innerHTML = '<li class="list-group-item px-0 py-2 text-muted small">Todo al dia por ahora.</li>';
    return;
  }

  focusSummary.textContent = `Tienes ${state.pendingTasks.length} tareas pendientes para gestionar.`;

  const preferredOrder = [
    ['REVISION_JURIDICA', 'Revision juridica'],
    ['REVISION_GERENCIA', 'Revision gerencia'],
    ['CORREGIR_REENVIAR', 'Corregir y reenviar'],
    ['FINALIZAR', 'Finalizar documentos'],
    ['ENVIAR_REVISION', 'Enviar a revision']
  ];

  const items = preferredOrder
    .filter(([code]) => byAction[code])
    .map(([code, label]) => `
      <li class="list-group-item px-0 py-2 d-flex justify-content-between align-items-center">
        <span class="small">${label}</span>
        <span class="badge text-bg-primary">${byAction[code]}</span>
      </li>
    `)
    .join('');

  focusList.innerHTML = items || '<li class="list-group-item px-0 py-2 text-muted small">No hay acciones priorizadas.</li>';
}

function renderLatestDocuments() {
  const tbody = document.getElementById('tabla-documentos');
  const docs = state.documents.slice(0, 8);

  if (!docs.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted small">Sin documentos para mostrar.</td></tr>';
    return;
  }

  tbody.innerHTML = docs.map((doc) => {
    const asunto = escapeHtml(doc.asunto || '');
    const estado = (doc.estado || '').toUpperCase();
    const creador = escapeHtml(doc.usuario_nombre || '-');

    return `
      <tr>
        <td><small>${doc.id}</small></td>
        <td><span class="dashboard-table-asunto" title="${asunto}">${asunto || '-'}</span></td>
        <td><small>${escapeHtml(doc.tipo_nombre || '-')}</small></td>
        <td><span class="badge estado-badge ${getStateBadgeClass(estado)}">${toStateLabel(estado)}</span></td>
        <td><small>${formatDate(doc.fecha_creacion)}</small></td>
        <td><small>${creador}</small></td>
      </tr>
    `;
  }).join('');
}

function setRefreshLoading(isLoading) {
  const btn = document.getElementById('btn-refresh-dashboard');
  if (!btn) return;

  if (isLoading) {
    if (!btn.dataset.originalHtml) {
      btn.dataset.originalHtml = btn.innerHTML;
    }
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>Actualizando';
    return;
  }

  btn.disabled = false;
  if (btn.dataset.originalHtml) {
    btn.innerHTML = btn.dataset.originalHtml;
  }
}

function renderDashboardError(message) {
  document.getElementById('kpi-documentos').textContent = '--';
  document.getElementById('kpi-firmas').textContent = '--';
  document.getElementById('kpi-tareas').textContent = '--';
  document.getElementById('kpi-observaciones').textContent = '--';
  document.getElementById('dashboard-subtitle').textContent = `No fue posible cargar datos: ${message}`;
  document.getElementById('estado-kpis-list').innerHTML = '<p class="small text-danger mb-0">Error al cargar distribucion de estados.</p>';
  document.getElementById('focus-summary').textContent = 'No se pudo calcular foco operativo.';
  document.getElementById('focus-list').innerHTML = '<li class="list-group-item px-0 py-2 text-danger small">Reintenta en unos segundos.</li>';
  document.getElementById('tabla-documentos').innerHTML = `<tr><td colspan="6" class="text-center text-danger small">Error al cargar documentos: ${escapeHtml(message)}</td></tr>`;
}

async function loadDashboardData() {
  setRefreshLoading(true);

  try {
    state.user = getSessionUser();

    const documents = await api.request('/documentos');
    state.documents = Array.isArray(documents) ? documents : [];
    state.pendingTasks = buildPendingTasks(state.documents, state.user);

    const observationResult = await loadObservationsCount(state.user, state.documents);
    state.observationsCount = observationResult.count;
    state.observationsSource = observationResult.source;

    renderKpis();
    renderStateBreakdown();
    renderFocusSummary();
    renderLatestDocuments();
  } catch (err) {
    renderDashboardError(err.message || 'Error desconocido');
  } finally {
    setRefreshLoading(false);
  }
}

function bindLogout() {
  const btn = document.getElementById('btn-logout');
  if (!btn) return; // Navbar might not be rendered yet
  if (btn.dataset.boundLogout === 'true') return; // avoid duplicate binding
  btn.addEventListener('click', () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = './index.html';
  });
  btn.dataset.boundLogout = 'true';
}

function bindRefresh() {
  const btn = document.getElementById('btn-refresh-dashboard');
  if (!btn || btn.dataset.boundRefresh === 'true') return;

  btn.addEventListener('click', () => {
    loadDashboardData();
  });

  btn.dataset.boundRefresh = 'true';
}

window.addEventListener('DOMContentLoaded', () => {
  bindLogout();
  bindRefresh();
  loadDashboardData();
});

// Bind logout once navbar is rendered by layout.js
document.addEventListener('layout:navbarReady', bindLogout);
