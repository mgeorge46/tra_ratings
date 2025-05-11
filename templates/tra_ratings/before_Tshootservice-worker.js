const CACHE_VERSION = 'v2';
const CACHE_NAME = `TransportRatings-${CACHE_VERSION}`;

const STATIC_ASSETS = [
  '/',
  '/offline/',
  '/static/css/styles.css',
  '/static/js/main.js',
  '/static/rating/css/rating.css',
  '/static/rating/js/rating.js',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
];

// Install: Pre-cache core assets
self.addEventListener('install', event => {
  console.log('[ServiceWorker] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('[ServiceWorker] Caching static assets...');
      return cache.addAll(STATIC_ASSETS);
    })
  );
});

// Activate: Clean up old caches
self.addEventListener('activate', event => {
  console.log('[ServiceWorker] Activating...');
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            console.log(`[ServiceWorker] Removing old cache: ${key}`);
            return caches.delete(key);
          }
        })
      )
    )
  );
});

// Fetch: Cache-first for static, network-first for pages, offline fallback
self.addEventListener('fetch', event => {
  if (event.request.mode === 'navigate') {
    // For HTML page requests: try network, fallback to offline
    event.respondWith(
      fetch(event.request)
        .then(response => {
          return response;
        })
        .catch(() => {
          return caches.match('/offline/');
        })
    );
  } else {
    // For static assets: try cache, fallback to network + auto-cache
    event.respondWith(
      caches.match(event.request).then(cachedResponse => {
        return (
          cachedResponse ||
          fetch(event.request)
            .then(networkResponse => {
              return caches.open(CACHE_NAME).then(cache => {
                cache.put(event.request, networkResponse.clone());
                return networkResponse;
              });
            })
            .catch(error => {
              console.error('[ServiceWorker] Asset fetch failed:', event.request.url, error);
              throw error;
            })
        );
      })
    );
  }
});

// Optional: Handle push notifications
self.addEventListener('push', function (event) {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body,
      icon: '/static/icons/icon-192x192.png',
      badge: '/static/icons/icon-192x192.png'
    };
    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});
