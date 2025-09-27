// Offline Mode Toggle for Frontend
// Provides easy controls to switch between online and offline modes

class OfflineModeToggle {
    constructor() {
        this.isOfflineMode = this.getOfflineStatus();
        this.init();
    }

    init() {
        this.createToggleButton();
        this.updateUI();
        this.bindEvents();
    }

    // Create floating toggle button
    createToggleButton() {
        // Remove existing toggle if present
        const existingToggle = document.getElementById('offline-mode-toggle');
        if (existingToggle) {
            existingToggle.remove();
        }

        const toggleContainer = document.createElement('div');
        toggleContainer.id = 'offline-mode-toggle';
        toggleContainer.className = 'offline-toggle-container';
        toggleContainer.innerHTML = `
            <div class="toggle-button" id="toggle-btn">
                <div class="toggle-icon">
                    <i class="fas fa-wifi" id="connection-icon"></i>
                </div>
                <div class="toggle-text">
                    <span id="connection-status">Online</span>
                </div>
            </div>
            <div class="toggle-dropdown" id="toggle-dropdown" style="display: none;">
                <div class="dropdown-header">
                    <strong>Connection Mode</strong>
                </div>
                <div class="dropdown-option" id="option-online">
                    <i class="fas fa-wifi"></i>
                    <span>Online Mode</span>
                    <small>Full functionality</small>
                </div>
                <div class="dropdown-option" id="option-offline">
                    <i class="fas fa-wifi-slash"></i>
                    <span>Offline Mode</span>
                    <small>Limited features</small>
                </div>
                <div class="dropdown-divider"></div>
                <div class="dropdown-option" id="option-test-offline">
                    <i class="fas fa-flask"></i>
                    <span>Test Offline</span>
                    <small>For development</small>
                </div>
            </div>
        `;

        // Add CSS styles
        this.addToggleStyles();

        document.body.appendChild(toggleContainer);
    }

