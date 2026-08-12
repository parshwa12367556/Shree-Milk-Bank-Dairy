/**
 * SHREE MILK BANK — Farmer: Daily Collection
 * Loads today's own milk collection from
 * GET /api/farmer/me/daily-collection (server-scoped to the farmer)
 * and auto-refreshes so a newly recorded collection appears automatically.
 */
let _dcTimer = null;

function _dcShiftBadge(shift) {
  return shift === 'MORNING'
    ? '<span class="tag tag-gold">Morning</span>'
    : '<span class="tag tag-blue">Evening</span>';
}

function _set(id, value) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = value;
}

function _renderShift(side, data) {
  const has = data && data.collections && data.collections.length > 0;
  _set(`dc-${side}-status`, has ? 'Recorded' : 'No entry yet');
  _set(`dc-${side}-qty`, data.quantity != null ? `<strong>${fmtNum(data.quantity, 2)} L</strong>` : '—');
  _set(`dc-${side}-fat`, data.fat != null ? `${data.fat}%` : '—');
  _set(`dc-${side}-snf`, data.snf != null ? `${data.snf}%` : '—');
  _set(`dc-${side}-rate`, data.ratePerLiter != null ? '₹' + fmtNum(data.ratePerLiter, 2) + '/L' : '—');
  _set(`dc-${side}-amount`, data.amount != null ? `<strong style="color:var(--forest);">${fmtINR(data.amount)}</strong>` : '—');
  const receipts = (data.collections || []).map(c => c.receiptNo).join(', ');
  _set(`dc-${side}-receipts`, receipts || '—');
}

async function loadFarmerDailyCollection() {
  try {
    const data = await API.getMyDailyCollection();

    const morning = data.morning || {};
    const evening = data.evening || {};
    const summary = data.summary || {};

    _set('dc-total-qty', `${fmtNum(summary.totalQuantity, 2)} L`);
    _set('dc-total-amount', fmtINR(summary.totalAmount));
    _set('dc-count', summary.collectionCount ?? 0);

    const allFats = [
      ...((morning.collections || []).map(c => c.fat).filter(f => f != null)),
      ...((evening.collections || []).map(c => c.fat).filter(f => f != null)),
    ];
    _set('dc-avg-fat', allFats.length
      ? `${fmtNum(allFats.reduce((a, b) => a + b, 0) / allFats.length, 1)}%`
      : '—');

    _renderShift('morning', morning);
    _renderShift('evening', evening);

    const entries = [...(morning.collections || []), ...(evening.collections || [])]
      .sort((a, b) => (a.createdAt || '').localeCompare(b.createdAt || ''));

    const info = document.getElementById('dc-entries-info');
    if (info) info.textContent = `${entries.length} entr${entries.length === 1 ? 'y' : 'ies'} today`;

    const body = document.getElementById('dc-body');
    if (!entries.length) {
      body.innerHTML = '<tr><td colspan="9" class="text-center" style="padding:var(--space-6);"><div class="empty-icon" style="margin:0 auto var(--space-3);"><i data-lucide="sun" style="width:36px;height:36px;"></i></div><p style="color:var(--ink-muted);font-size:var(--text-sm);">No milk collected today yet.</p><p style="color:var(--ink-muted);font-size:var(--text-xs);margin-top:var(--space-1);">Once the branch records your milk, it appears here automatically.</p></td></tr>';
    } else {
      body.innerHTML = entries.map(c => `
        <tr>
          <td>${c.createdAt ? new Date(c.createdAt).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : '—'}</td>
          <td>${_dcShiftBadge(c.shift)}</td>
          <td>${c.milkType || '—'}</td>
          <td>${fmtNum(c.quantity, 2)} L</td>
          <td>${c.fat != null ? c.fat + '%' : '—'}</td>
          <td>${c.snf != null ? c.snf + '%' : '—'}</td>
          <td>${c.ratePerLiter != null ? '₹' + fmtNum(c.ratePerLiter, 2) + '/L' : '—'}</td>
          <td style="font-weight:600;color:var(--forest);">${fmtINR(c.amount)}</td>
          <td>${c.status === 'ACCEPTED' ? '<span class="tag tag-green">Accepted</span>' : `<span class="tag tag-neutral">${c.status || '—'}</span>`}</td>
        </tr>`).join('');
    }
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.warn('Failed to load daily collection:', err);
    const body = document.getElementById('dc-body');
    if (body) body.innerHTML = `<tr><td colspan="9" class="text-center" style="padding:var(--space-5);">
      <p style="color:var(--ink-muted);font-size:var(--text-sm);">Unable to load today's collection. Try again.</p>
      <button class="btn btn-sm btn-ghost" style="margin-top:var(--space-2);" onclick="window.refreshFarmerDailyCollection && refreshFarmerDailyCollection()">Try Again</button>
    </td></tr>`;
  }
}

window.refreshFarmerDailyCollection = function () {
  loadFarmerDailyCollection();
};

window.initFarmerDailyCollection = function () {
  loadFarmerDailyCollection();
  // Auto-refresh every 30s so a just-recorded collection shows up without a reload.
  if (_dcTimer) clearInterval(_dcTimer);
  _dcTimer = setInterval(loadFarmerDailyCollection, 30000);
};
