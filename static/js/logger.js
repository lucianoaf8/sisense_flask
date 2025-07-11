/**
 * Frontend Logger for Sisense Flask Integration v2.0
 * Handles real-time log display and communication with backend logging system
 */

class SisenseLogger {
    constructor() {
        this.logsContainer = document.getElementById('logs-content');
        this.logCount = document.getElementById('log-count');
        this.logLevelFilter = document.getElementById('log-level-filter');
        this.clearLogsBtn = document.getElementById('clear-logs');
        this.downloadLogsBtn = document.getElementById('download-logs');
        
        this.logs = [];
        this.maxLogs = 1000;
        this.isAutoScroll = true;
        this.currentFilter = 'all';
        this.logUpdateInterval = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.startLogPolling();
        this.logSystemEvent('Frontend logger initialized', 'INFO');
    }
    
    setupEventListeners() {
        // Log level filter
        if (this.logLevelFilter) {
            this.logLevelFilter.addEventListener('change', (e) => {
                this.currentFilter = e.target.value;
                this.applyFilter();
            });
        }
        
        // Clear logs button
        if (this.clearLogsBtn) {
            this.clearLogsBtn.addEventListener('click', () => this.clearLogs());
        }
        
        // Download logs button
        if (this.downloadLogsBtn) {
            this.downloadLogsBtn.addEventListener('click', () => this.downloadLogs());
        }
        
        // Auto-scroll detection
        if (this.logsContainer) {
            this.logsContainer.addEventListener('scroll', () => {
                const { scrollTop, scrollHeight, clientHeight } = this.logsContainer;
                this.isAutoScroll = scrollTop + clientHeight >= scrollHeight - 10;
            });
        }
    }
    
    startLogPolling() {
        // Poll for new logs every 2 seconds
        this.logUpdateInterval = setInterval(() => {
            this.fetchRecentLogs();
        }, 2000);
    }
    
    stopLogPolling() {
        if (this.logUpdateInterval) {
            clearInterval(this.logUpdateInterval);
            this.logUpdateInterval = null;
        }
    }
    
    async fetchRecentLogs() {
        try {
            const response = await fetch('/api/logs/recent');
            if (response.ok) {
                const data = await response.json();
                if (data.logs && data.logs.length > 0) {
                    this.addLogs(data.logs);
                }
            }
        } catch (error) {
            console.error('Failed to fetch logs:', error);
        }
    }
    
    addLog(level, message, timestamp = null, metadata = null) {
        const logEntry = {
            id: Date.now() + Math.random(),
            timestamp: timestamp || new Date().toISOString(),
            level: level.toUpperCase(),
            message: message,
            metadata: metadata || {}
        };
        
        this.logs.push(logEntry);
        
        // Trim logs if exceeding max
        if (this.logs.length > this.maxLogs) {
            this.logs = this.logs.slice(-this.maxLogs);
        }
        
        this.renderLog(logEntry);
        this.updateLogCount();
        
        // Auto-scroll if enabled
        if (this.isAutoScroll) {
            this.scrollToBottom();
        }
    }
    
    addLogs(logEntries) {
        logEntries.forEach(entry => {
            if (typeof entry === 'string') {
                // Parse log string format: "timestamp - logger - level - message"
                const parsed = this.parseLogString(entry);
                if (parsed) {
                    this.addLog(parsed.level, parsed.message, parsed.timestamp);
                }
            } else if (typeof entry === 'object') {
                this.addLog(entry.level, entry.message, entry.timestamp, entry.metadata);
            }
        });
    }
    
    parseLogString(logString) {
        try {
            // Match format: "2024-01-01 12:00:00 - module_name - LEVEL - message"
            const regex = /^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*-\s*([^-]+)\s*-\s*(\w+)\s*-\s*(.+)$/;
            const match = logString.match(regex);
            
            if (match) {
                return {
                    timestamp: match[1],
                    module: match[2].trim(),
                    level: match[3].trim(),
                    message: match[4].trim()
                };
            }
        } catch (error) {
            console.error('Failed to parse log string:', error);
        }
        return null;
    }
    
