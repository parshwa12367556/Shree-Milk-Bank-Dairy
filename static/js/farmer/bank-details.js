/**
 * ============================================================
 * SMART DAIRY ERP — Farmer Bank Details (client-rendered)
 * ============================================================
 * Loads the authenticated farmer's real bank details from
 * GET /api/farmer/me/bank-details and renders the verification
 * status + masked account. Saving via POST resets verification
 * to PENDING (admin re-verifies before payments).
 * ============================================================
 */

window.initFarmerBankDetails = function () {
  loadBankDetails();
  initBankForm();
};

/** Load + render the farmer's own bank details */
async function loadBankDetails() {
  const values = document.querySelectorAll('#page-farmer-bank-details .info-value');
  try {
    const result = await API.getMyBankDetails();
    const b = (result && result.bankDetail) || null;

    // Render the real values (or empty states) in the info grid.
    if (values.length) {
      const map = ['accountHolder', 'bankName', 'branchName', 'accountNumberMasked', 'ifsc', 'upi'];
      values.forEach((el, i) => {
        if (i < map.length && b) {
          el.textContent = b[map[i]] || '—';
        } else {
          el.textContent = '—';
        }
      });
    }

    // Verification status badge + helper message
    const header = document.querySelector('#page-farmer-bank-details .card-header');
    const note = document.querySelector('#page-farmer-bank-details .card-body > div[style*="margin-top"]');
    if (header) {
      const old = header.querySelector('.tag');
      if (old) old.remove();
      if (b && b.verificationStatus) {
        const span = document.createElement('span');
        span.className = 'tag ' + ({ VERIFIED: 'tag-green', REJECTED: 'tag-red' }[b.verificationStatus] || 'tag-amber');
        span.textContent = b.verificationStatus === 'VERIFIED' ? 'Verified'
          : b.verificationStatus === 'REJECTED' ? 'Rejected' : 'Pending Verification';
        header.appendChild(span);
      }
    }
    if (note && b) {
      const msgs = {
        VERIFIED: 'Your bank details have been verified by the head office. Payments will be transferred to this account.',
        REJECTED: 'Your bank details were rejected. Please contact your branch with the correct details so they can be updated.',
        PENDING: 'Your bank details are awaiting verification by the head office. You can continue supplying milk while this is in progress.',
      };
      note.textContent = msgs[b.verificationStatus] || '';
    }

    // Pre-fill the edit form with the current (real) values.
    if (b) {
      const set = (id, v) => { const el = document.getElementById(id); if (el) el.value = v || ''; };
      set('bk-holder', b.accountHolder || '');
      set('bk-name', b.bankName || '');
      set('bk-branch', b.branchName || '');
      set('bk-account', b.accountNumber || '');
      set('bk-ifsc', b.ifsc || '');
      set('bk-upi', b.upi || '');
    }
  } catch (err) {
    console.warn('Failed to load bank details:', err);
  }
}

/** Wire the save handler */
function initBankForm() {
  const form = document.getElementById('form-bank-edit');
  if (!form || form.hasAttribute('data-listener')) return;
  form.setAttribute('data-listener', 'true');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    const show = (t, m, ty) => { if (window.Modal && Modal.toast) Modal.toast({ title: t, message: m, type: ty }); };
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="anim-spin" style="display:inline-flex;width:16px;height:16px;border:2.5px solid rgba(255,255,255,0.3);border-top-color:white;border-radius:50%;margin-right:8px;"></span> Saving…'; }
    try {
      const payload = {
        accountHolder: document.getElementById('bk-holder').value.trim(),
        bankName: document.getElementById('bk-name').value.trim(),
        branchName: document.getElementById('bk-branch').value.trim(),
        accountNumber: document.getElementById('bk-account').value.trim(),
        ifsc: document.getElementById('bk-ifsc').value.trim().toUpperCase(),
        upi: document.getElementById('bk-upi').value.trim(),
      };
      const result = await API.saveMyBankDetails(payload);
      show('Saved', result.message || 'Bank details saved.', 'success');
      await loadBankDetails();
    } catch (err) {
      show('Error', err.message || 'Could not save bank details.', 'error');
    } finally {
      if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="save" style="width:16px;height:16px;"></i> Save Bank Details'; if (window.lucide) lucide.createIcons(); }
    }
  });
}
