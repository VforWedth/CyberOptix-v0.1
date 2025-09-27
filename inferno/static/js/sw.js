const CACHE_NAME = 'laptopmart-offline-v3';
const OFFLINE_URL = '/admin/offline/';

const STATIC_CACHE_URLS = [
  '/static/css/',
  '/static/js/',
  '/static/assets/',
  '/admin/dashboard/',
  '/admin/analytics/',
  '/admin/sales/',
  '/admin/users/',
  '/admin/products/',
  '/admin/orders/',
  '/admin/offline/'
];

const API_CACHE_PATTERNS = [
  /\/admin\/api\//,
  /\/api\/v1\//
];

self.addEventListener('install', event => {
  console.log('[SW] Installing Service Worker');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Caching app shell');
        return cache.addAll([
          '/admin/dashboard/',
          '/admin/offline/',
          // Essential CSS for offline mode
          '/static/assets/libs/bootstrap/css/bootstrap.min.css',
          '/static/assets/libs/fontawesome/all.min.css',
          '/static/assets/libs/bootstrap-icons/bootstrap-icons.css',
          '/static/assets/libs/boxicons/boxicons.min.css',
          '/static/assets/css/cyberoptixcss.css',
          '/static/assets/css/style.css',
          // Essential JS for offline mode
          '/static/assets/libs/jquery/jquery.min.js',
          '/static/assets/libs/bootstrap/js/bootstrap.bundle.min.js',
          '/static/assets/libs/qrcode/qrcode.min.js',
          '/static/assets/libs/chartjs/chart.min.js',
          '/static/assets/js/function.js',
          '/static/js/offline-manager.js',
          '/static/js/offline-mode-toggle.js',
          // Myanmar address data for offline checkout
          '/static/data/myanmar_address_data.json',
          // Core app pages for demo flow
          '/',
          '/en/',
          '/shop/',
          '/products/',
          '/cart/',
          '/checkout/',
          '/orders/',
          '/account/',
          // Font files for offline
          '/static/assets/libs/bootstrap-icons/bootstrap-icons.woff',
          '/static/assets/libs/bootstrap-icons/bootstrap-icons.woff2'
        ]);
      })
      .then(() => {
        console.log('[SW] Skip waiting');
        self.skipWaiting();
      })
  );
});

self.addEventListener('activate', event => {
  console.log('[SW] Activating Service Worker');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[SW] Claiming clients');
      return self.clients.claim();
    })
  );
});

self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip chrome-extension and other non-http requests
  if (!request.url.startsWith('http')) {
    return;
  }

  // Handle admin panel routes
  if (url.pathname.startsWith('/admin/')) {
    event.respondWith(handleAdminRequest(request));
    return;
  }

  // Handle API requests
  if (API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // Handle static assets
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(handleStaticRequest(request));
    return;
  }

  // Default network first strategy
  event.respondWith(
    fetch(request).catch(() => {
      return caches.match(request);
    })
  );
});

async function handleAdminRequest(request) {
  const url = new URL(request.url);
  const isAjax = request.headers.get('X-Requested-With') === 'XMLHttpRequest' ||
                 url.searchParams.has('ajax');

  try {
    // Try network first
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      // Cache successful responses
      const cache = await caches.open(CACHE_NAME);
      await cache.put(request, networkResponse.clone());

      // Store data in IndexedDB for offline access
      if (isAjax) {
        const data = await networkResponse.clone().text();
        await storeOfflineData(url.pathname, data);
      }

      return networkResponse;
    }
  } catch (error) {
    console.log('[SW] Network failed, trying cache for:', request.url);
  }

  // Try cache
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  // If AJAX request and offline, return stored data
  if (isAjax) {
    const offlineData = await getOfflineData(url.pathname);
    if (offlineData) {
      return new Response(offlineData, {
        headers: { 'Content-Type': 'text/html' }
      });
    }
  }

  // Fallback to offline page for admin routes
  if (url.pathname.startsWith('/admin/')) {
    const offlinePage = await caches.match('/admin/offline/');
    if (offlinePage) {
      return offlinePage;
    }
  }

  return new Response('Offline - Content not available', {
    status: 503,
    statusText: 'Service Unavailable'
  });
}

async function handleApiRequest(request) {
  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      await cache.put(request, networkResponse.clone());
      return networkResponse;
    }
  } catch (error) {
    console.log('[SW] API network failed:', request.url);
  }

  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  return new Response(JSON.stringify({
    error: 'Offline',
    message: 'This feature requires internet connection'
  }), {
    status: 503,
    headers: { 'Content-Type': 'application/json' }
  });
}

async function handleStaticRequest(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      await cache.put(request, networkResponse.clone());
      return networkResponse;
    }
  } catch (error) {
    console.log('[SW] Static asset failed:', request.url);
  }

  return new Response('Asset not available offline', { status: 404 });
}

// IndexedDB functions for offline data storage
async function storeOfflineData(path, data) {
  try {
    const db = await openDB();
    const transaction = db.transaction(['adminData'], 'readwrite');
    const store = transaction.objectStore('adminData');
    await store.put({
      path: path,
      data: data,
      timestamp: Date.now()
    });
  } catch (error) {
    console.error('[SW] Error storing offline data:', error);
  }
}

async function getOfflineData(path) {
  try {
    const db = await openDB();
    const transaction = db.transaction(['adminData'], 'readonly');
    const store = transaction.objectStore('adminData');
    const result = await store.get(path);
    return result ? result.data : null;
  } catch (error) {
    console.error('[SW] Error getting offline data:', error);
    return null;
  }
}

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('LaptopMartAdmin', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('adminData')) {
        db.createObjectStore('adminData', { keyPath: 'path' });
      }
    };
  });
}

// Background sync for future implementation
self.addEventListener('sync', event => {
  if (event.tag === 'admin-data-sync') {
    event.waitUntil(syncAdminData());
  }
});

async function syncAdminData() {
  console.log('[SW] Background sync triggered');
  // Future implementation for syncing offline changes
}

// Push notifications support for future implementation
self.addEventListener('push', event => {
  if (event.data) {
    const data = event.data.json();
    event.waitUntil(
      self.registration.showNotification(data.title, {
        body: data.body,
        icon: '/static/assets/images/logo.png',
        badge: '/static/assets/images/badge.png'
      })
    );
  }
});