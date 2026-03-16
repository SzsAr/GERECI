(function guardAuth() {
  const token = localStorage.getItem('token');
  if (!token) window.location.href = './index.html';
})();

let modalRol, modalCargo, modalUsuario, modalPlantilla, modalUploadPlantilla;

function showSection(section) {
  document.querySelectorAll('.section').forEach(s => s.classList.add('d-none'));
  const el = document.getElementById(`section-${section}`);
  if (el) el.classList.remove('d-none');
  document.querySelectorAll('#admin-menu a').forEach(a => a.classList.remove('active'));
  const active = document.querySelector(`#admin-menu a[data-section="${section}"]`);
  if (active) active.classList.add('active');
  
  // Limpiar mensajes de error cuando se cambia de sección
  document.querySelectorAll('[id$="-error"]').forEach(el => el.classList.add('d-none'));
}

function bindMenu() {
  document.querySelectorAll('#admin-menu a').forEach(a => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      const sec = a.dataset.section;
      showSection(sec);
      if (sec === 'roles') loadRoles();
      if (sec === 'cargos') loadCargos();
      if (sec === 'usuarios') loadUsuarios();
      if (sec === 'plantillas') loadPlantillas();
    });
  });
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

async function loadRoles() {
  const tbody = document.querySelector('#tabla-roles tbody');
  tbody.innerHTML = '<tr><td colspan="4" class="text-muted small">Cargando...</td></tr>';
  try {
    const data = await api.request('/roles');
    if (!data || data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="text-muted small">Sin datos</td></tr>';
      return;
    }
    tbody.innerHTML = data.map(r => `
      <tr>
        <td>${r.id}</td>
        <td>${r.nombre}</td>
        <td>
          <div class="form-check form-switch">
            <input class="form-check-input role-estado-switch" type="checkbox" data-role-id="${r.id}" ${r.estado ? 'checked' : ''}>
            <label class="form-check-label small">${r.estado ? 'Activo' : 'Inactivo'}</label>
          </div>
        </td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-primary me-1" data-edit-rol="${r.id}" data-nombre="${r.nombre}" data-estado="${r.estado}"><i class="bi bi-pencil"></i></button>
          <button class="btn btn-sm btn-outline-danger" data-del-rol="${r.id}"><i class="bi bi-trash"></i></button>
        </td>
      </tr>
    `).join('');
    bindRoleActions();
    bindRoleStateSwitch();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-danger small">Error: ${err.message}</td></tr>`;
  }
}

function bindRoleActions() {
  document.querySelectorAll('[data-edit-rol]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.editRol;
      const nombre = btn.dataset.nombre;
      document.getElementById('rol-id').value = id;
      document.getElementById('rol-nombre').value = nombre;
      document.getElementById('modalRolTitle').textContent = 'Editar rol';
      document.getElementById('rol-error').classList.add('d-none');
      modalRol.show();
    });
  });

  document.querySelectorAll('[data-del-rol]').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('¿Eliminar rol?')) return;
      const id = btn.dataset.delRol;
      try {
        await api.request(`/roles/${id}`, { method: 'DELETE' });
        loadRoles();
      } catch (err) {
        alert(err.message);
      }
    });
  });
}

function bindRoleStateSwitch() {
  document.querySelectorAll('.role-estado-switch').forEach(sw => {
    sw.addEventListener('change', async () => {
      const id = sw.dataset.roleId;
      const nuevoEstado = sw.checked ? 1 : 0;
      const label = sw.closest('.form-check')?.querySelector('.form-check-label');
      try {
        await api.request(`/roles/${id}`, { method: 'PUT', body: { estado: nuevoEstado } });
        if (label) label.textContent = nuevoEstado ? 'Activo' : 'Inactivo';
      } catch (err) {
        // En caso de error, dejar el rol activo y alertar
        sw.checked = true;
        if (label) label.textContent = 'Activo';
        alert(`No se pudo cambiar el estado del rol (ID ${id}). El rol permanece activo.\nDetalle: ${err.message}`);
      }
    });
  });
}

