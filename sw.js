/* 寰宇经纬 · Service Worker v2 —— 外壳预存 + 全文懒存 */
const VERSION = "v7";
const SHELL_FILES = [
  "./", "./index.html", "./3d.html", "./manifest.json",
  "./css/main.css?v=7",
  "./vendor/leaflet.js?v=7",
  "./vendor/leaflet.css?v=7",
  "./vendor/maplibre-gl.js?v=7",
  "./vendor/maplibre-gl.css?v=7",
  "./data/site_data.js?v=7",
  "./data/xref_fy.js?v=7",
  "./data/xrev_yh.js?v=7",
  "./js/config.js?v=7",
  "./js/map.js?v=7",
  "./js/rail.js?v=7",
  "./js/panels.js?v=7",
  "./js/reader.js?v=7",
  "./js/search.js?v=7",
  "./js/ftworker.js?v=7",
  "./js/fulltext.js?v=7",
  "./js/app.js?v=7",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open("hy-shell-" + VERSION)
    .then((c) => c.addAll(SHELL_FILES.map((f) => f.replace(/\?v=\d+/, "?v=" + VERSION.slice(1))))
    .catch(() => {})  // 个别资源失败不阻塞安装
    .then(() => self.skipWaiting())));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) =>
    Promise.all(keys.filter((k) => k !== "hy-shell-" + VERSION && k !== "hy-text").map((k) => caches.delete(k)))
  ).then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  if (url.href.includes("arcgisonline.com")) {
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
    /* 离线先回本页缓存（3d.html 离线得 3d，不调包成首页）再回外壳 */
    e.respondWith(fetch(e.request)
      .catch(() => caches.match(e.request).then((r) => r || caches.match("./index.html"))));
    return;
  }
  if (url.origin !== self.location.origin) return;
  /* 同源资源：网络优先防钉旧版，成功回填（全文分片→hy-text 懒存 · 其余→外壳），
     离线回缓存——css/site_data/xref/vendor 此前无分支，断网即断供（离线三验实证） */
  const isText = url.pathname.includes("/data/text/");
  e.respondWith(fetch(e.request).then((r) => {
    const cp = r.clone();
    caches.open(isText ? "hy-text" : "hy-shell-" + VERSION).then((c) => c.put(e.request, cp));
    return r;
  }).catch(() => caches.match(e.request)));
});
