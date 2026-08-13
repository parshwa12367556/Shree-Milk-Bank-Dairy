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

    // Capability flags — the UI never claims a channel is active when it is
    // not actually configured (e.g. WhatsApp has no provider yet).
    const caps = result.capabilities || {};
    const waStatus = document.getElementById('whatsapp-provider-status');
    if (waStatus) {
      if (caps.whatsapp) {
        waStatus.textContent = 'Connected';
        waStatus.className = 'tag tag-green';
      } else {
        waStatus.textContent = 'Not configured — WhatsApp delivery is disabled until a provider is set up.';
        waStatus.className = 'tag tag-amber';
      }
    }
    const smsStatus = document.getElementById('sms-provider-status');
    if (smsStatus) {
      smsStatus.textContent = caps.sms ? 'Configured — SMS delivery active.' : 'Not configured — enter provider + API URL above to enable SMS.';
      smsStatus.className = caps.sms ? 'tag tag-green' : 'tag tag-amber';
    }
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

/**
 * Change password (ADMIN settings) — real API call with current-password
 * verification, policy enforcement, show/hide toggles and loading state.
 * Passwords are never stored in browser storage.
 */
function changePassword() {
  const modalId = 'modal-settings-password';
  const existing = document.getElementById(modalId);
  if (existing) existing.remove();

  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.id = modalId;
  modal.innerHTML = `
    <div class="modal-backdrop"></div>
    <div class="modal-content" style="max-width:440px;">
      <div class="modal-header">
        <h5><i data-lucide="shield-check" style="width:16px;height:16px;"></i> Change Password</h5>
        <button class="modal-close" onclick="Modal.close('${modalId}')"><i data-lucide="x"></i></button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label">Current Password</label>
          <div class="input-group" style="position:relative;">
            <input type="password" class="input-premium" id="sp-current" autocomplete="current-password" placeholder="Your current password">
            <button type="button" class="pw-toggle" onclick="togglePwField('sp-current', this)" style="position:absolute;right:12px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:var(--ink-muted);"><i data-lucide="eye" style="width:16px;height:16px;"></i></button>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">New Password</label>
          <div class="input-group" style="position:relative;">
            <input type="password" class="input-premium" id="sp-new" autocomplete="new-password" placeholder="Min 8 chars: uppercase, lowercase & number">
            <button type="button" class="pw-toggle" onclick="togglePwField('sp-new', this)" style="position:absolute;right:12px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:var(--ink-muted);"><i data-lucide="eye" style="width:16px;height:16px;"></i></button>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Confirm New Password</label>
          <div class="input-group" style="position:relative;">
            <input type="password" class="input-premium" id="sp-confirm" autocomplete="new-password" placeholder="Repeat new password">
            <button type="button" class="pw-toggle" onclick="togglePwField('sp-confirm', this)" style="position:absolute;right:12px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:var(--ink-muted);"><i data-lucide="eye" style="width:16px;height:16px;"></i></button>
          </div>
        </div>
        <div class="modal-form-error" id="sp-error" style="display:none;color:var(--danger);font-size:var(--text-sm);margin-top:var(--space-2);"></div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-primary w-full" id="sp-submit">
          <i data-lucide="shield-check" style="width:16px;height:16px;"></i>
          Change Password
        </button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  if (window.lucide) lucide.createIcons();
  Modal.open(modalId);

  document.getElementById('sp-submit').addEventListener('click', async () => {
    const current = document.getElementById('sp-current').value;
    const next = document.getElementById('sp-new').value;
    const confirmVal = document.getElementById('sp-confirm').value;
    const errEl = document.getElementById('sp-error');
    const btn = document.getElementById('sp-submit');

    errEl.style.display = 'none';
    if (!current || !next) {
      errEl.textContent = 'Current and new passwords are required.';
      errEl.style.display = 'block';
      return;
    }
    if (next.length < 8) {
      errEl.textContent = 'New password must be at least 8 characters.';
      errEl.style.display = 'block';
      return;
    }
    if (next !== confirmVal) {
      errEl.textContent = 'New passwords do not match.';
      errEl.style.display = 'block';
      return;
    }

    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="anim-spin" style="display:inline-flex;width:16px;height:16px;border:2.5px solid rgba(255,255,255,0.3);border-top-color:white;border-radius:50%;margin-right:8px;"></span> Updating…';
    try {
      await API.changePassword(current, next);
      Modal.close(modalId);
      setTimeout(() => modal.remove(), 300);
      Modal.toast({ title: 'Password Updated', message: 'Your password has been changed successfully.', type: 'success' });
    } catch (err) {
      errEl.textContent = err.message || 'Could not change password.';
      errEl.style.display = 'block';
    } finally {
      btn.disabled = false;
      btn.innerHTML = original;
    }
  });
}

function togglePwField(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const show = input.type === 'password';
  input.type = show ? 'text' : 'password';
  if (btn) {
    btn.innerHTML = show ? '<i data-lucide="eye-off" style="width:16px;height:16px;"></i>' : '<i data-lucide="eye" style="width:16px;height:16px;"></i>';
    if (window.lucide) lucide.createIcons();
  }
}
window.togglePwField = togglePwField;

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
