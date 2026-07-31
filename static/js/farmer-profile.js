/**
 * ============================================================
 * SMART DAIRY ERP — Farmer Profile & Passbook
 * ============================================================
 */

window.initFarmerProfile = function() {
  console.log('Farmer profile initialized');
  
  const farmer = App.selectedFarmer;
  if (!farmer) {
    console.warn('No farmer selected');
    loadEmptyProfile();
    return;
  }
  
  renderFarmerHeader(farmer);
  loadEmptyStats();
  loadEmptyPassbook();
  initProfileActions(farmer);
};

/**
 * Show empty profile state when no farmer is selected
 */
function loadEmptyProfile() {
  const nameEl = document.getElementById('profile-name');
  const subEl = document.getElementById('profile-subtitle');
  const avatarEl = document.getElementById('profile-avatar-text');
  
  if (avatarEl) avatarEl.textContent = '?';
  if (nameEl) nameEl.textContent = 'No Farmer Selected';
  if (subEl) subEl.textContent = 'Select a farmer from the Farmers page';
  
  loadEmptyStats();
  loadEmptyPassbook();
}

/**
 * Initialize Edit & Print button handlers
 */
function initProfileActions(farmer) {
  const editBtn = document.querySelector('[data-action="edit-farmer"]');
  if (editBtn && !editBtn.hasAttribute('data-listener')) {
    editBtn.setAttribute('data-listener', 'true');
    editBtn.addEventListener('click', () => {
      if (farmer) {
        App.editFarmer = farmer;
      }
      Router.navigate('farmer-form');
    });
  }

  const printBtn = document.querySelector('[data-action="print-profile"]');
  if (printBtn && !printBtn.hasAttribute('data-listener')) {
    printBtn.setAttribute('data-listener', 'true');
    printBtn.addEventListener('click', () => {
      const pageContainer = document.getElementById('page-farmer-profile');
      if (pageContainer) {
        printElement(pageContainer);
      }
    });
  }
}

/**
 * Render the farmer profile header with dynamic data
 */
function renderFarmerHeader(farmer) {
  if (!farmer) return;
  
  const initials = getInitials(farmer.name);
  const avatarEl = document.getElementById('profile-avatar-text');
  const nameEl = document.getElementById('profile-name');
  const subEl = document.getElementById('profile-subtitle');
  const phoneEl = document.getElementById('profile-phone');
  const locEl = document.getElementById('profile-location');
  const typeEl = document.getElementById('profile-milk-type');
  const joinEl = document.getElementById('profile-joined');
  const statusEl = document.getElementById('profile-status-tag');
  
  if (avatarEl) avatarEl.textContent = initials;
  if (nameEl) nameEl.textContent = farmer.name;
  if (subEl) subEl.textContent = `${farmer.code || ''}`;
  if (phoneEl) phoneEl.innerHTML = `<i data-lucide="phone" style="width:14px;height:14px;"></i> ${farmer.mobile || '-'}`;
  if (locEl) locEl.innerHTML = `<i data-lucide="map-pin" style="width:14px;height:14px;"></i> ${farmer.village || '-'}`;
  if (typeEl) typeEl.innerHTML = `<i data-lucide="milk" style="width:14px;height:14px;"></i> ${fmtMilkType(farmer.type) || '-'}`;
  if (joinEl) joinEl.innerHTML = `<i data-lucide="calendar" style="width:14px;height:14px;"></i> Joined: ${farmer.joined || '-'}`;
  if (statusEl) {
    const statusClass = statusBadge(farmer.status);
    statusEl.innerHTML = `<span class="tag ${statusClass}">${farmer.status || 'Unknown'}</span>`;
  }
  
  if (window.lucide) lucide.createIcons();
}

/**
 * Load empty stats
 */
function loadEmptyStats() {
  const stats = document.querySelectorAll('.farmer-stats-grid .kpi-card');
  const data = [
    { value: '0 L', label: 'Total Delivered' },
    { value: '₹0', label: 'Total Earnings' },
    { value: '—', label: 'Avg Fat' },
    { value: '—', label: 'Avg SNF' },
    { value: '0', label: 'Collections' },
    { value: '—', label: 'Quality Score' },
  ];
  
  stats.forEach((el, i) => {
    if (data[i]) {
      el.className = `kpi-card kpi-${['green','gold','purple','teal','blue','green'][i]}`;
      el.innerHTML = `
        <div class="kpi-value">${data[i].value}</div>
        <div class="kpi-label">${data[i].label}</div>
      `;
    }
  });
}

/**
 * Load empty passbook
 */
function loadEmptyPassbook() {
  const tbody = document.querySelector('#passbook-table tbody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="8" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
        <i data-lucide="book-open" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
        No collection records yet.
      </td>
    </tr>
  `;
  if (window.lucide) lucide.createIcons();
}

/**
 * Passbook page init
 */
window.initFarmerPassbook = function() {
  console.log('Farmer passbook initialized');
  
  const farmer = App.selectedFarmer;
  const headerEl = document.getElementById('passbook-header-text');
  if (headerEl) {
    const name = farmer ? farmer.name : 'Farmer Name';
    const code = farmer ? farmer.code : 'Code';
    headerEl.innerHTML = `Passbook for <strong>${name} (${code})</strong>`;
  }
  
  loadEmptyPassbook();
  initPassbookActions(farmer);
};

/**
 * Initialize passbook page action buttons
 */
function initPassbookActions(farmer) {
  const printBtn = document.querySelector('[data-action="print-passbook"]');
  if (printBtn && !printBtn.hasAttribute('data-listener')) {
    printBtn.setAttribute('data-listener', 'true');
    printBtn.addEventListener('click', () => {
      const pageContainer = document.getElementById('page-farmer-passbook');
      if (pageContainer) {
        printElement(pageContainer);
      }
    });
  }

  const pdfBtn = document.querySelector('[data-action="export-pdf"]');
  if (pdfBtn && !pdfBtn.hasAttribute('data-listener')) {
    pdfBtn.setAttribute('data-listener', 'true');
    pdfBtn.addEventListener('click', () => {
      Modal.toast({ title: 'PDF Export', message: 'No data to export.', type: 'info' });
    });
  }
}
