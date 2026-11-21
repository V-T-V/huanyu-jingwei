/* ═══════════ 審宇经纬 · 舆图（Leaflet · 州点 + 县微点 + 道色） ═══════════ */

var HYMAP = (() => {
  var map, tileLayer = null, tileErrs = 0;
  var zhouLayer = L.layerGroup();
  var xianLayer = L.layerGroup();
  var selName = null, selDao = null;
  var daoColorMode = true;
  var onZhou = null;      // 回调：州被点选
  var onXian = null;      // 回调：县被点选

  function init() {
    map = L.map("map", {
      attributionControl: false, zoomControl: true,
      center: CONF.center, zoom: CONF.zoom,
      maxBounds: CONF.bounds, maxBoundsViscosity: .55,
      minZoom: 4, maxZoom: 10,
    });
    var c = BASEMAPS.physical;
    tileLayer = L.tileLayer(c.url, { maxZoom: c.maxZoom, maxNativeZoom: c.maxNative });
    tileLayer.addTo(map);
    tileLayer.on("tileerror", function () { tileErrs++; });
    xianLayer.addTo(map);
    zhouLayer.addTo(map);
    map.on("zoomend", renderXian);
    map.on("click", function () { if (typeof HYAPP !== "undefined" && HYAPP.deselect) HYAPP.deselect(); });
  }

  function daoOf(z) { return z.dao; }
  function colorOf(z) {
    return daoColorMode ? (DAOCOLORS[daoOf(z)] || "#8b8069") : "#2f5d70";
  }

  /* ── 州治印章点 ── */
  function render() {
    zhouLayer.clearLayers();
    var shown = HY.zhou.filter(function (z) { return z.c && (!selDao || z.dao === selDao); });
    shown.forEach(function (z) {
      var sel = z.n === selName;
      var size = z.xian.length >= 10 ? 17 : z.xian.length >= 5 ? 14 : 12;
      var icon = L.divIcon({
        className: "",
        html: '<span class="zhoudot' + (sel ? " sel" : "") + '" style="width:' + size + "px;height:" + size +
              "px;color:" + colorOf(z) + ";font-size:" + (size - 4) + 'px">' + z.n.charAt(0) + "</span>",
        iconSize: [size, size], iconAnchor: [size / 2, size / 2],
      });
      var m = L.marker(z.c, { icon: icon });
      m.bindTooltip(z.n + (z.now ? " · 今" + z.now : "") + " · " + z.xian.length + "縣",
        { direction: "top", opacity: .95, className: "ftip" });
      m.on("click", function (e) {
        L.DomEvent.stopPropagation(e);
        onZhou && onZhou(z);
      });
      m.addTo(zhouLayer);
    });
    /* 未定位州：不入图（计数见关于页） */
  }

  /* ── 县微点（附郭=州治；三角化推算 zoom≥6） ── */
  function renderXian() {
    xianLayer.clearLayers();
    if (!map || map.getZoom() < 6) return;
    var box = map.getBounds();
    HY.zhou.forEach(function (z) {
      if (selDao && z.dao !== selDao) return;
      if (!z.c || !box.contains(z.c)) return;
      z.xian.forEach(function (x) {
        if (!x.c || x.src === "fu") return;   // 附郭与州印重合, 不叠点
        var dot = L.circleMarker(x.c, {
          radius: 2.6, color: "rgba(246,239,220,.85)", weight: 1,
          fillColor: colorOf(z), fillOpacity: x.src === "tri" ? .85 : 1,
        });
        dot.bindTooltip(x.n + "縣" + (x.d ? " · " + x.d + "（三角化推算）" : "") + " · 隸" + z.n,
          { direction: "top", opacity: .95, className: "ftip" });
        dot.on("click", function (e) {
          L.DomEvent.stopPropagation(e);
          onXian && onXian(z, x);
        });
        dot.addTo(xianLayer);
      });
    });
  }

  function select(name, opt) {
    selName = name;
    var z = HY.zhou.find(function (x) { return x.n === name; });
    render();
    renderXian();
    if (z && z.c && (!opt || opt.fly !== false)) {
      map.flyTo(z.c, Math.max(map.getZoom(), 6.6), { duration: 1.0 });
    }
  }
  function selectDao(dao) {
    selDao = dao ? ((HY.daos.find(function (d) { return d.id === dao; }) || {}).name || dao) : null;
    render();
    renderXian();
    if (dao) {
      var pts = HY.zhou.filter(function (z) { return z.dao === dao && z.c; }).map(function (z) { return z.c; });
      if (pts.length) map.flyToBounds(L.latLngBounds(pts).pad(.22), { duration: 1.1 });
    }
  }
  function toggleDaoColor() {
    daoColorMode = !daoColorMode;
    render();
    renderXian();
    return daoColorMode;
  }

  function flyTo(c, zoom) { map.flyTo(c, zoom || 7, { duration: .9 }); }

  return {
    init: init, render: render, renderXian: renderXian,
    select: select, selectDao: selectDao, toggleDaoColor: toggleDaoColor, flyTo: flyTo,
    get map() { return map; },
    set onZhou(fn) { onZhou = fn; },
    set onXian(fn) { onXian = fn; },
  };
})();
window.HYMAP = HYMAP;
