/**
 * ============================================================
 * SMART DAIRY ERP — Quality Control
 * ============================================================
 * Full quality test management via API
 * ============================================================
 */

window.initQuality = function() {
  console.log('Quality page initialized');
  loadQualityData();
};

async function loadQualityData() {
  const tbody = document.querySelector('#quality-table tbody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="10"><div class="skeleton skeleton-table-row"></div></td></tr>';

  try {
    const result = await API.getQuality();
    const tests = result.qualityTests || result.data || result || [];
    renderQualityTable(tests);
  } catch (err) {
    console.warn('Failed to load quality tests:', err);
    renderQualityTable([]);
  }
}

function renderQualityTable(tests) {
  const tbody = document.querySelector('#quality-table tbody');
  if (!tbody) return;

  if (!tests.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="10" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
          <i data-lucide="flask-conical" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
          No quality tests recorded yet.
        </td>
      </tr>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  const resultBadges = { PASS: 'tag-green', BORDERLINE: 'tag-gold', FAIL: 'tag-red' };
  tbody.innerHTML = tests.map(t => `
    <tr>
      <td>${t.collectionId || '-'}</td>
      <td>${t.farmerName || '-'}</td>
      <td>${t.fat || '-'}</td>
      <td>${t.snf || '-'}</td>
      <td>${t.clr || '-'}</td>
      <td>${t.waterContent || '-'}%</td>
      <td>${t.temperature || '-'}°C</td>
      <td><span class="tag ${resultBadges[t.overallResult] || 'tag-neutral'}">${t.overallResult || '-'}</span></td>
      <td>${fmtDate(t.date, true)}</td>
      <td><div class="table-actions"><button class="btn btn-icon btn-sm btn-ghost" title="View"><i data-lucide="eye" style="width:16px;height:16px;"></i></button></div></td>
    </tr>
  `).join('');
  if (window.lucide) lucide.createIcons();
}

// Quality test modal functions
function openQualityModal() {
  document.getElementById('quality-modal-title').textContent = 'New Quality Test';
  document.getElementById('quality-form').reset();
  Modal.open('quality-modal');
  if (window.lucide) setTimeout(() => lucide.createIcons(), 50);
}

function closeQualityModal() {
  Modal.close('quality-modal');
}

async function saveQualityTest() {
  const data = {
    collection_id: parseInt(document.getElementById('q-test-collection')?.value) || null,
    farmer_id: parseInt(document.getElementById('q-test-farmer')?.value) || null,
    branch_id: 1,
    fat: parseFloat(document.getElementById('q-test-fat')?.value) || 0,
    snf: parseFloat(document.getElementById('q-test-snf')?.value) || 0,
    clr: parseFloat(document.getElementById('q-test-clr')?.value) || 0,
    temperature: parseFloat(document.getElementById('q-test-temp')?.value) || 0,
    water_content: parseFloat(document.getElementById('q-test-water')?.value) || 0,
    overall_result: document.getElementById('q-test-result')?.value || 'PASS',
  };

  if (!data.farmer_id) {
    Modal.toast({ title: 'Validation Error', message: 'Farmer ID is required', type: 'error' });
    return;
  }

  try {
    await API.createQuality(data);
    closeQualityModal();
    await loadQualityData();
    Modal.toast({ title: 'Test Saved', message: 'Quality test recorded successfully', type: 'success' });
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message || 'Failed to save test', type: 'error' });
  }
}

window.openQualityModal = openQualityModal;
window.closeQualityModal = closeQualityModal;
window.saveQualityTest = saveQualityTest;
