# -*- coding: utf-8 -*-
"""寰宇经纬 · lint（确定性检查，失败即红）
用法: python tools/lint.py
类别:
  1  版本一致性    全站 ?v= 与 sw.js VERSION 一致
  2  资源存在性    index.html/tests 引用的本地资源存在
  3  数据哨兵      192 实卷 · 阙卷=8 · 14 道组 · 州>=350 · 坐标>=250 · 县>=1200 · 全文>=80万字
  4  分片哨兵      data/text 14 片 · manifest 与文件一致 · 分片可 JS 解析(语法哨兵)
  5  禁用模式      map.fire("click") / innerHTML.indexOf / window._闭包量 / git mv -q / || true
  6  Worker 纯净   ftworker.js 不引用 document/window
  7  深链语法      app.js 含 #dao=/#zhou=/#mode= 写回
  8  覆盖如实      coverage.json 阙卷 = [4,113-119] · 缺卷=0
  9  数据-覆盖一致  site_data.js vols_got 与 coverage.json 一致
 10  论文同步      ANALYSIS.md 改动而 PDF 未重排即红（md 新于 PDF → 跑 tools/build_paper_pdf.py）
 11  互查桥哨兵    data/xref_fy.js 存在可解析 · 总数=州数 · 分档计数自洽 · 深链格式
 12  导出哨兵      docs/export 五件存在 · 行数与 stats 一致 · CSV 带 BOM
 13  唐桥哨兵      data/xrev_yh.js 存在可解析 · 总数=州数 · 分档自洽 · 深链 ../YHJZ/ · 与元和侧对账字段
"""
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails, checks = [], 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


