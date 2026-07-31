/**
 * ============================================================
 * SMART DAIRY ERP — Chart Helpers (Chart.js wrapper)
 * ============================================================
 */

const AppCharts = {
  instances: {},

  /**
   * Default chart options
   */
  defaults: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 16,
          usePointStyle: true,
          font: { family: "'Inter', sans-serif", size: 12 }
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0,0,0,0.8)',
        padding: 12,
        titleFont: { family: "'Inter', sans-serif", size: 13 },
        bodyFont: { family: "'Inter', sans-serif", size: 12 },
        cornerRadius: 8,
        displayColors: true,
      }
    }
  },

  /**
   * Create or update an area chart
   */
  areaChart(canvasId, labels, datasets, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const config = {
      type: 'line',
      data: { labels, datasets },
      options: {
        ...this.defaults,
        fill: true,
        tension: 0.4,
        elements: {
          point: {
            radius: 3,
            hoverRadius: 6,
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { font: { family: "'Inter', sans-serif", size: 11 } }
          },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(0,0,0,0.06)' },
            ticks: { font: { family: "'Inter', sans-serif", size: 11 } }
          }
        },
        ...options
      }
    };

    return this._createOrUpdate(canvasId, config);
  },

  /**
   * Create or update a bar chart
   */
  barChart(canvasId, labels, datasets, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const config = {
      type: 'bar',
      data: { labels, datasets },
      options: {
        ...this.defaults,
        borderRadius: 6,
        barPercentage: 0.6,
        categoryPercentage: 0.8,
        scales: {
          x: {
            grid: { display: false },
            ticks: { font: { family: "'Inter', sans-serif", size: 11 } }
          },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(0,0,0,0.06)' },
            ticks: { font: { family: "'Inter', sans-serif", size: 11 } }
          }
        },
        ...options
      }
    };

    return this._createOrUpdate(canvasId, config);
  },

  /**
   * Create or update a doughnut/pie chart
   */
  doughnutChart(canvasId, labels, data, colors, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const config = {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: colors,
          borderWidth: 0,
          hoverOffset: 8,
        }]
      },
      options: {
        ...this.defaults,
        cutout: '72%',
        plugins: {
          ...this.defaults.plugins,
          legend: {
            position: 'bottom',
            labels: {
              padding: 12,
              usePointStyle: true,
              font: { family: "'Inter', sans-serif", size: 11 }
            }
          }
        },
        ...options
      }
    };

    return this._createOrUpdate(canvasId, config);
  },

  /**
   * Create or update a line chart
   */
  lineChart(canvasId, labels, datasets, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const config = {
      type: 'line',
      data: { labels, datasets },
      options: {
        ...this.defaults,
        tension: 0.3,
        elements: {
          point: {
            radius: 4,
            hoverRadius: 7,
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { font: { family: "'Inter', sans-serif", size: 11 } }
          },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(0,0,0,0.06)' },
            ticks: { font: { family: "'Inter', sans-serif", size: 11 } }
          }
        },
        ...options
      }
    };

    return this._createOrUpdate(canvasId, config);
  },

  /**
   * Create or update chart instance
   */
  _createOrUpdate(id, config) {
    if (this.instances[id]) {
      this.instances[id].data = config.data;
      this.instances[id].options = config.options;
      this.instances[id].update('none');
      return this.instances[id];
    }

    this.instances[id] = new Chart(document.getElementById(id), config);
    return this.instances[id];
  },

  /**
   * Destroy a chart instance
   */
  destroy(id) {
    if (this.instances[id]) {
      this.instances[id].destroy();
      delete this.instances[id];
    }
  },

  /**
   * Destroy all chart instances
   */
  destroyAll() {
    Object.keys(this.instances).forEach(id => this.destroy(id));
  },

  /**
   * Default color palette
   */
  colors: {
    forest: ['#2e7d32', '#4caf50', '#81c784', '#a5d6a7', '#c8e6c9'],
    gold: ['#d4a043', '#e0b65c', '#e8c77a', '#f0d898', '#f5e6b6'],
    mixed: ['#2e7d32', '#d4a043', '#1565c0', '#d32f2f', '#7b1fa2', '#00897b', '#f9a825', '#e65100'],
    qualitative: ['#2e7d32', '#1565c0', '#d4a043', '#d32f2f', '#7b1fa2', '#00897b', '#f9a825', '#e65100', '#00acc1', '#6d4c41'],
  }
};

window.AppCharts = AppCharts;
