/**
 * SHREE MILK BANK — Farmer: My Milk Collection
 * Loads the authenticated farmer's own records from
 * GET /api/farmer/me/collections (always scoped server-side).
 */
let _collectionsPage = 1;
const PER_PAGE = 20;

function _collectionsParams() {
  return {
    page: _collectionsPage,
    per_page: PER_PAGE,
    from: document.getElementById('filter-from')?.value || '',
    to: document.getElementById('filter-to')?.value || '',
    shift: document.getElementById('filter-shift')?.value || '',
  };
}

function _shiftBadge(shift) {
  return shift === 'MORNING'
    ? '<span class="tag tag-blue">Morning</span>'
    : '<span class="tag tag-gold">Evening</span>';
}

function _statusBadge(status) {
  const map = {
    ACCEPTED: 'tag-green', RECORDED: 'tag-green', VERIFIED: 'tag-blue',
    CORRECTED: 'tag-amber', REJECTED: 'tag-red',
  };
  return `<span class="tag ${map[status] || 'tag-neutral'}" style="font-size:10px;">${status ? status.charAt(0) + status.slice(1).toLowerCase() : '—'}</span>`;
}

async function loadFarmerCollections() {
  const body = document.getElementById('collections-body');
  const totalEl = document.getElementById('collections-total');
  const pager = document.getElementById('collections-pager-info');
  if (body) body.innerHTML = '<tr><td colspan="10" class="text-center" style="padding:var(--space-4);color:var(--ink-muted);font-size:var(--text-sm);">Loading milk collections…</td></tr>';

  try {
    const data = await API.getMyCollections(_collectionsParams());
    const rows = data.collections || [];

    if (totalEl) totalEl.textContent = `${data.total || 0} record(s)`;
    if (pager) {
      const from = data.total === 0 ? 0 : ((data.page - 1) * (data.perPage || PER_PAGE)) + 1;
      const to = Math.min((data.page || 1) * (data.perPage || PER_PAGE), data.total || 0);
      pager.textContent = `Showing ${from}-${to} of ${data.total || 0} entries`;
    }

    const prev = document.getElementById('collections-prev');
    const next = document.getElementById('collections-next');
    if (prev) prev.disabled = !(data.page && data.page > 1);
    if (next) next.disabled = !(data.page && data.pages && data.page < data.pages);

    if (!rows.length) {
      body.innerHTML = '<tr><td colspan="10" class="text-center" style="padding:var(--space-6);"><div class="empty-icon" style="margin:0 auto var(--space-3);"><i data-lucide="milk" style="width:36px;height:36px;"></i></div><p style="color:var(--ink-muted);font-size:var(--text-sm);">No milk collection records found.</p><p style="color:var(--ink-muted);font-size:var(--text-xs);margin-top:var(--space-1);">When the branch operator records your milk, it will appear here automatically.</p></td></tr>';
    } else {
      body.innerHTML = rows.map(c => `
        <tr>
          <td><span class="font-mono">${c.receiptNo || '—'}</span></td>
          <td>${fmtDate(c.date)}</td>
          <td>${_shiftBadge(c.shift)}</td>
          <td>${(c.milkType || '').charAt(0) + (c.milkType || '').slice(1).toLowerCase()}</td>
          <td>${fmtNum(c.quantity, 2)} L</td>
          <td>${c.fat != null ? c.fat + '%' : '—'}</td>
          <td>${c.snf != null ? c.snf + '%' : '—'}</td>
          <td>${c.ratePerLiter != null ? '₹' + fmtNum(c.ratePerLiter, 2) + '/L' : '—'}</td>
          <td style="font-weight:600;">${fmtINR(c.amount)}</td>
          <td>${_statusBadge(c.status)}</td>
        </tr>`).join('');
    }
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.warn('Failed to load collections:', err);
    if (body) body.innerHTML = `<tr><td colspan="10" class="text-center" style="padding:var(--space-5);">
      <p style="color:var(--ink-muted);font-size:var(--text-sm);">Unable to load milk collections. Try again.</p>
      <button class="btn btn-sm btn-ghost" style="margin-top:var(--space-2);" onclick="window.refreshFarmerCollections && refreshFarmerCollections()">Try Again</button>
    </td></tr>`;
  }
}

window.refreshFarmerCollections = function () {
  _collectionsPage = 1;
  loadFarmerCollections();
};

window.pageFarmerCollections = function (delta) {
  _collectionsPage = Math.max(1, _collectionsPage + delta);
  loadFarmerCollections();
};

window.initFarmerCollections = function () {
  ['filter-from', 'filter-to', 'filter-shift'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', () => { _collectionsPage = 1; loadFarmerCollections(); });
  });
  loadFarmerCollections();
};
