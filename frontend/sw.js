// JobSeeker Service Worker v1.1.1
const CACHE_NAME = 'jobseeker-v1.1.1';

// Core app shell files to cache for offline support
const APP_SHELL = [
  '/',
  '/static/index.html',
  '/static/styles.css',
  '/static/app.js',
  '/static/logo.png',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700;800&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

// Install: pre-cache app shell
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('[SW] Pre-caching app shell');
      return cache.addAll(APP_SHELL.map(url => new Request(url, { mode: 'no-cors' })));
    }).catch(err => console.log('[SW] Pre-cache failed (non-critical):', err))
  );
  self.skipWaiting();
});

// Activate: clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch: Network-first for API calls, Cache-first for static assets
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Always go to network for API requests (live job data)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response(JSON.stringify({ error: 'Offline – cannot reach server.' }), {
          headers: { 'Content-Type': 'application/json' }
        })
      )
    );
    return;
  }

  // Cache-first for static assets
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        // Cache successful GET responses for static files
        if (response && response.status === 200 && event.request.method === 'GET') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      });
    }).catch(() => {
      // Fallback to root HTML for navigation requests
      if (event.request.mode === 'navigate') {
        return caches.match('/');
      }
    })
  );
});
