/* ═══════════ sw.js — Dijital Kütüphane PWA Service Worker ═══════════ */
const CACHE_NAME = 'dijital-kutuphane-v2026111809';
const CDN_CACHE_NAME = 'dijital-kutuphane-cdn-v2';
const PERSISTENT_CACHES = new Set([
  CACHE_NAME,
  'dijital-kutuphane-vault-v1',
  CDN_CACHE_NAME
]);
const CDN_HOSTS = new Set([
  'cdnjs.cloudflare.com',
  'fonts.googleapis.com',
  'fonts.gstatic.com'
]);
const STATIC_ASSETS = [
  '/',
  '/static/favicon.svg',
  '/static/manifest.json',
  '/static/css/style.css',
  '/static/css/tokens.css',
  '/static/css/design.css',
  '/static/css/motion.css',
  '/static/css/app.css',
  '/static/js/state.js',
  '/static/js/motion.js',
  '/static/js/api.js',
  '/static/js/offline_vault.js',
  '/static/js/ui_core.js',
  '/static/js/ui_logs.js',
  '/static/js/ui_chat_settings.js',
  '/static/js/ui_srs.js',
  '/static/js/ui_telegram.js',
  '/static/js/workspace_state.js',
  '/static/js/workspace_selection.js',
  '/static/js/workspace_renderer.js',
  '/static/js/workspace_search.js',
  '/static/js/workspace_tts.js',
  '/static/js/workspace_chat.js',
  '/static/js/ui_workspace.js',
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
        keys.filter((key) => !PERSISTENT_CACHES.has(key)).map((key) => caches.delete(key))
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

async function handleCdnAssetFetch(request) {
  const cache = await caches.open(CDN_CACHE_NAME);
  const cached = await cache.match(request);
  if (cached) {
    if (cached.type === 'opaque' && request.mode === 'cors') {
      try {
        await cache.delete(request);
      } catch (_delErr) {}
    } else {
      return cached;
    }
  }
  try {
    const resp = await fetch(request);
    if (resp && resp.status === 200 && resp.type !== 'opaque') {
      try {
        await cache.put(request, resp.clone());
      } catch (_putErr) {}
    }
    return resp;
  } catch {
    return Response.error();
  }
}

async function handleStaticAssetFetch(request) {
  try {
    const exactCached = await caches.match(request);
    if (exactCached) return exactCached;

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
    const ignoreQueryMatch = await caches.match(request, { ignoreSearch: true });
    if (ignoreQueryMatch) return ignoreQueryMatch;
    return Response.error();
  }
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET' || req.headers.has('range')) {
    return;
  }

  const url = new URL(req.url);
  if (CDN_HOSTS.has(url.hostname)) {
    event.respondWith(handleCdnAssetFetch(req));
    return;
  }

  if (url.origin !== self.location.origin) {
    return;
  }

  if (
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/ws') ||
    url.pathname.startsWith('/handoff/') ||
    url.pathname.startsWith('/thumbnails/') ||
    url.pathname.startsWith('/opds') ||
    url.pathname === '/login' ||
    url.pathname === '/sw.js'
  ) {
    return;
  }

  if (req.mode === 'navigate') {
    event.respondWith(handleNavigationFetch(req));
    return;
  }

  event.respondWith(handleStaticAssetFetch(req));
});
