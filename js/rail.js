/* ═══════════ 寰宇经纬 · 左列纲目（十三道 → 州名录） ═══════════ */

var HYRAIL = (() => {
  var expanded = null;    // 当前展开的道 id

  function build() {
    var host = document.getElementById("raillist");
    var sub = document.getElementById("railsub");
    var zc = HY.zhou.length;
    sub.textContent = "府州軍監 " + zc + " · 縣 " + HY.stats.xian_count;
    var html = "";
    HY.daos.forEach(function (d) {
      var color = DAOCOLORS[d.id] || "#8b8069";
      var vols = "卷" + d.vols[0] + (d.vols.length > 1 ? "–" + d.vols[d.vols.length - 1] : "");
      html += '<div class="ri" data-dao="' + d.id + '">' +
        '<span class="dot" style="color:' + color + '"></span>' +
        '<span><span class="nm">' + d.name + '</span><span class="ju">' + vols + "</span></span>" +
        '<span class="ct">' + d.zc + "州</span></div>";
      if (expanded === d.id) {
        var zs = HY.zhou.filter(function (z) { return z.dao === d.name; });
        html += '<div class="zlist">';
        zs.forEach(function (z) {
          html += '<div class="zrow" data-z="' + z.n + '">' + z.n +
            '<span class="no">' + (z.c ? z.xian.length + "縣" : "未定位") + "</span></div>";
        });
        html += "</div>";
      }
    });
    host.innerHTML = html;
    host.querySelectorAll(".ri").forEach(function (el) {
      el.onclick = function () {
        var id = el.dataset.dao;
        expanded = (expanded === id) ? null : id;
        highlightDao(expanded);
        HYAPP.openDao(expanded || id, expanded ? true : false);
        build();
      };
    });
    host.querySelectorAll(".zrow").forEach(function (el) {
      el.onclick = function (e) { e.stopPropagation(); HYAPP.openZhou(el.dataset.z); };
    });
    highlightDao(expanded);
  }

  function highlightDao(id) {
    document.querySelectorAll("#raillist .ri").forEach(function (el) {
      el.classList.toggle("on", el.dataset.dao === id);
    });
  }
  function highlightZhou(name) {
    document.querySelectorAll("#raillist .zrow").forEach(function (el) {
      el.classList.toggle("cur", el.dataset.z === name);
    });
  }
  function expand(daoId) { expanded = daoId; build(); }

  return { build: build, highlightZhou: highlightZhou, expand: expand, get expanded() { return expanded; } };
})();
window.HYRAIL = HYRAIL;
