/**
 * SHREE MILK BANK — Branch Operator: Notifications
 * Lists the operator's notifications + dairy-wide announcements via
 * GET /api/notifications and marks them read via PATCH /api/notifications.
 */

function _notifIcon(type) {
  const icons = {
    collection: 'milk', payment: 'wallet', quality: 'flask-conical',
    system: 'settings', farmer: 'users',
  };
  return icons[type] || 'bell';
}

async function loadBranchNotifications() {
  const list = document.getElementById('branch-notif-list');
  if (!list) return;
  try {
    const data = await API.getNotifications({ limit: 60 });
    const notifs = data.notifications || [];

    if (!notifs.length) {
      list.innerHTML = `<div style="text-align:center;padding:var(--space-10);">
        <div class="empty-icon" style="margin:0 auto var(--space-3);"><i data-lucide="bell-off" style="width:36px;height:36px;"></i></div>
        <p style="color:var(--ink-muted);font-size:var(--text-sm);">No notifications yet.</p>
      </div>`;
      return;
    }

    list.innerHTML = notifs.map(n => `
      <div style="display:flex;gap:var(--space-3);padding:var(--space-4) var(--space-5);border-bottom:1px solid var(--line);${n.read ? 'opacity:0.65;' : 'background:var(--bg-subtle);'}">
        <div class="kpi-icon" style="width:38px;height:38px;flex-shrink:0;"><i data-lucide="${_notifIcon(n.type)}" style="width:18px;height:18px;"></i></div>
        <div style="flex:1;min-width:0;">
          <div style="display:flex;justify-content:space-between;gap:var(--space-2);align-items:flex-start;">
            <div style="font-weight:600;font-size:var(--text-sm);">${n.title || ''}</div>
            <span style="font-size:var(--text-xs);color:var(--ink-muted);white-space:nowrap;">${fmtDate(n.createdAt)}</span>
          </div>
          <div style="color:var(--ink-muted);font-size:var(--text-sm);margin-top:2px;">${n.message || ''}</div>
          ${n.link ? `<a href="${n.link}" style="font-size:var(--text-xs);color:var(--forest);">View →</a>` : ''}
        </div>
        ${n.read ? '' : '<span class="status-dot online" style="flex-shrink:0;margin-top:6px;"></span>'}
      </div>`).join('');
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.warn('Failed to load notifications:', err);
    list.innerHTML = `<div style="text-align:center;padding:var(--space-10);">
      <p style="color:var(--ink-muted);font-size:var(--text-sm);">Unable to load notifications.</p>
      <button class="btn btn-sm btn-ghost" style="margin-top:var(--space-2);" onclick="window.refreshBranchNotifications && refreshBranchNotifications()">Try Again</button>
    </div>`;
  }
}

window.refreshBranchNotifications = loadBranchNotifications;

window.markAllBranchNotifications = async function () {
  try {
    await API.markNotificationsRead({});
    Modal.toast({ title: 'Done', message: 'All notifications marked as read.', type: 'success' });
    loadBranchNotifications();
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message || 'Could not update notifications.', type: 'error' });
  }
};

window.initBranchNotifications = function () {
  loadBranchNotifications();
};
