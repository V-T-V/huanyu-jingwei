# -*- coding: utf-8 -*-
"""
寰宇经纬 · 全文分片管线(可重入)
data_raw/KR2k0004_NNN.txt → data/text/{dao_id}.js (懒加载分片)
分片按道组织, 每片内按卷; 段落保留缩进版式(前端以「　　」顶格识别条目头)。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data_raw")
INTDIR = os.path.join(HERE, "data", "intermediate")
TEXTDIR = os.path.join(HERE, "data", "text")


def vol_paras(n: int):
    """复用 build_data.load_paras 的段落化"""
    sys.path.insert(0, HERE)
    from build_data import load_paras
    return load_paras(n)


def main():
    full = json.load(open(os.path.join(INTDIR, "full.json"), encoding="utf-8"))
    # 道 → 卷映射(实卷)
    dao_of_vol = {}
    for v in full["vols"]:
        if not v["lost"]:
            dao_of_vol[v["vol"]] = v["dao"]
    # 道 id 与 site_data.js 一致: 顺序生成
    DAO_PINYIN = {"河南道": "henan", "關西道": "guanxi", "河東道": "hedong", "河北道": "hebei",
                  "劍南西道": "jiannanxi", "劍南東道": "jiannandong", "江南東道": "jiangnandong",
                  "江南西道": "jiangnanxi", "淮南道": "huainan", "山南西道": "shannanxi",
                  "山南東道": "shannandong", "隴右道": "longyou", "嶺南道": "lingnan", "四夷": "siyi"}
    daos_sorted = sorted(full["report"]["daos"].items(), key=lambda x: min(x[1]))
    dao_ids = {name: DAO_PINYIN.get(name, "dao%d" % (i + 1)) for i, (name, _) in enumerate(daos_sorted)}

    os.makedirs(TEXTDIR, exist_ok=True)
    # 清掉旧分片(防止道重编号后残留)
    for f in os.listdir(TEXTDIR):
        if f.endswith(".js"):
            os.remove(os.path.join(TEXTDIR, f))

    by_dao = {}
    total_chars = 0
    for vol in range(1, 201):
        dao = dao_of_vol.get(vol)
        if not dao:
            continue
        paras = vol_paras(vol)
        if paras is None:
            continue
        chars = len(re.sub(r"\s", "", "".join(paras)))
        total_chars += chars
        by_dao.setdefault(dao, []).append({"v": vol, "ch": chars, "p": paras})

    manifest = []
    for dao, vols in by_dao.items():
        did = dao_ids[dao]
        js = ("/* 《太平寰宇記》全文分片 · build_text.py 生成 · 懶加載 */\n"
              "window.HYTEXT=window.HYTEXT||{};"
              "HYTEXT[%s]=%s;\n" % (json.dumps(did), json.dumps(vols, ensure_ascii=False, separators=(",", ":"))))
        with open(os.path.join(TEXTDIR, did + ".js"), "w", encoding="utf-8") as f:
            f.write(js)
        manifest.append({"dao": dao, "id": did, "vols": [v["v"] for v in vols],
                         "chars": sum(v["ch"] for v in vols)})

    with open(os.path.join(TEXTDIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"total_chars": total_chars, "files": manifest}, f, ensure_ascii=False, indent=1)
    print("全文分片: %d 道 %d 文件 · 总字数 %s" % (len(manifest), len(manifest), format(total_chars, ",")))
    for m in manifest:
        print("  %-10s %-6s %2d 卷 %9s 字" % (m["id"], m["dao"], len(m["vols"]), format(m["chars"], ",")))


if __name__ == "__main__":
    main()
