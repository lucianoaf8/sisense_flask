/**
 * Panel management for Sisense Flask Integration v2.0
 * Handles sidebar, right panel, and logs panel interactions
 */

class PanelManager {
    constructor() {
        this.leftSidebar = document.getElementById('left-sidebar');
        this.rightPanel = document.getElementById('right-panel');
        this.logsPanel = document.getElementById('logs-panel');
        this.overlay = document.getElementById('overlay');
        this.appLayout = document.querySelector('.app-layout');
        
        this.isLeftSidebarCollapsed = false;
        this.isRightPanelHidden = false;
        this.isLogsPanelExpanded = false;
        this.isMobile = window.innerWidth <= 768;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.updateActiveNavigation();
        this.loadPanelState();
        
        // Initialize data sources and elasticubes
        this.loadDataSources();
        this.loadElasticubes();
        
        // Update system stats
        this.updateSystemStats();
        setInterval(() => this.updateSystemStats(), 30000); // Update every 30 seconds
    }
    
    setupEventListeners() {
        // Sidebar toggle
        const sidebarToggle = document.getElementById('sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => this.toggleLeftSidebar());
        }
        
        // Right panel toggle
        const rightPanelToggle = document.getElementById('right-panel-toggle');
        if (rightPanelToggle) {
            rightPanelToggle.addEventListener('click', () => this.toggleRightPanel());
        }
        
        // Logs panel toggle
        const logsToggle = document.getElementById('logs-toggle');
        const logsHeader = document.querySelector('.logs-header');
        if (logsToggle) {
            logsToggle.addEventListener('click', () => this.toggleLogsPanel());
        }
        if (logsHeader) {
            logsHeader.addEventListener('click', () => this.toggleLogsPanel());
        }
        
        // Overlay click (mobile)
        if (this.overlay) {
            this.overlay.addEventListener('click', () => this.closeAllPanels());
        }
        
        // Window resize
        window.addEventListener('resize', () => this.handleResize());
        
        // Navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => this.handleNavigation(e));
        });
        
        // Fuzzy search threshold slider
        const fuzzyThreshold = document.getElementById('fuzzy-threshold');
        const thresholdValue = document.getElementById('threshold-value');
        if (fuzzyThreshold && thresholdValue) {
            fuzzyThreshold.addEventListener('input', (e) => {
                thresholdValue.textContent = e.target.value;
                this.updateFuzzyThreshold(parseInt(e.target.value));
            });
        }
        
        // Global search
        const globalSearch = document.getElementById('global-search');
        if (globalSearch) {
            globalSearch.addEventListener('input', (e) => this.handleGlobalSearch(e.target.value));
        }
    }
    
    toggleLeftSidebar() {
        this.isLeftSidebarCollapsed = !this.isLeftSidebarCollapsed;
        
        if (this.isMobile) {
            this.leftSidebar.classList.toggle('open');
            this.overlay.classList.toggle('active');
        } else {
            this.leftSidebar.classList.toggle('collapsed');
            this.appLayout.classList.toggle('sidebar-collapsed');
        }
        
        this.savePanelState();
    }
    
    toggleRightPanel() {
        this.isRightPanelHidden = !this.isRightPanelHidden;
        this.rightPanel.classList.toggle('collapsed');
        this.appLayout.classList.toggle('right-panel-hidden');
        
        // Update toggle icon
        const toggleIcon = document.querySelector('#right-panel-toggle i');
        if (toggleIcon) {
            toggleIcon.className = this.isRightPanelHidden ? 'fas fa-chevron-left' : 'fas fa-chevron-right';
        }
        
        this.savePanelState();
    }
    
    toggleLogsPanel() {
        this.isLogsPanelExpanded = !this.isLogsPanelExpanded;
        this.logsPanel.classList.toggle('expanded');
        
        // Update toggle icon
        const toggleIcon = document.querySelector('#logs-toggle i');
        if (toggleIcon) {
            toggleIcon.parentElement.classList.toggle('expanded');
        }
        
        // Adjust app layout margin
        const appLayout = document.querySelector('.app-layout');
        if (appLayout) {
            const margin = this.isLogsPanelExpanded ? 'var(--logs-panel-height)' : 'var(--logs-panel-collapsed-height)';
            appLayout.style.marginBottom = margin;
        }
        
        this.savePanelState();
    }
    
    closeAllPanels() {
        if (this.isMobile && this.leftSidebar.classList.contains('open')) {
            this.leftSidebar.classList.remove('open');
            this.overlay.classList.remove('active');
        }
    }
    
    handleResize() {
        const wasMobile = this.isMobile;
        this.isMobile = window.innerWidth <= 768;
        
        if (wasMobile !== this.isMobile) {
            // Reset classes when switching between mobile and desktop
            if (this.isMobile) {
                this.leftSidebar.classList.remove('collapsed');
                this.appLayout.classList.remove('sidebar-collapsed');
            } else {
                this.leftSidebar.classList.remove('open');
                this.overlay.classList.remove('active');
            }
        }
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
    
    handleNavigation(e) {
        // Log navigation
        if (window.sisenseLogger) {
            window.sisenseLogger.logUserAction('navigation', {
                from: window.location.pathname,
                to: e.target.getAttribute('href'),
                section: e.target.dataset.section
            });
        }
        
        // Close mobile sidebar after navigation
        if (this.isMobile) {
            setTimeout(() => this.closeAllPanels(), 100);
        }
    }
    
    updateFuzzyThreshold(value) {
        // Store fuzzy search threshold
        localStorage.setItem('fuzzy-threshold', value.toString());
        
        // Trigger global search update if there's a current search
        const globalSearch = document.getElementById('global-search');
        if (globalSearch && globalSearch.value.trim()) {
            this.handleGlobalSearch(globalSearch.value);
        }
        
        // Log threshold change
        if (window.sisenseLogger) {
            window.sisenseLogger.logUserAction('fuzzy_threshold_changed', { threshold: value });
        }
    }
    
    handleGlobalSearch(query) {
        if (query.length < 2) {
            this.clearSearchResults();
            return;
        }
        
        const threshold = parseInt(document.getElementById('fuzzy-threshold').value);
        
        // Log search action
        if (window.sisenseLogger) {
            window.sisenseLogger.logUserAction('global_search', { 
                query: query, 
                threshold: threshold 
            });
        }
        
        // Implement fuzzy search across different sections
        this.performGlobalSearch(query, threshold);
    }
    
    async performGlobalSearch(query, threshold) {
        try {
            // Search dashboards
            const dashboardsResponse = await fetch(`/api/search/dashboards?q=${encodeURIComponent(query)}`);
            if (dashboardsResponse.ok) {
                const dashboards = await dashboardsResponse.json();
                this.updateSearchResults('dashboards', dashboards.data);
            }
            
            // Search data models
            const modelsResponse = await fetch(`/api/search/datamodels?q=${encodeURIComponent(query)}`);
            if (modelsResponse.ok) {
                const models = await modelsResponse.json();
                this.updateSearchResults('models', models.data);
            }
            
        } catch (error) {
            console.error('Global search failed:', error);
            if (window.sisenseLogger) {
                window.sisenseLogger.logSystemEvent('global_search_error', 'ERROR', { error: error.message });
            }
        }
    }
    
    updateSearchResults(type, results) {
        // Update search results in the right panel
        // This would need to be implemented based on specific UI requirements
        console.log(`Search results for ${type}:`, results);
    }
    
    clearSearchResults() {
        // Clear search results displays
    }
    
    async loadDataSources() {
        try {
            const response = await fetch('/api/connections');
            if (response.ok) {
                const data = await response.json();
                this.displayDataSources(data.data || []);
            } else {
                this.displayDataSourcesError('Failed to load data sources');
            }
        } catch (error) {
            console.error('Failed to load data sources:', error);
            this.displayDataSourcesError('Connection error');
        }
    }
    
    displayDataSources(dataSources) {
        const container = document.getElementById('data-sources-list');
        if (!container) return;
        
        if (dataSources.length === 0) {
            container.innerHTML = '<div class="no-data">No data sources found</div>';
            return;
        }
        
        const html = dataSources.slice(0, 5).map(ds => `
            <div class="data-source-item" data-id="${ds.id}" onclick="selectDataSource('${ds.id}')">
                <div class="ds-name">${ds.name || ds.id}</div>
                <div class="ds-type">${ds.type || 'Unknown'}</div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    displayDataSourcesError(message) {
        const container = document.getElementById('data-sources-list');
        if (container) {
            container.innerHTML = `<div class="error-message">${message}</div>`;
        }
    }
    
    async loadElasticubes() {
        try {
            const response = await fetch('/api/datamodels');
            if (response.ok) {
                const data = await response.json();
                this.displayElasticubes(data.data || []);
            } else {
                this.displayElasticubesError('Failed to load elasticubes');
            }
        } catch (error) {
            console.error('Failed to load elasticubes:', error);
            this.displayElasticubesError('Connection error');
        }
    }
    
    displayElasticubes(elasticubes) {
        const container = document.getElementById('elasticubes-list');
        if (!container) return;
        
        if (elasticubes.length === 0) {
            container.innerHTML = '<div class="no-data">No elasticubes found</div>';
            return;
        }
        
        const html = elasticubes.slice(0, 5).map(ec => `
            <div class="elasticube-item" data-id="${ec.oid}" onclick="selectElasticube('${ec.oid}')">
                <div class="ec-name">${ec.title}</div>
                <div class="ec-type">${ec.type || 'Unknown'}</div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    displayElasticubesError(message) {
        const container = document.getElementById('elasticubes-list');
        if (container) {
            container.innerHTML = `<div class="error-message">${message}</div>`;
        }
    }
    
    updateSystemStats() {
        // Update uptime
        const uptimeElement = document.getElementById('uptime');
        if (uptimeElement) {
            const startTime = sessionStorage.getItem('app-start-time') || Date.now();
            const uptime = Date.now() - parseInt(startTime);
            const hours = Math.floor(uptime / (1000 * 60 * 60));
            const minutes = Math.floor((uptime % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((uptime % (1000 * 60)) / 1000);
            uptimeElement.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
        
        // Update memory usage (approximate)
        const memoryElement = document.getElementById('memory-usage');
        if (memoryElement && 'memory' in performance) {
            const memory = (performance.memory.usedJSHeapSize / 1024 / 1024).toFixed(1);
            memoryElement.textContent = `${memory} MB`;
        }
    }
    
    savePanelState() {
        const state = {
            leftSidebarCollapsed: this.isLeftSidebarCollapsed,
            rightPanelHidden: this.isRightPanelHidden,
            logsPanelExpanded: this.isLogsPanelExpanded
        };
        localStorage.setItem('panel-state', JSON.stringify(state));
    }
    
    loadPanelState() {
        try {
            const savedState = localStorage.getItem('panel-state');
            if (savedState) {
                const state = JSON.parse(savedState);
                
                if (state.leftSidebarCollapsed && !this.isMobile) {
                    this.isLeftSidebarCollapsed = true;
                    this.leftSidebar.classList.add('collapsed');
                    this.appLayout.classList.add('sidebar-collapsed');
                }
                
                if (state.rightPanelHidden) {
                    this.isRightPanelHidden = true;
                    this.rightPanel.classList.add('collapsed');
                    this.appLayout.classList.add('right-panel-hidden');
                    const toggleIcon = document.querySelector('#right-panel-toggle i');
                    if (toggleIcon) {
                        toggleIcon.className = 'fas fa-chevron-left';
                    }
                }
                
                if (state.logsPanelExpanded) {
                    this.isLogsPanelExpanded = true;
                    this.logsPanel.classList.add('expanded');
                    const toggleIcon = document.querySelector('#logs-toggle i');
                    if (toggleIcon) {
                        toggleIcon.parentElement.classList.add('expanded');
                    }
                }
            }
            
            // Load fuzzy threshold
            const savedThreshold = localStorage.getItem('fuzzy-threshold');
            if (savedThreshold) {
                const slider = document.getElementById('fuzzy-threshold');
                const value = document.getElementById('threshold-value');
                if (slider && value) {
                    slider.value = savedThreshold;
                    value.textContent = savedThreshold;
                }
            }
            
        } catch (error) {
            console.error('Failed to load panel state:', error);
        }
    }
}

// Global functions for data source and elasticube selection
window.selectDataSource = function(id) {
    console.log('Selected data source:', id);
    if (window.sisenseLogger) {
        window.sisenseLogger.logUserAction('data_source_selected', { id: id });
    }
    
    // Highlight selected item
    document.querySelectorAll('.data-source-item').forEach(item => {
        item.classList.remove('selected');
    });
    document.querySelector(`[data-id="${id}"]`).classList.add('selected');
    
    // Store selection
    sessionStorage.setItem('selected-data-source', id);
};

window.selectElasticube = function(id) {
    console.log('Selected elasticube:', id);
    if (window.sisenseLogger) {
        window.sisenseLogger.logUserAction('elasticube_selected', { id: id });
    }
    
    // Highlight selected item
    document.querySelectorAll('.elasticube-item').forEach(item => {
        item.classList.remove('selected');
    });
    document.querySelector(`[data-id="${id}"]`).classList.add('selected');
    
    // Store selection
    sessionStorage.setItem('selected-elasticube', id);
};

window.refreshDataSources = function() {
    if (window.panelManager) {
        window.panelManager.loadDataSources();
    }
};

window.refreshElasticubes = function() {
    if (window.panelManager) {
        window.panelManager.loadElasticubes();
    }
};

// Initialize panel manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.panelManager = new PanelManager();
    
    // Set app start time for uptime calculation
    if (!sessionStorage.getItem('app-start-time')) {
        sessionStorage.setItem('app-start-time', Date.now().toString());
    }
});
