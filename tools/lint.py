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
"""
import json
import os
import re
import sys

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

    print(f"lint：{checks} 项检查")
    if fails:
        print(f"✗ {len(fails)} 项失败：")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("✓ 全绿")


if __name__ == "__main__":
    main()
