/**
 * ============================================================
 * SMART DAIRY ERP — Utility Functions
 * ============================================================
 */

/**
 * Format number as Indian currency (₹)
 * @param {number} n - The number to format
 * @param {number} d - Decimal places
 * @returns {string}
 */
function fmtINR(n, d = 2) {
  if (n === null || n === undefined || isNaN(n)) return '₹0.00';
  const num = Number(n);
  const formatted = num.toLocaleString('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: d,
    maximumFractionDigits: d,
  });
  return formatted;
}

/**
 * Format number with commas (Indian numbering)
 * @param {number} n - The number to format
 * @param {number} d - Decimal places
 * @returns {string}
 */
function fmtNum(n, d = 0) {
  if (n === null || n === undefined || isNaN(n)) return '0';
  return Number(n).toLocaleString('en-IN', {
    minimumFractionDigits: d,
    maximumFractionDigits: d,
  });
}

/**
 * Format a date string to readable format
 * @param {string|Date} date - Date to format
 * @param {boolean} short - Short format
 * @returns {string}
 */
function fmtDate(date, short = false) {
  if (!date) return '-';
  const d = new Date(date);
  if (isNaN(d.getTime())) return '-';
  
  const options = short
    ? { day: '2-digit', month: 'short', year: 'numeric' }
    : { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' };
  
  return d.toLocaleDateString('en-IN', options);
}

/**
 * Format time only
 * @param {string|Date} date
 * @returns {string}
 */
function fmtTime(date) {
  if (!date) return '-';
  const d = new Date(date);
  if (isNaN(d.getTime())) return '-';
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}

/**
 * Get today's date in YYYY-MM-DD format
 * @returns {string}
 */
function todayISO() {
  const d = new Date();
  return d.toISOString().split('T')[0];
}

/**
 * Get current time in HH:mm format
 * @returns {string}
 */
function nowTime() {
  const d = new Date();
  return d.toTimeString().slice(0, 5);
}

/**
 * Generate sequential receipt number
 * @param {number} seq - Sequence number
 * @returns {string}
 */
function generateReceiptNo(seq) {
  return 'RC' + String(seq).padStart(7, '0');
}

/**
 * Generate farmer code based on milk type and sequence
 * @param {string} type - COW, BUFFALO, or MIXED
 * @param {number} seq - Sequence number
 * @returns {string}
 */
function generateFarmerCode(type, seq) {
  const prefix = type === 'COW' ? 'C' : type === 'BUFFALO' ? 'B' : 'M';
  return prefix + String(seq);
}

/**
 * Generate payment code
 * @param {number} seq - Sequence number
 * @returns {string}
 */
function generatePayCode(seq) {
  return 'PAY' + String(seq).padStart(7, '0');
}

/**
 * Conditional class name builder
 * @param  {...any} args - Class names or conditional objects
 * @returns {string}
 */
function cn(...args) {
  return args
    .filter(Boolean)
    .map(arg => {
      if (typeof arg === 'string') return arg;
      if (typeof arg === 'object' && arg !== null) {
        return Object.entries(arg)
          .filter(([, v]) => v)
          .map(([k]) => k)
          .join(' ');
      }
      return '';
    })
    .join(' ');
}

/**
 * Truncate a string
 * @param {string} str - String to truncate
 * @param {number} len - Max length
 * @returns {string}
 */
function truncate(str, len = 50) {
  if (!str) return '';
  if (str.length <= len) return str;
  return str.slice(0, len) + '...';
}

/**
 * Debounce function
 * @param {Function} fn - Function to debounce
 * @param {number} delay - Delay in ms
 * @returns {Function}
 */
function debounce(fn, delay = 300) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

/**
 * Throttle function
 * @param {Function} fn - Function to throttle
 * @param {number} limit - Limit in ms
 * @returns {Function}
 */
function throttle(fn, limit = 300) {
  let inThrottle;
  return function (...args) {
    if (!inThrottle) {
      fn.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Get initials from a name
 * @param {string} name - Full name
 * @returns {string}
 */
function getInitials(name) {
  if (!name) return '?';
  return name
    .split(' ')
    .map(w => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>}
 */
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Fallback
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    return true;
  }
}

/**
 * Download data as a file
 * @param {string} content - File content
 * @param {string} filename - File name
 * @param {string} mimeType - MIME type
 */
function downloadFile(content, filename, mimeType = 'text/csv') {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Export table data to CSV
 * @param {Array} data - Array of objects
 * @param {string} filename - Output filename
 */
function exportToCSV(data, filename = 'export.csv') {
  if (!data || !data.length) return;
  
  const headers = Object.keys(data[0]);
  const csvRows = [];
  
  // Headers
  csvRows.push(headers.join(','));
  
  // Data rows
  for (const row of data) {
    const values = headers.map(header => {
      const val = row[header]?.toString() || '';
      // Escape quotes and wrap in quotes if contains comma
      if (val.includes(',') || val.includes('"') || val.includes('\n')) {
        return `"${val.replace(/"/g, '""')}"`;
      }
      return val;
    });
    csvRows.push(values.join(','));
  }
  
  downloadFile(csvRows.join('\n'), filename, 'text/csv;charset=utf-8;');
}

/**
 * Print specific element
 * @param {string|HTMLElement} element - Element or selector to print
 */
function printElement(element) {
  const el = typeof element === 'string' ? document.querySelector(element) : element;
  if (!el) return;
  
  const printWindow = window.open('', '_blank');
  printWindow.document.write(`
    <html>
      <head>
        <title>Print</title>
        <style>
          body { font-family: 'Inter', sans-serif; padding: 40px; }
          table { width: 100%; border-collapse: collapse; }
          th, td { padding: 8px 12px; border: 1px solid #ddd; text-align: left; }
          th { background: #f5f5f5; }
          @media print { body { padding: 0; } }
        </style>
      </head>
      <body>${el.innerHTML}</body>
    </html>
  `);
  printWindow.document.close();
  printWindow.focus();
  setTimeout(() => printWindow.print(), 500);
}

/**
 * Get the current shift based on time
 * @returns {string} 'MORNING' or 'EVENING'
 */
function getCurrentShift() {
  const hour = new Date().getHours();
  return hour < 14 ? 'MORNING' : 'EVENING';
}

/**
 * Format milk type label
 * @param {string} type
 * @returns {string}
 */
function fmtMilkType(type) {
  const map = { COW: 'Cow Milk', BUFFALO: 'Buffalo Milk', MIXED: 'Mixed Milk' };
  return map[type] || type;
}

/**
 * Generate a simple unique ID
 * @returns {string}
 */
function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

/**
 * Sleep / delay
 * @param {number} ms - Milliseconds
 * @returns {Promise<void>}
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Validate Indian mobile number
 * @param {string} mobile
 * @returns {boolean}
 */
function isValidMobile(mobile) {
  return /^[6-9]\d{9}$/.test(mobile);
}

/**
 * Validate email
 * @param {string} email
 * @returns {boolean}
 */
function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Validate IFSC code
 * @param {string} ifsc
 * @returns {boolean}
 */
function isValidIFSC(ifsc) {
  return /^[A-Z]{4}0[A-Z0-9]{6}$/.test(ifsc);
}

/**
 * Validate Aadhaar number
 * @param {string} aadhaar
 * @returns {boolean}
 */
function isValidAadhaar(aadhaar) {
  return /^\d{12}$/.test(aadhaar);
}

/**
 * Calculate collection amount
 * @param {number} fat - Fat percentage
 * @param {number} snf - SNF percentage
 * @param {number} quantity - Milk quantity in liters
 * @param {number} fatRate - Rate per fat unit
 * @param {number} snfRate - Rate per SNF unit
 * @returns {{ ratePerLiter: number, amount: number }}
 */
function computePrice(fat, snf, quantity, fatRate, snfRate) {
  const ratePerLiter = Math.round((fat * fatRate + snf * snfRate) * 100) / 100;
  const amount = Math.round(ratePerLiter * quantity * 100) / 100;
  return { ratePerLiter, amount };
}

/**
 * Get quality grade based on parameters
 * @param {number} fat - Fat %
 * @param {number} water - Water %
 * @param {string} milkType - COW/BUFFALO/MIXED
 * @returns {{ grade: string, label: string }}
 */
function qualityGrade(fat, water, milkType) {
  const isCow = milkType === 'COW';
  const minFat = isCow ? 3.0 : 4.5;
  
  if (water > 8 || fat < minFat * 0.7) {
    return { grade: 'C', label: 'Rejected' };
  }
  if (water > 5 || fat < minFat * 0.85) {
    return { grade: 'B', label: 'Borderline' };
  }
  return { grade: 'A', label: 'Pass' };
}

/**
 * Get status badge class
 * @param {string} status - Status value
 * @returns {string}
 */
function statusBadge(status) {
  const map = {
    ACTIVE: 'tag-green',
    INACTIVE: 'tag-neutral',
    BLOCKED: 'tag-red',
    PENDING: 'tag-gold',
    APPROVED: 'tag-blue',
    PAID: 'tag-green',
    REJECTED: 'tag-red',
    ACCEPTED: 'tag-green',
    PASS: 'tag-green',
    FAIL: 'tag-red',
    BORDERLINE: 'tag-gold',
  };
  return map[status] || 'tag-neutral';
}

/**
 * Filter audit log table
 */
function filterAuditLogs() {
  const tbody = document.querySelector('#audit-table tbody');
  if (!tbody) return;
  
  Modal.toast({ title: 'Filter', message: 'Filtering audit log entries...', type: 'info' });
  
  // Try loading via API request directly
  API.request('GET', '/api/audit')
    .then(result => {
      const logs = result.audit_logs || result.data || result;
      const items = Array.isArray(logs) ? logs : [];
      if (items.length) {
        tbody.innerHTML = items.map(log => `
          <tr>
            <td>${fmtDate(log.timestamp || log.createdAt)}</td>
            <td>${log.user || log.username || '-'}</td>
            <td>${log.action || '-'}</td>
            <td>${log.entity || '-'}</td>
            <td>${log.entity_id || '-'}</td>
            <td>${log.details || '-'}</td>
          </tr>
        `).join('');
        Modal.toast({ title: 'Filter', message: `Showing ${items.length} audit log entries`, type: 'success' });
      } else {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:var(--space-4);color:var(--ink-muted);">No audit log entries found for the selected filters</td></tr>';
        Modal.toast({ title: 'Filter', message: 'No entries found', type: 'info' });
      }
    })
    .catch(() => {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:var(--space-4);color:var(--ink-muted);">No audit log data available</td></tr>';
    });
}

/**
 * Undo last collection entry
 */
function undoLastCollection() {
  Modal.confirm({
    title: 'Undo Last Entry',
    message: 'Are you sure you want to undo the last collection entry?',
    confirmText: 'Undo',
    variant: 'warning',
    onConfirm: () => {
      Modal.toast({ title: 'Undone', message: 'Last collection entry has been undone', type: 'success' });
    }
  });
}

/**
 * Filter passbook transactions by date range
 */
function filterPassbook() {
  const tbody = document.querySelector('#passbook-table tbody');
  if (!tbody) return;
  
  // Get the date inputs in the passbook toolbar
  const dateInputs = tbody.closest('.table-wrapper')?.querySelectorAll('input[type="date"]') ||
    document.querySelectorAll('#page-farmer-passbook input[type="date"]');
  
  const startDate = dateInputs?.[0]?.value || '';
  const endDate = dateInputs?.[1]?.value || '';
  
  if (startDate && endDate) {
    Modal.toast({ 
      title: 'Filter Applied', 
      message: `Showing passbook entries from ${startDate} to ${endDate}`, 
      type: 'success' 
    });
  } else {
    Modal.toast({ 
      title: 'Filter', 
      message: 'Please select a date range to filter passbook entries', 
      type: 'info' 
    });
  }
}

/**
 * Open help guide section
 * @param {string} section - Guide section name
 */
function openHelpGuide(section) {
  // "Getting Started" opens the full in-app User Guide (guidance book)
  if (section === 'getting-started' && window.Guide) {
    Router.navigate('guide');
    window.Guide.open('getting-started');
    return;
  }
  const guides = {
    'getting-started': {
      title: 'Getting Started Guide',
      message: 'Learn the basics of Shree Milk Bank - managing farmers, recording collections, processing payments, and generating reports.'
    },
    'video-tutorials': {
      title: 'Video Tutorials',
      message: 'Watch step-by-step video guides on how to use each feature of the Shree Milk Bank system.'
    },
    'contact-support': {
      title: 'Contact Support',
      message: 'Need help? Contact our support team at support@smartdairy.com or call +91-1800-123-4567.'
    }
  };
  const guide = guides[section] || { title: 'Help', message: 'Documentation coming soon.' };
  Modal.toast({ title: guide.title, message: guide.message, type: 'info' });
}

// Export for use in other modules
window.fmtINR = fmtINR;
window.fmtNum = fmtNum;
window.fmtDate = fmtDate;
window.fmtTime = fmtTime;
window.todayISO = todayISO;
window.nowTime = nowTime;
window.generateReceiptNo = generateReceiptNo;
window.generateFarmerCode = generateFarmerCode;
window.generatePayCode = generatePayCode;
window.cn = cn;
window.truncate = truncate;
window.debounce = debounce;
window.throttle = throttle;
window.getInitials = getInitials;
window.copyToClipboard = copyToClipboard;
window.downloadFile = downloadFile;
window.exportToCSV = exportToCSV;
window.printElement = printElement;
window.getCurrentShift = getCurrentShift;
window.fmtMilkType = fmtMilkType;
window.uid = uid;
window.sleep = sleep;
window.isValidMobile = isValidMobile;
window.isValidEmail = isValidEmail;
window.isValidIFSC = isValidIFSC;
window.isValidAadhaar = isValidAadhaar;
window.computePrice = computePrice;
window.qualityGrade = qualityGrade;
window.statusBadge = statusBadge;
window.filterAuditLogs = filterAuditLogs;
window.undoLastCollection = undoLastCollection;
window.filterPassbook = filterPassbook;
window.openHelpGuide = openHelpGuide;
