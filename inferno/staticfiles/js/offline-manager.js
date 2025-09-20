// Offline Manager for LaptopMart Myanmar
// Handles offline data storage, cart management, and synchronization

class OfflineManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.dbName = 'LaptopMartOfflineDB';
        this.dbVersion = 1;
        this.db = null;

        this.initDB();
        this.setupEventListeners();
        this.registerServiceWorker();
    }

    // Initialize IndexedDB
    async initDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Products store
                if (!db.objectStoreNames.contains('products')) {
                    const productsStore = db.createObjectStore('products', { keyPath: 'id' });
                    productsStore.createIndex('category', 'category', { unique: false });
                    productsStore.createIndex('brand', 'brand', { unique: false });
                    productsStore.createIndex('shop', 'shop', { unique: false });
                }

                // Cart store
                if (!db.objectStoreNames.contains('cart')) {
                    const cartStore = db.createObjectStore('cart', { keyPath: 'product_id' });
                    cartStore.createIndex('shop', 'shop', { unique: false });
                }

                // Wishlist store
                if (!db.objectStoreNames.contains('wishlist')) {
                    db.createObjectStore('wishlist', { keyPath: 'product_id' });
                }

                // Offline actions store
                if (!db.objectStoreNames.contains('offline_actions')) {
                    const actionsStore = db.createObjectStore('offline_actions', { keyPath: 'id', autoIncrement: true });
                    actionsStore.createIndex('type', 'type', { unique: false });
                    actionsStore.createIndex('timestamp', 'timestamp', { unique: false });
                }

                // User data store
                if (!db.objectStoreNames.contains('user_data')) {
                    db.createObjectStore('user_data', { keyPath: 'key' });
                }

                console.log('IndexedDB initialized successfully');
            };
        });
    }

    // Register service worker
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/static/js/serviceworker.js');
                console.log('Service Worker registered successfully:', registration);

                // Enable background sync
                if ('sync' in window.ServiceWorkerRegistration.prototype) {
                    console.log('Background Sync is supported');
                }

                // Listen for service worker updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateNotification();
                        }
                    });
                });
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }

    // Setup event listeners
    setupEventListeners() {
        // Online/Offline status
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.updateOnlineStatus();
            this.syncOfflineData();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.updateOnlineStatus();
        });

        // Update status on load
        this.updateOnlineStatus();
    }

    // Update online status indicator
    updateOnlineStatus() {
        const statusIndicator = document.getElementById('connection-status');
        const offlineNotice = document.getElementById('offline-notice');

        if (statusIndicator) {
            statusIndicator.className = this.isOnline ? 'online' : 'offline';
            statusIndicator.textContent = this.isOnline ? 'Online' : 'Offline';
        }

        if (offlineNotice) {
            offlineNotice.style.display = this.isOnline ? 'none' : 'block';
        }

        // Disable/enable certain features based on connection
        this.updateUIForOfflineMode();
    }

    // Update UI for offline mode
    updateUIForOfflineMode() {
        const paymentButtons = document.querySelectorAll('.payment-btn:not(.cod-payment)');
        const onlineOnlyElements = document.querySelectorAll('.online-only');

        if (!this.isOnline) {
            paymentButtons.forEach(btn => {
                btn.disabled = true;
                btn.title = 'This payment method requires internet connection';
            });

            onlineOnlyElements.forEach(element => {
                element.style.opacity = '0.5';
                element.style.pointerEvents = 'none';
            });
        } else {
            paymentButtons.forEach(btn => {
                btn.disabled = false;
                btn.title = '';
            });

            onlineOnlyElements.forEach(element => {
                element.style.opacity = '1';
                element.style.pointerEvents = 'auto';
            });
        }
    }

    // Cache products for offline access
    async cacheProducts(products) {
        if (!this.db) await this.initDB();

        const transaction = this.db.transaction(['products'], 'readwrite');
        const store = transaction.objectStore('products');

        for (const product of products) {
            await store.put({
                id: product.id,
                title: product.title,
                price: product.price,
                old_price: product.old_price,
                image: product.image,
                category: product.category,
                brand: product.brand,
                shop: product.shop,
                description: product.description,
                cpu: product.cpu,
                ram: product.ram,
                in_stock: product.in_stock,
                cached_at: new Date().toISOString()
            });
        }

        console.log(`Cached ${products.length} products for offline access`);
    }

    // Get cached products
    async getCachedProducts(limit = 50) {
        if (!this.db) await this.initDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['products'], 'readonly');
            const store = transaction.objectStore('products');
            const request = store.getAll();

            request.onsuccess = () => {
                const products = request.result.slice(0, limit);
                resolve(products);
            };

            request.onerror = () => reject(request.error);
        });
    }

    // Add item to offline cart
    async addToOfflineCart(productId, quantity = 1, shopId = null) {
        if (!this.db) await this.initDB();

        const transaction = this.db.transaction(['cart'], 'readwrite');
        const store = transaction.objectStore('cart');

        const existingItem = await this.getOfflineCartItem(productId);

        const cartItem = {
            product_id: productId,
            quantity: existingItem ? existingItem.quantity + quantity : quantity,
            shop: shopId,
            added_at: new Date().toISOString(),
            synced: false
        };

        await store.put(cartItem);

        // Queue for sync when online
        if (this.isOnline) {
            this.syncCartItem(cartItem);
        } else {
            this.queueOfflineAction('cart_add', cartItem);
        }

        this.updateCartUI();
        console.log('Item added to offline cart:', cartItem);
    }

    // Get offline cart item
    async getOfflineCartItem(productId) {
        if (!this.db) await this.initDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['cart'], 'readonly');
            const store = transaction.objectStore('cart');
            const request = store.get(productId);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    // Get all offline cart items
    async getOfflineCart() {
        if (!this.db) await this.initDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['cart'], 'readonly');
            const store = transaction.objectStore('cart');
            const request = store.getAll();

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    // Remove item from offline cart
    async removeFromOfflineCart(productId) {
        if (!this.db) await this.initDB();

        const transaction = this.db.transaction(['cart'], 'readwrite');
        const store = transaction.objectStore('cart');

        await store.delete(productId);

        // Queue for sync when online
        this.queueOfflineAction('cart_remove', { product_id: productId });

        this.updateCartUI();
        console.log('Item removed from offline cart:', productId);
    }

    // Update cart UI
    async updateCartUI() {
        const cart = await this.getOfflineCart();
        const cartCount = cart.reduce((total, item) => total + item.quantity, 0);

        // Update cart counter
        const cartCounters = document.querySelectorAll('.cart-count');
        cartCounters.forEach(counter => {
            counter.textContent = cartCount;
            counter.style.display = cartCount > 0 ? 'inline' : 'none';
        });

        // Update cart dropdown or page if exists
        this.updateCartDisplay(cart);
    }

    // Update cart display
    updateCartDisplay(cartItems) {
        const cartContainer = document.getElementById('cart-items');
        if (!cartContainer) return;

        if (cartItems.length === 0) {
            cartContainer.innerHTML = '<p class="text-center">Your cart is empty</p>';
            return;
        }

        // This would be expanded to show actual cart items
        // For now, just show count
        cartContainer.innerHTML = `<p>You have ${cartItems.length} items in your cart</p>`;
    }

    // Queue offline action for later sync
    async queueOfflineAction(type, data) {
        if (!this.db) await this.initDB();

        const transaction = this.db.transaction(['offline_actions'], 'readwrite');
        const store = transaction.objectStore('offline_actions');

        const action = {
            type: type,
            data: data,
            timestamp: new Date().toISOString(),
            synced: false
        };

        await store.add(action);
        console.log('Queued offline action:', action);
    }

    // Sync offline data when connection is restored
    async syncOfflineData() {
        if (!this.isOnline || !this.db) return;

        console.log('Syncing offline data...');

        // Register background sync if supported
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            const registration = await navigator.serviceWorker.ready;
            await registration.sync.register('cart-sync');
            await registration.sync.register('wishlist-sync');
            await registration.sync.register('order-sync');
        }

        // Immediate sync for critical data
        await this.syncPendingActions();
    }

    // Sync pending actions
    async syncPendingActions() {
        const transaction = this.db.transaction(['offline_actions'], 'readwrite');
        const store = transaction.objectStore('offline_actions');
        const request = store.getAll();

        request.onsuccess = async () => {
            const actions = request.result.filter(action => !action.synced);

            for (const action of actions) {
                try {
                    await this.syncAction(action);

                    // Mark as synced
                    action.synced = true;
                    await store.put(action);
                } catch (error) {
                    console.error('Failed to sync action:', action, error);
                }
            }
        };
    }

    // Sync individual action
    async syncAction(action) {
        const csrfToken = this.getCSRFToken();

        switch (action.type) {
            case 'cart_add':
                await fetch('/api/cart/add/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(action.data)
                });
                break;

            case 'cart_remove':
                await fetch('/api/cart/remove/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(action.data)
                });
                break;

            case 'wishlist_add':
                await fetch('/api/wishlist/add/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(action.data)
                });
                break;
        }
    }

    // Get CSRF token
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }

    // Show update notification
    showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'update-notification';
        notification.innerHTML = `
            <div class="alert alert-info">
                <strong>Update Available!</strong>
                A new version of the app is available.
                <button onclick="location.reload()" class="btn btn-sm btn-primary ml-2">
                    Update Now
                </button>
            </div>
        `;
        document.body.appendChild(notification);
    }

    // Save order for offline submission
    async saveOfflineOrder(orderData) {
        if (!this.db) await this.initDB();

        const transaction = this.db.transaction(['offline_actions'], 'readwrite');
        const store = transaction.objectStore('offline_actions');

        const action = {
            type: 'order_create',
            data: orderData,
            timestamp: new Date().toISOString(),
            synced: false
        };

        await store.add(action);

        // Show user confirmation
        this.showOfflineOrderConfirmation();

        console.log('Order saved for offline submission:', action);
    }

    // Show offline order confirmation
    showOfflineOrderConfirmation() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Order Saved</h5>
                    </div>
                    <div class="modal-body">
                        <p>Your order has been saved and will be submitted automatically when you're back online.</p>
                        <p>You'll receive a notification once the order is successfully submitted.</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" data-dismiss="modal">OK</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        $(modal).modal('show');
    }
}

// Initialize offline manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.offlineManager = new OfflineManager();

    // Cache current page products
    const productElements = document.querySelectorAll('[data-product-id]');
    if (productElements.length > 0) {
        const products = Array.from(productElements).map(el => ({
            id: el.dataset.productId,
            title: el.dataset.productTitle || '',
            price: el.dataset.productPrice || '',
            old_price: el.dataset.productOldPrice || '',
            image: el.dataset.productImage || '',
            category: el.dataset.productCategory || '',
            brand: el.dataset.productBrand || '',
            shop: el.dataset.productShop || '',
            description: el.dataset.productDescription || '',
            cpu: el.dataset.productCpu || '',
            ram: el.dataset.productRam || '',
            in_stock: el.dataset.productInStock === 'true'
        }));

        window.offlineManager.cacheProducts(products);
    }
});

// Export for global access
window.OfflineManager = OfflineManager;