async function saveRol() {
  const id = document.getElementById('rol-id').value;
  const nombre = document.getElementById('rol-nombre').value.trim();
  const errBox = document.getElementById('rol-error');
  errBox.classList.add('d-none');

  if (!nombre) {
    errBox.textContent = 'Nombre requerido';
    errBox.classList.remove('d-none');
    return;
  }

  try {
    if (id) {
      await api.request(`/roles/${id}`, { method: 'PUT', body: { nombre } });
    } else {
      await api.request('/roles', { method: 'POST', body: { nombre, estado: 1 } });
    }
    modalRol.hide();
    loadRoles();
  } catch (err) {
    errBox.textContent = err.message;
    errBox.classList.remove('d-none');
  }
}

// CARGOS
async function loadCargos() {
  const tbody = document.querySelector('#tabla-cargos tbody');
  tbody.innerHTML = '<tr><td colspan="4" class="text-muted small">Cargando...</td></tr>';
  try {
    const data = await api.request('/cargos');
    if (!data || data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="text-muted small">Sin datos</td></tr>';
      return;
    }
    tbody.innerHTML = data.map(c => `
      <tr>
        <td>${c.id}</td>
        <td>${c.nombre}</td>
        <td>${c.descripcion || ''}</td>
        <td>
          <div class="form-check form-switch">
            <input class="form-check-input cargo-estado-switch" type="checkbox" data-cargo-id="${c.id}" ${c.estado ? 'checked' : ''}>
            <label class="form-check-label small">${c.estado ? 'Activo' : 'Inactivo'}</label>
          </div>
        </td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-primary me-1" data-edit-cargo="${c.id}" data-nombre="${c.nombre}" data-desc="${c.descripcion || ''}"><i class="bi bi-pencil"></i></button>
          <button class="btn btn-sm btn-outline-danger" data-del-cargo="${c.id}"><i class="bi bi-trash"></i></button>
        </td>
      </tr>
    `).join('');
    bindCargoActions();
    bindCargoStateSwitch();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-danger small">Error: ${err.message}</td></tr>`;
  }
}

function bindCargoActions() {
  document.querySelectorAll('[data-edit-cargo]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.editCargo;
      const nombre = btn.dataset.nombre;
      const desc = btn.dataset.desc;
      document.getElementById('cargo-id').value = id;
      document.getElementById('cargo-nombre').value = nombre;
      document.getElementById('cargo-desc').value = desc;
      document.getElementById('modalCargoTitle').textContent = 'Editar cargo';
      document.getElementById('cargo-error').classList.add('d-none');
      modalCargo.show();
    });
  });

  document.querySelectorAll('[data-del-cargo]').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('¿Eliminar cargo?')) return;
      const id = btn.dataset.delCargo;
      try {
        await api.request(`/cargos/${id}`, { method: 'DELETE' });
        loadCargos();
      } catch (err) {
        alert(err.message);
      }
    });
  });
}

function bindCargoStateSwitch() {
  document.querySelectorAll('.cargo-estado-switch').forEach(sw => {
    sw.addEventListener('change', async () => {
      const id = sw.dataset.cargoId;
      const nuevoEstado = sw.checked ? 1 : 0;
      const label = sw.closest('.form-check')?.querySelector('.form-check-label');
      try {
        await api.request(`/cargos/${id}`, { method: 'PUT', body: { estado: nuevoEstado } });
        if (label) label.textContent = nuevoEstado ? 'Activo' : 'Inactivo';
      } catch (err) {
        sw.checked = true;
        if (label) label.textContent = 'Activo';
        alert(`No se pudo cambiar el estado del cargo (ID ${id}). El cargo permanece activo.\nDetalle: ${err.message}`);
      }
    });
  });
}

