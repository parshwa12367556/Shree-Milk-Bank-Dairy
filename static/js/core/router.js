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
   * Role-based access map — restricts pages to specific roles.
   * Branch Managers are limited to their own branch modules; head-office
   * modules (branches, procurement, vehicles, rates, audit, settings) and
   * farmer registration are role-gated per the architecture spec.
   */
  roleAccess: {
    // Head-office modules — ADMIN only
    branches: ['ADMIN'],
    procurement: ['ADMIN'],
    vehicles: ['ADMIN'],
    expenses: ['ADMIN'],
    pricing: ['ADMIN'],
    audit: ['ADMIN'],
    settings: ['ADMIN'],
    inventory: ['ADMIN'],
    employees: ['ADMIN'],
    // Farmer registry & operational pages — ADMIN + BRANCH_MANAGER
    'farmer-form': ['ADMIN', 'BRANCH_MANAGER'],
    'farmer-profile': ['ADMIN', 'BRANCH_MANAGER'],
    'farmer-passbook': ['ADMIN', 'BRANCH_MANAGER'],
    farmers: ['ADMIN', 'BRANCH_MANAGER'],
    collection: ['ADMIN', 'BRANCH_MANAGER'],
    quality: ['ADMIN', 'BRANCH_MANAGER'],
    rejections: ['ADMIN', 'BRANCH_MANAGER'],
    reports: ['ADMIN', 'BRANCH_MANAGER'],
    notifications: ['ADMIN', 'BRANCH_MANAGER'],
    profile: ['ADMIN', 'BRANCH_MANAGER'],
    // Shared workspace — every authenticated user except farmers
    dashboard: ['ADMIN', 'BRANCH_MANAGER'],
    // Farmer portal — FARMER only
    'farmer-dashboard': ['FARMER'],
    'farmer-collections': ['FARMER'],
    'farmer-daily': ['FARMER'],
    'my-passbook': ['FARMER'],
    'farmer-payments': ['FARMER'],
    'farmer-notifications': ['FARMER'],
    'my-profile': ['FARMER'],
    'farmer-bank-details': ['FARMER'],
    'farmer-documents': ['FARMER'],
    'farmer-grievance': ['FARMER'],
    'farmer-settings': ['FARMER'],
  },

  /**
   * Role home route — used for post-login redirects and guard fallbacks.
   */
  homeRoute() {
    const user = window.Auth ? Auth.getUser() : null;
    if (user && user.role === 'FARMER') return 'farmer-dashboard';
    return 'dashboard';
  },

  /**
   * Check whether the current user may open a page
   * @param {string} page - Route name
   * @returns {boolean}
   */
  canAccess(page) {
    // Farmer form: ADMIN and BRANCH_MANAGER may REGISTER new farmers, but any
    // authenticated user may open it to EDIT an existing farmer.
    if (page === 'farmer-form') {
      const user = window.Auth ? Auth.getUser() : null;
      if (!user) return false;
      if (['ADMIN', 'BRANCH_MANAGER'].includes(user.role)) return true;
      return !!(window.App && window.App.editFarmer);
    }
    const allowed = this.roleAccess[page];
    if (!allowed) return true;
    const user = window.Auth ? Auth.getUser() : null;
    return !!(user && allowed.includes(user.role));
  },

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

    // Role-based route guard — redirect forbidden pages to the role home
    if (!this.canAccess(page)) {
      if (window.Modal) {
        Modal.toast({ title: 'Access Denied', message: 'You do not have permission to view this page.', type: 'error' });
      }
      window.location.replace(`#${this.homeRoute()}`);
      return;
    }

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
      document.title = route ? `${route.title} - Shree Milk Bank` : 'Shree Milk Bank';
      
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
   * Get the role owner of a route
   * ('admin' | 'branch' | 'farmer' | 'shared' | 'auth')
   * @param {string} page - Route name
   * @returns {string|null}
   */
  getRouteOwner(page) {
    const route = this.routes[page];
    return route ? route.owner : null;
  },

  /**
   * Reload current route
   */
  reload() {
    this._handleRoute();
  }
};

