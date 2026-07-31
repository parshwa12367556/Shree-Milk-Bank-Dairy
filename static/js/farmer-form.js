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
  }
  
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
            await API.updateFarmer(editFarmer.code, buildFarmerPayload(data));
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
  return {
    farmer_name: data.farmer_name,
    father_name: data.father_name,
    mobile: data.mobile,
    alt_mobile: data.alt_mobile || null,
    email: data.email || null,
    aadhaar: data.aadhaar,
    pan: data.pan || null,
    date_of_birth: data.date_of_birth || null,
    address: data.address || null,
    village: data.village,
    taluka: data.taluka || null,
    district: data.district || null,
    state: data.state || null,
    pincode: data.pincode || null,
    landmark: data.landmark || null,
    milk_type: data.milk_type,
    cow_count: parseInt(data.cow_count) || 0,
    buffalo_count: parseInt(data.buffalo_count) || 0,
    breed: data.breed || null,
    preferred_shift: data.preferred_shift || null,
    branch_id: parseInt(data.branch_id) || 1,
    notification_sms: data.notification_sms === 'on',
    notification_whatsapp: data.notification_whatsapp === 'on',
    notification_email: data.notification_email === 'on',
  };
}

function updateFormForEdit(isEditing, farmer) {
  const pageHeader = document.querySelector('#page-farmer-form .page-header');
  if (!pageHeader) return;

  const titleEl = pageHeader.querySelector('h2');
  const subtitleEl = pageHeader.querySelector('.subtitle');
  const submitBtn = document.querySelector('#farmer-form button[type="submit"]');

  if (isEditing && farmer) {
    if (titleEl) titleEl.textContent = `Edit Farmer: ${farmer.code}`;
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
  const fieldMap = {
    'farmer_name': farmer.name,
    'father_name': farmer.father,
    'mobile': farmer.mobile,
    'village': farmer.village,
    'district': farmer.district,
    'state': farmer.state,
    'milk_type': farmer.type,
  };
  Object.entries(fieldMap).forEach(([name, value]) => {
    const input = document.querySelector(`[name="${name}"]`);
    if (input && value) input.value = value;
  });
  if (farmer.animals) {
    if (farmer.type === 'COW') {
      const cowInput = document.querySelector('[name="cow_count"]');
      if (cowInput) cowInput.value = farmer.animals;
    } else if (farmer.type === 'BUFFALO') {
      const bufInput = document.querySelector('[name="buffalo_count"]');
      if (bufInput) bufInput.value = farmer.animals;
    }
  }
}

function generateFarmerQR() {
  const name = document.querySelector('[name="farmer_name"]')?.value;
  if (!name) {
    Modal.toast({ title: 'Warning', message: 'Please enter farmer name first', type: 'warning' });
    return;
  }
  Modal.toast({ title: 'QR Generated', message: 'QR code generated for ' + name, type: 'success' });
}
