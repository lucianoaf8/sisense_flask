// Sisense Flask UI JavaScript v2.0

class SisenseAPIManager {
    constructor() {
        this.capabilities = null;
    }

    async initialize() {
        // Get API capabilities
        try {
            const response = await fetch('/api/system/capabilities');
            if (response.ok) {
                const data = await response.json();
                this.capabilities = data.capabilities;
                console.log('API capabilities loaded:', this.capabilities);
            }
        } catch (error) {
            console.warn('Failed to load API capabilities:', error);
            this.capabilities = null;
        }
    }

    async loadDataModels() {
        try {
            const response = await fetch('/api/datamodels');
            const data = await response.json();

            if (response.ok) {
                // Show which API pattern was used
                if (data.api_pattern) {
                    this.showAlert(`Loaded ${data.count} data models using ${data.api_pattern}`, 'success');
                } else {
                    this.showAlert(`Loaded ${data.count} data models`, 'success');
                }
                return data.data;
            } else {
                this.showAlert(data.message, 'warning');
                return [];
            }
        } catch (error) {
            this.showAlert(`Failed to load data models: ${error.message}`, 'error');
            return [];
        }
    }

    async validateAuth() {
        try {
            const response = await fetch('/api/auth/validate');
            const data = await response.json();

            if (response.ok) {
                if (data.auth_pattern) {
                    this.showAlert(`Authentication validated using ${data.auth_pattern}`, 'success');
                }
                return data.valid;
            } else {
                this.showAlert(data.message, 'error');
                return false;
            }
        } catch (error) {
            this.showAlert(`Authentication failed: ${error.message}`, 'error');
            return false;
        }
    }

    async executeQuery(queryType, queryData) {
        try {
            let endpoint;
            if (queryType === 'jaql') {
                endpoint = '/api/jaql';
            } else if (queryType === 'sql') {
                endpoint = '/api/sql';
            } else {
                throw new Error(`Unsupported query type: ${queryType}`);
            }

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(queryData)
            });

            const data = await response.json();

