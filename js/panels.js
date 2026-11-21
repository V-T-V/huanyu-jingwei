/* ═══════════ 寰宇经纬 · 面板（道 / 州 / 县 / 对照 / 关于） ═══════════ */

var HYEXPORT = (() => {
  /* 导出（与 tools/export_data.py 同口径）：CSV 带 BOM / KML / GeoJSON */
  function typ(n) {
    if (n.slice(-1) === "府") return "府";
    if (n.slice(-1) === "軍") return "军";
    if (n.slice(-1) === "監") return "监";
    if (n.slice(-1) === "州") return "州";
    return "州";
  }
  function esc(v) {
    v = String(v);
    return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  }
  function save(name, text, mime) {
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type: mime }));
    a.download = name;
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 3000);
  }
  function csv(name, head, rows) {
    var NL = String.fromCharCode(10), BOM = String.fromCharCode(0xFEFF);
    save(name, BOM + head.join(",") + NL +
      rows.map(function (r) { return r.map(esc).join(","); }).join(NL),
      "text/csv;charset=utf-8");
  }
  function zhouRows() {
    return HY.zhou.map(function (z) {
      return [z.dao, z.n, typ(z.n), z.vols.join("·"), z.now || "",
        z.c ? z.c[0].toFixed(2) : "", z.c ? z.c[1].toFixed(2) : "",
        z.cf || "", z.src || "", z.c ? "" : "未定位（坐标表未收，舆图不上点）"];
    });
  }
  function xianRows() {
    var out = [];
    HY.zhou.forEach(function (z) {
      (z.xian || []).forEach(function (x) {
        if (!x.c) return;
        var fu = x.src === "fu";
        out.push([z.dao, z.n, x.n, x.c[0].toFixed(2), x.c[1].toFixed(2),
          fu ? "附郭" : "三角化", x.d || "",
          fu ? "附郭县取州治坐标" : "以州治为极点按原载方位里程推算（1里≈0.55km），方法近似精度±20%"]);
      });
    });
    return out;
  }
  function points() {
    var pts = [];
    HY.zhou.forEach(function (z) {
      if (z.c) pts.push([z.n, z.c, z.dao + " · 今" + (z.now || "") + (z.cf ? "（" + z.cf + "）" : "")]);
      (z.xian || []).forEach(function (x) {
        if (x.c) pts.push([x.n + "縣", x.c,
          (x.src === "fu" ? "附郭" : "三角化±20%") + " · 隶" + z.n + (x.d ? "（" + x.d + "）" : "")]);
      });
    });
    return pts;
  }
  return {
    zhouCsv: function () {
      csv("寰宇经纬-府州对照.csv",
        ["道", "州名", "类型", "卷", "今地依据", "纬度", "经度", "置信", "src", "未定位"], zhouRows());
    },
    xianCsv: function () {
      csv("寰宇经纬-县对照.csv",
        ["道", "州名", "县名", "纬度", "经度", "定位方法", "原载方位里程", "备注"], xianRows());
    },
    kml: function () {
      var pts = points();
      var pins = pts.map(function (p) {
        return "<Placemark><name>" + p[0] + "</name><description>" + p[2] + "</description>" +
          "<Point><coordinates>" + p[1][1].toFixed(4) + "," + p[1][0].toFixed(4) + ",0</coordinates></Point></Placemark>";
      }).join("");
      save("寰宇经纬-州县点位.kml",
        '<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document>' +
        "<name>寰宇经纬·州县点位</name>" +
        "<description>宋·太平寰宇记 255 州治 + 626 上图县；三角化县点为示意坐标（±20%）</description>" +
        pins + "</Document></kml>", "application/vnd.google-earth.kml+xml");
    },
    geojson: function () {
      var feats = [];
      HY.zhou.forEach(function (z) {
        if (z.c) feats.push({ type: "Feature",
          geometry: { type: "Point", coordinates: [z.c[1], z.c[0]] },
          properties: { 名: z.n, 类: typ(z.n), 道: z.dao, 今地: z.now || "",
            置信: z.cf || "", src: z.src || "", 依据: "州治今地整编" } });
        (z.xian || []).forEach(function (x) {
          if (!x.c) return;
          feats.push({ type: "Feature",
            geometry: { type: "Point", coordinates: [x.c[1], x.c[0]] },
            properties: { 名: x.n, 类: "县", 道: z.dao, 隶: z.n,
              定位: x.src === "fu" ? "附郭=州治" : "三角化示意坐标(±20%)", 原载: x.d || "" } });
        });
      });
      save("寰宇经纬-州县点位.geojson",
        JSON.stringify({ type: "FeatureCollection", name: "寰宇经纬-州县点位", features: feats }),
        "application/geo+json");
    },
    xrefCsv: function () {
      var REL = { same: "同名", promo: "升府", rename: "改名", mzhou: "明属州", near: "近邻存疑", none: "无对应" };
      csv("寰宇经纬-宋明对照.csv",
        ["宋州", "道", "宋治今地", "关系", "明省", "明府", "对应单位", "明治今地", "证据", "备注"],
        HYXREF.rows.map(function (r) {
          return [r.z, r.dao, r.now, REL[r.rel], r.mpn, r.mf, r.mn, r.mnow,
            r.ev + (r.d != null ? "·" + r.d + "km" : ""), r.note];
        }));
    }
  };
})();
window.HYEXPORT = HYEXPORT;

