/**
 * ============================================================
 * SMART DAIRY ERP — Farmer Registration Form
 * ============================================================
 * Connected to backend API for create and update
 * ============================================================
 */

window.initFarmerForm = function() {
  console.log('Farmer form initialized');
  
  const editFarmer = App.editFarmer;
  const isEditing = !!editFarmer;
  App.editFarmer = null;
  
  updateFormForEdit(isEditing, editFarmer);
  
  if (isEditing) {
    populateFormFields(editFarmer);
  } else {
    // Only Branch Managers can register new farmers (architecture spec)
    const user = Auth.getUser();
    if (!user || !['ADMIN', 'BRANCH_OPERATOR'].includes(user.role)) {
      const card = document.getElementById('farmer-form-card');
      const notice = document.getElementById('farmer-form-access-notice');
      if (card) card.style.display = 'none';
      if (notice) {
        notice.style.display = 'block';
      } else {
        Modal.toast({ title: 'Access Denied', message: 'Only Admin or Branch Operators can register farmers.', type: 'error' });
        setTimeout(() => Router.navigate('farmers'), 1200);
        return;
      }
    }
  }
  
  initBranchLock();
  initFarmerFormHeader();
  
  FormValidator.init('farmer-form', {
    farmer_name: { required: true, minLength: 2, requiredMessage: 'Farmer name is required' },
    father_name: { required: true, requiredMessage: "Father's name is required" },
    mobile: { required: true, type: 'mobile' },
    aadhaar: { required: true, pattern: /^\d{12}$/, patternMessage: 'Enter valid 12-digit Aadhaar' },
    village: { required: true, requiredMessage: 'Village is required' },
    milk_type: { required: true, requiredMessage: 'Select milk type' },
    cow_count: { type: 'number', min: 0 },
    buffalo_count: { type: 'number', min: 0 },
    account_number: { pattern: /^\d{9,18}$/, patternMessage: 'Invalid account number' },
    ifsc: { pattern: /^[A-Z]{4}0[A-Z0-9]{6}$/, patternMessage: 'Invalid IFSC code' },
  }, async (data) => {
    if (isEditing) {
      Modal.confirm({
        title: 'Update Farmer',
        message: 'Are you sure you want to update this farmer?',
        confirmText: 'Update',
        variant: 'primary',
        onConfirm: async () => {
          try {
            await API.updateFarmer(editFarmer.farmerCode || editFarmer.code, buildFarmerPayload(data));
            Modal.toast({ title: 'Success', message: `Farmer ${data.farmer_name} updated successfully!`, type: 'success' });
            setTimeout(() => Router.navigate('farmers'), 1500);
          } catch (err) {
            Modal.toast({ title: 'Error', message: err.message || 'Update failed', type: 'error' });
          }
        }
      });
    } else {
      Modal.confirm({
        title: 'Register Farmer',
        message: 'Are you sure you want to register this farmer?',
        confirmText: 'Register',
        variant: 'primary',
        onConfirm: async () => {
          try {
            const payload = buildFarmerPayload(data);
            await API.createFarmer(payload);
            Modal.toast({ title: 'Success', message: `Farmer ${data.farmer_name} registered successfully!`, type: 'success' });
            setTimeout(() => Router.navigate('farmers'), 1500);
          } catch (err) {
            Modal.toast({ title: 'Error', message: err.message || 'Registration failed', type: 'error' });
          }
        }
      });
    }
  });
};

function buildFarmerPayload(data) {
  const user = Auth.getUser();
  // Farmers always belong to the logged-in Branch Manager's own branch
  const branchId = user && user.branchId ? parseInt(user.branchId) : (parseInt(data.branch_id) || null);
  return {
    name: data.farmer_name,
    fatherName: data.father_name,
    mobile: data.mobile,
    altMobile: data.alt_mobile || null,
    email: data.email || null,
    aadhaar: data.aadhaar,
    pan: data.pan || null,
    dateOfBirth: data.date_of_birth || null,
    address: data.address || null,
    village: data.village,
    taluka: data.taluka || null,
    district: data.district || null,
    state: data.state || null,
    pincode: data.pincode || null,
    landmark: data.landmark || null,
    milkType: data.milk_type,
    cowCount: parseInt(data.cow_count) || 0,
    buffaloCount: parseInt(data.buffalo_count) || 0,
    breed: data.breed || null,
    preferredShift: data.preferred_shift || null,
    branch_id: branchId,
    // Bank details (created at registration, editable by Head Office)
    accountHolder: data.account_holder || data.farmer_name,
    bankName: data.bank_name || null,
    bankBranch: data.branch_name || null,
    accountNumber: data.account_number || null,
    ifsc: data.ifsc || null,
    upi: data.upi || null,
    notification_sms: data.notification_sms === 'on',
    notification_whatsapp: data.notification_whatsapp === 'on',
    notification_email: data.notification_email === 'on',
  };
}

