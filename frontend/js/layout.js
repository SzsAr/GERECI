const layout = (function() {
  function renderNavbar(containerId = 'app-navbar') {
    const el = document.getElementById(containerId);
    if (!el) return;
    
    // Obtener datos del usuario desde localStorage
    let userInfo = '';
    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const user = JSON.parse(userStr);
        const nombre = user.nombre || 'Usuario';
        const rol = user.rol_nombre || 'Sin rol asignado';
        userInfo = `<div class="text-end small">
          <div class="fw-semibold text-dark">${nombre}</div>
          <div class="text-muted">${rol}</div>
        </div>`;
      }
    } catch (e) {
      console.warn('No se pudo obtener datos del usuario');
    }
    
    el.innerHTML = `
      <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
        <div class="container-fluid px-4">
          <a class="navbar-brand fw-semibold" href="./dashboard.html">GERECI</a>
          <div class="d-flex align-items-center gap-3">
            ${userInfo}
            <button class="btn btn-outline-secondary btn-sm" id="btn-logout">
              <i class="bi bi-box-arrow-right"></i> Logout
            </button>
          </div>
        </div>
      </nav>`;
    // Notify listeners that navbar is ready (for binding logout)
    document.dispatchEvent(new CustomEvent('layout:navbarReady'));
  }

  function renderSidebar(active = 'dashboard', containerId = 'app-sidebar') {
    const el = document.getElementById(containerId);
    if (!el) return;
    
    // Obtener rol del usuario desde localStorage
    let esAdmin = false;
    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const user = JSON.parse(userStr);
        // Asumir que rol 1 es admin/superadmin
        esAdmin = user.id_rol === 1;
      }
    } catch (e) {
      console.warn('No se pudo obtener rol del usuario');
    }
    
    el.innerHTML = `
      <div class="list-group list-group-flush sidebar" id="menu-sidebar">
        <a class="list-group-item list-group-item-action ${active==='dashboard'?'active':''}" href="./dashboard.html"><i class="bi bi-speedometer2 me-2"></i>Dashboard</a>
        <a class="list-group-item list-group-item-action ${active==='documentos'?'active':''}" href="./documentos.html"><i class="bi bi-file-earmark-text me-2"></i>Documentos</a>
        <a class="list-group-item list-group-item-action ${active==='tareas'?'active':''}" href="./mis_tareas.html"><i class="bi bi-list-check me-2"></i>Mis tareas</a>
        ${esAdmin ? `<a class="list-group-item list-group-item-action ${active==='admin'?'active':''}" href="./admin.html"><i class="bi bi-gear me-2"></i>Administración</a>` : ''}
      </div>`;
  }

  function renderFooter(containerId = 'app-footer') {
    const el = document.getElementById(containerId);
    if (!el) return;
    const year = new Date().getFullYear();
    el.innerHTML = `
      <footer class="footer bg-white border-top mt-5">
        <div class="container-fluid px-4 py-3 d-flex justify-content-between align-items-center">
          <span class="text-muted small">GERECI · Sistema De Gestión De Resoluciones Y Circulares</span>
          <span class="text-muted small">© ${year}</span>
        </div>
      </footer>`;
    el.style.backgroundColor = '#f8f9fa';
  }

  return { renderNavbar, renderSidebar, renderFooter };
})();

(function initUiHelpers() {
  // Paleta de colores amable alineada con custom.css
  const colorPalette = {
    primary: '#0d6efd',    // Azul
    success: '#198754',    // Verde
    warning: '#fd7e14',    // Naranja
    error: '#dc3545',      // Rojo
    info: '#17a2b8'        // Cyan
  };

  function hasSweetAlert() {
    return typeof window !== 'undefined' && typeof window.Swal !== 'undefined';
  }

  function getColorByIcon(icon) {
    const colorMap = {
      'success': colorPalette.success,
      'error': colorPalette.error,
      'warning': colorPalette.warning,
      'info': colorPalette.info,
      'question': colorPalette.primary
    };
    return colorMap[icon] || colorPalette.primary;
  }

  async function notify(icon, title, text) {
    if (hasSweetAlert()) {
      const confirmColor = getColorByIcon(icon);
      await window.Swal.fire({
        icon,
        title,
        text,
        confirmButtonText: 'Aceptar',
        confirmButtonColor: confirmColor,
        customClass: {
          popup: 'swal2-rounded',
          title: 'swal2-title-friendly',
          content: 'swal2-content-friendly'
        }
      });
      return;
    }

    window.alert(text || title || '');
  }

  async function confirmDialog(text, title = 'Confirmacion') {
    if (hasSweetAlert()) {
      const result = await window.Swal.fire({
        icon: 'question',
        title,
        text,
        showCancelButton: true,
        confirmButtonText: 'Si, continuar',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: colorPalette.primary,
        cancelButtonColor: '#6c757d',
        customClass: {
          popup: 'swal2-rounded',
          title: 'swal2-title-friendly',
          content: 'swal2-content-friendly'
        }
      });
      return Boolean(result.isConfirmed);
    }

    return window.confirm(text || title);
  }

  // Inyectar estilos CSS para SweetAlert amable
  function injectSweetAlertStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .swal2-rounded {
        border-radius: 12px !important;
      }
      .swal2-title-friendly {
        font-weight: 600 !important;
        color: #212529 !important;
      }
      .swal2-content-friendly {
        color: #6c757d !important;
      }
      .swal2-confirm {
        border-radius: 6px !important;
        font-weight: 500 !important;
        padding: 0.6rem 1.5rem !important;
      }
      .swal2-cancel {
        border-radius: 6px !important;
        font-weight: 500 !important;
        padding: 0.6rem 1.5rem !important;
      }
      .swal2-icon {
        border-radius: 50% !important;
      }
    `;
    document.head.appendChild(style);
  }

  // Inyectar estilos al cargar
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectSweetAlertStyles);
  } else {
    injectSweetAlertStyles();
  }

  window.ui = {
    confirm: confirmDialog,
    info: async (text, title = 'Informacion') => notify('info', title, text),
    success: async (text, title = 'Exito') => notify('success', title, text),
    warning: async (text, title = 'Atencion') => notify('warning', title, text),
    error: async (text, title = 'Error') => notify('error', title, text)
  };
})();
