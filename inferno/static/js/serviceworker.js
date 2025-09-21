// Service Worker for LaptopMart Myanmar
// Handles offline functionality, caching, and background sync

const CACHE_NAME = 'laptopmart-v1';
const OFFLINE_URL = '/offline/';

// Files to cache for offline functionality
const STATIC_CACHE_URLS = [
    '/',
    '/offline/',
    '/static/css/bootstrap.css',
    '/static/css/main.css',
    '/static/js/bootstrap.bundle.min.js',
    '/static/js/jquery.min.js',
    '/static/js/offline-manager.js',
    '/static/assets/libs/bootstrap.min.css',
    '/static/assets/libs/bootstrap.bundle.min.js',
    '/static/assets/libs/font-awesome.min.css',
    '/static/assets/libs/jquery.min.js',
    '/static/assets/libs/qrcode.min.js',
    '/static/assets/css/cyberoptixcss.css',
    '/static/assets/js/function.js'
];

// API endpoints to cache
const API_CACHE_URLS = [
    '/api/states/',
    '/api/cities-by-state/',
    '/api/townships-by-city/'
];

// Install event - cache essential resources
self.addEventListener('install', event => {
    console.log('Service Worker: Installing...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Service Worker: Caching essential files');
                return cache.addAll(STATIC_CACHE_URLS);
            })
            .then(() => {
                console.log('Service Worker: Installation complete');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('Service Worker: Installation failed', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker: Activating...');

    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== CACHE_NAME) {
                            console.log('Service Worker: Deleting old cache', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker: Activation complete');
                return self.clients.claim();
            })
    );
});

// Fetch event - handle network requests
self.addEventListener('fetch', event => {
    const request = event.request;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Handle different types of requests
    if (isStaticAsset(url)) {
        event.respondWith(handleStaticAsset(request));
    } else if (isAPIRequest(url)) {
        event.respondWith(handleAPIRequest(request));
    } else if (isPageRequest(url)) {
        event.respondWith(handlePageRequest(request));
    }
});

// Check if request is for a static asset
function isStaticAsset(url) {
    return url.pathname.startsWith('/static/') ||
           url.pathname.startsWith('/media/') ||
           url.pathname.includes('.css') ||
           url.pathname.includes('.js') ||
           url.pathname.includes('.png') ||
           url.pathname.includes('.jpg') ||
           url.pathname.includes('.jpeg') ||
           url.pathname.includes('.svg');
}

// Check if request is for API endpoint
function isAPIRequest(url) {
    return url.pathname.startsWith('/api/');
}

// Check if request is for a page
function isPageRequest(url) {
    return url.pathname.startsWith('/') &&
           !isStaticAsset(url) &&
           !isAPIRequest(url);
}

// Handle static assets with cache-first strategy
function handleStaticAsset(request) {
    return caches.match(request)
        .then(cachedResponse => {
            if (cachedResponse) {
                return cachedResponse;
            }

            return fetch(request)
                .then(response => {
                    // Cache successful responses
                    if (response.status === 200) {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(request, responseClone);
                            });
                    }
                    return response;
                })
                .catch(() => {
                    // Return a default offline image or asset if available
                    if (request.destination === 'image') {
                        return caches.match('/static/images/offline-placeholder.png');
                    }
                });
        });
}

// Handle API requests with network-first strategy
function handleAPIRequest(request) {
    return fetch(request)
        .then(response => {
            // Cache successful API responses for offline use
            if (response.status === 200) {
                const responseClone = response.clone();
                caches.open(CACHE_NAME)
                    .then(cache => {
                        cache.put(request, responseClone);
                    });
            }
            return response;
        })
        .catch(() => {
            // Return cached API response if network fails
            return caches.match(request)
                .then(cachedResponse => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }

                    // Return offline indicator for API requests
                    return new Response(
                        JSON.stringify({
                            error: 'Offline',
                            message: 'This request requires internet connection'
                        }),
                        {
                            status: 503,
                            statusText: 'Service Unavailable',
                            headers: { 'Content-Type': 'application/json' }
                        }
                    );
                });
        });
}

