/**
 * ============================================================
 * SMART DAIRY ERP — Profile Page
 * ============================================================
 * Profile update and password change via API
 * ============================================================
 */

window.initProfile = function() {
  console.log('Profile page initialized');
  loadProfile();
};

function loadProfile() {
  try {
    const userData = Auth.getUser();
    if (userData) {
      const nameInput = document.querySelector('#page-profile input[type="text"]');
      const emailInput = document.querySelector('#page-profile input[type="email"]');
      const avatarEl = document.querySelector('#page-profile .profile-avatar');
      const nameEl = document.querySelector('#page-profile .profile-header h3');
      const subtitleEl = document.querySelector('#page-profile .profile-header .profile-meta');
      
      if (nameInput) nameInput.value = userData.name || '';
      if (emailInput) emailInput.value = userData.username || '';
      if (nameEl) nameEl.textContent = userData.name || 'Admin User';
      if (avatarEl) avatarEl.textContent = getInitials(userData.name || 'Admin User');
    }
  } catch (err) {
    console.warn('Failed to load profile:', err);
  }
}

async function updateProfile() {
  const name = document.querySelector('#page-profile input[type="text"]')?.value;
  const email = document.querySelector('#page-profile input[type="email"]')?.value;
  const phone = document.querySelector('#page-profile input[type="tel"]')?.value;

  if (!name) {
    Modal.toast({ title: 'Error', message: 'Name is required', type: 'error' });
    return;
  }

  try {
    await API.request('PATCH', '/api/auth/profile', { name, email, phone });
    Modal.toast({ title: 'Profile Updated', message: 'Your profile has been updated successfully', type: 'success' });
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message || 'Failed to update profile', type: 'error' });
  }
}

function changePassword() {
  const currentPw = document.getElementById('profile-current-pw')?.value;
  const newPw = document.getElementById('profile-new-pw')?.value;
  const confirmPw = document.getElementById('profile-confirm-pw')?.value;

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

  Modal.confirm({
    title: 'Change Password',
    message: 'Are you sure you want to change your password?',
    confirmText: 'Change',
    variant: 'warning',
    onConfirm: async () => {
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
      }
    }
  });
}

function forgotPassword() {
  const email = prompt('Enter your email or username to reset password:');
  if (!email) return;

  Modal.toast({ title: 'Sending...', message: 'Requesting password reset...', type: 'info' });

  fetch('/api/auth/forgot-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  })
  .then(r => r.json())
  .then(data => {
    Modal.toast({ title: 'Reset Sent', message: data.message || 'Check your email for reset instructions', type: 'success' });
  })
  .catch(err => {
    Modal.toast({ title: 'Error', message: 'Failed to send reset request', type: 'error' });
  });
}

window.updateProfile = updateProfile;
window.changePassword = changePassword;
window.forgotPassword = forgotPassword;
