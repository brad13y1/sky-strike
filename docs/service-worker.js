// Sky Strike — Service Worker
// Caches all game files on first load so every launch after that
// is instant, even with no internet connection.
//
// VERSION: bump this string any time you push a new build.
// Changing the version forces the browser to download fresh files
// and replace the old cache. If you forget to bump it, players
// may get a stale version of the game after an update.

const CACHE_NAME = "sky-strike-v1";

const FILES_TO_CACHE = [
    "/sky-strike/",
    "/sky-strike/index.html",
    "/sky-strike/manifest.json",
    "/sky-strike/favicon.png",
    "/sky-strike/extra.css",
    "/sky-strike/icon-192.png",
    "/sky-strike/icon-512.png",
    "/sky-strike/sky_strike.tar.gz",
];

// Install — cache all files on first visit
self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            console.log("Sky Strike: caching game files...");
            return cache.addAll(FILES_TO_CACHE);
        })
    );
    // Take over immediately without waiting for old SW to expire
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

// Fetch — serve from cache, fall back to network if not cached
self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request).then(cached => {
            if (cached) {
                return cached;
            }
            return fetch(event.request);
        })
    );
});