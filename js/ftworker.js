/* ═══════════ 寰宇经纬 · 全文检索 Worker（纯数据，无 DOM） ═══════════
   主线程依次 fetch 分片 → transfer 文本 → Worker 统计命中与片段 */
var FTW = null;

function ftWorkerStart(files, term, cb) {
  if (typeof Worker === "undefined") { cb({ error: "no worker" }); return; }
  var src = `
    var total = { hits: 0, secs: [] };
    onmessage = function (e) {
      var d = e.data;
      if (d.done) { postMessage({ done: true, hits: total.hits, secs: total.secs.slice(0, 40) }); return; }
      var t = d.text, term = d.term, n = 0, idx = 0, snippets = [];
      while ((idx = t.indexOf(term, idx)) >= 0) { n++; idx += term.length; }
      if (n > 0) {
        /* 片段：前 2 处 */
        var i1 = t.indexOf(term);
        var s1 = Math.max(0, i1 - 30);
        snippets.push(t.slice(s1, s1 + 74).replace(/\\s/g, ""));
      }
      total.hits += n;
      for (var k = 0; k < snippets.length; k++) total.secs.push({ v: d.vol, dao: d.dao, snip: snippets[k], n: n });
      postMessage({ prog: d.i + 1, of: d.of });
    };
  `;
  var blob = new Blob([src], { type: "text/javascript" });
  var w = new Worker(URL.createObjectURL(blob));
  w.onmessage = function (e) {
    cb(e.data);
  };
  /* 主线程逐分片逐卷喂文本 */
  var vi = 0;
  var daoNames = {};
  HY.daos.forEach(function (d) { daoNames[d.id] = d.name; });
  var flat = [];
  files.forEach(function (f) {
    var vols = HYTEXT[f.id] || [];
    vols.forEach(function (v) { flat.push({ id: f.id, v: v.v, text: v.p.join("\n") }); });
  });
  function feed() {
    if (vi >= flat.length) { w.postMessage({ done: 1 }); return; }
    var it = flat[vi];
    w.postMessage({ text: it.text, term: term, vol: it.v, dao: daoNames[it.id] || it.id, i: vi, of: flat.length });
    vi++;
  }
  w.onmessage = function (e) {
    var d = e.data;
    if (d.done) { cb(d); w.terminate(); return; }
    cb({ prog: d.prog, of: d.of });
    feed();
  };
  feed();
}