def read(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()


def main():
    # ── 1 版本一致性 ──
    sw_path = os.path.join(ROOT, "sw.js")
    ver = "1"
    if os.path.exists(sw_path):
        m = re.search(r'VERSION = "v(\d+)"', read("sw.js"))
        ok(m, "sw.js 缺 VERSION")
        ver = m.group(1) if m else ""
    for f in ["index.html", "sw.js"] + ["js/" + x for x in os.listdir(os.path.join(ROOT, "js")) if x.endswith(".js")] \
            + ["tests/" + x for x in os.listdir(os.path.join(ROOT, "tests")) if x.endswith(".html")]:
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            continue
        t = open(p, encoding="utf-8").read()
        for bad in set(re.findall(r"\?v=(\d+)", t)):
            ok(bad == ver, f"{f} 过期版本 ?v={bad}（当前 v{ver}）")

    # ── 2 资源存在性 ──
    idx = read("index.html")
    for src in re.findall(r'(?:src|href)="([^"#?]+)(?:\?[^"]*)?"', idx):
        if src.startswith(("http", "data:")):
            continue
        ok(os.path.exists(os.path.join(ROOT, src)), f"index.html 引用缺失: {src}")

    # ── 3 数据哨兵 ──
    t = read("data/site_data.js")
    i = t.find("const HY = ")
    ok(i >= 0, "site_data.js 缺 const HY")
    hy = json.loads(t[i + len("const HY = "):].rstrip().rstrip(";"))
    s = hy["stats"]
    ok(s["vols_got"] == 192, f"实卷 {s['vols_got']} ≠ 192")
    ok(hy["lost_vols"] == [4, 113, 114, 115, 116, 117, 118, 119], f"阙卷异常: {hy['lost_vols']}")
    ok(len(hy["daos"]) == 14, f"道组 {len(hy['daos'])} ≠ 14")
    ok(s["zhou_count"] >= 350, f"府州 {s['zhou_count']} < 350")
    ok(s["zhou_coord"] >= 250, f"州坐标 {s['zhou_coord']} < 250")
    ok(s["coord_sure"] >= 190, f"确坐标 {s['coord_sure']} < 190")
    ok(s["xian_count"] >= 1200, f"县 {s['xian_count']} < 1200")
    ok(s["xian_coord"] >= 600, f"县坐标 {s['xian_coord']} < 600")
    ok(s["total_chars"] >= 800000, f"全文字数 {s['total_chars']} < 80 万")
    ok(all(z.get("dao") for z in hy["zhou"]), "存在无道名的州")
    coords = [z for z in hy["zhou"] if z.get("c")]
    ok(all(15 < z["c"][0] < 46 and 88 < z["c"][1] < 132 for z in coords), "坐标越界(域外点)")

    # ── 4 分片哨兵 ──
    tdir = os.path.join(ROOT, "data", "text")
    js_files = sorted(f for f in os.listdir(tdir) if f.endswith(".js"))
    ok(len(js_files) == 14, f"分片数 {len(js_files)} ≠ 14")
    mani = json.load(open(os.path.join(tdir, "manifest.json"), encoding="utf-8"))
    ok(mani["total_chars"] == s["total_chars"], f"manifest 字数 {mani['total_chars']} ≠ {s['total_chars']}")
    ids = {f[:-3] for f in js_files}
    ok(ids == {m["id"] for m in mani["files"]}, "manifest 与分片文件不一致")
    for f in js_files:
        t = open(os.path.join(tdir, f), encoding="utf-8").read()
        ok(t.startswith("/* 《太平寰宇記》全文分片") and "HYTEXT[" in t, f"{f} 头部标记异常")
        ok(t.rstrip().endswith(";"), f"{f} 结尾异常")

    # ── 5 禁用模式 ──
    banned = [
        (r'map\.fire\(\s*["\']click', "map.fire(click) 委托分发不可靠"),
        (r'innerHTML\.indexOf\(', "innerHTML.indexOf 验证（& 序列化）"),
        (r'window\._ftw', "闭包 let 量不在 window"),
        (r'git mv -q', "git mv 无 -q"),
        (r'\|\|\s*true', "|| true 兜底吞错"),
    ]
    for f in ["js/" + x for x in os.listdir(os.path.join(ROOT, "js")) if x.endswith(".js")]:
        t = open(os.path.join(ROOT, f), encoding="utf-8").read()
        for pat, why in banned:
            ok(not re.search(pat, t), f"{f} 触禁：{why}")

    # ── 5b JS 语法（node --check，静默失败即红）──
    import subprocess
    for f in ["js/" + x for x in sorted(os.listdir(os.path.join(ROOT, "js"))) if x.endswith(".js")]:
        r2 = subprocess.run(["node", "--check", os.path.join(ROOT, f)], capture_output=True, timeout=20)
        ok(r2.returncode == 0, f"{f} 语法错误：{r2.stderr.decode('utf-8', 'replace')[:160]}")

    # ── 6 Worker 纯净 ──
    w = read("js/ftworker.js")
    ok("document" not in w, "ftworker.js 引用 document")
    ok("window." not in w.replace("window.HYTEXT_MANIFEST", ""), "ftworker.js 引用 window")

    # ── 7 深链语法 ──
    app = read("js/app.js")
    for frag in ["dao=", "zhou=", "mode=", "search="]:
        ok(frag in app, f"app.js 深链缺 {frag}")

    # ── 8 覆盖如实 ──
    cov = json.load(open(os.path.join(ROOT, "data", "coverage.json"), encoding="utf-8"))
    ok(cov["got_vols"] == 192, f"coverage 实卷 {cov['got_vols']} ≠ 192")
    ok(cov["lost_vol_list"] == [4, 113, 114, 115, 116, 117, 118, 119], "coverage 阙卷异常")
    ok(cov["missing_vols"] == [], f"存在未抓到卷: {cov['missing_vols']}")
    ok("wikisource" in json.dumps(cov, ensure_ascii=False).lower() or cov["source"], "coverage 缺源说明")

    # ── 9 数据-覆盖一致 ──
    ok(cov["got_vols"] == s["vols_got"], "site_data 与 coverage 实卷数不一致")
    ok(abs(cov["total_chars"] - s["total_chars"]) < 5000, "site_data 与 coverage 字数不一致")

    # ── 10 论文同步（md 改了 PDF 忘排即红）──
    pdf_path = os.path.join(ROOT, "docs", "寰宇经纬-数字人文.pdf")
    md_path = os.path.join(ROOT, "docs", "ANALYSIS.md")
    ok(os.path.exists(pdf_path), "docs/寰宇经纬-数字人文.pdf 不存在（跑 tools/build_paper_pdf.py）")
    if os.path.exists(pdf_path):
        ok(os.path.getmtime(md_path) <= os.path.getmtime(pdf_path) + 60,
           "ANALYSIS.md 新于论文 PDF——重跑 python tools/build_paper_pdf.py（改于 %s）"
           % time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(md_path))))

    # ── 11 互查桥哨兵 ──
    xr_path = os.path.join(ROOT, "data", "xref_fy.js")
    ok(os.path.exists(xr_path), "data/xref_fy.js 不存在（跑 tools/build_xref_fy.py）")
    xr = None
    if os.path.exists(xr_path):
        xt = open(xr_path, encoding="utf-8").read()
        k = xt.find("const HYXREF = ")
        ok(k >= 0, "xref_fy.js 缺 const HYXREF")
        try:
            xr = json.loads(xt[k + len("const HYXREF = "):].rstrip().rstrip(";"))
        except Exception as e:
            ok(False, "xref_fy.js 解析失败: %s" % e)
    if xr:
        xs = xr["stats"]
        ok(xs["song_zhou"] == s["zhou_count"], "桥总数 %s ≠ 州数 %s" % (xs["song_zhou"], s["zhou_count"]))
        ok(xs["matched"] == xs["same"] + xs["promo"] + xs["rename"] + xs["mzhou"], "桥分档不自洽")
        ok(xs["matched"] + xs["near"] + xs["none"] == xs["song_zhou"], "桥总账不自洽")
        ok(len(xr["rows"]) == xs["song_zhou"], "桥行数 %d ≠ %d" % (len(xr["rows"]), xs["song_zhou"]))
        rels = {r["rel"] for r in xr["rows"]}
        ok(rels <= {"same", "promo", "rename", "mzhou", "near", "none"}, "桥出现未定义 rel: %s" % rels)
        ok(all(r["z"] and r["dao"] for r in xr["rows"]), "桥行缺州名/道名")
        ok(all(r["mp"] and r["mf"] for r in xr["rows"] if r["rel"] not in ("none",)), "匹配行缺深链字段")
        ok("../HHH/" in xr.get("link", ""), "桥深链基址异常")
        idx_html = read("index.html")
        ok("data/xref_fy.js" in idx_html, "index.html 未引入 data/xref_fy.js")

    # ── 13 唐桥哨兵（宋×唐，data/xrev_yh.js）──
    xr2_path = os.path.join(ROOT, "data", "xrev_yh.js")
    ok(os.path.exists(xr2_path), "data/xrev_yh.js 不存在（跑 tools/build_xrev_yh.py）")
    xr2 = None
    if os.path.exists(xr2_path):
        x2t = open(xr2_path, encoding="utf-8").read()
        k2 = x2t.find("const HYXREV_YH = ")
        ok(k2 >= 0, "xrev_yh.js 缺 const HYXREV_YH")
        try:
            xr2 = json.loads(x2t[k2 + len("const HYXREV_YH = "):].rstrip().rstrip(";"))
        except Exception as e:
            ok(False, "xrev_yh.js 解析失败: %s" % e)
    if xr2:
        x2 = xr2["stats"]
        ok(x2["song_zhou"] == s["zhou_count"], "唐桥总数 %s ≠ 州数 %s" % (x2["song_zhou"], s["zhou_count"]))
        ok(x2["matched"] == x2["tong"] + x2["yiming"] + x2["yili"], "唐桥分档不自洽")
        ok(x2["matched"] + x2["wu"] == x2["song_zhou"], "唐桥总账不自洽")
        ok(x2["wu"] == x2["none_new"] + x2["ph"], "唐桥无对应子账不自洽")
        ok(len(xr2["rows"]) == x2["song_zhou"], "唐桥行数 %d ≠ %d" % (len(xr2["rows"]), x2["song_zhou"]))
        rels2 = {r["rel"] for r in xr2["rows"]}
        ok(rels2 <= {"tong", "yiming", "yili", "wu"}, "唐桥出现未定义 rel: %s" % rels2)
        ok(all(r["z"] and r["dao"] for r in xr2["rows"]), "唐桥行缺州名/道名")
        ok(all(r.get("tn") and r.get("tid") for r in xr2["rows"] if r["rel"] != "wu"),
           "唐桥匹配行缺唐州名/元和道 id（深链字段）")
        ok(all(r.get("why") for r in xr2["rows"] if r["rel"] == "wu"), "唐桥无对应行缺 why 说明")
        ok("../YHJZ/" in xr2.get("link", ""), "唐桥深链基址异常")
        ok("data/xrev_yh.js" in idx, "index.html 未引入 data/xrev_yh.js")

    # ── 12 导出哨兵 ──
    ex = os.path.join(ROOT, "docs", "export")
    for f in ("寰宇经纬-府州对照.csv", "寰宇经纬-县对照.csv", "寰宇经纬-州县点位.kml",
              "寰宇经纬-州县点位.geojson", "寰宇经纬-宋明对照.csv"):
        ok(os.path.exists(os.path.join(ex, f)), "docs/export 缺 %s（跑 tools/export_data.py）" % f)
    zc = os.path.join(ex, "寰宇经纬-府州对照.csv")
    xc = os.path.join(ex, "寰宇经纬-县对照.csv")
    rc = os.path.join(ex, "寰宇经纬-宋明对照.csv")
    if os.path.exists(zc):
        raw = open(zc, "rb").read()
        ok(raw[:3] == b"\xef\xbb\xbf", "府州 CSV 缺 BOM")
        ok(raw.decode("utf-8-sig").count("\n") == s["zhou_count"], "府州 CSV 行数 ≠ %s" % s["zhou_count"])
    if os.path.exists(xc):
        raw = open(xc, "rb").read()
        ok(raw[:3] == b"\xef\xbb\xbf", "县 CSV 缺 BOM")
        ok(raw.decode("utf-8-sig").count("\n") == s["xian_coord"], "县 CSV 行数 ≠ %s" % s["xian_coord"])
    if os.path.exists(rc):
        raw = open(rc, "rb").read()
        ok(raw[:3] == b"\xef\xbb\xbf", "宋明对照 CSV 缺 BOM")
        ok(raw.decode("utf-8-sig").count("\n") == s["zhou_count"], "宋明对照 CSV 行数 ≠ 州数")
    gj = os.path.join(ex, "寰宇经纬-州县点位.geojson")
    if os.path.exists(gj):
        g = json.load(open(gj, encoding="utf-8"))
        ok(len(g["features"]) == s["zhou_coord"] + s["xian_coord"],
           "GeoJSON 要素 %d ≠ 州点+县点 %d" % (len(g["features"]), s["zhou_coord"] + s["xian_coord"]))

    print(f"lint：{checks} 项检查")
    if fails:
        print(f"✗ {len(fails)} 项失败：")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("✓ 全绿")


if __name__ == "__main__":
    main()
