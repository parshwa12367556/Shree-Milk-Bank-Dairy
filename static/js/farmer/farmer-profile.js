/**
 * ============================================================
 * SMART DAIRY ERP — Farmer Profile & Passbook (admin view)
 * Renders the real farmer record fetched via API.getFarmer()
 * (stored on App.selectedFarmerData by the farmers list).
 * ============================================================
 */

window.initFarmerProfile = function() {
  const data = App.selectedFarmerData || {};
  const farmer = data.farmer || App.selectedFarmer || null;
  if (!farmer) {
    renderEmptyProfile();
    return;
  }
  renderFarmerHeader(farmer);
  renderStats(data.stats || {});
  renderProfilePassbook(data.recentCollections || []);
  initProfileActions(farmer);
};

/**
 * Show empty profile state when no farmer is selected
 */
function renderEmptyProfile() {
  const nameEl = document.getElementById('profile-name');
  const subEl = document.getElementById('profile-subtitle');
  const avatarEl = document.getElementById('profile-avatar-text');

  if (avatarEl) avatarEl.textContent = '?';
  if (nameEl) nameEl.textContent = 'No Farmer Selected';
  if (subEl) subEl.textContent = 'Select a farmer from the Farmers page';
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
  if (subEl) subEl.textContent = `${farmer.code || ''} · ${farmer.fatherName || '—'}`;
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
 * Render real collection stats into the farmer-stats-grid cards
 */
function renderStats(stats) {
  const cards = document.querySelectorAll('.farmer-stats-grid .kpi-card');
  if (!cards.length) return;
  const data = [
    { value: `${fmtNum(stats.totalQuantity, 2)} L`, label: 'Total Delivered' },
    { value: fmtINR(stats.totalAmount), label: 'Total Earnings' },
    { value: stats.avgFat != null ? `${stats.avgFat}%` : '—', label: 'Avg Fat' },
    { value: stats.avgSnf != null ? `${stats.avgSnf}%` : '—', label: 'Avg SNF' },
    { value: `${stats.collectionCount || 0}`, label: 'Collections' },
    { value: fmtINR(stats.paidAmount), label: 'Paid' },
  ];
  cards.forEach((el, i) => {
    if (!data[i]) return;
    el.className = `kpi-card kpi-${['green', 'gold', 'purple', 'teal', 'blue', 'green'][i]}`;
    el.innerHTML = `
      <div class="kpi-value">${data[i].value}</div>
      <div class="kpi-label">${data[i].label}</div>
    `;
  });
}

/**
 * Render real recent collections into the profile passbook table
 */
function renderProfilePassbook(entries) {
  const tbody = document.getElementById('profile-passbook-body');
  if (!tbody) return;
  if (!entries.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
          <i data-lucide="book-open" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
          No collection records yet.
        </td>
      </tr>`;
  } else {
    tbody.innerHTML = entries.map(c => `
      <tr>
        <td>${fmtDate(c.date)}</td>
        <td><span class="font-mono" style="font-size:var(--text-xs);">${c.receiptNo || '—'}</span></td>
        <td>${c.shift === 'MORNING' ? 'Morning' : 'Evening'}</td>
        <td>${fmtNum(c.quantity, 2)} L</td>
        <td>${c.fat != null ? c.fat + '%' : '—'}</td>
        <td>${c.snf != null ? c.snf + '%' : '—'}</td>
        <td>${c.ratePerLiter != null ? '₹' + fmtNum(c.ratePerLiter, 2) : '—'}</td>
        <td style="font-weight:600;">${fmtINR(c.amount)}</td>
      </tr>`).join('');
  }
  if (window.lucide) lucide.createIcons();
}

/**
 * Passbook page init (admin view of the selected farmer)
 */
window.initFarmerPassbook = function() {
  const data = App.selectedFarmerData || {};
  const farmer = data.farmer || App.selectedFarmer || null;
  const headerEl = document.getElementById('passbook-header-text');
  if (headerEl) {
    const name = farmer ? farmer.name : 'Farmer Name';
    const code = farmer ? farmer.code : 'Code';
    headerEl.innerHTML = `Passbook for <strong>${name} (${code})</strong>`;
  }

  renderAdminPassbook(data.recentCollections || []);
  initPassbookActions(farmer);
};

/**
 * Render real entries into the admin passbook page table
 */
function renderAdminPassbook(entries) {
  const tbody = document.getElementById('passbook-body');
  if (!tbody) return;
  if (!entries.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
          <i data-lucide="book-open" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
          No collection records yet.
        </td>
      </tr>`;
  } else {
    tbody.innerHTML = entries.map(c => `
      <tr>
        <td>${fmtDate(c.date)}</td>
        <td><span class="font-mono" style="font-size:var(--text-xs);">${c.receiptNo || '—'}</span></td>
        <td>${c.shift === 'MORNING' ? 'Morning' : 'Evening'}</td>
        <td>${fmtNum(c.quantity, 2)} L</td>
        <td>${c.fat != null ? c.fat + '%' : '—'}</td>
        <td>${c.snf != null ? c.snf + '%' : '—'}</td>
        <td>${c.ratePerLiter != null ? '₹' + fmtNum(c.ratePerLiter, 2) : '—'}</td>
        <td style="font-weight:600;">${fmtINR(c.amount)}</td>
      </tr>`).join('');
  }
  if (window.lucide) lucide.createIcons();
}

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
      const tbody = document.getElementById('passbook-body');
      const rows = tbody ? tbody.querySelectorAll('tr').length : 0;
      if (!rows || (rows === 1 && tbody.textContent.includes('No collection'))) {
        Modal.toast({ title: 'PDF Export', message: 'No data to export.', type: 'info' });
      } else {
        Modal.toast({ title: 'PDF Export', message: 'Use Print → Save as PDF to export this page.', type: 'info' });
      }
    });
  }
}