async function saveCargo() {
  const id = document.getElementById('cargo-id').value;
  const nombre = document.getElementById('cargo-nombre').value.trim();
  const descripcion = document.getElementById('cargo-desc').value.trim();
  const errBox = document.getElementById('cargo-error');
  errBox.classList.add('d-none');

  if (!nombre) {
    errBox.textContent = 'Nombre requerido';
    errBox.classList.remove('d-none');
    return;
  }

  try {
    if (id) {
      await api.request(`/cargos/${id}`, { method: 'PUT', body: { nombre, descripcion } });
    } else {
      await api.request('/cargos', { method: 'POST', body: { nombre, descripcion, estado: 1 } });
    }
    modalCargo.hide();
    loadCargos();
  } catch (err) {
    errBox.textContent = err.message;
    errBox.classList.remove('d-none');
  }
}

// USUARIOS
async function loadUsuarios() {
  const tbody = document.querySelector('#tabla-usuarios tbody');
  tbody.innerHTML = '<tr><td colspan="8" class="text-muted small">Cargando...</td></tr>';
  try {
    const data = await api.request('/users/all');
    if (!data || data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-muted small">Sin datos</td></tr>';
      return;
    }
    tbody.innerHTML = data.map(u => `
      <tr>
        <td>${u.id_usuario}</td>
        <td>${u.nombre}</td>
        <td>${u.username}</td>
        <td>${u.rol_nombre || u.id_rol || ''}</td>
        <td>${u.cargo_nombre || u.id_cargo || ''}</td>
        <td>
          <div class="form-check form-switch">
            <input class="form-check-input usuario-estado-switch" type="checkbox" data-usuario-id="${u.id_usuario}" ${u.estado ? 'checked' : ''}>
            <label class="form-check-label small">${u.estado ? 'Activo' : 'Inactivo'}</label>
          </div>
        </td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-warning me-1" data-pdf-usuario="${u.id_usuario}" title="Descargar PDF"><i class="bi bi-file-pdf"></i></button>
          <button class="btn btn-sm btn-outline-primary me-1" data-edit-usuario="${u.id_usuario}"><i class="bi bi-pencil"></i></button>
          <button class="btn btn-sm btn-outline-danger" data-del-usuario="${u.id_usuario}"><i class="bi bi-trash"></i></button>
        </td>
      </tr>
    `).join('');
    bindUserActions();
    bindUserStateSwitch();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-danger small">Error: ${err.message}</td></tr>`;
  }
}

function bindUserStateSwitch() {
  document.querySelectorAll('.usuario-estado-switch').forEach(sw => {
    sw.addEventListener('change', async () => {
      const id = sw.dataset.usuarioId;
      const nuevoEstado = sw.checked ? 1 : 0;
      const label = sw.closest('.form-check')?.querySelector('.form-check-label');
      try {
        await api.request(`/users/${id}/inactivar`, { method: 'PUT' });
        if (label) label.textContent = nuevoEstado ? 'Activo' : 'Inactivo';
      } catch (err) {
        sw.checked = !sw.checked;
        if (label) label.textContent = sw.checked ? 'Activo' : 'Inactivo';
        alert(`No se pudo cambiar el estado del usuario (ID ${id}).\nDetalle: ${err.message}`);
      }
    });
  });
}

