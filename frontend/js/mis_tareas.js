(function guardAuth() {
  const token = localStorage.getItem('token');
  if (!token) {
    window.location.href = './index.html';
  }
})();

let modalVerDoc;
let documentoActual = null;
let usuarioActual = null;
let tareasPendientesCache = [];
const ui = window.ui;

const FILTROS_STORAGE_KEY = 'mis_tareas_filtros_v1';
const ACCIONES_REVISION = new Set([
  'ENVIAR_REVISION',
  'REVISION_JURIDICA',
  'REVISION_GERENCIA',
  'CORREGIR_REENVIAR'
]);

const CAMPOS_AUTOMATICOS = new Set([
  'consecutivo',
  'fecha',
  'fecha_emision',
  'fecha_creacion',
  'gerente_firma',
  'gerente_nombre',
  'gerente_cargo',
  'unidad_firma',
  'unidad_nombre',
  'unidad_cargo',
  'juridica_firma',
  'juridica_nombre',
  'juridica_cargo'
]);

const TINYMCE_TOOLBAR = 'bold italic | bullist numlist | removeformat';

function tinyMceDisponible() {
  return typeof window !== 'undefined' && typeof window.tinymce !== 'undefined';
}

function asegurarTextareaId(textarea) {
  if (textarea.id) return textarea.id;
  const generatedId = `tiny-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  textarea.id = generatedId;
  return generatedId;
}

function sincronizarTinyMce() {
  if (!tinyMceDisponible()) return;
  try {
    window.tinymce.triggerSave();
  } catch (err) {
    console.warn('No se pudo sincronizar TinyMCE:', err);
  }
}

function destruirTinyMceEnContenedor(container) {
  if (!tinyMceDisponible() || !container) return;

  const textareas = container.querySelectorAll('textarea');
  textareas.forEach((textarea) => {
    if (!textarea.id) return;
    const editor = window.tinymce.get(textarea.id);
    if (editor) {
      editor.remove();
    }
  });
}

function inicializarTinyMceEnContenedor(container) {
  if (!tinyMceDisponible() || !container) return;

  const textareas = container.querySelectorAll('textarea');
  textareas.forEach((textarea) => {
    const textareaId = asegurarTextareaId(textarea);
    if (window.tinymce.get(textareaId)) {
      return;
    }

    window.tinymce.init({
      target: textarea,
      menubar: false,
      branding: false,
      statusbar: false,
      plugins: 'lists',
      toolbar: TINYMCE_TOOLBAR,
      content_style: 'body { font-family: Arial, sans-serif; font-size: 12pt; }',
      height: 220,
      setup: (editor) => {
        const sync = () => {
          textarea.value = normalizarValorCampo(editor.getContent());
        };

        editor.on('init', sync);
        editor.on('change input keyup undo redo', sync);
      }
    });
  });
}

function esCampoAutomatico(nombreCampo) {
  return CAMPOS_AUTOMATICOS.has((nombreCampo || '').toString().trim().toLowerCase());
}

function normalizarValorCampo(rawValue) {
  const value = (rawValue || '').toString().trim();
  if (!value) return '';

  const tmp = document.createElement('div');
  tmp.innerHTML = value;
  if (!tmp.textContent || !tmp.textContent.trim()) {
    return '';
  }

  return value;
}

function obtenerLongitudTextoPlano(rawValue) {
  const value = (rawValue || '').toString().trim();
  if (!value) return 0;

  const tmp = document.createElement('div');
  tmp.innerHTML = value;
  return (tmp.textContent || '').trim().length;
}

function ordenarTareasPendientes(listado) {
  return listado.sort((a, b) => {
    if (a.accion_prioridad !== b.accion_prioridad) {
      return a.accion_prioridad - b.accion_prioridad;
    }

    const fechaA = a.fecha_creacion ? new Date(a.fecha_creacion).getTime() : 0;
    const fechaB = b.fecha_creacion ? new Date(b.fecha_creacion).getTime() : 0;
    return fechaB - fechaA;
  });
}

function actualizarResumenOperativo(tareasFiltradas = tareasPendientesCache) {
  const total = tareasPendientesCache.length;
  const porRevisar = tareasPendientesCache.filter((t) => ACCIONES_REVISION.has(t.accion_codigo)).length;
  const porFinalizar = tareasPendientesCache.filter((t) => t.accion_codigo === 'FINALIZAR').length;

  const kpiTotal = document.getElementById('kpi-total');
  const kpiRevisar = document.getElementById('kpi-revisar');
  const kpiFinalizar = document.getElementById('kpi-finalizar');
  const resumenFiltros = document.getElementById('resumen-filtros');

  if (kpiTotal) kpiTotal.textContent = String(total);
  if (kpiRevisar) kpiRevisar.textContent = String(porRevisar);
  if (kpiFinalizar) kpiFinalizar.textContent = String(porFinalizar);
  if (resumenFiltros) resumenFiltros.textContent = `Mostrando ${tareasFiltradas.length} de ${total} tareas`;
}

function guardarFiltrosPersistidos() {
  const asunto = document.getElementById('filtro-asunto').value;
  const accion = document.getElementById('filtro-accion').value;

  try {
    localStorage.setItem(FILTROS_STORAGE_KEY, JSON.stringify({ asunto, accion }));
  } catch (err) {
    console.warn('No se pudieron persistir los filtros', err);
  }
}

function restaurarFiltrosPersistidos() {
  try {
    const raw = localStorage.getItem(FILTROS_STORAGE_KEY);
    if (!raw) return;

    const parsed = JSON.parse(raw);
    if (typeof parsed.asunto === 'string') {
      document.getElementById('filtro-asunto').value = parsed.asunto;
    }
    if (typeof parsed.accion === 'string') {
      document.getElementById('filtro-accion').value = parsed.accion;
    }
  } catch (err) {
    console.warn('No se pudieron restaurar los filtros', err);
  }
}

function actualizarBotonesFiltroRapido() {
  const accionActual = document.getElementById('filtro-accion').value;
  document.querySelectorAll('.filtro-rapido').forEach((btn) => {
    const match = (btn.dataset.accion || '') === accionActual;
    btn.classList.toggle('is-active', match);
  });
}

function setButtonLoading(button, isLoading, loadingText = 'Procesando') {
  if (!button) return;

  if (isLoading) {
    if (!button.dataset.originalHtml) {
      button.dataset.originalHtml = button.innerHTML;
    }
    button.disabled = true;
    button.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>${loadingText}`;
    return;
  }

  button.disabled = false;
  if (button.dataset.originalHtml) {
    button.innerHTML = button.dataset.originalHtml;
  }
}

