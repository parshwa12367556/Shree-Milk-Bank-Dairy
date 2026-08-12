/**
 * SHREE MILK BANK — Admin: Farmer Grievances
 * Loads grievances from GET /api/admin/grievances with branch/status/search
 * filters and supports responding via PATCH /api/admin/grievances/<id>.
 */
let _grvPage = 1;
const GRV_PER_PAGE = 20;
let _grvActive = null;

function _grvStatusBadge(status) {
  const map = { OPEN: 'tag-red', IN_PROGRESS: 'tag-blue', RESOLVED: 'tag-green', CLOSED: 'tag-neutral' };
  return `<span class="tag ${map[status] || 'tag-neutral'}" style="font-size:10px;">${status ? status.replace('_', ' ') : '—'}</span>`;
}

// Escape HTML in any user-supplied text rendered into the DOM (grievance
// subjects/descriptions are farmer-controlled — never trust them).
function _esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function _grvCategory(cat) {
  const map = { PAYMENT: 'Payment', QUALITY: 'Quality', COLLECTION: 'Collection', OTHER: 'Other' };
  return map[cat] || cat || '—';
}

async function _loadGrvBranches() {
  const select = document.getElementById('grv-branch');
  if (!select) return;
  try {
    const data = await API.getBranches();
    (data.branches || []).forEach(b => {
      const opt = document.createElement('option');
      opt.value = b.id;
      opt.textContent = `${b.name} (${b.code})`;
      select.appendChild(opt);
    });
  } catch (e) { /* fallback */ }
}

function _grvParams() {
  const params = { page: _grvPage, per_page: GRV_PER_PAGE };
  const branch = document.getElementById('grv-branch')?.value || '';
  const status = document.getElementById('grv-status')?.value || '';
  const q = document.getElementById('grv-q')?.value.trim() || '';
  if (branch) params.branchId = branch;
  if (status) params.status = status;
  if (q) params.q = q;
  return params;
}

async function loadAdminGrievances() {
  const body = document.getElementById('grv-body');
  if (body) body.innerHTML = '<tr><td colspan="8" class="text-center" style="padding:var(--space-4);color:var(--ink-muted);font-size:var(--text-sm);">Loading grievances…</td></tr>';
  try {
    const data = await API.getAdminGrievances(_grvParams());
    const grievances = data.grievances || [];
    const summary = data.summary || {};

    const set = (id, v) => { const el = document.getElementById(id); if (el) el.innerHTML = v; };
    set('grv-open', summary.open ?? 0);
    set('grv-progress', summary.inProgress ?? 0);
    set('grv-resolved', summary.resolved ?? 0);
    set('grv-total', `${data.total || 0} grievance${(data.total || 0) === 1 ? '' : 's'}`);

    const pager = document.getElementById('grv-pager-info');
    if (pager) {
      const from = data.total === 0 ? 0 : ((data.page - 1) * (data.perPage || GRV_PER_PAGE)) + 1;
      const to = Math.min((data.page || 1) * (data.perPage || GRV_PER_PAGE), data.total || 0);
      pager.textContent = `Showing ${from}-${to} of ${data.total || 0}`;
    }
    const prev = document.getElementById('grv-prev');
    const next = document.getElementById('grv-next');
    if (prev) prev.disabled = !(data.page && data.page > 1);
    if (next) next.disabled = !(data.page && data.pages && data.page < data.pages);

    if (!grievances.length) {
      body.innerHTML = '<tr><td colspan="8" class="text-center" style="padding:var(--space-6);"><div class="empty-icon" style="margin:0 auto var(--space-3);"><i data-lucide="inbox" style="width:36px;height:36px;"></i></div><p style="color:var(--ink-muted);font-size:var(--text-sm);">No grievances match the current filters.</p></td></tr>';
    } else {
      body.innerHTML = grievances.map(g => `
        <tr>
          <td class="font-mono" style="font-size:var(--text-xs);">${_esc(g.grievanceCode) || '—'}</td>
          <td>
            <div style="font-weight:600;font-size:var(--text-sm);">${_esc(g.farmerName) || '—'}</div>
            <div style="font-size:var(--text-xs);color:var(--ink-muted);">${_esc(g.farmerCode)}</div>
          </td>
          <td style="font-size:var(--text-sm);max-width:220px;">
            <div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${_esc(g.subject)}">${_esc(g.subject) || '—'}</div>
            ${g.receiptNo ? `<div style="font-size:10px;color:var(--ink-muted);">Receipt ${_esc(g.receiptNo)}</div>` : ''}
          </td>
          <td style="font-size:var(--text-xs);">${_grvCategory(g.category)}</td>
          <td style="font-size:var(--text-xs);">${g.branchId || '—'}</td>
          <td style="font-size:var(--text-xs);">${fmtDate(g.createdAt)}</td>
          <td>${_grvStatusBadge(g.status)}</td>
          <td>
            <button class="btn btn-sm btn-ghost" onclick="window.openAdminGrievance && openAdminGrievance(${g.id})">
              <i data-lucide="message-square" style="width:14px;height:14px;"></i> Respond
            </button>
          </td>
        </tr>`).join('');
    }
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.warn('Failed to load grievances:', err);
    if (body) body.innerHTML = `<tr><td colspan="8" class="text-center" style="padding:var(--space-5);">
      <p style="color:var(--ink-muted);font-size:var(--text-sm);">Unable to load grievances. Try again.</p>
      <button class="btn btn-sm btn-ghost" style="margin-top:var(--space-2);" onclick="window.refreshAdminGrievances && refreshAdminGrievances()">Try Again</button>
    </td></tr>`;
  }
}

