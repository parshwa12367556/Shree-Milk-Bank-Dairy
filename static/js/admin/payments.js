/**
 * ============================================================
 * SMART DAIRY ERP — Payments Page
 * ============================================================
 * Full payment sheet generation via API
 * ============================================================
 */

window.initPayments = function() {
  console.log('Payments page initialized');
  // Keep the table in sync with the (persistent) status filter selection
  const statusFilter = document.getElementById('payment-status-filter');
  loadPayments(statusFilter && statusFilter.value ? { status: statusFilter.value } : {});
  initPaymentActions();
};

async function loadPayments(filters = {}) {
  const tbody = document.querySelector('#payments-table tbody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="9"><div class="skeleton skeleton-table-row"></div></td></tr>';

  try {
    const result = await API.getPayments(filters);
    const payments = result.payments || result.data || [];
    renderPaymentsTable(payments);
    updatePaymentSummary(result.summary);
  } catch (err) {
    console.warn('Failed to load payments:', err);
    renderPaymentsTable([]);
    updatePaymentSummary(null);
  }
}

/** Render payment summary cards from real API data */
function updatePaymentSummary(summary) {
  const paidEl = document.getElementById('summary-total-paid');
  const pendingEl = document.getElementById('summary-pending');
  const rateEl = document.getElementById('summary-rate');

  if (!summary) {
    if (paidEl) paidEl.textContent = '—';
    if (pendingEl) pendingEl.textContent = '—';
    if (rateEl) rateEl.textContent = '—';
    return;
  }

  if (paidEl) paidEl.textContent = summary.totalPaid != null ? fmtINR(summary.totalPaid) : '—';
  if (pendingEl) pendingEl.textContent = summary.totalPending != null ? fmtINR(summary.totalPending) : '—';
  if (rateEl) rateEl.textContent = summary.paymentRate != null ? summary.paymentRate + '%' : '—';
}

function renderPaymentsTable(payments) {
  const tbody = document.querySelector('#payments-table tbody');
  if (!tbody) return;

  if (!payments.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="9" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
          <i data-lucide="wallet" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
          No payment records yet. Generate a payment sheet to get started.
        </td>
      </tr>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  const statusBadges = { PENDING: 'tag-gold', APPROVED: 'tag-blue', PAID: 'tag-green' };
  const user = window.Auth ? Auth.getUser() : null;
  const isGlobal = !!user && ['SUPER_ADMIN', 'HEAD_OFFICE'].includes(user.role);

  tbody.innerHTML = payments.map(p => {
    const actions = [];
    if (isGlobal && p.status === 'PENDING') {
      actions.push(`<button class="btn btn-sm btn-primary" onclick="approvePayment(${p.id})"><i data-lucide="check-circle" style="width:14px;height:14px;"></i> Approve</button>`);
    }
    if (isGlobal && p.status === 'APPROVED') {
      actions.push(`<button class="btn btn-sm btn-success" onclick="markPaymentPaid(${p.id})"><i data-lucide="wallet" style="width:14px;height:14px;"></i> Mark Paid</button>`);
    }
    if (!actions.length) actions.push('<span style="color:var(--ink-muted);font-size:var(--text-xs);">—</span>');
    return `
    <tr>
      <td><span class="font-mono" style="font-weight:600;">${p.payCode || '-'}</span></td>
      <td>${p.farmerName || '-'}</td>
      <td>${p.periodStart ? fmtDate(p.periodStart, true) : '-'} - ${p.periodEnd ? fmtDate(p.periodEnd, true) : '-'}</td>
      <td>${p.totalQuantity ? p.totalQuantity + ' L' : '-'}</td>
      <td>${p.totalAmount ? fmtINR(p.totalAmount) : '-'}</td>
      <td><span class="font-mono" style="font-size:var(--text-xs);">${p.reference || '<span style="color:var(--ink-muted);">—</span>'}</span></td>
      <td><span class="tag ${statusBadges[p.status] || 'tag-neutral'}">${p.status || '-'}</span></td>
      <td>${fmtDate(p.createdAt, true)}</td>
      <td><div class="table-actions">${actions.join('')}</div></td>
    </tr>
  `;}).join('');
  if (window.lucide) lucide.createIcons();
}

/** Approve a payment (Head Office) */
async function approvePayment(id) {
  try {
    const result = await API.updatePayment(id, { status: 'APPROVED' });
    Modal.toast({ title: 'Approved', message: result.message || 'Payment approved', type: 'success' });
    const statusFilter = document.getElementById('payment-status-filter');
    loadPayments(statusFilter && statusFilter.value ? { status: statusFilter.value } : {});
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message, type: 'error' });
  }
}

