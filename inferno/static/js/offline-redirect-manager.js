// Offline Redirect Manager
// Handles dynamic redirects to offline URLs based on user context and connection status

class OfflineRedirectManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.currentPath = window.location.pathname;
        this.currentParams = new URLSearchParams(window.location.search);
        this.offlineRoutes = this.initializeOfflineRoutes();
        this.userContext = this.getUserContext();

        this.init();
    }

    init() {
        this.setupConnectionMonitoring();
        this.handleInitialLoad();
        this.setupFormInterception();
        this.setupLinkInterception();
    }

    // Initialize offline route mappings
    initializeOfflineRoutes() {
        return {
            // Checkout routes
            '/checkout/shop/': {
                offline: '/checkout/direct/',
                preserveParams: true,
                context: 'checkout'
            },

            // Product browsing
            '/products/': {
                offline: '/offline/',
                preserveParams: false,
                context: 'products',
                fallback: 'cached_products'
            },

            // Shop pages
            '/shop/': {
                offline: '/offline/',
                preserveParams: false,
                context: 'shop',
                fallback: 'cached_shop'
            },

            // Cart functionality
            '/cart/': {
                offline: '/offline/',
                preserveParams: false,
                context: 'cart',
                fallback: 'offline_cart'
            },

            // Search functionality
            '/search/': {
                offline: '/offline/',
                preserveParams: false,
                context: 'search',
                fallback: 'cached_search'
            },

            // User profile (requires auth)
            '/profile/': {
                offline: '/offline/',
                preserveParams: false,
                context: 'profile',
                requiresAuth: true
            },

            // Payment processing
            '/payment/': {
                offline: '/checkout/direct/',
                preserveParams: true,
                context: 'payment',
                message: 'Only Cash on Delivery available offline'
            }
        };
    }

    // Get user context information
    getUserContext() {
        return {
            isAuthenticated: this.checkAuthStatus(),
            hasCart: this.checkCartStatus(),
            currentShop: this.getCurrentShopId(),
            language: this.getCurrentLanguage(),
            savedAddresses: this.getSavedAddresses()
        };
    }

    checkAuthStatus() {
        // Check if user is logged in
        return document.querySelector('meta[name="user-authenticated"]')?.content === 'true' ||
               document.body.classList.contains('authenticated') ||
               localStorage.getItem('user_authenticated') === 'true';
    }

    checkCartStatus() {
        // Check if user has items in cart
        const cartCount = document.querySelector('.cart-count');
        return cartCount && parseInt(cartCount.textContent) > 0;
    }

    getCurrentShopId() {
        // Extract shop ID from current URL or context
        const shopMatch = this.currentPath.match(/shop\/([^\/]+)/);
        return shopMatch ? shopMatch[1] : null;
    }

    getCurrentLanguage() {
        return document.documentElement.lang || 'en';
    }

    getSavedAddresses() {
        try {
            return JSON.parse(localStorage.getItem('direct_saved_addresses') || '[]');
        } catch {
            return [];
        }
    }

    // Setup connection monitoring
    setupConnectionMonitoring() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.handleConnectionRestore();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.handleConnectionLoss();
        });

        // Check connection periodically
        setInterval(() => {
            this.checkConnection();
        }, 5000);
    }

    // Check actual connection (not just navigator.onLine)
    async checkConnection() {
        try {
            // Use AbortController for timeout instead of deprecated timeout option
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000);

            const response = await fetch('/api/ping/', {
                method: 'HEAD',
                cache: 'no-cache',
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            const wasOnline = this.isOnline;
            this.isOnline = response.ok;

            if (wasOnline !== this.isOnline) {
                if (this.isOnline) {
                    this.handleConnectionRestore();
                } else {
                    this.handleConnectionLoss();
                }
            }
        } catch (error) {
            // Handle both network errors and aborted requests
            if (this.isOnline) {
                this.isOnline = false;
                this.handleConnectionLoss();
            }
        }
    }

    // Handle initial page load
    handleInitialLoad() {
        if (!this.isOnline) {
            this.redirectToOfflineVersion();
        }
    }

    // Handle connection loss
    handleConnectionLoss() {
        console.log('Connection lost - checking for offline redirect');
        this.showOfflineNotification();

        // Don't redirect immediately, give user choice
        setTimeout(() => {
            if (!this.isOnline) {
                this.offerOfflineRedirect();
            }
        }, 3000);
    }

    // Handle connection restoration
    handleConnectionRestore() {
        console.log('Connection restored');
        this.hideOfflineNotification();
        this.showReconnectionNotification();

        // Sync offline data if available
        if (window.offlineManager) {
            window.offlineManager.syncOfflineData();
        }
    }

    // Redirect to offline version of current page
    redirectToOfflineVersion() {
        const offlineRoute = this.findOfflineRoute(this.currentPath);

        if (offlineRoute) {
            const offlineUrl = this.buildOfflineUrl(offlineRoute);

            if (offlineUrl !== this.currentPath) {
                console.log(`Redirecting to offline version: ${offlineUrl}`);
                this.performRedirect(offlineUrl, offlineRoute.context);
            }
        } else {
            // Default offline page
            this.performRedirect('/offline/', 'general');
        }
    }

    // Find matching offline route
    findOfflineRoute(path) {
        for (const [pattern, route] of Object.entries(this.offlineRoutes)) {
            if (path.startsWith(pattern) || this.matchesPattern(path, pattern)) {
                return { ...route, pattern };
            }
        }
        return null;
    }

    // Check if path matches pattern
    matchesPattern(path, pattern) {
        // Convert pattern to regex
        const regexPattern = pattern
            .replace(/\//g, '\\/')
            .replace(/\*/g, '.*')
            .replace(/:([^\/]+)/g, '([^\/]+)');

        const regex = new RegExp(`^${regexPattern}`);
        return regex.test(path);
    }

    // Build offline URL with context
    buildOfflineUrl(route) {
        let offlineUrl = route.offline;

        // Preserve shop ID for checkout routes
        if (route.preserveParams && this.userContext.currentShop) {
            offlineUrl = offlineUrl.replace(/\/$/, '') + this.userContext.currentShop + '/';
        }

        // Add query parameters for context
        const params = new URLSearchParams();

        if (route.context) {
            params.set('context', route.context);
        }

        if (route.message) {
            params.set('message', route.message);
        }

        if (this.currentParams.has('sid')) {
            params.set('sid', this.currentParams.get('sid'));
        }

        if (params.toString()) {
            offlineUrl += '?' + params.toString();
        }

        return offlineUrl;
    }

    // Perform redirect with user notification
    performRedirect(url, context) {
        const message = this.getRedirectMessage(context);

        // Show notification before redirect
        this.showRedirectNotification(message, () => {
            window.location.href = url;
        });
    }

    // Get appropriate redirect message
    getRedirectMessage(context) {
        const messages = {
            checkout: 'Redirecting to offline checkout. You can still place Cash on Delivery orders.',
            products: 'Redirecting to offline mode. You can browse cached products.',
            cart: 'Redirecting to offline cart. Your items are saved locally.',
            search: 'Redirecting to offline mode. Search in cached content.',
            profile: 'Redirecting to offline mode. Limited profile features available.',
            payment: 'Redirecting to offline checkout. Only Cash on Delivery available.',
            general: 'Redirecting to offline mode. Limited features available.'
        };

        return messages[context] || messages.general;
    }

    // Setup form submission interception
    setupFormInterception() {
        document.addEventListener('submit', (e) => {
            if (!this.isOnline) {
                this.handleOfflineFormSubmission(e);
            }
        });
    }

    // Handle form submissions when offline
    handleOfflineFormSubmission(event) {
        const form = event.target;
        const action = form.action || form.getAttribute('action');

        // Check if this is a checkout or payment form
        if (action && (action.includes('checkout') || action.includes('payment'))) {
            event.preventDefault();

            // Redirect to offline checkout
            const shopId = this.extractShopIdFromForm(form);
            const offlineUrl = shopId ? `/checkout/direct/${shopId}/` : '/checkout/direct/shop-1/';

            this.showOfflineFormMessage(() => {
                window.location.href = offlineUrl;
            });
        }
    }

    // Extract shop ID from form data
    extractShopIdFromForm(form) {
        const shopInput = form.querySelector('input[name="shop_id"]') ||
                         form.querySelector('input[name="sid"]');
        return shopInput ? shopInput.value : null;
    }

    // Setup link interception
    setupLinkInterception() {
        document.addEventListener('click', (e) => {
            if (!this.isOnline) {
                this.handleOfflineLinkClick(e);
            }
        });
    }

    // Handle link clicks when offline
    handleOfflineLinkClick(event) {
        const link = event.target.closest('a');
        if (!link) return;

        const href = link.href;
        if (!href || href.startsWith('javascript:') || href.startsWith('#')) return;

        // Check if this link requires online functionality
        const requiresOnline = this.linkRequiresOnline(href);

        if (requiresOnline) {
            event.preventDefault();

            const offlineRoute = this.findOfflineRoute(new URL(href).pathname);
            if (offlineRoute) {
                const offlineUrl = this.buildOfflineUrl(offlineRoute);
                this.showOfflineLinkMessage(href, () => {
                    window.location.href = offlineUrl;
                });
            } else {
                this.showOfflineWarning(href);
            }
        }
    }

    // Check if link requires online functionality
    linkRequiresOnline(href) {
        const onlineOnlyPatterns = [
            '/payment/',
            '/stripe/',
            '/paypal/',
            '/kbz/',
            '/api/',
            '/admin/',
            '/oauth/',
            '/login/google'
        ];

        return onlineOnlyPatterns.some(pattern => href.includes(pattern));
    }

    // Offer offline redirect with user choice
    offerOfflineRedirect() {
        const offlineRoute = this.findOfflineRoute(this.currentPath);

        if (offlineRoute) {
            this.showOfflineChoiceModal(offlineRoute);
        }
    }

    // Show offline choice modal
    showOfflineChoiceModal(route) {
        const modal = this.createModal({
            title: 'Connection Lost',
            message: `You're currently offline. Would you like to switch to the offline version of this page?`,
            primaryButton: {
                text: 'Go Offline',
                action: () => {
                    const offlineUrl = this.buildOfflineUrl(route);
                    window.location.href = offlineUrl;
                }
            },
            secondaryButton: {
                text: 'Stay Here',
                action: () => {
                    this.closeModal();
                }
            }
        });

        document.body.appendChild(modal);
        modal.style.display = 'block';
    }

    // Show notifications
    showOfflineNotification() {
        this.removeExistingNotification();

        const notification = document.createElement('div');
        notification.id = 'offline-notification';
        notification.className = 'alert alert-warning fixed-top m-3';
        notification.style.cssText = 'z-index: 9999; max-width: 400px; margin-left: auto!important; margin-right: auto!important;';
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-wifi-slash me-2"></i>
                <div>
                    <strong>You're Offline</strong><br>
                    <small>Some features may be limited. Consider switching to offline mode.</small>
                </div>
                <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;

        document.body.appendChild(notification);
    }

    hideOfflineNotification() {
        const notification = document.getElementById('offline-notification');
        if (notification) {
            notification.remove();
        }
    }

    showReconnectionNotification() {
        this.removeExistingNotification();

        const notification = document.createElement('div');
        notification.className = 'alert alert-success fixed-top m-3';
        notification.style.cssText = 'z-index: 9999; max-width: 400px; margin-left: auto!important; margin-right: auto!important;';
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-wifi me-2"></i>
                <div>
                    <strong>Connected!</strong><br>
                    <small>All features are now available. Syncing offline data...</small>
                </div>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    showRedirectNotification(message, callback) {
        const notification = document.createElement('div');
        notification.className = 'alert alert-info fixed-top m-3';
        notification.style.cssText = 'z-index: 9999; max-width: 500px; margin-left: auto!important; margin-right: auto!important;';
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-info-circle me-2"></i>
                <div>
                    <strong>Offline Mode</strong><br>
                    <small>${message}</small>
                </div>
            </div>
        `;

        document.body.appendChild(notification);

        // Redirect after 2 seconds
        setTimeout(() => {
            notification.remove();
            callback();
        }, 2000);
    }

    showOfflineFormMessage(callback) {
        const message = 'This form requires internet connection. Redirecting to offline checkout...';
        this.showRedirectNotification(message, callback);
    }

    showOfflineLinkMessage(originalUrl, callback) {
        const message = `This link requires internet connection. Redirecting to offline alternative...`;
        this.showRedirectNotification(message, callback);
    }

    showOfflineWarning(url) {
        const notification = document.createElement('div');
        notification.className = 'alert alert-warning fixed-top m-3';
        notification.style.cssText = 'z-index: 9999; max-width: 500px; margin-left: auto!important; margin-right: auto!important;';
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <div>
                    <strong>Offline</strong><br>
                    <small>This feature requires internet connection.</small>
                </div>
                <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    removeExistingNotification() {
        const existing = document.querySelector('.alert.fixed-top');
        if (existing) {
            existing.remove();
        }
    }

    // Create modal utility
    createModal({ title, message, primaryButton, secondaryButton }) {
        const modal = document.createElement('div');
        modal.className = 'modal fade show';
        modal.style.display = 'block';
        modal.style.backgroundColor = 'rgba(0,0,0,0.5)';

        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        ${secondaryButton ? `<button type="button" class="btn btn-secondary" data-action="secondary">${secondaryButton.text}</button>` : ''}
                        <button type="button" class="btn btn-primary" data-action="primary">${primaryButton.text}</button>
                    </div>
                </div>
            </div>
        `;

        // Add event listeners
        modal.querySelector('[data-action="primary"]').addEventListener('click', () => {
            this.closeModal();
            primaryButton.action();
        });

        if (secondaryButton) {
            modal.querySelector('[data-action="secondary"]').addEventListener('click', () => {
                this.closeModal();
                secondaryButton.action();
            });
        }

        return modal;
    }

    closeModal() {
        const modal = document.querySelector('.modal.show');
        if (modal) {
            modal.remove();
        }
    }

    // Get current offline status
    getOfflineStatus() {
        return {
            isOnline: this.isOnline,
            currentPath: this.currentPath,
            userContext: this.userContext,
            availableOfflineRoutes: Object.keys(this.offlineRoutes)
        };
    }

    // Force offline mode (for testing)
    forceOfflineMode() {
        this.isOnline = false;
        this.handleConnectionLoss();
    }

    // Force online mode (for testing)
    forceOnlineMode() {
        this.isOnline = true;
        this.handleConnectionRestore();
    }
}

// Export for use in other modules
window.OfflineRedirectManager = OfflineRedirectManager;

// Auto-initialize if DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.offlineRedirectManager = new OfflineRedirectManager();
    });
} else {
    window.offlineRedirectManager = new OfflineRedirectManager();
}