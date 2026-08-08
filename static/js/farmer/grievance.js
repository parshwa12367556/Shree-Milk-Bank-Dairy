/**
 * SHREE MILK BANK — Farmer: Grievance
 * Submit and view the authenticated farmer's own grievances via
 * POST/GET /api/farmer/me/grievances (server-scoped to the farmer).
 */

function _grievanceStatusBadge(status) {
  const map = { OPEN: 'tag-red', IN_PROGRESS: 'tag-blue', RESOLVED: 'tag-green', CLOSED: 'tag-neutral' };
  return `<span class="tag ${map[status] || 'tag-neutral'}" style="font-size:10px;">${status ? status.replace('_', ' ') : '—'}</span>`;
}

async function loadFarmerGrievances() {
  const list = document.getElementById('grievances-list');
  if (!list) return;
  try {
    const data = await API.getMyGrievances();
    const grievances = data.grievances || [];
    if (!grievances.length) {
      list.innerHTML = `<div style="text-align:center;padding:var(--space-8);">
        <div class="empty-icon" style="margin:0 auto var(--space-3);"><i data-lucide="inbox" style="width:36px;height:36px;"></i></div>
        <p style="color:var(--ink-muted);font-size:var(--text-sm);">No grievances raised yet.</p>
      </div>`;
      return;
    }
    list.innerHTML = grievances.map(g => `
      <div style="padding:var(--space-3) 0;border-bottom:1px solid var(--line);">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:var(--space-2);">
          <div style="font-weight:600;font-size:var(--text-sm);">${g.subject || ''}</div>
          ${_grievanceStatusBadge(g.status)}
        </div>
        <div style="color:var(--ink-muted);font-size:var(--text-xs);margin-top:2px;">
          <span class="font-mono">${g.grievanceCode || ''}</span> · ${g.category || ''} · ${fmtDate(g.createdAt)}
        </div>
        <div style="font-size:var(--text-sm);margin-top:var(--space-1);">${g.description || ''}</div>
        ${g.response ? `<div style="margin-top:var(--space-2);padding:var(--space-2) var(--space-3);background:var(--bg-subtle);border-left:3px solid var(--forest);border-radius:var(--radius-md);font-size:var(--text-sm);"><strong>Dairy response:</strong> ${g.response}</div>` : ''}
      </div>`).join('');
  } catch (err) {
    list.innerHTML = `<div style="text-align:center;padding:var(--space-8);">
      <p style="color:var(--ink-muted);font-size:var(--text-sm);">Unable to load grievances. Try again.</p>
      <button class="btn btn-sm btn-ghost" style="margin-top:var(--space-2);" onclick="window.refreshFarmerGrievances && refreshFarmerGrievances()">Try Again</button>
    </div>`;
  }
}

window.refreshFarmerGrievances = function () {
  loadFarmerGrievances();
};

window.initFarmerGrievance = function () {
  loadFarmerGrievances();
  const form = document.getElementById('form-grievance');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
      subject: form.subject?.value?.trim(),
      category: form.category?.value,
      description: form.description?.value?.trim(),
      receiptNo: form.receiptNo?.value?.trim(),
    };
    if (!data.subject || !data.category || !data.description) {
      if (window.Modal && Modal.toast) {
        Modal.toast({ title: 'Error', message: 'Please fill subject, category and description.', type: 'error' });
      }
      return;
    }
    const btn = form.querySelector('button[type="submit"]');
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="anim-spin" style="display:inline-flex;width:18px;height:18px;border:2.5px solid rgba(255,255,255,0.3);border-top-color:white;border-radius:50%;margin-right:8px;vertical-align:middle;"></span> Submitting…'; }
    try {
      await API.createMyGrievance(data);
      form.reset();
      await loadFarmerGrievances();
      if (window.Modal && Modal.toast) {
        Modal.toast({ title: 'Submitted', message: 'Your grievance has been submitted. The dairy will respond shortly.', type: 'success' });
      }
    } catch (err) {
      if (window.Modal && Modal.toast) {
        Modal.toast({ title: 'Error', message: err.message || 'Could not submit grievance. Try again.', type: 'error' });
      }
    } finally {
      if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="send" style="width:18px;height:18px;"></i> Submit Grievance'; if (window.lucide) lucide.createIcons(); }
    }
  });
};
