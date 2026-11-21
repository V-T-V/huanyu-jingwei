/* ═══════════ 寰宇经纬 · 全书全文检索（懒加载分片 + Worker） ═══════════ */

var HYFULL = (() => {
  var loadedDaos = {};

  function ensureAll(cb) {
    var files = (window.HYTEXT_MANIFEST) ? HYTEXT_MANIFEST : [];
    /* 无 manifest 时从 data/text/manifest.json 拉 */
    if (!files.length) {
      fetch((window.HYTEXT_BASE || "data/text/") + "manifest.json?v=1").then(function (r) { return r.json(); }).then(function (m) {
        window.HYTEXT_MANIFEST = m.files;
        loadAll(m.files, cb);
      });
      return;
    }
    loadAll(files, cb);
  }

  function loadAll(files, cb) {
    var todo = files.filter(function (f) { return !loadedDaos[f.id]; });
    if (!todo.length) { cb(files); return; }
    var done = 0;
    todo.forEach(function (f) {
      var s = document.createElement("script");
      s.src = (window.HYTEXT_BASE || "data/text/") + f.id + ".js?v=1";
      s.onload = function () {
        loadedDaos[f.id] = true;
        done++;
        cb(files, done / todo.length);
        if (done === todo.length) cb(files);
      };
      s.onerror = function () { done++; if (done === todo.length) cb(files); };
      document.head.appendChild(s);
    });
  }

  function run(term) {
    if (!term || term.length < 2) {
      HYPANEL.openFulltextInfo && HYPANEL.openFulltextInfo();
      return;
    }
    var pbody = HYPANEL.pbody;
    document.getElementById("vname").textContent = "全書檢索 · " + term;
    document.getElementById("vseal").textContent = "檢索";
    document.getElementById("pmeta").innerHTML = "<span>懶加載分片掃描</span>";
    pbody.className = "";
    pbody.innerHTML = '<div class="p-kicker">全文檢索</div><div class="kv" id="ftprog">正在加载全文分片……</div>';
    document.getElementById("panel").classList.add("open");
    document.body.classList.remove("nopanel");

    ensureAll(function (files, prog) {
      if (prog != null && prog < 1) {
        var el = document.getElementById("ftprog");
        if (el) el.textContent = "加载分片 " + Math.round(prog * 100) + "% ……";
        return;
      }
      if (!files.length) return;
      var filesSorted = files.slice().sort(function (a, b) { return a.vols[0] - b.vols[0]; });
      var progEl = document.getElementById("ftprog");
      ftWorkerStart(filesSorted, term, function (msg) {
        if (msg.error) {
          if (progEl) progEl.textContent = "Worker 不可用：" + msg.error;
          return;
        }
        if (msg.prog != null) {
          if (progEl) progEl.textContent = "掃描 " + msg.prog + "/" + msg.of + " 卷……";
          return;
        }
        if (msg.done) {
          renderResult(term, msg);
        }
      });
    });
  }

  function renderResult(term, msg) {
    var pbody = HYPANEL.pbody;
    var secs = msg.secs || [];
    secs.sort(function (a, b) { return b.n - a.n; });
    var html = '<div class="p-kicker">檢索「' + term + "」</div>" +
      '<div class="kv">全書命中 <b>' + msg.hits.toLocaleString() + "</b> 處 · 涉及 " + secs.length + " 卷（前 40 卷示片段）</div>";
    if (!secs.length) {
      html += '<div class="hint">无命中。或为异体字（本站已归并 關/闗、劍/劒、潁/頴 三组，其餘異體未歸）。</div>';
    }
    secs.forEach(function (s) {
      var daoObj = HY.daos.filter(function (d) { return d.name === s.dao; })[0];
      html += '<div class="sr2" data-dao="' + (daoObj ? daoObj.id : "") + '" data-vol="' + s.v +
        '" style="padding:7px 10px;border-bottom:1px solid var(--line2);cursor:pointer">' +
        '<b style="color:var(--teal)">' + s.dao + " · 卷" + s.v + "</b>" +
        '<span style="font-family:var(--sans);font-size:10px;color:var(--ink2);margin-left:6px">' + s.n + " 處</span>" +
        '<div style="font-size:12.5px;color:var(--ink2);margin-top:2px">……' +
        s.snip.replace(new RegExp("(" + term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "g"),
          '<mark style="background:rgba(178,58,46,.25)">$1</mark>') + "……</div></div>";
    });
    pbody.innerHTML = html;
    pbody.querySelectorAll(".sr2").forEach(function (el) {
      el.onclick = function () {
        var daoId = el.dataset.dao;
        if (!daoId) return;
        HYREADER.openDao(daoId).then ? null : null;
        /* 打开后定位命中 */
        HYREADER.openDao(daoId, true).then(function () {
          HYAPP.highlightTerm(term);
        }).catch(function () {});
      };
    });
  }

  return { run: run };
})();
window.HYFULL = HYFULL;