    renderLog(logEntry) {
        if (!this.logsContainer) return;
        
        const logElement = document.createElement('div');
        logElement.className = 'log-entry';
        logElement.dataset.level = logEntry.level;
        logElement.dataset.id = logEntry.id;
        
        const timestamp = this.formatTimestamp(logEntry.timestamp);
        const level = logEntry.level;
        const message = this.escapeHtml(logEntry.message);
        
        logElement.innerHTML = `
            <span class="log-timestamp">[${timestamp}]</span>
            <span class="log-level ${level.toLowerCase()}">${level}</span>
            <span class="log-message">${message}</span>
        `;
        
        // Apply current filter
        if (this.shouldShowLog(logEntry)) {
            logElement.style.display = 'flex';
        } else {
            logElement.style.display = 'none';
        }
        
        this.logsContainer.appendChild(logElement);
        
        // Animate new log entry
        requestAnimationFrame(() => {
            logElement.classList.add('fade-in');
        });
    }
    
    shouldShowLog(logEntry) {
        if (this.currentFilter === 'all') return true;
        return logEntry.level === this.currentFilter;
    }
    
    applyFilter() {
        if (!this.logsContainer) return;
        
        const logElements = this.logsContainer.querySelectorAll('.log-entry');
        let visibleCount = 0;
        
        logElements.forEach(element => {
            const level = element.dataset.level;
            if (this.currentFilter === 'all' || level === this.currentFilter) {
                element.style.display = 'flex';
                visibleCount++;
            } else {
                element.style.display = 'none';
            }
        });
        
        this.updateLogCount(visibleCount);
    }
    
    clearLogs() {
        this.logs = [];
        if (this.logsContainer) {
            this.logsContainer.innerHTML = '';
        }
        this.updateLogCount();
        this.logSystemEvent('Logs cleared by user', 'INFO');
    }
    
