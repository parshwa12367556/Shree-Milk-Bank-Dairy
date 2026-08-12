/**
 * SHREE MILK BANK — Farmer: Notifications / Milk Messages
 * Loads the authenticated farmer's notifications from
 * GET /api/farmer/me/notifications (own + dairy-wide).
 */
let _notifFetched = false;

async function loadFarmerNotifications() {
  const list = document.getElementById('fm-notifications-list');
  if (list && !_notifFetched) {
    list.innerHTML = '<div style="text-align:center;padding:var(--space-8);"><div class="empty-icon" style="margin:0 auto var(--space-3);"><i data-lucide="bell" style="width:36px;height:36px;"></i></div><p style="color:var(--ink-muted);font-size:var(--text-sm);">Loading notifications…</p></div>';
  }

  try {
    const data = await API.getMyNotifications({ limit: 100 });
    _notifFetched = true;
    const notifs = data.notifications || [];
    const unread = data.unreadCount || 0;

    const unreadTag = document.getElementById('fm-notif-unread-tag');
    if (unreadTag) unreadTag.textContent = `${unread} unread`;

    if (!list) return;
    if (!notifs.length) {
      list.innerHTML = `<div style="text-align:center;padding:var(--space-10);">
        <div class="empty-icon" style="margin:0 auto var(--space-4);"><i data-lucide="bell-off" style="width:48px;height:48px;"></i></div>
        <h4 style="margin-bottom:var(--space-2);">No notifications</h4>
        <p style="color:var(--ink-muted);max-width:440px;margin:0 auto;font-size:var(--text-sm);">When the branch records your milk or the head office processes a payment, the message will appear here automatically.</p>
      </div>`;
    } else {
      list.innerHTML = notifs.map(n => {
        const icon = n.type === 'payment' ? 'wallet' : n.type === 'collection' ? 'milk' : n.type === 'quality' ? 'flask-conical' : 'megaphone';
        return `
        <div style="display:flex;gap:var(--space-3);padding:var(--space-3) 0;border-bottom:1px solid var(--line);${n.read ? 'opacity:0.75;' : ''}">
          <div class="notif-icon" style="width:40px;height:40px;border-radius:var(--radius-full);display:flex;align-items:center;justify-content:center;flex-shrink:0;background:${n.read ? 'var(--bg-subtle)' : 'var(--forest-light)'};color:${n.read ? 'var(--ink-muted)' : 'var(--forest)'};">
            <i data-lucide="${icon}" style="width:18px;height:18px;"></i>
          </div>
          <div style="flex:1;min-width:0;">
            <div style="display:flex;justify-content:space-between;gap:var(--space-2);align-items:flex-start;">
              <span style="font-weight:600;font-size:var(--text-sm);">${n.title || ''}</span>
              ${n.read ? '' : '<span class="status-dot online" style="display:inline-block;flex-shrink:0;margin-top:6px;"></span>'}
            </div>
            <div style="color:var(--ink-muted);font-size:var(--text-sm);margin-top:2px;white-space:pre-line;">${n.message || ''}</div>
            <div style="color:var(--ink-muted);font-size:var(--text-xs);margin-top:4px;">${fmtDate(n.createdAt)}</div>
          </div>
        </div>`;
      }).join('');
    }
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.warn('Failed to load notifications:', err);
    if (list) list.innerHTML = `<div style="text-align:center;padding:var(--space-8);">
      <div class="empty-icon" style="margin:0 auto var(--space-3);"><i data-lucide="bell-off" style="width:36px;height:36px;"></i></div>
      <p style="color:var(--ink-muted);font-size:var(--text-sm);">Unable to load notifications. Try again.</p>
      <button class="btn btn-sm btn-ghost" style="margin-top:var(--space-2);" onclick="window.refreshFarmerNotifications && refreshFarmerNotifications()">Try Again</button>
    </div>`;
  }
}

window.refreshFarmerNotifications = function () {
  loadFarmerNotifications();
};

window.markAllFarmerNotificationsRead = async function () {
  try {
    await API.markMyNotificationsRead({});
    await loadFarmerNotifications();
    if (window.Modal && Modal.toast) {
      Modal.toast({ title: 'Done', message: 'All notifications marked as read', type: 'success' });
    }
  } catch (err) {
    if (window.Modal && Modal.toast) {
      Modal.toast({ title: 'Error', message: err.message || 'Could not update notifications', type: 'error' });
    }
  }
};

window.initFarmerNotifications = function () {
  loadFarmerNotifications();
};