/**
 * Branch select handling.
 * BRANCH_OPERATOR: locked to their own assigned branch.
 * ADMIN: free to pick any ACTIVE branch (spec 5.3 — Admin selects the branch).
 */
function initBranchLock() {
  const select = document.querySelector('#farmer-form [name="branch_id"]');
  if (!select) return;

  const user = Auth.getUser();
  if (user && user.branchId) {
    // Branch Operator: branch is locked to the operator's own branch
    select.innerHTML = '';
    const opt = document.createElement('option');
    opt.value = user.branchId;
    opt.textContent = user.branchName ? `${user.branchName} (${user.branchCode || ''})` : `Branch ${user.branchId}`;
    select.appendChild(opt);
    select.disabled = true;
  } else {
    // Admin: load ACTIVE branches so the farmer can be registered under
    // any branch the admin chooses. (In edit mode the farmer's existing
    // branch is preserved by the form's own prefill.)
    select.innerHTML = '<option value="">Select Branch</option>';
    if (window.API) {
      API.getBranches()
        .then((result) => {
          const branches = (result && (result.branches || result.data)) || [];
          if (branches.length) {
            select.innerHTML = '<option value="">Select Branch</option>';
            branches.forEach((b) => {
              const opt = document.createElement('option');
              opt.value = b.id;
              opt.textContent = `${b.name} (${b.code})`;
              select.appendChild(opt);
            });
          }
        })
        .catch(() => { /* keep the empty select */ });
    }
    select.disabled = false;
  }
}

/**
 * Fill the Company / Branch / Farmer-ID strip at the top of the form.
 */
function initFarmerFormHeader() {
  const branchEl = document.getElementById('farmer-form-branch');
  const idEl = document.getElementById('farmer-form-farmer-id');
  const user = Auth.getUser();

  if (branchEl) {
    branchEl.textContent = (user && user.branchCode)
      ? `${user.branchCode} · ${user.branchName || 'Branch'}`
      : '—';
  }
  if (idEl) {
    idEl.textContent = (user && user.branchCode)
      ? `Auto-generated (${user.branchCode}001)`
      : 'Auto-generated (BR01001)';
  }
}

function updateFormForEdit(isEditing, farmer) {
  const pageHeader = document.querySelector('#page-farmer-form .page-header');
  if (!pageHeader) return;

  const titleEl = pageHeader.querySelector('h2');
  const subtitleEl = pageHeader.querySelector('.subtitle');
  const submitBtn = document.querySelector('#farmer-form button[type="submit"]');

  if (isEditing && farmer) {
    if (titleEl) titleEl.textContent = `Edit Farmer: ${farmer.farmerCode || farmer.code}`;
    if (subtitleEl) subtitleEl.textContent = `Updating details for ${farmer.name}`;
    if (submitBtn) {
      submitBtn.innerHTML = '<i data-lucide="save" style="width:18px;height:18px;"></i> Update Farmer';
    }
  } else {
    if (titleEl) titleEl.textContent = 'Register New Farmer';
    if (subtitleEl) subtitleEl.textContent = 'Add a new farmer to the system';
    if (submitBtn) {
      submitBtn.innerHTML = '<i data-lucide="user-plus" style="width:18px;height:18px;"></i> Register Farmer';
    }
  }
  if (window.lucide) lucide.createIcons();
}

function populateFormFields(farmer) {
  const bank = farmer.bankDetail || {};
  const fieldMap = {
    'farmer_name': farmer.name,
    'father_name': farmer.fatherName || farmer.father,
    'mobile': farmer.mobile,
    'alt_mobile': farmer.altMobile,
    'email': farmer.email,
    'aadhaar': farmer.aadhaar,
    'village': farmer.village,
    'taluka': farmer.taluka,
    'district': farmer.district,
    'state': farmer.state,
    'pincode': farmer.pincode,
    'address': farmer.address,
    'milk_type': farmer.milkType || farmer.type,
    'cow_count': farmer.cowCount,
    'buffalo_count': farmer.buffaloCount,
    'breed': farmer.breed,
    'preferred_shift': farmer.preferredShift,
    'account_holder': bank.accountHolder || farmer.name,
    'bank_name': bank.bankName,
    'branch_name': bank.branchName,
    'account_number': bank.accountNumber,
    'ifsc': bank.ifsc,
    'upi': bank.upi,
  };
  Object.entries(fieldMap).forEach(([name, value]) => {
    const input = document.querySelector(`[name="${name}"]`);
    if (input && value !== undefined && value !== null) input.value = value;
  });
}

function generateFarmerQR() {
  const name = document.querySelector('[name="farmer_name"]')?.value;
  if (!name) {
    Modal.toast({ title: 'Warning', message: 'Please enter farmer name first', type: 'warning' });
    return;
  }
  Modal.toast({ title: 'QR Generated', message: 'QR code generated for ' + name, type: 'success' });
}
