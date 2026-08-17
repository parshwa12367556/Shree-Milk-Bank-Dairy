/**
 * ============================================================
 * SMART DAIRY ERP — Farmers List Page
 * Live data via API with search, filters, verification workflow,
 * CSV export.
 * ============================================================
 */

let _farmerPage = 1;
let _farmerQ = '';
let _farmerStatus = 'all';
let _farmerType = 'all';
let _farmerTimer = null;

window.initFarmers = function() {
  console.log('Farmers page initialized');
  loadFarmerStats();
  loadFarmersTable();
  initFarmerFilters();
  initFarmersSearch();
};

function _farmersIsGlobalRole() {
  const user = window.Auth ? Auth.getUser() : null;
  return !!user && ['ADMIN'].includes(user.role);
}

/** Load farmer stats from API */
async function loadFarmerStats() {
  const container = document.getElementById('farmer-stats');
  if (!container) return;

  container.innerHTML = Array(7).fill('<div class="kpi-card"><div class="skeleton skeleton-text"></div><div class="skeleton skeleton-text short"></div></div>').join('');

  try {
    const s = await API.getFarmerStats();
    const cards = [
      { cls: 'kpi-green', value: s.total || 0, label: 'Total Farmers' },
      { cls: 'kpi-gold', value: s.pendingVerification || 0, label: 'Pending Verification' },
      { cls: 'kpi-blue', value: s.cow || 0, label: 'Cow Farmers' },
      { cls: 'kpi-purple', value: s.buffalo || 0, label: 'Buffalo Farmers' },
      { cls: 'kpi-teal', value: s.mixed || 0, label: 'Mixed Farmers' },
      { cls: 'kpi-cyan', value: s.inactive || 0, label: 'Inactive' },
      { cls: 'kpi-red', value: s.blocked || 0, label: 'Blocked' },
    ];
    container.innerHTML = cards.map(c => `
      <div class="kpi-card ${c.cls}">
        <div class="kpi-value" style="font-size:var(--text-xl);">${c.value}</div>
        <div class="kpi-label" style="font-size:10px;">${c.label}</div>
      </div>
    `).join('');
  } catch (err) {
    console.warn('Failed to load farmer stats:', err);
  }
}

