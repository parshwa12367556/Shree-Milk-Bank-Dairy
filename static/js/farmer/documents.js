/**
 * SHREE MILK BANK — Farmer: Documents
 * Lists the authenticated farmer's own documents via
 * GET /api/farmer/me/documents, uploads via POST (multipart),
 * and deletes pending ones via DELETE /api/farmer/me/documents/<id>.
 */

function _docStatusBadge(status) {
  const map = { PENDING: 'tag-amber', APPROVED: 'tag-green', REJECTED: 'tag-red' };
  return `<span class="tag ${map[status] || 'tag-neutral'}" style="font-size:10px;">${status || '—'}</span>`;
}

async function loadFarmerDocuments() {
  const body = document.getElementById('documents-body');
  if (body) body.innerHTML = '<tr><td colspan="6" class="text-center" style="padding:var(--space-4);color:var(--ink-muted);font-size:var(--text-sm);">Loading documents…</td></tr>';
  try {
    const data = await API.getMyDocuments();
    const docs = data.documents || [];
    const totalEl = document.getElementById('docs-total');
    if (totalEl) totalEl.textContent = `${docs.length} document${docs.length === 1 ? '' : 's'}`;

    if (!docs.length) {
      body.innerHTML = `<tr><td colspan="6" class="text-center" style="padding:var(--space-6);">
        <div class="empty-icon" style="margin:0 auto var(--space-3);"><i data-lucide="file-text" style="width:36px;height:36px;"></i></div>
        <p style="color:var(--ink-muted);font-size:var(--text-sm);">No documents uploaded yet.</p>
        <button class="btn btn-sm btn-primary" style="margin-top:var(--space-2);" onclick="window.openFarmerDocUpload && openFarmerDocUpload()">Upload your first document</button>
      </td></tr>`;
    } else {
      body.innerHTML = docs.map(d => `
        <tr>
          <td>
            <div style="font-weight:600;font-size:var(--text-sm);">${d.title || 'Untitled'}</div>
            ${d.filePath ? `<a href="${d.filePath}" target="_blank" rel="noopener" style="font-size:var(--text-xs);color:var(--forest);">View file</a>` : ''}
          </td>
          <td><span style="font-size:var(--text-xs);">${(d.docType || 'OTHER').replace('_', ' ')}</span></td>
          <td style="font-size:var(--text-xs);">${fmtDate(d.createdAt)}</td>
          <td>${_docStatusBadge(d.status)}</td>
          <td style="font-size:var(--text-xs);color:var(--ink-muted);">${d.remarks || '—'}</td>
          <td>
            ${(d.status === 'PENDING' || d.status === 'REJECTED')
              ? `<button class="btn btn-sm btn-ghost" onclick="window.deleteFarmerDocument(${d.id})" title="Delete">
                   <i data-lucide="trash-2" style="width:15px;height:15px;"></i>
                 </button>`
              : ''}
          </td>
        </tr>`).join('');
    }
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.warn('Failed to load documents:', err);
    if (body) body.innerHTML = `<tr><td colspan="6" class="text-center" style="padding:var(--space-5);">
      <p style="color:var(--ink-muted);font-size:var(--text-sm);">Unable to load documents. Try again.</p>
      <button class="btn btn-sm btn-ghost" style="margin-top:var(--space-2);" onclick="window.refreshFarmerDocuments && refreshFarmerDocuments()">Try Again</button>
    </td></tr>`;
  }
}

window.refreshFarmerDocuments = loadFarmerDocuments;

window.openFarmerDocUpload = function () {
  const modal = document.getElementById('doc-upload-modal');
  if (modal) modal.style.display = 'flex';
};

function closeFarmerDocUpload() {
  const modal = document.getElementById('doc-upload-modal');
  if (modal) modal.style.display = 'none';
}

window.deleteFarmerDocument = async function (id) {
  if (!window.Modal || !Modal.confirm) {
    try { await API.deleteMyDocument(id); loadFarmerDocuments(); } catch (e) { console.warn(e); }
    return;
  }
  Modal.confirm({
    title: 'Delete Document',
    message: 'Delete this document? This cannot be undone.',
    confirmText: 'Delete',
    variant: 'danger',
    onConfirm: async () => {
      try {
        await API.deleteMyDocument(id);
        Modal.toast({ title: 'Deleted', message: 'Document removed.', type: 'success' });
        loadFarmerDocuments();
      } catch (err) {
        Modal.toast({ title: 'Error', message: err.message || 'Could not delete document.', type: 'error' });
      }
    }
  });
};

window.initFarmerDocuments = function () {
  loadFarmerDocuments();

  const openBtn = document.getElementById('btn-upload-doc');
  if (openBtn) openBtn.addEventListener('click', window.openFarmerDocUpload);

  document.querySelectorAll('[data-close-doc-modal]').forEach(btn => {
    btn.addEventListener('click', closeFarmerDocUpload);
  });
  document.getElementById('doc-upload-modal')?.addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeFarmerDocUpload();
  });

  const form = document.getElementById('form-doc-upload');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const title = document.getElementById('doc-title').value.trim();
      const docType = document.getElementById('doc-type').value;
      const fileInput = document.getElementById('doc-file');
      if (!title || !fileInput?.files?.length) {
        Modal.toast({ title: 'Error', message: 'Title and file are required.', type: 'error' });
        return;
      }
      if (fileInput.files[0].size > 5 * 1024 * 1024) {
        Modal.toast({ title: 'Error', message: 'File is larger than 5 MB.', type: 'error' });
        return;
      }
      const btn = document.getElementById('doc-submit');
      if (btn) { btn.disabled = true; btn.innerHTML = '<span class="anim-spin" style="display:inline-flex;width:16px;height:16px;border:2.5px solid rgba(255,255,255,0.3);border-top-color:white;border-radius:50%;margin-right:8px;"></span> Uploading…'; }
      try {
        const fd = new FormData();
        fd.append('title', title);
        fd.append('docType', docType);
        fd.append('file', fileInput.files[0]);
        await API.uploadMyDocument(fd);
        form.reset();
        closeFarmerDocUpload();
        Modal.toast({ title: 'Uploaded', message: 'Document submitted for review.', type: 'success' });
        loadFarmerDocuments();
      } catch (err) {
        Modal.toast({ title: 'Error', message: err.message || 'Upload failed.', type: 'error' });
      } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="upload" style="width:16px;height:16px;"></i> Upload'; if (window.lucide) lucide.createIcons(); }
      }
    });
  }
};
