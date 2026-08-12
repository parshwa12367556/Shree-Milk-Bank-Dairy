/**
 * SHREE MILK BANK — Branch Operator: Payment History (view only)
 * Loads the branch's payment records from GET /api/payments — the backend
 * scopes the query to the logged-in operator's branch automatically.
 * Payments can only be created/processed by the ADMIN role, so this page
 * exposes no write actions.
 */
let _bpPage = 1;
const BP_PER_PAGE = 20;

function _bpStatusBadge(status) {
  const map = { PAID: 'tag-green', APPROVED: 'tag-blue', PENDING: 'tag-amber', FAILED: 'tag-red' };
  return `<span class="tag ${map[status] || 'tag-neutral'}" style="font-size:10px;">${status || '—'}</span>`;
}

function _bpParams() {
  const from = document.getElementById('bp-from')?.value || '';
  const to = document.getElementById('bp-to')?.value || '';
  const params = { page: _bpPage, per_page: BP_PER_PAGE };
  const status = document.getElementById('bp-status')?.value || '';
  if (status) params.status = status;
  if (from) params.from = from;
  if (to) params.to = to;
  return params;
}

async function loadBranchPayments() {
  const body = document.getElementById('bp-body');
  if (body) body.innerHTML = '<tr><td colspan="8" class="text-center" style="padding:var(--space-4);color:var(--ink-muted);font-size:var(--text-sm);">Loading payments…</td></tr>';
  try {
    const data = await API.getPayments(_bpParams());
    const payments = data.payments || [];
    const summary = data.summary || {};

    const set = (id, v) => { const el = document.getElementById(id); if (el) el.innerHTML = v; };
    set('bp-paid-amount', fmtINR(summary.totalPaid));
    set('bp-pending-amount', fmtINR(summary.totalPending));
    set('bp-payment-rate', summary.paymentRate != null ? `${summary.paymentRate}%` : '—');
    set('bp-total', `${data.total || 0} payment${(data.total || 0) === 1 ? '' : 's'}`);

    const pager = document.getElementById('bp-pager-info');
    if (pager) {
      const from = data.total === 0 ? 0 : ((data.page - 1) * (data.perPage || BP_PER_PAGE)) + 1;
      const to = Math.min((data.page || 1) * (data.perPage || BP_PER_PAGE), data.total || 0);
      pager.textContent = `Showing ${from}-${to} of ${data.total || 0}`;
    }
    const prev = document.getElementById('bp-prev');
    const next = document.getElementById('bp-next');
    if (prev) prev.disabled = !(data.page && data.page > 1);
    if (next) next.disabled = !(data.page && data.pages && data.page < data.pages);

    if (!payments.length) {
      body.innerHTML = '<tr><td colspan="8" class="text-center" style="padding:var(--space-6);"><div class="empty-icon" style="margin:0 auto var(--space-3);"><i data-lucide="wallet" style="width:36px;height:36px;"></i></div><p style="color:var(--ink-muted);font-size:var(--text-sm);">No payment records found for this branch.</p></td></tr>';
    } else {
      body.innerHTML = payments.map(p => `
        <tr>
          <td class="font-mono" style="font-size:var(--text-xs);">${p.payCode || '—'}</td>
          <td>
            <div style="font-weight:600;font-size:var(--text-sm);">${p.farmerName || '—'}</div>
            <div style="font-size:var(--text-xs);color:var(--ink-muted);">${p.farmerCode || ''}</div>
          </td>
          <td style="font-size:var(--text-xs);">${p.periodStart ? fmtDate(p.periodStart) : '—'} → ${p.periodEnd ? fmtDate(p.periodEnd) : '—'}</td>
          <td>${p.totalQuantity != null ? fmtNum(p.totalQuantity, 2) + ' L' : '—'}</td>
          <td style="font-weight:600;">${fmtINR(p.totalAmount)}</td>
          <td>${_bpStatusBadge(p.status)}</td>
          <td style="font-size:var(--text-xs);">${p.paidAt ? fmtDate(p.paidAt) : '—'}</td>
          <td style="font-size:var(--text-xs);color:var(--ink-muted);">${p.reference || '—'}</td>
        </tr>`).join('');
    }
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.warn('Failed to load branch payments:', err);
    if (body) body.innerHTML = `<tr><td colspan="8" class="text-center" style="padding:var(--space-5);">
      <p style="color:var(--ink-muted);font-size:var(--text-sm);">Unable to load payments. Try again.</p>
      <button class="btn btn-sm btn-ghost" style="margin-top:var(--space-2);" onclick="window.refreshBranchPayments && refreshBranchPayments()">Try Again</button>
    </td></tr>`;
  }
}

window.refreshBranchPayments = function () {
  _bpPage = 1;
  loadBranchPayments();
};

window.pageBranchPayments = function (delta) {
  _bpPage = Math.max(1, _bpPage + delta);
  loadBranchPayments();
};

window.initBranchPayments = function () {
  ['bp-status', 'bp-from', 'bp-to'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', () => { _bpPage = 1; loadBranchPayments(); });
  });
  loadBranchPayments();
};