/** Load farmers from API and render table */
async function loadFarmersTable() {
  const tbody = document.querySelector('#farmers-table tbody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="12"><div class="skeleton skeleton-table-row"></div></td></tr>';

  const params = { page: _farmerPage, per_page: 10 };
  if (_farmerQ) params.q = _farmerQ;
  if (_farmerStatus !== 'all') params.status = _farmerStatus;
  if (_farmerType !== 'all') params.milk_type = _farmerType;

  try {
    const result = await API.getFarmers(params);
    renderFarmersTable(result.farmers || [], result.total, result.pages || 1);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="12" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">${err.message || 'Failed to load farmers'}</td></tr>`;
  }
}

const _statusBadge = (s) => {
  const map = {
    ACTIVE: 'tag-green', PENDING_VERIFICATION: 'tag-gold',
    INACTIVE: 'tag-neutral', BLOCKED: 'tag-red',
  };
  return `<span class="tag ${map[s] || 'tag-neutral'}">${String(s || '').replace(/_/g, ' ')}</span>`;
};

function renderFarmersTable(farmers, total, pages) {
  const tbody = document.querySelector('#farmers-table tbody');
  if (!tbody) return;

  const info = document.querySelector('#page-farmers .table-info');
  if (info) info.textContent = `Showing ${farmers.length} of ${total} farmers`;

  if (!farmers.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="12" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
          <i data-lucide="users" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
          No farmers found.
        </td>
      </tr>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  const isGlobal = _farmersIsGlobalRole();
  const milkIcons = { COW: '🐄', BUFFALO: '🐃', MIXED: '🥛' };

  tbody.innerHTML = farmers.map(f => {
    const animals = (f.cowCount || 0) + (f.buffaloCount || 0);
    const actions = [];
    actions.push(`<button class="btn btn-icon btn-sm btn-ghost" title="View Profile" onclick="openFarmerProfile('${f.farmerCode}')"><i data-lucide="eye" style="width:16px;height:16px;"></i></button>`);
    if (f.status === 'PENDING_VERIFICATION' && isGlobal) {
      actions.push(`<button class="btn btn-sm btn-primary" title="Verify Farmer" onclick="verifyFarmer('${f.farmerCode}')"><i data-lucide="badge-check" style="width:16px;height:16px;"></i> Verify</button>`);
    }
    actions.push(`<button class="btn btn-icon btn-sm btn-ghost" title="Edit" onclick="editFarmerProfile('${f.farmerCode}')"><i data-lucide="edit-3" style="width:16px;height:16px;"></i></button>`);

    return `
      <tr>
        <td class="checkbox-cell"><input type="checkbox"></td>
        <td><span class="font-mono" style="font-weight:600;">${f.farmerCode || ''}</span></td>
        <td>${f.name || '-'}</td>
        <td>${f.mobile || '-'}</td>
        <td>${f.village || '-'}</td>
        <td>${milkIcons[f.milkType] || ''} ${f.milkType || '-'}</td>
        <td>${animals}</td>
        <td>${f.branchName || '-'}</td>
        <td>${_statusBadge(f.status)}</td>
        <td>${f.joinedAt ? fmtDate(f.joinedAt, true) : '-'}</td>
        <td><div class="table-actions">${actions.join('')}</div></td>
      </tr>
    `;
  }).join('');

  if (window.lucide) lucide.createIcons();
  updateFarmerPagination(pages);
}

function updateFarmerPagination(pages) {
  const pagination = document.querySelector('#page-farmers .pagination');
  if (!pagination) return;
  const buttons = pagination.querySelectorAll('.page-btn');
  buttons.forEach(btn => btn.remove());
  const prev = document.createElement('button');
  prev.className = 'page-btn prev-btn';
  prev.innerHTML = '<i data-lucide="chevron-left" style="width:16px;height:16px;"></i>';
  prev.disabled = _farmerPage <= 1;
  prev.onclick = () => { _farmerPage = Math.max(1, _farmerPage - 1); loadFarmersTable(); };
  pagination.appendChild(prev);
  for (let p = 1; p <= Math.min(pages, 8); p++) {
    const b = document.createElement('button');
    b.className = 'page-btn' + (p === _farmerPage ? ' active' : '');
    b.textContent = p;
    b.onclick = () => { _farmerPage = p; loadFarmersTable(); };
    pagination.appendChild(b);
  }
  const next = document.createElement('button');
  next.className = 'page-btn next-btn';
  next.innerHTML = '<i data-lucide="chevron-right" style="width:16px;height:16px;"></i>';
  next.disabled = _farmerPage >= pages;
  next.onclick = () => { _farmerPage = Math.min(pages, _farmerPage + 1); loadFarmersTable(); };
  pagination.appendChild(next);
  if (window.lucide) lucide.createIcons();
}

/** Open farmer profile page */
function openFarmerProfile(code) {
  API.getFarmer(code)
    .then(result => {
      App.selectedFarmer = result.farmer || result;
      App.selectedFarmerData = result;
      Router.navigate('farmer-profile');
    })
    .catch(err => Modal.toast({ title: 'Error', message: err.message || 'Could not load farmer', type: 'error' }));
}

/** Open farmer edit form (any authenticated user may edit) */
function editFarmerProfile(code) {
  API.getFarmer(code)
    .then(result => {
      App.editFarmer = result.farmer || result;
      Router.navigate('farmer-form');
    })
    .catch(err => Modal.toast({ title: 'Error', message: err.message || 'Could not load farmer', type: 'error' }));
}

/** Verify a pending farmer (Head Office) */
function verifyFarmer(code) {
  Modal.confirm({
    title: 'Verify Farmer',
    message: `Approve <strong>${code}</strong>? Bank & KYC details will be confirmed and the farmer will become eligible for payments.`,
    confirmText: 'Verify & Activate',
    variant: 'info',
    onConfirm: async () => {
      try {
        const result = await API.verifyFarmer(code);
        Modal.toast({ title: 'Verified', message: result.message || 'Farmer activated', type: 'success' });
        loadFarmerStats();
        loadFarmersTable();
      } catch (err) {
        Modal.toast({ title: 'Error', message: err.message || 'Verification failed', type: 'error' });
      }
    }
  });
}

/** Export farmers as CSV via API */
async function exportFarmersCSV() {
  try {
    await API.exportFarmers();
    Modal.toast({ title: 'Export', message: 'Farmer data CSV downloaded', type: 'success' });
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message || 'Export failed', type: 'error' });
  }
}

function initFarmerFilters() {
  const typeFilter = document.getElementById('farmer-type-filter');
  if (typeFilter) {
    typeFilter.addEventListener('change', () => {
      _farmerType = typeFilter.value;
      _farmerPage = 1;
      loadFarmersTable();
    });
  }

  const statusFilter = document.getElementById('farmer-status-filter');
  if (statusFilter) {
    statusFilter.addEventListener('change', () => {
      _farmerStatus = statusFilter.value;
      _farmerPage = 1;
      loadFarmersTable();
    });
  }
}

/** Search farmers via API (debounced) */
function initFarmersSearch() {
  const searchInput = document.getElementById('farmer-search-input');
  if (!searchInput) return;

  searchInput.addEventListener('input', debounce((e) => {
    _farmerQ = e.target.value.trim();
    _farmerPage = 1;
    loadFarmersTable();
  }, 350));
}

window.openFarmerProfile = openFarmerProfile;
window.editFarmerProfile = editFarmerProfile;
window.verifyFarmer = verifyFarmer;
window.exportFarmersCSV = exportFarmersCSV;