function bindUserActions() {
  document.querySelectorAll('[data-pdf-usuario]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id = btn.dataset.pdfUsuario;
      try {
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i>';
        
        // Endpoint Jasper eliminado
        alert('Funcionalidad de PDF temporalmente deshabilitada');
        return;
        
        // Descargar el PDF
        if (respuesta.pdf_url) {
          const link = document.createElement('a');
          link.href = API_BASE + respuesta.pdf_url;
          link.download = `usuario_${id}.pdf`;
          link.click();
          alert('PDF descargado correctamente');
        }
      } catch (err) {
        alert(`Error generando PDF: ${err.message}`);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-file-pdf"></i>';
      }
    });
  });

  document.querySelectorAll('[data-del-usuario]').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('¿Eliminar usuario?')) return;
      const id = btn.dataset.delUsuario;
      try {
        await api.request(`/users/${id}`, { method: 'DELETE' });
        loadUsuarios();
      } catch (err) {
        alert(err.message);
      }
    });
  });

  document.querySelectorAll('[data-edit-usuario]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id = btn.dataset.editUsuario;
      try {
        const usuario = await api.request(`/users/id/${id}`);
        document.getElementById('usuario-id').value = usuario.id_usuario;
        document.getElementById('usuario-nombre').value = usuario.nombre;
        document.getElementById('usuario-documento').value = usuario.documento;
        document.getElementById('usuario-username').value = usuario.username;
        document.getElementById('usuario-rol').value = usuario.id_rol;
        document.getElementById('usuario-cargo').value = usuario.id_cargo || '';
        document.getElementById('usuario-password').value = '';
        
        // Mostrar firma actual si existe
        const previewContainer = document.getElementById('firma-preview-container');
        const previewNewContainer = document.getElementById('firma-preview-new');
        const firmaInput = document.getElementById('usuario-firma');
        
        if (usuario.firma) {
          const firmaUrl = usuario.firma.startsWith('http') ? usuario.firma : `${API_BASE}${usuario.firma}`;
          document.getElementById('firma-preview').src = firmaUrl;
          previewContainer.classList.remove('d-none');
        } else {
          previewContainer.classList.add('d-none');
        }
        
        // Limpiar preview de nueva firma
        previewNewContainer.classList.add('d-none');
        firmaInput.value = '';
        
        document.getElementById('modalUsuarioTitle').textContent = 'Editar usuario';
        document.getElementById('usuario-error').classList.add('d-none');
        modalUsuario.show();
      } catch (err) {
        alert(`Error al cargar usuario: ${err.message}`);
      }
    });
  });
}

async function loadPlantillas() {
  const tbody = document.querySelector('#tabla-plantillas tbody');
  tbody.innerHTML = '<tr><td colspan="5" class="text-muted small">Cargando...</td></tr>';
  try {
    const data = await api.request('/plantillas');
    if (!data || data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-muted small">Sin datos</td></tr>';
      return;
    }
    tbody.innerHTML = data.map(p => {
      const camposCount = p.campos_json ? Object.keys(p.campos_json).length : 0;
      const tieneArchivo = p.nombre_archivo ? true : false;
      const iconoArchivo = tieneArchivo 
        ? '<i class="bi bi-file-earmark-check text-success"></i>' 
        : '<i class="bi bi-file-earmark-x text-muted"></i>';
      const textoArchivo = tieneArchivo 
        ? `<small class="text-success">Archivo: ${p.nombre_archivo}</small>` 
        : '<small class="text-muted">Sin archivo</small>';
      
      return `
      <tr>
        <td>
          <div>${p.nombre}</div>
          <div>${iconoArchivo} ${textoArchivo}</div>
        </td>
        <td>${p.tipo_nombre || p.id_tipo}</td>
        <td><span class="badge bg-info">${camposCount} campos</span></td>
        <td><span class="badge bg-success">Activa</span></td>
        <td class="text-end">
          <button class="btn btn-sm ${tieneArchivo ? 'btn-outline-warning' : 'btn-outline-info'} me-1" 
                  data-upload-plantilla="${p.id}" 
                  data-tiene-archivo="${tieneArchivo}"
                  data-nombre-archivo="${p.nombre_archivo || ''}"
                  title="${tieneArchivo ? 'Reemplazar archivo .docx' : 'Subir archivo .docx'}">
            <i class="bi ${tieneArchivo ? 'bi-arrow-repeat' : 'bi-file-arrow-up'}"></i>
          </button>
          <button class="btn btn-sm btn-outline-primary me-1" data-edit-plantilla="${p.id}"><i class="bi bi-pencil"></i></button>
          <button class="btn btn-sm btn-outline-danger" data-del-plantilla="${p.id}"><i class="bi bi-trash"></i></button>
        </td>
      </tr>
    `}).join('');
    bindPlantillaActions();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-danger small">Error: ${err.message}</td></tr>`;
  }
}

