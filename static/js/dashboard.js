/**
 * ============================================================
 * SMART DAIRY ERP — Dashboard
 * ============================================================
 * All widgets load real data from GET /api/dashboard
 * ============================================================
 */

/** Format a number with Indian digit grouping */
function fmtNum(v) {
  if (v === null || v === undefined) return '—';
  return Number(v).toLocaleString('en-IN', { maximumFractionDigits: 1 });
}

window.initDashboard = function() {
  console.log('Dashboard initialized');
  initTrendSegments();
  // Keep charts in sync with the (persistent) 14/30-day segment selection
  loadDashboard(getActiveDays());
};

/** Reload every widget with fresh data */
function refreshDashboard() {
  const skeleton = '<div class="skeleton skeleton-text"></div><div class="skeleton skeleton-text short"></div>';
  document.querySelectorAll('.kpi-card').forEach(el => { el.innerHTML = skeleton; });
  ['today-entries', 'pending-payments', 'new-farmers', 'top-farmers'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = '<div class="skeleton skeleton-text"></div>';
  });
  loadDashboard(getActiveDays());
  Modal.toast({ title: 'Refreshed', message: 'Dashboard data refreshed', type: 'success' });
}

/** Read the currently active 14/30-day segment */
function getActiveDays() {
  const activeBtn = document.querySelector('.segmented-btn.active');
  return activeBtn && activeBtn.textContent.includes('30') ? 30 : 14;
}

/** Fetch dashboard data once and render every widget */
async function loadDashboard(days) {
  try {
    const result = await API.getDashboard({ days: days || 14 });
    const data = result || {};
    renderKPIs(data.kpis || {});
    renderCollectionProgress(data.collectionProgress || {});
    renderCharts(data.collectionTrend || {}, data.revenueTrend || {});
    renderRevenueGrowth(data.revenueGrowth);
    renderBranchPerformance(data.branches || []);
    renderTodayEntries(data.todayEntries || [], data.todayEntryCount || 0);
    renderPendingPayments(data.pendingPayments || [], (data.kpis || {}).pendingPayments || 0);
    renderNewFarmers(data.newFarmers || []);
    renderTopFarmers(data.topFarmers || []);
    renderSystemHealth(data.health || {});
  } catch (err) {
    console.warn('Failed to load dashboard:', err);
    renderKPIs({});
    renderCollectionProgress({});
    renderTodayEntries([], 0);
    renderPendingPayments([], 0);
    renderNewFarmers([]);
    renderTopFarmers([]);
  }
}

/** ── KPI cards ── */
function renderKPIs(k) {
  const items = [
    { id: 'kpi-collection', value: k.todayCollection != null ? fmtNum(k.todayCollection) + ' L' : '—', label: 'Today Collection', icon: 'milk' },
    { id: 'kpi-revenue', value: k.revenue != null ? fmtINR(k.revenue) : '—', label: 'Revenue', icon: 'indian-rupee' },
    { id: 'kpi-cow', value: k.todayCow != null ? fmtNum(k.todayCow) + ' L' : '—', label: "Today Cow Milk", icon: 'milk' },
    { id: 'kpi-buffalo', value: k.todayBuffalo != null ? fmtNum(k.todayBuffalo) + ' L' : '—', label: 'Today Buffalo Milk', icon: 'beaker' },
    { id: 'kpi-mixed', value: k.todayMixed != null ? fmtNum(k.todayMixed) + ' L' : '—', label: 'Today Mixed Milk', icon: 'droplets' },
    { id: 'kpi-farmers', value: k.activeFarmers != null ? String(k.activeFarmers) : '—', label: 'Active Farmers', icon: 'users' },
    { id: 'kpi-fat', value: k.avgFat != null ? String(k.avgFat) + '%' : '—', label: 'Avg Fat', icon: 'droplets' },
    { id: 'kpi-snf', value: k.avgSnf != null ? String(k.avgSnf) + '%' : '—', label: 'Avg SNF', icon: 'beaker' },
    { id: 'kpi-pending', value: k.pendingPayments != null ? fmtINR(k.pendingPayments) : '—', label: 'Pending Payments', icon: 'clock' },
    { id: 'kpi-rejected', value: k.rejectedToday != null ? String(k.rejectedToday) : '—', label: 'Rejected Today', icon: 'x-circle' },
    { id: 'kpi-efficiency', value: k.efficiency != null ? fmtNum(k.efficiency) + '%' : '—', label: 'Efficiency', icon: 'gauge' },
  ];

  const colors = ['green', 'gold', 'blue', 'purple', 'teal', 'blue', 'green', 'purple', 'amber', 'red', 'cyan'];
  items.forEach((item, i) => {
    const el = document.getElementById(item.id);
    if (!el) return;
    el.className = `kpi-card kpi-${colors[i]}`;
    el.innerHTML = `
      <div class="kpi-icon"><i data-lucide="${item.icon}" style="width:20px;height:20px;"></i></div>
      <div class="kpi-label">${item.label}</div>
      <div class="kpi-value">${item.value}</div>
    `;
  });
  if (window.lucide) lucide.createIcons();
}