function showToast(message, variant = 'info', title = '') {
  const container = document.getElementById('toast-container');
  if (!container || !window.bootstrap || !bootstrap.Toast) {
    ui.info(message, title || 'Mensaje');
    return;
  }

  const classMap = {
    success: 'text-bg-success',
    danger: 'text-bg-danger',
    warning: 'text-bg-warning',
    info: 'text-bg-primary'
  };

  const toast = document.createElement('div');
  toast.className = `toast border-0 ${classMap[variant] || classMap.info}`;
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'assertive');
  toast.setAttribute('aria-atomic', 'true');

  const heading = title ? `<strong class="me-auto">${title}</strong>` : '';
  toast.innerHTML = `
    <div class="toast-header">
      ${heading}
      <small class="text-muted">ahora</small>
      <button type="button" class="btn-close ms-2 mb-1" data-bs-dismiss="toast"></button>
    </div>
    <div class="toast-body">${message}</div>
  `;

  container.appendChild(toast);
  const toastInstance = new bootstrap.Toast(toast, { delay: 3500 });
  toast.addEventListener('hidden.bs.toast', () => toast.remove());
  toastInstance.show();
}

function escapeHtml(value) {
  return (value || '').toString()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function initMisTareasPage() {
  modalVerDoc = new bootstrap.Modal(document.getElementById('modalVerDoc'));
  usuarioActual = obtenerUsuarioActual();

  const modalElement = document.getElementById('modalVerDoc');
  if (modalElement) {
    modalElement.addEventListener('hidden.bs.modal', () => {
      const container = document.getElementById('ver-campos-container');
      destruirTinyMceEnContenedor(container);
    });
  }

  bindMenu();
  bindLogout();
  restaurarFiltrosPersistidos();
  actualizarBotonesFiltroRapido();

  document.getElementById('filtro-asunto').addEventListener('input', aplicarFiltrosLocales);
  document.getElementById('filtro-accion').addEventListener('change', () => {
    actualizarBotonesFiltroRapido();
    aplicarFiltrosLocales();
  });

  document.querySelectorAll('.filtro-rapido').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.getElementById('filtro-accion').value = btn.dataset.accion || '';
      actualizarBotonesFiltroRapido();
      aplicarFiltrosLocales();
    });
  });

  document.getElementById('btn-limpiar-filtros').addEventListener('click', () => {
    document.getElementById('filtro-asunto').value = '';
    document.getElementById('filtro-accion').value = '';
    localStorage.removeItem(FILTROS_STORAGE_KEY);
    actualizarBotonesFiltroRapido();
    aplicarFiltrosLocales();
    showToast('Filtros restablecidos', 'info', 'Filtros');
  });

  document.getElementById('btn-recargar').addEventListener('click', async (e) => {
    const btn = e.currentTarget;
    setButtonLoading(btn, true, 'Recargando');
    await cargarTareasPendientes();
    setButtonLoading(btn, false);
  });

  document.getElementById('btn-enviar-revision').addEventListener('click', (e) => enviarARevision(e.currentTarget));
  document.getElementById('btn-aprobar').addEventListener('click', (e) => aprobarDocumento(e.currentTarget));
  document.getElementById('btn-devolver').addEventListener('click', mostrarSectionObservaciones);
  document.getElementById('btn-finalizar').addEventListener('click', (e) => finalizarDocumento(e.currentTarget));
  document.getElementById('btn-enviar-observaciones').addEventListener('click', (e) => devolverDocumento(e.currentTarget));
  document.getElementById('btn-guardar-campos').addEventListener('click', (e) => guardarCamposDocumento(e.currentTarget));
  document.getElementById('btn-generar-pdf').addEventListener('click', (e) => generarPdfFinal(e.currentTarget));

  cargarTareasPendientes();
}