async function saveUsuario() {
  const id = document.getElementById('usuario-id').value;
  const nombre = document.getElementById('usuario-nombre').value.trim();
  const documento = document.getElementById('usuario-documento').value.trim();
  const username = document.getElementById('usuario-username').value.trim();
  const id_rol = parseInt(document.getElementById('usuario-rol').value);
  const id_cargo = document.getElementById('usuario-cargo').value ? parseInt(document.getElementById('usuario-cargo').value) : null;
  const password = document.getElementById('usuario-password').value.trim();
  const firmaInput = document.getElementById('usuario-firma');
  const errBox = document.getElementById('usuario-error');
  errBox.classList.add('d-none');

  if (!nombre || !documento || !username || !id_rol) {
    errBox.textContent = 'Nombre, documento, usuario y rol son requeridos';
    errBox.classList.remove('d-none');
    return;
  }

  try {
    let usuarioId = id;
    
    if (id) {
      // Editar usuario
      const body = { nombre, documento, username, id_rol, id_cargo };
      if (password) body.pass_hash = password;
      await api.request(`/users/${id}`, { method: 'PUT', body });
    } else {
      // Crear usuario - password es requerido
      if (!password) {
        errBox.textContent = 'Contraseña requerida para crear nuevo usuario';
        errBox.classList.remove('d-none');
        return;
      }
      const body = { nombre, documento, username, id_rol, id_cargo, pass_hash: password, estado: true };
      const respuesta = await api.request('/users/create', { method: 'POST', body });
      usuarioId = respuesta.id_usuario || respuesta.id;
    }
    
    // Subir firma si se seleccionó un archivo
    if (firmaInput.files && firmaInput.files.length > 0) {
      const formData = new FormData();
      formData.append('file', firmaInput.files[0]);
      
      try {
        await fetch(`${API_BASE}/users/${usuarioId}/firma`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
          body: formData
        });
      } catch (err) {
        errBox.textContent = `Usuario guardado, pero error al cargar firma: ${err.message}`;
        errBox.classList.remove('d-none');
      }
    }
    
    modalUsuario.hide();
    loadUsuarios();
  } catch (err) {
    errBox.textContent = err.message;
    errBox.classList.remove('d-none');
  }
}

async function loadRolesAndCargos() {
  try {
    const roles = await api.request('/roles?solo_activos=true');
    const cargos = await api.request('/cargos?solo_activos=true');
    
    const rolSelect = document.getElementById('usuario-rol');
    const cargoSelect = document.getElementById('usuario-cargo');
    
    rolSelect.innerHTML = roles.map(r => `<option value="${r.id}">${r.nombre}</option>`).join('');
    cargoSelect.innerHTML = '<option value="">Sin cargo</option>' + cargos.map(c => `<option value="${c.id}">${c.nombre}</option>`).join('');
  } catch (err) {
    console.error('Error cargando roles/cargos:', err);
  }
}

async function loadTiposDocumentos() {
  try {
    const tipos = await api.request('/tipos-documentos');
    const tipoSelect = document.getElementById('plantilla-tipo');
    tipoSelect.innerHTML = '<option value="">Seleccione...</option>' + tipos.map(t => `<option value="${t.id}">${t.nombre}</option>`).join('');
  } catch (err) {
    console.error('Error cargando tipos de documentos:', err);
  }
}

// Todos los campos se crean como tipo 'text' para simplificar UX
function addCampoInput(nombre = '', tipo = 'text') {
  const container = document.getElementById('plantilla-campos-container');
  const campoId = 'campo-' + Date.now();
  const campoDiv = document.createElement('div');
  campoDiv.className = 'row mb-2 campo-item';
  campoDiv.id = campoId;
  campoDiv.innerHTML = `
    <div class="col-10">
      <input type="text" class="form-control form-control-sm campo-nombre" placeholder="Nombre del campo (ej: asunto, descripción, número)" value="${nombre}">
      <input type="hidden" class="campo-tipo" value="text">
    </div>
    <div class="col-2 d-flex justify-content-end">
      <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeCampoInput('${campoId}')">
        <i class="bi bi-trash"></i>
      </button>
    </div>
  `;
  container.appendChild(campoDiv);
}