/** ── Collection progress gauge ── */
function renderCollectionProgress(p) {
  const pctEl = document.getElementById('collection-progress-pct');
  const circle = document.getElementById('collection-progress-circle');
  const targetEl = document.getElementById('collection-progress-target');
  const collectedEl = document.getElementById('collection-progress-collected');
  const remainingEl = document.getElementById('collection-progress-remaining');

  if (!p.target || p.target <= 0) {
    // No target available yet (no recent collections) - show placeholders
    if (pctEl) pctEl.textContent = '—';
    if (targetEl) targetEl.textContent = '—';
    if (collectedEl) collectedEl.textContent = '—';
    if (remainingEl) remainingEl.textContent = '—';
    if (circle) circle.style.strokeDashoffset = 326.73;
    return;
  }

  const pct = Math.min(p.percent, 100);
  if (pctEl) pctEl.textContent = fmtNum(pct) + '%';
  if (circle) circle.style.strokeDashoffset = 326.73 * (1 - pct / 100);
  if (targetEl) targetEl.textContent = fmtNum(p.target) + ' L';
  if (collectedEl) collectedEl.textContent = fmtNum(p.collected) + ' L';
  if (remainingEl) remainingEl.textContent = fmtNum(p.remaining) + ' L';
}

/** ── Collection trend + revenue charts ── */
function renderCharts(collectionTrend, revenueTrend) {
  if (!window.Chart) return;
  const labels = collectionTrend.labels || [];

  AppCharts.lineChart('chart-collection-trend', labels, [{
    label: 'Collection (L)',
    data: collectionTrend.values || [],
    borderColor: '#2e7d32',
    backgroundColor: 'rgba(46,125,50,0.12)',
    fill: true,
    tension: 0.3,
  }], { plugins: { legend: { display: false } } });

  AppCharts.lineChart('chart-revenue', labels, [{
    label: 'Revenue (₹)',
    data: revenueTrend.values || [],
    borderColor: '#d4a043',
    backgroundColor: 'rgba(212,160,67,0.12)',
    fill: true,
    tension: 0.3,
  }], { plugins: { legend: { display: false } } });
}

/** ── Revenue growth tag ── */
function renderRevenueGrowth(growth) {
  const tag = document.getElementById('revenue-growth-tag');
  if (!tag) return;
  if (growth === null || growth === undefined) {
    tag.textContent = '—';
    tag.className = 'tag tag-neutral';
    return;
  }
  const up = growth >= 0;
  tag.textContent = (up ? '+' : '') + fmtNum(growth) + '%';
  tag.className = up ? 'tag tag-green' : 'tag tag-red';
}

/** ── Branch performance table ── */
function renderBranchPerformance(branches) {
  const tbody = document.querySelector('#branch-performance-table tbody');
  if (!tbody) return;

  if (!branches.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="padding:var(--space-4);color:var(--ink-muted);font-size:var(--text-sm);">No branch data</td></tr>';
    return;
  }

  tbody.innerHTML = branches.map(b => `
    <tr>
      <td><span class="font-mono">${b.code || '-'}</span></td>
      <td>${b.name || '-'}</td>
      <td>${b.farmerCount || 0}</td>
      <td>${b.collection != null ? fmtNum(b.collection) + ' L' : '—'}</td>
      <td>${b.revenue != null ? fmtINR(b.revenue) : '—'}</td>
      <td>${b.efficiency != null ? '₹' + fmtNum(b.efficiency) + '/L' : '—'}</td>
    </tr>
  `).join('');
}

