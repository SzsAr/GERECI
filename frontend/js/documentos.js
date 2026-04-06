(function guardAuth() {
  const token = localStorage.getItem('token');
  if (!token) window.location.href = './index.html';
})();

let modalNuevoDoc, modalVerDoc;
let documentoActual = null;
let plantillasData = []; // Almacenar datos completos de plantillas
let documentosCache = []; // Almacenar documentos para filtrado local
let documentosFiltrados = []; // Documentos después de filtrar
let paginaActual = 1; // Página actual
const REGISTROS_POR_PAGINA = 10; // 10 registros por página
const ui = window.ui;

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

function esCampoAutomatico(nombreCampo) {
  return CAMPOS_AUTOMATICOS.has((nombreCampo || '').toString().trim().toLowerCase());
}

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

function initDocumentosPage() {
  modalNuevoDoc = new bootstrap.Modal(document.getElementById('modalNuevoDoc'));
  modalVerDoc = new bootstrap.Modal(document.getElementById('modalVerDoc'));
  
  bindMenu();
  bindLogout();
  cargarTiposYPlantillas();
  cargarDocumentos();
  
  document.getElementById('btn-nuevo-doc').addEventListener('click', () => {
    abrirModalNuevoDoc();
  });

  document.getElementById('btn-limpiar-filtros').addEventListener('click', () => {
    limpiarFiltrosDocumentos();
  });
  
  // Filtrado en tiempo real por asunto
  document.getElementById('filtro-asunto').addEventListener('input', () => {
    filtrarDocumentosLocal();
  });

  // Filtrado por tipo de documento
  document.getElementById('filtro-tipo').addEventListener('change', () => {
    filtrarDocumentosLocal();
  });

  // Filtrado por rango de fechas de creación
  document.getElementById('filtro-fecha-desde').addEventListener('change', () => {
    filtrarDocumentosLocal();
  });

  document.getElementById('filtro-fecha-hasta').addEventListener('change', () => {
    filtrarDocumentosLocal();
  });
  
  // Filtrado por estado
  document.getElementById('filtro-estado').addEventListener('change', () => {
    cargarDocumentos();
  });
  
  document.getElementById('btn-generar-doc').addEventListener('click', () => {
    generarDocumento();
  });
  
  document.getElementById('nuevo-plantilla').addEventListener('change', () => {
    cargarCamposPlantilla();
  });
  
  document.getElementById('btn-guardar-campos').addEventListener('click', () => {
    guardarCamposDocumento();
  });
  
  document.getElementById('btn-enviar-revision').addEventListener('click', () => {
    enviarARevision();
  });
  
  document.getElementById('btn-aprobar').addEventListener('click', () => {
    aprobarDocumento();
  });
  
  document.getElementById('btn-devolver').addEventListener('click', () => {
    mostrarSectionObservaciones();
  });
  
  document.getElementById('btn-firmar').addEventListener('click', () => {
    mostrarSectionFirma();
  });
  
  document.getElementById('btn-finalizar').addEventListener('click', () => {
    finalizarDocumento();
  });
  
  document.getElementById('btn-enviar-observaciones').addEventListener('click', () => {
    devolverDocumento();
  });
  
  document.getElementById('btn-confirmar-firma').addEventListener('click', () => {
    confirmarFirma();
  });
  
  document.getElementById('btn-generar-pdf').addEventListener('click', () => {
    generarPdfFinal();
  });
}

async function generarPdfFinal() {
  if (!documentoActual || !documentoActual.id) return;
  if (!(await ui.confirm('¿Generar PDF final del documento?'))) return;

  try {
    const resp = await api.request(`/documentos/${documentoActual.id}/generar-pdf`, {
      method: 'POST'
    });

    // Refrescar datos
    documentoActual = await api.request(`/documentos/${documentoActual.id}`);

    if (documentoActual.ruta_pdf_final) {
      await ui.success('PDF final generado correctamente');
    } else {
      await ui.warning('PDF solicitado, pero aún no se generó. Intente de nuevo.');
    }

    modalVerDoc.hide();
    cargarDocumentos();
  } catch (err) {
    await ui.error(`Error al generar PDF: ${err.message}`);
  }
}

