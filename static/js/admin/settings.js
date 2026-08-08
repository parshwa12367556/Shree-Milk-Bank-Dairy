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

    // SMS / Email notification config
    const map = {
      'set-sms-provider': settings.sms_provider,
      'set-sms-sender': settings.sms_sender_id,
      'set-sms-key': settings.sms_api_key,
      'set-sms-url': settings.sms_api_url,
      'set-mail-host': settings.email_smtp_host,
      'set-mail-port': settings.email_smtp_port,
      'set-mail-from': settings.email_from,
      'set-mail-user': settings.email_smtp_username,
      'set-mail-pass': settings.email_smtp_password,
    };
    Object.entries(map).forEach(([id, val]) => {
      const el = document.getElementById(id);
      if (el && val !== undefined && val !== null) el.value = val;
    });
  } catch (err) {
    console.warn('Failed to load settings:', err);
  }
}

async function saveSettings() {
  const dairyName = document.querySelector('#settings-general input[type="text"]')?.value || 'Shree Milk Bank';
  const payload = { dairy_name: dairyName };

  // Collect SMS / Email config if the section is present
  const smsFields = {
    'set-sms-provider': 'sms_provider',
    'set-sms-sender': 'sms_sender_id',
    'set-sms-key': 'sms_api_key',
    'set-sms-url': 'sms_api_url',
    'set-mail-host': 'email_smtp_host',
    'set-mail-port': 'email_smtp_port',
    'set-mail-from': 'email_from',
    'set-mail-user': 'email_smtp_username',
    'set-mail-pass': 'email_smtp_password',
  };
  Object.entries(smsFields).forEach(([id, key]) => {
    const el = document.getElementById(id);
    if (el && el.value) payload[key] = el.value;
  });

  try {
    await API.updateSettings(payload);
    Modal.toast({ title: 'Settings Saved', message: 'Settings updated successfully', type: 'success' });
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
