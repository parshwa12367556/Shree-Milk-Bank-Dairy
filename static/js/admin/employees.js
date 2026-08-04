/**
 * ============================================================
 * SMART DAIRY ERP — Employees Management
 * ============================================================
 * Full CRUD via API with modal form
 * ============================================================
 */

window.initEmployees = function() {
  console.log('Employees page initialized');
  loadEmployeeData();
};

async function loadEmployeeData() {
  loadEmployeeStats();
  await loadEmployeesTable();
}

function loadEmployeeStats() {
  const container = document.getElementById('employee-stats');
  if (!container) return;
  container.innerHTML = `
    <div class="kpi-card kpi-green"><div class="kpi-icon"><i data-lucide="users"></i></div><div class="kpi-label">Total Employees</div><div class="kpi-value">0</div></div>
    <div class="kpi-card kpi-blue"><div class="kpi-icon"><i data-lucide="user-check"></i></div><div class="kpi-label">Active</div><div class="kpi-value">0</div></div>
    <div class="kpi-card kpi-purple"><div class="kpi-icon"><i data-lucide="briefcase"></i></div><div class="kpi-label">Roles</div><div class="kpi-value">0</div></div>
    <div class="kpi-card kpi-gold"><div class="kpi-icon"><i data-lucide="indian-rupee"></i></div><div class="kpi-label">Avg Salary</div><div class="kpi-value">₹0</div></div>
  `;
  if (window.lucide) lucide.createIcons();
}

async function loadEmployeesTable() {
  const tbody = document.querySelector('#employees-table tbody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="8"><div class="skeleton skeleton-table-row"></div></td></tr>';

  try {
    const result = await API.getEmployees();
    const employees = result.employees || result.data || [];
    renderEmployeesTable(employees);
  } catch (err) {
    console.warn('Failed to load employees:', err);
    renderEmployeesTable([]);
  }
}

function renderEmployeesTable(employees) {
  const tbody = document.querySelector('#employees-table tbody');
  if (!tbody) return;

  if (!employees.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
          <i data-lucide="briefcase" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
          No employees registered yet. Click <strong>"Add Employee"</strong> to add one.
        </td>
      </tr>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  const statusDots = { ACTIVE: 'online', INACTIVE: 'offline' };
  tbody.innerHTML = employees.map((e, idx) => `
    <tr>
      <td><span class="font-mono" style="font-weight:600;">${e.code || '-'}</span></td>
      <td>${e.name || '-'}</td>
      <td><span class="tag tag-neutral">${e.role || '-'}</span></td>
      <td>${e.branchName || '-'}</td>
      <td>${e.mobile || '-'}</td>
      <td><span class="status-dot ${statusDots[e.status] || 'offline'}"></span> ${e.status || '-'}</td>
      <td>${e.joinedAt ? fmtDate(e.joinedAt, true) : '-'}</td>
      <td>
        <div class="table-actions">
          <button class="btn btn-icon btn-sm btn-ghost" title="Edit"><i data-lucide="edit-3" style="width:16px;height:16px;"></i></button>
          <button class="btn btn-icon btn-sm btn-ghost" title="Delete" style="color:var(--danger);"><i data-lucide="trash-2" style="width:16px;height:16px;"></i></button>
        </div>
      </td>
    </tr>
  `).join('');
  if (window.lucide) lucide.createIcons();
}

// Modal functions
function openEmployeeModal() {
  document.getElementById('employee-modal-title').textContent = 'Add Employee';
  document.getElementById('employee-form').reset();
  document.getElementById('employee-status').value = 'ACTIVE';
  Modal.open('employee-modal');
  if (window.lucide) setTimeout(() => lucide.createIcons(), 50);
}

function closeEmployeeModal() {
  Modal.close('employee-modal');
}

async function saveEmployee() {
  const code = document.getElementById('emp-code').value.trim();
  const name = document.getElementById('emp-name').value.trim();
  const role = document.getElementById('emp-role').value;
  const branchId = document.getElementById('emp-branch').value;
  const mobile = document.getElementById('emp-mobile').value.trim();

  if (!code || !name) {
    Modal.toast({ title: 'Validation Error', message: 'Employee code and name are required', type: 'error' });
    return;
  }

  try {
    await API.createEmployee({
      code, name, role,
      branch_id: branchId ? parseInt(branchId) : null,
      mobile: mobile || null,
      status: 'ACTIVE',
    });
    closeEmployeeModal();
    await loadEmployeesTable();
    Modal.toast({ title: 'Success', message: `Employee ${name} added successfully`, type: 'success' });
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message || 'Failed to add employee', type: 'error' });
  }
}

window.openEmployeeModal = openEmployeeModal;
window.closeEmployeeModal = closeEmployeeModal;
window.saveEmployee = saveEmployee;
