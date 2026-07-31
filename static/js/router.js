/**
 * ============================================================
 * SMART DAIRY ERP — Hash-based Client Router
 * ============================================================
 */

const Router = {
  currentPage: null,
  previousPage: null,
  routes: {},
  guards: {},

  /**
   * Register a route
   * @param {string} name - Route name (without #)
   * @param {object} config - Route configuration
   * @param {string} config.title - Page title
   * @param {string} config.icon - Lucide icon name
   * @param {Function} config.init - Initialize function
   * @param {string} config.guard - Auth guard (optional)
   */
  register(name, config = {}) {
    this.routes[name] = {
      name,
      title: config.title || name,
      icon: config.icon || 'file',
      init: config.init || null,
      guard: config.guard || null,
    };
  },

  /**
   * Set auth guard for a route
   * @param {string} name - Route name
   * @param {string} guard - Guard type
   */
  setGuard(name, guard) {
    if (this.routes[name]) {
      this.routes[name].guard = guard;
    }
  },

  /**
   * Navigate to a route
   * @param {string} name - Route name
   * @param {boolean} replace - Replace history entry
   */
  navigate(name, replace = false) {
    const hash = `#${name}`;
    if (replace) {
      window.location.replace(hash);
    } else {
      window.location.hash = hash;
    }
  },

  /**
   * Get current route name
   * @returns {string}
   */
  getCurrentRoute() {
    return (window.location.hash || '#dashboard').replace('#', '');
  },

  /**
   * Initialize the router
   */
  init() {
    window.addEventListener('hashchange', () => this._handleRoute());
    window.addEventListener('load', () => this._handleRoute());
  },

  /**
   * Handle route change
   */
  _handleRoute() {
    const hash = window.location.hash || '#dashboard';
    const page = hash.replace('#', '');
    
    // Store previous page
    this.previousPage = this.currentPage;
    this.currentPage = page;

    // Check if route exists
    const route = this.routes[page];
    
    // Hide all pages
    document.querySelectorAll('.page-container').forEach(p => {
      p.classList.remove('active');
      p.style.display = 'none';
    });

    // Show target page or 404
    const targetEl = document.getElementById(`page-${page}`);
    if (targetEl) {
      targetEl.style.display = 'block';
      // Force reflow for animation
      void targetEl.offsetWidth;
      targetEl.classList.add('active');
      
      // Update breadcrumb
      this._updateBreadcrumb(page, route);
      
      // Update sidebar active state
      this._updateSidebar(page);
      
      // Update document title
      document.title = route ? `${route.title} - Smart Dairy ERP` : 'Smart Dairy ERP';
      
      // Call page-specific init
      if (route && route.init && typeof window[route.init] === 'function') {
        window[route.init]();
      } else if (window[`init_${page}`]) {
        window[`init_${page}`]();
      }
    } else {
      // Show 404
      const notFound = document.getElementById('page-404');
      if (notFound) {
        notFound.style.display = 'block';
        notFound.classList.add('active');
        document.title = '404 - Page Not Found';
      }
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Close mobile sidebar
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    if (sidebar) sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('active');
  },

  /**
   * Update breadcrumb
   */
  _updateBreadcrumb(page, route) {
    const breadcrumb = document.querySelector('.breadcrumb-nav');
    if (!breadcrumb) return;
    
    const title = route ? route.title : page.charAt(0).toUpperCase() + page.slice(1);
    
    breadcrumb.innerHTML = `
      <a href="#dashboard">Dashboard</a>
      <span class="separator">/</span>
      <span class="current">${title}</span>
    `;
  },

  /**
   * Update sidebar active state
   */
  _updateSidebar(page) {
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
      item.classList.toggle('active', item.dataset.route === page);
    });
  },

  /**
   * Reload current route
   */
  reload() {
    this._handleRoute();
  }
};

// Register default routes
Router.register('dashboard', { title: 'Dashboard', icon: 'layout-dashboard', init: 'initDashboard' });
Router.register('login', { title: 'Login', icon: 'log-in' });
Router.register('collection', { title: 'Milk Collection', icon: 'milk', init: 'initCollection' });
Router.register('farmers', { title: 'Farmers', icon: 'users', init: 'initFarmers' });
Router.register('farmer-form', { title: 'Register Farmer', icon: 'user-plus', init: 'initFarmerForm' });
Router.register('farmer-profile', { title: 'Farmer Profile', icon: 'user', init: 'initFarmerProfile' });
Router.register('farmer-passbook', { title: 'Farmer Passbook', icon: 'book-open', init: 'initFarmerPassbook' });
Router.register('branches', { title: 'Branches', icon: 'building-2', init: 'initBranches' });
Router.register('payments', { title: 'Payments', icon: 'wallet', init: 'initPayments' });
Router.register('pricing', { title: 'Rate Engine', icon: 'dollar-sign', init: 'initPricing' });
Router.register('quality', { title: 'Quality Control', icon: 'flask', init: 'initQuality' });
Router.register('rejections', { title: 'Rejections', icon: 'x-circle', init: 'initRejections' });
Router.register('procurement', { title: 'Procurement', icon: 'truck', init: 'initProcurement' });
Router.register('inventory', { title: 'Inventory', icon: 'package', init: 'initInventory' });
Router.register('employees', { title: 'Employees', icon: 'briefcase', init: 'initEmployees' });
Router.register('vehicles', { title: 'Vehicles', icon: 'car', init: 'initVehicles' });
Router.register('reports', { title: 'Reports', icon: 'bar-chart-3', init: 'initReports' });
Router.register('audit', { title: 'Audit Logs', icon: 'scroll-text', init: 'initAudit' });
Router.register('settings', { title: 'Settings', icon: 'settings', init: 'initSettings' });
Router.register('notifications', { title: 'Notifications', icon: 'bell', init: 'initNotifications' });
Router.register('profile', { title: 'My Profile', icon: 'user-circle', init: 'initProfile' });
Router.register('help', { title: 'Help Center', icon: 'help-circle', init: 'initHelp' });

window.Router = Router;
