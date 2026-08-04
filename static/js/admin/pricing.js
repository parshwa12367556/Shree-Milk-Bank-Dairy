/**
 * ============================================================
 * SMART DAIRY ERP — Rate Engine / Pricing
 * ============================================================
 */

window.initPricing = function() {
  console.log('Pricing page initialized');
  loadRateHistory();
  loadRateChart();
};

function loadRateHistory() {
  const tbody = document.querySelector('#rate-history-table tbody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="6" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
        <i data-lucide="dollar-sign" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
        No rate history yet. Create a new rate to get started.
      </td>
    </tr>
  `;
  if (window.lucide) lucide.createIcons();
}

function loadRateChart() {
  if (!window.Chart) return;
  
  const canvas = document.getElementById('rate-comparison-chart');
  if (!canvas) return;

  AppCharts.lineChart('rate-comparison-chart', [], [], {
    plugins: {
      legend: { position: 'top' },
      title: { display: true, text: 'No rate data to display', color: '#9e9e9e' }
    }
  });
}
