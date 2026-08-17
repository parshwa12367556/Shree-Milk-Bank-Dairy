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
   * Check if user has global (admin) role
   * @returns {boolean}
   */
  isGlobalRole() {
    const role = this.getRole();
    return role === 'ADMIN';
  },

  /**
   * Check if user can collect milk
   * @returns {boolean}
   */
  canCollect() {
    const role = this.getRole();
    return ['ADMIN', 'BRANCH_MANAGER'].includes(role);
  },

  /**
   * Check if user can process payments
   * Payment actions are exclusively performed by the ADMIN role.
   * @returns {boolean}
   */
  canPay() {
    const role = this.getRole();
    return ['ADMIN'].includes(role);
  },

  /**
   * Check if user is a Branch Manager (registers farmers for own branch)
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
    return ['ADMIN'].includes(role);
  },

  /**
   * Handle login form submission — common Login ID + Password.
   * The backend detects the role and returns redirect_url; the frontend
   * never sends (or trusts) a role from the browser.
   */
  async handleLogin(loginId, password, rememberMe = false, portalRole = null) {
    try {
      const result = await API.login(loginId, password, rememberMe, portalRole);
      
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
        // First login with the temporary password — force a password change
        this.openChangePassword(true);
      } else {
        // Redirect to the role home (dashboard / farmer-dashboard)
        Router.navigate(Router.homeRoute());
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

    // Stop the farmer dashboard's background polling on logout.
    if (typeof window.stopFarmerPolling === 'function') {
      window.stopFarmerPolling();
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
   * Initialize login page — one common Login ID + Password form. No role
   * selection: the backend detects the role from the users table.
   */
  initLoginPage() {
    const loginForm = document.getElementById('login-form');
    if (!loginForm) return;

    const submitBtn = loginForm.querySelector('.btn-login');

    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const loginId = document.getElementById('login-username')?.value.trim();
      const password = document.getElementById('login-password')?.value;
      const rememberMe = document.getElementById('remember-me')?.checked || false;
      const portalRole = loginForm.dataset.portalRole || '';

      if (!portalRole) {
        this._showError('Please select the portal you want to sign in to');
        return;
      }
      if (!loginId || !password) {
        this._showError('Please enter your ID and password');
        return;
      }

      // Show loading state with smooth spinner
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="anim-spin" style="display:inline-flex;width:20px;height:20px;border:2.5px solid rgba(255,255,255,0.3);border-top-color:white;border-radius:50%;margin-right:8px;"></span> Signing in...';

      const result = await this.handleLogin(loginId, password, rememberMe, portalRole);

      if (!result.success) {
        this._showError(result.error);
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i data-lucide="log-in"></i> Sign In';
        if (window.lucide) lucide.createIcons();
      }
    });

    const portals = {
      ADMIN: { label: 'Administrator', idLabel: 'Admin Login ID', placeholder: 'e.g. ADMIN001', icon: 'shield-check' },
      BRANCH_MANAGER: { label: 'Branch Manager', idLabel: 'Manager Login ID', placeholder: 'e.g. BR01MG001', icon: 'building-2' },
      FARMER: { label: 'Farmer', idLabel: 'Farmer Code', placeholder: 'e.g. BR01001', icon: 'tractor' },
    };
    document.querySelectorAll('[data-portal-role]').forEach(button => {
      button.addEventListener('click', () => {
        const role = button.dataset.portalRole;
        const portal = portals[role];
        if (!portal) return;
        loginForm.dataset.portalRole = role;
        document.querySelectorAll('[data-portal-role]').forEach(item => {
          item.classList.toggle('active', item === button);
          item.setAttribute('aria-pressed', item === button ? 'true' : 'false');
        });
        document.getElementById('login-username-label').textContent = portal.idLabel;
        document.getElementById('login-username').placeholder = portal.placeholder;
        document.getElementById('login-portal-title').textContent = `${portal.label} Sign In`;
        document.getElementById('login-portal-description').textContent = `Sign in to your ${portal.label.toLowerCase()} portal.`;
        const icon = document.getElementById('login-username-icon');
        if (icon) icon.innerHTML = `<i data-lucide="${portal.icon}"></i>`;
        if (window.lucide) lucide.createIcons();
        document.getElementById('login-username')?.focus();
      });
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

    // Remember Me — remembers the Login ID only (never the password)
    const rememberMe = document.getElementById('remember-me');
    if (rememberMe) {
      const saved = localStorage.getItem('sd_remember_login');
      if (saved) {
        document.getElementById('login-username').value = saved;
        rememberMe.checked = true;
      }
      rememberMe.addEventListener('change', () => {
        const loginId = document.getElementById('login-username').value;
        if (rememberMe.checked && loginId) {
          localStorage.setItem('sd_remember_login', loginId);
        } else {
          localStorage.removeItem('sd_remember_login');
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

    // Wire the auth modals (change password / forgot password) once
    this._wireAuthModals();
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
    const policyError = Auth.passwordPolicyError(next);
    if (policyError) { showErr(policyError); return; }
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
   * Password policy — mirrors the backend policy (spec §21).
   * @param {string} password
   * @returns {string|null} First violation message, or null if valid
   */
  passwordPolicyError(password) {
    const p = password || '';
    if (p.length < 8) return 'Password must be at least 8 characters';
    if (!/[A-Z]/.test(p)) return 'Password must contain at least one uppercase letter';
    if (!/[a-z]/.test(p)) return 'Password must contain at least one lowercase letter';
    if (!/\d/.test(p)) return 'Password must contain at least one number';
    return null;
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
   * Legacy alias kept for any inline handlers — same as passwordPolicyError.
   * @param {string} password
   * @returns {string|null}
   */
  _passwordPolicyError(password) {
    return this.passwordPolicyError(password);
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
        if (!identifier) { err('fp-error1', 'Please enter your Login ID or email'); return; }
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
        const loginId = document.getElementById('fp-identifier')?.value.trim();
        const otp = document.getElementById('fp-otp')?.value.trim();
        const next = document.getElementById('fp-new')?.value.trim();
        if (!loginId || !otp) { err('fp-error2', 'Login ID and OTP are required'); return; }
        const policyError = Auth.passwordPolicyError(next);
        if (policyError) { err('fp-error2', policyError); return; }
        await API.resetPassword(loginId, otp, next);
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
        ADMIN: 'Admin',
        BRANCH_MANAGER: 'Branch Manager',
        FARMER: 'Farmer'
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

    // Farmer portal: point generic navbar links at the farmer equivalents
    if (user.role === 'FARMER') {
      const linkMap = {
        '#profile': '#my-profile',
        '#settings': '#farmer-settings',
        '#notifications': '#farmer-notifications',
      };
      document.querySelectorAll('a[href]').forEach(a => {
        const href = a.getAttribute('href');
        if (href && linkMap[href]) a.setAttribute('href', linkMap[href]);
      });
    }
  }
};

// Global hook used by the "Forgot password?" link on the login screen
window.forgotPassword = () => Auth.openForgotPassword();

window.Auth = Auth;
