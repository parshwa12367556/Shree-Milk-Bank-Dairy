/**
 * ============================================================
 * SMART DAIRY ERP — Vehicle Management
 * ============================================================
 * Full CRUD: Add, Edit, Service Log, and Delete vehicles
 * ============================================================
 */

let vehiclesData = [];

/** Initialize vehicles page */
window.initVehicles = function() {
  console.log('Vehicles page initialized');
  loadVehicles();
  loadBranchesForVehicleForm();
};

/** Load vehicles from API */
async function loadVehicles() {
  const tbody = document.querySelector('#vehicles-table tbody');
  if (!tbody) return;

  // Show skeleton while loading
  tbody.innerHTML = Array(3).fill('<tr><td colspan="10"><div class="skeleton skeleton-table-row"></div></td></tr>').join('');

  try {
    const result = await API.getVehicles();
    vehiclesData = result.vehicles || result.data || [];
  } catch (err) {
    console.warn('Failed to load vehicles from API:', err);
    vehiclesData = [];
  }

  renderVehiclesTable();
}

/** Render vehicles table */
function renderVehiclesTable() {
  const tbody = document.querySelector('#vehicles-table tbody');
  if (!tbody) return;

  if (!vehiclesData.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="10" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
          <i data-lucide="truck" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
          No vehicles found. Click <strong>"Add Vehicle"</strong> to register one.
        </td>
      </tr>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  const typeLabels = { TANKER: 'Tanker', PICKUP: 'Pickup', MINI_VAN: 'Mini Van' };
  const statusDots = { ACTIVE: 'online', MAINTENANCE: 'blocked', INACTIVE: 'offline' };
  const gpsDots = { ACTIVE: 'online', NOT_TRACKED: 'offline', OFFLINE: 'blocked' };

  const today = new Date();

  tbody.innerHTML = vehiclesData.map((v, idx) => {
    let insuranceTag = '-';
    if (v.insuranceNo) {
      const expired = v.insuranceExpiry && new Date(v.insuranceExpiry) < today;
      insuranceTag = `<div>${v.insuranceNo}</div><div style="font-size:10px;color:var(--ink-muted);">${v.insuranceExpiry ? formatDate(v.insuranceExpiry) : ''} ${expired ? '<span class="tag tag-red" style="font-size:9px;">EXPIRED</span>' : ''}</div>`;
    }
    let serviceTag = '-';
    if (v.nextServiceDate) {
      const dueSoon = (new Date(v.nextServiceDate) - today) < 30 * 24 * 3600 * 1000 && new Date(v.nextServiceDate) >= today;
      const overdue = new Date(v.nextServiceDate) < today;
      serviceTag = `${formatDate(v.nextServiceDate)} ${overdue ? '<span class="tag tag-red" style="font-size:9px;">OVERDUE</span>' : dueSoon ? '<span class="tag tag-gold" style="font-size:9px;">SOON</span>' : ''}`;
    }
    return `
    <tr>
      <td><span class="font-mono" style="font-size:var(--text-sm);font-weight:600;">${v.vehicleNumber || '-'}</span></td>
      <td><span class="tag tag-neutral">${typeLabels[v.type] || v.type || '-'}</span></td>
      <td>${v.driverName || '-'}</td>
      <td>${v.capacity ? Number(v.capacity).toLocaleString() + ' L' : '-'}</td>
      <td>${v.branchName || '-'}</td>
      <td>${insuranceTag}</td>
      <td>${serviceTag}</td>
      <td><span class="status-dot ${gpsDots[v.gpsStatus] || 'offline'}"></span> ${v.gpsStatus ? v.gpsStatus.replace(/_/g, ' ') : 'Not Tracked'}</td>
      <td>
        <span class="status-dot ${statusDots[v.status] || 'offline'}"></span>
        ${v.status ? v.status.charAt(0) + v.status.slice(1).toLowerCase() : 'Unknown'}
      </td>
      <td>
        <div class="table-actions">
          <button class="btn btn-icon btn-sm btn-ghost" title="Edit Vehicle" onclick="editVehicle(${idx})">
            <i data-lucide="edit-3" style="width:16px;height:16px;"></i>
          </button>
          <button class="btn btn-icon btn-sm btn-ghost" title="Delete Vehicle" onclick="deleteVehicle(${idx})" style="color:var(--danger);">
            <i data-lucide="trash-2" style="width:16px;height:16px;"></i>
          </button>
        </div>
      </td>
    </tr>
  `;}).join('');

  if (window.lucide) lucide.createIcons();
}

/** Format date string to readable format */
function formatDate(dateStr) {
  if (!dateStr) return '-';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch (e) {
    return dateStr;
  }
}

/** Load branches into vehicle form dropdown */
async function loadBranchesForVehicleForm() {
  const select = document.getElementById('vehicle-branch');
  if (!select) return;
  try {
    const result = await API.getBranches();
    const branches = result.branches || result.data || result || [];
    select.innerHTML = '<option value="">Select Branch</option>';
    branches.forEach(b => {
      const opt = document.createElement('option');
      opt.value = b.id;
      opt.textContent = b.name;
      select.appendChild(opt);
    });
  } catch (err) {
    console.warn('Could not load branches for vehicle form');
  }
}

/** Open modal to add a new vehicle */
function openVehicleModal() {
  document.getElementById('vehicle-modal-title').textContent = 'Add Vehicle';
  document.getElementById('vehicle-id').value = '';
  document.getElementById('vehicle-form').reset();
  document.getElementById('vehicle-status').value = 'ACTIVE';
  document.getElementById('vehicle-modal').classList.add('open');
  if (window.lucide) setTimeout(() => lucide.createIcons(), 50);
}

/** Open modal to edit an existing vehicle */
function editVehicle(idx) {
  const v = vehiclesData[idx];
  if (!v) return;

  document.getElementById('vehicle-modal-title').textContent = 'Edit Vehicle';
  document.getElementById('vehicle-id').value = v.id || '';
  document.getElementById('vehicle-number').value = v.vehicleNumber || '';
  document.getElementById('vehicle-type').value = v.type || '';
  document.getElementById('vehicle-driver').value = v.driverName || '';
  document.getElementById('vehicle-capacity').value = v.capacity || '';
  document.getElementById('vehicle-branch').value = v.branchId || '';
  document.getElementById('vehicle-status').value = v.status || 'ACTIVE';
  document.getElementById('vehicle-insurance-no').value = v.insuranceNo || '';
  document.getElementById('vehicle-insurance-expiry').value = v.insuranceExpiry ? v.insuranceExpiry.slice(0, 10) : '';
  document.getElementById('vehicle-last-service').value = v.lastServiceDate ? v.lastServiceDate.slice(0, 10) : '';
  document.getElementById('vehicle-next-service').value = v.nextServiceDate ? v.nextServiceDate.slice(0, 10) : '';
  document.getElementById('vehicle-gps').value = v.gpsStatus || 'NOT_TRACKED';
  document.getElementById('vehicle-modal').classList.add('open');
  if (window.lucide) setTimeout(() => lucide.createIcons(), 50);
}

/** Close vehicle modal */
function closeVehicleModal() {
  document.getElementById('vehicle-modal').classList.remove('open');
}

/** Save vehicle (create or update) */
async function saveVehicle() {
  const id = document.getElementById('vehicle-id').value;
  const number = document.getElementById('vehicle-number').value.trim();
  const type = document.getElementById('vehicle-type').value;
  const driver = document.getElementById('vehicle-driver').value.trim();
  const capacity = document.getElementById('vehicle-capacity').value;
  const branchId = document.getElementById('vehicle-branch').value;
  const status = document.getElementById('vehicle-status').value;

  if (!number) {
    Modal.toast({ title: 'Validation Error', message: 'Vehicle number is required', type: 'error' });
    return;
  }
  if (!type) {
    Modal.toast({ title: 'Validation Error', message: 'Vehicle type is required', type: 'error' });
    return;
  }

  const payload = {
    vehicleNumber: number,
    type: type,
    driverName: driver || null,
    capacity: capacity ? parseFloat(capacity) : null,
    branchId: branchId ? parseInt(branchId) : null,
    status: status,
    insuranceNo: document.getElementById('vehicle-insurance-no').value.trim() || null,
    insuranceExpiry: document.getElementById('vehicle-insurance-expiry').value || null,
    lastServiceDate: document.getElementById('vehicle-last-service').value || null,
    nextServiceDate: document.getElementById('vehicle-next-service').value || null,
    gpsStatus: document.getElementById('vehicle-gps').value,
  };

  try {
    if (id) {
      await API.updateVehicle(id, payload);
    } else {
      await API.createVehicle(payload);
    }
    closeVehicleModal();
    loadVehicles();
    Modal.toast({ title: id ? 'Updated' : 'Created', message: `Vehicle ${id ? 'updated' : 'added'} successfully`, type: 'success' });
  } catch (err) {
    console.warn('API failed, falling back to local update:', err);
    if (id) {
      const idx = vehiclesData.findIndex(v => v.id == id);
      if (idx >= 0) {
        vehiclesData[idx] = { ...vehiclesData[idx], ...payload, id: parseInt(id) };
      }
    } else {
      payload.id = Date.now();
      payload.branchName = document.getElementById('vehicle-branch').selectedOptions[0]?.text || '';
      vehiclesData.push(payload);
    }
    closeVehicleModal();
    renderVehiclesTable();
    Modal.toast({ title: id ? 'Updated' : 'Created', message: `Vehicle ${id ? 'updated' : 'added'} successfully`, type: 'success' });
  }
}

/** Delete a vehicle with confirmation */
function deleteVehicle(idx) {
  const v = vehiclesData[idx];
  if (!v) return;

  Modal.confirm({
    title: 'Delete Vehicle',
    message: `Are you sure you want to delete vehicle <strong>${v.vehicleNumber}</strong>?`,
    confirmText: 'Delete',
    variant: 'danger',
    onConfirm: async () => {
      try {
        if (v.id) {
          await API.deleteVehicle(v.id);
        }
        vehiclesData.splice(idx, 1);
        renderVehiclesTable();
        Modal.toast({ title: 'Deleted', message: 'Vehicle deleted successfully', type: 'success' });
      } catch (err) {
        console.warn('API delete failed, falling back to local delete:', err);
        vehiclesData.splice(idx, 1);
        renderVehiclesTable();
        Modal.toast({ title: 'Deleted', message: 'Vehicle deleted successfully', type: 'success' });
      }
    }
  });
}