/** ── Today's entries ── */
function renderTodayEntries(entries, count) {
  const container = document.getElementById('today-entries');
  const countTag = document.getElementById('today-entries-count');
  if (!container) return;

  if (countTag) countTag.textContent = `${count} entries`;

  if (!entries.length) {
    container.innerHTML = `
      <div class="empty-state" style="padding:var(--space-4);text-align:center;">
        <p style="font-size:var(--text-sm);color:var(--ink-muted);">No entries recorded today.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = entries.map(e => `
    <div style="display:flex;justify-content:space-between;align-items:center;padding:var(--space-2) 0;border-bottom:1px solid var(--line);font-size:var(--text-sm);">
      <div>
        <div style="font-weight:600;">${e.farmerName}</div>
        <div style="color:var(--ink-muted);font-size:var(--text-xs);">${e.receiptNo || ''} · ${e.shift || ''} ${e.time || ''}</div>
      </div>
      <div style="font-weight:700;">${e.quantity != null ? fmtNum(e.quantity) + ' L' : '—'}</div>
    </div>
  `).join('');
}

/** ── Pending payments ── */
function renderPendingPayments(payments, total) {
  const container = document.getElementById('pending-payments');
  const totalTag = document.getElementById('pending-payments-total');
  if (!container) return;

  if (totalTag) totalTag.textContent = total != null ? fmtINR(total) : '—';

  if (!payments.length) {
    container.innerHTML = `
      <div class="empty-state" style="padding:var(--space-4);text-align:center;">
        <p style="font-size:var(--text-sm);color:var(--ink-muted);">No pending payments.</p>
      </div>
    `;
    return;
  }

  const badges = { PENDING: 'tag-gold', APPROVED: 'tag-blue', PAID: 'tag-green' };
  container.innerHTML = payments.map(p => `
    <div style="display:flex;justify-content:space-between;align-items:center;padding:var(--space-2) 0;border-bottom:1px solid var(--line);font-size:var(--text-sm);">
      <div>
        <div style="font-weight:600;">${p.farmerName}</div>
        <div style="color:var(--ink-muted);font-size:var(--text-xs);">${p.payCode || ''}</div>
      </div>
      <div style="text-align:right;">
        <div style="font-weight:700;">${p.amount != null ? fmtINR(p.amount) : '—'}</div>
        <span class="tag ${badges[p.status] || 'tag-neutral'}" style="font-size:10px;">${p.status || ''}</span>
      </div>
    </div>
  `).join('');
}

/** ── New farmers ── */
function renderNewFarmers(farmers) {
  const container = document.getElementById('new-farmers');
  if (!container) return;

  if (!farmers.length) {
    container.innerHTML = `
      <div class="empty-state" style="padding:var(--space-4);text-align:center;">
        <p style="font-size:var(--text-sm);color:var(--ink-muted);">No new farmers this week.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = farmers.map(f => `
    <div style="display:flex;justify-content:space-between;align-items:center;padding:var(--space-2) 0;border-bottom:1px solid var(--line);font-size:var(--text-sm);">
      <div>
        <div style="font-weight:600;">${f.name}</div>
        <div style="color:var(--ink-muted);font-size:var(--text-xs);">${f.farmerCode || ''} · joined ${f.joinedAt ? fmtDate(f.joinedAt, true) : '—'}</div>
      </div>
    </div>
  `).join('');
}

/** ── Top farmers ── */
function renderTopFarmers(farmers) {
  const container = document.getElementById('top-farmers');
  if (!container) return;

  if (!farmers.length) {
    container.innerHTML = `
      <div class="empty-state" style="padding:var(--space-4);text-align:center;">
        <p style="font-size:var(--text-sm);color:var(--ink-muted);">No data for this month.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = farmers.map((f, i) => `
    <div style="display:flex;justify-content:space-between;align-items:center;padding:var(--space-2) 0;border-bottom:1px solid var(--line);font-size:var(--text-sm);">
      <div style="display:flex;align-items:center;gap:var(--space-2);">
        <span class="tag tag-gold" style="min-width:24px;text-align:center;">${i + 1}</span>
        <div>
          <div style="font-weight:600;">${f.name}</div>
          <div style="color:var(--ink-muted);font-size:var(--text-xs);">${f.farmerCode || ''}</div>
        </div>
      </div>
      <div style="text-align:right;">
        <div style="font-weight:700;">${f.quantity != null ? fmtNum(f.quantity) + ' L' : '—'}</div>
        <div style="color:var(--ink-muted);font-size:var(--text-xs);">${f.amount != null ? fmtINR(f.amount) : '—'}</div>
      </div>
    </div>
  `).join('');
}

/** ── System health ── */
function renderSystemHealth(health) {
  const container = document.getElementById('system-health');
  if (!container) return;

  const items = [
    { label: 'Database', value: health.database || '—' },
    { label: 'API Server', value: health.api || '—' },
    { label: 'Auth Service', value: health.auth || '—' },
    { label: 'Storage', value: health.storage || '—' },
  ];

  container.innerHTML = items.map(item => `
    <div class="health-item">
      <span class="status-dot ${String(item.value).toLowerCase() === 'connected' || String(item.value).toLowerCase() === 'running' || String(item.value).toLowerCase() === 'active' || String(item.value).toLowerCase() === 'ok' ? 'online' : 'offline'}"></span>
      ${item.label} <span class="health-status">${item.value}</span>
    </div>
  `).join('');
}

/** ── Trend segmented control (14 / 30 days) ── */
function initTrendSegments() {
  const btns = document.querySelectorAll('.segmented-btn');
  btns.forEach(btn => {
    if (btn.hasAttribute('data-listener')) return;
    btn.setAttribute('data-listener', 'true');
    btn.addEventListener('click', () => {
      btns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const days = btn.textContent.includes('30') ? 30 : 14;
      loadTrends(days);
    });
  });
}

/** Reload only the trend charts for the selected period */
async function loadTrends(days) {
  if (!window.Chart) return;
  try {
    const result = await API.getDashboard({ days });
    const data = result || {};
    renderCharts(data.collectionTrend || {}, data.revenueTrend || {});
    renderRevenueGrowth(data.revenueGrowth);
  } catch (err) {
    console.warn('Failed to load trends:', err);
  }
}

window.refreshDashboard = refreshDashboard;
