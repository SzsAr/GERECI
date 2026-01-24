(function guardAuth() {
  const token = localStorage.getItem('token');
  if (!token) window.location.href = './index.html';
})();

let modalRol, modalCargo, modalUsuario, modalPlantilla;

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
  tbody.innerHTML = '<tr><td colspan="7" class="text-muted small">Cargando...</td></tr>';
  try {
    const data = await api.request('/users/all');
    if (!data || data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-muted small">Sin datos</td></tr>';
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
          <button class="btn btn-sm btn-outline-primary me-1" data-edit-usuario="${u.id_usuario}"><i class="bi bi-pencil"></i></button>
          <button class="btn btn-sm btn-outline-danger" data-del-usuario="${u.id_usuario}"><i class="bi bi-trash"></i></button>
        </td>
      </tr>
    `).join('');
    bindUserActions();
    bindUserStateSwitch();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-danger small">Error: ${err.message}</td></tr>`;
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
    tbody.innerHTML = data.map(p => `
      <tr>
        <td>${p.nombre}</td>
        <td>${p.tipo_nombre || p.id_tipo}</td>
        <td><a href="${p.ruta_almacenamiento ? API_BASE + p.ruta_almacenamiento : '#'}" target="_blank">${p.nombre_archivo || 'Sin archivo'}</a></td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-primary me-1" data-edit-plantilla="${p.id}"><i class="bi bi-pencil"></i></button>
          <button class="btn btn-sm btn-outline-danger" data-del-plantilla="${p.id}"><i class="bi bi-trash"></i></button>
        </td>
      </tr>
    `).join('');
    bindPlantillaActions();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-danger small">Error: ${err.message}</td></tr>`;
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
  const errBox = document.getElementById('usuario-error');
  errBox.classList.add('d-none');

  if (!nombre || !documento || !username || !id_rol) {
    errBox.textContent = 'Nombre, documento, usuario y rol son requeridos';
    errBox.classList.remove('d-none');
    return;
  }

  try {
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
      await api.request('/users/create', { method: 'POST', body });
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

function addCampoInput(key = '') {
  const container = document.getElementById('plantilla-campos-container');
  const campoId = 'campo-' + Date.now();
  const campoDiv = document.createElement('div');
  campoDiv.className = 'row mb-2 campo-item';
  campoDiv.id = campoId;
  campoDiv.innerHTML = `
    <div class="col-10">
      <input type="text" class="form-control form-control-sm campo-key" placeholder="Nombre del campo" value="${key}">
    </div>
    <div class="col-2 d-flex justify-content-end">
      <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeCampoInput('${campoId}')">
        <i class="bi bi-trash"></i>
      </button>
    </div>
  `;
  container.appendChild(campoDiv);
}

function removeCampoInput(campoId) {
  const campo = document.getElementById(campoId);
  if (campo) campo.remove();
}

function clearCampos() {
  document.getElementById('plantilla-campos-container').innerHTML = '';
}

function loadCamposFromJSON(camposJSON) {
  clearCampos();
  if (camposJSON && typeof camposJSON === 'object') {
    Object.keys(camposJSON).forEach((key) => {
      addCampoInput(key);
    });
  }
}

function getCamposAsJSON() {
  const campos = {};
  document.querySelectorAll('.campo-item').forEach(item => {
    const key = item.querySelector('.campo-key').value.trim();
    if (key) {
      campos[key] = '';
    }
  });
  return Object.keys(campos).length > 0 ? campos : null;
}

function bindPlantillaActions() {
  document.querySelectorAll('[data-del-plantilla]').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('¿Eliminar plantilla?')) return;
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
        document.getElementById('plantilla-tipo').value = plantilla.id_tipo;
        loadCamposFromJSON(plantilla.campos_json);
        document.getElementById('plantilla-file').value = '';
        document.getElementById('modalPlantillaTitle').textContent = 'Editar plantilla';
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
  const campos = getCamposAsJSON();
  const fileInput = document.getElementById('plantilla-file');
  const file = fileInput.files[0];
  const errBox = document.getElementById('plantilla-error');
  errBox.classList.add('d-none');

  if (!nombre || !id_tipo) {
    errBox.textContent = 'Nombre y tipo de documento son requeridos';
    errBox.classList.remove('d-none');
    return;
  }

  if (!id && !file) {
    errBox.textContent = 'Debe seleccionar un archivo Word (.docx) al crear una plantilla';
    errBox.classList.remove('d-none');
    return;
  }

  try {
    const formData = new FormData();
    formData.append('nombre', nombre);
    formData.append('id_tipo', id_tipo);
    if (campos) formData.append('campos_json', JSON.stringify(campos));
    if (file) formData.append('file', file);

    if (id) {
      await api.request(`/plantillas/${id}`, { method: 'PUT', body: formData });
    } else {
      await api.request('/plantillas', { method: 'POST', body: formData });
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
    document.getElementById('modalUsuarioTitle').textContent = 'Nuevo usuario';
    document.getElementById('usuario-error').classList.add('d-none');
    modalUsuario.show();
  });
  document.getElementById('usuario-save').addEventListener('click', saveUsuario);

  document.getElementById('btn-new-plantilla').addEventListener('click', () => {
    document.getElementById('form-plantilla').reset();
    document.getElementById('plantilla-id').value = '';
    document.getElementById('plantilla-file').value = '';
    clearCampos();
    document.getElementById('modalPlantillaTitle').textContent = 'Nueva plantilla';
    document.getElementById('plantilla-error').classList.add('d-none');
    modalPlantilla.show();
  });
  document.getElementById('plantilla-save').addEventListener('click', savePlantilla);
  document.getElementById('btn-add-campo').addEventListener('click', () => addCampoInput());

  loadRoles();
});

// Bind logout once navbar is rendered by layout.js
document.addEventListener('layout:navbarReady', bindLogout);
