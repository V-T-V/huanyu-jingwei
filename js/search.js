/* ═══════════ 寰宇经纬 · 名录检索（州·县·道） ═══════════ */

var HYSEARCH = (() => {
  var box = document.getElementById("search");
  var res = document.getElementById("sresults");

  function run(q) {
    if (!q || q.length < 1) { res.classList.remove("open"); if (HYAPP.setSearch) HYAPP.setSearch(null); return; }
    if (typeof HYAPP !== "undefined" && HYAPP.setSearch) HYAPP.setSearch(q);
    var hits = [];
    /* 道名 */
    HY.daos.forEach(function (d) {
      if (d.name.indexOf(q) >= 0) {
        hits.push({ k: "道", t: d.name, s: "卷" + d.vols[0] + "–" + d.vols[d.vols.length - 1] + " · " + d.zc + "州",
                    go: function () { HYAPP.openDao(d.id); } });
      }
    });
    /* 州名 */
    HY.zhou.forEach(function (z) {
      if (z.n.indexOf(q) >= 0) {
        hits.push({ k: "州", t: z.n, s: z.dao + (z.now ? " · 今" + z.now : " · 未定位") + " · " + z.xian.length + "縣",
                    go: function () { HYAPP.openZhou(z.n); } });
      }
    });
    /* 县名 */
    HY.zhou.forEach(function (z) {
      z.xian.forEach(function (x) {
        if (x.n.indexOf(q) >= 0 && x.n !== z.n) {
          hits.push({ k: "縣", t: x.n + "縣", s: "隸" + z.n + " · " + z.dao + (x.d ? " · " + x.d : ""),
                      go: function () {
                        if (x.c) HYMAP.flyTo(x.c, 7.5);
                        HYPANEL.openXian(z, x);
                      } });
        }
      });
    });
    if (!hits.length) {
      res.innerHTML = '<div class="sr" style="cursor:default;color:var(--ink2)">名录无「' + q +
        '」——回车在全书原文中检索</div>';
      res.classList.add("open");
      return;
    }
    res.innerHTML = hits.slice(0, 16).map(function (h, i) {
      return '<div class="sr" data-i="' + i + '"><b>' + h.t + '</b><span class="sk">' + h.k +
        "</span><span class='snip'>" + h.s + "</span></div>";
    }).join("") + (hits.length > 16 ? '<div class="sr" style="cursor:default;color:var(--ink2)">…共 ' +
      hits.length + " 条</div>" : "") +
      '<div class="ftmore" id="ftmore">🔍 在全书 ' + (HY.stats.total_chars || 0).toLocaleString() +
      " 字原文中检索「" + q + "」</div>";
    res.classList.add("open");
    res.querySelectorAll(".sr[data-i]").forEach(function (el) {
      el.onclick = function () { hits[+el.dataset.i].go(); res.classList.remove("open"); };
    });
    var fm = document.getElementById("ftmore");
    if (fm) fm.onclick = function () { HYFULL.run(q); res.classList.remove("open"); };
  }

  function init() {
    var t = null;
    box.addEventListener("input", function () {
      clearTimeout(t);
      t = setTimeout(function () { run(box.value.trim()); }, 160);
    });
    box.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        var q = box.value.trim();
        if (!q) return;
        run(q);
        var first = res.querySelector(".sr[data-i]");
        if (first) { first.click(); }
        else { HYFULL.run(q); res.classList.remove("open"); }
      }
      if (e.key === "Escape") { res.classList.remove("open"); box.blur(); }
    });
    document.addEventListener("click", function (e) {
      if (!document.getElementById("searchwrap").contains(e.target)) res.classList.remove("open");
    });
  }

  return { init: init, run: run };
})();
window.HYSEARCH = HYSEARCH;
