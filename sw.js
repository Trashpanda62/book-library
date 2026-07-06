/* Our Library — service worker: offline app shell + persistent cover cache */
const V = "libshell-v1";
const SHELL = ["./", "./index.html", "./manifest.webmanifest",
  "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png", "./favicon.png"];
const COVER_HOSTS = ["covers.openlibrary.org", "books.google.com",
  "books.googleusercontent.com", "mzstatic.com"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(V).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) =>
    Promise.all(keys.filter((k) => k !== V && k !== "covers-v1").map((k) => caches.delete(k)))
  ).then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // Book covers: cache-first so they survive offline and load instantly on repeat.
  if (COVER_HOSTS.some((h) => url.hostname.endsWith(h))) {
    e.respondWith(caches.open("covers-v1").then(async (c) => {
      const hit = await c.match(req);
      if (hit) return hit;
      try {
        const res = await fetch(req);
        if (res && (res.ok || res.type === "opaque")) c.put(req, res.clone());
        return res;
      } catch (_) { return hit || Response.error(); }
    }));
    return;
  }

  // Same-origin (the app itself): network-first so updates land, cache as offline fallback.
  if (url.origin === location.origin) {
    e.respondWith((async () => {
      try {
        const res = await fetch(req);
        const c = await caches.open(V);
        c.put(req, res.clone());
        return res;
      } catch (_) {
        const c = await caches.open(V);
        return (await c.match(req)) || (await c.match("./index.html")) || Response.error();
      }
    })());
  }
  // Other cross-origin (Open Library / Google Books search JSON): default network passthrough.
});
