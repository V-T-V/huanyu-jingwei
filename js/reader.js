/* ═══════════ 寰宇经纬 · 分道而读（懒加载全文 + 州锚点） ═══════════ */

var HYREADER = (() => {
  var curDao = null, curZhou = null, mark = null;
  var pbody = document.getElementById("pbody");

  /* 懒加载分片 data/text/{dao}.js */
  var cache = {};
  function ensureDao(daoId) {
    if (cache[daoId] || window.HYTEXT && HYTEXT[daoId]) {
      cache[daoId] = cache[daoId] || HYTEXT[daoId];
      return Promise.resolve(cache[daoId]);
    }
    if (ensureDao._p && ensureDao._p[daoId]) return ensureDao._p[daoId];
    ensureDao._p = ensureDao._p || {};
    ensureDao._p[daoId] = new Promise(function (ok, bad) {
      var s = document.createElement("script");
      s.src = (window.HYTEXT_BASE || "data/text/") + daoId + ".js?v=7";
      s.onload = function () { cache[daoId] = HYTEXT[daoId]; ok(HYTEXT[daoId]); };
      s.onerror = function () { bad(new Error("分片加载失败 " + daoId)); };
      document.head.appendChild(s);
    });
    return ensureDao._p[daoId];
  }

  function daoIdOf(daoName) {
    var d = HY.daos.find(function (x) { return x.name === daoName; });
    return d ? d.id : null;
  }

  /* 段落 → HTML（「　　」顶格 = 条目头；标州锚） */
  function renderParas(vols, zhouFilter) {
    var html = "";
    vols.forEach(function (v) {
      html += '<div class="rpara volhead">太平寰宇記卷' + v.v + " · " + v.ch.toLocaleString() + " 字</div>";
      v.p.forEach(function (p, i) {
        var cls = "rpara";
        var headTxt = p.replace(/^\u3000\u3000/, "");
        var isEntry = p.indexOf("\u3000\u3000") === 0;
        /* 州名锚：条目头以某州名开头 */
        var anchor = null;
        if (isEntry) {
          for (var z = 0; z < HY.zhou.length; z++) {
            var zn = HY.zhou[z].n;
            if (headTxt.indexOf(zn) === 0) {
              var after = headTxt.charAt(zn.length);
              if (!after || "\u3000，。、；：（(".indexOf(after) >= 0 || /[\u4e00-\u9fff]{0,3}(今理|郡理|郡)/.test(headTxt.slice(zn.length, zn.length + 6))) {
                anchor = zn;
                break;
              }
            }
          }
        }
        if (anchor) {
          cls += " entry readanchor";
          html += '<div class="' + cls + '" data-z="' + anchor + '" id="an-' + anchor + '">' +
            '<span class="etag">' + anchor + "</span>" + headTxt.slice(anchor.length) + "</div>";
        } else if (isEntry) {
          cls += " entry";
          html += '<div class="' + cls + '"><span class="etag" style="color:var(--gold);border-color:rgba(160,119,47,.4)">◆</span>' + headTxt + "</div>";
        } else {
          html += '<div class="' + cls + '">' + p + "</div>";
        }
      });
    });
    return html;
  }

  function markHits(html, term) {
    if (!term) return html;
    try {
      var re = new RegExp("(" + term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "g");
      return html.replace(re, "<mark>$1</mark>");
    } catch (e) { return html; }
  }

  async function openDao(daoId, keepPanel) {
    curDao = daoId; curZhou = null; mark = null;
    var d = HY.daos.find(function (x) { return x.id === daoId; });
    if (!d) return;
    var vols;
    try { vols = await ensureDao(daoId); }
    catch (e) {
      HYPANEL.pbody.innerHTML = '<div class="hint">分片加载失败：' + e.message + "</div>";
      return;
    }
    if (typeof HYAPP !== "undefined") HYAPP.setMode("fen");
    document.getElementById("vname").textContent = d.name + " · 原文";
    document.getElementById("vseal").textContent = "分道";
    document.getElementById("pmeta").innerHTML =
      "<span>" + d.vols.length + " 卷 · " + vols.reduce(function (s, v) { return s + v.ch; }, 0).toLocaleString() + " 字</span>" +
      '<span>州条目朱标 · 點之跳州</span>';
    pbody.className = "reading";
    pbody.innerHTML = renderParas(vols);
    pbody.scrollTop = 0;
    document.getElementById("panel").classList.add("open");
    document.body.classList.remove("nopanel");
    document.getElementById("readerbar").classList.remove("hidden");
    document.getElementById("rprog").textContent = d.name + " · 分道而讀";
    bindEntryClicks();
    syncHash();
  }

  async function openZhou(z) {
    curZhou = z.n; mark = null;
    var daoId = daoIdOf(z.dao);
    if (!daoId) return;
    var vols;
    try { vols = await ensureDao(daoId); }
    catch (e) { return; }
    if (typeof HYAPP !== "undefined") HYAPP.setMode("fen");
    /* 只显示该州所在卷 + 滚动到州锚 */
    var volNos = z.vols;
    var sub = vols.filter(function (v) { return volNos.indexOf(v.v) >= 0; });
    document.getElementById("vname").textContent = z.n + " · 原文";
    document.getElementById("vseal").textContent = "州文";
    document.getElementById("pmeta").innerHTML = "<span>卷" + volNos.join("·") + "</span><span>" + z.dao + "</span>";
    pbody.className = "reading";
    pbody.innerHTML = renderParas(sub);
    document.getElementById("panel").classList.add("open");
    document.body.classList.remove("nopanel");
    document.getElementById("readerbar").classList.remove("hidden");
    document.getElementById("rprog").textContent = z.n + " · 原文";
    bindEntryClicks();
    var an = document.getElementById("an-" + z.n);
    if (an) {
      an.scrollIntoView({ block: "start" });
      an.style.transition = "background .8s";
      an.style.background = "rgba(178,58,46,.14)";
      setTimeout(function () { an.style.background = ""; }, 1800);
    }
    syncHash();
  }

  function bindEntryClicks() {
    pbody.querySelectorAll(".rpara.entry[data-z]").forEach(function (el) {
      el.addEventListener("click", function () {
        var zn = el.dataset.z;
        var zz = HY.zhou.find(function (q) { return q.n === zn; });
        if (zz && zz.c) HYMAP.select(zn);
        HYRAIL.highlightZhou(zn);
        /* 阅读态内点击州条目 → 面板切州详情（图随动） */
        if (typeof HYAPP !== "undefined" && HYAPP.openZhouCardOnly) HYAPP.openZhouCardOnly(zn);
      });
    });
  }

  /* 供县卡取县条目原文（懒加载后台静默） */
  function parasOfZhou(z, cb) {
    var daoId = daoIdOf(z.dao);
    if (!daoId) { cb(null); return; }
    ensureDao(daoId).then(function (vols) {
      var sub = vols.filter(function (v) { return z.vols.indexOf(v.v) >= 0; });
      var ps = [];
      sub.forEach(function (v) { ps = ps.concat(v.p); });
      cb(ps);
    }).catch(function () { cb(null); });
  }

  /* 阅读底条：上一州 / 下一州 */
  function nav(dir) {
    var z = HY.zhou.find(function (q) { return q.n === (curZhou || firstOfDao()); });
    var list = HY.zhou.filter(function (q) { return q.dao === (z ? z.dao : null); });
    var i = list.indexOf(z);
    var nz = list[(i + dir + list.length) % list.length];
    if (nz) openZhou(nz);
  }
  function firstOfDao() {
    var d = HY.daos.find(function (x) { return x.id === curDao; });
    if (!d) return null;
    var z = HY.zhou.find(function (q) { return q.dao === d.name; });
    return z ? z.n : null;
  }

  function close() {
    curDao = null; curZhou = null;
    document.getElementById("readerbar").classList.add("hidden");
  }

  function syncHash() {
    if (typeof HYAPP !== "undefined" && HYAPP.syncHash) HYAPP.syncHash();
  }

  return { openDao: openDao, openZhou: openZhou, parasOfZhou: parasOfZhou,
           nav: nav, close: close, renderParas: renderParas, markHits: markHits,
           get curDao() { return curDao; }, get curZhou() { return curZhou; } };
})();
window.HYREADER = HYREADER;