function bindMenu() {
  document.querySelectorAll('#menu-sidebar a').forEach(a => {
    a.addEventListener('click', (e) => {
      if (a.getAttribute('href') === './documentos.html') {
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
    window.location.href = './index.html';
  });
  btn.dataset.boundLogout = 'true';
}

async function cargarTiposYPlantillas() {
  try {
    console.log('Cargando plantillas...');
    const plantillas = await api.request('/plantillas');
    console.log('Plantillas obtenidas:', plantillas);
    
    // Guardar datos completos de plantillas
    plantillasData = plantillas || [];
    
    const plantillaSelect = document.getElementById('nuevo-plantilla');
    if (plantillas && plantillas.length > 0) {
      plantillaSelect.innerHTML = '<option value="">Seleccione una plantilla...</option>' + 
        plantillas.map(p => `<option value="${p.id}">${p.nombre} (${p.tipo_nombre || 'Sin tipo'})</option>`).join('');
    } else {
      plantillaSelect.innerHTML = '<option value="">No hay plantillas disponibles</option>';
    }
  } catch (err) {
    console.error('Error al cargar plantillas:', err);
    const plantillaSelect = document.getElementById('nuevo-plantilla');
    plantillaSelect.innerHTML = '<option value="">Error al cargar</option>';
  }
}

async function cargarDocumentos() {
  const estado = document.getElementById('filtro-estado').value;
  const tbody = document.querySelector('#tabla-documentos');
  
  tbody.innerHTML = '<tr><td colspan="8" class="text-muted text-center py-3">Cargando...</td></tr>';
  
  try {
    let url = '/documentos';
    const params = [];
    if (estado) params.push(`estado=${encodeURIComponent(estado)}`);
    if (url.includes('?')) url += '&' + params.join('&');
    else if (params.length) url += '?' + params.join('&');
    
    const docs = await api.request(url);
    
    // Almacenar en cache para filtrado local
    documentosCache = docs || [];

    poblarFiltroTipo(documentosCache);
    filtrarDocumentosLocal();
  } catch (err) {
    const tbody = document.querySelector('#tabla-documentos');
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4"><div class="alert alert-danger mb-0"><i class="bi bi-exclamation-triangle"></i> Error al cargar documentos: ${err.message}</div></td></tr>`;
  }
}

function limpiarFiltrosDocumentos() {
  document.getElementById('filtro-estado').value = '';
  document.getElementById('filtro-tipo').value = '';
  document.getElementById('filtro-fecha-desde').value = '';
  document.getElementById('filtro-fecha-hasta').value = '';
  document.getElementById('filtro-asunto').value = '';
  paginaActual = 1; // Resetear a página 1
  cargarDocumentos();
}

function poblarFiltroTipo(docs) {
  const select = document.getElementById('filtro-tipo');
  if (!select) return;

  const valorActual = select.value;
  const tiposUnicos = Array.from(new Set(
    (docs || [])
      .map(d => (d.tipo_nombre || '').toString().trim())
      .filter(Boolean)
  )).sort((a, b) => a.localeCompare(b, 'es', { sensitivity: 'base' }));

  select.innerHTML = '<option value="">Todos los tipos</option>' +
    tiposUnicos.map(tipo => `<option value="${tipo}">${tipo}</option>`).join('');

  if (valorActual && tiposUnicos.includes(valorActual)) {
    select.value = valorActual;
  }
}

// Renderizar documentos en la tabla con paginación
function renderizarDocumentos(docs) {
  const tbody = document.querySelector('#tabla-documentos');
  documentosFiltrados = docs || []; // Guardar documentos filtrados
  paginaActual = 1; // Resetear a página 1 cuando se cambian filtros
  
  if (!docs || docs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4"><div class="alert alert-info mb-0"><i class="bi bi-info-circle"></i> No hay documentos para mostrar. Crea uno nuevo con el botón <strong>Nuevo</strong></div></td></tr>';
    renderizarPaginacion(0);
    return;
  }
  
  // Calcular índices para la página actual
  const inicio = (paginaActual - 1) * REGISTROS_POR_PAGINA;
  const fin = inicio + REGISTROS_POR_PAGINA;
  const documentosPagina = docs.slice(inicio, fin);
  
  // Renderizar solo los documentos de esta página
  renderizarFilasDocumentos(documentosPagina, tbody);
  renderizarPaginacion(docs.length);
}

// Renderizar solo las filas de documentos (sin paginación)
function renderizarFilasDocumentos(docs, tbody) {
  if (!docs || docs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4"><div class="alert alert-info mb-0"><i class="bi bi-info-circle"></i> No hay documentos para mostrar. Crea uno nuevo con el botón <strong>Nuevo</strong></div></td></tr>';
    return;
  }
  
  tbody.innerHTML = docs.map(d => {
    const estadoClase = `estado-${d.estado.toLowerCase().replace(/_/g, '-')}`;
    const linkWord = (d.ruta_word_generado && d.estado !== 'FINALIZADO')
      ? `<a href="${API_BASE}${d.ruta_word_generado}" target="_blank" class="btn btn-sm btn-info"><i class="bi bi-file-word"></i></a>`
      : '';
    const linkPdf = d.ruta_pdf_final
      ? `<a href="${API_BASE}${d.ruta_pdf_final}" target="_blank" class="btn btn-sm btn-danger"><i class="bi bi-file-pdf"></i></a>`
      : (d.estado === 'FINALIZADO'
        ? `<button class="btn btn-sm btn-outline-danger" disabled title="PDF en proceso"><i class="bi bi-file-pdf"></i></button>`
        : '');
    
    return `
      <tr>
        <td><small>${d.id}</small></td>
        <td><strong>${d.asunto}</strong></td>
        <td><small>${d.tipo_nombre || ''}</small></td>
        <td><small>${d.plantilla_nombre || ''}</small></td>
        <td><small>${d.usuario_nombre || ''}</small></td>
        <td><span class="badge estado-badge ${estadoClase}">${d.estado.replace(/_/g, ' ')}</span></td>
        <td><code>${d.consecutivo || '-'}</code></td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-primary" data-ver-doc="${d.id}" title="Ver"><i class="bi bi-eye"></i></button>
          ${linkWord} ${linkPdf}
          <button class="btn btn-sm btn-outline-danger" data-eliminar-doc="${d.id}" title="Eliminar"><i class="bi bi-trash"></i></button>
        </td>
      </tr>
    `;
  }).join('');
}

// Renderizar controles de paginación
function renderizarPaginacion(totalDocumentos) {
  const paginacionControl = document.getElementById('paginacion-controles');
  const paginacionInfo = document.getElementById('paginacion-info');
  
  if (!paginacionControl) return;
  
  if (totalDocumentos === 0) {
    paginacionControl.innerHTML = '';
    paginacionInfo.textContent = '';
    return;
  }
  
  const totalPaginas = Math.ceil(totalDocumentos / REGISTROS_POR_PAGINA);
  const inicio = (paginaActual - 1) * REGISTROS_POR_PAGINA + 1;
  const fin = Math.min(paginaActual * REGISTROS_POR_PAGINA, totalDocumentos);
  
  paginacionInfo.textContent = `Mostrando ${inicio}-${fin} de ${totalDocumentos} documentos`;
  
  let html = '';
  
  // Botón anterior
  if (paginaActual > 1) {
    html += `<li class="page-item"><button class="page-link" data-pagina="${paginaActual - 1}" title="Página anterior"><i class="bi bi-chevron-left"></i></button></li>`;
  } else {
    html += '<li class="page-item disabled"><span class="page-link"><i class="bi bi-chevron-left"></i></span></li>';
  }
  
  // Números de página (máximo 5 botones visibles)
  let paginaInicio = Math.max(1, paginaActual - 2);
  let paginaFin = Math.min(totalPaginas, paginaActual + 2);
  
  if (paginaInicio > 1) {
    html += '<li class="page-item"><button class="page-link" data-pagina="1">1</button></li>';
    if (paginaInicio > 2) html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
  }
  
  for (let i = paginaInicio; i <= paginaFin; i++) {
    if (i === paginaActual) {
      html += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
    } else {
      html += `<li class="page-item"><button class="page-link" data-pagina="${i}">${i}</button></li>`;
    }
  }
  
  if (paginaFin < totalPaginas) {
    if (paginaFin < totalPaginas - 1) html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
    html += `<li class="page-item"><button class="page-link" data-pagina="${totalPaginas}">${totalPaginas}</button></li>`;
  }
  
  // Botón siguiente
  if (paginaActual < totalPaginas) {
    html += `<li class="page-item"><button class="page-link" data-pagina="${paginaActual + 1}" title="Página siguiente"><i class="bi bi-chevron-right"></i></button></li>`;
  } else {
    html += '<li class="page-item disabled"><span class="page-link"><i class="bi bi-chevron-right"></i></span></li>';
  }
  
  paginacionControl.innerHTML = html;
  
  // Vincular botones de paginación
  document.querySelectorAll('#paginacion-controles button[data-pagina]').forEach(btn => {
    btn.addEventListener('click', () => {
      paginaActual = parseInt(btn.dataset.pagina);
      const tbody = document.querySelector('#tabla-documentos');
      
      // Calcular índices para la página actual
      const inicio = (paginaActual - 1) * REGISTROS_POR_PAGINA;
      const fin = inicio + REGISTROS_POR_PAGINA;
      const documentosPagina = documentosFiltrados.slice(inicio, fin);
      
      renderizarFilasDocumentos(documentosPagina, tbody);
      renderizarPaginacion(documentosFiltrados.length);
      bindDocumentoActions(); // Vincular botones de documentos después de cambiar página
      tbody.closest('.card').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
  });
}

// Filtrado local en tiempo real por asunto
function filtrarDocumentosLocal() {
  const asunto = document.getElementById('filtro-asunto').value.trim().toLowerCase();
  const tipo = document.getElementById('filtro-tipo').value;
  const fechaDesde = document.getElementById('filtro-fecha-desde').value;
  const fechaHasta = document.getElementById('filtro-fecha-hasta').value;

  const desdeDate = fechaDesde ? new Date(`${fechaDesde}T00:00:00`) : null;
  const hastaDate = fechaHasta ? new Date(`${fechaHasta}T23:59:59.999`) : null;

  const filtrados = (documentosCache || []).filter(d => {
    const asuntoDoc = (d.asunto || '').toString().toLowerCase();
    if (asunto && !asuntoDoc.includes(asunto)) return false;

    const tipoDoc = (d.tipo_nombre || '').toString().trim();
    if (tipo && tipoDoc !== tipo) return false;

    if (desdeDate || hastaDate) {
      if (!d.fecha_creacion) return false;
      const fechaCreacion = new Date(d.fecha_creacion);
      if (Number.isNaN(fechaCreacion.getTime())) return false;
      if (desdeDate && fechaCreacion < desdeDate) return false;
      if (hastaDate && fechaCreacion > hastaDate) return false;
    }

    return true;
  });

  paginaActual = 1; // Resetear a página 1 cuando se aplica filtro
  renderizarDocumentos(filtrados);
  bindDocumentoActions(); // Vincular acciones de documentos después de renderizar
}

function bindDocumentoActions() {
  // Remover listeners previos para evitar acumulamiento
  document.querySelectorAll('[data-ver-doc]').forEach(btn => {
    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);
  });
  document.querySelectorAll('[data-eliminar-doc]').forEach(btn => {
    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);
  });
  
  // Vincular listen listeners nuevos
  document.querySelectorAll('[data-ver-doc]').forEach(btn => {
    btn.addEventListener('click', () => {
      const docId = btn.dataset.verDoc;
      verDocumento(parseInt(docId));
    });
  });
  
  document.querySelectorAll('[data-eliminar-doc]').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!(await ui.confirm('¿Eliminar documento?'))) return;
      const docId = btn.dataset.eliminarDoc;
      try {
        await api.request(`/documentos/${docId}`, { method: 'DELETE' });
        await ui.success('Documento eliminado correctamente');
        cargarDocumentos();
      } catch (err) {
        await ui.error(`Error: ${err.message}`);
      }
    });
  });
}