// Handle page requests with network-first strategy
function handlePageRequest(request) {
    return fetch(request)
        .then(response => {
            // Cache successful page responses
            if (response.status === 200) {
                const responseClone = response.clone();
                caches.open(CACHE_NAME)
                    .then(cache => {
                        cache.put(request, responseClone);
                    });
            }
            return response;
        })
        .catch(() => {
            // Check cache for the requested page
            return caches.match(request)
                .then(cachedResponse => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }

                    // Return offline page
                    return caches.match(OFFLINE_URL);
                });
        });
}

// Background sync for offline actions
self.addEventListener('sync', event => {
    console.log('Service Worker: Background sync event', event.tag);

    if (event.tag === 'cart-sync') {
        event.waitUntil(syncCartData());
    } else if (event.tag === 'order-sync') {
        event.waitUntil(syncOrderData());
    } else if (event.tag === 'wishlist-sync') {
        event.waitUntil(syncWishlistData());
    }
});

// Sync cart data when online
async function syncCartData() {
    try {
        const offlineActions = await getOfflineActions('cart');

        for (const action of offlineActions) {
            try {
                await fetch('/api/cart/sync/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': await getCSRFToken()
                    },
                    body: JSON.stringify(action)
                });

                // Remove synced action from offline storage
                await removeOfflineAction('cart', action.id);
            } catch (error) {
                console.error('Failed to sync cart action:', error);
            }
        }
    } catch (error) {
        console.error('Cart sync failed:', error);
    }
}

// Sync order data when online
async function syncOrderData() {
    try {
        const offlineOrders = await getOfflineActions('orders');

        for (const order of offlineOrders) {
            try {
                const response = await fetch('/api/orders/create/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': await getCSRFToken()
                    },
                    body: JSON.stringify(order)
                });

                if (response.ok) {
                    await removeOfflineAction('orders', order.id);

                    // Notify user of successful order submission
                    self.registration.showNotification('Order Submitted', {
                        body: 'Your offline order has been successfully submitted!',
                        icon: '/static/images/icons/icon-192x192.png',
                        badge: '/static/images/icons/icon-72x72.png'
                    });
                }
            } catch (error) {
                console.error('Failed to sync order:', error);
            }
        }
    } catch (error) {
        console.error('Order sync failed:', error);
    }
}

// Sync wishlist data when online
async function syncWishlistData() {
    try {
        const offlineWishlist = await getOfflineActions('wishlist');

        for (const action of offlineWishlist) {
            try {
                await fetch('/api/wishlist/sync/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': await getCSRFToken()
                    },
                    body: JSON.stringify(action)
                });

                await removeOfflineAction('wishlist', action.id);
            } catch (error) {
                console.error('Failed to sync wishlist action:', error);
            }
        }
    } catch (error) {
        console.error('Wishlist sync failed:', error);
    }
}

// Helper functions for offline storage management
async function getOfflineActions(type) {
    return new Promise((resolve) => {
        const stored = localStorage.getItem(`offline_${type}`);
        resolve(stored ? JSON.parse(stored) : []);
    });
}

async function removeOfflineAction(type, actionId) {
    const actions = await getOfflineActions(type);
    const filtered = actions.filter(action => action.id !== actionId);
    localStorage.setItem(`offline_${type}`, JSON.stringify(filtered));
}

async function getCSRFToken() {
    try {
        const response = await fetch('/api/csrf-token/');
        const data = await response.json();
        return data.csrf_token;
    } catch (error) {
        // Fallback: try to get token from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }
}

// Push notification handling
self.addEventListener('push', event => {
    if (event.data) {
        const data = event.data.json();

        event.waitUntil(
            self.registration.showNotification(data.title, {
                body: data.body,
                icon: data.icon || '/static/images/icons/icon-192x192.png',
                badge: '/static/images/icons/icon-72x72.png',
                data: data.url
            })
        );
    }
});

// Notification click handling
self.addEventListener('notificationclick', event => {
    event.notification.close();

    if (event.notification.data) {
        event.waitUntil(
            clients.openWindow(event.notification.data)
        );
    }
});

console.log('Service Worker: Loaded successfully');