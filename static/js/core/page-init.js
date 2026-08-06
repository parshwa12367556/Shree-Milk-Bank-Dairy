/**
 * ============================================================
 * SMART DAIRY ERP — Server-Rendered Page Initializer
 * ============================================================
 * Used by the Jinja2 template pages. It:
 *   1. Applies the saved theme + sidebar state
 *   2. Starts the clock / hides the page loader
 *   3. Provides lightweight App & Router shims so the existing
 *      page modules (which were written for the SPA) keep working
 *   4. Calls the page's init function (body[data-page-init])
 * ============================================================
 */

// ── Router shim: hash routing is replaced by real URLs ──
// SPA route names (used by the page modules) map to the server-rendered
// pages served by the Flask pages blueprint.
const ROUTE_MAP = {
  dashboard: () => {
    const role = window.Auth && Auth.getUser() ? Auth.getUser().role : null;
    if (role === 'BRANCH_MANAGER' || role === 'OPERATOR') return '/branch/dashboard';
    if (role === 'FARMER') return '/farmer/profile';
    return '/admin/dashboard';
  },
  login: () => '/login',
  collection: () => '/branch/collection/morning',
  farmers: () => {
    const role = window.Auth && Auth.getUser() ? Auth.getUser().role : null;
    return role === 'BRANCH_MANAGER' || role === 'OPERATOR' ? '/branch/farmers' : '/admin/farmers';
  },
  'farmer-form': () => '/branch/farmers/register',
  'farmer-profile': () => '/branch/farmers/profile',
  'farmer-passbook': () => '/branch/farmers/passbook',
  branches: () => '/admin/branches',
  payments: () => '/admin/payments/dashboard',
  pricing: () => '/admin/settings/milk-pricing',
  quality: () => '/branch/quality/testing',
  rejections: () => '/branch/quality/rejected',
  procurement: () => '/admin/procurement/dashboard',
  inventory: () => '/admin/inventory/dashboard',
  employees: () => '/admin/employees/dashboard',
  vehicles: () => '/admin/vehicles/dashboard',
  reports: () => '/admin/reports/dashboard',
  audit: () => '/admin/audit/dashboard',
  settings: () => '/admin/settings/company',
  notifications: () => '/shared/notifications',
  profile: () => '/shared/profile',
  guide: () => '/shared/user-guide',
  help: () => '/shared/help',
};

window.Router = window.Router || {
  navigate(url) {
    if (typeof url === 'string' && url.indexOf('#') === 0) {
      url = url.slice(1);
    }
    if (url && !/^(\/|http)/.test(url)) {
      const mapped = ROUTE_MAP[url];
      window.location.href = mapped ? mapped() : ('/' + url);
    } else {
      window.location.href = url || '/admin/dashboard';
    }
  },
  getCurrentRoute() {
    return (window.location.pathname || '/').replace(/^\//, '');
  },
  reload() {
    window.location.reload();
  },
};

// ── App shim: shared state + skeleton helpers used by page modules ──
window.App = window.App || {
  // Farmer selection/edit state (used by farmers / farmer-profile / farmer-form)
  selectedFarmer: null,
  editFarmer: null,

  showSkeleton(containerId, count = 3) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = Array(count).fill(
      '<div class="skeleton skeleton-card" style="margin-bottom: var(--space-3);"></div>'
    ).join('');
  },

  hideSkeleton(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.querySelectorAll('.skeleton').forEach(el => el.remove());
  },

  _updateDateTime() {
    const now = new Date();
    const dateEl = document.querySelector('.navbar .current-date');
    const timeEl = document.querySelector('.navbar .current-time');
    if (dateEl) dateEl.textContent = now.toLocaleDateString('en-IN', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' });
    if (timeEl) timeEl.textContent = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
  },
};

document.addEventListener('DOMContentLoaded', () => {
  // ── Theme ──
  const theme = window.Storage ? Storage.getTheme() : 'light';
  document.documentElement.setAttribute('data-theme', theme);
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.innerHTML = theme === 'dark'
      ? '<i data-lucide="moon"></i>'
      : '<i data-lucide="sun"></i>';
    themeToggle.addEventListener('click', () => {
      const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      if (window.Storage) Storage.setTheme(next);
      if (window.lucide) lucide.createIcons();
    });
  }

  // ── Sidebar collapsed state ──
  if (window.Storage && Storage.isSidebarCollapsed()) {
    document.querySelector('.app-layout')?.classList.add('sidebar-collapsed');
  }

  // ── Sidebar submenu toggles (click a section to expand its menu) ──
  document.querySelectorAll('.sidebar-nav .nav-item.has-submenu').forEach(item => {
    item.addEventListener('click', () => {
      const submenu = item.nextElementSibling;
      if (submenu && submenu.classList.contains('nav-submenu')) {
        submenu.classList.toggle('open');
        const chevron = item.querySelector('.nav-chevron');
        if (chevron) chevron.classList.toggle('open');
      }
    });
  });

  // ── Clock ──
  App._updateDateTime();
  setInterval(() => App._updateDateTime(), 60000);

  // ── Hide page loader ──
  const loader = document.getElementById('page-loader');
  if (loader) {
    loader.classList.add('loaded');
    setTimeout(() => loader.remove(), 400);
  }

  // ── User dropdown + notification dropdown ──
  const userTrigger = document.querySelector('.user-dropdown .user-trigger');
  const userDropdown = document.querySelector('.user-dropdown .dropdown-menu');
  if (userTrigger && userDropdown) {
    userTrigger.addEventListener('click', (e) => {
      e.stopPropagation();
      userDropdown.classList.toggle('open');
    });
  }
  const notifTrigger = document.querySelector('.notif-trigger');
  const notifDropdown = document.querySelector('.notif-dropdown');
  if (notifTrigger && notifDropdown) {
    notifTrigger.addEventListener('click', (e) => {
      e.stopPropagation();
      notifDropdown.classList.toggle('open');
    });
  }
  document.addEventListener('click', () => {
    if (userDropdown) userDropdown.classList.remove('open');
    if (notifDropdown) notifDropdown.classList.remove('open');
  });

  // ── Logout ──
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      if (window.Modal) {
        Modal.confirm({
          title: 'Logout',
          message: 'Are you sure you want to logout?',
          confirmText: 'Logout',
          variant: 'warning',
          onConfirm: () => {
            if (window.Storage) Storage.clear();
            window.location.href = '/login';
          }
        });
      } else {
        if (window.Storage) Storage.clear();
        window.location.href = '/login';
      }
    });
  }

  // ── Lucide icons ──
  if (window.lucide) lucide.createIcons();

  // ── Page-specific init (body[data-page-init="initXxx"]) ──
  const initName = document.body.getAttribute('data-page-init');
  if (initName && typeof window[initName] === 'function') {
    try {
      window[initName]();
    } catch (err) {
      console.warn('Page init failed:', initName, err);
    }
  }
});
