/**
 * ============================================================
 * SMART DAIRY ERP — Farmer Profile (client-rendered)
 * ============================================================
 * Loads the authenticated farmer's real profile from
 * GET /api/farmer/me and renders it into the profile page.
 * Saves permitted personal fields via PATCH /api/farmer/me/profile.
 * ============================================================
 */

window.initFarmerProfilePage = function () {
  loadMyProfile();
  initProfileTabs();
  initProfileForm();
};

/** Load + render the farmer's own profile */
async function loadMyProfile() {
  try {
    const result = await API.getMyProfile();
    const f = (result && result.farmer) || null;
    if (!f) return;
    renderProfileHeader(f);
    renderOverview(f);
    renderLivestock(f);
    renderBankTab(f.bankDetail);
    fillEditForm(f);
  } catch (err) {
    console.warn('Failed to load profile:', err);
  }
}

function renderProfileHeader(f) {
  const container = document.querySelector('#page-my-profile .card');
  if (!container) return;
  const initials = (f.name || 'PR').trim().slice(0, 2).toUpperCase();
  const status = f.status === 'ACTIVE';
  container.querySelector('div[style*="border-radius:var(--radius-full)"]').textContent = initials;
  container.querySelector('h3').textContent = f.name || 'Farmer';
  const sub = container.querySelector('p[style*="font-size:var(--text-sm)"]');
  if (sub) {
    sub.innerHTML = `ID: <span class="font-mono">${f.farmerCode || '—'}</span>` +
      (f.branchName ? ` · ${f.branchName}` : '') +
      ` · Status: <span class="tag ${status ? 'tag-green' : 'tag-amber'}">${status ? 'Active' : 'Pending / Inactive'}</span>`;
  }
  if (window.lucide) lucide.createIcons();
}

function renderOverview(f) {
  const grid = document.querySelector('#tab-overview .info-grid');
  if (!grid) return;
  const vals = [
    f.name || '—', f.fatherName || '—', f.mobile || '—', f.email || '—',
    f.village || '—', f.taluka || '—', f.district || '—', f.milkType || '—',
  ];
  grid.querySelectorAll('.info-value').forEach((el, i) => { el.textContent = vals[i] || '—'; });
}

function renderLivestock(f) {
  const grid = document.querySelector('#tab-livestock .info-grid');
  if (!grid) return;
  const vals = [
    f.cowCount != null ? f.cowCount : '—',
    f.buffaloCount != null ? f.buffaloCount : '—',
    f.breed || '—', f.preferredShift || '—',
  ];
  grid.querySelectorAll('.info-value').forEach((el, i) => { el.textContent = vals[i] || '—'; });
}

function renderBankTab(b) {
  const tab = document.querySelector('#tab-bank');
  if (!tab) return;
  const grid = tab.querySelector('.info-grid');
  const note = tab.querySelector('p');
  if (b) {
    if (grid) {
      const vals = [b.accountHolder, b.bankName, b.branchName, b.accountNumberMasked, b.ifsc, b.upi];
      grid.querySelectorAll('.info-value').forEach((el, i) => { el.textContent = vals[i] || '—'; });
    }
    if (note) note.style.display = 'none';
  } else {
    if (grid) grid.style.display = 'none';
    if (note) { note.style.display = ''; note.textContent = 'No bank details on file. Please add them from the Bank Details page.'; }
  }
}

function fillEditForm(f) {
  const set = (id, v) => { const el = document.getElementById(id); if (el) el.value = v || ''; };
  set('pe-mobile', f.mobile); set('pe-alt-mobile', f.altMobile);
  set('pe-email', f.email); set('pe-address', f.address);
  set('pe-village', f.village); set('pe-taluka', f.taluka);
  set('pe-district', f.district); set('pe-state', f.state); set('pe-pincode', f.pincode);
}

function initProfileTabs() {
  const tabs = document.querySelectorAll('#page-my-profile .tabs .tab-btn');
  if (!tabs.length) return;
  tabs.forEach(tab => {
    if (tab.hasAttribute('data-listener')) return;
    tab.setAttribute('data-listener', 'true');
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      document.querySelectorAll('#page-my-profile [id^="tab-"]').forEach(panel => {
        panel.style.display = panel.id === tab.dataset.tab ? '' : 'none';
      });
    });
  });
}

function initProfileForm() {
  const form = document.getElementById('form-profile-edit');
  if (!form || form.hasAttribute('data-listener')) return;
  form.setAttribute('data-listener', 'true');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="anim-spin" style="display:inline-flex;width:16px;height:16px;border:2.5px solid rgba(255,255,255,0.3);border-top-color:white;border-radius:50%;margin-right:8px;"></span> Saving…'; }
    try {
      const payload = {
        mobile: document.getElementById('pe-mobile').value.trim(),
        altMobile: document.getElementById('pe-alt-mobile').value.trim(),
        email: document.getElementById('pe-email').value.trim(),
        address: document.getElementById('pe-address').value.trim(),
        village: document.getElementById('pe-village').value.trim(),
        taluka: document.getElementById('pe-taluka').value.trim(),
        district: document.getElementById('pe-district').value.trim(),
        state: document.getElementById('pe-state').value.trim(),
        pincode: document.getElementById('pe-pincode').value.trim(),
      };
      const result = await API.updateMyProfile(payload);
      if (window.Modal && Modal.toast) Modal.toast({ title: 'Saved', message: result.message || 'Profile updated successfully.', type: 'success' });
      await loadMyProfile();
    } catch (err) {
      if (window.Modal && Modal.toast) Modal.toast({ title: 'Error', message: err.message || 'Could not save profile.', type: 'error' });
    } finally {
      if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="save" style="width:16px;height:16px;"></i> Save Changes'; if (window.lucide) lucide.createIcons(); }
    }
  });
}
