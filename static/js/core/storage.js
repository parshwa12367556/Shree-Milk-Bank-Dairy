/**
 * ============================================================
 * SMART DAIRY ERP — Local Storage Helpers
 * ============================================================
 */

const Storage = {
  /**
   * Get an item from local storage
   * @param {string} key
   * @param {*} defaultValue
   * @returns {*}
   */
  get(key, defaultValue = null) {
    try {
      const value = localStorage.getItem(key);
      if (value === null) return defaultValue;
      return JSON.parse(value);
    } catch {
      return defaultValue;
    }
  },

  /**
   * Set an item in local storage
   * @param {string} key
   * @param {*} value
   */
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      console.warn('Storage.set error:', e);
    }
  },

  /**
   * Remove an item from local storage
   * @param {string} key
   */
  remove(key) {
    localStorage.removeItem(key);
  },

  /**
   * Clear all app data from local storage
   */
  clear() {
    const keys = [
      'sd_token', 'sd_user', 'sd_theme', 'sd_sidebar',
      'sd_draft', 'sd_language', 'sd_branch'
    ];
    keys.forEach(k => localStorage.removeItem(k));
  },

  /**
   * Get the auth token
   * @returns {string|null}
   */
  getToken() {
    return localStorage.getItem('sd_token');
  },

  /**
   * Set the auth token
   * @param {string} token
   */
  setToken(token) {
    localStorage.setItem('sd_token', token);
  },

  /**
   * Get the current user
   * @returns {object|null}
   */
  getUser() {
    return this.get('sd_user');
  },

  /**
   * Set the current user
   * @param {object} user
   */
  setUser(user) {
    this.set('sd_user', user);
  },

  /**
   * Get theme preference
   * @returns {string} 'light' or 'dark'
   */
  getTheme() {
    return this.get('sd_theme', 'light');
  },

  /**
   * Set theme preference
   * @param {string} theme
   */
  setTheme(theme) {
    this.set('sd_theme', theme);
  },

  /**
   * Get sidebar state
   * @returns {boolean}
   */
  isSidebarCollapsed() {
    return this.get('sd_sidebar', false);
  },

  /**
   * Set sidebar state
   * @param {boolean} collapsed
   */
  setSidebarCollapsed(collapsed) {
    this.set('sd_sidebar', collapsed);
  },

  /**
   * Save collection draft
   * @param {object} draft
   */
  saveDraft(draft) {
    this.set('sd_draft', {
      ...draft,
      savedAt: new Date().toISOString()
    });
  },

  /**
   * Get saved collection draft
   * @returns {object|null}
   */
  getDraft() {
    return this.get('sd_draft');
  },

  /**
   * Clear collection draft
   */
  clearDraft() {
    this.remove('sd_draft');
  },

  /**
   * Get language preference
   * @returns {string}
   */
  getLanguage() {
    return this.get('sd_language', 'en');
  },

  /**
   * Set language preference
   * @param {string} lang
   */
  setLanguage(lang) {
    this.set('sd_language', lang);
  },

  /**
   * Cache API data
   * @param {string} key
   * @param {*} data
   * @param {number} ttl - Time to live in minutes
   */
  setCache(key, data, ttl = 5) {
    this.set(`cache_${key}`, {
      data,
      expires: Date.now() + ttl * 60 * 1000
    });
  },

  /**
   * Get cached API data
   * @param {string} key
   * @returns {*|null}
   */
  getCache(key) {
    const cached = this.get(`cache_${key}`);
    if (!cached) return null;
    if (Date.now() > cached.expires) {
      this.remove(`cache_${key}`);
      return null;
    }
    return cached.data;
  },

  /**
   * Clear all cache
   */
  clearCache() {
    const keys = Object.keys(localStorage);
    keys.filter(k => k.startsWith('cache_')).forEach(k => localStorage.removeItem(k));
  }
};

window.Storage = Storage;
