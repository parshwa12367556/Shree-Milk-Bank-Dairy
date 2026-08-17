/**
 * ============================================================
 * SMART DAIRY ERP — Milk Collection Desk
 * ============================================================
 * Connected to backend API for saving collections
 * ============================================================
 */

let _liveRates = { COW: { fat: 5.0, snf: 2.5 }, BUFFALO: { fat: 5.0, snf: 2.5 } };

window.initCollection = function() {
  console.log('Collection page initialized');
  autoDetectShift();
  loadCollectionsTable();
  loadCollectionQueue();
  loadTodaySummary();
  initQuantityPills();
  initCollectionFarmerSearch();
  initCollectionForm();
  initQrScanner();
  loadLiveRates();
};

/** Fetch the ACTIVE rate card from the backend so the live price preview is real. */
async function loadLiveRates() {
  try {
    const result = await API.getPricing();
    const current = (result && (result.current || result.currentRates)) || {};
    const pick = (r) => ({
      fat: parseFloat((r && (r.fatRate ?? r.ratePerFat)) || 0) || 0,
      snf: parseFloat((r && (r.snfRate ?? r.ratePerSnf)) || 0) || 0,
    });
    if (current.COW) _liveRates.COW = pick(current.COW);
    if (current.BUFFALO) _liveRates.BUFFALO = pick(current.BUFFALO);
  } catch (err) {
    console.warn('Could not load live rates — using fallback values:', err);
  }
}

function _rateFor(farmer) {
  const type = (farmer && farmer.milkType) || 'COW';
  return _liveRates[type] || _liveRates.COW;
}

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
  const rates = _rateFor(_selectedCollectionFarmer);
  const result = computePrice(fat, snf, qty, rates.fat, rates.snf);
  document.getElementById('rate-per-liter').textContent = fmtINR(result.ratePerLiter);
  document.getElementById('total-amount').textContent = fmtINR(result.amount);
  document.getElementById('calc-fat').textContent = `${fat.toFixed(1)}%`;
  document.getElementById('calc-snf').textContent = `${snf.toFixed(1)}%`;
  document.getElementById('calc-qty').textContent = `${qty.toFixed(1)} L`;
}

function initCollectionFarmerSearch() {
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
        container.innerHTML = `<div class="card" style="margin-top:var(--space-2);padding:var(--space-3);text-align:center;color:var(--ink-muted);font-size:var(--text-sm);">No farmers found matching "${escapeHtml(query)}"</div>`;
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
    const num = (id) => { const v = document.getElementById(id)?.value; return v !== undefined && v !== '' ? parseFloat(v) : undefined; };

    try {
      await API.createCollection({
        farmerId: _selectedCollectionFarmer.id,
        quantity: qty,
        fat: fat,
        snf: snf,
        shift: _currentShift(),
        clr: num('collection-clr'),
        temperature: num('collection-temperature'),
        density: num('collection-density'),
        water: num('collection-water'),
        protein: num('collection-protein'),
        lactose: num('collection-lactose'),
        remarks: document.querySelector('#page-collection textarea')?.value || '',
        // Idempotency key makes the save safe to retry on network hiccups.
        idempotencyKey: `ui-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
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

// ══════════════════════════════════════════════════════════════════
// QR SCANNER (camera) — identifies a farmer from a signed QR payload
// ══════════════════════════════════════════════════════════════════
let _qrStream = null;
let _qrRaf = null;
let _qrLastResult = '';

function loadJsQR() {
  return new Promise((resolve) => {
    if (window.jsQR) return resolve(true);
    const s = document.createElement('script');
    s.src = 'https://unpkg.com/jsqr@1.4.0/dist/jsQR.js';
    s.onload = () => resolve(true);
    s.onerror = () => resolve(false);
    document.head.appendChild(s);
  });
}

function initQrScanner() {
  const btn = document.getElementById('btn-open-scanner');
  if (btn && !btn.hasAttribute('data-listener')) {
    btn.setAttribute('data-listener', 'true');
    btn.addEventListener('click', openQrScanner);
  }
}

async function openQrScanner() {
  if (!document.getElementById('modal-qr-scanner')) {
    Modal.toast({ title: 'QR Scanner', message: 'Scanner is not available on this page.', type: 'error' });
    return;
  }
  const status = document.getElementById('qr-scanner-status');
  if (status) status.textContent = 'Loading scanner library…';

  const loaded = await loadJsQR();
  if (!loaded) {
    if (status) status.textContent = 'Scanner library could not be loaded — check connectivity.';
    Modal.toast({ title: 'QR Scanner', message: 'The scanner library could not be loaded. Use code/name search instead.', type: 'error' });
    return;
  }

  Modal.open('modal-qr-scanner');
  if (status) status.textContent = 'Requesting camera access…';

  try {
    _qrStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' },
      audio: false,
    });
    const video = document.getElementById('qr-video');
    video.srcObject = _qrStream;
    await video.play();
    if (status) status.textContent = 'Scanning — point at the farmer QR card.';
    _qrLastResult = '';
    _qrScanLoop();
  } catch (err) {
    stopQrScanner();
    if (status) status.textContent = 'Camera unavailable or permission denied.';
    Modal.toast({
      title: 'Camera Error',
      message: 'Could not start the camera. Grant camera permission or use code/name search instead.',
      type: 'error',
    });
  }
}

function _qrScanLoop() {
  const video = document.getElementById('qr-video');
  if (!video || !video.videoWidth) {
    _qrRaf = requestAnimationFrame(_qrScanLoop);
    return;
  }
  try {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const code = window.jsQR(imageData.data, imageData.width, imageData.height, {
      inversionAttempts: 'dontInvert',
    });
    if (code && code.data && code.data !== _qrLastResult) {
      _qrLastResult = code.data;
      _handleScannedQr(code.data);
      return; // stop the loop — the handler either selects a farmer or the user re-opens
    }
  } catch (err) {
    /* a single bad frame must not kill the scanner */
  }
  _qrRaf = requestAnimationFrame(_qrScanLoop);
}

async function _handleScannedQr(payload) {
  stopQrScanner();
  try {
    const result = await API.qrLookup(payload);
    const farmer = result.farmer;
    if (!farmer) throw new Error('Farmer not found for this QR code.');
    if (['INACTIVE', 'BLOCKED', 'REJECTED'].includes((farmer.status || '').toUpperCase())) {
      Modal.toast({
        title: 'Farmer Not Collectable',
        message: `${farmer.name} (${farmer.farmerCode}) is ${farmer.status}. Contact Head Office.`,
        type: 'warning',
      });
      return;
    }
    selectFarmer(farmer);
    Modal.toast({
      title: 'Farmer Selected',
      message: `${farmer.name} (${farmer.farmerCode}) loaded from QR.`,
      type: 'success',
    });
  } catch (err) {
    Modal.toast({ title: 'Invalid QR', message: err.message || 'Could not resolve this QR code.', type: 'error' });
  }
}

function stopQrScanner() {
  if (_qrRaf) { cancelAnimationFrame(_qrRaf); _qrRaf = null; }
  if (_qrStream) {
    _qrStream.getTracks().forEach((t) => t.stop());
    _qrStream = null;
  }
  const video = document.getElementById('qr-video');
  if (video) video.srcObject = null;
  _qrLastResult = '';
  if (document.getElementById('modal-qr-scanner')) Modal.close('modal-qr-scanner');
}

window.openQrScanner = openQrScanner;
window.stopQrScanner = stopQrScanner;
