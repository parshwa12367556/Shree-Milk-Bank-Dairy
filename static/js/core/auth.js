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
   * Payment system is fully controlled by the Head Office (Super Admin).
   * @returns {boolean}
   */
  canPay() {
    const role = this.getRole();
    return ['SUPER_ADMIN'].includes(role);
  },

  /**
   * Check if user is a Branch Manager (the only role that registers farmers)
   * @returns {boolean}
   */
  isBranchManager() {
    return this.getRole() === 'BRANCH_MANAGER';
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
  async handleLogin(username, password, branchId, role) {
    try {
      const result = await API.login(username, password, branchId, role);
      
      // Store token and user
      Storage.setToken(result.token);
      const user = result.user || {};
      user.mustChangePassword = !!result.mustChangePassword;
      Storage.setUser(user);
      
      // Smooth transition: hide login, show app layout
      document.getElementById('page-login').style.display = 'none';
      document.querySelector('.app-layout').style.display = 'flex';
      
      // Init app for the logged-in user
      this.initApp();
      
      if (user.mustChangePassword) {
        // First login with the default password — force a password change
        this.openChangePassword(true);
      } else {
        // Redirect to dashboard
        Router.navigate('dashboard');
      }
      
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
      const role = this._getSelectedRole();

      if (!username || !password) {
        this._showError('Please enter username and password');
        return;
      }

      // Show loading state with smooth spinner
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="anim-spin" style="display:inline-flex;width:20px;height:20px;border:2.5px solid rgba(255,255,255,0.3);border-top-color:white;border-radius:50%;margin-right:8px;"></span> Signing in...';

      const result = await this.handleLogin(username, password, branchId, role);

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

    // Role selector tabs
    const roleTabs = document.querySelectorAll('#login-role-tabs .role-tab');
    roleTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        roleTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
      });
    });

    // Language selector
    document.querySelectorAll('.login-language button').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.login-language button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        Storage.setLanguage(btn.dataset.lang);
      });
    });

    // Wire the auth modals (change password / forgot password) once
    this._wireAuthModals();
  },

  /**
   * Get the role selected on the login-screen role tabs
   * @returns {string|null}
   */
  _getSelectedRole() {
    const active = document.querySelector('#login-role-tabs .role-tab.active');
    return active ? active.dataset.role : null;
  },

  /**
   * Wire the change-password and forgot-password modals (idempotent)
   */
  _wireAuthModals() {
    const cpSubmit = document.getElementById('cp-submit');
    if (cpSubmit && !cpSubmit.hasAttribute('data-wired')) {
      cpSubmit.setAttribute('data-wired', '1');
      cpSubmit.addEventListener('click', () => this._submitChangePassword());
    }
    const fpSubmit = document.getElementById('fp-submit');
    if (fpSubmit && !fpSubmit.hasAttribute('data-wired')) {
      fpSubmit.setAttribute('data-wired', '1');
      fpSubmit.addEventListener('click', () => this._handleForgotPasswordStep());
    }
    const fpBack = document.getElementById('fp-back');
    if (fpBack && !fpBack.hasAttribute('data-wired')) {
      fpBack.setAttribute('data-wired', '1');
      fpBack.addEventListener('click', () => this._resetForgotPassword());
    }
  },

  /**
   * Open the change-password modal (forced after first login)
   * @param {boolean} forced - Non-dismissable when true
   */
  openChangePassword(forced = false) {
    const modal = document.getElementById('modal-change-password');
    if (!modal) {
      Router.navigate('dashboard');
      return;
    }
    if (forced) modal.setAttribute('data-force', '');
    else modal.removeAttribute('data-force');
    ['cp-current', 'cp-new', 'cp-confirm'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
    const errEl = document.getElementById('cp-error');
    if (errEl) errEl.style.display = 'none';
    Modal.open('modal-change-password');
  },

  /**
   * Submit the (forced) change-password form
   */
  async _submitChangePassword() {
    const current = document.getElementById('cp-current')?.value.trim();
    const next = document.getElementById('cp-new')?.value.trim();
    const confirm = document.getElementById('cp-confirm')?.value.trim();
    const errEl = document.getElementById('cp-error');
    const showErr = (msg) => { if (errEl) { errEl.textContent = msg; errEl.style.display = 'block'; } };

    if (!current || !next) { showErr('Current and new passwords are required'); return; }
    if (next.length < 6) { showErr('New password must be at least 6 characters'); return; }
    if (next !== confirm) { showErr('Passwords do not match'); return; }

    const btn = document.getElementById('cp-submit');
    if (btn) { btn.disabled = true; btn.textContent = 'Updating...'; }

    try {
      await API.changePassword(current, next);
      const user = Storage.getUser();
      if (user) { user.mustChangePassword = false; Storage.setUser(user); }
      if (errEl) errEl.style.display = 'none';
      Modal.close('modal-change-password');
      Modal.toast({ title: 'Password Updated', message: 'Your password has been changed successfully.', type: 'success' });
      Router.navigate('dashboard');
    } catch (error) {
      showErr(error.message || 'Failed to update password');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="shield-check" style="width:16px;height:16px;"></i> Update Password';
      }
      if (window.lucide) lucide.createIcons();
    }
  },

  /**
   * Open the forgot-password modal (step 1: request OTP)
   */
  openForgotPassword() {
    this._resetForgotPassword();
    Modal.open('modal-forgot-password');
  },

  /**
   * Reset the forgot-password modal back to step 1
   */
  _resetForgotPassword() {
    const s1 = document.getElementById('fp-step-1');
    const s2 = document.getElementById('fp-step-2');
    const back = document.getElementById('fp-back');
    const submit = document.getElementById('fp-submit');
    const devOtp = document.getElementById('fp-dev-otp');
    if (s1) s1.style.display = '';
    if (s2) s2.style.display = 'none';
    if (back) back.style.display = 'none';
    if (submit) submit.innerHTML = 'Send OTP';
    if (devOtp) devOtp.style.display = 'none';
    ['fp-error1', 'fp-error2'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.style.display = 'none';
    });
    const idEl = document.getElementById('fp-identifier');
    if (idEl) idEl.value = document.getElementById('login-username')?.value || '';
  },

  /**
   * Handle the forgot-password flow step (1: send OTP, 2: reset password)
   */
  async _handleForgotPasswordStep() {
    const step2 = document.getElementById('fp-step-2');
    const isStep2 = step2 && step2.style.display !== 'none';
    const submit = document.getElementById('fp-submit');
    const err = (id, msg) => {
      const el = document.getElementById(id);
      if (el) { el.textContent = msg; el.style.display = 'block'; }
    };

    if (submit) submit.disabled = true;
    try {
      if (!isStep2) {
        const identifier = document.getElementById('fp-identifier')?.value.trim();
        if (!identifier) { err('fp-error1', 'Please enter your username or email'); return; }
        const result = await API.forgotPassword(identifier);
        // DEV: show the OTP until real SMS/email delivery is wired
        if (result.dev_otp) {
          const devOtp = document.getElementById('fp-dev-otp');
          if (devOtp) { devOtp.textContent = `Dev mode — your OTP is: ${result.dev_otp}`; devOtp.style.display = 'block'; }
        }
        const s1 = document.getElementById('fp-step-1');
        if (s1) s1.style.display = 'none';
        if (step2) step2.style.display = '';
        const back = document.getElementById('fp-back');
        if (back) back.style.display = '';
        if (submit) submit.innerHTML = 'Reset Password';
      } else {
        const username = document.getElementById('fp-identifier')?.value.trim();
        const otp = document.getElementById('fp-otp')?.value.trim();
        const next = document.getElementById('fp-new')?.value.trim();
        if (!username || !otp) { err('fp-error2', 'Username and OTP are required'); return; }
        if (!next || next.length < 6) { err('fp-error2', 'New password must be at least 6 characters'); return; }
        await API.resetPassword(username, otp, next);
        Modal.close('modal-forgot-password');
        this._resetForgotPassword();
        Modal.toast({ title: 'Password Reset', message: 'Password reset successfully. Please login with your new password.', type: 'success' });
      }
    } catch (error) {
      err(isStep2 ? 'fp-error2' : 'fp-error1', error.message || 'Request failed');
    } finally {
      if (submit) {
        submit.disabled = false;
        // Restore the step-1 label only if we never advanced to step 2
        if (!isStep2 && document.getElementById('fp-step-2')?.style.display === 'none') {
          submit.innerHTML = 'Send OTP';
        }
      }
    }
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

    // Persist selection so it is restored on the next login
    if (!select.hasAttribute('data-branch-listener')) {
      select.setAttribute('data-branch-listener', 'true');
      select.addEventListener('change', () => {
        if (select.value) localStorage.setItem('sd_last_branch', select.value);
      });
    }
  },

  /**
   * Populate branch dropdown from cache or hardcoded fallback
   */
  _loadBranchFallback(select) {
    const cached = Storage.getCache('branches');
    const branches = (cached && cached.length > 0) ? cached : [
      { id: 1, name: 'Nippani Branch', code: 'BR01' },
      { id: 2, name: 'Belagavi Branch', code: 'BR02' },
      { id: 3, name: 'Chikkodi Branch', code: 'BR03' },
      { id: 4, name: 'Sankeshwar Branch', code: 'BR04' },
      { id: 5, name: 'Athani Branch', code: 'BR05' },
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

    // Set branch display (navbar chip)
    const branchEl = document.querySelector('.navbar .current-branch');
    if (branchEl) {
      const nameEl = branchEl.querySelector('.current-branch-name') || branchEl;
      nameEl.textContent = user.branchName || 'All Branches';
      branchEl.title = user.branchName ? `Current Branch: ${user.branchName}` : 'All Branches';
    }

    // Show/hide role-based elements
    document.querySelectorAll('[data-role]').forEach(el => {
      const roles = el.dataset.role.split(',');
      el.style.display = roles.includes(user.role) ? '' : 'none';
    });
  }
};

// Global hook used by the "Forgot password?" link on the login screen
window.forgotPassword = () => Auth.openForgotPassword();

window.Auth = Auth;
