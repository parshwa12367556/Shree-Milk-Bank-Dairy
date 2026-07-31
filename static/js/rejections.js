/**
 * ============================================================
 * SMART DAIRY ERP — Milk Rejections
 * ============================================================
 */

window.initRejections = function() {
  console.log('Rejections page initialized');
  loadRejectionsTable();
};

function loadRejectionsTable() {
  const tbody = document.querySelector('#rejections-table tbody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="10" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
        <i data-lucide="x-circle" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
        No milk rejections recorded.
      </td>
    </tr>
  `;
  if (window.lucide) lucide.createIcons();
}