function abrirModalNuevoDoc() {
  document.getElementById('form-nuevo-doc').reset();
  document.getElementById('nuevo-doc-error').classList.add('d-none');
  const containerCampos = document.getElementById('nuevo-campos-container');
  destruirTinyMceEnContenedor(containerCampos);
  containerCampos.innerHTML = '';
  document.getElementById('tipo-documento-info').classList.add('d-none');
  document.getElementById('campos-section').style.display = 'none';
  document.getElementById('modalNuevoDocTitle').textContent = 'Nuevo documento';
  modalNuevoDoc.show();
}

async function cargarCamposPlantilla() {
  const plantillaId = parseInt(document.getElementById('nuevo-plantilla').value);
  const tipoInfo = document.getElementById('tipo-documento-info');
  const camposSection = document.getElementById('campos-section');
  const container = document.getElementById('nuevo-campos-container');

  destruirTinyMceEnContenedor(container);
  
  if (!plantillaId) {
    tipoInfo.classList.add('d-none');
    camposSection.style.display = 'none';
    container.innerHTML = '';
    return;
  }
  
  // Buscar la plantilla en los datos cargados
  const plantilla = plantillasData.find(p => p.id === plantillaId);
  
  if (!plantilla) {
    console.error('Plantilla no encontrada');
    return;
  }
  
  // Mostrar tipo de documento
  if (plantilla.tipo_nombre) {
    tipoInfo.textContent = `Tipo de documento: ${plantilla.tipo_nombre}`;
    tipoInfo.classList.remove('d-none');
  }
  
  // Limpiar y generar campos
  container.innerHTML = '';
  
  if (plantilla.campos_json && typeof plantilla.campos_json === 'object') {
    // Mantener el orden de inserción de los campos
    const campos = Object.keys(plantilla.campos_json);
    if (campos.length > 0) {
      let camposRenderizados = 0;
      // Iterar en el mismo orden que fueron creados
      for (const key of campos) {
        if (esCampoAutomatico(key)) {
          continue;
        }
        agregarCampoInput('nuevo-campos-container', key, plantilla.campos_json[key]);
        camposRenderizados += 1;
      }

      camposSection.style.display = camposRenderizados > 0 ? 'block' : 'none';
      if (camposRenderizados > 0) {
        inicializarTinyMceEnContenedor(container);
      }
    } else {
      camposSection.style.display = 'none';
    }
  } else {
    camposSection.style.display = 'none';
  }
}

