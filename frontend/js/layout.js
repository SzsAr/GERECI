const layout = (function() {
  function renderNavbar(containerId = 'app-navbar') {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = `
      <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
        <div class="container-fluid px-4">
          <a class="navbar-brand fw-semibold" href="./dashboard.html">GERECI</a>
          <div class="d-flex align-items-center gap-3">
            <span id="user-name" class="text-muted small"></span>
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
    el.innerHTML = `
      <div class="list-group list-group-flush sidebar" id="menu-sidebar">
        <a class="list-group-item list-group-item-action ${active==='dashboard'?'active':''}" href="./dashboard.html"><i class="bi bi-speedometer2 me-2"></i>Dashboard</a>
        <a class="list-group-item list-group-item-action ${active==='documentos'?'active':''}" href="#"><i class="bi bi-file-earmark-text me-2"></i>Documentos</a>
        <a class="list-group-item list-group-item-action ${active==='firmas'?'active':''}" href="#"><i class="bi bi-pencil-square me-2"></i>Firmas pendientes</a>
        <a class="list-group-item list-group-item-action ${active==='tareas'?'active':''}" href="#"><i class="bi bi-list-check me-2"></i>Mis tareas</a>
        <a class="list-group-item list-group-item-action ${active==='observaciones'?'active':''}" href="#"><i class="bi bi-chat-dots me-2"></i>Observaciones</a>
        <a class="list-group-item list-group-item-action ${active==='admin'?'active':''}" href="./admin.html"><i class="bi bi-gear me-2"></i>Administración</a>
      </div>`;
  }

  function renderFooter(containerId = 'app-footer') {
    const el = document.getElementById(containerId);
    if (!el) return;
    const year = new Date().getFullYear();
    el.innerHTML = `
      <footer class="footer bg-white border-top">
        <div class="container-fluid px-4 py-2 d-flex justify-content-between align-items-center">
          <span class="text-muted small">GERECI · Sistema De Gestión De Resoluciones Y Circulares</span>
          <span class="text-muted small">© ${year}</span>
        </div>
      </footer>`;
  }

  return { renderNavbar, renderSidebar, renderFooter };
})();