/** Mark a payment as PAID — simulated bank transfer with UTR reference */
async function markPaymentPaid(id) {
  Modal.confirm({
    title: 'Transfer Payment',
    message: 'Confirm bank transfer to the farmer\'s registered account? A UTR reference will be generated.',
    confirmText: 'Transfer & Mark Paid',
    variant: 'info',
    onConfirm: async () => {
      try {
        const result = await API.updatePayment(id, { status: 'PAID' });
        Modal.toast({ title: 'Paid', message: result.message || 'Payment transferred', type: 'success' });
        const statusFilter = document.getElementById('payment-status-filter');
        loadPayments(statusFilter && statusFilter.value ? { status: statusFilter.value } : {});
      } catch (err) {
        Modal.toast({ title: 'Error', message: err.message, type: 'error' });
      }
    }
  });
}

function initPaymentActions() {
  const generateBtn = document.getElementById('generate-payment');
  if (generateBtn && !generateBtn.hasAttribute('data-listener')) {
    generateBtn.setAttribute('data-listener', 'true');
    generateBtn.addEventListener('click', openPaymentModal);
  }
  // Payment modal buttons
  const saveBtn = document.getElementById('payment-save-btn');
  if (saveBtn && !saveBtn.hasAttribute('data-listener')) {
    saveBtn.setAttribute('data-listener', 'true');
    saveBtn.addEventListener('click', generatePaymentSheet);
  }
  // Status filter - reloads from the API with the selected status
  const statusFilter = document.getElementById('payment-status-filter');
  if (statusFilter && !statusFilter.hasAttribute('data-listener')) {
    statusFilter.setAttribute('data-listener', 'true');
    statusFilter.addEventListener('change', () => {
      loadPayments({ status: statusFilter.value });
    });
  }
}

function openPaymentModal() {
  document.getElementById('payment-modal-title').textContent = 'Generate Payment Sheet';
  document.getElementById('payment-form').reset();
  document.getElementById('payment-farmer-id').value = '';
  Modal.open('payment-modal');
  if (window.lucide) setTimeout(() => lucide.createIcons(), 50);
}

function closePaymentModal() {
  Modal.close('payment-modal');
}

async function generatePaymentSheet() {
  const farmerId = document.getElementById('payment-farmer-id').value.trim();
  const periodStart = document.getElementById('payment-period-start').value;
  const periodEnd = document.getElementById('payment-period-end').value;

  if (!farmerId || !periodStart || !periodEnd) {
    Modal.toast({ title: 'Validation Error', message: 'Farmer ID, period start and end are required', type: 'error' });
    return;
  }

  try {
    const result = await API.createPayment({
      farmer_id: parseInt(farmerId),
      period_start: periodStart,
      period_end: periodEnd,
      branch_id: 1,
      status: 'PENDING',
    });
    closePaymentModal();
    const statusFilter = document.getElementById('payment-status-filter');
    await loadPayments(statusFilter && statusFilter.value ? { status: statusFilter.value } : {});
    Modal.toast({ title: 'Payment Sheet Created', message: `Payment ${result.payment?.payCode || ''} generated successfully`, type: 'success' });
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message || 'Failed to generate payment', type: 'error' });
  }
}

// Expose modal functions
window.openPaymentModal = openPaymentModal;
window.closePaymentModal = closePaymentModal;
window.approvePayment = approvePayment;
window.markPaymentPaid = markPaymentPaid;
