/**
 * ============================================================
 * SMART DAIRY ERP — Modal Dialog System
 * ============================================================
 */

const Modal = {
  /**
   * Open a modal
   * @param {string} id - Modal element ID
   */
  open(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    
    modal.classList.add('open');
    document.body.classList.add('overflow-hidden');
    
    // Trigger animation
    const content = modal.querySelector('.modal-content');
    if (content) {
      content.style.animation = 'none';
      void content.offsetWidth;
      content.style.animation = 'modalIn 0.3s ease forwards';
    }
    
    // Focus trap
    setTimeout(() => {
      const firstInput = modal.querySelector('input, button, select, textarea');
      if (firstInput) firstInput.focus();
    }, 100);
    
    // Dispatch event
    modal.dispatchEvent(new CustomEvent('modal:open'));
  },

  /**
   * Close a modal
   * @param {string} id - Modal element ID
   */
  close(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    
    modal.classList.remove('open');
    document.body.classList.remove('overflow-hidden');
    
    // Dispatch event
    modal.dispatchEvent(new CustomEvent('modal:close'));
  },

  /**
   * Close all modals
   */
  closeAll() {
    document.querySelectorAll('.modal.open').forEach(m => {
      m.classList.remove('open');
    });
    document.body.classList.remove('overflow-hidden');
  },

  /**
   * Show a confirmation dialog
   * @param {object} options
   * @param {string} options.title - Dialog title
   * @param {string} options.message - Dialog message
   * @param {string} options.confirmText - Confirm button text
   * @param {string} options.cancelText - Cancel button text
   * @param {string} options.variant - 'danger' | 'warning' | 'info'
   * @param {Function} options.onConfirm - Confirm callback
   * @param {Function} options.onCancel - Cancel callback
   */
  confirm(options = {}) {
    const {
      title = 'Confirm Action',
      message = 'Are you sure?',
      confirmText = 'Confirm',
      cancelText = 'Cancel',
      variant = 'danger',
      onConfirm = () => {},
      onCancel = () => {},
    } = options;

    // Create modal dynamically
    const modalId = 'modal-confirm-' + Date.now();
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = modalId;
    modal.innerHTML = `
      <div class="modal-backdrop"></div>
      <div class="modal-content" style="max-width: 420px;">
        <div class="modal-header">
          <h5>${title}</h5>
          <button class="modal-close" onclick="Modal.close('${modalId}')">
            <i data-lucide="x"></i>
          </button>
        </div>
        <div class="modal-body">
          <div style="text-align: center; padding: var(--space-4) 0;">
            <div style="font-size: 3rem; margin-bottom: var(--space-3); color: var(--${variant});">
              <i data-lucide="${variant === 'danger' ? 'alert-triangle' : variant === 'warning' ? 'alert-circle' : 'info'}"></i>
            </div>
            <p style="color: var(--ink-secondary);">${message}</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" onclick="Modal.close('${modalId}')">${cancelText}</button>
          <button class="btn btn-${variant}" id="${modalId}-confirm">${confirmText}</button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
    this.open(modalId);
    
    // Bind events
    document.getElementById(`${modalId}-confirm`).addEventListener('click', () => {
      onConfirm();
      this.close(modalId);
      setTimeout(() => modal.remove(), 300);
    });

    // Close on backdrop click
    modal.querySelector('.modal-backdrop').addEventListener('click', () => {
      onCancel();
      this.close(modalId);
      setTimeout(() => modal.remove(), 300);
    });

    // Clean up on close
    modal.addEventListener('modal:close', () => {
      setTimeout(() => {
        if (document.body.contains(modal)) modal.remove();
      }, 300);
    });

    // Lucide icons
    if (window.lucide) {
      lucide.createIcons();
    }

    return modalId;
  },

  /**
   * Show a toast notification
   * @param {object} options
   * @param {string} options.title - Toast title
   * @param {string} options.message - Toast message
   * @param {string} options.type - 'success' | 'error' | 'warning' | 'info'
   * @param {number} options.duration - Duration in ms
   */
  toast(options = {}) {
    const {
      title = '',
      message = '',
      type = 'info',
      duration = 4000,
    } = options;

    const toastId = 'toast-' + Date.now();
    const icons = {
      success: 'check-circle',
      error: 'x-circle',
      warning: 'alert-triangle',
      info: 'info',
    };

    const colors = {
      success: 'var(--success)',
      error: 'var(--danger)',
      warning: 'var(--warning-dark)',
      info: 'var(--info)',
    };

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.id = toastId;
    toast.style.cssText = `
      position: fixed;
      top: var(--space-4);
      right: var(--space-4);
      max-width: 380px;
      background: var(--bg-card);
      border: 1px solid var(--line);
      border-radius: var(--radius-xl);
      box-shadow: var(--shadow-xl);
      padding: var(--space-4) var(--space-4);
      display: flex;
      align-items: flex-start;
      gap: var(--space-3);
      z-index: var(--z-toast);
      animation: toastIn 0.3s ease forwards;
      border-left: 4px solid ${colors[type]};
    `;

    toast.innerHTML = `
      <div style="font-size: 1.25rem; color: ${colors[type]}; flex-shrink: 0;">
        <i data-lucide="${icons[type]}" style="width: 20px; height: 20px;"></i>
      </div>
      <div style="flex: 1; min-width: 0;">
        ${title ? `<div style="font-weight: var(--weight-semibold); font-size: var(--text-sm); color: var(--ink); margin-bottom: 2px;">${title}</div>` : ''}
        <div style="font-size: var(--text-sm); color: var(--ink-secondary);">${message}</div>
      </div>
      <button onclick="this.closest('.toast').remove()" style="background: none; border: none; cursor: pointer; color: var(--ink-muted); font-size: 1rem; padding: 0; flex-shrink: 0;">
        <i data-lucide="x" style="width: 16px; height: 16px;"></i>
      </button>
    `;

    document.body.appendChild(toast);

    if (window.lucide) {
      lucide.createIcons();
    }

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        if (document.body.contains(toast)) {
          toast.style.animation = 'toastOut 0.3s ease forwards';
          setTimeout(() => {
            if (document.body.contains(toast)) toast.remove();
          }, 300);
        }
      }, duration);
    }

    return toastId;
  },

  /**
   * Show a loading state
   * @param {string} elementId - Element to show loading in
   * @param {boolean} show - Show or hide
   */
  loading(elementId, show = true) {
    const el = document.getElementById(elementId);
    if (!el) return;
    
    if (show) {
      const loader = document.createElement('div');
      loader.className = 'modal-loading';
      loader.id = `${elementId}-loader`;
      loader.innerHTML = '<div class="loader"></div>';
      el.style.position = 'relative';
      el.appendChild(loader);
    } else {
      const loader = document.getElementById(`${elementId}-loader`);
      if (loader) loader.remove();
    }
  },

  /**
   * Show a slide-out drawer
   * @param {string} id - Drawer ID
   */
  openDrawer(id) {
    const drawer = document.getElementById(id);
    if (!drawer) return;
    drawer.classList.add('open');
    document.body.classList.add('overflow-hidden');
  },

  /**
   * Close a drawer
   * @param {string} id - Drawer ID
   */
  closeDrawer(id) {
    const drawer = document.getElementById(id);
    if (!drawer) return;
    drawer.classList.remove('open');
    document.body.classList.remove('overflow-hidden');
  }
};

// Close modal on Escape key (data-force modals cannot be dismissed)
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal.open:not([data-force])').forEach(m => Modal.close(m.id));
  }
});

// Close modal on backdrop click (data-force modals cannot be dismissed)
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-backdrop')) {
    const modal = e.target.closest('.modal');
    if (modal && !modal.hasAttribute('data-force')) Modal.close(modal.id);
  }
});

window.Modal = Modal;
