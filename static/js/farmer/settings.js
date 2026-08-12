/**
 * SHREE MILK BANK — Farmer: Settings
 * - Change password via POST /api/auth/change-password
 * - Notification preferences via GET/PATCH /api/farmer/me/settings
 */

async function loadFarmerSettings() {
  try {
    const data = await API.getMySettings();
    const s = (data && data.settings) || {};
    const set = (id, v) => { const el = document.getElementById(id); if (el) el.checked = !!v; };
    set('pref-sms', s.notificationSms);
    set('pref-whatsapp', s.notificationWhatsapp);
    set('pref-email', s.notificationEmail);
  } catch (err) {
    console.warn('Failed to load settings:', err);
  }
}

window.initFarmerSettings = function () {
  loadFarmerSettings();

  // ── Change password ──
  const form = document.getElementById('form-farmer-password');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const current = document.getElementById('fp-current').value.trim();
      const next = document.getElementById('fp-new').value.trim();
      const confirm = document.getElementById('fp-confirm').value.trim();

      if (!current || !next) {
        Modal.toast({ title: 'Error', message: 'Current and new passwords are required.', type: 'error' });
        return;
      }
      if (next.length < 6) {
        Modal.toast({ title: 'Error', message: 'New password must be at least 6 characters.', type: 'error' });
        return;
      }
      if (next !== confirm) {
        Modal.toast({ title: 'Error', message: 'New passwords do not match.', type: 'error' });
        return;
      }

      const btn = form.querySelector('button[type="submit"]');
      if (btn) { btn.disabled = true; btn.innerHTML = '<span class="anim-spin" style="display:inline-flex;width:16px;height:16px;border:2.5px solid rgba(255,255,255,0.3);border-top-color:white;border-radius:50%;margin-right:8px;"></span> Updating…'; }
      try {
        await API.changePassword(current, next);
        form.reset();
        Modal.toast({ title: 'Password Updated', message: 'Your password has been changed successfully.', type: 'success' });
      } catch (err) {
        Modal.toast({ title: 'Error', message: err.message || 'Could not change password.', type: 'error' });
      } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="shield-check" style="width:16px;height:16px;"></i> Update Password'; if (window.lucide) lucide.createIcons(); }
      }
    });
  }

  // ── Notification preferences ──
  const saveBtn = document.getElementById('btn-save-prefs');
  if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
      saveBtn.disabled = true;
      try {
        const payload = {
          notificationSms: document.getElementById('pref-sms')?.checked,
          notificationWhatsapp: document.getElementById('pref-whatsapp')?.checked,
          notificationEmail: document.getElementById('pref-email')?.checked,
        };
        await API.updateMySettings(payload);
        Modal.toast({ title: 'Saved', message: 'Notification preferences updated.', type: 'success' });
      } catch (err) {
        Modal.toast({ title: 'Error', message: err.message || 'Could not save preferences.', type: 'error' });
      } finally {
        saveBtn.disabled = false;
      }
    });
  }
};