// Register default routes.
// `owner` groups each page by role responsibility:
//   admin  → Head Office (Super Admin) only
//   branch → Branch Manager operational pages
//   farmer → Farmer-facing pages (register/view/passbook)
//   shared → Used by all roles
//   auth   → Login / pre-auth pages
Router.register('dashboard', { title: 'Dashboard', icon: 'layout-dashboard', init: 'initDashboard', owner: 'shared' });
Router.register('login', { title: 'Login', icon: 'log-in', owner: 'auth' });
Router.register('collection', { title: 'Milk Collection', icon: 'milk', init: 'initCollection', owner: 'branch' });
Router.register('farmers', { title: 'Farmers', icon: 'users', init: 'initFarmers', owner: 'farmer' });
Router.register('farmer-form', { title: 'Register Farmer', icon: 'user-plus', init: 'initFarmerForm', owner: 'farmer' });
Router.register('farmer-profile', { title: 'Farmer Profile', icon: 'user', init: 'initFarmerProfile', owner: 'farmer' });
Router.register('farmer-passbook', { title: 'Farmer Passbook', icon: 'book-open', init: 'initFarmerPassbook', owner: 'farmer' });
Router.register('branches', { title: 'Branches', icon: 'building-2', init: 'initBranches', owner: 'admin' });
Router.register('payments', { title: 'Payments', icon: 'wallet', init: 'initPayments', owner: 'admin' });
Router.register('pricing', { title: 'Rate Engine', icon: 'dollar-sign', init: 'initPricing', owner: 'admin' });
Router.register('quality', { title: 'Quality Control', icon: 'flask-conical', init: 'initQuality', owner: 'branch' });
Router.register('rejections', { title: 'Rejections', icon: 'x-circle', init: 'initRejections', owner: 'branch' });
Router.register('procurement', { title: 'Procurement', icon: 'truck', init: 'initProcurement', owner: 'admin' });
Router.register('inventory', { title: 'Inventory', icon: 'package', init: 'initInventory', owner: 'admin' });
Router.register('employees', { title: 'Employees', icon: 'briefcase', init: 'initEmployees', owner: 'admin' });
Router.register('vehicles', { title: 'Vehicles', icon: 'car', init: 'initVehicles', owner: 'admin' });
Router.register('expenses', { title: 'Expenses', icon: 'receipt', init: 'initExpenses', owner: 'admin' });
Router.register('reports', { title: 'Reports', icon: 'bar-chart-3', init: 'initReports', owner: 'shared' });
Router.register('audit', { title: 'Audit Logs', icon: 'scroll-text', init: 'initAudit', owner: 'admin' });
Router.register('settings', { title: 'Settings', icon: 'settings', init: 'initSettings', owner: 'admin' });
Router.register('notifications', { title: 'Notifications', icon: 'bell', init: 'initNotifications', owner: 'shared' });
Router.register('profile', { title: 'My Profile', icon: 'user-circle', init: 'initProfile', owner: 'shared' });
Router.register('help', { title: 'Help Center', icon: 'help-circle', init: 'initHelp', owner: 'shared' });
Router.register('guide', { title: 'User Guide', icon: 'book-open', init: 'initGuide', owner: 'shared' });

// ── Farmer portal routes ──
Router.register('farmer-dashboard', { title: 'My Dashboard', icon: 'layout-dashboard', init: 'initFarmerDashboard', owner: 'farmer' });
Router.register('farmer-collections', { title: 'My Collections', icon: 'milk', init: 'initFarmerCollections', owner: 'farmer' });
Router.register('farmer-daily', { title: 'Daily Collection', icon: 'sunrise', init: 'initFarmerDailyCollection', owner: 'farmer' });
Router.register('my-passbook', { title: 'My Passbook', icon: 'book-open', init: 'initMyPassbook', owner: 'farmer' });
Router.register('farmer-payments', { title: 'My Payments', icon: 'wallet', init: 'initFarmerPayments', owner: 'farmer' });
Router.register('farmer-notifications', { title: 'My Notifications', icon: 'bell', init: 'initFarmerNotifications', owner: 'farmer' });
Router.register('my-profile', { title: 'My Profile', icon: 'user-circle', init: 'initFarmerProfilePage', owner: 'farmer' });
Router.register('farmer-bank-details', { title: 'Bank Details', icon: 'landmark', init: 'initFarmerBankDetails', owner: 'farmer' });
Router.register('farmer-documents', { title: 'My Documents', icon: 'file-text', init: 'initFarmerDocuments', owner: 'farmer' });
Router.register('farmer-grievance', { title: 'Grievance', icon: 'message-square', init: 'initFarmerGrievance', owner: 'farmer' });
Router.register('farmer-settings', { title: 'My Settings', icon: 'settings', init: 'initFarmerSettings', owner: 'farmer' });

window.Router = Router;