function agregarCampoInput(containerId, key = '', descripcion = '') {
  const container = document.getElementById(containerId);
  const campoId = 'campo-' + Date.now();
  const campoDiv = document.createElement('div');
  campoDiv.className = 'mb-3 campo-item';
  campoDiv.id = campoId;
  campoDiv.innerHTML = `
    <label class="form-label">${key} ${descripcion ? '<small class="text-muted">(' + descripcion + ')</small>' : ''}</label>
    <textarea
      class="form-control campo-valor"
      data-campo-nombre="${key}"
      rows="5"
      placeholder="Ingrese ${key}"
    ></textarea>
  `;
  container.appendChild(campoDiv);
}

function removeCampoInput(campoId) {
  const campo = document.getElementById(campoId);
  if (campo) campo.remove();
}

function limpiarCamposContainer(containerId) {
  document.getElementById(containerId).innerHTML = '';
}

function getCamposAsJSON(containerId) {
  sincronizarTinyMce();
  const campos = {};
  document.querySelectorAll(`#${containerId} .campo-valor`).forEach(input => {
    const nombre = input.getAttribute('data-campo-nombre');
    const valor = normalizarValorCampo(input.value);
    if (nombre && !esCampoAutomatico(nombre)) campos[nombre] = valor;
  });
  return Object.keys(campos).length > 0 ? campos : null;
}

