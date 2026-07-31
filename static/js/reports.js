/**
 * ============================================================
 * SMART DAIRY ERP — Reports
 * ============================================================
 * Full report generation via API
 * ============================================================
 */

window.initReports = function() {
  console.log('Reports page initialized');
  initReportTypes();
  initReportActions();
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

function showEmptyReport() {
  const container = document.getElementById('report-content');
  if (!container) return;
  container.innerHTML = `
    <div class="empty-state" style="padding:var(--space-12);">
      <div class="empty-icon"><i data-lucide="file-text" style="width:64px;height:64px;opacity:0.2;"></i></div>
      <h3>No Report Data</h3>
      <p style="color:var(--ink-muted);">Select a report type and click <strong>"Generate"</strong> to generate a report.</p>
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
    const result = await API.getReports({ type: _selectedReportType, start_date: '2026-07-01', end_date: '2026-07-19' });
    const data = result.report || result.data || result || [];
    renderReport(data);
  } catch (err) {
    container.innerHTML = `
      <div class="empty-state" style="padding:var(--space-12);">
        <div class="empty-icon"><i data-lucide="alert-circle" style="width:48px;height:48px;opacity:0.3;"></i></div>
        <h3>Report Not Available</h3>
        <p style="color:var(--ink-muted);">${err.message || 'No data available for this report type.'}</p>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
  }
}

function renderReport(data) {
  const container = document.getElementById('report-content');
  if (!container) return;

  const jsonStr = JSON.stringify(data, null, 2);
  container.innerHTML = `
    <div class="card">
      <div class="card-header"><h5 class="section-title">${_selectedReportType.charAt(0).toUpperCase() + _selectedReportType.slice(1)} Report</h5></div>
      <div class="card-body">
        <pre style="background:var(--bg-canvas);padding:var(--space-4);border-radius:var(--radius-md);overflow:auto;max-height:400px;font-size:var(--text-sm);">${jsonStr}</pre>
      </div>
    </div>
  `;
}

function initReportActions() {
  const exportBtn = document.querySelector('[data-action="export-report"]');
  if (exportBtn) {
    exportBtn.addEventListener('click', () => {
      const content = document.getElementById('report-content');
      if (!content || content.querySelector('.empty-state')) {
        Modal.toast({ title: 'Export', message: 'Generate a report first before exporting.', type: 'info' });
        return;
      }
      printElement(content);
    });
  }

  const printBtn = document.querySelector('[data-action="print-report"]');
  if (printBtn) {
    printBtn.addEventListener('click', () => {
      const content = document.getElementById('report-content');
      if (!content || content.querySelector('.empty-state')) {
        Modal.toast({ title: 'Print', message: 'Generate a report first before printing.', type: 'info' });
        return;
      }
      printElement(content);
    });
  }
}

window.generateReport = generateReport;
