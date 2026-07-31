/**
 * ============================================================
 * SMART DAIRY ERP — Procurement Management
 * ============================================================
 */

window.initProcurement = function() {
  console.log('Procurement page initialized');
  
  initProcurementTabs();
  loadCollectionCenters();
};

function initProcurementTabs() {
  document.querySelectorAll('.procurement-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.procurement-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      
      document.querySelectorAll('.procurement-tab-content').forEach(c => c.classList.remove('active'));
      const target = document.getElementById(tab.dataset.tab);
      if (target) target.classList.add('active');
      
      if (tab.dataset.tab === 'centers') loadCollectionCenters();
      else if (tab.dataset.tab === 'routes') loadCollectionRoutes();
      else if (tab.dataset.tab === 'chilling') loadChillingCenters();
    });
  });
}

function loadCollectionCenters() {
  const tbody = document.querySelector('#centers-table tbody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="7" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
        <i data-lucide="building-2" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
        No collection centers yet.
      </td>
    </tr>
  `;
  if (window.lucide) lucide.createIcons();
}

function loadCollectionRoutes() {
  const tbody = document.querySelector('#routes-table tbody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="9" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
        <i data-lucide="route" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
        No collection routes yet.
      </td>
    </tr>
  `;
  if (window.lucide) lucide.createIcons();
}

function loadChillingCenters() {
  const tbody = document.querySelector('#chilling-table tbody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="9" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
        <i data-lucide="snowflake" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
        No chilling centers yet.
      </td>
    </tr>
  `;
  if (window.lucide) lucide.createIcons();
}