async function generarDocumento() {
  const asunto = document.getElementById('nuevo-asunto').value.trim();
  const plantillaId = parseInt(document.getElementById('nuevo-plantilla').value);
  const campos = getCamposAsJSON('nuevo-campos-container');
  const errBox = document.getElementById('nuevo-doc-error');
  errBox.classList.add('d-none');
  
  if (!asunto || !plantillaId) {
    errBox.textContent = 'Asunto y plantilla son requeridos';
    errBox.classList.remove('d-none');
    return;
  }
  
  // Obtener id_tipo de la plantilla seleccionada
  const plantilla = plantillasData.find(p => p.id === plantillaId);
  if (!plantilla || !plantilla.id_tipo) {
    errBox.textContent = 'No se pudo obtener el tipo de documento de la plantilla';
    errBox.classList.remove('d-none');
    return;
  }
  
  try {
    // Crear documento (se guarda en tabla dinámica automáticamente)
    const body = {
      id_tipo: plantilla.id_tipo,
      id_plantilla: plantillaId,
      asunto: asunto,
      valores_campos: campos
    };
    
    const respuesta = await api.request('/documentos/create', { method: 'POST', body });
    
    // Documento creado exitosamente
    modalNuevoDoc.hide();
    cargarDocumentos();
    
  } catch (err) {
    errBox.textContent = err.message;
    errBox.classList.remove('d-none');
  }
}

async function verDocumento(docId) {
  try {
    documentoActual = await api.request(`/documentos/${docId}`);
    
    // Rellenar datos básicos
    document.getElementById('ver-id').textContent = documentoActual.id;
    document.getElementById('ver-asunto').textContent = documentoActual.asunto;
    document.getElementById('ver-tipo').textContent = documentoActual.tipo_nombre || '';
    document.getElementById('ver-fecha').textContent = new Date(documentoActual.fecha_creacion).toLocaleString('es-ES');
    document.getElementById('ver-creador').textContent = documentoActual.usuario_nombre || '';
    
    // Badge de estado
    const estadoSpan = document.getElementById('ver-estado');
    const estadoClase = `estado-${documentoActual.estado.toLowerCase().replace(/_/g, '-')}`;
    estadoSpan.className = `estado-badge ${estadoClase}`;
    estadoSpan.textContent = documentoActual.estado.replace(/_/g, ' ');
    
    // Información de estado
    document.getElementById('ver-estado-info').innerHTML = `
      <strong>Estado actual:</strong> ${documentoActual.estado.replace(/_/g, ' ')}<br>
      <small class="text-muted">Creado: ${new Date(documentoActual.fecha_creacion).toLocaleString('es-ES')}</small>
      ${documentoActual.fecha_emision ? `<br><small class="text-muted">Emitido: ${new Date(documentoActual.fecha_emision).toLocaleString('es-ES')}</small>` : ''}
      ${documentoActual.consecutivo ? `<br><strong>Consecutivo: ${documentoActual.consecutivo}</strong>` : ''}
    `;
    
    // Descargas y generación de PDF
    const linkWord = document.getElementById('link-descargar-word');
    const linkPdf = document.getElementById('link-descargar-pdf');
    const btnGenerarPdf = document.getElementById('btn-generar-pdf');
    const sectionPreview = document.getElementById('section-preview');
    const previewLoading = document.getElementById('preview-loading');
    const iframePreview = document.getElementById('iframe-preview');
    
    // Generar Word si no existe
    if (!documentoActual.ruta_word_generado && documentoActual.estado !== 'BORRADOR') {
      try {
        sectionPreview.classList.remove('d-none');
        previewLoading.classList.remove('d-none');
        iframePreview.style.display = 'none';
        
        const respWordGen = await api.request(`/documentos/${docId}/generar-word`, { method: 'POST' });
        
        // Refrescar datos del documento
        documentoActual = await api.request(`/documentos/${docId}`);
      } catch (err) {
        console.warn('No se pudo generar Word automáticamente:', err);
      }
    }
    
    if (documentoActual.ruta_word_generado && documentoActual.estado !== 'FINALIZADO') {
      linkWord.href = API_BASE + documentoActual.ruta_word_generado;
      linkWord.classList.remove('d-none');
    } else {
      linkWord.classList.add('d-none');
    }
    
    if (documentoActual.ruta_pdf_final) {
      linkPdf.href = API_BASE + documentoActual.ruta_pdf_final;
      linkPdf.classList.remove('d-none');
      btnGenerarPdf.classList.add('d-none');
      
      // Mostrar previsualización del PDF
      sectionPreview.classList.remove('d-none');
      previewLoading.classList.add('d-none');
      iframePreview.style.display = 'block';
      iframePreview.src = API_BASE + documentoActual.ruta_pdf_final;
    } else if (documentoActual.ruta_word_generado && 
               (documentoActual.estado !== 'BORRADOR' && 
                documentoActual.estado !== 'DEVUELTO_JURIDICA' && 
                documentoActual.estado !== 'DEVUELTO_GERENCIA')) {
      // Mostrar previsualización con mensaje para estados en revisión/aprobación
      sectionPreview.classList.remove('d-none');
      previewLoading.innerHTML = '<div class="alert alert-info"><i class="bi bi-file-word"></i> Documento Word generado. Puede descargarlo con el botón arriba.</div>';
      previewLoading.classList.remove('d-none');
      iframePreview.style.display = 'none';
      linkPdf.classList.add('d-none');
      
      // Mostrar botón de generar PDF si está FINALIZADO y no hay PDF
      if (documentoActual.estado === 'FINALIZADO') {
        btnGenerarPdf.classList.remove('d-none');
      } else {
        btnGenerarPdf.classList.add('d-none');
      }
    } else {
      linkPdf.classList.add('d-none');
      sectionPreview.classList.add('d-none');
      // Mostrar botón de generar PDF si está FINALIZADO y no hay PDF
      if (documentoActual.estado === 'FINALIZADO') {
        btnGenerarPdf.classList.remove('d-none');
      } else {
        btnGenerarPdf.classList.add('d-none');
      }
    }
    
    // Limpiar secciones
    document.getElementById('section-editar-campos').classList.add('d-none');
    document.getElementById('section-acciones').classList.add('d-none');
    document.getElementById('section-observaciones').classList.add('d-none');
    document.getElementById('section-observaciones-historial').classList.add('d-none');
    document.getElementById('ver-doc-error').classList.add('d-none');
    document.getElementById('section-preview').classList.add('d-none');
    
    // Mostrar campos editables si está DEVUELTO
    if (documentoActual.estado === 'DEVUELTO_JURIDICA' || documentoActual.estado === 'DEVUELTO_GERENCIA') {
      await cargarObservacionesDocumento(documentoActual);
      await cargarCamposParaEditar(documentoActual);
    }
    
    // Obtener transiciones válidas
    try {
      const transiciones = await api.request(`/documentos/${docId}/transiciones`);
      mostrarAccionesDisponibles(transiciones.transiciones_validas);
    } catch (err) {
      console.warn('No se pudieron cargar transiciones:', err);
    }
    
    document.getElementById('modalVerDocTitle').textContent = `Documento #${documentoActual.id}`;
    modalVerDoc.show();
  } catch (err) {
    await ui.error(`Error al cargar documento: ${err.message}`);
  }
}

