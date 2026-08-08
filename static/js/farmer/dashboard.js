/**
 * ============================================================
 * SHREE MILK BANK — Farmer Dashboard
 * ============================================================
 * Loads the authenticated farmer's own data from
 * GET /api/farmer/me/dashboard and re-fetches automatically
 * every 30 seconds so a new milk collection recorded by the
 * Branch Operator appears without the farmer refreshing.
 *
 * NOTE: this deployment uses lightweight API polling (the
 * explicitly-supported fallback) because the app server is a
 * plain Flask dev server without Socket.IO. If a WebSocket
 * transport is added later, swap `startPolling` for a socket
 * listener emitting the same events (collection.created /
 * collection.updated / payment.created / notification.created).
 * ============================================================
 */

const POLL_INTERVAL_MS = 30000;
let pollTimer = null;
let lastCollectionCount = null;

window.initFarmerDashboard = function () {
  loadFarmerDashboard();
  startPolling();
};

/** Poll the dashboard API every 30s (no manual refresh needed) */
function startPolling() {
  stopPolling();
  pollTimer = setInterval(() => loadFarmerDashboard(false), POLL_INTERVAL_MS);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

function setRefreshStatus(text) {
  const el = document.getElementById('refresh-status');
  if (el) el.textContent = text;
}

function shiftBadge(shift) {
  return shift === 'MORNING'
    ? '<span class="tag tag-blue">Morning</span>'
    : '<span class="tag tag-gold">Evening</span>';
}

function statusBadge(status) {
  const map = {
    ACCEPTED: 'tag-green', RECORDED: 'tag-green', VERIFIED: 'tag-blue',
    CORRECTED: 'tag-amber', REJECTED: 'tag-red',
  };
  return `<span class="tag ${map[status] || 'tag-neutral'}" style="font-size:10px;">${status ? status.charAt(0) + status.slice(1).toLowerCase() : '—'}</span>`;
}

async function loadFarmerDashboard(manual = false) {
  if (manual) setRefreshStatus('Refreshing…');
  try {
    const data = await API.getMyDashboard();
    renderDashboard(data);

    // New collection detected since the last poll → toast the farmer
    const count = (data.today || {}).collectionCount ?? 0;
    if (lastCollectionCount !== null && count > lastCollectionCount && !manual) {
      const latest = (data.recentCollections || [])[0];
      if (latest) {
        if (window.Modal && Modal.toast) {
          Modal.toast({
            title: 'New milk collection recorded',
            message: `${fmtNum(latest.quantity)} L · Fat ${latest.fat}% · SNF ${latest.snf}% · Amount ${fmtINR(latest.amount)}`,
            type: 'success',
          });
        }
      }
    }
    lastCollectionCount = count;
    if (manual) {
      setRefreshStatus(`Updated just now · ${new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}`);
      if (window.Modal && Modal.toast) {
        Modal.toast({ title: 'Updated', message: 'Dashboard refreshed', type: 'success' });
      }
    }
  } catch (err) {
    console.warn('Farmer dashboard load failed:', err);
    if (manual) {
      setRefreshStatus('Unable to refresh. Will retry automatically.');
      if (window.Modal && Modal.toast) {
        Modal.toast({ title: 'Error', message: err.message || 'Unable to load dashboard. Try again.', type: 'error' });
      }
    }
  }
}

function renderDashboard(data) {
  const k = data.today || {};
  const t = data.totals || {};
  const p = data.payment || {};

  const kpiMap = {
    'kpi-today-qty': `${fmtNum(k.quantity, 2)} L`,
    'kpi-today-amount': fmtINR(k.amount),
    'kpi-total-qty': `${fmtNum(t.totalQuantity, 2)} L`,
    'kpi-avg-fat': t.avgFat != null ? `${t.avgFat}%` : '—',
    'kpi-pending': fmtINR(p.pendingAmount),
    'kpi-paid': fmtINR(p.paidAmount),
  };
  Object.entries(kpiMap).forEach(([id, value]) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = value;
  });

  const countTag = document.getElementById('today-count-tag');
  if (countTag) countTag.textContent = `${k.collectionCount || 0} entries`;

  // Today's shift split
  const shiftsEl = document.getElementById('today-shifts');
  if (shiftsEl) {
    if (!k.collectionCount) {
      shiftsEl.innerHTML = `<div class="empty-state" style="padding:var(--space-4);text-align:center;">
        <p style="font-size:var(--text-sm);color:var(--ink-muted);">No milk collection recorded today yet. Your latest entries will appear here automatically.</p>
      </div>`;
    } else {
      shiftsEl.innerHTML = [
        { label: 'Morning', qty: k.morningQuantity, amt: k.morningAmount, icon: 'sunrise' },
        { label: 'Evening', qty: k.eveningQuantity, amt: k.eveningAmount, icon: 'sunset' },
      ].map(s => `
        <div style="display:flex;justify-content:space-between;align-items:center;padding:var(--space-2) 0;border-bottom:1px solid var(--line);font-size:var(--text-sm);">
          <div style="display:flex;align-items:center;gap:var(--space-2);">
            <i data-lucide="${s.icon}" style="width:16px;height:16px;color:var(--ink-muted);"></i>
            <span style="font-weight:600;">${s.label}</span>
          </div>
          <div style="text-align:right;">
            <div style="font-weight:700;">${fmtNum(s.qty, 2)} L</div>
            <div style="color:var(--ink-muted);font-size:var(--text-xs);">${fmtINR(s.amt)}</div>
          </div>
        </div>`).join('');
      if (window.lucide) lucide.createIcons();
    }
  }

  // Recent collection highlight
  const recent = data.recentCollections || [];
  const rcEl = document.getElementById('recent-collection');
  if (rcEl) {
    if (!recent.length) {
      rcEl.innerHTML = `<div class="empty-state" style="padding:var(--space-4);text-align:center;">
        <p style="font-size:var(--text-sm);color:var(--ink-muted);">No collections yet.</p>
      </div>`;
    } else {
      const c = recent[0];
      rcEl.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:var(--space-3);">
          <div>
            <div style="font-weight:700;font-size:1.15rem;">${fmtNum(c.quantity, 2)} L</div>
            <div style="color:var(--ink-muted);font-size:var(--text-sm);">${(c.milkType || '').charAt(0) + (c.milkType || '').slice(1).toLowerCase()} Milk · ${shiftBadge(c.shift)}</div>
          </div>
          <div style="text-align:right;">
            <div style="font-weight:700;color:var(--forest);">${fmtINR(c.amount)}</div>
            <div style="color:var(--ink-muted);font-size:var(--text-xs);">${fmtDate(c.date)}</div>
          </div>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:var(--space-3);font-size:var(--text-sm);">
          <span>Fat: <strong>${c.fat != null ? c.fat + '%' : '—'}</strong></span>
          <span>SNF: <strong>${c.snf != null ? c.snf + '%' : '—'}</strong></span>
          <span>Rate: <strong>${c.ratePerLiter != null ? '₹' + fmtNum(c.ratePerLiter, 2) + '/L' : '—'}</strong></span>
          <span>${statusBadge(c.status)}</span>
        </div>
        <div style="margin-top:var(--space-3);color:var(--ink-muted);font-size:var(--text-xs);">Receipt ${c.receiptNo || '—'}</div>`;
    }
  }

  // Recent collections table
  const body = document.getElementById('recent-collections-body');
  if (body) {
    if (!recent.length) {
      body.innerHTML = '<tr><td colspan="8" class="text-center" style="padding:var(--space-4);color:var(--ink-muted);font-size:var(--text-sm);">No milk collection records found.</td></tr>';
    } else {
      body.innerHTML = recent.map(c => `
        <tr>
          <td>${fmtDate(c.date)}</td>
          <td>${shiftBadge(c.shift)}</td>
          <td>${fmtNum(c.quantity, 2)} L</td>
          <td>${c.fat != null ? c.fat + '%' : '—'}</td>
          <td>${c.snf != null ? c.snf + '%' : '—'}</td>
          <td>${c.ratePerLiter != null ? '₹' + fmtNum(c.ratePerLiter, 2) : '—'}</td>
          <td style="font-weight:600;">${fmtINR(c.amount)}</td>
          <td>${statusBadge(c.status)}</td>
        </tr>`).join('');
    }
  }

  // Notifications
  const notifs = (data.notifications || {}).recent || [];
  const unread = (data.notifications || {}).unreadCount || 0;
  const nEl = document.getElementById('recent-notifications');
  if (nEl) {
    if (!notifs.length) {
      nEl.innerHTML = `<div class="empty-state" style="padding:var(--space-4);text-align:center;">
        <p style="font-size:var(--text-sm);color:var(--ink-muted);">No messages yet. You'll be notified here when milk is recorded or a payment is made.</p>
      </div>`;
    } else {
      nEl.innerHTML = notifs.map(n => `
        <div style="display:flex;gap:var(--space-3);padding:var(--space-2) 0;border-bottom:1px solid var(--line);font-size:var(--text-sm);">
          <div style="flex-shrink:0;margin-top:2px;${n.read ? 'color:var(--ink-muted);' : 'color:var(--forest);'}">
            <i data-lucide="${n.type === 'payment' ? 'wallet' : n.type === 'collection' ? 'milk' : 'bell'}" style="width:16px;height:16px;"></i>
          </div>
          <div style="flex:1;min-width:0;">
            <div style="font-weight:600;">${n.title || ''}${n.read ? '' : ' <span class="status-dot online" style="display:inline-block;vertical-align:middle;margin-left:6px;"></span>'}</div>
            <div style="color:var(--ink-muted);font-size:var(--text-xs);margin-top:2px;">${n.message || ''}</div>
            <div style="color:var(--ink-muted);font-size:10px;margin-top:2px;">${fmtDate(n.createdAt, true)}</div>
          </div>
        </div>`).join('');
      if (window.lucide) lucide.createIcons();
    }
  }
  const unreadTag = document.getElementById('unread-tag');
  if (unreadTag) unreadTag.textContent = `${unread} unread`;

  if (window.lucide) lucide.createIcons();
}

/** Manual refresh (Refresh Now button) */
window.refreshFarmerDashboard = function (manual = true) {
  loadFarmerDashboard(manual);
};
