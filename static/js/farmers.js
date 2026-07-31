/**
 * ============================================================
 * SMART DAIRY ERP — Farmers List Page
 * ============================================================
 */

window.initFarmers = function() {
  console.log('Farmers page initialized');
  
  loadFarmerStats();
  loadFarmersTable();
  initFarmerFilters();
  initFarmerSearch();
};

/**
 * Load farmer stats - zero values
 */
function loadFarmerStats() {
  const container = document.getElementById('farmer-stats');
  if (!container) return;

  container.innerHTML = `
    <div class="kpi-card kpi-green"><div class="kpi-value" style="font-size:var(--text-xl);">0</div><div class="kpi-label" style="font-size:10px;">Total Farmers</div></div>
    <div class="kpi-card kpi-blue"><div class="kpi-value" style="font-size:var(--text-xl);">0</div><div class="kpi-label" style="font-size:10px;">Cow Farmers</div></div>
    <div class="kpi-card kpi-purple"><div class="kpi-value" style="font-size:var(--text-xl);">0</div><div class="kpi-label" style="font-size:10px;">Buffalo Farmers</div></div>
    <div class="kpi-card kpi-teal"><div class="kpi-value" style="font-size:var(--text-xl);">0</div><div class="kpi-label" style="font-size:10px;">Mixed Farmers</div></div>
    <div class="kpi-card kpi-green"><div class="kpi-value" style="font-size:var(--text-xl);">0</div><div class="kpi-label" style="font-size:10px;">Active</div></div>
    <div class="kpi-card kpi-amber"><div class="kpi-value" style="font-size:var(--text-xl);">0</div><div class="kpi-label" style="font-size:10px;">Inactive</div></div>
    <div class="kpi-card kpi-red"><div class="kpi-value" style="font-size:var(--text-xl);">0</div><div class="kpi-label" style="font-size:10px;">Blocked</div></div>
  `;
}

/**
 * Load farmers table - empty
 */
function loadFarmersTable() {
  const tbody = document.querySelector('#farmers-table tbody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="12" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
        <i data-lucide="users" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
        No farmers registered yet. Click "Register Farmer" to add one.
      </td>
    </tr>
  `;
  if (window.lucide) lucide.createIcons();
}

/**
 * Initialize filters
 */
// Initialize Help page
window.initHelp = function() {
  console.log('Help page initialized');
};

// Initialize Profile page
window.initProfile = function() {
  console.log('Profile page initialized');
};

function initFarmerFilters() {
  const filterSelect = document.getElementById('farmer-type-filter');
  if (filterSelect) {
    filterSelect.addEventListener('change', () => {
      // Will filter from API data when connected
    });
  }

  const statusFilter = document.getElementById('farmer-status-filter');
  if (statusFilter) {
    statusFilter.addEventListener('change', () => {
      // Will filter from API data when connected
    });
  }
}

/**
 * Initialize farmer search - filters the farmers table
 */
function initFarmerSearch() {
  const searchInput = document.querySelector('#page-farmers .toolbar-left .search-bar input');
  if (!searchInput) return;

  searchInput.addEventListener('input', debounce((e) => {
    const query = e.target.value.trim();
    Table.filter('farmers-table', query);
  }, 300));
}
