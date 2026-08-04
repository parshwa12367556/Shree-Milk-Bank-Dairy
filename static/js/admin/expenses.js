/**
 * ============================================================
 * SMART DAIRY ERP — Expenses Page
 * Operational expense tracking for profit/loss accounting.
 * ============================================================
 */

let _expensesData = [];
let _expenseFilter = '';

window.initExpenses = function() {
  console.log('Expenses page initialized');
  loadExpenses();
  initExpenseFilter();
  loadExpenseBranches();
};

async function loadExpenses() {
  const tbody = document.querySelector('#expenses-table tbody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="7"><div class="skeleton skeleton-table-row"></div></td></tr>';

  const params = { per_page: 50 };
  if (_expenseFilter) params.category = _expenseFilter;

  try {
    const result = await API.getExpenses(params);
    _expensesData = result.expenses || [];
    const summary = result.summary || {};

    const totalEl = document.getElementById('exp-kpi-total');
    const countEl = document.getElementById('exp-kpi-count');
    if (totalEl) totalEl.querySelector('.kpi-value').textContent = fmtINR(summary.totalAmount ?? 0);
    if (countEl) countEl.querySelector('.kpi-value').textContent = summary.total ?? _expensesData.length;

    if (!_expensesData.length) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">
            <i data-lucide="receipt" style="width:48px;height:48px;margin-bottom:var(--space-4);opacity:0.3;"></i><br>
            No expenses recorded yet. Click "Add Expense".
          </td>
        </tr>
      `;
      if (window.lucide) lucide.createIcons();
      return;
    }

    const catBadges = {
      FEED: 'tag-green', LABOUR: 'tag-blue', TRANSPORT: 'tag-purple',
      MAINTENANCE: 'tag-gold', ELECTRICITY: 'tag-teal', ADMIN: 'tag-neutral',
      PROCUREMENT: 'tag-blue', OTHER: 'tag-neutral',
    };

    tbody.innerHTML = _expensesData.map((e, idx) => `
      <tr>
        <td><span class="font-mono" style="font-weight:600;">${e.code || '-'}</span></td>
        <td>${e.expenseDate ? fmtDate(e.expenseDate, true) : '-'}</td>
        <td><span class="tag ${catBadges[e.category] || 'tag-neutral'}">${e.category || '-'}</span></td>
        <td>${e.description || '-'}</td>
        <td>${e.branchName || '<span style="color:var(--ink-muted);">Head Office</span>'}</td>
        <td><strong>${fmtINR(e.amount ?? 0)}</strong></td>
        <td>
          <div class="table-actions">
            <button class="btn btn-icon btn-sm btn-ghost" title="Edit" onclick="editExpense(${idx})"><i data-lucide="edit-3" style="width:16px;height:16px;"></i></button>
            <button class="btn btn-icon btn-sm btn-ghost" title="Delete" onclick="deleteExpense(${idx})" style="color:var(--danger);"><i data-lucide="trash-2" style="width:16px;height:16px;"></i></button>
          </div>
        </td>
      </tr>
    `).join('');
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.warn('Failed to load expenses:', err);
    tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding:var(--space-8);color:var(--ink-muted);">${err.message || 'Failed to load expenses'}</td></tr>`;
  }
}

function initExpenseFilter() {
  const select = document.getElementById('expense-category-filter');
  if (!select) return;
  select.addEventListener('change', () => {
    _expenseFilter = select.value;
    loadExpenses();
  });
}

async function loadExpenseBranches() {
  const select = document.getElementById('expense-branch');
  if (!select) return;
  try {
    const result = await API.getBranches();
    const branches = result.branches || [];
    select.innerHTML = '<option value="">Head Office</option>' +
      branches.map(b => `<option value="${b.id}">${b.code} — ${b.name}</option>`).join('');
  } catch (err) { /* ignore */ }
}

function openExpenseModal() {
  document.getElementById('expense-modal-title').textContent = 'Add Expense';
  document.getElementById('expense-id').value = '';
  document.getElementById('expense-form').reset();
  document.getElementById('expense-category').value = 'OTHER';
  document.getElementById('expense-date').value = todayISO();
  document.getElementById('expense-modal').classList.add('open');
}

function editExpense(idx) {
  const e = _expensesData[idx];
  if (!e) return;
  document.getElementById('expense-modal-title').textContent = 'Edit Expense';
  document.getElementById('expense-id').value = e.id;
  document.getElementById('expense-category').value = e.category || 'OTHER';
  document.getElementById('expense-amount').value = e.amount ?? '';
  document.getElementById('expense-description').value = e.description || '';
  document.getElementById('expense-date').value = e.expenseDate ? e.expenseDate.slice(0, 10) : todayISO();
  document.getElementById('expense-branch').value = e.branchId || '';
  document.getElementById('expense-modal').classList.add('open');
}

function closeExpenseModal() {
  document.getElementById('expense-modal').classList.remove('open');
}

async function saveExpense() {
  const id = document.getElementById('expense-id').value;
  const amount = document.getElementById('expense-amount').value;
  const category = document.getElementById('expense-category').value;
  if (!amount || parseFloat(amount) <= 0) {
    Modal.toast({ title: 'Validation Error', message: 'Enter a valid amount', type: 'error' });
    return;
  }
  const payload = {
    category,
    amount: parseFloat(amount),
    description: document.getElementById('expense-description').value.trim(),
    expenseDate: document.getElementById('expense-date').value,
    branchId: document.getElementById('expense-branch').value ? parseInt(document.getElementById('expense-branch').value) : null,
  };
  try {
    if (id) await API.updateExpense(id, payload);
    else await API.createExpense(payload);
    closeExpenseModal();
    loadExpenses();
    Modal.toast({ title: 'Saved', message: 'Expense saved successfully', type: 'success' });
  } catch (err) {
    Modal.toast({ title: 'Error', message: err.message || 'Save failed', type: 'error' });
  }
}

function deleteExpense(idx) {
  const e = _expensesData[idx];
  if (!e) return;
  Modal.confirm({
    title: 'Delete Expense',
    message: `Delete expense <strong>${e.code}</strong> (${fmtINR(e.amount)})?`,
    confirmText: 'Delete',
    variant: 'danger',
    onConfirm: async () => {
      try {
        await API.deleteExpense(e.id);
        loadExpenses();
        Modal.toast({ title: 'Deleted', message: 'Expense deleted', type: 'success' });
      } catch (err) {
        Modal.toast({ title: 'Error', message: err.message || 'Delete failed', type: 'error' });
      }
    }
  });
}

window.openExpenseModal = openExpenseModal;
window.editExpense = editExpense;
window.closeExpenseModal = closeExpenseModal;
window.saveExpense = saveExpense;
window.deleteExpense = deleteExpense;
