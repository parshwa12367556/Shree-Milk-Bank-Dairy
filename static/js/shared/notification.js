/**
 * ============================================================
 * SMART DAIRY ERP — Notifications Page
 * ============================================================
 * Connected to backend API with Mark All Read
 * ============================================================
 */

let _notificationsData = [];

window.initNotifications = function() {
  console.log('Notifications page initialized');
  loadNotifications();
};

async function loadNotifications() {
  const container = document.getElementById('notifications-list');
  if (!container) return;

  container.innerHTML = '<div class="text-center" style="padding:var(--space-8);color:var(--ink-muted);"><i data-lucide="loader-2" style="width:32px;height:32px;animation:spin 1s linear infinite;"></i><br>Loading notifications...</div>';
  if (window.lucide) lucide.createIcons();

  try {
    const result = await API.getNotifications({ limit: 50 });
    _notificationsData = result.notifications || result.data || [];
    renderNotifications();
  } catch (err) {
    console.warn('Failed to load notifications:', err);
    _notificationsData = [];
    container.innerHTML = `
      <div class="empty-state" style="padding:var(--space-12);text-align:center;">
        <i data-lucide="bell-off" style="width:64px;height:64px;opacity:0.2;margin-bottom:var(--space-4);"></i>
        <h3>No Notifications</h3>
        <p style="color:var(--ink-muted);">No notifications yet. They will appear here as system activity happens.</p>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
  }
}

async function markAllRead() {
  try {
    await API.markNotificationsRead({});
    _notificationsData.forEach(n => n.read = true);
    renderNotifications();
    Modal.toast({ title: 'Marked Read', message: 'All notifications marked as read', type: 'success' });
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message || 'Failed to mark as read', type: 'error' });
  }
}

function renderNotifications() {
  const container = document.getElementById('notifications-list');
  if (!container) return;

  if (!_notificationsData.length) {
    container.innerHTML = `
      <div class="empty-state" style="padding:var(--space-12);text-align:center;">
        <i data-lucide="bell-off" style="width:64px;height:64px;opacity:0.2;margin-bottom:var(--space-4);"></i>
        <h3>No Notifications</h3>
        <p style="color:var(--ink-muted);">No notifications yet.</p>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  const iconMap = {
    collection: { icon: 'milk', bg: 'var(--info-light)', color: 'var(--info)' },
    payment: { icon: 'wallet', bg: 'var(--success-light)', color: 'var(--success)' },
    quality: { icon: 'flask', bg: 'var(--purple-light)', color: 'var(--purple)' },
    system: { icon: 'settings', bg: 'var(--warning-light)', color: 'var(--warning-dark)' },
    farmer: { icon: 'user-plus', bg: 'var(--teal-light)', color: 'var(--teal)' },
  };

  container.innerHTML = _notificationsData.map(n => {
    const meta = iconMap[n.type] || { icon: 'bell', bg: 'var(--gray-100)', color: 'var(--gray-600)' };
    const date = n.createdAt ? fmtDate(n.createdAt, true) : n.time || '';
    return `
      <div class="activity-item" style="${n.read ? '' : 'background: var(--accent-light); border-radius: var(--radius-md); padding: var(--space-3); margin-bottom: var(--space-1);'}">
        <div class="activity-icon" style="background: ${meta.bg}; color: ${meta.color};">
          <i data-lucide="${meta.icon}"></i>
        </div>
        <div class="activity-body">
          <div class="activity-text"><strong>${n.title || ''}</strong></div>
          <div style="font-size:var(--text-sm);color:var(--ink-secondary);margin:var(--space-1) 0;">${n.message || ''}</div>
          <div class="activity-time">${date} ${n.read ? '' : '· <span class="status-dot online" style="display:inline-block;width:6px;height:6px;vertical-align:middle;"></span> New'}</div>
        </div>
      </div>
    `;
  }).join('');
  if (window.lucide) lucide.createIcons();
}

window.markAllRead = markAllRead;