    async downloadLogs() {
        try {
            const response = await fetch('/api/logs/download');
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `sisense_logs_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.log`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.logUserAction('Logs downloaded');
            } else {
                throw new Error('Download failed');
            }
        } catch (error) {
            console.error('Failed to download logs:', error);
            this.logSystemEvent('Log download failed: ' + error.message, 'ERROR');
        }
    }
    
    updateLogCount(visibleCount = null) {
        if (!this.logCount) return;
        
        const total = this.logs.length;
        const visible = visibleCount !== null ? visibleCount : total;
        
        if (this.currentFilter === 'all') {
            this.logCount.textContent = `(${total})`;
        } else {
            this.logCount.textContent = `(${visible}/${total})`;
        }
    }
    
    scrollToBottom() {
        if (this.logsContainer) {
            this.logsContainer.scrollTop = this.logsContainer.scrollHeight;
        }
    }
    
    formatTimestamp(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleTimeString('en-US', { 
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch (error) {
            return timestamp;
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Public logging methods
    logApiCall(method, endpoint, payload = null, responseStatus = null, responseTime = null) {
        const message = `API ${method} ${endpoint}${responseStatus ? ` - ${responseStatus}` : ''}${responseTime ? ` (${responseTime}ms)` : ''}`;
        this.addLog('INFO', message, null, {
            type: 'api_call',
            method,
            endpoint,
            payload,
            responseStatus,
            responseTime
        });
        
        // Send to backend
        this.sendLogToBackend('api_call', message, {
            method,
            endpoint,
            payload,
            responseStatus,
            responseTime
        });
    }
    
    logUserAction(action, details = null) {
        const message = `User Action: ${action}${details ? ` - ${JSON.stringify(details)}` : ''}`;
        this.addLog('INFO', message, null, {
            type: 'user_action',
            action,
            details
        });
        
        // Send to backend
        this.sendLogToBackend('user_action', message, { action, details });
    }
    
    logSystemEvent(event, level = 'INFO', details = null) {
        const message = `System: ${event}${details ? ` - ${JSON.stringify(details)}` : ''}`;
        this.addLog(level, message, null, {
            type: 'system_event',
            event,
            details
        });
        
        // Send to backend
        this.sendLogToBackend('system_event', message, { event, level, details });
    }
    
    async sendLogToBackend(type, message, metadata) {
        try {
            await fetch('/api/logs/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    type,
                    message,
                    metadata,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (error) {
            console.error('Failed to send log to backend:', error);
        }
    }
}

// Enhanced alert system
class AlertManager {
    constructor() {
        this.alertsContainer = document.getElementById('alerts-container');
        this.alerts = [];
        this.maxAlerts = 5;
    }
    
    show(message, type = 'info', duration = 5000) {
        const alert = this.createAlert(message, type);
        this.addAlert(alert);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                this.removeAlert(alert);
            }, duration);
        }
        
        // Log alert
        if (window.sisenseLogger) {
            window.sisenseLogger.logSystemEvent(`Alert shown: ${message}`, type.toUpperCase());
        }
        
        return alert;
    }
    
    createAlert(message, type) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} fade-in`;
        
        const icon = this.getIconForType(type);
        alert.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${this.escapeHtml(message)}</span>
            <button class="alert-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        return alert;
    }
    
    addAlert(alert) {
        if (!this.alertsContainer) return;
        
        this.alerts.push(alert);
        this.alertsContainer.appendChild(alert);
        
        // Remove oldest alerts if exceeding max
        while (this.alerts.length > this.maxAlerts) {
            const oldAlert = this.alerts.shift();
            this.removeAlert(oldAlert);
        }
    }
    
    removeAlert(alert) {
        if (alert && alert.parentElement) {
            alert.classList.add('fade-out');
            setTimeout(() => {
                if (alert.parentElement) {
                    alert.parentElement.removeChild(alert);
                }
                const index = this.alerts.indexOf(alert);
                if (index > -1) {
                    this.alerts.splice(index, 1);
                }
            }, 300);
        }
    }
    
    getIconForType(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Connection status monitor
class ConnectionStatusMonitor {
    constructor() {
        this.statusIndicator = document.getElementById('status-indicator');
        this.statusText = document.getElementById('status-text');
        this.isConnected = false;
        this.checkInterval = null;
        
        this.init();
    }
    
    init() {
        this.startMonitoring();
        this.checkStatus(); // Initial check
    }
    
    startMonitoring() {
        this.checkInterval = setInterval(() => {
            this.checkStatus();
        }, 30000); // Check every 30 seconds
    }
    
    stopMonitoring() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    }
    
    async checkStatus() {
        try {
            const response = await fetch('/api/auth/validate');
            const data = await response.json();
            
            if (data.valid) {
                this.setStatus('connected', 'Connected');
            } else {
                this.setStatus('disconnected', 'Disconnected');
            }
        } catch (error) {
            this.setStatus('disconnected', 'Connection Error');
            console.error('Status check failed:', error);
        }
    }
    
    setStatus(status, text) {
        const wasConnected = this.isConnected;
        this.isConnected = (status === 'connected');
        
        if (this.statusIndicator) {
            this.statusIndicator.className = `fas fa-circle status-indicator ${status}`;
        }
        
        if (this.statusText) {
            this.statusText.textContent = text;
        }
        
        // Log status changes
        if (wasConnected !== this.isConnected) {
            if (window.sisenseLogger) {
                window.sisenseLogger.logSystemEvent(
                    `Connection status changed to: ${text}`,
                    this.isConnected ? 'INFO' : 'WARNING'
                );
            }
            
            if (window.alertManager) {
                window.alertManager.show(
                    `Connection ${this.isConnected ? 'restored' : 'lost'}`,
                    this.isConnected ? 'success' : 'warning'
                );
            }
        }
    }
}

// Initialize all systems when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize logger
    window.sisenseLogger = new SisenseLogger();
    
    // Initialize alert manager
    window.alertManager = new AlertManager();
    
    // Initialize connection monitor
    window.connectionMonitor = new ConnectionStatusMonitor();
    
    // Set up global error handling
    window.addEventListener('error', (event) => {
        if (window.sisenseLogger) {
            window.sisenseLogger.logSystemEvent(
                `JavaScript Error: ${event.error.message}`,
                'ERROR',
                {
                    filename: event.filename,
                    lineno: event.lineno,
                    colno: event.colno,
                    stack: event.error.stack
                }
            );
        }
    });
    
    // Set up unhandled promise rejection handling
    window.addEventListener('unhandledrejection', (event) => {
        if (window.sisenseLogger) {
            window.sisenseLogger.logSystemEvent(
                `Unhandled Promise Rejection: ${event.reason}`,
                'ERROR'
            );
        }
    });
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.sisenseLogger) {
        window.sisenseLogger.stopLogPolling();
    }
    
    if (window.connectionMonitor) {
        window.connectionMonitor.stopMonitoring();
    }
});
