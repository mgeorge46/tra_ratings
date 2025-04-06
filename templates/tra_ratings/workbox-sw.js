importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.5.4/workbox-sw.js');

workbox.setConfig({ debug: false });

workbox.precaching.precacheAndRoute([
  { url: '/static/css/styles.css', revision: null },
  { url: '/static/js/main.js', revision: null },
  { url: '/static/rating/css/rating.css', revision: null },
  { url: '/static/rating/js/rating.js', revision: null }
]);

// Cache-first for static assets
workbox.routing.registerRoute(
  /\.(?:js|css|png|jpg|jpeg|svg|woff2?)$/,
  new workbox.strategies.CacheFirst({
    cacheName: 'assets-cache',
    plugins: [new workbox.expiration.ExpirationPlugin({
      maxEntries: 60,
      maxAgeSeconds: 30 * 24 * 60 * 60,
    })],
  })
);

// Network-first for pages
workbox.routing.registerRoute(
  ({ request }) => request.mode === 'navigate',
  new workbox.strategies.NetworkFirst({ cacheName: 'pages-cache' })
);

// 🔁 Background Sync for failed POSTs
const bgSyncPlugin = new workbox.backgroundSync.BackgroundSyncPlugin('ratingQueue', {
  maxRetentionTime: 24 * 60 // Retry for 24 hours
});

workbox.routing.registerRoute(
  /\/api\/v1\/ratings\//,
  new workbox.strategies.NetworkOnly({
    plugins: [bgSyncPlugin]
  }),
  'POST'
);

// 🔔 Push notifications support
self.addEventListener('push', function(event) {
  const data = event.data.json();
  const options = {
    body: data.body,
    icon: '/static/icons/icon-192x192.png'
  };
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});
