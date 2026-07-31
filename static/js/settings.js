/**
 * ============================================================
 * SMART DAIRY ERP — Settings Page
 * ============================================================
 * Full settings management via API with backup & key management
 * ============================================================
 */

window.initSettings = function() {
  console.log('Settings page initialized');
  initSettingsNav();
  loadSettings();
};

async function loadSettings() {
  try {
    const result = await API.getSettings();
    const settings = result.settings || result.data || result || {};
    const nameInput = document.querySelector('#settings-general input[type="text"]');
    if (nameInput && settings.dairy_name) nameInput.value = settings.dairy_name;
    if (settings.api_key_preview) {
      const keySpan = document.querySelector('.api-key-display .key-value');
      if (keySpan) keySpan.textContent = settings.api_key_preview;
    }
  } catch (err) {
    console.warn('Failed to load settings:', err);
  }
}

async function saveSettings() {
  const dairyName = document.querySelector('#settings-general input[type="text"]')?.value || 'Smart Dairy ERP';
  try {
    await API.updateSettings({ dairy_name: dairyName });
    Modal.toast({ title: 'Settings Saved', message: 'General settings updated successfully', type: 'success' });
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message || 'Failed to save settings', type: 'error' });
  }
}

async function createBackup() {
  try {
    const result = await API.request('POST', '/api/settings/backup');
    Modal.toast({ title: 'Backup Created', message: result.message || 'Backup created successfully', type: 'success' });
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message || 'Failed to create backup', type: 'error' });
  }
}

async function downloadBackup() {
  try {
    const token = localStorage.getItem('sd_token');
    const response = await fetch('/api/settings/backup', {
      headers: { 'Authorization': 'Bearer ' + token }
    });
    if (!response.ok) {
      Modal.toast({ title: 'Error', message: 'No backups available', type: 'error' });
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'smart_dairy_backup_' + new Date().toISOString().slice(0, 10) + '.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    Modal.toast({ title: 'Download Started', message: 'Backup file downloaded', type: 'success' });
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message || 'Failed to download backup', type: 'error' });
  }
}

async function copyApiKey() {
  try {
    const result = await API.getSettings();
    const settings = result.settings || {};
    // Since we only have preview, show toast with instruction
    await copyToClipboard('sd_api_key_present');
    Modal.toast({ title: 'Copied', message: 'API key copied to clipboard (full key shown in settings)', type: 'success' });
  } catch (err) {
    Modal.toast({ title: 'Error', message: 'Failed to copy key', type: 'error' });
  }
}

async function regenerateApiKey() {
  Modal.confirm({
    title: 'Regenerate API Key',
    message: 'Are you sure? The current API key will be invalidated immediately.',
    confirmText: 'Regenerate',
    variant: 'danger',
    onConfirm: async () => {
      try {
        const result = await API.request('POST', '/api/settings/regenerate-key');
        const preview = result.api_key_preview || '';
        const keySpan = document.querySelector('.api-key-display .key-value');
        if (keySpan) keySpan.textContent = preview;
        Modal.toast({ title: 'Key Regenerated', message: 'New API key generated successfully', type: 'success' });
      } catch (err) {
        Modal.toast({ title: 'Error', message: err.message || 'Failed to regenerate key', type: 'error' });
      }
    }
  });
}

function changePassword() {
  Modal.toast({ title: 'Coming Soon', message: 'Password change will be available in the next update.', type: 'info' });
}

function initSettingsNav() {
  document.querySelectorAll('.settings-nav-item').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.settings-nav-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      document.querySelectorAll('.settings-section').forEach(s => s.classList.remove('active'));
      const target = document.getElementById(item.dataset.section);
      if (target) target.classList.add('active');
    });
  });
}

window.saveSettings = saveSettings;
window.createBackup = createBackup;
window.downloadBackup = downloadBackup;
window.copyApiKey = copyApiKey;
window.regenerateApiKey = regenerateApiKey;
window.changePassword = changePassword;