function removeCampoInput(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function clearCampos() {
  document.getElementById('plantilla-campos-container').innerHTML = '';
}

function getCamposAsJSON() {
  const campos = {};
  document.querySelectorAll('.campo-item').forEach(item => {
    const nombre = item.querySelector('.campo-nombre').value.trim();
    const tipo = item.querySelector('.campo-tipo').value; // Siempre será 'text'
    if (nombre) {
      campos[nombre] = tipo;
    }
  });
  return Object.keys(campos).length > 0 ? campos : null;
}

function loadCamposFromJSON(camposJson) {
  clearCampos();
  if (camposJson && typeof camposJson === 'object') {
    Object.entries(camposJson).forEach(([nombre, tipo]) => {
      addCampoInput(nombre, tipo);
    });
  }
}
  

async function uploadPlantillaArchivo() {
  const plantillaId = document.getElementById('upload-plantilla-id').value;
  const archivo = document.getElementById('upload-plantilla-archivo').files[0];
  const errBox = document.getElementById('upload-plantilla-error');
  const btnText = document.getElementById('upload-btn-text');
  const btnLoading = document.getElementById('upload-btn-loading');
  const btn = document.getElementById('upload-plantilla-save');

  errBox.classList.add('d-none');

  if (!archivo) {
    errBox.textContent = 'Debes seleccionar un archivo';
    errBox.classList.remove('d-none');
    return;
  }

  if (!archivo.name.toLowerCase().endsWith('.docx')) {
    errBox.textContent = 'El archivo debe ser .docx';
    errBox.classList.remove('d-none');
    return;
  }

  try {
    // Mostrar loading
    btn.disabled = true;
    btnText.classList.add('d-none');
    btnLoading.classList.remove('d-none');

    // Crear FormData para enviar archivo
    const formData = new FormData();
    formData.append('archivo', archivo);

    // Hacer request directo con fetch (api.request no soporta FormData bien)
    const token = localStorage.getItem('token');
    const baseUrl = api.baseUrl || 'http://localhost:8000';
    const response = await fetch(
      `${baseUrl}/plantillas/${plantillaId}/upload-archivo`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error al subir archivo (${response.status})`);
    }

    const result = await response.json();

    // Mostrar éxito
    errBox.textContent = '';
    errBox.classList.add('d-none');
    
    // Cerrar modal y recargar
    modalUploadPlantilla.hide();
    loadPlantillas();

    // Mostrar mensaje de éxito
    alert('Archivo subido correctamente: ' + result.nombre_archivo);

  } catch (err) {
    errBox.textContent = err.message;
    errBox.classList.remove('d-none');
  } finally {
    // Esconder loading
    btn.disabled = false;
    btnText.classList.remove('d-none');
    btnLoading.classList.add('d-none');
  }
}

function bindPlantillaActions() {
  // Upload archivo
  document.querySelectorAll('[data-upload-plantilla]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.uploadPlantilla;
      const tieneArchivo = btn.dataset.tieneArchivo === 'true';
      const nombreArchivoActual = btn.dataset.nombreArchivo || '';
      const row = btn.closest('tr');
      const nombre = row.querySelector('td:first-child div:first-child').textContent;
      
      document.getElementById('upload-plantilla-id').value = id;
      document.getElementById('upload-plantilla-archivo').value = '';
      document.getElementById('upload-plantilla-error').classList.add('d-none');
      
      // Actualizar el título del modal
      const modalTitle = tieneArchivo 
        ? `Reemplazar archivo en: ${nombre}`
        : `Subir archivo a: ${nombre}`;
      document.querySelector('#modalUploadPlantilla .modal-title').textContent = modalTitle;
      
      // Mostrar información si ya tiene archivo
      const infoArchivoDiv = document.getElementById('info-archivo-actual');
      if (tieneArchivo && nombreArchivoActual) {
        infoArchivoDiv.innerHTML = `
          <div class="alert alert-warning" role="alert">
            <i class="bi bi-exclamation-triangle"></i> 
            <strong>Esta plantilla ya tiene un archivo:</strong> 
            <code>${nombreArchivoActual}</code>
            <br><small>Si subes un nuevo archivo, reemplazará el actual.</small>
          </div>
        `;
        infoArchivoDiv.classList.remove('d-none');
      } else {
        infoArchivoDiv.innerHTML = '';
        infoArchivoDiv.classList.add('d-none');
      }
      
      modalUploadPlantilla.show();
    });
  });

  document.querySelectorAll('[data-del-plantilla]').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('¿Eliminar plantilla y su tabla de datos? Esta acción es irreversible.')) return;
      const id = btn.dataset.delPlantilla;
      try {
        await api.request(`/plantillas/${id}`, { method: 'DELETE' });
        loadPlantillas();
      } catch (err) {
        alert(err.message);
      }
    });
  });

  document.querySelectorAll('[data-edit-plantilla]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id = btn.dataset.editPlantilla;
      try {
        const plantilla = await api.request(`/plantillas/${id}`);
        document.getElementById('plantilla-id').value = plantilla.id;
        document.getElementById('plantilla-nombre').value = plantilla.nombre;
        document.getElementById('plantilla-descripcion').value = ''; // Campo descripcion no está en BD
        document.getElementById('plantilla-tipo').value = plantilla.id_tipo;
        document.getElementById('plantilla-tipo').disabled = true; // No permitir cambiar tipo
        loadCamposFromJSON(plantilla.campos_json);
        
        // Deshabilitar edición de campos (estructura SQL ya creada)
        document.querySelectorAll('.campo-nombre, .campo-tipo').forEach(input => {
          input.disabled = true;
        });
        document.querySelectorAll('.campo-item .btn-outline-danger').forEach(btn => {
          btn.disabled = true;
          btn.style.opacity = '0.5';
        });
        document.getElementById('btn-add-campo').disabled = true;
        document.getElementById('btn-add-campo').style.opacity = '0.5';
        
        // Agregar mensaje informativo
        const container = document.getElementById('plantilla-campos-container');
        const infoMsg = document.createElement('div');
        infoMsg.className = 'alert alert-info alert-sm mt-2';
        infoMsg.id = 'campos-readonly-msg';
        infoMsg.innerHTML = '<small><i class="bi bi-info-circle"></i> Los campos no se pueden modificar después de crear la plantilla (estructura de tabla SQL ya generada)</small>';
        container.appendChild(infoMsg);
        
        document.getElementById('modalPlantillaTitle').textContent = 'Editar plantilla (solo nombre y descripción)';
        document.getElementById('plantilla-error').classList.add('d-none');
        modalPlantilla.show();
      } catch (err) {
        alert(`Error al cargar plantilla: ${err.message}`);
      }
    });
  });
}

async function savePlantilla() {
  const id = document.getElementById('plantilla-id').value;
  const nombre = document.getElementById('plantilla-nombre').value.trim();
  const id_tipo = parseInt(document.getElementById('plantilla-tipo').value);
  const descripcion = document.getElementById('plantilla-descripcion').value.trim();
  const campos_json = getCamposAsJSON();
  const errBox = document.getElementById('plantilla-error');
  errBox.classList.add('d-none');

  // Validaciones
  if (!nombre || !id_tipo) {
    errBox.textContent = 'Nombre y tipo de documento son requeridos';
    errBox.classList.remove('d-none');
    return;
  }

  // Solo validar campos si es creación nueva (no edición)
  if (!id && (!campos_json || Object.keys(campos_json).length === 0)) {
    errBox.textContent = 'Debe agregar al menos un campo a la plantilla';
    errBox.classList.remove('d-none');
    return;
  }

  try {
    const body = {
      nombre,
      id_tipo,
      campos_json,
      descripcion: descripcion || null
    };

    if (id) {
      // Editar plantilla (solo nombre, descripción, estado)
      await api.request(`/plantillas/${id}`, { 
        method: 'PUT', 
        body: {
          nombre,
          descripcion: descripcion || null,
          estado: 1
        }
      });
    } else {
      // Crear plantilla
      await api.request('/plantillas', { method: 'POST', body });
    }

    modalPlantilla.hide();
    loadPlantillas();
  } catch (err) {
    errBox.textContent = err.message;
    errBox.classList.remove('d-none');
  }
}

window.addEventListener('DOMContentLoaded', () => {
  bindMenu();
  bindLogout();
  showSection('roles');
  modalRol = new bootstrap.Modal(document.getElementById('modalRol'));
  modalCargo = new bootstrap.Modal(document.getElementById('modalCargo'));
  modalUsuario = new bootstrap.Modal(document.getElementById('modalUsuario'));
  modalPlantilla = new bootstrap.Modal(document.getElementById('modalPlantilla'));
  modalUploadPlantilla = new bootstrap.Modal(document.getElementById('modalUploadPlantilla'));
  
  loadRolesAndCargos();
  loadTiposDocumentos();

  document.getElementById('btn-new-rol').addEventListener('click', () => {
    document.getElementById('form-rol').reset();
    document.getElementById('rol-id').value = '';
    document.getElementById('modalRolTitle').textContent = 'Nuevo rol';
    document.getElementById('rol-error').classList.add('d-none');
    modalRol.show();
  });
  document.getElementById('rol-save').addEventListener('click', saveRol);

  document.getElementById('btn-new-cargo').addEventListener('click', () => {
    document.getElementById('form-cargo').reset();
    document.getElementById('cargo-id').value = '';
    document.getElementById('modalCargoTitle').textContent = 'Nuevo cargo';
    document.getElementById('cargo-error').classList.add('d-none');
    modalCargo.show();
  });
  document.getElementById('cargo-save').addEventListener('click', saveCargo);
  
  document.getElementById('btn-new-usuario').addEventListener('click', () => {
    document.getElementById('form-usuario').reset();
    document.getElementById('usuario-id').value = '';
    document.getElementById('usuario-password').value = '';
    document.getElementById('usuario-firma').value = '';
    document.getElementById('firma-preview-container').classList.add('d-none');
    document.getElementById('firma-preview-new').classList.add('d-none');
    document.getElementById('modalUsuarioTitle').textContent = 'Nuevo usuario';
    document.getElementById('usuario-error').classList.add('d-none');
    modalUsuario.show();
  });
  document.getElementById('usuario-save').addEventListener('click', saveUsuario);

  // Event listener para preview de nueva firma
  document.getElementById('usuario-firma').addEventListener('change', (e) => {
    const file = e.target.files[0];
    const previewNewContainer = document.getElementById('firma-preview-new');
    const previewNewImg = document.getElementById('firma-preview-new-img');
    
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        previewNewImg.src = event.target.result;
        previewNewContainer.classList.remove('d-none');
      };
      reader.readAsDataURL(file);
    } else {
      previewNewContainer.classList.add('d-none');
    }
  });

  document.getElementById('btn-new-plantilla').addEventListener('click', () => {
    document.getElementById('form-plantilla').reset();
    document.getElementById('plantilla-id').value = '';
    clearCampos();
    
    // Habilitar edición de campos y tipo para nueva plantilla
    document.getElementById('plantilla-tipo').disabled = false;
    document.getElementById('btn-add-campo').disabled = false;
    document.getElementById('btn-add-campo').style.opacity = '1';
    
    // Eliminar mensaje de campos readonly si existe
    const msg = document.getElementById('campos-readonly-msg');
    if (msg) msg.remove();
    
    document.getElementById('modalPlantillaTitle').textContent = 'Nueva plantilla';
    document.getElementById('plantilla-error').classList.add('d-none');
    modalPlantilla.show();
  });
  document.getElementById('plantilla-save').addEventListener('click', savePlantilla);
  document.getElementById('btn-add-campo').addEventListener('click', () => addCampoInput());
  document.getElementById('upload-plantilla-save').addEventListener('click', uploadPlantillaArchivo);

  loadRoles();
});

// Bind logout once navbar is rendered by layout.js
document.addEventListener('layout:navbarReady', bindLogout);