function mostrarAccionesDisponibles(transiciones) {
  const sectionAcciones = document.getElementById('section-acciones');
  const sectionObs = document.getElementById('section-observaciones');
  const sectionFirma = document.getElementById('section-firma');
  
  // Obtener rol actual del usuario
  let usuarioActual = null;
  try {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      usuarioActual = JSON.parse(userStr);
    }
  } catch (e) {
    console.warn('No se pudo obtener datos del usuario');
  }
  
  // Ocultar todas las acciones primero
  document.getElementById('btn-enviar-revision').classList.add('d-none');
  document.getElementById('btn-aprobar').classList.add('d-none');
  document.getElementById('btn-devolver').classList.add('d-none');
  document.getElementById('btn-firmar').classList.add('d-none');
  document.getElementById('btn-finalizar').classList.add('d-none');
  
  if (!transiciones || transiciones.length === 0) {
    sectionAcciones.classList.add('d-none');
    return;
  }
  
  sectionAcciones.classList.remove('d-none');
  sectionObs.classList.add('d-none');
  sectionFirma.classList.add('d-none');
  
  // Mostrar botones según las transiciones disponibles Y rol del usuario
  const estado = documentoActual.estado;
  const idRol = usuarioActual ? usuarioActual.id_rol : null;
  
  // Flujo: BORRADOR → EN_REVISION_JURIDICA → EN_REVISION_GERENCIAL → FIRMADO → FINALIZADO
  // Las aprobaciones (APROBADO_JURIDICA, APROBADO_GERENCIA) se hacen automáticamente
  
  if (estado === 'BORRADOR') {
    // Cualquiera puede enviar documento a revisión
    document.getElementById('btn-enviar-revision').classList.remove('d-none');
  } else if (estado === 'EN_REVISION_JURIDICA') {
    // Solo rol 3 (Jurídica) puede aprobar o devolver
    if (idRol === 3) {
      if (transiciones.includes('APROBADO_JURIDICA')) {
        document.getElementById('btn-aprobar').classList.remove('d-none');
      }
      if (transiciones.includes('DEVUELTO_JURIDICA')) {
        document.getElementById('btn-devolver').classList.remove('d-none');
      }
    }
  } else if (estado === 'EN_REVISION_GERENCIAL') {
    // Solo rol 2 (Gerencia) puede aprobar o devolver
    if (idRol === 2) {
      if (transiciones.includes('APROBADO_GERENCIA')) {
        document.getElementById('btn-aprobar').classList.remove('d-none');
      }
      if (transiciones.includes('DEVUELTO_GERENCIA')) {
        document.getElementById('btn-devolver').classList.remove('d-none');
      }
    }
  } else if (estado === 'DEVUELTO_JURIDICA') {
    // Rol 1/4 (Unidad) puede corregir y reenviar
    if (idRol === 1 || idRol === 4) {
      if (transiciones.includes('EN_REVISION_JURIDICA')) {
        document.getElementById('btn-enviar-revision').classList.remove('d-none');
      }
    }
  } else if (estado === 'DEVUELTO_GERENCIA') {
    // Rol 1/4 (Unidad) puede corregir y reenviar
    if (idRol === 1 || idRol === 4) {
      if (transiciones.includes('EN_REVISION_GERENCIAL') || transiciones.includes('EN_REVISION_JURIDICA')) {
        document.getElementById('btn-enviar-revision').classList.remove('d-none');
      }
    }
  } else if (estado === 'FIRMADO' || estado === 'PENDIENTE_FINALIZACION') {
    // Solo el creador puede finalizar
    const usuarioCreador = documentoActual ? documentoActual.usuario_genera : null;
    const usuarioId = usuarioActual ? usuarioActual.id_usuario : null;
    if (transiciones.includes('FINALIZADO') && usuarioCreador && usuarioId && usuarioCreador === usuarioId) {
      document.getElementById('btn-finalizar').classList.remove('d-none');
    }
  }
}

