# -*- coding: utf-8 -*-
"""
寰宇经纬 · 可得性侦察与覆盖统计
用法: python tools/coverage.py            # 扫描 data_raw/, 产出 data/coverage.json + 控制台报告

侦察结论（2026-11-21, 本会话实测）:
  1. 维基文库 zh.wikisource.org —— 本网络环境不可达（TCP 直连失败, 443 超时/拒绝）。
     其收录《太平寰宇記》卷数无法核实, 本站不采用、不冒称。
  2. 国学导航 guoxue123.com —— 可达, 但史部目录无《太平寰宇记》。
  3. kanripo/KR2k0004 (GitHub raw) —— 可达、稳定、UTF-8。
     文淵閣四庫全書本《太平寰宇記》轉錄, 200 卷全帙编号,
     其中原书即阙之卷以「(原阙)」标注 —— 覆盖以扫描实测为准。
主源定为 kanripo (ctext.org 四库本转录), 依据存续于本文件与 README。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
RAW = os.path.join(ROOT, "data_raw")
OUT = os.path.join(ROOT, "data", "coverage.json")

DAO_RE = re.compile(r"^[　\s]*((?:[\u4e00-\u9fff]{1,4}道|四夷))[一二三四五六七八九十百]*[　\s]*$")


def analyze_volume(n: int) -> dict:
    """单卷分析: 是否实存 / 是否原阙 / 道名 / 字数 (与 build_data.load_paras 同口径)"""
    from build_data import load_paras, norm_dao
    p = os.path.join(RAW, "KR2k0004_%03d.txt" % n)
    d = {"vol": n, "got": os.path.exists(p), "lost": False, "dao": None, "chars": 0}
    if not d["got"]:
        return d
    paras = load_paras(n)
    body = "".join(paras) if paras else open(p, encoding="utf-8").read()
    core = re.sub(r"\(闕\)|\(原闕\)|\(阙\)|\(原阙\)|\s", "", body)
    core = re.sub(r"^#.*$", "", core, flags=re.M)
    d["chars"] = len(re.sub(r"\s", "", body))
    if paras is None:
        d["lost"] = True
        return d
    for pp in paras[:8]:
        m = DAO_RE.match(pp)
        if m:
            d["dao"] = norm_dao(m.group(1))
            break
    return d


def main():
    rows = [analyze_volume(n) for n in range(1, 201)]
    got = [r for r in rows if r["got"] and not r["lost"]]
    lost = [r for r in rows if r["lost"]]
    missing = [r for r in rows if not r["got"]]
    daos = {}
    for r in got:
        daos.setdefault(r["dao"] or "未知", []).append(r["vol"])

    report = {
        "source": "kanripo/KR2k0004 (GitHub raw) — 文淵閣四庫全書本《太平寰宇記》轉錄",
        "scouted": "2026-11-21",
        "scout_notes": [
            "维基文库 zh.wikisource.org 于本网络环境不可达（TCP 直连失败）",
            "国学导航 guoxue123.com 可达但无此书",
            "主源 kanripo/ctext 四库本转录, 200 卷编号, 原阙卷以「(原阙)」标注",
        ],
        "total_vols": 200,
        "got_vols": len(got),
        "lost_vols": len(lost),
        "lost_vol_list": [r["vol"] for r in lost],
        "missing_vols": [r["vol"] for r in missing],
        "total_chars": sum(r["chars"] for r in got),
        "by_dao": {k: {"vols": v, "count": len(v)} for k, v in sorted(daos.items(), key=lambda x: min(x[1]))},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    print("覆盖报告 → data/coverage.json")
    print("  实得卷: %d / 200" % len(got))
    print("  原阙卷(四库本即缺): %d → %s" % (len(lost), report["lost_vol_list"]))
    if missing:
        print("  未抓到(网络): %d → %s" % (len(missing), report["missing_vols"]))
    print("  正文总字数(去空白): %s" % format(report["total_chars"], ","))
    print("  分道分布:")
    for k, v in report["by_dao"].items():
        print("    %-8s %2d 卷  %s" % (k, v["count"], v["vols"][:12]))
    return 0 if not missing else 2


if __name__ == "__main__":
    sys.exit(main())
