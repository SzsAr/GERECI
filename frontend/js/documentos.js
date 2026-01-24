(function guardAuth() {
  const token = localStorage.getItem('token');
  if (!token) window.location.href = './index.html';
})();

let modalNuevoDoc, modalVerDoc;
let documentoActual = null;
let plantillasData = []; // Almacenar datos completos de plantillas

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
  
  document.getElementById('btn-filtrar').addEventListener('click', () => {
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
  
  document.getElementById('btn-aprobar-firmar').addEventListener('click', () => {
    firmarDocumento();
  });
  
  document.getElementById('btn-devolver').addEventListener('click', () => {
    mostrarSectionObservaciones();
  });
  
  document.getElementById('btn-enviar-observaciones').addEventListener('click', () => {
    devolverDocumento();
  });
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
  const asunto = document.getElementById('filtro-asunto').value.trim();
  const tbody = document.querySelector('#tabla-documentos');
  
  tbody.innerHTML = '<tr><td colspan="8" class="text-muted text-center py-3">Cargando...</td></tr>';
  
  try {
    let url = '/documentos';
    const params = [];
    if (estado) params.push(`estado=${encodeURIComponent(estado)}`);
    if (url.includes('?')) url += '&' + params.join('&');
    else if (params.length) url += '?' + params.join('&');
    
    const docs = await api.request(url);
    
    if (!docs || docs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4"><div class="alert alert-info mb-0"><i class="bi bi-info-circle"></i> No hay documentos para mostrar. Crea uno nuevo con el botón <strong>Nuevo</strong></div></td></tr>';
      return;
    }
    
    tbody.innerHTML = docs.map(d => {
      const estadoClase = `estado-${d.estado.toLowerCase().replace(/_/g, '-')}`;
      const linkWord = d.ruta_word_generado ? `<a href="${API_BASE}${d.ruta_word_generado}" target="_blank" class="btn btn-sm btn-info"><i class="bi bi-file-word"></i></a>` : '';
      const linkPdf = d.ruta_pdf_final ? `<a href="${API_BASE}${d.ruta_pdf_final}" target="_blank" class="btn btn-sm btn-danger"><i class="bi bi-file-pdf"></i></a>` : '';
      
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
    
    bindDocumentoActions();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4"><div class="alert alert-danger mb-0"><i class="bi bi-exclamation-triangle"></i> Error al cargar documentos: ${err.message}</div></td></tr>`;
  }
}

function bindDocumentoActions() {
  document.querySelectorAll('[data-ver-doc]').forEach(btn => {
    btn.addEventListener('click', () => {
      const docId = btn.dataset.verDoc;
      verDocumento(parseInt(docId));
    });
  });
  
  document.querySelectorAll('[data-eliminar-doc]').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('¿Eliminar documento?')) return;
      const docId = btn.dataset.eliminarDoc;
      try {
        await api.request(`/documentos/${docId}`, { method: 'DELETE' });
        cargarDocumentos();
      } catch (err) {
        alert(`Error: ${err.message}`);
      }
    });
  });
}