function mostrarSectionObservaciones() {
  document.getElementById('section-acciones').classList.add('d-none');
  document.getElementById('section-observaciones').classList.remove('d-none');
}

async function firmarDocumento() {
  try {
    // Obtener siguiente estado (el primero de las transiciones)
    const transiciones = await api.request(`/documentos/${documentoActual.id}/transiciones`);
    if (!transiciones.transiciones_validas || transiciones.transiciones_validas.length === 0) {
      throw new Error('No hay estados disponibles para este documento');
    }
    
    const nuevoEstado = transiciones.transiciones_validas[0];
    
    // Firmar documento
    const formData = new FormData();
    formData.append('nuevo_estado', nuevoEstado);
    
    const respuesta = await api.request(`/documentos/${documentoActual.id}/firmar`, { method: 'POST', body: formData });
    
    await ui.success(`Documento ${respuesta.nuevo_estado === 'FINALIZADO' ? 'finalizado' : 'actualizado'} correctamente`);
    
    modalVerDoc.hide();
    cargarDocumentos();
  } catch (err) {
    const errBox = document.getElementById('ver-doc-error');
    errBox.textContent = err.message;
    errBox.classList.remove('d-none');
  }
}

function mostrarSectionFirma() {
  document.getElementById('section-acciones').classList.add('d-none');
  document.getElementById('section-firma').classList.remove('d-none');
}

async function enviarARevision() {
  if (!(await ui.confirm('¿Enviar documento a revisión?'))) return;
  
  try {
    const transiciones = await api.request(`/documentos/${documentoActual.id}/transiciones`);
    const siguienteEstado = transiciones.transiciones_validas[0];
    
    if (!siguienteEstado) {
      throw new Error('No hay estados disponibles para este documento');
    }
    
    await api.request(`/documentos/${documentoActual.id}/estado`, {
      method: 'PUT',
      body: { nuevo_estado: siguienteEstado, descripcion_cambio: 'Enviado a revisión' }
    });
    
    await ui.success(`Documento enviado a ${siguienteEstado.replace(/_/g, ' ')}`);
    modalVerDoc.hide();
    cargarDocumentos();
  } catch (err) {
    await ui.error(`Error: ${err.message}`);
  }
}

async function aprobarDocumento() {
  if (!(await ui.confirm('¿Aprobar este documento?'))) return;
  
  try {
    const transiciones = await api.request(`/documentos/${documentoActual.id}/transiciones`);
    const siguienteEstado = transiciones.transiciones_validas.find(t => t.includes('APROBADO'));
    
    if (!siguienteEstado) {
      throw new Error('No hay estado de aprobación disponible');
    }
    
    await api.request(`/documentos/${documentoActual.id}/estado`, {
      method: 'PUT',
      body: { nuevo_estado: siguienteEstado, descripcion_cambio: 'Documento aprobado' }
    });
    
    // Recargar documento para mostrar el estado final (puede haber transición automática)
    const docActualizado = await api.request(`/documentos/${documentoActual.id}`);
    documentoActual = docActualizado;
    
    await ui.success(`Documento aprobado. Estado actual: ${documentoActual.estado.replace(/_/g, ' ')}`);
    modalVerDoc.hide();
    cargarDocumentos();
  } catch (err) {
    await ui.error(`Error: ${err.message}`);
  }
}

async function confirmarFirma() {
  const inputFirma = document.getElementById('input-firma');
  
  if (!inputFirma.files || inputFirma.files.length === 0) {
    await ui.warning('Seleccione una imagen de firma');
    return;
  }
  
  try {
    const formData = new FormData();
    formData.append('firma', inputFirma.files[0]);
    formData.append('nuevo_estado', 'FIRMADO');
    
    await api.request(`/documentos/${documentoActual.id}/firmar`, {
      method: 'POST',
      body: formData
    });
    
    await ui.success('Documento firmado correctamente');
    modalVerDoc.hide();
    cargarDocumentos();
  } catch (err) {
    await ui.error(`Error al firmar: ${err.message}`);
  }
}

async function finalizarDocumento() {
  if (!(await ui.confirm('¿Finalizar documento? Se asignará consecutivo y generará PDF final'))) return;
  
  try {
    await api.request(`/documentos/${documentoActual.id}/estado`, {
      method: 'PUT',
      body: { nuevo_estado: 'FINALIZADO', descripcion_cambio: 'Documento finalizado' }
    });
    
    await ui.success('Documento finalizado. Se ha asignado consecutivo y generado PDF');
    modalVerDoc.hide();
    cargarDocumentos();
  } catch (err) {
    await ui.error(`Error: ${err.message}`);
  }
}