            if (response.ok) {
                this.showAlert('Query executed successfully', 'success');
                return data;
            } else {
                this.showAlert(data.message, 'error');
                throw new Error(data.message);
            }
        } catch (error) {
            this.showAlert(`Query failed: ${error.message}`, 'error');
            throw error;
        }
    }

    showAlert(message, type) {
        // Delegate to main UI class if available
        if (window.sisenseUI && typeof window.sisenseUI.showAlert === 'function') {
            window.sisenseUI.showAlert(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
}

class SisenseUI {
    constructor() {
        this.baseUrl = '';
        this.currentResults = null;
        this.requestCount = 0;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAuthStatus();
        this.logSystemEvent('SisenseUI initialized', 'INFO');
    }

    setupEventListeners() {
        // Authentication form
        const authForm = document.getElementById('auth-form');
        if (authForm) {
            authForm.addEventListener('submit', (e) => this.handleAuth(e));
        }

        // SQL query form
        const sqlForm = document.getElementById('sql-form');
        if (sqlForm) {
            sqlForm.addEventListener('submit', (e) => this.handleSQLQuery(e));
        }

        // JAQL query form
        const jaqlForm = document.getElementById('jaql-form');
        if (jaqlForm) {
            jaqlForm.addEventListener('submit', (e) => this.handleJAQLQuery(e));
        }

        // Dashboard search
        const dashboardSearch = document.getElementById('dashboard-search');
        if (dashboardSearch) {
            dashboardSearch.addEventListener('input', (e) => this.handleDashboardSearch(e));
        }

        // Data model search
        const modelSearch = document.getElementById('model-search');
        if (modelSearch) {
            modelSearch.addEventListener('input', (e) => this.handleModelSearch(e));
        }

        // Refresh buttons
        document.querySelectorAll('.refresh-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleRefresh(e));
        });

        // Export buttons
        document.querySelectorAll('.export-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleExport(e));
        });

        // Enhanced navigation tracking
        this.updateActiveNavigation();
        
        // Track page visits
        this.logUserAction('page_visit', { 
            page: window.location.pathname,
            timestamp: new Date().toISOString()
        });
    }

    updateActiveNavigation() {
        const currentPath = window.location.pathname;
        document.querySelectorAll('.nav-link').forEach(link => {
            const href = link.getAttribute('href');
            if (href === currentPath) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    async checkAuthStatus() {
        const startTime = performance.now();
        
        try {
            const response = await fetch('/api/auth/validate');
            const data = await response.json();
            const responseTime = performance.now() - startTime;
            
            // Log API call
            this.logApiCall('GET', '/api/auth/validate', null, response.status, responseTime);
            
            // Update legacy auth status elements (for backward compatibility)
            const authStatus = document.getElementById('auth-status');
            if (authStatus) {
                if (data.valid) {
                    authStatus.innerHTML = '<span class="badge badge-success">Connected</span>';
                } else {
                    authStatus.innerHTML = '<span class="badge badge-danger">Disconnected</span>';
                }
            }
            
            // Update connection status in header is handled by ConnectionStatusMonitor
            
        } catch (error) {
            console.error('Auth check failed:', error);
            this.logSystemEvent('Auth check failed: ' + error.message, 'ERROR');
            
            const authStatus = document.getElementById('auth-status');
            if (authStatus) {
                authStatus.innerHTML = '<span class="badge badge-warning">Unknown</span>';
            }
        }
    }

    async handleAuth(e) {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]');
        const originalText = btn.textContent;
        
        try {
            btn.textContent = 'Connecting...';
            btn.disabled = true;

            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();
            
            if (response.ok) {
                this.showAlert('Authentication successful!', 'success');
                this.checkAuthStatus();
            } else {
                this.showAlert(data.message || 'Authentication failed', 'danger');
            }
        } catch (error) {
            this.showAlert('Connection error: ' + error.message, 'danger');
        } finally {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    }

    async handleSQLQuery(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const datasource = formData.get('datasource');
        const query = formData.get('query');
        const limit = formData.get('limit');
        
        if (!datasource || !query) {
            this.showAlert('Please provide both datasource and query', 'warning');
            return;
        }

        const btn = e.target.querySelector('button[type="submit"]');
        const originalText = btn.textContent;
        const resultsDiv = document.getElementById('sql-results');
        const startTime = performance.now();
        
        // Log user action
        this.logUserAction('sql_query_executed', { 
            datasource: datasource, 
            query_length: query.length,
            has_limit: !!limit
        });
        
        try {
            btn.textContent = 'Executing...';
            btn.disabled = true;
            resultsDiv.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Executing query...</div>';

            const params = new URLSearchParams({
                query: query
            });
            
            if (limit) params.append('limit', limit);

            const response = await fetch(`/api/datasources/${datasource}/sql?${params}`);
            const data = await response.json();
            const responseTime = performance.now() - startTime;
            
            // Log API call
            this.logApiCall('GET', `/api/datasources/${datasource}/sql`, 
                { datasource, query: query.substring(0, 100) + '...', limit }, 
                response.status, responseTime);
            
            if (response.ok) {
                this.displaySQLResults(data, resultsDiv);
                this.showAlert(`Query executed successfully in ${Math.round(responseTime)}ms`, 'success');
                this.logSystemEvent('SQL query executed successfully', 'INFO', { 
                    rows: data.data?.length || 0,
                    responseTime: Math.round(responseTime)
                });
            } else {
                resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${data.message}</div>`;
                this.showAlert(data.message || 'Query failed', 'danger');
                this.logSystemEvent('SQL query failed', 'ERROR', { error: data.message });
            }
        } catch (error) {
            resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
            this.showAlert('Query execution failed: ' + error.message, 'danger');
            this.logSystemEvent('SQL query execution error', 'ERROR', { error: error.message });
        } finally {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    }

    async handleJAQLQuery(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const datasource = formData.get('datasource');
        const jaqlQuery = formData.get('jaql');
        
        if (!datasource || !jaqlQuery) {
            this.showAlert('Please provide both datasource and JAQL query', 'warning');
            return;
        }

        const btn = e.target.querySelector('button[type="submit"]');
        const originalText = btn.textContent;
        const resultsDiv = document.getElementById('jaql-results');
        
        try {
            btn.textContent = 'Executing...';
            btn.disabled = true;
            resultsDiv.innerHTML = '<div class="spinner"></div>';

            const response = await fetch(`/api/datasources/${datasource}/jaql`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jaql: JSON.parse(jaqlQuery),
                    format: 'json'
                })
            });

            const data = await response.json();
            
            if (response.ok) {
                this.displayJAQLResults(data, resultsDiv);
                this.showAlert('JAQL query executed successfully', 'success');
            } else {
                resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${data.message}</div>`;
                this.showAlert(data.message || 'JAQL query failed', 'danger');
            }
        } catch (error) {
            resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
            this.showAlert('JAQL execution failed: ' + error.message, 'danger');
        } finally {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    }

    async handleDashboardSearch(e) {
        const searchTerm = e.target.value.trim();
        const resultsDiv = document.getElementById('dashboard-results');
        
        if (searchTerm.length < 2) {
            resultsDiv.innerHTML = '';
            return;
        }

        try {
            const response = await fetch(`/api/search/dashboards?q=${encodeURIComponent(searchTerm)}`);
            const data = await response.json();
            
            if (response.ok) {
                this.displayDashboardResults(data.data, resultsDiv);
            } else {
                resultsDiv.innerHTML = `<div class="alert alert-danger">Search failed: ${data.message}</div>`;
            }
        } catch (error) {
            resultsDiv.innerHTML = `<div class="alert alert-danger">Search error: ${error.message}</div>`;
        }
    }

    async handleModelSearch(e) {
        const searchTerm = e.target.value.trim();
        const resultsDiv = document.getElementById('model-results');
        
        if (searchTerm.length < 2) {
            resultsDiv.innerHTML = '';
            return;
        }

        try {
            const response = await fetch(`/api/search/datamodels?q=${encodeURIComponent(searchTerm)}`);
            const data = await response.json();
            
            if (response.ok) {
                this.displayModelResults(data.data, resultsDiv);
            } else {
                resultsDiv.innerHTML = `<div class="alert alert-danger">Search failed: ${data.message}</div>`;
            }
        } catch (error) {
            resultsDiv.innerHTML = `<div class="alert alert-danger">Search error: ${error.message}</div>`;
        }
    }

    async handleRefresh(e) {
        const btn = e.target;
        const originalText = btn.textContent;
        const target = btn.dataset.target;
        
        try {
            btn.textContent = 'Refreshing...';
            btn.disabled = true;
            
            // Refresh specific section based on target
            if (target === 'auth') {
                await this.checkAuthStatus();
            } else if (target === 'dashboards') {
                await this.loadDashboards();
            } else if (target === 'models') {
                await this.loadDataModels();
            }
            
            this.showAlert('Refreshed successfully', 'success');
        } catch (error) {
            this.showAlert('Refresh failed: ' + error.message, 'danger');
        } finally {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    }

    async handleExport(e) {
        const btn = e.target;
        const format = btn.dataset.format;
        const type = btn.dataset.type;
        const id = btn.dataset.id;
        
        try {
            const url = this.buildExportUrl(type, id, format);
            window.open(url, '_blank');
            this.showAlert(`Export initiated for ${type} ${id}`, 'info');
        } catch (error) {
            this.showAlert('Export failed: ' + error.message, 'danger');
        }
    }

    buildExportUrl(type, id, format) {
        if (type === 'dashboard') {
            return `/api/dashboards/${id}/export/${format}`;
        } else if (type === 'widget') {
            return `/api/widgets/${id}/export/${format}`;
        }
        throw new Error('Unknown export type');
    }

    displaySQLResults(data, container) {
        if (!data.data || data.data.length === 0) {
            container.innerHTML = '<div class="alert alert-info">No results found</div>';
            return;
        }

        let html = '<div class="table-container"><table class="table">';
        
        // Headers
        if (data.columns && data.columns.length > 0) {
            html += '<thead><tr>';
            data.columns.forEach(col => {
                html += `<th>${this.escapeHtml(col)}</th>`;
            });
            html += '</tr></thead>';
        }
        
        // Data rows
        html += '<tbody>';
        data.data.forEach(row => {
            html += '<tr>';
            if (Array.isArray(row)) {
                row.forEach(cell => {
                    html += `<td>${this.escapeHtml(String(cell))}</td>`;
                });
            } else {
                Object.values(row).forEach(cell => {
                    html += `<td>${this.escapeHtml(String(cell))}</td>`;
                });
            }
            html += '</tr>';
        });
        html += '</tbody></table></div>';
        
        container.innerHTML = html;
    }

    displayJAQLResults(data, container) {
        container.innerHTML = `<div class="code-block"><pre>${JSON.stringify(data, null, 2)}</pre></div>`;
    }

    displayDashboardResults(dashboards, container) {
        if (!dashboards || dashboards.length === 0) {
            container.innerHTML = '<div class="alert alert-info">No dashboards found</div>';
            return;
        }

        let html = '<div class="grid">';
        dashboards.forEach(dashboard => {
            html += `
                <div class="card">
                    <h3>${this.escapeHtml(dashboard.title)}</h3>
                    <p>${this.escapeHtml(dashboard.description || 'No description')}</p>
                    <div class="mt-3">
                        <a href="/dashboard/${dashboard.oid}" class="btn btn-primary btn-sm">View</a>
                        <button class="btn btn-secondary btn-sm export-btn" data-type="dashboard" data-id="${dashboard.oid}" data-format="png">Export PNG</button>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        container.innerHTML = html;
        
        // Re-attach event listeners for new buttons
        container.querySelectorAll('.export-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleExport(e));
        });
    }

    displayModelResults(models, container) {
        if (!models || models.length === 0) {
            container.innerHTML = '<div class="alert alert-info">No data models found</div>';
            return;
        }

        let html = '<div class="grid">';
        models.forEach(model => {
            html += `
                <div class="card">
                    <h3>${this.escapeHtml(model.title)}</h3>
                    <p>${this.escapeHtml(model.description || 'No description')}</p>
                    <div class="mt-2">
                        <span class="badge badge-info">${model.type || 'Unknown'}</span>
                    </div>
                    <div class="mt-3">
                        <a href="/datamodel/${model.oid}" class="btn btn-primary btn-sm">View</a>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        container.innerHTML = html;
    }

    async loadDashboards() {
        const container = document.getElementById('dashboards-list');
        if (!container) return;

        try {
            const response = await fetch('/api/dashboards');
            const data = await response.json();
            
            if (response.ok) {
                this.displayDashboardResults(data.data, container);
            } else {
                container.innerHTML = `<div class="alert alert-danger">Failed to load dashboards: ${data.message}</div>`;
            }
        } catch (error) {
            container.innerHTML = `<div class="alert alert-danger">Error loading dashboards: ${error.message}</div>`;
        }
    }

    async loadDataModels() {
        const container = document.getElementById('models-list');
        if (!container) return;

        try {
            const response = await fetch('/api/datamodels');
            const data = await response.json();
            
            if (response.ok) {
                this.displayModelResults(data.data, container);
            } else {
                container.innerHTML = `<div class="alert alert-danger">Failed to load data models: ${data.message}</div>`;
            }
        } catch (error) {
            container.innerHTML = `<div class="alert alert-danger">Error loading data models: ${error.message}</div>`;
        }
    }

    showAlert(message, type = 'info') {
        const alertsContainer = document.getElementById('alerts-container') || document.body;
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} fade-in`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        alertsContainer.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentElement) {
                alert.remove();
            }
        }, 5000);
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, (m) => map[m]);
    }

    formatDateTime(dateString) {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleString();
    }
    
    // Enhanced logging methods
    logApiCall(method, endpoint, payload = null, responseStatus = null, responseTime = null) {
        if (window.sisenseLogger) {
            window.sisenseLogger.logApiCall(method, endpoint, payload, responseStatus, responseTime);
        }
    }
    
    logUserAction(action, details = null) {
        if (window.sisenseLogger) {
            window.sisenseLogger.logUserAction(action, details);
        }
    }
    
    logSystemEvent(event, level = 'INFO', details = null) {
        if (window.sisenseLogger) {
            window.sisenseLogger.logSystemEvent(event, level, details);
        }
    }
    
    // Enhanced alert system
    showAlert(message, type = 'info', duration = 5000) {
        if (window.alertManager) {
            return window.alertManager.show(message, type, duration);
        } else {
            // Fallback to console if alert manager not available
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.sisenseUI = new SisenseUI();
});

// Utility functions
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        window.sisenseUI.showAlert('Copied to clipboard!', 'success');
    }).catch(err => {
        window.sisenseUI.showAlert('Failed to copy: ' + err.message, 'danger');
    });
}

function downloadJSON(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

function downloadCSV(data, filename) {
    if (!data || data.length === 0) return;
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => `"${row[header]}"`).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}