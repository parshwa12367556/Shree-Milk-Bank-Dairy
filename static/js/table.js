/**
 * ============================================================
 * SMART DAIRY ERP — Table Utilities
 * ============================================================
 */

const Table = {
  /**
   * Initialize table sorting
   * @param {string} tableId - Table element ID
   */
  initSorting(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const headers = table.querySelectorAll('thead th[data-sortable]');
    headers.forEach(header => {
      header.addEventListener('click', () => {
        const key = header.dataset.sortable;
        const currentDir = header.dataset.dir || 'none';
        let dir = 'asc';
        
        if (currentDir === 'asc') dir = 'desc';
        if (currentDir === 'desc') dir = 'none';
        
        // Reset all headers
        headers.forEach(h => {
          h.dataset.dir = 'none';
          h.classList.remove('sorted');
          const icon = h.querySelector('.sort-icon');
          if (icon) icon.textContent = '';
        });
        
        if (dir !== 'none') {
          header.dataset.dir = dir;
          header.classList.add('sorted');
          const icon = header.querySelector('.sort-icon');
          if (icon) icon.textContent = dir === 'asc' ? '▲' : '▼';
          this._sortTable(table, key, dir);
        } else {
          this._resetSort(table);
        }
      });
    });
  },

  /**
   * Sort table by column
   */
  _sortTable(table, key, dir) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
      const aVal = a.querySelector(`td[data-${key}]`)?.dataset[key] || 
                   a.cells[this._getColumnIndex(table, key)]?.textContent.trim() || '';
      const bVal = b.querySelector(`td[data-${key}]`)?.dataset[key] || 
                   b.cells[this._getColumnIndex(table, key)]?.textContent.trim() || '';
      
      const aNum = parseFloat(aVal);
      const bNum = parseFloat(bVal);
      
      if (!isNaN(aNum) && !isNaN(bNum)) {
        return dir === 'asc' ? aNum - bNum : bNum - aNum;
      }
      
      return dir === 'asc' 
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    });
    
    rows.forEach(row => tbody.appendChild(row));
  },

  /**
   * Reset table to original order
   */
  _resetSort(table) {
    // Implement if needed - store original order
  },

  /**
   * Get column index by data attribute
   */
  _getColumnIndex(table, key) {
    const headers = table.querySelectorAll('thead th');
    for (let i = 0; i < headers.length; i++) {
      if (headers[i].dataset.sortable === key) return i;
    }
    return 0;
  },

  /**
   * Initialize pagination
   * @param {string} tableId - Table element ID
   * @param {number} pageSize - Rows per page
   */
  initPagination(tableId, pageSize = 10) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const pagination = table.closest('.table-wrapper')?.querySelector('.pagination');
    if (!pagination) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
    let currentPage = 1;
    
    // Bail out early if already initialized
    if (pagination.hasAttribute('data-init')) return;
    pagination.setAttribute('data-init', 'true');
    
    // Dynamically assign data-page attributes to numbered buttons
    const allBtns = pagination.querySelectorAll('.page-btn');
    let pageNum = 1;
    allBtns.forEach(btn => {
      if (btn.classList.contains('prev-btn') || btn.classList.contains('next-btn')) return;
      if (btn.classList.contains('page-ellipsis')) return;
      const val = parseInt(btn.textContent.trim());
      if (!isNaN(val)) {
        btn.dataset.page = val;
      }
    });
    
    const renderPage = (page) => {
      currentPage = page;
      const start = (page - 1) * pageSize;
      const end = start + pageSize;
      
      rows.forEach((row, i) => {
        row.style.display = (i >= start && i < end) ? '' : 'none';
      });
      
      // Update pagination buttons
      this._updatePagination(pagination, currentPage, totalPages, renderPage);
    };
    
    // Attach click handlers - use event delegation for safety
    this._wirePagination(pagination, renderPage, totalPages);
    
    renderPage(1);
  },

  /**
   * Wire up pagination button click handlers
   */
  _wirePagination(pagination, renderFn, totalPages) {
    const allBtns = pagination.querySelectorAll('.page-btn');
    
    allBtns.forEach(btn => {
      // Remove old listener if any by cloning
      if (btn.hasAttribute('data-listener')) return;
      btn.setAttribute('data-listener', 'true');
      
      btn.addEventListener('click', (e) => {
        let page;
        
        if (btn.classList.contains('prev-btn')) {
          // Find the currently active page
          const activeBtn = pagination.querySelector('.page-btn.active');
          page = activeBtn ? parseInt(activeBtn.dataset.page) - 1 : 1;
        } else if (btn.classList.contains('next-btn')) {
          const activeBtn = pagination.querySelector('.page-btn.active');
          page = activeBtn ? parseInt(activeBtn.dataset.page) + 1 : totalPages;
        } else {
          page = parseInt(btn.dataset.page);
        }
        
        if (page && page >= 1 && page <= totalPages) {
          renderFn(page);
        }
      });
    });
  },

  /**
   * Update pagination UI
   */
  _updatePagination(pagination, current, total, renderFn) {
    const pageBtns = pagination.querySelectorAll('.page-btn');
    const info = pagination.closest('.table-footer')?.querySelector('.table-info');
    
    if (info) {
      info.textContent = `Page ${current} of ${total}`;
    }
    
    pageBtns.forEach(btn => {
      const page = parseInt(btn.dataset.page);
      btn.classList.toggle('active', page === current);
      
      if (btn.classList.contains('prev-btn')) {
        btn.disabled = current === 1;
      } else if (btn.classList.contains('next-btn')) {
        btn.disabled = current === total;
      }
    });
  },

  /**
   * Filter table rows
   * @param {string} tableId - Table element ID
   * @param {string} query - Search query
   * @param {number} columnIndex - Column to search (optional, searches all if omitted)
   */
  filter(tableId, query, columnIndex = -1) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = tbody.querySelectorAll('tr');
    const q = query.toLowerCase().trim();
    
    rows.forEach(row => {
      let match = false;
      const cells = row.querySelectorAll('td');
      
      if (columnIndex >= 0 && cells[columnIndex]) {
        match = cells[columnIndex].textContent.toLowerCase().includes(q);
      } else {
        cells.forEach(cell => {
          if (cell.textContent.toLowerCase().includes(q)) match = true;
        });
      }
      
      row.style.display = match || !q ? '' : 'none';
    });
  },

  /**
   * Check/uncheck all rows
   * @param {string} tableId - Table element ID
   * @param {boolean} checked - Checked state
   */
  checkAll(tableId, checked) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const checkboxes = table.querySelectorAll('tbody input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = checked);
    
    // Update bulk action bar
    this._updateBulkBar(table);
  },

  /**
   * Update bulk action bar visibility
   */
  _updateBulkBar(table) {
    const wrapper = table.closest('.table-wrapper');
    const bar = wrapper?.querySelector('.bulk-action-bar');
    if (!bar) return;
    
    const checked = table.querySelectorAll('tbody input[type="checkbox"]:checked');
    const count = bar.querySelector('.bulk-count');
    
    if (checked.length > 0) {
      bar.style.display = 'flex';
      if (count) count.textContent = `${checked.length} selected`;
    } else {
      bar.style.display = 'none';
    }
  },

  /**
   * Export table to CSV
   * @param {string} tableId - Table element ID
   * @param {string} filename - Output filename
   */
  exportCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = [];
    
    // Headers
    const headers = [];
    table.querySelectorAll('thead th').forEach(th => {
      // Skip checkbox column
      if (th.classList.contains('checkbox-cell')) return;
      headers.push(th.textContent.trim());
    });
    rows.push(headers.join(','));
    
    // Data rows
    table.querySelectorAll('tbody tr').forEach(tr => {
      if (tr.style.display === 'none') return;
      const cells = [];
      tr.querySelectorAll('td').forEach(td => {
        if (td.classList.contains('checkbox-cell')) return;
        let val = td.textContent.trim().replace(/,/g, '');
        cells.push(val);
      });
      rows.push(cells.join(','));
    });
    
    downloadFile(rows.join('\n'), filename, 'text/csv;charset=utf-8;');
  },

  /**
   * Print table
   * @param {string} tableId - Table element ID
   */
  printTable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    printElement(table);
  }
};

window.Table = Table;
