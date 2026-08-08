/**
 * SHREE MILK BANK — Farmer: My Passbook
 * Loads the authenticated farmer's passbook from
 * GET /api/farmer/me/passbook (server-scoped to the farmer).
 */
let _passbookPage = 1;
const PB_PER_PAGE = 20;

function _pbParams() {
  return {
    page: _passbookPage,
    per_page: PB_PER_PAGE,
    from: document.getElementById('filter-from')?.value || '',
    to: document.getElementById('filter-to')?.value || '',
  };
}

function _shiftBadge(shift) {
  return shift === 'MORNING'
    ? '<span class="tag tag-blue">Morning</span>'
    : '<span class="tag tag-gold">Evening</span>';
}

function _payStatusBadge(status) {
  const map = { PAID: 'tag-green', APPROVED: 'tag-blue', PENDING: 'tag-gold' };
  if (!status) return '<span class="tag tag-neutral" style="font-size:10px;">Unpaid</span>';
  return `<span class="tag ${map[status] || 'tag-neutral'}" style="font-size:10px;">${status.charAt(0) + status.slice(1).toLowerCase()}</span>`;
}

async function loadFarmerPassbook() {
  const body = document.getElementById('passbook-body');
  if (body) body.innerHTML = '<tr><td colspan="9" class="text-center" style="padding:var(--space-4);color:var(--ink-muted);font-size:var(--text-sm);">Loading passbook…</td></tr>';

  try {
    const data = await API.getMyPassbook(_pbParams());
    const entries = data.entries || [];
    const summary = data.summary || {};

    // Summary cards
    const cards = {
      'pb-total-qty': `${fmtNum(summary.totalQuantity, 2)} L`,
      'pb-total-amount': fmtINR(summary.totalAmount),
      'pb-paid-amount': fmtINR(summary.paidAmount),
      'pb-pending-amount': fmtINR(summary.pendingAmount),
    };
    Object.entries(cards).forEach(([id, v]) => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = v;
    });

    const totalEl = document.getElementById('passbook-total');
    if (totalEl) totalEl.textContent = `${data.total || 0} entries`;

    const pager = document.getElementById('passbook-pager-info');
    if (pager) {
      const from = data.total === 0 ? 0 : ((data.page - 1) * (data.perPage || PB_PER_PAGE)) + 1;
      const to = Math.min((data.page || 1) * (data.perPage || PB_PER_PAGE), data.total || 0);
      pager.textContent = `Showing ${from}-${to} of ${data.total || 0} entries`;
    }
    const prev = document.getElementById('passbook-prev');
    const next = document.getElementById('passbook-next');
    if (prev) prev.disabled = !(data.page && data.page > 1);
    if (next) next.disabled = !(data.page && data.pages && data.page < data.pages);

    if (!entries.length) {
      body.innerHTML = '<tr><td colspan="9" class="text-center" style="padding:var(--space-6);"><div class="empty-icon" style="margin:0 auto var(--space-3);"><i data-lucide="book-open" style="width:36px;height:36px;"></i></div><p style="color:var(--ink-muted);font-size:var(--text-sm);">No passbook entries found.</p><p style="color:var(--ink-muted);font-size:var(--text-xs);margin-top:var(--space-1);">Milk collections will appear here automatically once recorded by your branch.</p></td></tr>';
    } else {
      body.innerHTML = entries.map(e => `
        <tr>
          <td>${fmtDate(e.date)}</td>
          <td>${_shiftBadge(e.shift)}</td>
          <td>${fmtNum(e.quantity, 2)} L</td>
          <td>${e.fat != null ? e.fat + '%' : '—'}</td>
          <td>${e.snf != null ? e.snf + '%' : '—'}</td>
          <td>${e.ratePerLiter != null ? '₹' + fmtNum(e.ratePerLiter, 2) + '/L' : '—'}</td>
          <td style="font-weight:600;color:var(--forest);">${fmtINR(e.amount)}</td>
          <td>${fmtINR(e.balance)}</td>
          <td>${_payStatusBadge(e.paymentStatus)}${e.paymentCode ? `<div style="font-size:10px;color:var(--ink-muted);">${e.paymentCode}</div>` : ''}</td>
        </tr>`).join('');
    }
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.warn('Failed to load passbook:', err);
    if (body) body.innerHTML = `<tr><td colspan="9" class="text-center" style="padding:var(--space-5);">
      <p style="color:var(--ink-muted);font-size:var(--text-sm);">Unable to load passbook. Try again.</p>
      <button class="btn btn-sm btn-ghost" style="margin-top:var(--space-2);" onclick="window.refreshFarmerPassbook && refreshFarmerPassbook()">Try Again</button>
    </td></tr>`;
  }
}

window.refreshFarmerPassbook = function () {
  _passbookPage = 1;
  loadFarmerPassbook();
};

window.pageFarmerPassbook = function (delta) {
  _passbookPage = Math.max(1, _passbookPage + delta);
  loadFarmerPassbook();
};

window.initFarmerPassbook = function () {
  ['filter-from', 'filter-to'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', () => { _passbookPage = 1; loadFarmerPassbook(); });
  });
  loadFarmerPassbook();
};
