// Force Cache Update Service Worker
const CACHE_NAME = 'pulse-app-v' + Date.now(); // Always new cache
const urlsToCache = [];

// Install event - skip waiting to activate immediately
self.addEventListener('install', (event) => {
  console.log('🔄 Service Worker installing, clearing old cache');
  self.skipWaiting();
});

// Activate event - delete old caches immediately
self.addEventListener('activate', (event) => {
  console.log('🚀 Service Worker activated, clearing all caches');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('🗑️ Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      // Force reload of all clients
      return clients.claim();
    })
  );
});

// Fetch event - always fetch from network for HTML files
self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate' || event.request.destination === 'document') {
    // Always fetch fresh HTML
    event.respondWith(
      fetch(event.request.url + '?t=' + Date.now()).catch(() => {
        return fetch(event.request);
      })
    );
  } else {
    // For other resources, use network first
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(event.request);
      })
    );
  }
});

// Message event - handle manual cache clear
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => caches.delete(cacheName))
      );
    }).then(() => {
      event.ports[0].postMessage({ success: true });
    });
  }
});