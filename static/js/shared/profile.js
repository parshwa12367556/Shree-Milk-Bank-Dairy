/**
 * ============================================================
 * SMART DAIRY ERP — Profile Page (ADMIN / BRANCH_MANAGER)
 * Loads the real logged-in user from GET /api/auth/me and
 * wires the profile update + change-password forms.
 * ============================================================
 */

window.initProfile = function () {
  loadProfile();
  initSharedProfileForm();
  initPasswordForm();
};

async function loadProfile() {
  try {
    const res = await API.getMe();
    const user = (res && res.user) || Auth.getUser() || {};
    const nameEl = document.getElementById('profile-name');
    const avatarEl = document.getElementById('profile-avatar-text');
    const subEl = document.getElementById('profile-username');
    const roleTag = document.getElementById('profile-role-tag');
    const branchEl = document.getElementById('profile-branch');
    const lastLoginEl = document.getElementById('profile-last-login');

    const roleMap = { ADMIN: 'Admin', BRANCH_MANAGER: 'Branch Manager', FARMER: 'Farmer' };
    const roleClassMap = { ADMIN: 'tag-green', BRANCH_MANAGER: 'tag-blue', FARMER: 'tag-gold' };

    if (nameEl) nameEl.textContent = user.name || user.username || '—';
    if (avatarEl) avatarEl.textContent = getInitials(user.name || user.username || 'U');
    if (subEl) subEl.textContent = `@${user.username || '—'}`;
    if (roleTag) {
      const role = user.role || '—';
      roleTag.innerHTML = `<span class="tag ${roleClassMap[role] || 'tag-neutral'}">${roleMap[role] || role}</span>`;
    }
    if (branchEl) {
      branchEl.innerHTML = user.branchName
        ? `<i data-lucide="building-2" style="width:13px;height:13px;vertical-align:-2px;"></i> ${user.branchName}`
        : '<i data-lucide="globe" style="width:13px;height:13px;vertical-align:-2px;"></i> All Branches';
    }
    if (lastLoginEl) {
      lastLoginEl.textContent = user.lastLoginAt ? `Last login: ${fmtDate(user.lastLoginAt, true)}` : '';
    }
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.warn('Failed to load profile:', err);
    // Fall back to the cached user so the page is never blank
    const user = Auth.getUser();
    if (user) {
      const nameEl = document.getElementById('profile-name');
      const avatarEl = document.getElementById('profile-avatar-text');
      if (nameEl) nameEl.textContent = user.name || user.username;
      if (avatarEl) avatarEl.textContent = getInitials(user.name || user.username);
    }
  }
}

function initSharedProfileForm() {
  const form = document.getElementById('form-profile-update');
  if (!form || form.hasAttribute('data-listener')) return;
  form.setAttribute('data-listener', 'true');

  // Pre-fill with cached values so the form is never empty
  const user = Auth.getUser() || {};
  const set = (id, v) => { const el = document.getElementById(id); if (el) el.value = v || ''; };
  set('pf-name', user.name);
  set('pf-email', user.email || '');
  set('pf-phone', user.phone || '');
  set('pf-username', user.username);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    const name = document.getElementById('pf-name').value.trim();
    const email = document.getElementById('pf-email').value.trim();
    const phone = document.getElementById('pf-phone').value.trim();

    if (!name) {
      Modal.toast({ title: 'Error', message: 'Name is required', type: 'error' });
      return;
    }
    if (btn) { btn.disabled = true; btn.innerHTML = 'Saving…'; }
    try {
      await API.request('PATCH', '/api/auth/profile', { name, email, phone });
      Modal.toast({ title: 'Profile Updated', message: 'Your profile has been updated successfully', type: 'success' });
      loadProfile();
    } catch (err) {
      Modal.toast({ title: 'Error', message: err.message || 'Failed to update profile', type: 'error' });
    } finally {
      if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="save" style="width:16px;height:16px;"></i> Update Profile'; if (window.lucide) lucide.createIcons(); }
    }
  });
}

function initPasswordForm() {
  const form = document.getElementById('form-profile-password');
  if (!form || form.hasAttribute('data-listener')) return;
  form.setAttribute('data-listener', 'true');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const currentPw = document.getElementById('profile-current-pw')?.value || '';
    const newPw = document.getElementById('profile-new-pw')?.value || '';
    const confirmPw = document.getElementById('profile-confirm-pw')?.value || '';

    if (!currentPw || !newPw) {
      Modal.toast({ title: 'Error', message: 'Current and new passwords are required', type: 'error' });
      return;
    }
    if (newPw !== confirmPw) {
      Modal.toast({ title: 'Error', message: 'New passwords do not match', type: 'error' });
      return;
    }
    if (newPw.length < 6) {
      Modal.toast({ title: 'Error', message: 'New password must be at least 6 characters', type: 'error' });
      return;
    }
    const btn = form.querySelector('button[type="submit"]');
    if (btn) { btn.disabled = true; btn.innerHTML = 'Changing…'; }
    try {
      await API.request('POST', '/api/auth/change-password', {
        current_password: currentPw,
        new_password: newPw,
      });
      document.getElementById('profile-current-pw').value = '';
      document.getElementById('profile-new-pw').value = '';
      document.getElementById('profile-confirm-pw').value = '';
      Modal.toast({ title: 'Password Changed', message: 'Your password has been changed successfully', type: 'success' });
    } catch (err) {
      Modal.toast({ title: 'Error', message: err.message || 'Failed to change password', type: 'error' });
    } finally {
      if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="key-round" style="width:16px;height:16px;"></i> Change Password'; if (window.lucide) lucide.createIcons(); }
    }
  });
}