function abrirModalNuevoDoc() {
  document.getElementById('form-nuevo-doc').reset();
  document.getElementById('nuevo-doc-error').classList.add('d-none');
  document.getElementById('nuevo-campos-container').innerHTML = '';
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
    const campos = Object.keys(plantilla.campos_json);
    if (campos.length > 0) {
      camposSection.style.display = 'block';
      campos.forEach(key => {
        agregarCampoInput('nuevo-campos-container', key, plantilla.campos_json[key]);
      });
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
    <input type="text" class="form-control campo-valor" data-campo-nombre="${key}" placeholder="Ingrese ${key}">
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
  const campos = {};
  document.querySelectorAll(`#${containerId} .campo-valor`).forEach(input => {
    const nombre = input.getAttribute('data-campo-nombre');
    const valor = input.value.trim();
    if (nombre) campos[nombre] = valor;
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
    // Crear documento
    const body = {
      id_tipo: plantilla.id_tipo,
      id_plantilla: plantillaId,
      asunto: asunto,
      valores_campos: campos
    };
    
    const respuesta = await api.request('/documentos/create', { method: 'POST', body });
    const docId = respuesta.documento_id;
    
    // Generar Word desde plantilla
    await api.request(`/documentos/${docId}/generar`, { method: 'POST' });
    
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
    
    // Descargas
    const linkWord = document.getElementById('link-descargar-word');
    const linkPdf = document.getElementById('link-descargar-pdf');
    if (documentoActual.ruta_word_generado) {
      linkWord.href = API_BASE + documentoActual.ruta_word_generado;
      linkWord.classList.remove('d-none');
    } else {
      linkWord.classList.add('d-none');
    }
    if (documentoActual.ruta_pdf_final) {
      linkPdf.href = API_BASE + documentoActual.ruta_pdf_final;
      linkPdf.classList.remove('d-none');
    } else {
      linkPdf.classList.add('d-none');
    }
    
    // Limpiar secciones
    document.getElementById('section-editar-campos').classList.add('d-none');
    document.getElementById('section-acciones').classList.add('d-none');
    document.getElementById('section-observaciones').classList.add('d-none');
    document.getElementById('ver-doc-error').classList.add('d-none');
    
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
    alert(`Error al cargar documento: ${err.message}`);
  }
}

function mostrarAccionesDisponibles(transiciones) {
  const sectionAcciones = document.getElementById('section-acciones');
  const btnAprobar = document.getElementById('btn-aprobar-firmar');
  const btnDevolver = document.getElementById('btn-devolver');
  const sectionObs = document.getElementById('section-observaciones');
  
  if (!transiciones || transiciones.length === 0) {
    sectionAcciones.classList.add('d-none');
    return;
  }
  
  sectionAcciones.classList.remove('d-none');
  sectionObs.classList.add('d-none');
  
  // Mostrar botón "Aprobar" si hay transiciones
  const esAprobacion = transiciones.some(t => t.includes('APROBADO') || t === 'FIRMADO' || t === 'PENDIENTE_FINALIZACION');
  const esDevolucion = transiciones.some(t => t.includes('DEVUELTO'));
  
  if (esAprobacion) {
    btnAprobar.classList.remove('d-none');
  } else {
    btnAprobar.classList.add('d-none');
  }
  
  if (esDevolucion) {
    btnDevolver.classList.remove('d-none');
  } else {
    btnDevolver.classList.add('d-none');
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
    
    alert(`Documento ${respuesta.nuevo_estado === 'FINALIZADO' ? 'finalizado' : 'actualizado'} correctamente`);
    
    modalVerDoc.hide();
    cargarDocumentos();
  } catch (err) {
    const errBox = document.getElementById('ver-doc-error');
    errBox.textContent = err.message;
    errBox.classList.remove('d-none');
  }
}

async function devolverDocumento() {
  const observaciones = document.getElementById('textarea-observaciones').value.trim();
  if (!observaciones) {
    alert('Ingrese observaciones para devolver el documento');
    return;
  }
  
  try {
    // Para ahora, solo marcamos que hay observaciones y devolvemos a BORRADOR
    // Se puede extender para guardar en tabla observaciones
    await api.request(`/documentos/${documentoActual.id}/estado`, {
      method: 'PUT',
      body: { nuevo_estado: 'BORRADOR', descripcion_cambio: observaciones }
    });
    
    alert('Documento devuelto con observaciones');
    modalVerDoc.hide();
    cargarDocumentos();
  } catch (err) {
    const errBox = document.getElementById('ver-doc-error');
    errBox.textContent = err.message;
    errBox.classList.remove('d-none');
  }
}

async function guardarCamposDocumento() {
  // Esta función podría guardar campos dinámicos del documento
  // Por ahora solo muestra un mensaje
  alert('Funcionalidad en desarrollo');
}

document.addEventListener('layout:navbarReady', bindLogout);
