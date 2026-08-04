/**
 * ============================================================
 * SMART DAIRY ERP — Procurement Management
 * Centers, Routes, Chilling Centers, Suppliers,
 * Purchase Orders (workflow), Vendor Payments.
 * ============================================================
 */

let _suppliers = [];
let _purchaseOrders = [];

window.initProcurement = function() {
  console.log('Procurement page initialized');
  initProcurementTabs();
  loadCollectionCenters();
  loadSuppliers();
  loadPurchaseOrders();
  loadVendorPayments();
};

function initProcurementTabs() {
  document.querySelectorAll('.procurement-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.procurement-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      document.querySelectorAll('.procurement-tab-content').forEach(c => c.classList.remove('active'));
      const target = document.getElementById(tab.dataset.tab);
      if (target) target.classList.add('active');

      const tabName = tab.dataset.tab;
      if (tabName === 'centers') loadCollectionCenters();
      else if (tabName === 'routes') loadCollectionRoutes();
      else if (tabName === 'chilling') loadChillingCenters();
      else if (tabName === 'suppliers') loadSuppliers();
      else if (tabName === 'purchase-orders') loadPurchaseOrders();
      else if (tabName === 'vendor-payments') loadVendorPayments();
    });
  });
}

/* ── Centers / Routes / Chilling (live data) ── */

