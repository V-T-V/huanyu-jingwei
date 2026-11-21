/* 寰宇经纬 · Service Worker v2 —— 外壳预存 + 全文懒存 */
const VERSION = "v3";
const SHELL_FILES = [
  "./index.html",
  "./css/main.css?v=3",
  "./vendor/leaflet.js?v=3",
  "./vendor/leaflet.css?v=3",
  "./data/site_data.js?v=3",
  "./data/xref_fy.js?v=3",
  "./data/xrev_yh.js?v=3",
  "./js/config.js?v=3",
  "./js/map.js?v=3",
  "./js/rail.js?v=3",
  "./js/panels.js?v=3",
  "./js/reader.js?v=3",
  "./js/search.js?v=3",
  "./js/ftworker.js?v=3",
  "./js/fulltext.js?v=3",
  "./js/app.js?v=3",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open("hy-shell-" + VERSION)
    .then((c) => c.addAll(SHELL_FILES.map((f) => f.replace(/\?v=\d+/, "?v=" + VERSION.slice(1))))
    .catch(() => {})  // 个别资源失败不阻塞安装
    .then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) =>
    Promise.all(keys.filter((k) => k !== "hy-shell-" + VERSION && k !== "hy-text").map((k) => caches.delete(k)))
  ).then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const url = e.request.url;
  if (url.includes("data/text/") || url.endsWith(".js") && url.includes("/js/")) {
    /* 全文分片与模块: 网络优先回退缓存（懒存） */
    e.respondWith(fetch(e.request).then((r) => {
      const cp = r.clone();
      caches.open("hy-text").then((c) => c.put(e.request, cp));
      return r;
    }).catch(() => caches.match(e.request)));
    return;
  }
  if (url.includes("arcgisonline.com")) {
    /* 瓦片: stale-while-revalidate, 限额防膨胀 */
    e.respondWith(caches.open("hy-tiles").then((c) =>
      c.match(e.request).then((hit) => {
        const net = fetch(e.request).then((r) => {
          c.keys().then((ks) => { if (ks.length > 900) c.delete(ks[0]); });
          const cp = r.clone(); c.put(e.request, cp); return r;
        }).catch(() => hit);
        return hit || net;
      })));
    return;
  }
  if (e.request.mode === "navigate") {
    e.respondWith(fetch(e.request).catch(() => caches.match("./index.html")));
  }
});
