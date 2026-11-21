# -*- coding: utf-8 -*-
"""
寰宇经纬 · 结构化解析管线（可重入）
data_raw/KR2k0004_NNN.txt (四库本 Kanripo 转录)
  → 段落化 → 状态机解析(道/府州/县/栏目) → 坐标整编/推算
  → data/site_data.js (前端结构化数据) + data/intermediate/full.json (管线中间产物)

版刻结构约定(实测):
  - 段落 = 连续非空行合并; 空行分段
  - 行首两个全角空格 = 顶格条目(府州标题/栏目/县条目/古迹)
  - 卷首段落: 太平寰宇記卷N / 宋 樂史 撰 / 「XX道N」/ 首府州名
  - 府州沿革段: 「汝州臨汝郡今理梁縣禹貢…」(州名+郡名+今理)
  - 县条目: 「葉縣西南二百里舊七鄉…」(县名[方位里程]…), 附郭县无里程
  - 阙卷: 正文仅「(闕)」或「(原闕)」
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
from coords import CURATED, CONF_SURE as CONF_SURE_TAG   # 州治今地坐标整编表(人工依地文学常识, 全部 src=derived)

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data_raw")
OUTDIR = os.path.join(HERE, "data")
INTDIR = os.path.join(OUTDIR, "intermediate")

SECTIONS = ("元領縣", "州境", "府境", "四至八到", "户", "風俗", "姓氏", "人物", "土産", "土貢", "古蹟", "古跡")
ZH_NUM = "一二三四五六七八九十百"
DAO_RE = re.compile(r"^[　\s]*((?:[\u4e00-\u9fff]{1,4}道|四夷))[" + ZH_NUM + r"]*[　\s]*$")
ZHOU_TAIL = ("府", "州", "軍", "監")


def load_paras(n: int):
    """读卷 → 段落列表（保留段落首缩进），未得/阙卷返回 None。
    四库本版式: 版叶 a 面页眉「欽定四庫全書」· b 面页脚「太平寰宇記卷N」· 卷首「宋 樂史 撰」——逐行滤除。"""
    p = os.path.join(RAW, "KR2k0004_%03d.txt" % n)
    if not os.path.exists(p):
        return None
    t = open(p, encoding="utf-8").read()
    t = "\n".join(ln for ln in t.split("\n") if not ln.startswith("#"))
    t = re.sub(r"<pb:[^>]*>", "", t).replace("¶", "")
    juan_hdr = re.compile(r"^[　\s]*太平寰宇記卷[一二三四五六七八九十百]+[　\s]*$")
    keep = []
    for ln in t.split("\n"):
        s = ln.strip()
        if not s:
            keep.append("")          # 空行 = 段落边界, 必须保留
            continue
        if s == "欽定四庫全書" or juan_hdr.match(ln):
            continue
        if re.match(r"^[　\s]*宋[　\s]+樂史[　\s]+撰[　\s]*$", ln):
            continue
        keep.append(ln)
    # 空行即段界
    buf, paras = [], []
    for ln in keep:
        if ln.strip():
            buf.append(ln)
        elif buf:
            paras.append("".join(buf))
            buf = []
    if buf:
        paras.append("".join(buf))
    body = "".join(paras)
    core = re.sub(r"\(闕\)|\(原闕\)|\(阙\)|\(原阙\)|\s", "", body)
    if len(core) < 60:
        return None  # 阙卷(整卷无正文; 局部「(闕)」缺文注记不在此列)
    return paras


def norm_dao(d: str):
    """道名归一化: 异体字/阙名兜底"""
    if not d:
        return d
    d = d.replace("闗", "關").replace("劒", "劍").replace("劔", "劍")
    return {"關西道": "關西道", "右江道": "嶺南道", "已上右江道": "嶺南道"}.get(d, d)


def norm_zhou(z: str) -> str:
    """州名归一化: 潁/頴 异体"""
    return z.replace("潁", "頴")


def head(p: str) -> str:
    """去段落首两个全角空格"""
    return p[2:] if p.startswith("\u3000\u3000") else p


def is_indented(p: str) -> bool:
    return p.startswith("\u3000\u3000")


def _clean_zhou_name(h: str) -> str:
    """候选州名净化: 去尾序数, 拒绝变动注记/合卷标题"""
    h = re.sub(r"[" + ZH_NUM + r"]+$", "", h.strip())
    if len(h) < 2 or len(h) > 8:
        return ""
    if any(w in h for w in ("入", "割", "併", "並", "并", "廢", "徙", "隸", "自", "同", "仝",
                            "置", "為", "在", "去", "至", "載", "具", "户", "縣", "都督", "　")):
        return ""
    if h.endswith("建軍"):   # 「唐明建軍」= 建置注记, 非州名
        return ""
    if h[-1] in ZHOU_TAIL and not h.startswith("("):
        return h
    return ""


def is_zhou_title(p: str) -> str:
    """「汝州」「開封府一」→ 州名; 非条目返回 ''"""
    if not is_indented(p):
        return ""
    h = head(p).strip()
    if len(h) > 12:
        return ""
    return _clean_zhou_name(h)


def zhou_titles(p: str):
    """合卷标题「滑州　鄭州」→ ['滑州','鄭州']; 单标题 → [名]; 非标题 → []"""
    if not is_indented(p):
        return []
    h = head(p).strip()
    if len(h) > 16 or (len(h) <= 12 and not re.search(r"[　\s]", h)):
        z = is_zhou_title(p)
        return [z] if z else []
    # 含全角空格的短标题 → 拆分逐个校验
    toks = [t for t in re.split(r"[　\s]+", h) if t]
    if len(toks) < 2 or len(h) > 16:
        return []
    out = []
    for t in toks:
        z = _clean_zhou_name(t)
        if not z:
            return []   # 任一 token 非州名 → 整段不是合卷标题
        out.append(z)
    return out


def zhou_yanlai(p: str):
    """沿革段: 「汝州臨汝郡今理梁縣禹貢…」「宋州睢陽郡理宋城縣…」→ (州名, 今理县串)"""
    if not is_indented(p):
        return None
    h = head(p)
    if len(h) < 12:
        return None
    m = re.match(r"^([\u4e00-\u9fff]{1,6}?(?:府|州|軍|監))", h)
    if not m:
        return None
    name = m.group(1)
    if not _clean_zhou_name(name):
        return None
    jl = re.search(r"(?:今理|郡理|今)([\u4e00-\u9fff]{1,6})縣", h[:30])
    if not jl:
        return None   # 无「今理/郡理X縣」句式 → 非沿革段
    jinli = None
    if jl:
        jinli = jl.group(1)
        jinli = re.sub(r"[一二三四五六七八九十百]$", "", jinli)   # 「長安萬年二」→「長安萬年」
        if len(jinli) in (4, 6):   # 双附郭「開封浚儀」→「開封、浚儀」
            jinli = "、".join(jinli[i:i + 2] for i in range(0, len(jinli), 2))
    return (name, jinli)


def county_list(paras, i: int):
    """「元領縣」段之后的段(缩进或顶格续段) → 县名列表; 返回 (names, next_i)"""
    names = []
    j = i + 1
    while j < len(paras) and j <= i + 4:
        q = paras[j].strip()
        if not q:
            break
        if q.startswith(("一縣", "二縣", "三縣", "四縣", "五縣", "六縣", "七縣", "八縣", "九縣", "十縣",
                         "十一縣", "元領")) or q in SECTIONS:
            break
        toks = re.split(r"[　\s]+", q)
        got = []
        for tk in toks:
            tk = re.sub(r"\(.*?\)", "", tk).strip()
            if not tk:
                continue
            tk = re.sub(r"(?:自.{0,5})?割到$|(?:自.{0,5})?割出$|新置$|入.{0,4}$", "", tk)
            if tk and _like_county(tk):
                got.append(tk)
        q_core = re.sub(r"\(.*?\)", "", q.replace("　", ""))
        if got and len(q) <= 240 and sum(len(g) for g in got) >= len(q_core) * .5:
            names.extend(got)
            j += 1
            continue
        break
    return names, j


def _like_county(s: str) -> bool:
    if s in SECTIONS or s.endswith(("廢", "併", "置", "省", "割", "到", "鄉", "里")):
        return False
    if re.match(r"^[一二三四五六七八九十百]+縣", s):   # 「一縣割出」类
        return False
    if any(w in s for w in ("入", "割", "併", "境", "廢", "所")):
        return False
    return len(s) <= 4


def parse_vol(n: int):
    """一卷 → {vol, dao, zhou:[...]}；阙卷返回 {vol, dao, zhou:[]} 且 lost=True"""
    paras = load_paras(n)
    if paras is None:
        return {"vol": n, "lost": True, "dao": None, "zhou": []}
    dao = None
    out = []
    cur = None          # 当前府州 dict
    cur_counties = []   # 当前府州县名白名单
    i = 0
    while i < len(paras):
        p = paras[i]
        # 卷首: 道名
        m = DAO_RE.match(p)
        if m:
            dao = norm_dao(m.group(1))
            i += 1
            continue
        # 栏目: 元領縣 → 县清单
        h = head(p).strip() if is_indented(p) else ""
        if h.startswith("元領縣") or h.startswith("領縣"):
            if cur is not None:
                names, j = county_list(paras, i)
                cur["xian_list"] = names
                cur_counties = names
                i = j
                continue
        # 栏目字段
        sec_hit = next((s for s in SECTIONS if h == s or (len(s) >= 2 and h.startswith(s))), "")
        if sec_hit or h.startswith("四至八到"):
            key_h = sec_hit or "四至八到"
            if cur is not None and key_h not in cur["fields"] and key_h not in ("元領縣",):
                # 栏目内容 = 下一段(顶格或缩进的正文)
                # 栏目内容 = 紧随的第一段(四库栏目正文多为一段; 续文已在段内)
                val = ""
                j = i + 1
                if j < len(paras):
                    q = paras[j]
                    qh = head(q).strip() if is_indented(q) else q.strip()
                    nxt = paras[j] if j + 1 < len(paras) else ""
                    nxt_h = head(nxt).strip() if is_indented(nxt) else nxt.strip()
                    is_new_item = (DAO_RE.match(q) or zhou_titles(q) or zhou_yanlai(q)
                                   or qh in SECTIONS or qh.startswith("元領"))
                    if not is_new_item and qh and not qh.startswith(("一縣", "二縣", "三縣")):
                        val = qh[:400]
                        j += 1
                key = {"州境": "jing", "府境": "jing", "四至八到": "sizhi", "户": "hu",
                       "風俗": "fengsu", "土貢": "tugong", "土産": "tuchan",
                       "姓氏": "xingishi", "人物": "renwu"}.get(key_h, key_h)
                cur["fields"][key] = val[:400]
                i = j
                continue
        # 府州沿革段(优先: 「XX州…今理…」)
        zy = zhou_yanlai(p)
        if zy:
            name, jinli = zy
            if cur is not None and cur["name"] == norm_zhou(name) and not cur["yanzhi"]:
                cur["yanzhi"] = p.strip()
                cur["jinli"] = jinli
            else:
                cur = {"name": norm_zhou(name), "jinli": jinli, "yanzhi": p.strip(), "vol": n,
                       "fields": {}, "xian_list": [], "xian_paras": [], "tail": []}
                out.append(cur)
            cur_counties = []
            i += 1
            continue
        # 府州标题段(短; 含合卷「滑州　鄭州」拆分)
        zts = zhou_titles(p)
        if zts:
            first = None
            for zt in zts:
                cur = {"name": norm_zhou(zt), "jinli": None, "yanzhi": "", "vol": n,
                       "fields": {}, "xian_list": [], "xian_paras": [], "tail": []}
                out.append(cur)
                if first is None:
                    first = cur
            cur = first          # 合卷: 当前态指向首州, 沿革段到达时再切换
            cur_counties = []
            i += 1
            continue
        # 县条目: 白名单内 县名+縣 开头
        if cur is not None and is_indented(p):
            hh = head(p)
            m2 = re.match(r"^([\u4e00-\u9fff]{1,4})縣", hh)
            if m2 and m2.group(1) in cur_counties:
                cur["xian_paras"].append(p.strip())
                i += 1
                continue
        # 其余 → 当前府州正文尾部(顶格续文或古迹段)
        if cur is not None:
            cur["tail"].append(p.strip())
        i += 1
    return {"vol": n, "dao": dao, "zhou": out, "lost": False}


def main():
    os.makedirs(INTDIR, exist_ok=True)
    vols = [parse_vol(n) for n in range(1, 201)]
    # 道名补全: 阙卷/缺道名 → 用相邻实卷
    last_dao = None
    for v in vols:
        if v["dao"]:
            last_dao = v["dao"]
        else:
            v["dao"] = last_dao
    # 阙卷道名: 前后包夹(卷4 阙 → 用卷3/卷5 道)
    for idx, v in enumerate(vols):
        if not v["lost"]:
            continue
        for nb in (idx - 1, idx + 1):
            if 0 <= nb < len(vols) and vols[nb]["dao"]:
                v["dao"] = vols[nb]["dao"]
                break

    got = [v for v in vols if not v["lost"]]
    zhous = []
    for v in got:
        for z in v["zhou"]:
            z["dao"] = v["dao"]
            zhous.append(z)
    # 同名府州跨卷去重说明: 太平寰宇记一府州常跨卷, 首条(有沿革)为主条目, 续条并入
    merged = {}
    order = []
    for z in zhous:
        key = z["name"]
        if key not in merged:
            z["vols"] = [z["vol"]]
            merged[key] = z
            order.append(key)
        else:
            t = merged[key]
            if z["vol"] not in t["vols"]:
                t["vols"].append(z["vol"])
            if not t["yanzhi"] and z["yanzhi"]:
                t["yanzhi"] = z["yanzhi"]
                t["jinli"] = z["jinli"]
            for k, val in z["fields"].items():
                t["fields"].setdefault(k, val)
            t["xian_list"] = t["xian_list"] or z["xian_list"]
            t["xian_paras"].extend(z["xian_paras"])
            t["tail"].extend(z["tail"])

    # ghost 条目(无沿革无县清单, 多为粘连注记) → 丢弃
    order = [k for k in order if merged[k]["yanzhi"] or merged[k]["xian_list"]
             or len(merged[k]["vols"]) > 1 or k in CURATED]

    # ── 坐标整编 + 县三角化 ──
    BEARING = {"東": 90, "西": 270, "南": 180, "北": 0, "東南": 135, "西南": 225,
               "東北": 45, "西北": 315}
    LI_KM = 0.55   # 宋初里≈550m
    DIG = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}

    def zh_li(s):
        """汉字里程 → 里数(汉); 「二百」=200 「四十五」=45 「一百二」=102"""
        m = re.match(r"^([一二三四五六七八九十百]+)里", s)
        if not m:
            return None
        t = m.group(1)
        if t == "十":
            return 10
        if "百" in t:
            head, _, tail = t.partition("百")
            base = DIG.get(head, 1) * 100
            if not tail:
                return base
            if tail == "十":
                return base + 10
            if tail.startswith("十"):
                return base + DIG.get(tail[1:], 0)
            return base + DIG.get(tail, 0)
        if "十" in t:
            head, _, tail = t.partition("十")
            return DIG.get(head, 1 if head == "" else 0) * 10 + DIG.get(tail, 0)
        return DIG.get(t)

    def xian_pos(zhou_c, dist_text):
        """县条目方位里程 → 推算坐标"""
        if not zhou_c:
            return None, None
        m = re.match(r"^(東南|西南|東北|西北|東|西|南|北)([一二三四五六七八九十百]+)里", dist_text)
        if not m:
            return None, None
        br, li = m.group(1), zh_li(m.group(2) + "里")
        if li is None or li > 800:
            return None, None
        d = li * LI_KM
        import math
        rad = math.radians(BEARING[m.group(1)])
        dlat = d * math.cos(rad) / 111.0
        dlng = d * math.sin(rad) / (111.0 * math.cos(math.radians(zhou_c[0])))
        return [round(zhou_c[0] + dlat, 3), round(zhou_c[1] + dlng, 3)], "%s%s里" % (m.group(1), m.group(2))

    out_zhou = []
    n_coord = n_sure = n_derived = 0
    for k in order:
        z = merged[k]
        cur = CURATED.get(k)
        coord = [cur[0], cur[1]] if cur else None
        now = cur[2] if cur else None
        cf = cur[3] if cur else None
        if coord:
            n_coord += 1
            if cf == CONF_SURE_TAG:
                n_sure += 1
            else:
                n_derived += 1
        # 县: 附郭(州治) + 三角化
        jl_names = [x for x in re.split("[、]", z["jinli"] or "")]
        xians = []
        for xn in z["xian_list"]:
            entry = {"n": xn}
            if xn in jl_names and coord:
                entry["c"] = coord
                entry["src"] = "fu"       # 附郭=州治
            else:
                # 在县条目段中找该县方位里程
                hit = None
                for xp in z["xian_paras"]:
                    hh = head(xp) if xp.startswith("\u3000\u3000") else xp
                    if hh.startswith(xn + "縣"):
                        c, d = xian_pos(coord, hh[len(xn) + 1:len(xn) + 12])
                        if c:
                            hit = (c, d)
                        break
                if hit:
                    entry["c"] = hit[0]
                    entry["d"] = hit[1]
                    entry["src"] = "tri"   # 方位里程三角化
            xians.append(entry)
        out_zhou.append({
            "n": k, "dao": z["dao"], "vols": z["vols"], "jl": z["jinli"],
            "c": coord, "now": now, "cf": cf, "src": "derived" if coord else None,
            "yz": z["yanzhi"][:520], "ex": {kk: vv for kk, vv in z["fields"].items() if vv},
            "xian": xians, "xc": len(z["xian_paras"]),
        })
    n_xc = sum(1 for z in out_zhou for x in z["xian"] if x.get("c"))
    n_tri = sum(1 for z in out_zhou for x in z["xian"] if x.get("src") == "tri")

    total_chars = 0
    for v in vols:
        if v["lost"]:
            continue
        ps = load_paras(v["vol"])
        if ps:
            total_chars += len(re.sub(r"\s", "", "".join(ps)))

    report = {
        "vols_total": 200,
        "vols_got": len(got),
        "vols_lost": [v["vol"] for v in vols if v["lost"]],
        "daos": {},
        "zhou_count": len(order),
        "xian_count": sum(len(z["xian_list"]) for z in merged.values()),
        "zhou_coord": n_coord, "coord_sure": n_sure, "coord_derived": n_derived,
        "total_chars": total_chars,
        "xian_coord": n_xc, "xian_tri": n_tri,
    }
    for v in got:
        report["daos"].setdefault(v["dao"], []).append(v["vol"])

    # ── data/site_data.js ──
    DAO_PINYIN = {"河南道": "henan", "關西道": "guanxi", "河東道": "hedong", "河北道": "hebei",
                  "劍南西道": "jiannanxi", "劍南東道": "jiannandong", "江南東道": "jiangnandong",
                  "江南西道": "jiangnanxi", "淮南道": "huainan", "山南西道": "shannanxi",
                  "山南東道": "shannandong", "隴右道": "longyou", "嶺南道": "lingnan", "四夷": "siyi"}
    dao_ids = {}
    def dao_id(name):
        if name not in dao_ids:
            dao_ids[name] = DAO_PINYIN.get(name, "dao%d" % (len(dao_ids) + 1))
        return dao_ids[name]

    daos_js = []
    for dname, vv in sorted(report["daos"].items(), key=lambda x: min(x[1])):
        daos_js.append({"id": dao_id(dname), "name": dname, "vols": vv,
                        "zc": sum(1 for z in out_zhou if z["dao"] == dname)})
    lost_vols = report["vols_lost"]
    js = ("/* 《太平寰宇記》數據 · build_data.py 生成 · 勿手改 */\n"
          "const HY = " + json.dumps({
              "book": "太平寰宇記", "author": "樂史(宋)",
              "edition": "文淵閣四庫全書本 · kanripo/ctext 轉錄",
              "daos": daos_js, "zhou": out_zhou,
              "lost_vols": lost_vols,
              "stats": report,
          }, ensure_ascii=False, separators=(",", ":")) + ";\n")
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "site_data.js"), "w", encoding="utf-8") as f:
        f.write(js)
    with open(os.path.join(INTDIR, "full.json"), "w", encoding="utf-8") as f:
        json.dump({"vols": vols, "merged": {k: merged[k] for k in order}, "report": report},
                  f, ensure_ascii=False)
    print("解析: 实卷 %d · 阙卷 %s" % (len(got), report["vols_lost"]))
    print("府州 %d (定位 %d: 确 %d / 推 %d) · 县 %d (上图 %d: 附郭 %d + 三角化 %d)"
          % (len(order), n_coord, n_sure, n_derived, report["xian_count"], n_xc,
             n_xc - n_tri, n_tri))
    for d, vv in sorted(report["daos"].items(), key=lambda x: min(x[1])):
        print("  %-6s %2d 卷  卷%d–卷%d" % (d, len(vv), min(vv), max(vv)))
    return report


if __name__ == "__main__":
    main()
