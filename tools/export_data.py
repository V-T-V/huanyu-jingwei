# -*- coding: utf-8 -*-
"""
寰宇经纬 · 古今对照导出（P2-B）
产 docs/export/ 五件（与前端「⤓ 导出」按钮同口径）:
  寰宇经纬-府州对照.csv   361 府州军监（含未定位标注；BOM UTF-8）
  寰宇经纬-县对照.csv     上图 626 县（附郭=州治 / 方位里程三角化 ±20%）
  寰宇经纬-州县点位.kml   Google Earth
  寰宇经纬-州县点位.geojson
  寰宇经纬-宋明对照.csv   xref 桥全表（若无 data/xref_fy.js 则跳过并提示）
凡行数打印复核。示意坐标（三角化）在文件内注明。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "export")
BOM = "\ufeff"
NL = "\r\n"


def load():
    t = open(os.path.join(ROOT, "data", "site_data.js"), encoding="utf-8").read()
    i = t.find("const HY = ")
    return json.loads(t[i + len("const HY = "):].rstrip().rstrip(";"))


def typ(n):
    if n.endswith("府"):
        return "府"
    if n.endswith("军"):
        return "军"
    if n.endswith("监"):
        return "监"
    if n.endswith("州"):
        return "州"
    return "州"


def csv_escape(v):
    v = str(v)
    return '"' + v.replace('"', '""') + '"' if any(c in v for c in ",\"\n") else v


def main():
    hy = load()
    os.makedirs(OUT, exist_ok=True)

    # ── 府州 CSV ──
    head = ["道", "州名", "类型", "卷", "今地依据", "纬度", "经度", "置信", "src", "未定位"]
    lines = [",".join(head)]
    for z in hy["zhou"]:
        lines.append(",".join(csv_escape(x) for x in [
            z["dao"], z["n"], typ(z["n"]), "·".join(str(v) for v in z["vols"]),
            z.get("now") or "",
            ("%.2f" % z["c"][0]) if z.get("c") else "",
            ("%.2f" % z["c"][1]) if z.get("c") else "",
            z.get("cf") or "", z.get("src") or "",
            "未定位（坐标表未收，舆图不上点）" if not z.get("c") else ""]))
    with open(os.path.join(OUT, "寰宇经纬-府州对照.csv"), "w", encoding="utf-8-sig", newline="") as f:
        f.write(NL.join(lines))
    n_zhou = len(lines) - 1

    # ── 县 CSV（仅上图 626）──
    head2 = ["道", "州名", "县名", "纬度", "经度", "定位方法", "原载方位里程", "备注"]
    lines2 = [",".join(head2)]
    for z in hy["zhou"]:
        for x in z.get("xian", []):
            if not x.get("c"):
                continue
            if x.get("src") == "fu":
                how, note = "附郭", "附郭县取州治坐标"
            else:
                how, note = "三角化", "以州治为极点按原载方位里程推算（1里≈0.55km），方法近似精度±20%"
            lines2.append(",".join(csv_escape(x) for x in [
                z["dao"], z["n"], x["n"], "%.2f" % x["c"][0], "%.2f" % x["c"][1],
                how, x.get("d") or "", note]))
    with open(os.path.join(OUT, "寰宇经纬-县对照.csv"), "w", encoding="utf-8-sig", newline="") as f:
        f.write(NL.join(lines2))
    n_xian = len(lines2) - 1

    # ── KML ──
    pins = []
    for z in hy["zhou"]:
        if z.get("c"):
            pins.append('<Placemark><name>%s</name><description>%s · 今%s%s</description>'
                        '<Point><coordinates>%.4f,%.4f,0</coordinates></Point></Placemark>'
                        % (z["n"], z["dao"], z.get("now") or "",
                           "（%s）" % z["cf"] if z.get("cf") else "", z["c"][1], z["c"][0]))
        for x in z.get("xian", []):
            if x.get("c"):
                how = "附郭" if x.get("src") == "fu" else "三角化±20%"
                pins.append('<Placemark><name>%s縣</name><description>%s · 隶%s%s</description>'
                            '<Point><coordinates>%.4f,%.4f,0</coordinates></Point></Placemark>'
                            % (x["n"], how, z["n"], ("（" + x["d"] + "）") if x.get("d") else "",
                               x["c"][1], x["c"][0]))
    kml = ('<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
           '<name>寰宇经纬·州县点位</name>'
           '<description>宋·太平寰宇记 255 州治 + 626 上图县；三角化县点为示意坐标（±20%）</description>'
           + "".join(pins) + "</Document></kml>")
    with open(os.path.join(OUT, "寰宇经纬-州县点位.kml"), "w", encoding="utf-8") as f:
        f.write(kml)

    # ── GeoJSON ──
    feats = []
    for z in hy["zhou"]:
        if z.get("c"):
            feats.append({"type": "Feature",
                          "geometry": {"type": "Point", "coordinates": [z["c"][1], z["c"][0]]},
                          "properties": {"名": z["n"], "类": typ(z["n"]), "道": z["dao"],
                                         "今地": z.get("now") or "", "置信": z.get("cf") or "",
                                         "src": z.get("src") or "", "依据": "州治今地整编"}})
        for x in z.get("xian", []):
            if x.get("c"):
                feats.append({"type": "Feature",
                              "geometry": {"type": "Point", "coordinates": [x["c"][1], x["c"][0]]},
                              "properties": {"名": x["n"], "类": "县", "道": z["dao"], "隶": z["n"],
                                             "定位": "附郭=州治" if x.get("src") == "fu" else "三角化示意坐标(±20%)",
                                             "原载": x.get("d") or ""}})
    gj = json.dumps({"type": "FeatureCollection",
                     "name": "寰宇经纬-州县点位",
                     "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
                     "features": feats}, ensure_ascii=False)
    with open(os.path.join(OUT, "寰宇经纬-州县点位.geojson"), "w", encoding="utf-8") as f:
        f.write(gj)

    # ── 宋明对照 CSV（桥）──
    n_xref = 0
    xp = os.path.join(ROOT, "data", "xref_fy.js")
    if os.path.exists(xp):
        t = open(xp, encoding="utf-8").read()
        xr = json.loads(t[t.find("const HYXREF = ") + len("const HYXREF = "):].rstrip().rstrip(";"))
        REL = {"same": "同名", "promo": "升府", "rename": "改名", "mzhou": "明属州",
               "near": "近邻存疑", "none": "无对应"}
        lines3 = [",".join(["宋州", "道", "宋治今地", "关系", "明省", "明府", "对应单位", "明治今地", "证据", "备注"])]
        for r in xr["rows"]:
            lines3.append(",".join(csv_escape(x) for x in [
                r["z"], r["dao"], r["now"], REL[r["rel"]], r["mpn"], r["mf"], r["mn"], r["mnow"],
                r["ev"] + (("·" + str(r["d"]) + "km") if r.get("d") is not None else ""), r["note"]]))
        with open(os.path.join(OUT, "寰宇经纬-宋明对照.csv"), "w", encoding="utf-8-sig", newline="") as f:
            f.write(NL.join(lines3))
        n_xref = len(lines3) - 1
    else:
        print("！data/xref_fy.js 不存在，宋明对照 CSV 跳过（先跑 tools/build_xref_fy.py）")

    print("docs/export/ 写出：府州 CSV %d 行 · 县 CSV %d 行 · KML %d 点 · GeoJSON %d 要素 · 宋明对照 %d 行"
          % (n_zhou, n_xian, len(pins), len(feats), n_xref))
    s = hy["stats"]
    assert n_zhou == s["zhou_count"], "府州行数 %d ≠ stats %d" % (n_zhou, s["zhou_count"])
    assert n_xian == s["xian_coord"], "县行数 %d ≠ stats.xian_coord %d" % (n_xian, s["xian_coord"])


if __name__ == "__main__":
    main()
