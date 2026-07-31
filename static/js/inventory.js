/**
 * ============================================================
 * SMART DAIRY ERP — Inventory Management
 * ============================================================
 */

window.initInventory = function() {
  console.log('Inventory page initialized');
  loadInventoryTable();
};

function loadInventoryTable() {
  const tbody = document.querySelector('#inventory-table tbody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="9" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
        <i data-lucide="package" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
        No inventory items yet. Add items to start tracking stock.
      </td>
    </tr>
  `;
  if (window.lucide) lucide.createIcons();
}
