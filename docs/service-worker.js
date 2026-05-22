// Sky Strike — Service Worker
// Caches the small essential files on install.
// The large game bundle (sky_strike.tar.gz) is NOT pre-cached —
// it's too large to reliably cache during the install event on
// mobile. The browser caches it naturally after the first load.
//
// VERSION: bump this string every time you push a new build so
// players get fresh files instead of the old cached version.

const CACHE_NAME = "sky-strike-v6";

const FILES_TO_CACHE = [
    "/sky-strike/",
    "/sky-strike/index.html",
    "/sky-strike/manifest.json",
    "/sky-strike/favicon.png",
    "/sky-strike/extra.css",
    "/sky-strike/icon-192.png",
    "/sky-strike/icon-512.png",
];

// Install — cache small essential files only
self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            console.log("Sky Strike: caching essential files...");
            return cache.addAll(FILES_TO_CACHE);
        })
    );
    self.skipWaiting();
});

// Activate — delete any old caches from previous versions
self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys
                .filter(key => key !== CACHE_NAME)
                .map(key => {
                    console.log("Sky Strike: removing old cache", key);
                    return caches.delete(key);
                })
            )
        )
    );
    self.clients.claim();
});

// Fetch — serve from cache if available, otherwise fetch from
// network and cache the response for next time.
// This way the large game bundle gets cached after first load
// without blocking the service worker install.
self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request).then(cached => {
            if (cached) {
                return cached;
            }
            // Not in cache — fetch from network and cache for next time
            return fetch(event.request).then(response => {
                // Only cache valid responses
                if (!response || response.status !== 200) {
                    return response;
                }
                const responseClone = response.clone();
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(event.request, responseClone);
                });
                return response;
            });
        })
    );
});