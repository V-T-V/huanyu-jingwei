# -*- coding: utf-8 -*-
"""
寰宇经纬 × 元和经纬 · 唐宋互查桥（宋视角，P2-D）
读 D:\\W_A_W\\YHJZ\\data\\xref_hy.js + site_data.js（**只读，绝不写入 YHJZ**），
将元和站已判好的「唐州→宋条」反转为「宋州→唐对应」，产 data/xrev_yh.js。

档位（宋视角分档，全部承自元和站已判结论、本脚本仅重组复核）:
  同名  唐宋同名同治（kind=同名 且无异隶）
  异名  同治异名（kind=同治异名，如 雍州→京兆府、鎮州→恒州；升降 sj 并注）
  异隶  名同而唐道/宋志道不同（m.yili，如 渝州、信州）
  无唐对应  元和志（813）无此条——宋新置军监 / 唐末五代改置 / 唐志阙卷，如实计
深链（元和站实测）: ../YHJZ/#dao=<元和道id>&zhou=<唐州名>
  元和站 modes.js 支持 #dao=/#zhou=/#zhen=/#search=；本桥只发 dao+zhou。
口径注: 元和站 meta song_total=360 系其剔除占位条「領覊縻州」；本站全表 361 行
（占位条单列 why、不计「宋代新置」），none_new = none - 占位 与元和侧 song_new 对账。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YHJZ = r"D:\W_A_W\YHJZ"      # 姐妹站，只读
OUT = os.path.join(ROOT, "data", "xrev_yh.js")


def load_js(path, mark):
    t = open(path, encoding="utf-8").read()
    i = t.find(mark)
    if i < 0:
        raise SystemExit("找不到 %s 于 %s" % (mark, path))
    return json.loads(t[i + len(mark):].rstrip().rstrip(";"))


def main():
    hy = load_js(os.path.join(ROOT, "data", "site_data.js"), "const HY = ")
    xr = load_js(os.path.join(YHJZ, "data", "xref_hy.js"), "var YHXREF = ")
    yh = load_js(os.path.join(YHJZ, "data", "site_data.js"), "var YH = ")

    # 元和站道 id / 州名（深链目标存在性校验用；州名=简体，与 xref_hy 行名同源）
    yh_dao = {d["name"]: d for d in yh["daos"]}
    dao_id = {d["name"]: d["id"] for d in hy["daos"]}

    # ── 反转：唐行 m（宋条）→ 宋州 → 唐行 ──
    inv = {}
    for r in xr["rows"]:
        m = r.get("m")
        if not m:
            continue
        key = (m["n"], m["id"])
        assert key not in inv, "宋条被两条唐州争配: %s" % (key,)
        t_dao_id = yh_dao[r["dao"]]["id"]
        assert any(s["n"] == r["n"] for s in yh_dao[r["dao"]]["states"]), \
            "元和站无此州: %s·%s" % (r["dao"], r["n"])
        inv[key] = r

    rows = []
    cnt = {"tong": 0, "yiming": 0, "yili": 0, "wu": 0}
    sj_n = 0
    ph_n = jun_n = 0
    for z in hy["zhou"]:
        key = (z["n"], dao_id[z["dao"]])
        row = dict(z=z["n"], dao=z["dao"], now=z.get("now") or "", rel="wu", why="")
        r = inv.get(key)
        if r:
            m = r["m"]
            assert m["kind"] in ("同名", "同治异名"), "未知 kind: %s" % m["kind"]
            if m.get("yili"):
                rel = "yili"
                note = "唐隶%s，宋志列%s——道隶不同（名同治同）" % (r["dao"], z["dao"])
            elif m["kind"] == "同治异名":
                rel = "yiming"
                note = m.get("note", "治所同今地而名异——唐宋间升降/改置")
            else:
                rel = "tong"
                note = m.get("note", "")
            if m.get("sj"):
                sj_n += 1
            row.update(rel=rel, tn=r["n"], tdao=r["dao"], tzhen=r.get("zhen", ""),
                       tnow=r.get("now") or "", tid=yh_dao[r["dao"]]["id"],
                       sj=m.get("sj", ""), note=(m.get("note") or note))
        elif z["n"] == "領覊縻州":
            ph_n += 1
            row["why"] = "领羁縻州占位条（非单一州，不参与匹配）"
        elif z["n"].endswith(("軍", "監")):
            jun_n += 1
            row["why"] = "宋新置军监——《元和郡县图志》(813) 成书后置"
        else:
            row["why"] = "元和志无对应条目（唐末五代新置/改并，或唐志阙卷所失——如实计）"
        cnt[row["rel"]] += 1
        rows.append(row)

    matched = cnt["tong"] + cnt["yiming"] + cnt["yili"]
    assert len(rows) == hy["stats"]["zhou_count"], "行数 ≠ 州数"
    assert matched == xr["meta"]["matched"] == xr["meta"]["song_matched"], "对账失败: 元和侧 matched"

    by_dao = []
    for d in hy["daos"]:
        sub = [r for r in rows if r["dao"] == d["name"]]
        if not sub:
            continue
        bd = dict(dao=d["name"], total=len(sub))
        for k in ("tong", "yiming", "yili", "wu"):
            bd[k] = sum(1 for r in sub if r["rel"] == k)
        by_dao.append(bd)

    # ── 样例（元和站 8 组，翻转方向：宋条目在上、唐对应在下；补元和道 id 供深链）──
    samples = [dict(sn=s["sn"], sq=s["sq"], tn=s["tn"], tid=None, tq=s["tq"],
                    kind=s["kind"], sj=s.get("sj", ""), yili=bool(s.get("yili")))
               for s in xr["samples"]]
    for s in samples:
        for d in yh["daos"]:
            if any(st["n"] == s["tn"] for st in d["states"]):
                s["tid"] = d["id"]
                break
        assert s["tid"], "样例唐州未落到元和道: %s" % s["tn"]

    xrev = {
        "built": "2026-11-22",
        "source": "元和经纬 D:/W_A_W/YHJZ/data/xref_hy.js（唐·元和郡县图志 813 · 已判对读 · 只读桥接）",
        "method": "宋视角重组：元和站 build_xref_hy.py 已判 227 唐州↔198 宋条，本脚本反转为每宋州→唐对应；"
                  "档位承判（同名/同治异名/异隶），无对应=元和志无此条（新置军监/改并/阙卷，如实计）；"
                  "深链目标逐条对元和站 site_data.js 校验存在",
        "link": "../YHJZ/#dao={tid}&zhou={tn}",
        "stats": dict(song_zhou=len(rows), tang_states=xr["meta"]["tang_states"],
                      matched=matched, **cnt,
                      sj=sj_n, none_new=cnt["wu"] - ph_n, none_jun=jun_n, ph=ph_n),
        "by_dao": by_dao,
        "rows": rows,
        "samples": samples,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("/* 寰宇经纬 × 元和经纬 · 唐宋互查桥（宋视角） · tools/build_xrev_yh.py 生成（YHJZ 只读）· 勿手改 */\n")
        f.write("const HYXREV_YH = ")
        f.write(json.dumps(xrev, ensure_ascii=False, separators=(",", ":")))
        f.write(";\n")
    print("data/xrev_yh.js 写出")
    print("  宋府州 %d → 得唐对应 %d（同名 %d · 同治异名 %d · 异隶 %d）· 无唐对应 %d"
          "（新置军监 %d · 改并/阙卷 %d · 占位条 %d）"
          % (len(rows), matched, cnt["tong"], cnt["yiming"], cnt["yili"], cnt["wu"],
             jun_n, cnt["wu"] - ph_n - jun_n, ph_n))
    print("  唐侧 %d 州被反向对应（元和站判 matched=%d 对账一致）；升降注 %d 组"
          % (matched, xr["meta"]["matched"], sj_n))
    for bd in by_dao:
        print("   %-6s %3d: 同%2d 异名%2d 异隶%2d 无%2d"
              % (bd["dao"], bd["total"], bd["tong"], bd["yiming"], bd["yili"], bd["wu"]))


if __name__ == "__main__":
    main()
