/**
 * SHREE MILK BANK — Admin: Milk Collections
 * Loads collection records across all branches from GET /api/collections
 * with branch / date-range / shift / milk-type / status filters.
 */
let _acPage = 1;
const AC_PER_PAGE = 25;

function _acShiftBadge(shift) {
  return shift === 'MORNING'
    ? '<span class="tag tag-gold">Morning</span>'
    : '<span class="tag tag-blue">Evening</span>';
}

function _acStatusBadge(status) {
  const map = { ACCEPTED: 'tag-green', RECORDED: 'tag-neutral', VERIFIED: 'tag-blue', REJECTED: 'tag-red', CORRECTED: 'tag-amber' };
  return `<span class="tag ${map[status] || 'tag-neutral'}" style="font-size:10px;">${status || '—'}</span>`;
}

async function _loadBranches() {
  const select = document.getElementById('ac-branch');
  if (!select) return;
  try {
    const data = await API.getBranches();
    const branches = data.branches || [];
    select.innerHTML = '<option value="">All Branches</option>';
    branches.forEach(b => {
      const opt = document.createElement('option');
      opt.value = b.id;
      opt.textContent = `${b.name} (${b.code})`;
      select.appendChild(opt);
    });
  } catch (e) { /* keep fallback */ }
}

function _acParams() {
  const params = { page: _acPage, per_page: AC_PER_PAGE };
  const branch = document.getElementById('ac-branch')?.value || '';
  const from = document.getElementById('ac-from')?.value || '';
  const to = document.getElementById('ac-to')?.value || '';
  const shift = document.getElementById('ac-shift')?.value || '';
  const type = document.getElementById('ac-type')?.value || '';
  const status = document.getElementById('ac-status')?.value || '';
  const farmer = document.getElementById('ac-farmer')?.value.trim() || '';
  if (branch) params.branchId = branch;
  if (from) params.from = from;
  if (to) params.to = to;
  if (shift) params.shift = shift;
  if (type) params.milkType = type;
  if (status) params.status = status;
  if (farmer) params.q = farmer;
  return params;
}

async function loadAdminCollections() {
  const body = document.getElementById('ac-body');
  if (body) body.innerHTML = '<tr><td colspan="13" class="text-center" style="padding:var(--space-4);color:var(--ink-muted);font-size:var(--text-sm);">Loading collections…</td></tr>';
  try {
    const data = await API.getCollections(_acParams());
    const collections = data.collections || [];
    const summary = data.summary || {};

    const set = (id, v) => { const el = document.getElementById(id); if (el) el.innerHTML = v; };
    set('ac-qty', `${fmtNum(summary.totalQuantity, 2)} L`);
    set('ac-amount', fmtINR(summary.totalAmount));
    set('ac-count', summary.collectionCount ?? 0);
    set('ac-total', `${data.total || 0} record${(data.total || 0) === 1 ? '' : 's'}`);

    const pager = document.getElementById('ac-pager-info');
    if (pager) {
      const from = data.total === 0 ? 0 : ((data.page - 1) * (data.perPage || AC_PER_PAGE)) + 1;
      const to = Math.min((data.page || 1) * (data.perPage || AC_PER_PAGE), data.total || 0);
      pager.textContent = `Showing ${from}-${to} of ${data.total || 0}`;
    }
    const prev = document.getElementById('ac-prev');
    const next = document.getElementById('ac-next');
    if (prev) prev.disabled = !(data.page && data.page > 1);
    if (next) next.disabled = !(data.page && data.pages && data.page < data.pages);

    if (!collections.length) {
      body.innerHTML = '<tr><td colspan="13" class="text-center" style="padding:var(--space-6);"><div class="empty-icon" style="margin:0 auto var(--space-3);"><i data-lucide="milk" style="width:36px;height:36px;"></i></div><p style="color:var(--ink-muted);font-size:var(--text-sm);">No collection records match the current filters.</p></td></tr>';
    } else {
      body.innerHTML = collections.map(c => `
        <tr>
          <td class="font-mono" style="font-size:var(--text-xs);">${c.receiptNo || '—'}</td>
          <td style="font-size:var(--text-xs);">
            ${fmtDate(c.date)}
            ${c.createdAt ? `<div style="color:var(--ink-muted);">${new Date(c.createdAt).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}</div>` : ''}
          </td>
          <td style="font-size:var(--text-xs);">${c.branchName || '—'}</td>
          <td>
            <div style="font-weight:600;font-size:var(--text-sm);">${c.farmerName || '—'}</div>
            <div style="font-size:var(--text-xs);color:var(--ink-muted);">${c.farmerCode || ''}</div>
          </td>
          <td>${_acShiftBadge(c.shift)}</td>
          <td style="font-size:var(--text-xs);">${c.milkType || '—'}</td>
          <td>${c.quantity != null ? fmtNum(c.quantity, 2) + ' L' : '—'}</td>
          <td>${c.fat != null ? c.fat + '%' : '—'}</td>
          <td>${c.snf != null ? c.snf + '%' : '—'}</td>
          <td>${c.ratePerLiter != null ? '₹' + fmtNum(c.ratePerLiter, 2) : '—'}</td>
          <td style="font-weight:600;">${fmtINR(c.amount)}</td>
          <td style="font-size:var(--text-xs);">${c.status === 'REJECTED' ? '<span class="tag tag-red">Rejected</span>' : '—'}</td>
          <td>${_acStatusBadge(c.status)}</td>
        </tr>`).join('');
    }
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.warn('Failed to load collections:', err);
    if (body) body.innerHTML = `<tr><td colspan="13" class="text-center" style="padding:var(--space-5);">
      <p style="color:var(--ink-muted);font-size:var(--text-sm);">Unable to load collections. Try again.</p>
      <button class="btn btn-sm btn-ghost" style="margin-top:var(--space-2);" onclick="window.refreshAdminCollections && refreshAdminCollections()">Try Again</button>
    </td></tr>`;
  }
}

window.refreshAdminCollections = function () {
  _acPage = 1;
  loadAdminCollections();
};

window.pageAdminCollections = function (delta) {
  _acPage = Math.max(1, _acPage + delta);
  loadAdminCollections();
};

window.initAdminCollections = function () {
  _loadBranches();
  ['ac-branch', 'ac-from', 'ac-to', 'ac-shift', 'ac-type', 'ac-status'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', () => { _acPage = 1; loadAdminCollections(); });
  });
  const farmerInput = document.getElementById('ac-farmer');
  if (farmerInput) {
    farmerInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { _acPage = 1; loadAdminCollections(); }
    });
  }
  loadAdminCollections();
};
