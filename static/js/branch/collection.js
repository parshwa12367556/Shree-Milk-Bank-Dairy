/**
 * ============================================================
 * SMART DAIRY ERP — Milk Collection Desk
 * ============================================================
 * Connected to backend API for saving collections
 * ============================================================
 */

window.initCollection = function() {
  console.log('Collection page initialized');
  autoDetectShift();
  loadCollectionsTable();
  loadCollectionQueue();
  loadTodaySummary();
  initQuantityPills();
  initFarmerSearch();
  initCollectionForm();
};

function autoDetectShift() {
  const hour = new Date().getHours();
  const shift = hour < 14 ? 'Morning' : 'Evening';
  const tag = document.querySelector('.panel-header .tag');
  if (tag) tag.textContent = `Shift: ${shift}`;
}

function loadCollectionsTable() {
  const tbody = document.querySelector('#collections-table tbody');
  if (!tbody) return;
  tbody.innerHTML = `
    <tr>
      <td colspan="10" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
        <i data-lucide="milk" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
        No collections recorded today. Use the collection form above to add entries.
      </td>
    </tr>
  `;
  if (window.lucide) lucide.createIcons();
}

function loadCollectionQueue() {
  const container = document.getElementById('collection-queue');
  if (!container) return;
  container.innerHTML = `
    <div class="empty-state" style="padding:var(--space-4);">
      <p style="font-size:var(--text-sm);color:var(--ink-muted);">No farmers in queue. Search or select a farmer above.</p>
    </div>
  `;
}

let _selectedCollectionFarmer = null;

function selectFarmer(farmer) {
  if (!farmer) return;
  _selectedCollectionFarmer = farmer;
  const initials = getInitials(farmer.name);
  document.getElementById('current-farmer').innerHTML = `
    <div class="card" style="padding:var(--space-4);">
      <div class="flex items-center gap-3">
        <div class="farmer-avatar-lg" style="width:48px;height:48px;border-radius:var(--radius-full);background:linear-gradient(135deg,var(--forest-light),var(--forest));display:flex;align-items:center;justify-content:center;font-size:1.25rem;color:white;font-weight:700;flex-shrink:0;">${initials}</div>
        <div>
          <div style="font-weight:600;">${farmer.name}</div>
          <div style="font-size:var(--text-xs);color:var(--ink-muted);">${farmer.farmerCode || farmer.code || ''}</div>
        </div>
      </div>
    </div>
  `;
}

function _currentShift() {
  const hour = new Date().getHours();
  return hour < 14 ? 'MORNING' : 'EVENING';
}

async function loadTodaySummary() {
  const container = document.getElementById('today-summary');
  const today = new Date().toISOString().slice(0, 10);
  let rows = [];
  let count = 0, totalQty = 0, totalAmount = 0, rateSum = 0, rateN = 0;
  try {
    const result = await API.getCollections({ date: today, per_page: 10000 });
    rows = result.collections || [];
    count = rows.length;
    rows.forEach(c => {
      totalQty += c.quantity || 0;
      totalAmount += c.amount || 0;
      if (c.ratePerLiter) { rateSum += c.ratePerLiter; rateN++; }
    });
  } catch (err) { /* API failure — show empty state below */ }
  if (container) {
    container.innerHTML = `
      <div class="today-summary">
        <div class="summary-item"><div class="summary-label">Collections</div><div class="summary-value">${count}</div></div>
        <div class="summary-item"><div class="summary-label">Total Qty</div><div class="summary-value">${fmtNum(totalQty)} L</div></div>
        <div class="summary-item"><div class="summary-label">Total Amount</div><div class="summary-value">${fmtINR(totalAmount)}</div></div>
        <div class="summary-item"><div class="summary-label">Avg Rate</div><div class="summary-value">${rateN ? fmtINR(rateSum / rateN) : '—'}</div></div>
      </div>
    `;
  }
  // Shift KPI cards (morning_collection.html / evening_collection.html)
  const shift = _currentShift();
  const shiftRows = rows.filter(c => (c.shift || '').toUpperCase() === shift);
  const cardIds = {
    'MORNING': { count: 'col-morning-count', qty: 'col-morning-qty', avg: 'col-morning-avg', pending: 'col-morning-pending' },
    'EVENING': { count: 'col-evening-count', qty: 'col-evening-qty', avg: 'col-evening-avg', pending: 'col-evening-pending' },
  }[shift] || {};
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.querySelector('.kpi-value').textContent = val;
  };
  if (cardIds.count) {
    set(cardIds.count, shiftRows.length);
    set(cardIds.qty, fmtNum(shiftRows.reduce((s, c) => s + (c.quantity || 0), 0)) + ' L');
    const fats = shiftRows.filter(c => c.fat);
    set(cardIds.avg, fats.length ? (fats.reduce((s, c) => s + (c.fat || 0), 0) / fats.length).toFixed(1) + '%' : '—');
    set(cardIds.pending, '—');  // pending-farmer count needs attendance data — kept as empty state
  }
}