window.openAdminGrievance = async function (id) {
  try {
    const data = await API.getAdminGrievance(id);
    const g = data.grievance || {};
    _grvActive = g;
    const detail = document.getElementById('grv-detail');
    if (detail) {
      detail.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-2);">
          <strong style="font-size:var(--text-sm);">${_esc(g.subject)}</strong>
          ${_grvStatusBadge(g.status)}
        </div>
        <div style="font-size:var(--text-xs);color:var(--ink-muted);margin-bottom:var(--space-2);">
          <span class="font-mono">${_esc(g.grievanceCode)}</span> · ${_esc(g.farmerName)} (${_esc(g.farmerCode)}) · ${_grvCategory(g.category)}
        </div>
        <div style="font-size:var(--text-sm);color:var(--ink-muted);background:var(--bg-subtle);border-radius:var(--radius-md);padding:var(--space-3);">
          ${_esc(g.description) || '—'}
        </div>
        ${g.response ? `<div style="margin-top:var(--space-3);padding:var(--space-3);background:#eef7f3;border-left:3px solid var(--forest);border-radius:var(--radius-md);font-size:var(--text-sm);"><strong>Previous response:</strong><br>${_esc(g.response)}</div>` : ''}`;
    }
    document.getElementById('grv-new-status').value = g.status === 'OPEN' ? 'IN_PROGRESS' : (g.status === 'IN_PROGRESS' ? 'RESOLVED' : 'RESOLVED');
    document.getElementById('grv-response').value = '';
    document.getElementById('grv-modal').style.display = 'flex';
  } catch (err) {
    if (window.Modal && Modal.toast) Modal.toast({ title: 'Error', message: err.message || 'Could not load grievance.', type: 'error' });
  }
};

window.submitAdminGrievanceResponse = async function () {
  if (!_grvActive) return;
  const response = (document.getElementById('grv-response')?.value || '').trim();
  const status = document.getElementById('grv-new-status')?.value || 'RESOLVED';
  if (!response) {
    if (window.Modal && Modal.toast) Modal.toast({ title: 'Error', message: 'Please write a response.', type: 'error' });
    return;
  }
  const btn = document.getElementById('grv-submit-btn');
  if (btn) { btn.disabled = true; btn.textContent = 'Submitting…'; }
  try {
    await API.respondAdminGrievance(_grvActive.id, { response, status });
    document.getElementById('grv-modal').style.display = 'none';
    if (window.Modal && Modal.toast) Modal.toast({ title: 'Sent', message: `Grievance ${_grvActive.grievanceCode || ''} updated. The farmer has been notified.`, type: 'success' });
    _grvActive = null;
    await loadAdminGrievances();
  } catch (err) {
    if (window.Modal && Modal.toast) Modal.toast({ title: 'Error', message: err.message || 'Could not submit response.', type: 'error' });
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="send" style="width:16px;height:16px;"></i> Submit Response'; if (window.lucide) lucide.createIcons(); }
  }
};

window.refreshAdminGrievances = function () {
  _grvPage = 1;
  loadAdminGrievances();
};

window.pageAdminGrievances = function (delta) {
  _grvPage = Math.max(1, _grvPage + delta);
  loadAdminGrievances();
};

window.initAdminGrievances = function () {
  _loadGrvBranches();
  ['grv-branch', 'grv-status'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', () => { _grvPage = 1; loadAdminGrievances(); });
  });
  const q = document.getElementById('grv-q');
  if (q) q.addEventListener('keydown', (e) => { if (e.key === 'Enter') { _grvPage = 1; loadAdminGrievances(); } });
  loadAdminGrievances();
};
