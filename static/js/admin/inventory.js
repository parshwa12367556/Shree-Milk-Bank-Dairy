/**
 * ============================================================
 * SMART DAIRY ERP — Inventory Management
 * Live items, stock IN/OUT/ALLOCATE movements, item CRUD.
 * ============================================================
 */

let _inventoryView = 'items'; // 'items' | 'movements'

window.initInventory = function() {
  console.log('Inventory page initialized');
  loadInventoryTable();
  loadInventoryMovements();
  loadBranchesForMovement();
};

function _inventoryIsGlobalRole() {
  const user = window.Auth ? Auth.getUser() : null;
  return !!user && ['ADMIN'].includes(user.role);
}

function toggleInventoryView() {
  _inventoryView = _inventoryView === 'items' ? 'movements' : 'items';
  const itemsView = document.getElementById('inventory-items-view');
  const movesView = document.getElementById('inventory-movements-view');
  const label = document.getElementById('inventory-view-label');
  if (itemsView) itemsView.style.display = _inventoryView === 'items' ? '' : 'none';
  if (movesView) movesView.style.display = _inventoryView === 'movements' ? '' : 'none';
  if (label) label.textContent = _inventoryView === 'items' ? 'Stock Movements' : 'Items';
  if (_inventoryView === 'items') loadInventoryTable();
  else loadInventoryMovements();
}

/** Load inventory items */
async function loadInventoryTable() {
  const tbody = document.querySelector('#inventory-table tbody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="10"><div class="skeleton skeleton-table-row"></div></td></tr>';

  try {
    const result = await API.getInventory();
    const items = result.items || [];
    const summary = result.summary || {};

    const totalEl = document.getElementById('inv-kpi-total');
    const lowEl = document.getElementById('inv-kpi-low');
    if (totalEl) totalEl.querySelector('.kpi-value').textContent = summary.totalItems ?? items.length;
    if (lowEl) lowEl.querySelector('.kpi-value').textContent = summary.lowStockCount ?? 0;

    if (!items.length) {
      tbody.innerHTML = `
        <tr>
          <td colspan="10" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
            <i data-lucide="package" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
            No inventory items yet. Add items to start tracking stock.
          </td>
        </tr>
      `;
      if (window.lucide) lucide.createIcons();
      return;
    }

    const isGlobal = _inventoryIsGlobalRole();
    tbody.innerHTML = items.map((it, idx) => {
      const low = it.status === 'Low Stock';
      const actions = [];
      if (isGlobal) {
        actions.push(`<button class="btn btn-icon btn-sm btn-ghost" title="Stock In" onclick="openMovementModal(${idx}, 'IN')"><i data-lucide="arrow-down-to-line" style="width:16px;height:16px;color:var(--success);"></i></button>`);
        actions.push(`<button class="btn btn-icon btn-sm btn-ghost" title="Stock Out" onclick="openMovementModal(${idx}, 'OUT')"><i data-lucide="arrow-up-from-line" style="width:16px;height:16px;color:var(--danger);"></i></button>`);
        actions.push(`<button class="btn btn-icon btn-sm btn-ghost" title="Allocate to Branch" onclick="openMovementModal(${idx}, 'ALLOCATE')"><i data-lucide="send" style="width:16px;height:16px;color:var(--info);"></i></button>`);
        actions.push(`<button class="btn btn-icon btn-sm btn-ghost" title="Edit" onclick="editInventoryItem(${idx})"><i data-lucide="edit-3" style="width:16px;height:16px;"></i></button>`);
      }
      return `
        <tr>
          <td><span class="font-mono" style="font-weight:600;">${it.code || '-'}</span></td>
          <td>${it.name || '-'}</td>
          <td>${it.category || '-'}</td>
          <td><strong>${fmtNum(it.stock ?? 0)}</strong> ${it.unit || ''}</td>
          <td>${it.unit || '-'}</td>
          <td>${it.minStock ?? 0}</td>
          <td>${it.branchName || '<span style="color:var(--ink-muted);">Central</span>'}</td>
          <td><span class="tag ${low ? 'tag-red' : 'tag-green'}">${it.status || 'In Stock'}</span></td>
          <td>${it.updatedAt ? fmtDate(it.updatedAt, true) : '-'}</td>
          <td><div class="table-actions">${actions.join('')}</div></td>
        </tr>
      `;
    }).join('');
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.warn('Failed to load inventory:', err);
    tbody.innerHTML = `<tr><td colspan="10" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">${err.message || 'Failed to load inventory'}</td></tr>`;
  }
}

/** Load stock movement ledger */
async function loadInventoryMovements() {
  const tbody = document.querySelector('#inventory-movements-table tbody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="7"><div class="skeleton skeleton-table-row"></div></td></tr>';

  try {
    const result = await API.getInventoryMovements({ per_page: 50 });
    const movements = result.movements || [];

    if (!movements.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">No stock movements recorded yet.</td></tr>';
      return;
    }

    const typeBadge = (t) => {
      const map = { IN: 'tag-green', OUT: 'tag-red', ALLOCATE: 'tag-blue' };
      return `<span class="tag ${map[t] || 'tag-neutral'}">${t}</span>`;
    };

    tbody.innerHTML = movements.map(m => `
      <tr>
        <td>${m.createdAt ? fmtDate(m.createdAt) : '-'}</td>
        <td>${m.itemName || '-'}</td>
        <td>${typeBadge(m.movementType)}</td>
        <td><strong>${fmtNum(m.quantity ?? 0)}</strong></td>
        <td>${m.branchName || '<span style="color:var(--ink-muted);">—</span>'}</td>
        <td>${m.reference || '-'}</td>
        <td>${m.note || '-'}</td>
      </tr>
    `).join('');
  } catch (err) {
    console.warn('Failed to load movements:', err);
  }
}

async function loadBranchesForMovement() {
  const select = document.getElementById('inv-move-branch');
  if (!select) return;
  try {
    const result = await API.getBranches();
    const branches = result.branches || [];
    select.innerHTML = '<option value="">Select Branch</option>' +
      branches.map(b => `<option value="${b.id}">${b.code} — ${b.name}</option>`).join('');
  } catch (err) {
    console.warn('Could not load branches');
  }
}

let _inventoryItems = [];

async function ensureItems() {
  if (_inventoryItems.length) return;
  try {
    const result = await API.getInventory({ per_page: 100 });
    _inventoryItems = result.items || [];
  } catch (err) {
    _inventoryItems = [];
  }
}

/** Open stock movement modal */
async function openMovementModal(idx, type) {
  await ensureItems();
  const item = _inventoryItems[idx];
  if (!item) return;

  document.getElementById('inv-move-item-id').value = item.id;
  document.getElementById('inv-move-type').value = type;
  document.getElementById('inv-move-qty').value = '';
  document.getElementById('inv-move-ref').value = '';
  document.getElementById('inv-move-note').value = '';
  document.getElementById('inventory-movement-item-info').textContent =
    `${item.name} (${item.code}) — Current stock: ${fmtNum(item.stock ?? 0)} ${item.unit || ''}`;

  const branchGroup = document.getElementById('inv-move-branch-group');
  branchGroup.style.display = type === 'ALLOCATE' ? '' : 'none';

  document.getElementById('inventory-movement-modal').classList.add('open');
  if (window.lucide) setTimeout(() => lucide.createIcons(), 50);
}

function closeInventoryMovementModal() {
  document.getElementById('inventory-movement-modal').classList.remove('open');
}

/** Record a stock movement */
async function saveInventoryMovement() {
  const id = document.getElementById('inv-move-item-id').value;
  const type = document.getElementById('inv-move-type').value;
  const qty = document.getElementById('inv-move-qty').value;
  const branchId = document.getElementById('inv-move-branch').value;
  const reference = document.getElementById('inv-move-ref').value;
  const note = document.getElementById('inv-move-note').value;

  if (!id || !qty || parseFloat(qty) <= 0) {
    Modal.toast({ title: 'Validation Error', message: 'Quantity is required', type: 'error' });
    return;
  }
  if (type === 'ALLOCATE' && !branchId) {
    Modal.toast({ title: 'Validation Error', message: 'Select a branch for allocation', type: 'error' });
    return;
  }

  try {
    const result = await API.addInventoryMovement(id, {
      type, quantity: parseFloat(qty), branchId: branchId ? parseInt(branchId) : null,
      reference, note,
    });
    closeInventoryMovementModal();
    Modal.toast({ title: 'Movement Recorded', message: result.message || 'Stock updated', type: 'success' });
    _inventoryItems = [];
    loadInventoryTable();
    loadInventoryMovements();
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message || 'Movement failed', type: 'error' });
  }
}

