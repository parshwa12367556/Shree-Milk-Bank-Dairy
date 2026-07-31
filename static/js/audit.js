/**
 * ============================================================
 * SMART DAIRY ERP — Audit Logs
 * ============================================================
 */

window.initAudit = function() {
  console.log('Audit page initialized');
  loadAuditLogs();
};

function loadAuditLogs() {
  const tbody = document.querySelector('#audit-table tbody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="6" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
        <i data-lucide="scroll-text" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
        No audit logs yet. Activity will be recorded here as you use the system.
      </td>
    </tr>
  `;
  if (window.lucide) lucide.createIcons();
}
