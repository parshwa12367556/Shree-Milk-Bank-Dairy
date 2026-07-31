/**
 * ============================================================
 * SMART DAIRY ERP — API Client
 * REST API wrapper with JWT authentication
 * ============================================================
 */

const API = {
  base: '', // Same-origin requests

  /**
   * Make an API request
   * @param {string} method - HTTP method
   * @param {string} path - API endpoint path
   * @param {*} body - Request body (optional)
   * @returns {Promise<*>} Response data
   */
  async request(method, path, body = null) {
    const token = localStorage.getItem('sd_token');
    const headers = { 'Content-Type': 'application/json' };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const opts = { method, headers };
    if (body !== null) {
      opts.body = JSON.stringify(body);
    }

    try {
      const res = await fetch(this.base + path, opts);
      const data = await res.json();

      if (!res.ok) {
        if (res.status === 401) {
          // Unauthorized - redirect to login
          localStorage.removeItem('sd_token');
          localStorage.removeItem('sd_user');
          window.location.hash = '#login';
          throw new Error(data.error || 'Session expired. Please login again.');
        }
        
        // Handle validation errors
        if (res.status === 422 && data.errors) {
          const messages = data.errors.map(e => e.msg || e.message).join(', ');
          throw new Error(messages || data.error || 'Validation failed');
        }
        
        throw new Error(data.error || data.message || 'Request failed');
      }

      return data;
    } catch (err) {
      if (err.message === 'Failed to fetch') {
        throw new Error('Network error. Please check your connection.');
      }
      throw err;
    }
  },

  /** GET request */
  get(path) {
    return this.request('GET', path);
  },

  /** POST request */
  post(path, body) {
    return this.request('POST', path, body);
  },

  /** PATCH request */
  patch(path, body) {
    return this.request('PATCH', path, body);
  },

  /** DELETE request */
  delete(path, body = null) {
    return this.request('DELETE', path, body);
  },

  // ── Dashboard ──
  getDashboard(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/dashboard${query ? '?' + query : ''}`);
  },

  // ── Auth ──
  login(username, password, branchId) {
    return this.post('/api/auth/login', { username, password, branch_id: branchId });
  },

  logout() {
    return this.post('/api/auth/logout');
  },

  getMe() {
    return this.get('/api/auth/me');
  },

  // ── Branches ──
  getBranches() {
    return this.get('/api/branches');
  },

  createBranch(data) {
    return this.post('/api/branches', data);
  },

  updateBranch(id, data) {
    return this.patch(`/api/branches/${id}`, data);
  },

  deleteBranch(id) {
    return this.delete(`/api/branches/${id}`);
  },

  // ── Farmers ──
  getFarmers(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/farmers?${query}`);
  },

  getFarmerStats() {
    return this.get('/api/farmers/stats');
  },

  getFarmer(code) {
    return this.get(`/api/farmers/${code}`);
  },

  createFarmer(data) {
    return this.post('/api/farmers', data);
  },

  updateFarmer(code, data) {
    return this.patch(`/api/farmers/${code}`, data);
  },

  // ── Collections ──
  getCollections(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/collections?${query}`);
  },

  createCollection(data) {
    return this.post('/api/collections', data);
  },

  // ── Payments ──
  getPayments(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/payments?${query}`);
  },

  createPayment(data) {
    return this.post('/api/payments', data);
  },

  updatePayment(id, data) {
    return this.patch(`/api/payments/${id}`, data);
  },

  // ── Pricing ──
  getPricing() {
    return this.get('/api/pricing');
  },

  createPricing(data) {
    return this.post('/api/pricing', data);
  },

  // ── Quality ──
  getQuality(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/quality?${query}`);
  },

  createQuality(data) {
    return this.post('/api/quality', data);
  },

  // ── Rejections ──
  getRejections(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/rejections?${query}`);
  },

  createRejection(data) {
    return this.post('/api/rejections', data);
  },

  // ── Notifications ──
  getNotifications(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/notifications?${query}`);
  },

  markNotificationsRead(data) {
    return this.patch('/api/notifications', data);
  },

  deleteNotifications(data) {
    return this.delete('/api/notifications', data);
  },

  // ── Reports ──
  getReports(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/reports?${query}`);
  },

  // ── Procurement ──
  getProcurementCenters(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/procurement/centers?${query}`);
  },

  createProcurementCenter(data) {
    return this.post('/api/procurement/centers', data);
  },

  getProcurementRoutes(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/procurement/routes?${query}`);
  },

  createProcurementRoute(data) {
    return this.post('/api/procurement/routes', data);
  },

  getChillingCenters(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/procurement/chilling?${query}`);
  },

  createChillingCenter(data) {
    return this.post('/api/procurement/chilling', data);
  },

  // ── Inventory ──
  getInventory(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/inventory?${query}`);
  },

  createInventory(data) {
    return this.post('/api/inventory', data);
  },

  // ── Employees ──
  getEmployees(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/employees?${query}`);
  },

  createEmployee(data) {
    return this.post('/api/employees', data);
  },

  // ── Vehicles ──
  getVehicles(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/vehicles?${query}`);
  },

  createVehicle(data) {
    return this.post('/api/vehicles', data);
  },

  updateVehicle(id, data) {
    return this.patch(`/api/vehicles/${id}`, data);
  },

  deleteVehicle(id) {
    return this.delete(`/api/vehicles/${id}`);
  },

  // ── Audit ──
  getAuditLogs(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/audit?${query}`);
  },

  // ── Settings ──
  getSettings() {
    return this.get('/api/settings');
  },

  updateSettings(data) {
    return this.patch('/api/settings', data);
  },
};

window.API = API;