async function loadCollectionCenters() {
  const tbody = document.querySelector('#centers-table tbody');
  if (!tbody) return;
  try {
    const result = await API.getProcurementCenters();
    const centers = result.centers || [];
    if (!centers.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">No collection centers yet.</td></tr>';
      return;
    }
    tbody.innerHTML = centers.map(c => `
      <tr>
        <td><span class="font-mono" style="font-weight:600;">${c.code || '-'}</span></td>
        <td>${c.name || '-'}</td>
        <td><span class="tag tag-neutral">${c.centerType || '-'}</span></td>
        <td>${c.managerName || '-'}</td>
        <td>${c.capacity ? fmtNum(c.capacity) + ' L' : '-'}</td>
        <td><span class="tag ${c.status === 'ACTIVE' ? 'tag-green' : 'tag-neutral'}">${c.status || '-'}</span></td>
        <td>-</td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">${err.message}</td></tr>`;
  }
}

async function loadCollectionRoutes() {
  const tbody = document.querySelector('#routes-table tbody');
  if (!tbody) return;
  try {
    const result = await API.getProcurementRoutes();
    const routes = result.routes || [];
    if (!routes.length) {
      tbody.innerHTML = '<tr><td colspan="9" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">No collection routes yet.</td></tr>';
      return;
    }
    tbody.innerHTML = routes.map(r => `
      <tr>
        <td><span class="font-mono" style="font-weight:600;">${r.code || '-'}</span></td>
        <td>${r.name || '-'}</td>
        <td>${r.centerId || '-'}</td>
        <td>${r.driverName || '-'}</td>
        <td>${r.vehicleNumber || '-'}</td>
        <td>${r.distance ? r.distance + ' km' : '-'}</td>
        <td>${r.farmerCount ?? 0}</td>
        <td><span class="tag ${r.status === 'ACTIVE' ? 'tag-green' : 'tag-neutral'}">${r.status || '-'}</span></td>
        <td>-</td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">${err.message}</td></tr>`;
  }
}

async function loadChillingCenters() {
  const tbody = document.querySelector('#chilling-table tbody');
  if (!tbody) return;
  try {
    const result = await API.getChillingCenters();
    const centers = result.chilling_centers || [];
    if (!centers.length) {
      tbody.innerHTML = '<tr><td colspan="9" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">No chilling centers yet.</td></tr>';
      return;
    }
    tbody.innerHTML = centers.map(c => `
      <tr>
        <td><span class="font-mono" style="font-weight:600;">${c.code || '-'}</span></td>
        <td>${c.name || '-'}</td>
        <td>${c.tankCount ?? 0}</td>
        <td>${c.totalCapacity ? fmtNum(c.totalCapacity) + ' L' : '-'}</td>
        <td>${c.currentStock ? fmtNum(c.currentStock) + ' L' : '0 L'}</td>
        <td>${c.temperature != null ? c.temperature + '°C' : '-'}</td>
        <td>${c.hasGenerator ? '<span class="tag tag-green">Yes</span>' : '<span class="tag tag-neutral">No</span>'}</td>
        <td><span class="tag ${c.status === 'ACTIVE' ? 'tag-green' : 'tag-neutral'}">${c.status || '-'}</span></td>
        <td>-</td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">${err.message}</td></tr>`;
  }
}

/* ── Suppliers ── */

async function loadSuppliers() {
  const tbody = document.querySelector('#suppliers-table tbody');
  if (!tbody) return;
  try {
    const result = await API.getSuppliers();
    _suppliers = result.suppliers || [];
    if (!_suppliers.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">No suppliers yet. Click "Add Supplier".</td></tr>';
      return;
    }
    tbody.innerHTML = _suppliers.map((s, idx) => `
      <tr>
        <td><span class="font-mono" style="font-weight:600;">${s.code || '-'}</span></td>
        <td>${s.name || '-'}</td>
        <td><span class="tag tag-blue">${s.category || '-'}</span></td>
        <td>${s.contactPerson || '-'}</td>
        <td>${s.phone || '-'}</td>
        <td>${s.email || '-'}</td>
        <td><span class="tag ${s.status === 'ACTIVE' ? 'tag-green' : 'tag-neutral'}">${s.status || '-'}</span></td>
        <td>
          <div class="table-actions">
            <button class="btn btn-icon btn-sm btn-ghost" title="Edit" onclick="editSupplier(${idx})"><i data-lucide="edit-3" style="width:16px;height:16px;"></i></button>
            <button class="btn btn-icon btn-sm btn-ghost" title="Delete" onclick="deleteSupplier(${idx})" style="color:var(--danger);"><i data-lucide="trash-2" style="width:16px;height:16px;"></i></button>
          </div>
        </td>
      </tr>
    `).join('');
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">${err.message}</td></tr>`;
  }
}

function openSupplierModal() {
  document.getElementById('supplier-modal-title').textContent = 'Add Supplier';
  document.getElementById('supplier-id').value = '';
  document.getElementById('supplier-form').reset();
  document.getElementById('supplier-modal').classList.add('open');
}

function editSupplier(idx) {
  const s = _suppliers[idx];
  if (!s) return;
  document.getElementById('supplier-modal-title').textContent = 'Edit Supplier';
  document.getElementById('supplier-id').value = s.id;
  document.getElementById('supplier-name').value = s.name || '';
  document.getElementById('supplier-category').value = s.category || 'OTHER';
  document.getElementById('supplier-contact').value = s.contactPerson || '';
  document.getElementById('supplier-phone').value = s.phone || '';
  document.getElementById('supplier-email').value = s.email || '';
  document.getElementById('supplier-address').value = s.address || '';
  document.getElementById('supplier-modal').classList.add('open');
}

function closeSupplierModal() {
  document.getElementById('supplier-modal').classList.remove('open');
}

async function saveSupplier() {
  const id = document.getElementById('supplier-id').value;
  const name = document.getElementById('supplier-name').value.trim();
  if (!name) {
    Modal.toast({ title: 'Validation Error', message: 'Supplier name is required', type: 'error' });
    return;
  }
  const payload = {
    name,
    category: document.getElementById('supplier-category').value,
    contactPerson: document.getElementById('supplier-contact').value.trim(),
    phone: document.getElementById('supplier-phone').value.trim(),
    email: document.getElementById('supplier-email').value.trim(),
    address: document.getElementById('supplier-address').value.trim(),
  };
  try {
    if (id) await API.updateSupplier(id, payload);
    else await API.createSupplier(payload);
    closeSupplierModal();
    loadSuppliers();
    Modal.toast({ title: 'Saved', message: 'Supplier saved successfully', type: 'success' });
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message || 'Save failed', type: 'error' });
  }
}

function deleteSupplier(idx) {
  const s = _suppliers[idx];
  if (!s) return;
  Modal.confirm({
    title: 'Delete Supplier',
    message: `Delete supplier <strong>${s.name}</strong>?`,
    confirmText: 'Delete',
    variant: 'danger',
    onConfirm: async () => {
      try {
        await API.deleteSupplier(s.id);
        loadSuppliers();
        Modal.toast({ title: 'Deleted', message: 'Supplier deleted', type: 'success' });
      } catch (err) {
        Modal.toast({ title: 'Error', message: err.message, type: 'error' });
      }
    }
  });
}

/* ── Purchase Orders ── */

const _poStatusBadge = (s) => {
  const map = {
    DRAFT: 'tag-neutral', PENDING: 'tag-gold', APPROVED: 'tag-blue',
    RECEIVED: 'tag-purple', COMPLETED: 'tag-green', REJECTED: 'tag-red',
  };
  return `<span class="tag ${map[s] || 'tag-neutral'}">${s || ''}</span>`;
};

async function loadPurchaseOrders() {
  const tbody = document.querySelector('#pos-table tbody');
  if (!tbody) return;
  try {
    const result = await API.getPurchaseOrders();
    _purchaseOrders = result.purchase_orders || [];
    if (!_purchaseOrders.length) {
      tbody.innerHTML = '<tr><td colspan="9" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">No purchase orders yet. Click "New Purchase Order".</td></tr>';
      return;
    }
    tbody.innerHTML = _purchaseOrders.map((po, idx) => `
      <tr>
        <td><span class="font-mono" style="font-weight:600;">${po.poCode || '-'}</span></td>
        <td>${po.supplierName || '-'}</td>
        <td>${po.orderDate ? fmtDate(po.orderDate, true) : '-'}</td>
        <td>${po.items ? po.items.length : 0}</td>
        <td>${fmtINR(po.totalAmount ?? 0)}</td>
        <td>${fmtINR(po.paidAmount ?? 0)}</td>
        <td>${fmtINR(po.balance ?? (po.totalAmount || 0))}</td>
        <td>${_poStatusBadge(po.status)}</td>
        <td><div class="table-actions">${poActions(po, idx)}</div></td>
      </tr>
    `).join('');
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">${err.message}</td></tr>`;
  }
}

function poActions(po, idx) {
  const btns = [];
  const next = {
    DRAFT: ['PENDING', 'Submit', 'send'],
    PENDING: ['APPROVED', 'Approve', 'check-circle'],
    APPROVED: ['RECEIVED', 'Receive Stock', 'package-check'],
    RECEIVED: ['COMPLETED', 'Complete', 'check'],
  };
  if (next[po.status]) {
    btns.push(`<button class="btn btn-sm btn-primary" title="${next[po.status][1]}" onclick="advancePO(${idx}, '${next[po.status][0]}')"><i data-lucide="${next[po.status][2]}" style="width:14px;height:14px;"></i> ${next[po.status][1]}</button>`);
  }
  if (['DRAFT', 'PENDING', 'APPROVED'].includes(po.status)) {
    btns.push(`<button class="btn btn-icon btn-sm btn-ghost" title="Reject" onclick="advancePO(${idx}, 'REJECTED')" style="color:var(--danger);"><i data-lucide="x-circle" style="width:16px;height:16px;"></i></button>`);
  }
  return btns.join('');
}

function advancePO(idx, status) {
  const po = _purchaseOrders[idx];
  if (!po) return;
  Modal.confirm({
    title: `${status} Purchase Order`,
    message: `Move <strong>${po.poCode}</strong> to <strong>${status}</strong>?`,
    confirmText: status === 'RECEIVED' ? 'Receive & Add Stock' : status,
    variant: status === 'REJECTED' ? 'danger' : 'info',
    onConfirm: async () => {
      try {
        const result = await API.updatePurchaseOrder(po.id, { status });
        loadPurchaseOrders();
        Modal.toast({ title: 'Updated', message: result.message || `PO is now ${status}`, type: 'success' });
      } catch (err) {
        Modal.toast({ title: 'Error', message: err.message || 'Transition failed', type: 'error' });
      }
    }
  });
}

async function openPOModal() {
  await ensureSuppliersLoaded();
  document.getElementById('po-form').reset();
  document.getElementById('po-date').value = todayISO();
  document.getElementById('po-items-container').innerHTML = '';
  addPOItemRow();
  const branchSelect = document.getElementById('po-branch');
  branchSelect.innerHTML = '<option value="">Central Warehouse</option>';
  try {
    const branches = (await API.getBranches()).branches || [];
    branchSelect.innerHTML += branches.map(b => `<option value="${b.id}">${b.code} — ${b.name}</option>`).join('');
  } catch (err) { /* ignore */ }
  document.getElementById('po-modal').classList.add('open');
  if (window.lucide) setTimeout(() => lucide.createIcons(), 50);
}

function closePOModal() {
  document.getElementById('po-modal').classList.remove('open');
}

function addPOItemRow() {
  const container = document.getElementById('po-items-container');
  if (!container) return;
  const row = document.createElement('div');
  row.className = 'form-grid';
  row.style.marginBottom = 'var(--space-2)';
  row.innerHTML = `
    <div class="form-group"><label class="form-label">Item</label><input type="text" class="input-premium po-item-name" placeholder="e.g. Milk Cans"></div>
    <div class="form-group"><label class="form-label">Qty</label><input type="number" class="input-premium po-item-qty" min="0" step="0.5" value="0"></div>
    <div class="form-group"><label class="form-label">Unit</label><input type="text" class="input-premium po-item-unit" placeholder="nos" value="nos"></div>
    <div class="form-group"><label class="form-label">Rate</label><input type="number" class="input-premium po-item-price" min="0" step="0.01" value="0"></div>
    <div class="form-group"><button type="button" class="btn btn-icon btn-sm btn-ghost" style="margin-top:24px;color:var(--danger);" onclick="this.closest('.form-grid').remove(); updatePOTotal();"><i data-lucide="x" style="width:16px;height:16px;"></i></button></div>
  `;
  container.appendChild(row);
  row.querySelectorAll('.po-item-qty, .po-item-price').forEach(inp => {
    inp.addEventListener('input', updatePOTotal);
  });
  if (window.lucide) lucide.createIcons();
}

function updatePOTotal() {
  const rows = document.querySelectorAll('#po-items-container .form-grid');
  let total = 0;
  rows.forEach(row => {
    const qty = parseFloat(row.querySelector('.po-item-qty')?.value || 0);
    const price = parseFloat(row.querySelector('.po-item-price')?.value || 0);
    total += qty * price;
  });
  const el = document.getElementById('po-total');
  if (el) el.textContent = fmtINR(total);
}

async function savePurchaseOrder() {
  const supplierId = document.getElementById('po-supplier').value;
  if (!supplierId) {
    Modal.toast({ title: 'Validation Error', message: 'Select a supplier', type: 'error' });
    return;
  }
  const items = [];
  document.querySelectorAll('#po-items-container .form-grid').forEach(row => {
    const itemName = row.querySelector('.po-item-name')?.value.trim();
    const qty = parseFloat(row.querySelector('.po-item-qty')?.value || 0);
    const unit = row.querySelector('.po-item-unit')?.value.trim() || 'nos';
    const price = parseFloat(row.querySelector('.po-item-price')?.value || 0);
    if (itemName && qty > 0) items.push({ itemName, quantity: qty, unit, unitPrice: price });
  });
  if (!items.length) {
    Modal.toast({ title: 'Validation Error', message: 'Add at least one line item', type: 'error' });
    return;
  }
  const payload = {
    supplierId: parseInt(supplierId),
    branchId: document.getElementById('po-branch').value ? parseInt(document.getElementById('po-branch').value) : null,
    orderDate: document.getElementById('po-date').value,
    expectedDate: document.getElementById('po-expected').value,
    remarks: document.getElementById('po-remarks').value.trim(),
    items,
  };
  try {
    const result = await API.createPurchaseOrder(payload);
    closePOModal();
    loadPurchaseOrders();
    Modal.toast({ title: 'Created', message: result.message || 'Purchase order created', type: 'success' });
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message || 'Failed to create PO', type: 'error' });
  }
}

