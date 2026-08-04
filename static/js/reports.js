/**
 * ============================================================
 * SMART DAIRY ERP — Reports
 * Real report generation via API with date/branch filters,
 * rendered summary cards, and CSV export.
 * ============================================================
 */

window.initReports = function() {
  console.log('Reports page initialized');
  initReportTypes();
  initReportActions();
  loadReportBranches();
};

let _selectedReportType = 'collection';

function initReportTypes() {
  document.querySelectorAll('.report-type-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('.report-type-card').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      _selectedReportType = card.dataset.report;
      showEmptyReport();
    });
  });
}

async function loadReportBranches() {
  const select = document.getElementById('report-branch');
  if (!select) return;
  try {
    const result = await API.getBranches();
    const branches = result.branches || [];
    select.innerHTML = '<option value="">All Branches</option>' +
      branches.map(b => `<option value="${b.id}">${b.code} — ${b.name}</option>`).join('');
  } catch (err) { /* ignore */ }
}

function getReportParams() {
  const params = { type: _selectedReportType };
  const from = document.getElementById('report-from')?.value;
  const to = document.getElementById('report-to')?.value;
  const branch = document.getElementById('report-branch')?.value;
  if (from) params.from = from;
  if (to) params.to = to;
  if (branch) params.branchId = branch;
  return params;
}

function showEmptyReport() {
  const container = document.getElementById('report-content');
  if (!container) return;
  container.innerHTML = `
    <div class="empty-state" style="padding:var(--space-12);">
      <div class="empty-icon"><i data-lucide="file-text" style="width:64px;height:64px;opacity:0.2;"></i></div>
      <h3>No Report Data</h3>
      <p style="color:var(--ink-muted);">Select a report type and click <strong>"Generate"</strong>.</p>
    </div>
  `;
  if (window.lucide) lucide.createIcons();
}

