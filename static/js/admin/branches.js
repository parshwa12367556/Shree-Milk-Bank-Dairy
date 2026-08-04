/**
 * ============================================================
 * SMART DAIRY ERP — Branches Management
 * ============================================================
 * Full CRUD: Add, Edit, and manage branches via API
 * ============================================================
 */

let branchesData = [];

/** Initialize branches page */
window.initBranches = function() {
  console.log('Branches page initialized');
  loadBranches();
};

/** Load branches from API */
async function loadBranches() {
  const tbody = document.querySelector('#branches-table tbody');
  if (!tbody) return;

  // Show loading skeleton
  tbody.innerHTML = '<tr><td colspan="9"><div class="skeleton skeleton-table-row"></div></td></tr>';

  try {
    const result = await API.getBranches();
    branchesData = result.branches || result.data || [];
  } catch (err) {
    console.warn('Failed to load branches:', err);
    branchesData = [];
  }

  renderBranchesTable();
}

/** Render branches table */
function renderBranchesTable() {
  const tbody = document.querySelector('#branches-table tbody');
  if (!tbody) return;

  if (!branchesData.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="9" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
          <i data-lucide="building-2" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
          No branches configured yet. Click <strong>"Add Branch"</strong> to create one.
        </td>
      </tr>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  const statusDots = { ACTIVE: 'online', INACTIVE: 'offline' };

  tbody.innerHTML = branchesData.map((b, idx) => {
    const farmerCount = b.farmerCount || b.farmer_count || 0;
    return `
      <tr>
        <td><span class="font-mono" style="font-weight:600;">${b.code || '-'}</span></td>
        <td>${b.name || '-'}</td>
        <td>${b.managerName || b.manager_name || '-'}</td>
        <td>${b.phone || '-'}</td>
        <td>${b.village || b.district || b.address || '-'}</td>
        <td>${farmerCount}</td>
        <td>—</td>
        <td>
          <span class="status-dot ${statusDots[b.status] || 'offline'}"></span>
          ${b.status ? b.status.charAt(0) + b.status.slice(1).toLowerCase() : 'Unknown'}
        </td>
        <td>
          <div class="table-actions">
            <button class="btn btn-icon btn-sm btn-ghost" title="Reset Login Password" onclick="resetBranchPassword(${idx})" style="color:var(--warning-dark);">
              <i data-lucide="key-round" style="width:16px;height:16px;"></i>
            </button>
            <button class="btn btn-icon btn-sm btn-ghost" title="Edit Branch" onclick="editBranch(${idx})">
              <i data-lucide="edit-3" style="width:16px;height:16px;"></i>
            </button>
            <button class="btn btn-icon btn-sm btn-ghost" title="Delete Branch" onclick="deleteBranch(${idx})" style="color:var(--danger);">
              <i data-lucide="trash-2" style="width:16px;height:16px;"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  if (window.lucide) lucide.createIcons();
}

/** Open modal to add a new branch */
function openBranchModal() {
  document.getElementById('branch-modal-title').textContent = 'Add New Branch';
  document.getElementById('branch-id').value = '';
  document.getElementById('branch-form').reset();
  document.getElementById('branch-status').value = 'ACTIVE';
  document.getElementById('branch-submit-btn').innerHTML = '<i data-lucide="plus" style="width:16px;height:16px;"></i> Create Branch';
  Modal.open('branch-modal');
  if (window.lucide) setTimeout(() => lucide.createIcons(), 50);
}

/** Open modal to edit an existing branch */
function editBranch(idx) {
  const b = branchesData[idx];
  if (!b) return;

  document.getElementById('branch-modal-title').textContent = 'Edit Branch';
  document.getElementById('branch-id').value = b.id || '';
  document.getElementById('branch-code').value = b.code || '';
  document.getElementById('branch-name').value = b.name || '';
  document.getElementById('branch-manager').value = b.managerName || b.manager_name || '';
  document.getElementById('branch-phone').value = b.phone || '';
  document.getElementById('branch-address').value = b.address || '';
  document.getElementById('branch-village').value = b.village || '';
  document.getElementById('branch-district').value = b.district || '';
  document.getElementById('branch-state').value = b.state || '';
  document.getElementById('branch-status').value = b.status || 'ACTIVE';
  document.getElementById('branch-submit-btn').innerHTML = '<i data-lucide="save" style="width:16px;height:16px;"></i> Update Branch';
  Modal.open('branch-modal');
  if (window.lucide) setTimeout(() => lucide.createIcons(), 50);
}

/** Close branch modal */
function closeBranchModal() {
  Modal.close('branch-modal');
}

/** Save branch (create or update) */
async function saveBranch(event) {
  event.preventDefault();

  const id = document.getElementById('branch-id').value;
  const code = document.getElementById('branch-code').value.trim();
  const name = document.getElementById('branch-name').value.trim();
  const managerName = document.getElementById('branch-manager').value.trim();
  const phone = document.getElementById('branch-phone').value.trim();
  const address = document.getElementById('branch-address').value.trim();
  const village = document.getElementById('branch-village').value.trim();
  const district = document.getElementById('branch-district').value.trim();
  const state = document.getElementById('branch-state').value.trim();
  const status = document.getElementById('branch-status').value;

  // Validate
  if (!code) {
    Modal.toast({ title: 'Validation Error', message: 'Branch code is required', type: 'error' });
    return;
  }
  if (!name) {
    Modal.toast({ title: 'Validation Error', message: 'Branch name is required', type: 'error' });
    return;
  }

  const payload = {
    code,
    name,
    managerName: managerName || null,
    phone: phone || null,
    address: address || null,
    village: village || null,
    district: district || null,
    state: state || null,
    status,
  };

  try {
    if (id) {
      await API.updateBranch(parseInt(id), payload);
      closeBranchModal();
      await loadBranches();
      Modal.toast({ title: 'Branch Updated', message: `Branch ${name} (${code}) updated successfully`, type: 'success' });
      return;
    }

    const result = await API.createBranch(payload);
    closeBranchModal();
    await loadBranches();
    const loginMsg = result.message || `Branch login: ${code} / ${phone || '—'}`;
    Modal.toast({ title: 'Branch Created', message: loginMsg, type: 'success' });
  } catch (err) {
    console.warn('Failed to save branch:', err);
    Modal.toast({ title: 'Error', message: err.message || 'Failed to create branch', type: 'error' });
  }
}

/** Reset a branch's login password to its phone number */
async function resetBranchPassword(idx) {
  const b = branchesData[idx];
  if (!b) return;

  Modal.confirm({
    title: 'Reset Branch Password',
    message: `Reset login password for <strong>${b.code}</strong>?<br>It will be set to the branch phone number: <strong>${b.phone || '—'}</strong>`,
    confirmText: 'Reset',
    variant: 'warning',
    onConfirm: async () => {
      try {
        const result = await API.resetBranchPassword(b.id);
        Modal.toast({ title: 'Password Reset', message: result.message || 'Password reset successfully', type: 'success' });
      } catch (err) {
        Modal.toast({ title: 'Error', message: err.message || 'Failed to reset password', type: 'error' });
      }
    }
  });
}

/** Delete branch with confirmation */
function deleteBranch(idx) {
  const b = branchesData[idx];
  if (!b) return;

  Modal.confirm({
    title: 'Delete Branch',
    message: `Are you sure you want to delete branch <strong>${b.name}</strong> (${b.code})?`,
    confirmText: 'Delete',
    variant: 'danger',
    onConfirm: async () => {
      try {
        await API.deleteBranch(b.id);
        await loadBranches();
        Modal.toast({ title: 'Deleted', message: 'Branch deleted successfully', type: 'success' });
      } catch (err) {
        Modal.toast({ title: 'Error', message: err.message || 'Failed to delete branch', type: 'error' });
      }
    }
  });
}

// Make functions globally accessible
window.openBranchModal = openBranchModal;
window.closeBranchModal = closeBranchModal;
window.saveBranch = saveBranch;
window.resetBranchPassword = resetBranchPassword;