async function ensureSuppliersLoaded() {
  const select = document.getElementById('po-supplier');
  if (!select) return;
  try {
    const result = await API.getSuppliers();
    _suppliers = result.suppliers || [];
    select.innerHTML = '<option value="">Select Supplier</option>' +
      _suppliers.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
  } catch (err) { /* ignore */ }
}

/* ── Vendor Payments ── */

async function loadVendorPayments() {
  const tbody = document.querySelector('#vp-table tbody');
  if (!tbody) return;
  try {
    const result = await API.getVendorPayments();
    const payments = result.vendor_payments || [];
    if (!payments.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">No vendor payments yet.</td></tr>';
      return;
    }
    tbody.innerHTML = payments.map(p => `
      <tr>
        <td><span class="font-mono" style="font-weight:600;">${p.paymentCode || '-'}</span></td>
        <td>${p.poCode || '-'}</td>
        <td>${p.supplierName || '-'}</td>
        <td><strong>${fmtINR(p.amount ?? 0)}</strong></td>
        <td>${p.paymentDate ? fmtDate(p.paymentDate, true) : '-'}</td>
        <td><span class="tag tag-neutral">${(p.method || 'BANK_TRANSFER').replace(/_/g, ' ')}</span></td>
        <td>${p.reference || '-'}</td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">${err.message}</td></tr>`;
  }
}

async function openVendorPaymentModal() {
  const select = document.getElementById('vp-po');
  select.innerHTML = '<option value="">Select PO</option>';
  try {
    const result = await API.getPurchaseOrders({ per_page: 50 });
    const pos = (result.purchase_orders || []).filter(p => (p.balance ?? 0) > 0 && p.status !== 'COMPLETED' && p.status !== 'REJECTED');
    select.innerHTML += pos.map(p => `<option value="${p.id}">${p.poCode} — ${p.supplierName} (balance ${fmtINR(p.balance)})</option>`).join('');
  } catch (err) { /* ignore */ }
  document.getElementById('vp-form').reset();
  document.getElementById('vp-date').value = todayISO();
  document.getElementById('vp-modal').classList.add('open');
}

function closeVendorPaymentModal() {
  document.getElementById('vp-modal').classList.remove('open');
}

async function saveVendorPayment() {
  const poId = document.getElementById('vp-po').value;
  const amount = document.getElementById('vp-amount').value;
  if (!poId || !amount || parseFloat(amount) <= 0) {
    Modal.toast({ title: 'Validation Error', message: 'Select a PO and enter a valid amount', type: 'error' });
    return;
  }
  const payload = {
    poId: parseInt(poId),
    amount: parseFloat(amount),
    paymentDate: document.getElementById('vp-date').value,
    method: document.getElementById('vp-method').value,
    reference: document.getElementById('vp-reference').value.trim(),
  };
  try {
    const result = await API.createVendorPayment(payload);
    closeVendorPaymentModal();
    loadVendorPayments();
    loadPurchaseOrders();
    Modal.toast({ title: 'Payment Recorded', message: result.message || 'Vendor payment recorded', type: 'success' });
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message || 'Payment failed', type: 'error' });
  }
}

window.openSupplierModal = openSupplierModal;
window.editSupplier = editSupplier;
window.closeSupplierModal = closeSupplierModal;
window.saveSupplier = saveSupplier;
window.deleteSupplier = deleteSupplier;
window.openPOModal = openPOModal;
window.closePOModal = closePOModal;
window.addPOItemRow = addPOItemRow;
window.updatePOTotal = updatePOTotal;
window.savePurchaseOrder = savePurchaseOrder;
window.advancePO = advancePO;
window.openVendorPaymentModal = openVendorPaymentModal;
window.closeVendorPaymentModal = closeVendorPaymentModal;
window.saveVendorPayment = saveVendorPayment;