async function generateReport() {
  const container = document.getElementById('report-content');
  if (!container) return;

  container.innerHTML = '<div class="text-center" style="padding:var(--space-8);color:var(--ink-muted);"><i data-lucide="loader-2" style="width:32px;height:32px;animation:spin 1s linear infinite;"></i><br>Generating report...</div>';
  if (window.lucide) lucide.createIcons();

  try {
    const data = await API.getReports(getReportParams());
    renderReport(data);
  } catch (err) {
    container.innerHTML = `
      <div class="empty-state" style="padding:var(--space-12);">
        <div class="empty-icon"><i data-lucide="alert-circle" style="width:48px;height:48px;opacity:0.3;"></i></div>
        <h3>Report Not Available</h3>
        <p style="color:var(--ink-muted);">${err.message || 'No data available.'}</p>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
  }
}

/** Render a report summary nicely */
function renderReport(data) {
  const container = document.getElementById('report-content');
  if (!container) return;

  const summary = data.summary || {};
  const period = data.period || {};
  const type = data.type || _selectedReportType;

  const titleMap = {
    collection: 'Milk Collection', payment: 'Farmer Payments', quality: 'Quality Control',
    rejection: 'Milk Rejections', branch: 'Branch Performance', expense: 'Operational Expenses',
    pnl: 'Profit & Loss',
  };

  let body = '';

  if (type === 'collection') {
    body = summaryGrid([
      ['Total Quantity', fmtNum(summary.totalQuantity ?? 0) + ' L', 'kpi-green'],
      ['Total Amount', fmtINR(summary.totalAmount ?? 0), 'kpi-gold'],
      ['Morning', fmtNum(summary.morningQuantity ?? 0) + ' L', 'kpi-blue'],
      ['Evening', fmtNum(summary.eveningQuantity ?? 0) + ' L', 'kpi-purple'],
      ['Collections', summary.collectionCount ?? 0, 'kpi-teal'],
      ['Avg Fat', summary.avgFat ?? '—', 'kpi-cyan'],
      ['Avg SNF', summary.avgSnf ?? '—', 'kpi-green'],
    ]);
  } else if (type === 'payment') {
    body = summaryGrid([
      ['Total Paid', fmtINR(summary.totalPaid ?? 0), 'kpi-green'],
      ['Total Pending', fmtINR(summary.totalPending ?? 0), 'kpi-gold'],
      ['Payments', summary.paymentCount ?? 0, 'kpi-blue'],
    ]);
  } else if (type === 'quality') {
    body = summaryGrid([
      ['Total Tests', summary.totalTests ?? 0, 'kpi-blue'],
      ['Passed', summary.passed ?? 0, 'kpi-green'],
      ['Borderline', summary.borderline ?? 0, 'kpi-gold'],
      ['Failed', summary.failed ?? 0, 'kpi-red'],
      ['Pass Rate', (summary.passRate ?? 0) + '%', 'kpi-teal'],
    ]);
  } else if (type === 'rejection') {
    body = summaryGrid([
      ['Rejected Quantity', fmtNum(summary.totalQuantity ?? 0) + ' L', 'kpi-red'],
      ['Events', summary.totalEvents ?? 0, 'kpi-gold'],
    ]);
    if (summary.byReason && Object.keys(summary.byReason).length) {
      body += `
        <div class="card" style="margin-top:var(--space-4);">
          <div class="card-header"><h5 class="section-title">Rejected by Reason</h5></div>
          <div class="card-body">
            ${Object.entries(summary.byReason).map(([k, v]) => `
              <div style="display:flex;justify-content:space-between;padding:var(--space-2) 0;border-bottom:1px solid var(--line);font-size:var(--text-sm);">
                <span>${k.replace(/_/g, ' ')}</span><strong>${fmtNum(v)} L</strong>
              </div>`).join('')}
          </div>
        </div>`;
    }
  } else if (type === 'branch') {
    const branches = data.branches || [];
    body = `
      <div class="table-responsive">
        <table class="table-premium" id="report-branch-table" style="width:100%;">
          <thead><tr><th>Code</th><th>Branch</th><th>Farmers</th><th>Quantity</th><th>Amount</th><th>Collections</th></tr></thead>
          <tbody>${branches.map(b => `
            <tr>
              <td><span class="font-mono" style="font-weight:600;">${b.branchCode || ''}</span></td>
              <td>${b.branchName || ''}</td>
              <td>${b.farmerCount ?? 0}</td>
              <td>${fmtNum(b.totalQuantity ?? 0)} L</td>
              <td>${fmtINR(b.totalAmount ?? 0)}</td>
              <td>${b.collectionCount ?? 0}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>`;
  } else if (type === 'expense') {
    body = summaryGrid([
      ['Total Expenses', fmtINR(summary.totalAmount ?? 0), 'kpi-red'],
      ['Entries', summary.expenseCount ?? 0, 'kpi-gold'],
    ]);
    if (summary.byCategory && Object.keys(summary.byCategory).length) {
      body += `
        <div class="card" style="margin-top:var(--space-4);">
          <div class="card-header"><h5 class="section-title">Expenses by Category</h5></div>
          <div class="card-body">
            ${Object.entries(summary.byCategory).map(([k, v]) => `
              <div style="display:flex;justify-content:space-between;padding:var(--space-2) 0;border-bottom:1px solid var(--line);font-size:var(--text-sm);">
                <span>${k.replace(/_/g, ' ')}</span><strong>${fmtINR(v)}</strong>
              </div>`).join('')}
          </div>
        </div>`;
    }
  } else if (type === 'pnl') {
    const net = summary.net ?? 0;
    body = summaryGrid([
      ['Revenue (Milk)', fmtINR(summary.revenue ?? 0), 'kpi-green'],
      ['Total Costs', fmtINR(summary.totalCosts ?? 0), 'kpi-red'],
      ['Expenses', fmtINR(summary.expenses ?? 0), 'kpi-gold'],
      ['Procurement Spend', fmtINR(summary.procurementSpend ?? 0), 'kpi-purple'],
      ['Net ' + (net >= 0 ? 'Profit' : 'Loss'), fmtINR(Math.abs(net)), net >= 0 ? 'kpi-green' : 'kpi-red'],
      ['Total Quantity', fmtNum(summary.totalQuantity ?? 0) + ' L', 'kpi-blue'],
    ]);
  } else {
    body = `<pre style="background:var(--bg-canvas);padding:var(--space-4);border-radius:var(--radius-md);overflow:auto;max-height:400px;font-size:var(--text-sm);">${JSON.stringify(data, null, 2)}</pre>`;
  }

  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h5 class="section-title">${titleMap[type] || type} Report</h5>
        <span class="tag tag-neutral">${period.from || ''} → ${period.to || ''}</span>
      </div>
      <div class="card-body">${body}</div>
    </div>
  `;
}

function summaryGrid(cards) {
  return `
    <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit,minmax(180px,1fr));">
      ${cards.map(c => `
        <div class="kpi-card ${c[2] || 'kpi-blue'}">
          <div class="kpi-value" style="font-size:var(--text-lg);">${c[1]}</div>
          <div class="kpi-label" style="font-size:11px;">${c[0]}</div>
        </div>`).join('')}
    </div>`;
}

function initReportActions() {
  const csvBtn = document.querySelector('[data-action="export-report-csv"]');
  if (csvBtn) {
    csvBtn.addEventListener('click', async () => {
      try {
        await API.exportReport(getReportParams());
        Modal.toast({ title: 'Export', message: 'Report CSV downloaded', type: 'success' });
      } catch (err) {
        Modal.toast({ title: 'Export', message: err.message || 'Export failed', type: 'error' });
      }
    });
  }

  const printBtn = document.querySelector('[data-action="print-report"]');
  if (printBtn) {
    printBtn.addEventListener('click', () => {
      const content = document.getElementById('report-content');
      if (!content || content.querySelector('.empty-state')) {
        Modal.toast({ title: 'Print', message: 'Generate a report first.', type: 'info' });
        return;
      }
      printElement(content);
    });
  }
}

window.generateReport = generateReport;
