# -*- coding: utf-8 -*-
"""
寰宇经纬 · 抓取管线（断点续抓）
数据源: kanripo/KR2k0004 (GitHub) —— 太平寰宇記 200 卷, 文淵閣四庫全書本轉錄
       (維基文庫 zh.wikisource.org 於本網絡環境不可達, 見 tools/coverage.py 偵察結論;
        國學導航無此書)

特性:
  - 斷點續抓: data_raw/ 已存在且非空的卷直接跳過 (可中斷重入)
  - 限速: 每頁 >= 0.6s
  - UA 自報家門
  - 失敗重試 3 次, 429/5xx 退避

用法: python tools/fetch_text.py [--dry] [--only 001,002]
"""
import os
import sys
import time
import urllib.request
import urllib.error

# 本机注册表存有失效代理 (127.0.0.1:58319) 会被 urllib 误用 —— 显式禁用系统代理。
# 如需走代理: 设 TPHY_PROXY=http://host:port
_opener = urllib.request.build_opener(
    urllib.request.ProxyHandler(
        {"http": os.environ.get("TPHY_PROXY", ""),
         "https": os.environ.get("TPHY_PROXY", "")} if os.environ.get("TPHY_PROXY") else {})
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "data_raw")

BASE = "https://raw.githubusercontent.com/kanripo/KR2k0004/master/KR2k0004_%03d.txt"
UA = ("HuanyuJingwei-DH/0.1 (static digital-humanities site build; book: Taiping Huanyuji; "
      "rate-limited; contact: local build agent)")
VOLUMES = list(range(1, 201))  # 000 为四库提要, 不入正文; 1..200 为卷


def fetch_one(n: int, dry: bool = False) -> str:
    dest = os.path.join(RAW, "KR2k0004_%03d.txt" % n)
    if os.path.exists(dest) and os.path.getsize(dest) > 200:
        return "skip"
    if dry:
        return "would-fetch"
    url = BASE % n
    last_err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with _opener.open(req, timeout=60) as r:
                data = r.read()
            if len(data) < 100:
                raise IOError("suspiciously small (%d bytes)" % len(data))
            with open(dest, "wb") as f:
                f.write(data)
            return "fetched %d bytes" % len(data)
        except urllib.error.HTTPError as e:
            last_err = "HTTP %d" % e.code
            if e.code == 404:
                return "missing-404"
            time.sleep(5 * (attempt + 1))
        except Exception as e:  # 网络/超时
            last_err = str(e)
            time.sleep(5 * (attempt + 1))
    return "ERROR " + str(last_err)


def main():
    dry = "--dry" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",") if x.strip()}
    os.makedirs(RAW, exist_ok=True)
    ok = miss = err = skip = 0
    t0 = time.time()
    for n in VOLUMES:
        if only and n not in only:
            continue
        res = fetch_one(n, dry)
        tag = res.split()[0]
        if tag == "skip":
            skip += 1
        elif tag in ("fetched", "would-fetch"):
            ok += 1
        elif tag == "missing-404":
            miss += 1
        else:
            err += 1
            print("  ✗ 卷%03d: %s" % (n, res))
        if tag == "fetched":
            time.sleep(0.6)  # 限速
    print("抓取完成: 新抓 %d · 跳过(已有) %d · 404 %d · 失败 %d · 用时 %.0fs"
          % (ok, skip, miss, err, time.time() - t0))
    sys.exit(1 if err else 0)


if __name__ == "__main__":
    main()