function obtenerUsuarioActual() {
  try {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  } catch (err) {
    console.warn('No se pudo leer el usuario de la sesión', err);
    return null;
  }
}

function bindMenu() {
  document.querySelectorAll('#menu-sidebar a').forEach((a) => {
    a.addEventListener('click', (e) => {
      if (a.getAttribute('href') === './mis_tareas.html') {
        e.preventDefault();
      }
    });
  });
}

function bindLogout() {
  const btn = document.getElementById('btn-logout');
  if (!btn || btn.dataset.boundLogout === 'true') return;

  btn.addEventListener('click', () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = './index.html';
  });

  btn.dataset.boundLogout = 'true';
}

document.addEventListener('layout:navbarReady', bindLogout);

function determinarAccionPendiente(doc) {
  if (!doc || !usuarioActual) return null;

  const idRol = Number(usuarioActual.id_rol);
  const userId = Number(usuarioActual.id_usuario);
  const creadorId = Number(doc.usuario_genera);
  const esCreador = userId === creadorId;

  const esSuperAdmin = idRol === 1;
  const esGerencia = idRol === 2;
  const esJuridica = idRol === 3;
  const esUnidad = idRol === 4;

  const estado = (doc.estado || '').toUpperCase();

  if (estado === 'BORRADOR') {
    if (esSuperAdmin || (esUnidad && esCreador)) {
      return {
        accion_codigo: 'ENVIAR_REVISION',
        accion_label: 'Enviar a revisión',
        accion_prioridad: 5
      };
    }
    return null;
  }

  if (estado === 'EN_REVISION_JURIDICA') {
    if (esSuperAdmin || esJuridica) {
      return {
        accion_codigo: 'REVISION_JURIDICA',
        accion_label: 'Revisión jurídica',
        accion_prioridad: 2
      };
    }
    return null;
  }

  if (estado === 'EN_REVISION_GERENCIAL') {
    if (esSuperAdmin || esGerencia) {
      return {
        accion_codigo: 'REVISION_GERENCIA',
        accion_label: 'Revisión gerencia',
        accion_prioridad: 2
      };
    }
    return null;
  }

  if (estado === 'DEVUELTO_JURIDICA' || estado === 'DEVUELTO_GERENCIA') {
    if (esSuperAdmin || (esUnidad && esCreador)) {
      return {
        accion_codigo: 'CORREGIR_REENVIAR',
        accion_label: 'Corregir y reenviar',
        accion_prioridad: 3
      };
    }
    return null;
  }

  if (estado === 'FIRMADO' || estado === 'PENDIENTE_FINALIZACION') {
    if (esCreador) {
      return {
        accion_codigo: 'FINALIZAR',
        accion_label: 'Finalizar',
        accion_prioridad: 1
      };
    }
    return null;
  }

  return null;
}

async function cargarTareasPendientes() {
  const tbody = document.getElementById('tabla-tareas');
  tbody.innerHTML = '<tr><td colspan="8" class="text-muted text-center py-3">Cargando tareas pendientes...</td></tr>';

  try {
    const documentos = await api.request('/documentos');

    tareasPendientesCache = (documentos || [])
      .map((doc) => {
        const accion = determinarAccionPendiente(doc);
        if (!accion) return null;
        return {
          ...doc,
          ...accion
        };
      })
      .filter(Boolean);

    ordenarTareasPendientes(tareasPendientesCache);

    aplicarFiltrosLocales();
  } catch (err) {
    tareasPendientesCache = [];
    actualizarResumenOperativo([]);
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4"><div class="alert alert-danger mb-0"><i class="bi bi-exclamation-triangle"></i> Error al cargar tareas: ${err.message}</div></td></tr>`;
    showToast(`Error al cargar tareas: ${err.message}`, 'danger', 'Mis tareas');
  }
}

function aplicarFiltrosLocales() {
  const asunto = document.getElementById('filtro-asunto').value.trim().toLowerCase();
  const accion = document.getElementById('filtro-accion').value;

  const filtradas = tareasPendientesCache.filter((t) => {
    const coincideAsunto = !asunto || (t.asunto || '').toLowerCase().includes(asunto);
    const coincideAccion = !accion || t.accion_codigo === accion;
    return coincideAsunto && coincideAccion;
  });

  renderizarTareas(filtradas);
  bindTareaActions();
  guardarFiltrosPersistidos();
  actualizarResumenOperativo(filtradas);
}

function obtenerClaseEstado(estado) {
  return `estado-${(estado || '').toLowerCase().replace(/_/g, '-')}`;
}