function initQuantityPills() {
  document.querySelectorAll('.qty-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.qty-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const qtyInput = document.getElementById('collection-qty');
      if (qtyInput) qtyInput.value = pill.dataset.value;
      calculateCollectionAmount();
    });
  });
}

function calculateCollectionAmount() {
  const qty = parseFloat(document.getElementById('collection-qty')?.value) || 0;
  const fat = parseFloat(document.getElementById('collection-fat')?.value) || 0;
  const snf = parseFloat(document.getElementById('collection-snf')?.value) || 0;
  const fatRate = 5.0;
  const snfRate = 2.5;
  const result = computePrice(fat, snf, qty, fatRate, snfRate);
  document.getElementById('rate-per-liter').textContent = fmtINR(result.ratePerLiter);
  document.getElementById('total-amount').textContent = fmtINR(result.amount);
  document.getElementById('calc-fat').textContent = `${fat.toFixed(1)}%`;
  document.getElementById('calc-snf').textContent = `${snf.toFixed(1)}%`;
  document.getElementById('calc-qty').textContent = `${qty.toFixed(1)} L`;
}

function initFarmerSearch() {
  const searchInput = document.getElementById('farmer-search-input');
  if (!searchInput) return;

  searchInput.addEventListener('input', debounce(async (e) => {
    const query = e.target.value.trim();
    const container = document.getElementById('farmer-suggestions');
    if (query.length < 1) { container.innerHTML = ''; return; }

    try {
      const result = await API.getFarmers({ q: query, per_page: 5 });
      const farmers = result.farmers || result.data || [];
      if (farmers.length) {
        container.innerHTML = farmers.map(f => `
          <div class="card" style="margin-top:var(--space-1);padding:var(--space-2);cursor:pointer;" onclick="selectFarmer(${JSON.stringify(f).replace(/"/g, '&quot;')})">
            <div style="font-weight:500;">${f.name}</div>
            <div style="font-size:var(--text-xs);color:var(--ink-muted);">${f.farmerCode || f.code} · ${f.village}</div>
          </div>
        `).join('');
      } else {
        container.innerHTML = `<div class="card" style="margin-top:var(--space-2);padding:var(--space-3);text-align:center;color:var(--ink-muted);font-size:var(--text-sm);">No farmers found matching "${query}"</div>`;
      }
    } catch (err) {
      container.innerHTML = `<div class="card" style="margin-top:var(--space-2);padding:var(--space-3);text-align:center;color:var(--ink-muted);font-size:var(--text-sm);">Search error. Try again.</div>`;
    }
  }, 300));
}

function initCollectionForm() {
  const saveBtn = document.getElementById('save-collection');
  if (!saveBtn) return;

  saveBtn.addEventListener('click', async () => {
    const qty = parseFloat(document.getElementById('collection-qty')?.value) || 0;
    if (qty === 0) {
      Modal.toast({ title: 'Validation Error', message: 'Please enter quantity', type: 'error' });
      return;
    }
    if (!_selectedCollectionFarmer) {
      Modal.toast({ title: 'Validation Error', message: 'Please select a farmer first', type: 'error' });
      return;
    }

    const fat = parseFloat(document.getElementById('collection-fat')?.value) || 0;
    const snf = parseFloat(document.getElementById('collection-snf')?.value) || 0;

    try {
      await API.createCollection({
        farmer_id: _selectedCollectionFarmer.id,
        quantity: qty,
        fat: fat,
        snf: snf,
        shift: getCurrentShift(),
        branch_id: _selectedCollectionFarmer.branchId || 1,
        milk_type: _selectedCollectionFarmer.milkType || 'COW',
      });
      Modal.toast({ title: 'Success', message: `Collection of ${qty}L recorded for ${_selectedCollectionFarmer.name}`, type: 'success' });
      _selectedCollectionFarmer = null;
      document.getElementById('collection-qty').value = '';
      document.getElementById('collection-fat').value = '';
      document.getElementById('collection-snf').value = '';
      loadCollectionsTable();
      loadTodaySummary();
    } catch (err) {
      Modal.toast({ title: 'Error', message: err.message || 'Failed to save collection', type: 'error' });
    }
  });
}
