/* Digital Menu QR — Service Worker (Level 4, demo)
   Cache-first untuk shell aplikasi agar bisa dibuka offline setelah
   kunjungan pertama. Hanya menangani permintaan GET same-origin.
   Versi cache dinaikkan setiap ada perubahan file aplikasi. */
var CACHE_NAMA = "dmq-v3";
var SHELL = ["./", "index.html", "manifest.json", "icon-192.png", "icon-512.png"];

self.addEventListener("install", function (e) {
  e.waitUntil(
    caches.open(CACHE_NAMA).then(function (c) { return c.addAll(SHELL); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k !== CACHE_NAMA; })
        .map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (e) {
  if (e.request.method !== "GET") { return; }
  var url = new URL(e.request.url);
  if (url.origin !== self.location.origin) { return; }
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then(function (cached) {
      var ambil = fetch(e.request).then(function (resp) {
        if (resp && resp.status === 200) {
          var salinan = resp.clone();
          caches.open(CACHE_NAMA).then(function (c) { c.put(e.request, salinan); });
        }
        return resp;
      }).catch(function () { return cached; });
      return cached || ambil;
    })
  );
});
