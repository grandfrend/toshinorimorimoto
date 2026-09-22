const CACHE_NAME = 'toshinori-cache-v4';
const ASSETS = [
  '/',
  '/index.html',
  '/quienes-somos/',
  '/pedagogia/',
  '/admisiones/',
  '/contacto/',
  '/app.js',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
  'https://cdn.jsdelivr.net/npm/lucide@0.344.0/dist/umd/lucide.min.js'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (url.pathname.startsWith('/api/')) {
    e.respondWith(
      fetch(e.request).catch(() => {
        return new Response(JSON.stringify({ 
          offline: true, 
          message: 'Estás sin conexión. Los datos se guardarán y sincronizarán luego.' 
        }), { headers: { 'Content-Type': 'application/json' } });
      })
    );
  } else {
    e.respondWith(
      caches.match(e.request).then((cachedResponse) => {
        if (cachedResponse) {
          fetch(e.request).then((networkResponse) => {
            if (networkResponse.status === 200) {
              caches.open(CACHE_NAME).then((cache) => cache.put(e.request, networkResponse));
            }
          }).catch(() => {});
          return cachedResponse;
        }
        return fetch(e.request);
      })
    );
  }
});