function obtenerBadgeAccion(accionCodigo, accionLabel) {
  const clases = {
    ENVIAR_REVISION: 'bg-secondary text-white',
    REVISION_JURIDICA: 'bg-warning text-dark',
    REVISION_GERENCIA: 'bg-warning text-dark',
    CORREGIR_REENVIAR: 'bg-info text-dark',
    FINALIZAR: 'bg-success text-white'
  };

  const clase = clases[accionCodigo] || 'bg-light text-dark';
  return `<span class="accion-badge ${clase}">${accionLabel}</span>`;
}

function renderizarTareas(tareas) {
  const tbody = document.getElementById('tabla-tareas');

  if (!tareas || tareas.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4"><div class="alert alert-info mb-0"><i class="bi bi-info-circle"></i> No tienes tareas pendientes por tu rol en este momento.</div></td></tr>';
    return;
  }

  tbody.innerHTML = tareas.map((t) => {
    const estadoClase = obtenerClaseEstado(t.estado);
    const fecha = t.fecha_creacion ? new Date(t.fecha_creacion).toLocaleString('es-ES') : '-';
    const asunto = t.asunto || '';
    const asuntoSafe = escapeHtml(asunto);

    return `
      <tr>
        <td><small>${t.id}</small></td>
        <td><strong class="asunto-truncate" title="${asuntoSafe}">${asuntoSafe}</strong></td>
        <td><small>${t.tipo_nombre || ''}</small></td>
        <td><small>${t.usuario_nombre || ''}</small></td>
        <td><span class="badge estado-badge ${estadoClase}">${(t.estado || '').replace(/_/g, ' ')}</span></td>
        <td>${obtenerBadgeAccion(t.accion_codigo, t.accion_label)}</td>
        <td><small>${fecha}</small></td>
        <td class="text-end">
          <div class="acciones-inline">
            ${renderizarBotonAccionRapida(t)}
            <button class="btn btn-sm btn-outline-primary" data-ver-doc="${t.id}" title="Ver detalle">
              <i class="bi bi-eye"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function renderizarBotonAccionRapida(tarea) {
  if (!tarea || !tarea.accion_codigo) return '';

  if (tarea.accion_codigo === 'ENVIAR_REVISION' || tarea.accion_codigo === 'CORREGIR_REENVIAR') {
    return `
      <button class="btn btn-sm btn-outline-secondary" data-quick-doc="${tarea.id}" data-quick-action="ENVIAR" title="Enviar directamente a revisión">
        <i class="bi bi-send-check"></i>
      </button>
    `;
  }

  if (tarea.accion_codigo === 'REVISION_JURIDICA' || tarea.accion_codigo === 'REVISION_GERENCIA') {
    return `
      <button class="btn btn-sm btn-outline-success" data-quick-doc="${tarea.id}" data-quick-action="APROBAR" title="Aprobar directamente">
        <i class="bi bi-check-circle"></i>
      </button>
    `;
  }

  if (tarea.accion_codigo === 'FINALIZAR') {
    return `
      <button class="btn btn-sm btn-outline-success" data-quick-doc="${tarea.id}" data-quick-action="FINALIZAR" title="Finalizar directamente">
        <i class="bi bi-check2-all"></i>
      </button>
    `;
  }

  return '';
}

function bindTareaActions() {
  document.querySelectorAll('[data-ver-doc]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const docId = Number(btn.dataset.verDoc);
      verDocumento(docId);
    });
  });

  document.querySelectorAll('[data-quick-doc][data-quick-action]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const docId = Number(btn.dataset.quickDoc);
      const quickAction = btn.dataset.quickAction;
      await ejecutarAccionRapida(docId, quickAction, btn);
    });
  });
}

function actualizarDocumentoEnCache(documento) {
  const index = tareasPendientesCache.findIndex((t) => Number(t.id) === Number(documento.id));
  const accion = determinarAccionPendiente(documento);

  if (!accion) {
    if (index >= 0) {
      tareasPendientesCache.splice(index, 1);
    }
    aplicarFiltrosLocales();
    return;
  }

  const tareaActualizada = { ...documento, ...accion };
  if (index >= 0) {
    tareasPendientesCache[index] = tareaActualizada;
  } else {
    tareasPendientesCache.push(tareaActualizada);
  }

  ordenarTareasPendientes(tareasPendientesCache);
  aplicarFiltrosLocales();
}

async function ejecutarAccionRapida(docId, quickAction, triggerButton = null) {
  const mensajesConfirmacion = {
    ENVIAR: '¿Enviar este documento a revisión? ',
    APROBAR: '¿Aprobar este documento directamente?',
    FINALIZAR: '¿Finalizar este documento ahora?'
  };

  if (!(await ui.confirm(mensajesConfirmacion[quickAction] || '¿Ejecutar esta acción rápida?'))) return;

  setButtonLoading(triggerButton, true, 'Aplicando');

  try {
    let nuevoEstado = null;
    let descripcionCambio = 'Cambio de estado desde Mis tareas';

    if (quickAction === 'FINALIZAR') {
      nuevoEstado = 'FINALIZADO';
      descripcionCambio = 'Documento finalizado desde acciones rápidas';
    } else {
      const transiciones = await api.request(`/documentos/${docId}/transiciones`);
      const validas = transiciones.transiciones_validas || [];

      if (quickAction === 'ENVIAR') {
        nuevoEstado = validas[0] || null;
        descripcionCambio = 'Enviado a revisión desde acciones rápidas';
      }

      if (quickAction === 'APROBAR') {
        nuevoEstado = validas.find((t) => t.includes('APROBADO')) || null;
        descripcionCambio = 'Documento aprobado desde acciones rápidas';
      }
    }

    if (!nuevoEstado) {
      throw new Error('No hay transición válida para esta acción');
    }

    await api.request(`/documentos/${docId}/estado`, {
      method: 'PUT',
      body: { nuevo_estado: nuevoEstado, descripcion_cambio: descripcionCambio }
    });

    const documentoActualizado = await api.request(`/documentos/${docId}`);
    actualizarDocumentoEnCache(documentoActualizado);

    showToast('Acción aplicada correctamente', 'success', 'Mis tareas');
  } catch (err) {
    showToast(`No se pudo aplicar la acción: ${err.message}`, 'danger', 'Mis tareas');
  } finally {
    setButtonLoading(triggerButton, false);
  }
}

async function generarPdfFinal(triggerButton = null) {
  if (!documentoActual || !documentoActual.id) return;
  if (!(await ui.confirm('¿Generar PDF final del documento?'))) return;

  setButtonLoading(triggerButton, true, 'Generando');

  try {
    await api.request(`/documentos/${documentoActual.id}/generar-pdf`, {
      method: 'POST'
    });

    documentoActual = await api.request(`/documentos/${documentoActual.id}`);

    if (documentoActual.ruta_pdf_final) {
      showToast('PDF final generado correctamente', 'success', 'Documento');
    } else {
      showToast('PDF solicitado, pero aún no se generó. Intente de nuevo.', 'warning', 'Documento');
    }

    await verDocumento(documentoActual.id);
    await cargarTareasPendientes();
  } catch (err) {
    showToast(`Error al generar PDF: ${err.message}`, 'danger', 'Documento');
  } finally {
    setButtonLoading(triggerButton, false);
  }
}

async function verDocumento(docId) {
  try {
    documentoActual = await api.request(`/documentos/${docId}`);

    document.getElementById('ver-id').textContent = documentoActual.id;
    document.getElementById('ver-asunto').textContent = documentoActual.asunto;
    document.getElementById('ver-tipo').textContent = documentoActual.tipo_nombre || '';
    document.getElementById('ver-fecha').textContent = new Date(documentoActual.fecha_creacion).toLocaleString('es-ES');
    document.getElementById('ver-creador').textContent = documentoActual.usuario_nombre || '';

    const estadoSpan = document.getElementById('ver-estado');
    const estadoClase = obtenerClaseEstado(documentoActual.estado);
    estadoSpan.className = `estado-badge ${estadoClase}`;
    estadoSpan.textContent = (documentoActual.estado || '').replace(/_/g, ' ');

    document.getElementById('ver-estado-info').innerHTML = `
      <strong>Estado actual:</strong> ${(documentoActual.estado || '').replace(/_/g, ' ')}<br>
      <small class="text-muted">Creado: ${new Date(documentoActual.fecha_creacion).toLocaleString('es-ES')}</small>
      ${documentoActual.fecha_emision ? `<br><small class="text-muted">Emitido: ${new Date(documentoActual.fecha_emision).toLocaleString('es-ES')}</small>` : ''}
      ${documentoActual.consecutivo ? `<br><strong>Consecutivo: ${documentoActual.consecutivo}</strong>` : ''}
    `;

    limpiarSeccionesModal();

    if (!documentoActual.ruta_word_generado && documentoActual.estado !== 'BORRADOR') {
      try {
        await api.request(`/documentos/${docId}/generar-word`, { method: 'POST' });
        documentoActual = await api.request(`/documentos/${docId}`);
      } catch (err) {
        console.warn('No se pudo generar Word automáticamente', err);
      }
    }

    configurarDescargasYPreview(documentoActual);

    if (documentoActual.estado === 'DEVUELTO_JURIDICA' || documentoActual.estado === 'DEVUELTO_GERENCIA') {
      await cargarObservacionesDocumento(documentoActual);
      await cargarCamposParaEditar(documentoActual);
    }

    try {
      const transiciones = await api.request(`/documentos/${docId}/transiciones`);
      mostrarAccionesDisponibles(transiciones.transiciones_validas || []);
    } catch (err) {
      console.warn('No se pudieron cargar transiciones', err);
      mostrarAccionesDisponibles([]);
    }

    document.getElementById('modalVerDocTitle').textContent = `Documento #${documentoActual.id}`;
    modalVerDoc.show();
  } catch (err) {
    showToast(`Error al cargar documento: ${err.message}`, 'danger', 'Documento');
  }
}

function limpiarSeccionesModal() {
  const camposContainer = document.getElementById('ver-campos-container');
  destruirTinyMceEnContenedor(camposContainer);

  document.getElementById('section-editar-campos').classList.add('d-none');
  document.getElementById('section-observaciones').classList.add('d-none');
  document.getElementById('section-observaciones-historial').classList.add('d-none');
  document.getElementById('section-acciones').classList.add('d-none');
  document.getElementById('ver-doc-error').classList.add('d-none');

  if (camposContainer) camposContainer.innerHTML = '';

  const txtObs = document.getElementById('textarea-observaciones');
  if (txtObs) txtObs.value = '';
}

function configurarDescargasYPreview(doc) {
  const linkWord = document.getElementById('link-descargar-word');
  const linkPdf = document.getElementById('link-descargar-pdf');
  const btnGenerarPdf = document.getElementById('btn-generar-pdf');
  const sectionPreview = document.getElementById('section-preview');
  const previewLoading = document.getElementById('preview-loading');
  const iframePreview = document.getElementById('iframe-preview');

  linkWord.classList.add('d-none');
  linkPdf.classList.add('d-none');
  btnGenerarPdf.classList.add('d-none');
  sectionPreview.classList.add('d-none');
  previewLoading.classList.add('d-none');
  iframePreview.style.display = 'none';
  iframePreview.src = 'about:blank';

  if (doc.ruta_word_generado && doc.estado !== 'FINALIZADO') {
    linkWord.href = API_BASE + doc.ruta_word_generado;
    linkWord.classList.remove('d-none');
  }

  if (doc.ruta_pdf_final) {
    linkPdf.href = API_BASE + doc.ruta_pdf_final;
    linkPdf.classList.remove('d-none');

    sectionPreview.classList.remove('d-none');
    iframePreview.style.display = 'block';
    iframePreview.src = API_BASE + doc.ruta_pdf_final;
    return;
  }

  if (doc.estado === 'FINALIZADO') {
    btnGenerarPdf.classList.remove('d-none');
  }

  if (
    doc.ruta_word_generado &&
    doc.estado !== 'BORRADOR' &&
    doc.estado !== 'DEVUELTO_JURIDICA' &&
    doc.estado !== 'DEVUELTO_GERENCIA'
  ) {
    sectionPreview.classList.remove('d-none');
    previewLoading.classList.remove('d-none');
    previewLoading.innerHTML = '<div class="alert alert-info mb-0"><i class="bi bi-file-word"></i> Documento Word generado. Puede descargarlo con el botón de Word.</div>';
  }
}

function mostrarAccionesDisponibles(transiciones) {
  const sectionAcciones = document.getElementById('section-acciones');
  const sectionObs = document.getElementById('section-observaciones');

  const btnEnviar = document.getElementById('btn-enviar-revision');
  const btnAprobar = document.getElementById('btn-aprobar');
  const btnDevolver = document.getElementById('btn-devolver');
  const btnFinalizar = document.getElementById('btn-finalizar');

  btnEnviar.classList.add('d-none');
  btnAprobar.classList.add('d-none');
  btnDevolver.classList.add('d-none');
  btnFinalizar.classList.add('d-none');

  if (!Array.isArray(transiciones) || transiciones.length === 0 || !documentoActual || !usuarioActual) {
    sectionAcciones.classList.add('d-none');
    return;
  }

  sectionAcciones.classList.remove('d-none');
  sectionObs.classList.add('d-none');

  const idRol = Number(usuarioActual.id_rol);
  const esSuperAdmin = idRol === 1;
  const esGerencia = idRol === 2;
  const esJuridica = idRol === 3;
  const esUnidad = idRol === 4;

  const esCreador = Number(documentoActual.usuario_genera) === Number(usuarioActual.id_usuario);
  const estado = documentoActual.estado;

  if (estado === 'BORRADOR') {
    if ((esSuperAdmin || (esUnidad && esCreador)) &&
      (transiciones.includes('EN_REVISION_JURIDICA') || transiciones.includes('EN_REVISION_GERENCIAL'))) {
      btnEnviar.classList.remove('d-none');
    }
    return;
  }

  if (estado === 'EN_REVISION_JURIDICA') {
    if (esSuperAdmin || esJuridica) {
      if (transiciones.includes('APROBADO_JURIDICA')) btnAprobar.classList.remove('d-none');
      if (transiciones.includes('DEVUELTO_JURIDICA')) btnDevolver.classList.remove('d-none');
    }
    return;
  }

  if (estado === 'EN_REVISION_GERENCIAL') {
    if (esSuperAdmin || esGerencia) {
      if (transiciones.includes('APROBADO_GERENCIA')) btnAprobar.classList.remove('d-none');
      if (transiciones.includes('DEVUELTO_GERENCIA')) btnDevolver.classList.remove('d-none');
    }
    return;
  }

  if (estado === 'DEVUELTO_JURIDICA' || estado === 'DEVUELTO_GERENCIA') {
    if ((esSuperAdmin || (esUnidad && esCreador)) &&
      (transiciones.includes('EN_REVISION_JURIDICA') || transiciones.includes('EN_REVISION_GERENCIAL'))) {
      btnEnviar.classList.remove('d-none');
    }
    return;
  }

  if (estado === 'FIRMADO' || estado === 'PENDIENTE_FINALIZACION') {
    if (transiciones.includes('FINALIZADO') && esCreador) {
      btnFinalizar.classList.remove('d-none');
    }
  }
}

function mostrarSectionObservaciones() {
  document.getElementById('section-acciones').classList.add('d-none');
  document.getElementById('section-observaciones').classList.remove('d-none');
}

async function enviarARevision(triggerButton = null) {
  if (!documentoActual) return;
  if (!(await ui.confirm('¿Enviar documento a revisión?'))) return;

  setButtonLoading(triggerButton, true, 'Enviando');

  try {
    const transiciones = await api.request(`/documentos/${documentoActual.id}/transiciones`);
    const siguienteEstado = (transiciones.transiciones_validas || [])[0];

    if (!siguienteEstado) {
      throw new Error('No hay estados disponibles para este documento');
    }

    await api.request(`/documentos/${documentoActual.id}/estado`, {
      method: 'PUT',
      body: { nuevo_estado: siguienteEstado, descripcion_cambio: 'Enviado a revisión' }
    });

    showToast(`Documento enviado a ${siguienteEstado.replace(/_/g, ' ')}`, 'success', 'Mis tareas');
    modalVerDoc.hide();
    await cargarTareasPendientes();
  } catch (err) {
    showToast(`Error: ${err.message}`, 'danger', 'Mis tareas');
  } finally {
    setButtonLoading(triggerButton, false);
  }
}

async function aprobarDocumento(triggerButton = null) {
  if (!documentoActual) return;
  if (!(await ui.confirm('¿Aprobar este documento?'))) return;

  setButtonLoading(triggerButton, true, 'Aprobando');

  try {
    const transiciones = await api.request(`/documentos/${documentoActual.id}/transiciones`);
    const siguienteEstado = (transiciones.transiciones_validas || []).find((t) => t.includes('APROBADO'));

    if (!siguienteEstado) {
      throw new Error('No hay estado de aprobación disponible');
    }

    await api.request(`/documentos/${documentoActual.id}/estado`, {
      method: 'PUT',
      body: { nuevo_estado: siguienteEstado, descripcion_cambio: 'Documento aprobado' }
    });

    showToast('Documento aprobado correctamente', 'success', 'Mis tareas');
    modalVerDoc.hide();
    await cargarTareasPendientes();
  } catch (err) {
    showToast(`Error: ${err.message}`, 'danger', 'Mis tareas');
  } finally {
    setButtonLoading(triggerButton, false);
  }
}

async function finalizarDocumento(triggerButton = null) {
  if (!documentoActual) return;
  if (!(await ui.confirm('¿Finalizar documento? Se asignará consecutivo y se intentará generar PDF final.'))) return;

  setButtonLoading(triggerButton, true, 'Finalizando');

  try {
    await api.request(`/documentos/${documentoActual.id}/estado`, {
      method: 'PUT',
      body: { nuevo_estado: 'FINALIZADO', descripcion_cambio: 'Documento finalizado' }
    });

    showToast('Documento finalizado correctamente', 'success', 'Mis tareas');
    modalVerDoc.hide();
    await cargarTareasPendientes();
  } catch (err) {
    showToast(`Error: ${err.message}`, 'danger', 'Mis tareas');
  } finally {
    setButtonLoading(triggerButton, false);
  }
}

async function devolverDocumento(triggerButton = null) {
  if (!documentoActual) return;

  const observaciones = document.getElementById('textarea-observaciones').value.trim();
  if (!observaciones) {
    showToast('Ingrese observaciones para devolver el documento', 'warning', 'Mis tareas');
    return;
  }

  const longitudTexto = obtenerLongitudTextoPlano(observaciones);
  if (longitudTexto < 10) {
    showToast('La observacion debe tener al menos 10 caracteres', 'warning', 'Mis tareas');
    return;
  }

  setButtonLoading(triggerButton, true, 'Devolviendo');

  try {
    const transiciones = await api.request(`/documentos/${documentoActual.id}/transiciones`);
    const estadoDevolucion = (transiciones.transiciones_validas || []).find((t) => t.includes('DEVUELTO'));

    if (!estadoDevolucion) {
      throw new Error('No se puede devolver desde este estado');
    }

    await api.request(`/documentos/${documentoActual.id}/estado`, {
      method: 'PUT',
      body: { nuevo_estado: estadoDevolucion, descripcion_cambio: observaciones }
    });

    showToast('Documento devuelto con observaciones', 'success', 'Mis tareas');
    modalVerDoc.hide();
    await cargarTareasPendientes();
  } catch (err) {
    showToast(`Error: ${err.message}`, 'danger', 'Mis tareas');
  } finally {
    setButtonLoading(triggerButton, false);
  }
}

async function cargarCamposParaEditar(documento) {
  try {
    const sectionEditar = document.getElementById('section-editar-campos');
    const container = document.getElementById('ver-campos-container');
    destruirTinyMceEnContenedor(container);

    const plantilla = await api.request(`/plantillas/${documento.id_plantilla}`);

    if (!plantilla.campos_json || typeof plantilla.campos_json !== 'object' || Object.keys(plantilla.campos_json).length === 0) {
      container.innerHTML = '<p class="text-muted">Esta plantilla no tiene campos definidos.</p>';
      sectionEditar.classList.remove('d-none');
      return;
    }

    let html = '<div class="campos-editables-stack">';
    let camposEditables = 0;

    for (const [nombre_campo, tipo_dato] of Object.entries(plantilla.campos_json)) {
      if (esCampoAutomatico(nombre_campo)) {
        continue;
      }

      const valor = documento.valores_campos && documento.valores_campos[nombre_campo]
        ? documento.valores_campos[nombre_campo]
        : '';

      const tipoUpper = (tipo_dato || '').toString().toUpperCase();
      let inputHtml = '';

      if (tipoUpper === 'TEXT') {
        inputHtml = `<textarea class="form-control form-control-sm campo-editable" name="${nombre_campo}" rows="5">${valor}</textarea>`;
      } else if (tipoUpper === 'VARCHAR') {
        inputHtml = `<textarea class="form-control form-control-sm campo-editable" name="${nombre_campo}" rows="5">${valor}</textarea>`;
      } else if (tipoUpper === 'INT' || tipoUpper === 'DECIMAL' || tipoUpper === 'FLOAT') {
        inputHtml = `<input type="number" step="${tipoUpper === 'INT' ? '1' : '0.01'}" class="form-control form-control-sm campo-editable" name="${nombre_campo}" value="${valor}" />`;
      } else if (tipoUpper === 'DATE') {
        inputHtml = `<input type="date" class="form-control form-control-sm campo-editable" name="${nombre_campo}" value="${valor}" />`;
      } else if (tipoUpper === 'DATETIME') {
        inputHtml = `<input type="datetime-local" class="form-control form-control-sm campo-editable" name="${nombre_campo}" value="${valor}" />`;
      } else {
        inputHtml = `<textarea class="form-control form-control-sm campo-editable" name="${nombre_campo}" rows="5">${valor}</textarea>`;
      }

      html += `
        <div class="campo-edit-item">
          <label class="form-label small fw-semibold">
            ${nombre_campo}
            <small class="text-muted">(${tipo_dato})</small>
          </label>
          ${inputHtml}
        </div>
      `;

      camposEditables += 1;
    }
    if (camposEditables === 0) {
      container.innerHTML = '<p class="text-muted">Esta plantilla solo tiene campos automáticos del sistema.</p>';
      sectionEditar.classList.remove('d-none');
      return;
    }

    html += '</div>';
    container.innerHTML = html;
    sectionEditar.classList.remove('d-none');
    inicializarTinyMceEnContenedor(container);
  } catch (err) {
    console.error('Error al cargar campos editables', err);
    await ui.error('Error al cargar campos editables');
  }
}

async function guardarCamposDocumento(triggerButton = null) {
  if (!documentoActual) return;

  setButtonLoading(triggerButton, true, 'Guardando');

  try {
    sincronizarTinyMce();

    const campos = document.querySelectorAll('.campo-editable');
    const valores_campos = {};

    campos.forEach((campo) => {
      valores_campos[campo.name] = normalizarValorCampo(campo.value);
    });

    if (Object.keys(valores_campos).length === 0) {
      showToast('No hay campos para actualizar', 'warning', 'Documento');
      setButtonLoading(triggerButton, false);
      return;
    }

    await api.request(`/documentos/${documentoActual.id}`, {
      method: 'PUT',
      body: { valores_campos }
    });

    try {
      await api.request(`/documentos/${documentoActual.id}/generar-word`, { method: 'POST' });
    } catch (err) {
      console.warn('No se pudo regenerar Word', err);
    }

    showToast('Campos actualizados correctamente', 'success', 'Documento');
    await verDocumento(documentoActual.id);
    await cargarTareasPendientes();
  } catch (err) {
    showToast(`Error al guardar campos: ${err.message}`, 'danger', 'Documento');
  } finally {
    setButtonLoading(triggerButton, false);
  }
}

async function cargarObservacionesDocumento(documento) {
  try {
    const sectionObs = document.getElementById('section-observaciones-historial');
    const container = document.getElementById('ver-observaciones-container');

    const observaciones = await api.request(`/observaciones/documento/${documento.id}`);

    if (!observaciones || observaciones.length === 0) {
      container.innerHTML = '<p class="text-muted">No hay observaciones registradas.</p>';
      sectionObs.classList.remove('d-none');
      return;
    }

    const items = observaciones.map((obs) => {
      const fecha = obs.fecha ? new Date(obs.fecha).toLocaleString('es-ES') : '';
      return `
        <div class="border rounded p-2 mb-2">
          <div class="d-flex justify-content-between">
            <span class="badge bg-secondary">${obs.tipo}</span>
            <small class="text-muted">${fecha}</small>
          </div>
          <div class="mt-1">${obs.descripcion}</div>
        </div>
      `;
    }).join('');

    container.innerHTML = items;
    sectionObs.classList.remove('d-none');
  } catch (err) {
    console.warn('No se pudieron cargar observaciones', err);
  }
}