/** Add / edit item modal */
function openInventoryItemModal() {
  document.getElementById('inventory-item-modal-title').textContent = 'Add Inventory Item';
  document.getElementById('inv-item-id').value = '';
  document.getElementById('inventory-item-form').reset();
  document.getElementById('inv-item-stock').value = 0;
  document.getElementById('inv-item-min').value = 0;
  document.getElementById('inventory-item-modal').classList.add('open');
}

async function editInventoryItem(idx) {
  await ensureItems();
  const item = _inventoryItems[idx];
  if (!item) return;
  document.getElementById('inventory-item-modal-title').textContent = 'Edit Inventory Item';
  document.getElementById('inv-item-id').value = item.id;
  document.getElementById('inv-item-name').value = item.name || '';
  document.getElementById('inv-item-category').value = item.category || '';
  document.getElementById('inv-item-stock').value = item.stock ?? 0;
  document.getElementById('inv-item-unit').value = item.unit || '';
  document.getElementById('inv-item-min').value = item.minStock ?? 0;
  document.getElementById('inventory-item-modal').classList.add('open');
}

function closeInventoryItemModal() {
  document.getElementById('inventory-item-modal').classList.remove('open');
}

async function saveInventoryItem() {
  const id = document.getElementById('inv-item-id').value;
  const name = document.getElementById('inv-item-name').value.trim();
  if (!name) {
    Modal.toast({ title: 'Validation Error', message: 'Item name is required', type: 'error' });
    return;
  }
  const payload = {
    name,
    category: document.getElementById('inv-item-category').value.trim(),
    unit: document.getElementById('inv-item-unit').value.trim(),
    minStock: parseFloat(document.getElementById('inv-item-min').value || 0),
  };
  try {
    if (id) {
      await API.updateInventory(id, payload);
    } else {
      payload.stock = parseFloat(document.getElementById('inv-item-stock').value || 0);
      await API.createInventory(payload);
    }
    closeInventoryItemModal();
    _inventoryItems = [];
    loadInventoryTable();
    Modal.toast({ title: id ? 'Updated' : 'Created', message: 'Inventory item saved', type: 'success' });
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message || 'Save failed', type: 'error' });
  }
}

window.toggleInventoryView = toggleInventoryView;
window.openMovementModal = openMovementModal;
window.closeInventoryMovementModal = closeInventoryMovementModal;
window.saveInventoryMovement = saveInventoryMovement;
window.openInventoryItemModal = openInventoryItemModal;
window.editInventoryItem = editInventoryItem;
window.closeInventoryItemModal = closeInventoryItemModal;
window.saveInventoryItem = saveInventoryItem;
