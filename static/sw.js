/* ═══════════ sw.js — Dijital Kütüphane PWA Service Worker ═══════════ */
const CACHE_NAME = 'dijital-kutuphane-v20261115';
const STATIC_ASSETS = [
  '/',
  '/static/favicon.svg',
  '/static/manifest.json',
  '/static/css/style.css',
  '/static/css/tokens.css',
  '/static/css/design.css',
  '/static/css/app.css',
  '/static/js/state.js',
  '/static/js/api.js',
  '/static/js/ui_core.js',
  '/static/js/ui_workspace.js',
  '/static/js/ui_chat_settings.js',
  '/static/js/ui_logs.js',
  '/static/js/ui_telegram.js',
  '/static/js/websocket.js',
  '/static/js/app.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    try {
      const cache = await caches.open(CACHE_NAME);
      try {
        await cache.addAll(STATIC_ASSETS);
      } catch (err) {
        console.warn('PWA Asset pre-cache error (tolerated):', err);
      }
      await self.skipWaiting();
    } catch (err) {
      console.warn('PWA install error:', err);
    }
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    try {
      const keys = await caches.keys();
      await Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
      await self.clients.claim();
    } catch (err) {
      console.warn('PWA activate error:', err);
    }
  })());
});

async function handleNavigationFetch(request) {
  try {
    return await fetch(request);
  } catch {
    return (await caches.match('/')) || Response.error();
  }
}

async function handleStaticAssetFetch(request) {
  try {
    const cached = await caches.match(request);
    if (cached) return cached;

    const response = await fetch(request);
    if (response?.status === 200 && response.type === 'basic') {
      const clone = response.clone();
      try {
        const cache = await caches.open(CACHE_NAME);
        await cache.put(request, clone);
      } catch (err) {
        console.warn('PWA cache put error:', err);
      }
    }
    return response;
  } catch (err) {
    console.warn('PWA static asset fetch failed:', err);
    return (await caches.match('/')) || Response.error();
  }
}

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Bypass cache for API calls, WebSocket, handoff, and book downloads
  if (
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/ws') ||
    url.pathname.startsWith('/handoff/') ||
    url.pathname.startsWith('/thumbnails/') ||
    url.pathname.startsWith('/opds') ||
    event.request.method !== 'GET'
  ) {
    return;
  }

  // Network-first strategy for HTML pages, cache fallback
  if (event.request.mode === 'navigate') {
    event.respondWith(handleNavigationFetch(event.request));
    return;
  }

  // Cache-first strategy for static assets
  event.respondWith(handleStaticAssetFetch(event.request));
});

