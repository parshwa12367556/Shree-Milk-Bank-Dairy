/**
 * ============================================================
 * SMART DAIRY ERP — Application Shell
 * Main entry point - manages sidebar, navbar, theme,
 * notifications, and global UI interactions.
 * ============================================================
/**
 * Global HTML Escaping Utility for XSS Prevention
 */
window.escapeHtml = function(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
};

const App = {
  /**
   * Initialize the application
   */
  init() {
    // Apply saved theme
    this._initTheme();
    
    // Apply sidebar state
    this._initSidebar();
    
    // Initialize router
    Router.init();
    
    // Initialize global event listeners
    this._initGlobalEvents();
    
    // Initialize Lucide icons
    if (window.lucide) {
      lucide.createIcons();
    }
    
    // Check auth state
    this._checkAuth();
    
    // Load notifications
    this._loadNotifications();
    
    // Set current date/time
    this._updateDateTime();
    setInterval(() => this._updateDateTime(), 60000);

    console.log('🐄 Shree Milk Bank initialized');
  },

  /**
   * Check authentication state
   */
  _checkAuth() {
    const loginPage = document.getElementById('page-login');
    const appLayout = document.querySelector('.app-layout');
    
    if (Auth.isAuthenticated()) {
      // Show app, hide login
      loginPage.style.display = 'none';
      appLayout.style.display = 'flex';
      Auth.initApp();
      // Navigate to the role home (dashboard / farmer-dashboard)
      if (Router.getCurrentRoute() === 'login') {
        Router.navigate(Router.homeRoute(), true);
      }
    } else {
      // Show login, hide app
      loginPage.style.display = 'flex';
      appLayout.style.display = 'none';
      // Initialize login form
      Auth.initLoginPage();
    }
  },

  /**
   * Initialize theme
   */
  _initTheme() {
    const theme = Storage.getTheme();
    document.documentElement.setAttribute('data-theme', theme);
    
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
      toggle.innerHTML = theme === 'dark' 
        ? '<i data-lucide="sun"></i>' 
        : '<i data-lucide="moon"></i>';
    }
  },

  /**
   * Initialize sidebar state
   */
  _initSidebar() {
    const collapsed = Storage.isSidebarCollapsed();
    if (collapsed) {
      document.querySelector('.app-layout').classList.add('sidebar-collapsed');
    }
  },

  /**
   * Initialize global events
   */
  _initGlobalEvents() {
    // Theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => this._toggleTheme());
    }

    // Sidebar collapse toggle
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    if (sidebarToggle) {
      sidebarToggle.addEventListener('click', () => this._toggleSidebar());
    }

    // Mobile sidebar toggle
    const mobileToggle = document.querySelector('.sidebar-toggle-mobile');
    if (mobileToggle) {
      mobileToggle.addEventListener('click', () => this._toggleMobileSidebar());
    }

    // Sidebar overlay close
    const sidebarOverlay = document.querySelector('.sidebar-overlay');
    if (sidebarOverlay) {
      sidebarOverlay.addEventListener('click', () => this._closeMobileSidebar());
    }

    // User dropdown
    const userTrigger = document.querySelector('.user-dropdown .user-trigger');
    const userDropdown = document.querySelector('.user-dropdown .dropdown-menu');
    if (userTrigger && userDropdown) {
      userTrigger.addEventListener('click', (e) => {
        e.stopPropagation();
        userDropdown.classList.toggle('open');
        const chevron = userTrigger.querySelector('.user-chevron');
        if (chevron) chevron.classList.toggle('open');
      });
    }

    // Notification dropdown
    const notifTrigger = document.querySelector('.notif-trigger');
    const notifDropdown = document.querySelector('.notif-dropdown');
    if (notifTrigger && notifDropdown) {
      notifTrigger.addEventListener('click', (e) => {
        e.stopPropagation();
        notifDropdown.classList.toggle('open');
      });
    }

    // Close dropdowns on outside click
    document.addEventListener('click', (e) => {
      // User dropdown
      if (userDropdown) userDropdown.classList.remove('open');
      if (notifDropdown) notifDropdown.classList.remove('open');
      
      // Chevron
      const chevron = document.querySelector('.user-chevron');
      if (chevron) chevron.classList.remove('open');
    });

    // Logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        Modal.confirm({
          title: 'Logout',
          message: 'Are you sure you want to logout?',
          confirmText: 'Logout',
          variant: 'warning',
          onConfirm: () => Auth.handleLogout()
        });
      });
    }

    // Sidebar navigation items
    document.querySelectorAll('.sidebar-nav .nav-item[data-route]').forEach(item => {
      item.addEventListener('click', () => {
        const route = item.dataset.route;
        Router.navigate(route);
      });
    });

    // Sidebar submenu toggles
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

    // Global search functionality - dispatch page-specific searches
    const globalSearch = document.getElementById('global-search');
    if (globalSearch) {
      globalSearch.addEventListener('input', debounce((e) => {
        const query = e.target.value.trim();
        // Determine current page and apply appropriate filter
        const currentPage = Router.getCurrentRoute();
        switch (currentPage) {
          case 'farmers':
            Table.filter('farmers-table', query);
            break;
          case 'collection':
            Table.filter('collections-table', query);
            break;
          case 'employees':
            Table.filter('employees-table', query);
            break;
          case 'payments':
            Table.filter('payments-table', query);
            break;
          case 'inventory':
            Table.filter('inventory-table', query);
            break;
          case 'branches':
            Table.filter('branches-table', query);
            break;
          case 'vehicles':
            Table.filter('vehicles-table', query);
            break;
          case 'quality':
            Table.filter('quality-table', query);
            break;
          case 'rejections':
            Table.filter('rejections-table', query);
            break;
          case 'audit':
            Table.filter('audit-table', query);
            break;
          default:
            break;
        }
      }, 300));
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      // Ctrl+B - Toggle sidebar
      if (e.ctrlKey && e.key === 'b') {
        e.preventDefault();
        this._toggleSidebar();
      }
      // Ctrl+K - Focus search
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('.search-bar input');
        if (searchInput) searchInput.focus();
      }
    });
  },

  /**
   * Toggle dark/light theme
   */
  _toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', next);
    Storage.setTheme(next);
    
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
      toggle.innerHTML = next === 'dark' 
        ? '<i data-lucide="sun"></i>' 
        : '<i data-lucide="moon"></i>';
      if (window.lucide) lucide.createIcons();
    }
  },

  /**
   * Toggle sidebar collapsed state
   */
  _toggleSidebar() {
    const layout = document.querySelector('.app-layout');
    const collapsed = layout.classList.toggle('sidebar-collapsed');
    Storage.setSidebarCollapsed(collapsed);
    
    // Recreate icons because layout changes
    if (window.lucide) {
      setTimeout(() => lucide.createIcons(), 100);
    }
  },

  /**
   * Open mobile sidebar
   */
  _toggleMobileSidebar() {
    document.querySelector('.sidebar').classList.toggle('open');
    document.querySelector('.sidebar-overlay').classList.toggle('active');
  },

  /**
   * Close mobile sidebar
   */
  _closeMobileSidebar() {
    document.querySelector('.sidebar').classList.remove('open');
    document.querySelector('.sidebar-overlay').classList.remove('active');
  },

  /**
   * Update date/time display
   */
  _updateDateTime() {
    const now = new Date();
    const dateStr = now.toLocaleDateString('en-IN', {
      weekday: 'short',
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
    const timeStr = now.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit'
    });
    
    const dateEl = document.querySelector('.navbar .current-date');
    const timeEl = document.querySelector('.navbar .current-time');
    
    if (dateEl) dateEl.textContent = dateStr;
    if (timeEl) timeEl.textContent = timeStr;
  },

  /**
   * Load notifications
   */
  async _loadNotifications() {
    if (!Auth.isAuthenticated()) return;

    try {
      const result = await API.getNotifications({ limit: 5 });
      const notifications = result.notifications || result.data || result || [];
      
      this._renderNotifications(notifications);
    } catch (error) {
      console.warn('Failed to load notifications:', error);
    }
  },

  /**
   * Render notifications in dropdown
   */
  _renderNotifications(notifications) {
    const list = document.querySelector('.notif-dropdown .notif-list');
    const count = document.querySelector('.notif-count');
    if (!list) return;

    if (!notifications || !notifications.length) {
      list.innerHTML = `
        <div class="empty-state" style="padding: var(--space-8);">
          <div class="empty-icon"><i data-lucide="bell-off"></i></div>
          <p style="font-size: var(--text-sm); color: var(--ink-muted);">No notifications</p>
        </div>
      `;
      if (window.lucide) lucide.createIcons();
      return;
    }

    const unread = notifications.filter(n => !n.read).length;
    if (count) {
      count.textContent = unread;
      count.style.display = unread > 0 ? 'flex' : 'none';
    }

    const iconMap = {
      payment: { icon: 'wallet', bg: 'var(--success-light)', color: 'var(--success)' },
      collection: { icon: 'milk', bg: 'var(--info-light)', color: 'var(--info)' },
      quality: { icon: 'flask-conical', bg: 'var(--purple-light)', color: 'var(--purple)' },
      system: { icon: 'settings', bg: 'var(--warning-light)', color: 'var(--warning-dark)' },
      farmer: { icon: 'user-plus', bg: 'var(--teal-light)', color: 'var(--teal)' },
    };

    list.innerHTML = notifications.map(n => {
      const meta = iconMap[n.type] || { icon: 'bell', bg: 'var(--gray-100)', color: 'var(--gray-600)' };
      return `
        <div class="notif-item ${n.read ? '' : 'unread'}" onclick="Router.navigate('${n.link || 'notifications'}')">
          <div class="notif-icon" style="background: ${meta.bg}; color: ${meta.color};">
            <i data-lucide="${meta.icon}"></i>
          </div>
          <div class="notif-body">
            <div class="notif-title">${n.title || ''}</div>
            <div class="notif-text">${truncate(n.message, 80)}</div>
            <div class="notif-time">${fmtDate(n.created_at, true)}</div>
          </div>
        </div>
      `;
    }).join('');

    if (window.lucide) lucide.createIcons();
  },

  /**
   * Show loading skeleton
   * @param {string} containerId - Container element ID
   * @param {number} count - Number of skeleton items
   */
  showSkeleton(containerId, count = 3) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = Array(count).fill(`
      <div class="skeleton skeleton-card" style="margin-bottom: var(--space-3);"></div>
    `).join('');
  },

  /**
   * Hide skeleton (show actual content)
   * @param {string} containerId - Container element ID
   */
  hideSkeleton(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.querySelectorAll('.skeleton').forEach(el => el.remove());
  }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => App.init());

window.App = App;
