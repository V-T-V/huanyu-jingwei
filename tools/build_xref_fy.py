# -*- coding: utf-8 -*-
"""
寰宇经纬 × 方舆经纬 · 宋明府州互查桥（P2-C）
读 D:\\W_A_W\\HHH\\data\\site_data.js（**只读，绝不写入 HHH**），
将《太平寰宇记》361 宋府州军监匹配到《读史方舆纪要》明府/属州，产 data/xref_fy.js。

三重证据（凡匹配可复核）:
  名合    宋州名(简体化) == 明单位名 / 去缀干支相同
  今名合  宋州治今地(去省前缀/括注) 与 明单位今地 相等或互含
  坐标近距  两站治所坐标 haversine ≤ 32 km
匹配档位（如实分栏）:
  同名   名同 + 今名/坐标佐证（宋府=明府、宋州=明州）
  升府   干支同 + 宋州→明府（青州→青州府）
  改名   治所同城而名改（洪州→南昌府、宋州→归德府）
  明属州 对应单位为明属州（許州→开封府许州）
  近邻存疑 仅坐标近距、无名/今名佐证——不冒认，单列存疑
  无对应  明废置/降为县/羁縻/两站皆未定位
仅名合（宋州未定位）须过 道→明省粗域 门（防剑南高州误配广东高州府之类同名异地）。
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HHH = r"D:\W_A_W\HHH"          # 兄弟站，只读
OUT = os.path.join(ROOT, "data", "xref_fy.js")

# ── 繁→简（仅覆盖本书州名用字；异体并归）──
T2S = {}
for pair in ("開开 陽阳 陝陕 陜陕 潁颍 頴颍 濟济 濰潍 濱滨 瀘泸 營营 環环 瓊琼 疊叠"
             "祿禄 竇窦 簡简 籠笼 絳绛 綏绥 維维 綿绵 義义 肃肅 興兴 華华 萊莱 萬万 薊蓟"
             "蘄蕲 蘇苏 蘭兰 處处 衛卫 覊羁 許许 豐丰 貝贝 貴贵 費费 賀贺 資资 賓宾 趙赵"
             "軍军 逺远 達达 遼辽 鄆郓 鄧邓 鄭郑 銀银 鎮镇 長长 閬阆 陳陈 陸陆 階阶 隨随"
             "隴陇 雲云 靈灵 靜静 順顺 領领 饒饶 鬱郁 鮮鲜 鳳凤 鳯凤 鹵卤 鹽盐 齊齐 龍龙"
             "龔龚 廬庐 廣广 澤泽 慶庆 寧宁 寕宁 夀寿 峩峨 峯峰 嵐岚 懐怀 懷怀 揚扬 撫抚"
             "晉晋 涼凉 涇泾 溫温 滄沧 漢汉 漣涟 潯浔 劍剑 監监 於于 為为 種种 鉅钜 譚谭"
             "縣县 記记 經经 緯纬 圖图 傳传").split():
    T2S[pair[0]] = pair[1]
T2S.update({"𡊮": "袁", "𤓰": "瓜", "𤣥": "玄", "髙": "高", "㑹": "会", "䖍": "虔", "䝉": "蒙", "宻": "密"})

PROVS = ["黑龙江", "内蒙古", "吉林", "辽宁", "河北", "山西", "山东", "江苏", "浙江", "安徽",
         "福建", "江西", "河南", "湖北", "湖南", "广东", "广西", "海南", "贵州", "云南",
         "四川", "陕西", "甘肃", "宁夏", "青海", "新疆", "北京", "天津", "上海", "重庆"]

# 道 → 明省粗域（仅作「仅名合」级 sanity 门；治所/坐标证据不经此表）
DAO_PROV = {
    "河南道": "河南 山东 江苏 安徽 北直隶",
    "關西道": "陕西 甘肃 宁夏",
    "河東道": "山西",
    "河北道": "北直隶 河南 山东 山西",
    "劍南西道": "四川 重庆 云南 贵州",
    "劍南東道": "四川 重庆 云南 贵州",
    "江南東道": "江苏 安徽 浙江 上海 江西 福建",
    "江南西道": "江西 湖南 湖北 安徽 福建",
    "淮南道": "安徽 江苏 河南 湖北",
    "山南西道": "陕西 四川 重庆 湖北",
    "山南東道": "湖北 河南 重庆 陕西",
    "隴右道": "甘肃 青海 新疆 陕西",
    "嶺南道": "广东 广西 海南 云南",
}


def simp(s):
    return "".join(T2S.get(c, c) for c in s)


def strip_prov(now):
    """去省前缀；余文以括注开头或为空则不剥（防「重庆(巴县)」误剥）。"""
    for p in sorted(PROVS, key=len, reverse=True):
        if now.startswith(p):
            rest = now[len(p):]
            if rest and rest[0] not in "(（":
                return rest
            return now
    return now


def clean(now):
    out, depth = [], 0
    for c in now:
        if c in "(（":
            depth += 1
        elif c in ")）":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(c)
    return "".join(out)


def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def load_hyh():
    t = open(os.path.join(ROOT, "data", "site_data.js"), encoding="utf-8").read()
    i = t.find("const HY = ")
    return json.loads(t[i + len("const HY = "):].rstrip().rstrip(";"))


def load_fy():
    t = open(os.path.join(HHH, "data", "site_data.js"), encoding="utf-8").read()
    i = t.find("const FY = ")
    return json.loads(t[i + len("const FY = "):].rstrip().rstrip(";"))


def main():
    hy = load_hyh()
    fy = load_fy()
    units = []
    n_fu = 0
    for p in fy["provinces"]:
        for u in p["fu"]:
            n_fu += 1
            units.append(dict(pid=p["id"], pn=p["name"], nm=u["n"], now=u.get("now", ""),
                              c=u.get("c"), parent=None, isfu=True, stem=simp(u["n"]).rstrip("府州卫")))
            for z in u.get("zx", []):
                units.append(dict(pid=p["id"], pn=p["name"], nm=z["n"], now=z.get("now", ""),
                                  c=z.get("c"), parent=u["n"], isfu=False, stem=simp(z["n"]).rstrip("州")))

    rows = []
    cnt = {"same": 0, "promo": 0, "rename": 0, "mzhou": 0, "near": 0, "none": 0}
    for z in hy["zhou"]:
        sn = simp(z["n"])
        stem = sn.rstrip("军监") if sn.endswith(("军", "监")) else (sn[:-1] if sn.endswith(("府", "州")) else sn)
        loc = clean(strip_prov(z.get("now") or ""))
        located = bool(z.get("c") or loc)
        cands = []
        for u in units:
            nm_s = simp(u["nm"])
            sc, name_ev, nowsc, d = 0, False, 0, None
            if sn == nm_s:
                sc += 10; name_ev = True
            elif stem and stem == u["stem"]:
                sc += 7; name_ev = True
            if loc and u["now"]:
                if loc == u["now"]:
                    nowsc = 9
                elif len(u["now"]) >= 2 and (u["now"] in loc or (len(loc) >= 2 and loc in u["now"])):
                    nowsc = 6
            if nowsc:
                sc += nowsc
            if z.get("c") and u.get("c"):
                d = hav(z["c"], u["c"])
                if d <= 32:
                    sc += max(3.0, 8 - d / 12)
            prov_ok = u["pn"] in (DAO_PROV.get(z["dao"], "") or "")
            qualifies = (nowsc > 0 or (d is not None and d <= 32)
                         or (name_ev and sc >= 7 and not located and prov_ok))
            if qualifies and sc >= 5:
                cands.append((sc, d if d is not None else 9999, u, name_ev, nowsc))
        cands.sort(key=lambda x: (-x[0], x[1]))
        row = dict(z=z["n"], dao=z["dao"], now=z.get("now") or "", rel="none", note="",
                   mp="", mpn="", mf="", mn="", mnow="", ev="", d=None)
        if cands:
            sc, d, u, name_ev, nowsc = cands[0]
            geo_only = (not name_ev) and nowsc == 0
            nm_s = simp(u["nm"])
            if geo_only:
                rel = "near"
                row["note"] = "仅治所坐标近距，无名/今名佐证——存疑"
            else:
                if sn == nm_s:
                    rel = "same" if (sn.endswith("府") or not u["isfu"] or not nm_s.endswith("府")) else "promo"
                elif stem and stem == u["stem"]:
                    rel = "promo" if (u["isfu"] and nm_s.endswith("府") and sn.endswith(("州", "军", "监"))) else "same"
                else:
                    rel = "rename"
                if not u["isfu"]:
                    rel = "mzhou"
                if not (nowsc > 0 or (d is not None and d <= 32)):
                    row["note"] = "仅名合（宋州未定位，道域相容）"
            evs = []
            if name_ev:
                evs.append("名同" if sn == nm_s else "干支同")
            if nowsc:
                evs.append("今名合")
            if d is not None and d <= 60:
                evs.append("距%.0fkm" % d)
            row.update(rel=rel, mp=u["pid"], mpn=u["pn"],
                       mf=(u["parent"] or u["nm"]), mn=u["nm"], mnow=u["now"],
                       ev="·".join(evs), d=(round(d, 1) if d is not None and d < 900 else None))
        else:
            hit = None
            for u in units:
                nm_s = simp(u["nm"])
                if (sn == nm_s or (stem and stem == u["stem"])) and u["pn"] in (DAO_PROV.get(z["dao"], "") or ""):
                    hit = u
                    break
            if hit:
                nm_s = simp(hit["nm"])
                rel = "promo" if (hit["isfu"] and nm_s.endswith("府") and sn.endswith(("州", "军", "监"))) else "same"
                if not hit["isfu"]:
                    rel = "mzhou"
                row.update(rel=rel, mp=hit["pid"], mpn=hit["pn"],
                           mf=(hit["parent"] or hit["nm"]), mn=hit["nm"], mnow=hit["now"],
                           ev="名同" if sn == nm_s else "干支同", note="仅名合（宋州未定位，道域相容）")
            else:
                row["note"] = "明废置/降县" if located else "未定位待考"
        cnt[row["rel"]] += 1
        rows.append(row)

    by_dao = []
    for d in hy["daos"]:
        nm = d["name"]
        sub = [r for r in rows if r["dao"] == nm]
        if not sub:
            continue
        bd = dict(dao=nm, total=len(sub))
        for k in ("same", "promo", "rename", "mzhou", "near", "none"):
            bd[k] = sum(1 for r in sub if r["rel"] == k)
        by_dao.append(bd)

    matched = cnt["same"] + cnt["promo"] + cnt["rename"] + cnt["mzhou"]
    fu_hit = len({r["mf"] for r in rows if r["mf"]})
    xref = {
        "built": "2026-11-22",
        "source": "方舆经纬 D:/W_A_W/HHH/data/site_data.js（明·读史方舆纪要 · 只读桥接）",
        "method": "名合 + 治所今名对齐 + 坐标近距≤32km 三重证据；仅名合须道-省粗域相容；"
                  "纯坐标近距单列「近邻存疑」，无明府/属州对应如实计「无对应」",
        "link": "../HHH/#mode=舆图&p={p}&fu={fu}",
        "stats": dict(song_zhou=len(rows), matched=matched, **cnt,
                      ming_fu=n_fu, ming_fu_hit=fu_hit),
        "by_dao": by_dao,
        "rows": rows,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("/* 寰宇经纬 × 方舆经纬 · 宋明府州互查桥 · tools/build_xref_fy.py 生成（HHH 只读）· 勿手改 */\n")
        f.write("const HYXREF = ")
        f.write(json.dumps(xref, ensure_ascii=False, separators=(",", ":")))
        f.write(";\n")
    print("data/xref_fy.js 写出")
    print("  宋府州 %d → 匹配 %d（同名 %d · 升府 %d · 改名 %d · 明属州 %d）· 近邻存疑 %d · 无对应 %d"
          % (len(rows), matched, cnt["same"], cnt["promo"], cnt["rename"], cnt["mzhou"], cnt["near"], cnt["none"]))
    print("  明府 %d 座中被对应 %d 座（明属州另计）" % (n_fu, fu_hit))
    for bd in by_dao:
        print("   %-6s %3d: 同%2d 升%2d 改%2d 属%2d 疑%2d 无%2d"
              % (bd["dao"], bd["total"], bd["same"], bd["promo"], bd["rename"], bd["mzhou"], bd["near"], bd["none"]))


if __name__ == "__main__":
    main()
