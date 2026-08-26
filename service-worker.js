const CACHE_NAME = "daily-251-sax-v59";
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./service-worker.js",
  "./README.md"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

// HTML(ページ本体)とJSONは常に最新を優先するnetwork-first。
// 端末に古い版が残ったまま気づかない、という事故を防ぐため。
function isNetworkFirst(request) {
  const url = new URL(request.url);
  return request.mode === "navigate" || url.pathname.endsWith(".html") || url.pathname.endsWith(".json");
}

self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;

  if (isNetworkFirst(event.request)) {
    event.respondWith(
      fetch(event.request).then(response => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
        return response;
      }).catch(() => caches.match(event.request).then(cached => cached || caches.match("./index.html")))
    );
    return;
  }

  // CSS/JS/画像などはcache-first。
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
        return response;
      }).catch(() => caches.match("./index.html"));
    })
  );
});