async function devolverDocumento() {
  const observaciones = document.getElementById('textarea-observaciones').value.trim();
  if (!observaciones) {
    await ui.warning('Ingrese observaciones para devolver el documento');
    return;
  }

  const longitudTexto = obtenerLongitudTextoPlano(observaciones);
  if (longitudTexto < 10) {
    await ui.warning('La observacion debe tener al menos 10 caracteres');
    return;
  }
  
  try {
    const transiciones = await api.request(`/documentos/${documentoActual.id}/transiciones`);
    const estadoDevolucion = transiciones.transiciones_validas.find(t => t.includes('DEVUELTO'));
    
    if (!estadoDevolucion) {
      throw new Error('No se puede devolver desde este estado');
    }
    
    await api.request(`/documentos/${documentoActual.id}/estado`, {
      method: 'PUT',
      body: { nuevo_estado: estadoDevolucion, descripcion_cambio: observaciones }
    });
    
    await ui.success('Documento devuelto con observaciones');
    modalVerDoc.hide();
    cargarDocumentos();
  } catch (err) {
    await ui.error(`Error: ${err.message}`);
  }
}

async function cargarCamposParaEditar(documento) {
  try {
    const sectionEditar = document.getElementById('section-editar-campos');
    const container = document.getElementById('ver-campos-container');

    destruirTinyMceEnContenedor(container);
    
    // Obtener campos de la plantilla
    const plantilla = await api.request(`/plantillas/${documento.id_plantilla}`);
    
    if (!plantilla.campos_json || typeof plantilla.campos_json !== 'object' || Object.keys(plantilla.campos_json).length === 0) {
      container.innerHTML = '<p class="text-muted">Esta plantilla no tiene campos definidos.</p>';
      sectionEditar.classList.remove('d-none');
      return;
    }
    
    // Construir formulario con bloques verticales para mejorar legibilidad en modal
    let html = '<div class="campos-editables-stack">';
    
    // Iterar sobre los campos (campos_json es un objeto {'nombre_campo': 'tipo_dato'})
    let camposEditables = 0;
    for (const [nombre_campo, tipo_dato] of Object.entries(plantilla.campos_json)) {
      if (esCampoAutomatico(nombre_campo)) {
        continue;
      }

      const valor = documento.valores_campos && documento.valores_campos[nombre_campo] 
        ? documento.valores_campos[nombre_campo] 
        : '';
      
      let inputHtml = '';
      const tipoUpper = (tipo_dato || '').toString().toUpperCase();
      
      // Generar input según tipo de dato
      if (tipoUpper === 'TEXT') {
        inputHtml = `<textarea 
            class="form-control form-control-sm campo-editable" 
            name="${nombre_campo}" 
            rows="5"
          >${valor}</textarea>`;
      } else if (tipoUpper === 'VARCHAR') {
        inputHtml = `<textarea 
            class="form-control form-control-sm campo-editable" 
            name="${nombre_campo}" 
            rows="5"
          >${valor}</textarea>`;
      } else if (tipoUpper === 'INT' || tipoUpper === 'DECIMAL' || tipoUpper === 'FLOAT') {
        inputHtml = `<input 
            type="number" 
            step="${tipoUpper === 'INT' ? '1' : '0.01'}"
            class="form-control form-control-sm campo-editable" 
            name="${nombre_campo}" 
            value="${valor}"
          />`;
      } else if (tipoUpper === 'DATE') {
        inputHtml = `<input 
            type="date" 
            class="form-control form-control-sm campo-editable" 
            name="${nombre_campo}" 
            value="${valor}"
          />`;
      } else if (tipoUpper === 'DATETIME') {
        inputHtml = `<input 
            type="datetime-local" 
            class="form-control form-control-sm campo-editable" 
            name="${nombre_campo}" 
            value="${valor}"
          />`;
      } else {
        inputHtml = `<textarea 
          class="form-control form-control-sm campo-editable" 
            name="${nombre_campo}" 
            rows="5"
          >${valor}</textarea>`;
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
    console.error('Error al cargar campos:', err);
    await ui.error('Error al cargar campos editables');
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
    
    const items = observaciones.map(obs => {
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
    console.warn('No se pudieron cargar observaciones:', err);
  }
}

async function guardarCamposDocumento() {
  try {
    if (!documentoActual) return;

    sincronizarTinyMce();
    
    // Recopilar valores de los campos
    const campos = document.querySelectorAll('.campo-editable');
    const valores_campos = {};
    
    campos.forEach(campo => {
      valores_campos[campo.name] = normalizarValorCampo(campo.value);
    });
    
    console.log('Guardando valores_campos:', valores_campos);
    
    // Validar que hay campos
    if (Object.keys(valores_campos).length === 0) {
      await ui.warning('No hay campos para actualizar');
      return;
    }
    
    // Actualizar documento
    const response = await api.request(`/documentos/${documentoActual.id}`, {
      method: 'PUT',
      body: { valores_campos }
    });
    
    console.log('Respuesta actualización:', response);
    await ui.success('Campos actualizados correctamente');
    
    // Regenerar Word con nuevos datos
    try {
      await api.request(`/documentos/${documentoActual.id}/generar-word`, { method: 'POST' });
    } catch (err) {
      console.warn('No se pudo regenerar Word:', err);
    } finally {
      // Refrescar documento para mostrar acciones disponibles
      await verDocumento(documentoActual.id);
    }
    
  } catch (err) {
    console.error('Error completo:', err);
    await ui.error(`Error al guardar campos: ${err.message}`);
  }
}

