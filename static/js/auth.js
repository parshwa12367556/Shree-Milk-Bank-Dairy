/**
 * ============================================================
 * SMART DAIRY ERP — Authentication Module
 * ============================================================
 */

const Auth = {
  /**
   * Check if user is authenticated
   * @returns {boolean}
   */
  isAuthenticated() {
    return !!Storage.getToken();
  },

  /**
   * Get current user
   * @returns {object|null}
   */
  getUser() {
    return Storage.getUser();
  },

  /**
   * Get user role
   * @returns {string|null}
   */
  getRole() {
    const user = this.getUser();
    return user ? user.role : null;
  },

  /**
   * Check if user has global role (SUPER_ADMIN, HEAD_OFFICE)
   * @returns {boolean}
   */
  isGlobalRole() {
    const role = this.getRole();
    return role === 'SUPER_ADMIN' || role === 'HEAD_OFFICE';
  },

  /**
   * Check if user can collect milk
   * @returns {boolean}
   */
  canCollect() {
    const role = this.getRole();
    return ['SUPER_ADMIN', 'BRANCH_MANAGER', 'OPERATOR'].includes(role);
  },

  /**
   * Check if user can process payments
   * @returns {boolean}
   */
  canPay() {
    const role = this.getRole();
    return ['SUPER_ADMIN', 'HEAD_OFFICE', 'ACCOUNTANT'].includes(role);
  },

  /**
   * Check if user can manage rates
   * @returns {boolean}
   */
  canManageRates() {
    const role = this.getRole();
    return ['SUPER_ADMIN', 'HEAD_OFFICE'].includes(role);
  },

  /**
   * Handle login form submission
   */
  async handleLogin(username, password, branchId) {
    try {
      const result = await API.login(username, password, branchId);
      
      // Store token and user
      Storage.setToken(result.token);
      Storage.setUser(result.user);
      
      // Smooth transition: hide login, show app layout
      document.getElementById('page-login').style.display = 'none';
      document.querySelector('.app-layout').style.display = 'flex';
      
      // Init app for the logged-in user
      this.initApp();
      
      // Redirect to dashboard
      Router.navigate('dashboard');
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  /**
   * Handle logout — smooth transition without page reload
   */
  async handleLogout() {
    try {
      await API.logout();
    } catch (e) {
      // Ignore errors on logout
    }
    
    Storage.remove('sd_token');
    Storage.remove('sd_user');
    
    // Smooth transition: hide app, show login
    document.querySelector('.app-layout').style.display = 'none';
    document.getElementById('page-login').style.display = 'flex';
    
    // Re-initialize login page
    this.initLoginPage();
    
    Router.navigate('login', true);
  },

  /**
   * Initialize login page
   */
  initLoginPage() {
    const loginForm = document.getElementById('login-form');
    if (!loginForm) return;

    const submitBtn = loginForm.querySelector('.btn-login');
    const errorDiv = loginForm.querySelector('.login-error');

    // Load branches
    this._loadBranches();

    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const username = document.getElementById('login-username')?.value.trim();
      const password = document.getElementById('login-password')?.value.trim();
      const branchId = document.getElementById('login-branch')?.value;

      if (!username || !password) {
        this._showError('Please enter username and password');
        return;
      }

      // Show loading state with smooth spinner
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="anim-spin" style="display:inline-flex;width:20px;height:20px;border:2.5px solid rgba(255,255,255,0.3);border-top-color:white;border-radius:50%;margin-right:8px;"></span> Signing in...';

      const result = await this.handleLogin(username, password, branchId);

      if (!result.success) {
        this._showError(result.error);
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Sign In';
      }
    });

    // Password visibility toggle
    const toggleBtn = document.getElementById('toggle-password');
    const passwordInput = document.getElementById('login-password');
    if (toggleBtn && passwordInput) {
      toggleBtn.addEventListener('click', () => {
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
        toggleBtn.innerHTML = type === 'password' ? '<i data-lucide="eye"></i>' : '<i data-lucide="eye-off"></i>';
        if (window.lucide) lucide.createIcons();
      });
    }

    // Remember me
    const rememberMe = document.getElementById('remember-me');
    if (rememberMe) {
      const saved = localStorage.getItem('sd_remember_user');
      if (saved) {
        document.getElementById('login-username').value = saved;
        rememberMe.checked = true;
      }
      rememberMe.addEventListener('change', () => {
        const username = document.getElementById('login-username').value;
        if (rememberMe.checked && username) {
          localStorage.setItem('sd_remember_user', username);
        } else {
          localStorage.removeItem('sd_remember_user');
        }
      });
    }

    // Language selector
    document.querySelectorAll('.login-language button').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.login-language button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        Storage.setLanguage(btn.dataset.lang);
      });
    });
  },

  /**
   * Load branches for login dropdown
   * Shows hardcoded fallback immediately, then tries to update from API
   */
  async _loadBranches() {
    const select = document.getElementById('login-branch');
    if (!select) return;

    // Show fallback branches immediately (synchronous - always works)
    this._loadBranchFallback(select);

    // Then try to get live data from API (async - may fail)
    try {
      const result = await API.getBranches();
      const branches = result.branches || result.data || result || [];
      
      if (branches.length > 0) {
        this._populateBranchDropdown(select, branches);
      }
    } catch (error) {
      console.warn('Could not load branches from API, using fallback:', error);
      // Fallback is already shown, nothing more to do
    }

    // Restore last selected branch
    const lastBranch = localStorage.getItem('sd_last_branch');
    if (lastBranch) select.value = lastBranch;
  },

  /**
   * Populate branch dropdown from cache or hardcoded fallback
   */
  _loadBranchFallback(select) {
    const cached = Storage.getCache('branches');
    const branches = (cached && cached.length > 0) ? cached : [
      { id: 1, name: 'Agar Malwa Main', code: 'BR-001' },
      { id: 2, name: 'Susner Sub', code: 'BR-002' },
      { id: 3, name: 'Kannod Branch', code: 'BR-003' },
      { id: 4, name: 'Shajapur Branch', code: 'BR-004' },
    ];
    this._populateBranchDropdown(select, branches);
  },

  /**
   * Populate branch select element with options
   */
  _populateBranchDropdown(select, branches) {
    select.innerHTML = '<option value="">Select Branch</option>';
    branches.forEach(branch => {
      const opt = document.createElement('option');
      opt.value = branch.id;
      opt.textContent = `${branch.name} (${branch.code})`;
      select.appendChild(opt);
    });
  },

  /**
   * Show error message
   */
  _showError(message) {
    const errorDiv = document.querySelector('.login-error');
    if (errorDiv) {
      errorDiv.textContent = message;
      errorDiv.classList.add('visible');
      setTimeout(() => errorDiv.classList.remove('visible'), 5000);
    }
  },

  /**
   * Initialize app after login
   */
  initApp() {
    const user = this.getUser();
    if (!user) return;

    // Update user info in sidebar footer
    const userNameEls = document.querySelectorAll('.user-info .user-name, .user-meta .user-name');
    const userRoleEls = document.querySelectorAll('.user-info .user-role, .user-meta .user-role');
    const avatarEls = document.querySelectorAll('.user-avatar');

    userNameEls.forEach(el => { el.textContent = user.name || user.username; });
    userRoleEls.forEach(el => { 
      const roleMap = {
        SUPER_ADMIN: 'Super Admin',
        HEAD_OFFICE: 'Head Office',
        BRANCH_MANAGER: 'Branch Manager',
        OPERATOR: 'Operator',
        ACCOUNTANT: 'Accountant'
      };
      el.textContent = roleMap[user.role] || user.role;
    });
    avatarEls.forEach(el => {
      el.textContent = getInitials(user.name || user.username);
    });

    // Set branch display
    if (user.branchName) {
      const branchEl = document.querySelector('.navbar .current-branch');
      if (branchEl) branchEl.textContent = user.branchName;
    }

    // Show/hide role-based elements
    document.querySelectorAll('[data-role]').forEach(el => {
      const roles = el.dataset.role.split(',');
      el.style.display = roles.includes(user.role) ? '' : 'none';
    });
  }
};

window.Auth = Auth;