    addToggleStyles() {
        // Check if styles already exist
        if (document.getElementById('offline-toggle-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'offline-toggle-styles';
        styles.textContent = `
            .offline-toggle-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }

            .toggle-button {
                background: #ffffff;
                border: 2px solid #e1e5e9;
                border-radius: 12px;
                padding: 8px 12px;
                display: flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                transition: all 0.2s ease;
                min-width: 100px;
            }

            .toggle-button:hover {
                border-color: #007bff;
                box-shadow: 0 6px 16px rgba(0,0,0,0.15);
            }

            .toggle-button.offline {
                border-color: #dc3545;
                background: #fff5f5;
            }

            .toggle-button.offline .toggle-icon i {
                color: #dc3545;
            }

            .toggle-icon i {
                font-size: 16px;
                color: #28a745;
                transition: color 0.2s ease;
            }

            .toggle-text {
                font-size: 14px;
                font-weight: 500;
                color: #333;
            }

            .toggle-dropdown {
                position: absolute;
                top: 100%;
                right: 0;
                margin-top: 8px;
                background: white;
                border: 1px solid #e1e5e9;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.15);
                min-width: 200px;
                overflow: hidden;
            }

            .dropdown-header {
                padding: 12px 16px;
                background: #f8f9fa;
                border-bottom: 1px solid #e1e5e9;
                font-size: 12px;
                font-weight: 600;
                color: #6c757d;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .dropdown-option {
                padding: 12px 16px;
                display: flex;
                align-items: center;
                gap: 12px;
                cursor: pointer;
                transition: background-color 0.2s ease;
                border-bottom: 1px solid #f8f9fa;
            }

            .dropdown-option:hover {
                background: #f8f9fa;
            }

            .dropdown-option:last-child {
                border-bottom: none;
            }

            .dropdown-option i {
                width: 16px;
                font-size: 14px;
                color: #6c757d;
            }

            .dropdown-option span {
                font-size: 14px;
                font-weight: 500;
                color: #333;
            }

            .dropdown-option small {
                font-size: 12px;
                color: #6c757d;
                margin-left: auto;
            }

            .dropdown-option.active {
                background: #e3f2fd;
                border-left: 3px solid #2196f3;
            }

            .dropdown-divider {
                height: 1px;
                background: #e1e5e9;
                margin: 8px 0;
            }

            @media (max-width: 768px) {
                .offline-toggle-container {
                    top: 10px;
                    right: 10px;
                }

                .toggle-button {
                    padding: 6px 10px;
                    min-width: 80px;
                }

                .toggle-dropdown {
                    min-width: 180px;
                }
            }
        `;

        document.head.appendChild(styles);
    }

    bindEvents() {
        // Toggle dropdown
        document.getElementById('toggle-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown();
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            this.closeDropdown();
        });

        // Option clicks
        document.getElementById('option-online').addEventListener('click', () => {
            this.switchToOnline();
        });

        document.getElementById('option-offline').addEventListener('click', () => {
            this.switchToOffline();
        });

        document.getElementById('option-test-offline').addEventListener('click', () => {
            this.testOfflineMode();
        });
    }

    toggleDropdown() {
        const dropdown = document.getElementById('toggle-dropdown');
        const isVisible = dropdown.style.display !== 'none';

        if (isVisible) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }

    openDropdown() {
        const dropdown = document.getElementById('toggle-dropdown');
        dropdown.style.display = 'block';

        // Update active option
        this.updateActiveOption();
    }

    closeDropdown() {
        const dropdown = document.getElementById('toggle-dropdown');
        dropdown.style.display = 'none';
    }

    updateActiveOption() {
        // Remove active class from all options
        document.querySelectorAll('.dropdown-option').forEach(option => {
            option.classList.remove('active');
        });

        // Add active class to current mode
        const activeOptionId = this.isOfflineMode ? 'option-offline' : 'option-online';
        document.getElementById(activeOptionId).classList.add('active');
    }

    async switchToOnline() {
        try {
            // Call API to enable online mode
            const response = await fetch('/api/force-online/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                this.isOfflineMode = false;
                this.updateUI();
                this.closeDropdown();
                this.showNotification('Online mode enabled', 'success');

                // Reload page to apply online mode
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } catch (error) {
            console.error('Failed to switch to online mode:', error);
            this.showNotification('Failed to switch to online mode', 'error');
        }
    }

    async switchToOffline() {
        try {
            // Call API to enable offline mode
            const response = await fetch('/api/force-offline/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                this.isOfflineMode = true;
                this.updateUI();
                this.closeDropdown();
                this.showNotification('Offline mode enabled', 'warning');

                // Redirect to offline version of current page
                this.redirectToOfflineVersion();
            }
        } catch (error) {
            console.error('Failed to switch to offline mode:', error);
            this.showNotification('Failed to switch to offline mode', 'error');
        }
    }

    testOfflineMode() {
        // Force offline mode using JavaScript (no server call)
        this.isOfflineMode = true;
        this.updateUI();
        this.closeDropdown();

        // Use the offline redirect manager if available
        if (window.offlineRedirectManager) {
            window.offlineRedirectManager.forceOfflineMode();
        }

        this.showNotification('Test offline mode activated', 'info');

        // Redirect to offline version after a delay
        setTimeout(() => {
            this.redirectToOfflineVersion();
        }, 1500);
    }

    redirectToOfflineVersion() {
        const currentPath = window.location.pathname;

        // Define redirect mappings
        const offlineRoutes = {
            '/checkout/shop/': '/checkout/direct/',
            '/products/': '/offline/',
            '/search/': '/offline/',
            '/shop/': '/offline/'
        };

        // Find matching route
        for (const [pattern, offlineUrl] of Object.entries(offlineRoutes)) {
            if (currentPath.includes(pattern.replace(/\/$/, ''))) {
                // Preserve shop ID if present
                const shopMatch = currentPath.match(/shop\/([^\/]+)/);
                if (shopMatch && offlineUrl.includes('direct')) {
                    const finalUrl = `${offlineUrl.replace(/\/$/, '')}/${shopMatch[1]}/`;
                    window.location.href = finalUrl;
                    return;
                }

                window.location.href = offlineUrl;
                return;
            }
        }

        // Default to offline page
        window.location.href = '/offline/';
    }

    updateUI() {
        const toggleBtn = document.getElementById('toggle-btn');
        const connectionIcon = document.getElementById('connection-icon');
        const connectionStatus = document.getElementById('connection-status');

        if (this.isOfflineMode) {
            toggleBtn.classList.add('offline');
            connectionIcon.className = 'fas fa-wifi-slash';
            connectionStatus.textContent = 'Offline';
        } else {
            toggleBtn.classList.remove('offline');
            connectionIcon.className = 'fas fa-wifi';
            connectionStatus.textContent = 'Online';
        }
    }

    getOfflineStatus() {
        // Check various indicators for offline mode
        const urlParams = new URLSearchParams(window.location.search);
        const isOfflineParam = urlParams.get('offline') === 'true';
        const isOfflinePage = window.location.pathname.includes('/offline/');
        const isDirectCheckout = window.location.pathname.includes('/checkout/direct/');

        return isOfflineParam || isOfflinePage || isDirectCheckout;
    }

    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value :
               document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    showNotification(message, type = 'info') {
        // Create notification
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} notification-toast`;
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 10000;
            min-width: 250px;
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideInRight 0.3s ease;
        `;

        const iconMap = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-circle',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle'
        };

        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <i class="${iconMap[type] || iconMap.info}"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }
}

// Add CSS animation
const animationStyles = document.createElement('style');
animationStyles.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(animationStyles);

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.offlineModeToggle = new OfflineModeToggle();
    });
} else {
    window.offlineModeToggle = new OfflineModeToggle();
}