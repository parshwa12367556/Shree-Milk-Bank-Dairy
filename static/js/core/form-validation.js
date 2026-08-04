/**
 * ============================================================
 * SMART DAIRY ERP — Form Validation
 * ============================================================
 */

const FormValidator = {
  /**
   * Initialize form validation
   * @param {string} formId - Form element ID
   * @param {object} rules - Validation rules
   * @param {Function} onSubmit - Submit handler
   */
  init(formId, rules = {}, onSubmit = null) {
    const form = document.getElementById(formId);
    if (!form) return;

    // Add real-time validation on blur
    Object.keys(rules).forEach(fieldName => {
      const input = form.querySelector(`[name="${fieldName}"]`);
      if (!input) return;

      input.addEventListener('blur', () => {
        this._validateField(input, rules[fieldName]);
      });

      input.addEventListener('input', () => {
        if (input.dataset.touched) {
          this._validateField(input, rules[fieldName]);
        }
      });
    });

    // Handle form submission
    if (onSubmit) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        let isValid = true;
        const data = {};

        Object.keys(rules).forEach(fieldName => {
          const input = form.querySelector(`[name="${fieldName}"]`);
          if (!input) return;

          const fieldValid = this._validateField(input, rules[fieldName]);
          if (!fieldValid) isValid = false;
          
          data[fieldName] = input.value;
        });

        if (isValid) {
          onSubmit(data, form);
        } else {
          // Scroll to first error
          const firstError = form.querySelector('.form-error');
          if (firstError) {
            firstError.closest('.form-group')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
          Modal.toast({ title: 'Validation Error', message: 'Please fix the highlighted fields.', type: 'error' });
        }
      });
    }

    return form;
  },

  /**
   * Validate a single field
   */
  _validateField(input, rules) {
    input.dataset.touched = 'true';
    const value = input.value.trim();
    const errorEl = input.closest('.form-group')?.querySelector('.form-error');
    let errorMessage = '';

    // Required check
    if (rules.required && !value) {
      errorMessage = rules.requiredMessage || 'This field is required';
    }

    // Min length
    if (!errorMessage && rules.minLength && value.length < rules.minLength) {
      errorMessage = rules.minLengthMessage || `Minimum ${rules.minLength} characters required`;
    }

    // Max length
    if (!errorMessage && rules.maxLength && value.length > rules.maxLength) {
      errorMessage = rules.maxLengthMessage || `Maximum ${rules.maxLength} characters allowed`;
    }

    // Pattern
    if (!errorMessage && rules.pattern && !rules.pattern.test(value)) {
      errorMessage = rules.patternMessage || 'Invalid format';
    }

    // Custom validator
    if (!errorMessage && rules.validator) {
      errorMessage = rules.validator(value);
    }

    // Email
    if (!errorMessage && rules.type === 'email' && value && !isValidEmail(value)) {
      errorMessage = 'Invalid email address';
    }

    // Mobile
    if (!errorMessage && rules.type === 'mobile' && value && !isValidMobile(value)) {
      errorMessage = 'Invalid mobile number (10 digits, starting with 6-9)';
    }

    // Number
    if (!errorMessage && rules.type === 'number' && value && isNaN(value)) {
      errorMessage = 'Please enter a valid number';
    }

    // Min value
    if (!errorMessage && rules.min !== undefined && parseFloat(value) < rules.min) {
      errorMessage = rules.minMessage || `Minimum value is ${rules.min}`;
    }

    // Max value
    if (!errorMessage && rules.max !== undefined && parseFloat(value) > rules.max) {
      errorMessage = rules.maxMessage || `Maximum value is ${rules.max}`;
    }

    // Update UI
    input.classList.remove('error', 'success');
    if (errorMessage) {
      input.classList.add('error');
      if (errorEl) {
        errorEl.textContent = errorMessage;
        errorEl.style.display = 'block';
      }
      return false;
    } else if (value) {
      input.classList.add('success');
      if (errorEl) {
        errorEl.textContent = '';
        errorEl.style.display = 'none';
      }
    } else {
      if (errorEl) {
        errorEl.textContent = '';
        errorEl.style.display = 'none';
      }
    }

    return true;
  },

  /**
   * Reset form validation state
   * @param {string} formId - Form element ID
   */
  reset(formId) {
    const form = document.getElementById(formId);
    if (!form) return;

    form.querySelectorAll('.form-error').forEach(el => {
      el.textContent = '';
      el.style.display = 'none';
    });

    form.querySelectorAll('.input-premium').forEach(el => {
      el.classList.remove('error', 'success');
      delete el.dataset.touched;
    });
  },

  /**
   * Get form data as object
   * @param {string} formId - Form element ID
   * @returns {object}
   */
  getFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) return {};

    const data = {};
    const formData = new FormData(form);
    
    for (const [key, value] of formData.entries()) {
      if (data[key] !== undefined) {
        if (!Array.isArray(data[key])) {
          data[key] = [data[key]];
        }
        data[key].push(value);
      } else {
        data[key] = value;
      }
    }

    return data;
  },

  /**
   * Set form data from object
   * @param {string} formId - Form element ID
   * @param {object} data - Data to populate
   */
  setFormData(formId, data) {
    const form = document.getElementById(formId);
    if (!form || !data) return;

    Object.keys(data).forEach(key => {
      const input = form.querySelector(`[name="${key}"]`);
      if (input) {
        input.value = data[key] || '';
      }
    });
  }
};

window.FormValidator = FormValidator;
