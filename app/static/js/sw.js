const CACHE_NAME = 'dartochsen-v1';
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/css/responsive.css',
  '/static/css/animations.css',
  '/static/js/main.js',
  '/static/images/logo.png'
];

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request).catch(() => caches.match('/offline.html'));
      })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});
