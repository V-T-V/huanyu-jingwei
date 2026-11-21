/* ═══════════ 寰宇经纬 · 应用主控（模式 / 深链 / 启动） ═══════════ */

var HYAPP = (() => {
  var mode = "yutu";
  var st = { dao: null, zhou: null, search: null };

  function setMode(m) {
    mode = m;
    document.querySelectorAll("#modes .mode").forEach(function (b) {
      b.classList.toggle("active", b.dataset.mode === m);
    });
    document.body.className = document.body.className.replace(/m-\w+/g, "").trim() + " m-" + m;
    document.getElementById("modelabel").textContent =
      m === "yutu" ? "舆图" : m === "fen" ? "分道" : "关于";
    document.getElementById("modenote") && (document.getElementById("modenote").textContent =
      m === "yutu" ? DAO_NOTE.yutu : m === "fen" ? DAO_NOTE.fen : DAO_NOTE.about);
    if (m === "about") HYPANEL.openAbout();
  }

  function openDao(daoId, fly) {
    var d = HY.daos.find(function (x) { return x.id === daoId; });
    if (!d) return;
    st.dao = daoId; st.zhou = null;
    setMode("yutu");
    HYMAP.selectDao(daoId);
    HYRAIL.expand(daoId);
    HYPANEL.openDao(daoId);
    syncHash();
  }

  function openZhou(name) {
    var z = HY.zhou.find(function (x) { return x.n === name; });
    if (!z) return;
    st.dao = (HY.daos.find(function (d) { return d.name === z.dao; }) || {}).id || null;
    st.zhou = name;
    setMode("yutu");
    HYMAP.select(name);
    if (st.dao) HYRAIL.expand(st.dao);
    HYRAIL.highlightZhou(name);
    HYPANEL.openZhou(z);
    syncHash();
  }

  /* 阅读态内点州条目：仅切面板，不退出阅读 */
  function openZhouCardOnly(name) {
    var z = HY.zhou.find(function (x) { return x.n === name; });
    if (z) HYPANEL.openZhou(z);
    st.zhou = name;
  }

  function deselect() {
    st.dao = null; st.zhou = null;
    HYMAP.selectDao(null);
    HYMAP.select(null);
    HYRAIL.highlightZhou(null);
    syncHash();
  }

  function syncHash() {
    var h = [];
    h.push("mode=" + mode);
    if (st.dao) h.push("dao=" + st.dao);
    if (st.zhou) h.push("zhou=" + encodeURIComponent(st.zhou));
    if (st.search) h.push("search=" + encodeURIComponent(st.search));
    if (HYREADER.curDao && mode === "fen") h.push("read=" + HYREADER.curDao);
    history.replaceState(null, "", "#" + h.join("&"));
  }

  function fromHash() {
    var q = {};
    location.hash.replace(/^#/, "").split("&").forEach(function (kv) {
      var p = kv.split("=");
      q[p[0]] = decodeURIComponent(p[1] || "");
    });
    if (q.zhou && HY.zhou.some(function (z) { return z.n === q.zhou; })) { openZhou(q.zhou); return; }
    if (q.dao && HY.daos.some(function (d) { return d.id === q.dao; })) { openDao(q.dao); }
    if (q.read && q.read !== "undefined") { HYREADER.openDao(q.read); }
    if (q.search) {
      var si = document.getElementById("search");
      si.value = q.search;
      HYSEARCH.run(q.search);
    }
    if (q.mode === "about") setMode("about");
  }

  /* 全文检索定位后高亮 */
  function highlightTerm(term) {
    var pbody = HYPANEL.pbody;
    var html = pbody.innerHTML;
    try {
      var re = new RegExp("(" + term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "g");
      pbody.innerHTML = html.replace(re, "<mark>$1</mark>");
    } catch (e) {}
  }

  function elBind(id) { var el = document.getElementById(id); return el || { set onclick(f) {} }; }
  function bindUI() {
    document.querySelectorAll("#modes .mode").forEach(function (b) {
      b.onclick = function () { setMode(b.dataset.mode); if (b.dataset.mode === "about") syncHash(); };
    });
    elBind("pclose").onclick = function () {
      HYPANEL.hide();
      HYREADER.close();
    };
    document.getElementById("bmtoggle");
    elBind("daotoggle").onclick = function () {
      var on = HYMAP.toggleDaoColor();
      this.classList.toggle("on", on);
      this.textContent = on ? "◈ 道色" : "◈ 单色";
    };
    elBind("wanderlink").onclick = function () {
      var zs = HY.zhou.filter(function (z) { return z.c; });
      var z = zs[Math.floor(Math.random() * zs.length)];
      openZhou(z.n);
    };
    elBind("ftlink").onclick = function () {
      var q = document.getElementById("search").value.trim();
      if (q) HYFULL.run(q);
      else {
        document.getElementById("vname").textContent = "全書檢索";
        document.getElementById("vseal").textContent = "檢索";
        document.getElementById("pmeta").innerHTML = "<span>懶加載掃描</span>";
        HYPANEL.pbody.className = "";
        HYPANEL.pbody.innerHTML = '<div class="p-kicker">全書全文檢索</div><div class="kv">頂欄輸入詞句（≥2 字）後回車，'
          + "或點「🔍 全文」——按需加載 <b>" + (HY.stats.total_chars || 0).toLocaleString() +
          "</b> 字原文（十四分片）掃描命中，Worker 纯数据计算。</div>";
        document.getElementById("panel").classList.add("open");
        document.body.classList.remove("nopanel");
      }
    };
    elBind("nightlink").onclick = function () {
      document.body.classList.toggle("night");
      try { localStorage.setItem("hynight", document.body.classList.contains("night") ? "1" : ""); } catch (e) {}
    };
    elBind("rprev").onclick = function () { HYREADER.nav(-1); };
    elBind("rnext").onclick = function () { HYREADER.nav(1); };
    elBind("rtop").onclick = function () {
      var d = HYREADER.curDao || st.dao;
      if (d) HYREADER.openDao(d);
    };
    var go = document.querySelector("#boot .go");
    if (go) go.onclick = function () {
      document.getElementById("boot").classList.add("off");
    };
    var bt = document.getElementById("boot");
    if (bt) bt.addEventListener("click", function (e) {
      if (e.target.id === "boot") bt.classList.add("off");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        HYPANEL.hide();
        HYREADER.close();
        document.getElementById("sresults").classList.remove("open");
      }
    });
  }

  var _inited = false;
  function init() {
    if (_inited) return;
    _inited = true;
    HYMAP.init();
    HYMAP.render();
    HYRAIL.build();
    HYSEARCH.init();
    bindUI();
    try {
      if (localStorage.getItem("hynight")) document.body.classList.add("night");
    } catch (e) {}
    /* 底栏统计 */
    var s = HY.stats;
    document.getElementById("bookstat").textContent =
      "存卷 " + s.vols_got + "/200 · 府州 " + s.zhou_count + " · 縣 " + s.xian_count;
    HYMAP.onZhou = function (z) { openZhou(z.n); };
    HYMAP.onXian = function (z, x) { HYPANEL.openXian(z, x); };
    fromHash();
    if (!location.hash) setTimeout(function () {
      var b = document.getElementById("boot");
      if (b) b.classList.add("off");
    }, 2600);
  }

  function setSearch(q) { st.search = q || null; syncHash(); }

  return { init: init, setMode: setMode, openDao: openDao, openZhou: openZhou, setSearch: setSearch,
           openZhouCardOnly: openZhouCardOnly, deselect: deselect, syncHash: syncHash,
           highlightTerm: highlightTerm, get mode() { return mode; } };
})();

window.addEventListener("DOMContentLoaded", function () { HYAPP.init(); });
window.HYAPP = HYAPP;
