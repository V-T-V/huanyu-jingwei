# -*- coding: utf-8 -*-
"""寰宇经纬 · 回归入口
python run_tests.py
  1) tools/lint.py           确定性静态检查
  2) 数据断言(Python 版, 与 tests/test_data.html 同口径)
  3) 无头浏览器断言页(Edge headless, TESTLOG 协议)
本地服务: python -m http.server 9700（FY_BASE 同款, 环境变量 HY_BASE 可覆盖）
"""
import os
import re
import subprocess
import sys
import tempfile
import json

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get("HY_BASE", "http://127.0.0.1:9700/")
fails = []


def step(name, fn):
    print(f"—— {name} ——")
    try:
        r = fn()
        print(f"✓ {name} 通过\n")
        return r
    except AssertionError as e:
        fails.append(name)
        print(f"✗ {name} 失败：{e}\n")


def lint():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "lint.py")],
                       capture_output=True, text=True, encoding="utf-8")
    print(r.stdout.strip())
    assert r.returncode == 0, "lint 未全绿"


def data_asserts():
    t = open(os.path.join(ROOT, "data", "site_data.js"), encoding="utf-8").read()
    i = t.find("const HY = ")
    assert i >= 0, "site_data.js 结构异常"
    hy = json.loads(t[i + len("const HY = "):].rstrip().rstrip(";"))
    s = hy["stats"]
    assert s["vols_got"] == 192, f"实卷 {s['vols_got']}"
    assert hy["lost_vols"] == [4, 113, 114, 115, 116, 117, 118, 119]
    assert len(hy["daos"]) == 14
    assert s["zhou_count"] >= 350 and s["zhou_coord"] >= 250
    assert s["xian_count"] >= 1200 and s["xian_coord"] >= 600
    assert s["total_chars"] >= 800000
    kf = next(z for z in hy["zhou"] if z["n"] == "開封府")
    assert abs(kf["c"][0] - 34.80) < 0.5, "開封府坐标漂移"
    print(f"实卷 {s['vols_got']}/200 · 州 {s['zhou_count']}(定位 {s['zhou_coord']}: 确 {s['coord_sure']}/推 {s['coord_derived']})"
          f" · 县 {s['xian_count']}(上图 {s['xian_coord']}) · 全文 {s['total_chars']:,} 字")


CANDS = [
    os.environ.get("HY_BROWSER", ""),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]
EDGE = next((c for c in CANDS if c and os.path.exists(c)), None)


def browser_pages():
    assert EDGE, "未找到浏览器（HY_BROWSER 可指定）"
    assert BASE.startswith("http"), "HY_BASE 异常"
    pages = ["tests/test_data.html", "tests/test_map.html"]       # virtual-time dump-dom
    for page in pages:
        prof = tempfile.mkdtemp(prefix="hyprof_")
        r = subprocess.run(
            [EDGE, "--headless=new", "--disable-gpu", "--no-first-run",
             "--user-data-dir=" + prof, "--virtual-time-budget=14000", "--dump-dom",
             BASE + page],
            capture_output=True, timeout=240)
        html = r.stdout.decode("utf-8", errors="replace")
        m = re.search(r'id="testlog"[^>]*>([^<]*)<', html)
        if not m or "TESTLOG" not in (m.group(1) or ""):
            fails.append(page)
            print(f"✗ {page} 无日志产出")
            continue
        lines = [l.strip() for l in m.group(1).splitlines()
                 if l.strip() and l.strip() not in ("TESTLOG", "ENDLOG")]
        bad = [l for l in lines if l.startswith("FAIL")]
        if not lines:
            bad = ["(0 项断言 = 未产出)"]
        status = "✓" if not bad else "✗"
        if bad:
            fails.append(page)
        print(f"{status} {page} {len(lines)} 项断言" + ("：" if bad else ""))
        for l in bad:
            print("    " + l)
    for page in ["tests/test_reader.html", "tests/test_search.html"]:   # CDP 真实时间
        cdp_page(page)


def cdp_page(page, timeout=45):
    """CDP 真实时间跑异步断言页（promise/Worker 与 virtual-time 不合）：
    页面自写 document.title = PASS/FAIL + TESTLOG；轮询 /json 目标。"""
    import urllib.request as ur
    import time as _t
    port = 9781
    prof = tempfile.mkdtemp(prefix="hycdp_")
    proc = subprocess.Popen([EDGE, "--headless=new", "--disable-gpu", "--no-first-run",
                             f"--remote-debugging-port={port}", "--user-data-dir=" + prof, "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        base = f"http://127.0.0.1:{port}"
        for _ in range(60):
            try:
                ur.urlopen(base + "/json/version", timeout=1).read()
                break
            except Exception:
                _t.sleep(.25)
        ur.urlopen(ur.Request(base + "/json/new?" + BASE + page, method="PUT"), timeout=5).read()
        deadline = _t.time() + timeout
        title = ""
        while _t.time() < deadline:
            _t.sleep(.6)
            try:
                tabs = json.loads(ur.urlopen(base + "/json", timeout=2).read())
            except Exception:
                continue
            for tb in tabs:
                if tb.get("url", "").split("#")[0].endswith(page):
                    title = tb.get("title", "")
                    if title.startswith(("PASS", "FAIL")):
                        break
            if title.startswith(("PASS", "FAIL")):
                break
        if title != "PASS":
            fails.append(page)
            print(f"✗ {page} title={title or '(超时)'}")
        else:
            print(f"✓ {page} (CDP) PASS")
    finally:
        proc.kill()


def main():
    print("浏览器:", EDGE or "(仅 python 断言)")
    step("lint", lint)
    step("数据断言", data_asserts)
    if BASE.startswith("http://127.0.0.1") or BASE.startswith("http://localhost"):
        import urllib.request
        try:
            urllib.request.urlopen(BASE + "index.html", timeout=3).read()
        except Exception as e:
            print(f"！本地服务不可达（{e}）——浏览器断言页跳过。起服务: python -m http.server 9700")
            _finish()
            return
    step("浏览器断言页", browser_pages)
    _finish()


def _finish():
    if fails:
        print(f"✗✗ 回归失败：{', '.join(fails)}")
        sys.exit(1)
    print("═══ 全绿 ═══")


if __name__ == "__main__":
    main()
