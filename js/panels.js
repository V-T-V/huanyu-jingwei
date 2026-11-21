/* ═══════════ 寰宇经纬 · 面板（道 / 州 / 县 / 关于） ═══════════ */

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
      "粘連縣名不強拆——寧少勿假。</div>";
    pbody.className = "";
    pbody.innerHTML = html;
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
           show: show, hide: hide, get pbody() { return pbody; } };
})();
window.HYPANEL = HYPANEL;