var HYPANEL = (() => {
  var pbody = document.getElementById("pbody");
  var vname = document.getElementById("vname");
  var vseal = document.getElementById("vseal");
  var pmeta = document.getElementById("pmeta");

  function show(seal) {
    vseal.textContent = seal || "寰宇";
    document.getElementById("panel").classList.add("open");
    document.body.classList.remove("nopanel");
  }
  function hide() {
    document.getElementById("panel").classList.remove("open");
    document.body.classList.add("nopanel");
  }

  var EXL = { sizhi: "四至八到", fengsu: "風俗", hu: "户口", tugong: "土貢", tuchan: "土産",
              xingishi: "姓氏", renwu: "人物", jing: "州境" };

  function openDao(daoId) {
    var d = HY.daos.find(function (x) { return x.id === daoId; });
    if (!d) return;
    vname.textContent = d.name;
    pmeta.innerHTML = "<span>卷" + d.vols[0] + (d.vols.length > 1 ? "–" + d.vols[d.vols.length - 1] : "") +
      "</span><span>" + d.vols.length + " 卷</span><span>府州 " + d.zc + "</span>";
    var zs = HY.zhou.filter(function (z) { return z.dao === d.name; });
    var withC = zs.filter(function (z) { return z.c; }).length;
    var html = '<div class="p-kicker">分道總覽</div>';
    html += '<div class="kv">本道府州軍監 <b>' + zs.length + "</b> · 輿圖定位 <b>" + withC +
      "</b> · 屬縣 <b>" + zs.reduce(function (s, z) { return s + z.xian.length; }, 0) + "</b></div>";
    html += '<div class="p-kicker" style="margin-top:14px">州名錄 · 點行入州</div><div class="xchips">';
    zs.forEach(function (z) {
      html += '<span class="xchip' + (z.c ? "" : " nop") + '" data-z="' + z.n + '" title="' +
        (z.c ? "今" + z.now : "未定位") + '">' + z.n + "</span>";
    });
    html += "</div>";
    html += '<div class="btnrow"><button class="abtn solid" id="daoread">☰ 分道而讀——原卷全文</button></div>';
    html += '<div class="hint">「分道而讀」按需加载本道各卷全文（data/text/' + daoId + '.js），'
          + "卷内府州条目自动锚定，可逐州跳读。</div>";
    pbody.className = "";
    pbody.innerHTML = html;
    bindChips();
    document.getElementById("daoread").onclick = function () { HYREADER.openDao(daoId); };
    show("分道");
  }

  function openZhou(z) {
    vname.textContent = z.n;
    var metas = [];
    metas.push("<span>" + z.dao + "</span>");
    metas.push('<span>卷' + z.vols.join("·") + "</span>");
    if (z.jl) metas.push("<span>今理" + z.jl + "縣</span>");
    if (z.now) metas.push('<span title="定位依据：州治今地（agent 依地文学常识整编，src=derived）">今 ' + z.now +
      (z.cf ? " · " + z.cf : "") + "</span>");
    else metas.push('<span style="border-color:rgba(178,58,46,.5);color:#8a2a20">未定位</span>');
    pmeta.innerHTML = metas.join("");
    var html = "";
    if (z.yz) {
      html += '<div class="quote"><span class="ql">沿革（節）</span>' + z.yz.slice(0, 300) + "……</div>";
    }
    for (var k in EXL) {
      if (z.ex && z.ex[k]) {
        html += '<div class="quote"><span class="ql">' + EXL[k] + "</span>" +
          z.ex[k].slice(0, 200) + (z.ex[k].length > 200 ? "……" : "") + "</div>";
      }
    }
    html += '<div class="p-kicker" style="margin-top:14px">屬縣 ' + z.xian.length +
      (z.xc ? " · 縣條目原文 " + z.xc + " 段" : "") + "</div>";
    html += '<div class="xchips">';
    z.xian.forEach(function (x) {
      var tip = x.src === "fu" ? "附郭=州治" : x.src === "tri" ? "三角化推算（" + x.d + "）" : "未定位";
      html += '<span class="xchip' + (x.c ? "" : " nop") + '" data-x="' + x.n + '" data-zn="' + z.n +
        '" title="' + tip + '">' + x.n + (x.src === "fu" ? "·郭" : "") + "</span>";
    });
    html += "</div>";
    if (!z.c) html += '<div class="hint">此州未能定位（坐标表未收），舆图不上点——如实留白，俟考。</div>';
    html += '<div class="btnrow">';
    html += '<button class="abtn" id="zread">📖 阅原卷全文</button>';
    html += '<button class="abtn" id="zfly">➤ 圖上觀之</button>';
    html += "</div>";
    pbody.className = "";
    pbody.innerHTML = html;
    bindChips();
    document.getElementById("zread").onclick = function () { HYREADER.openZhou(z); };
    var fl = document.getElementById("zfly");
    if (fl) fl.onclick = function () { if (z.c) HYMAP.flyTo(z.c, 7.4); };
    show(z.dao.slice(0, 2));
  }

  function openXian(z, x) {
    vname.textContent = x.n + "縣";
    pmeta.innerHTML = "<span>隸" + z.n + "</span><span>" + z.dao + "</span>" +
      (x.d ? '<span>距州 ' + x.d + "</span>" : "<span>附郭</span>");
    var html = '<div class="p-kicker">縣 · 定位方法</div>';
    if (x.src === "fu") {
      html += '<div class="kv">附郭縣（州治所在）——取州治坐標 <b>' + (z.now || "") + "</b>。</div>";
    } else if (x.src === "tri") {
      html += '<div class="kv">原書縣條目載「<b>' + x.d + '</b>」至州——以州治為極點，方位角+里程（1 里≈0.55 km）'
            + "三角化推算，方法近似，精度 ±20% 量级。</div>";
    } else {
      html += '<div class="hint">未定位：县条目无方位里程句式或州未定位。</div>';
    }
    /* 县条目原文首段 */
    var para = null;
    if (z.xc) {
      HYREADER.parasOfZhou(z, function (ps) {
        if (!ps) return;
        for (var i = 0; i < ps.length; i++) {
          var h = ps[i].replace(/^\u3000\u3000/, "");
          if (h.indexOf(x.n + "縣") === 0) { para = ps[i]; break; }
        }
        if (para) {
          pbody.insertAdjacentHTML("beforeend",
            '<div class="quote"><span class="ql">縣條目原文（節）</span>' + para.replace(/^\u3000\u3000/, "").slice(0, 260) + "……</div>");
        }
      });
    }
    html += '<div class="btnrow"><button class="abtn" id="xback">↩ 回' + z.n + "</button></div>";
    pbody.className = "";
    pbody.innerHTML = html;
    document.getElementById("xback").onclick = function () { HYAPP.openZhou(z.n); };
    show("縣");
  }

  /* ── 明志对照（宋×明府州互查桥，data/xref_fy.js 管线产物）── */
  var XR_REL = { same: "同名", promo: "升府", rename: "改名", mzhou: "明属州",
                 near: "近邻存疑", none: "无对应" };

  function xrLink(r) {
    return "../HHH/#mode=" + encodeURIComponent("舆图") + "&p=" + r.mp +
      "&fu=" + encodeURIComponent(r.mf);
  }

  function xrRowHtml(r) {
    var tag = XR_REL[r.rel];
    var right;
    if (r.rel === "none") {
      right = '<span class="xrnone">' + (r.note || "无对应") + "</span>";
    } else if (r.rel === "near") {
      right = '<span class="xrnear">' + r.mpn + "·" + r.mf + "？</span>" +
        '<a class="xrjump" href="' + xrLink(r) + '" target="_blank" rel="noopener" ' +
        'title="坐标近邻存疑，仍可跳方舆查看">↗</a>';
    } else {
      right = "<span>" + r.mpn + " · " + (r.mn !== r.mf ? r.mf + "·" : "") + r.mn + "</span>" +
        '<a class="xrjump" href="' + xrLink(r) + '" target="_blank" rel="noopener" ' +
        'title="↗方舆经纬：' + r.mf + '">↗方舆</a>';
    }
    return '<div class="xrrow" data-z="' + r.z + '" data-rel="' + r.rel + '">' +
      '<span class="xrz" title="' + (r.now ? "今" + r.now : "未定位") + '">' + r.z + "</span>" +
      '<span class="xrtag t-' + r.rel + '">' + tag + "</span>" +
      '<span class="xrev" title="' + (r.ev || r.note || "") + '">' +
      (r.ev ? r.ev + (r.d != null ? "·" + r.d + "km" : "") : (r.note || "")) + "</span>" +
      '<span class="xrr">' + right + "</span></div>";
  }

  function openXref() {
    var X = HYXREF, st = X.stats;
    vname.textContent = "明志对照 · 宋×明";
    pmeta.innerHTML = "<span>宋 361 府州 ↔ 明 193 府</span><span>三重证据匹配</span><span>HHH 只读桥接</span>";
    var html = '<div class="p-kicker">互查橋 · 總覽</div>';
    html += '<div class="kv">宋府州 <b>' + st.song_zhou + "</b> → 得對應 <b>" + st.matched +
      "</b>（同名 <b>" + st.same + "</b> · 宋州明升府 <b>" + st.promo + "</b> · 改名同城 <b>" +
      st.rename + "</b> · 明為屬州 <b>" + st.mzhou + "</b>）· 近鄰存疑 <b>" + st.near +
      "</b> · 無對應 <b>" + st.none + "</b>；明府 193 座中被反向對應 <b>" + st.ming_fu_hit + "</b> 座。</div>";
    html += '<div class="quote"><span class="ql">匹配方法（tools/build_xref_fy.py 可重算）</span>' +
      "名合（州名簡體化全同/去綴干支同）+ 治所今名對齊 + 兩站坐標近距 ≤32km 三重證據；" +
      "僅名合者須道-省粗域相容（防同名異地）；純坐標近鄰不入確定計數、單列存疑。凡計數出自腳本。</div>";

    /* 按道分组计数 */
    html += '<div class="p-kicker" style="margin-top:12px">分道計數</div><div class="xrtable-wrap"><table class="xrtable"><thead><tr>' +
      "<th>道</th><th>州</th><th>同名</th><th>升府</th><th>改名</th><th>明属州</th><th>疑</th><th>无</th></tr></thead><tbody>";
    X.by_dao.forEach(function (d) {
      html += "<tr><td>" + d.dao + "</td><td>" + d.total + "</td><td>" + d.same + "</td><td>" +
        d.promo + "</td><td>" + d.rename + "</td><td>" + d.mzhou + "</td><td>" +
        (d.near ? "<b>" + d.near + "</b>" : "0") + "</td><td>" + d.none + "</td></tr>";
    });
    html += "</tbody></table></div>";

    /* 样例 */
    html += '<div class="p-kicker" style="margin-top:14px">樣例 · 寰宇條目 × 方輿對應府</div>';
    var picks = [], seen = {};
    ["same", "promo", "rename", "mzhou", "near", "none"].forEach(function (rel) {
      var got = 0;
      X.rows.forEach(function (r) {
        if (r.rel === rel && got < (rel === "none" ? 2 : 3) && !seen[r.z]) {
          seen[r.z] = 1; got++; picks.push(r);
        }
      });
    });
    html += '<div class="xrsample">' + picks.map(xrRowHtml).join("") + "</div>";

    /* 全表（筛选） */
    html += '<div class="p-kicker" style="margin-top:14px">全表 ' + st.song_zhou + ' 行 · 點宋州名入本站州卡</div>';
    html += '<div class="xrfilters">';
    var cur = "all";
    html += '<button class="xf on" data-f="all">全部 ' + st.song_zhou + "</button>";
    ["same", "promo", "rename", "mzhou", "near", "none"].forEach(function (rel) {
      html += '<button class="xf" data-f="' + rel + '">' + XR_REL[rel] + " " + st[rel] + "</button>";
    });
    html += "</div><div id=\"xrlist\">";
    X.by_dao.forEach(function (d) {
      var sub = X.rows.filter(function (r) { return r.dao === d.dao; });
      html += '<div class="daohead">' + d.dao + '<span class="ct">' + sub.length + " 州</span></div>";
      html += sub.map(xrRowHtml).join("");
    });
    html += "</div>";
    html += '<div class="hint">↗ 深鏈約定<b>父目錄同根服務</b>：在 D:\\W_A_W 起 <code>python -m http.server</code> 後，' +
      "/TPHY/ 與 /HHH/ 同源互達（相對路徑 ../HHH/）。方輿經緯為兄弟站，本站只讀其數據、絕不寫入。";

    pbody.className = "";
    pbody.innerHTML = html;
    pbody.querySelectorAll(".xrrow .xrz").forEach(function (el) {
      el.onclick = function () { HYAPP.openZhou(el.parentNode.dataset.z); };
    });
    pbody.querySelectorAll(".xf").forEach(function (b) {
      b.onclick = function () {
        pbody.querySelectorAll(".xf").forEach(function (x) { x.classList.remove("on"); });
        b.classList.add("on");
        var f = b.dataset.f;
        pbody.querySelectorAll(".xrrow").forEach(function (row) {
          if (!row.parentNode.classList.contains("xrsample")) {
            row.style.display = (f === "all" || row.dataset.rel === f) ? "" : "none";
          }
        });
        pbody.querySelectorAll(".daohead").forEach(function (h) { h.style.display = ""; });
      };
    });
    show("對照");
  }

  function openAbout() {
    vname.textContent = "关于 · 校勘记";
    pmeta.innerHTML = "<span>數據源流</span><span>存佚如實</span>";
    var s = HY.stats;
    var html = '<div class="p-kicker">其書</div>' +
      '<div class="quote"><span class="ql">太平寰宇記</span>宋·樂史撰，二百卷，成於太平興國年間。' +
      "以十三道統府州軍監、以州統縣，沿革、四至、戶口、風俗、土貢、人物、古蹟畢載，" +
      "為宋代總志之祖。本站取其空間骨架——道·州·縣三級點織成圖。</div>" +
      '<div class="p-kicker">數據源（2026-11 偵察實錄）</div>' +
      '<div class="kv">維基文庫 zh.wikisource.org —— 本網絡環境不可達（TCP 直連失敗），未採用、不冒稱。<br>' +
      "國學導航 guoxue123.com —— 可達，史部目錄無此書。<br>" +
      "<b>主源：kanripo/KR2k0004（GitHub）</b>——文淵閣四庫全書本轉錄，UTF-8、結構完整。</div>" +
      '<div class="p-kicker">存佚（如實）</div>' +
      '<div class="kv">二百卷編號俱在；四庫本原闕 <b>8 卷</b>：卷四、卷一一三至一一九。實得 <b>' + s.vols_got +
      "</b> 卷，正文 <b>" + (s.total_chars || "").toLocaleString() + "</b> 字（去空白）。</div>" +
      '<div class="p-kicker">坐標口徑</div>' +
      '<div class="kv">府州定位 <b>' + s.zhou_coord + "</b>/" + s.zhou_count +
      "（確 " + s.coord_sure + " · 推 " + s.coord_derived + "）——agent 依地文學常識整編，一律標 src=derived；<br>" +
      "縣 " + s.xian_count + "：附郭取州治 " + (s.xian_coord - s.xian_tri) + " · 方位里程三角化 " + s.xian_tri +
      "（1里≈0.55km，方法近似）· 其餘如實留白。</div>" +
      '<div class="p-kicker">校勘約定</div>' +
      '<div class="kv">底本「(闕)」為四庫本局部缺文注記，如實保留；異體字（關/闗、劍/劒/劔、潁/頴）歸併；' +
      "粘連縣名不強拆——寧少勿假。</div>" +
      '<div class="p-kicker">導出（與 tools/export_data.py 同口徑）</div>' +
      '<div class="btnrow">' +
      '<button class="abtn" id="exz">⤓ 府州 CSV</button>' +
      '<button class="abtn" id="exx">⤓ 縣 CSV</button>' +
      '<button class="abtn" id="exk">⤓ KML</button>' +
      '<button class="abtn" id="exg">⤓ GeoJSON</button>' +
      '<button class="abtn" id="exr">⤓ 宋明對照 CSV</button></div>' +
      '<div class="hint">府州 361 行（含未定位標註與今地依據）· 縣 626 行（附郭=州治 / 三角化±20% 逐行註明）。' +
      "命令行同款：<code>python tools/export_data.py</code> → docs/export/。</div>" +
      '<div class="p-kicker">研究論文</div>' +
      '<div class="btnrow"><a class="abtn solid" href="docs/寰宇经纬-数字人文.pdf" target="_blank" rel="noopener">📄 寰宇經緯-數字人文.pdf</a>' +
      '<button class="abtn" id="goxref">☰ 明志對照</button></div>' +
      '<div class="hint">論文 PDF 由 tools/build_paper_pdf.py 排印，數字全出自 stats.json；' +
      "宋明互查橋見「對照」頁籤（../HHH/ 深鏈，父目錄同根服務）。</div>";
    pbody.className = "";
    pbody.innerHTML = html;
    document.getElementById("exz").onclick = HYEXPORT.zhouCsv;
    document.getElementById("exx").onclick = HYEXPORT.xianCsv;
    document.getElementById("exk").onclick = HYEXPORT.kml;
    document.getElementById("exg").onclick = HYEXPORT.geojson;
    document.getElementById("exr").onclick = HYEXPORT.xrefCsv;
    var gx = document.getElementById("goxref");
    if (gx) gx.onclick = function () { HYAPP.setMode("duizhao"); };
    show("關於");
  }

  function bindChips() {
    pbody.querySelectorAll(".xchip[data-z]").forEach(function (c) {
      c.onclick = function () { HYAPP.openZhou(c.dataset.z); };
    });
    pbody.querySelectorAll(".xchip[data-x]").forEach(function (c) {
      c.onclick = function () {
        var z = HY.zhou.find(function (q) { return q.n === c.dataset.zn; });
        var x = z && z.xian.find(function (q) { return q.n === c.dataset.x; });
        if (z && x) openXian(z, x);
      };
    });
  }

  return { openDao: openDao, openZhou: openZhou, openXian: openXian, openAbout: openAbout,
           openXref: openXref, show: show, hide: hide, get pbody() { return pbody; } };
})();
window.HYPANEL = HYPANEL;
