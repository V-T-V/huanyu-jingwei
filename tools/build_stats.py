# -*- coding: utf-8 -*-
"""
寰宇经纬 · 文本计量管线
data/intermediate/full.json + data_raw/ → docs/stats.json + docs/ANALYSIS.md 数字节
凡数字必出自脚本（视觉读图不作数据源）。
"""
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = HERE
RAW = os.path.join(ROOT, "data_raw")
INT = os.path.join(ROOT, "data", "intermediate")
DOCS = os.path.join(ROOT, "docs")


def vol_text(n):
    p = os.path.join(RAW, "KR2k0004_%03d.txt" % n)
    if not os.path.exists(p):
        return ""
    t = open(p, encoding="utf-8").read()
    t = "\n".join(ln for ln in t.split("\n") if not ln.startswith("#"))
    return re.sub(r"<pb:[^>]*>", "", t).replace("¶", "")


def main():
    full = json.load(open(os.path.join(INT, "full.json"), encoding="utf-8"))
    hy_text_manifest = json.load(open(os.path.join(ROOT, "data", "text", "manifest.json"), encoding="utf-8"))

    # ── 道卷字数（分片口径）──
    dao_chars = {f["dao"]: f["chars"] for f in hy_text_manifest["files"]}

    # ── 全书词频（风土地理词 + 引书）──
    TERMS = ["風俗", "姓氏", "人物", "土貢", "土産", "古蹟", "山", "水", "城", "祠", "廟", "墓", "驛",
             "湖", "泉", "洞", "石", "橋", "關", "津", "寨", "鎮", "鄉", "里"]
    BOOKS = ["水經注", "漢書", "後漢書", "史記", "元和郡縣志", "十三州志", "郡國志", "輿地志",
             "圖經", "左傳", "博物志", "括地志", "三輔黃圖", "吳越春秋", "華陽國志", "嶺表錄異"]
    term_counts = Counter()
    book_counts = Counter()
    got_vols = [v["vol"] for v in full["vols"] if not v["lost"]]
    for n in got_vols:
        t = vol_text(n)
        for w in TERMS:
            term_counts[w] += t.count(w)
        for b in BOOKS:
            book_counts[b] += t.count("《" + b) + t.count(b) if len(b) <= 3 else t.count(b)

    # ── 州条目字段覆盖 ──
    zs = full["merged"]
    f_cov = {}
    for key in ("sizhi", "fengsu", "hu", "tugong", "tuchan", "xingishi", "renwu", "jing"):
        f_cov[key] = sum(1 for z in zs.values() if z["fields"].get(key))

    # ── 县方位里程样本（三角化审计）──
    dists = []
    for z in zs.values():
        for xp in z["xian_paras"]:
            m = re.match(r"^[\s\u3000]*[\u4e00-\u9fff]{1,4}縣(東南|西南|東北|西北|東|西|南|北)([一二三四五六七八九十百]+)里", xp)
            if m:
                t = m.group(2)
                # 汉字数字粗转
                val = 0
                if "百" in t:
                    h, _, tail = t.partition("百")
                    val = ({"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9}.get(h, 1)) * 100
                    if tail:
                        val += 10 if tail == "十" else 0
                        if tail.startswith("十"):
                            val += {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9}.get(tail[1:], 0)
                elif "十" in t:
                    h, _, tail = t.partition("十")
                    val = ({"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9}.get(h, 1)) * 10
                    val += {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9}.get(tail, 0)
                if 1 <= val <= 800:
                    dists.append(val)

    dists.sort()
    med = dists[len(dists) // 2] if dists else 0

    stats = {
        "vols_got": full["report"]["vols_got"],
        "total_chars": full["report"]["total_chars"],
        "zhou_count": full["report"]["zhou_count"],
        "zhou_coord": full["report"]["zhou_coord"],
        "coord_sure": full["report"]["coord_sure"],
        "coord_derived": full["report"]["coord_derived"],
        "xian_count": full["report"]["xian_count"],
        "xian_coord": full["report"]["xian_coord"],
        "xian_tri": full["report"]["xian_tri"],
        "dao_chars": dao_chars,
        "field_coverage": f_cov,
        "term_counts": dict(term_counts.most_common(20)),
        "book_counts": dict(book_counts.most_common(16)),
        "dist_sample_n": len(dists),
        "dist_median_li": med,
        "dist_p10": dists[len(dists) // 10] if dists else 0,
        "dist_p90": dists[len(dists) * 9 // 10] if dists else 0,
        "dist_raw": dists,          # 558 个原始里程样本（论文直方图用，凡数字出自脚本）
    }
    os.makedirs(DOCS, exist_ok=True)
    with open(os.path.join(DOCS, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    print("docs/stats.json 写出")
    print("  县距样本 %d · 中位 %d 里 · P10 %d · P90 %d" % (len(dists), med, stats["dist_p10"], stats["dist_p90"]))
    print("  引书 top5:", dict(list(book_counts.most_common(5))))
    print("  词频 top8:", dict(list(term_counts.most_common(8))))


if __name__ == "__main__":
    main()
