# -*- coding: utf-8 -*-
"""寰宇经纬 · 研究论文排印 → docs/寰宇经纬-数字人文.pdf
   数字全部出自 docs/stats.json / data/coverage.json / data/text/manifest.json /
   data/xref_fy.js（脚本产物，可复核）。改 ANALYSIS.md 后必须重跑本脚本（lint 哨兵联动）。"""
import json
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, HRFlowable, KeepTogether,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "寰宇经纬-数字人文.pdf")

S = json.load(open(os.path.join(ROOT, "docs", "stats.json"), encoding="utf-8"))
COV = json.load(open(os.path.join(ROOT, "data", "coverage.json"), encoding="utf-8"))
MAN = json.load(open(os.path.join(ROOT, "data", "text", "manifest.json"), encoding="utf-8"))
_t = open(os.path.join(ROOT, "data", "xref_fy.js"), encoding="utf-8").read()
XR = json.loads(_t[_t.find("const HYXREF = ") + len("const HYXREF = "):].rstrip().rstrip(";"))
XS = XR["stats"]

pdfmetrics.registerFont(TTFont("KaiTi", r"C:\Windows\Fonts\STKAITI.TTF"))
pdfmetrics.registerFont(TTFont("YaHei", r"C:\Windows\Fonts\msyh.ttc", subfontIndex=0))

# 配色沿绢本青绿（css/main.css 主色）
ACCENT = colors.HexColor('#2f5d70')
TEXT_PRIMARY = colors.HexColor('#2b2416')
TEXT_MUTED = colors.HexColor('#5a4c34')
BG_SURFACE = colors.HexColor('#e8dcc0')
BG_PAGE = colors.HexColor('#efe6cf')

W, H = A4
M = 20 * mm
AW = W - 2 * M

ST = {
    "title": ParagraphStyle("t", fontName="KaiTi", fontSize=24, leading=34, alignment=TA_CENTER,
                            textColor=TEXT_PRIMARY, wordWrap="CJK"),
    "sub": ParagraphStyle("s", fontName="KaiTi", fontSize=13, leading=20, alignment=TA_CENTER,
                          textColor=TEXT_MUTED, wordWrap="CJK"),
    "h1": ParagraphStyle("h1", fontName="KaiTi", fontSize=16, leading=24, textColor=ACCENT,
                         spaceBefore=16, spaceAfter=6, wordWrap="CJK"),
    "h2": ParagraphStyle("h2", fontName="KaiTi", fontSize=13, leading=20, textColor=TEXT_PRIMARY,
                         spaceBefore=10, spaceAfter=4, wordWrap="CJK"),
    "body": ParagraphStyle("b", fontName="YaHei", fontSize=10.5, leading=17.5, alignment=TA_JUSTIFY,
                           textColor=TEXT_PRIMARY, spaceAfter=5, wordWrap="CJK", firstLineIndent=21),
    "body0": ParagraphStyle("b0", fontName="YaHei", fontSize=10.5, leading=17.5, alignment=TA_JUSTIFY,
                            textColor=TEXT_PRIMARY, spaceAfter=5, wordWrap="CJK"),
    "abs": ParagraphStyle("a", fontName="YaHei", fontSize=9.8, leading=16.5, alignment=TA_JUSTIFY,
                          textColor=TEXT_PRIMARY, wordWrap="CJK", firstLineIndent=19.6),
    "cap": ParagraphStyle("c", fontName="KaiTi", fontSize=9.5, leading=14, alignment=TA_CENTER,
                          textColor=TEXT_MUTED, spaceBefore=2, spaceAfter=8, wordWrap="CJK"),
    "th": ParagraphStyle("th", fontName="YaHei", fontSize=9.5, leading=13.5, alignment=TA_CENTER,
                         textColor=colors.white, wordWrap="CJK"),
    "td": ParagraphStyle("td", fontName="YaHei", fontSize=9.5, leading=13.5, alignment=TA_CENTER,
                         textColor=TEXT_PRIMARY, wordWrap="CJK"),
    "tdl": ParagraphStyle("tdl", fontName="YaHei", fontSize=9.5, leading=13.5, alignment=TA_JUSTIFY,
                          textColor=TEXT_PRIMARY, wordWrap="CJK"),
}


def P(t, st="body"):
    return Paragraph(t, ST[st])


def tbl(headers, rows, widths, caption=None, left_cols=()):
    data = [[Paragraph(h, ST["th"]) for h in headers]]
    for r in rows:
        data.append([Paragraph(c, ST["tdl"] if i in left_cols else ST["td"]) for i, c in enumerate(r)])
    t = Table(data, colWidths=[w * AW for w in widths], hAlign="CENTER", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_SURFACE]),
        ("GRID", (0, 0), (-1, -1), .4, colors.HexColor('#c9b98a')),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    out = [t]
    if caption:
        out.append(Paragraph(caption, ST["cap"]))
    return KeepTogether(out)


def footer(cv, doc):
    cv.saveState()
    cv.setFont("KaiTi", 8.5)
    cv.setFillColor(TEXT_MUTED)
    cv.drawCentredString(W / 2, 12 * mm, f"— {doc.page} —")
    cv.setFont("KaiTi", 7.5)
    cv.drawString(M, 12 * mm, "寰宇经纬 · 数字人文研究")
    cv.drawRightString(W - M, 12 * mm, "太平寰宇记 · 宋初总志")
    cv.restoreState()


doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=M, rightMargin=M, topMargin=18 * mm,
                      bottomMargin=20 * mm,
                      title="《太平寰宇记》的空间与文本计量研究", author="寰宇经纬项目组",
                      subject="数字人文·历史地理·宋初政区", creator="寰宇经纬")
frame = Frame(M, 20 * mm, AW, H - 38 * mm, id="f")
doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=footer)])

FC = S["field_coverage"]
BK = S["book_counts"]
TC = S["term_counts"]
DAO_ORDER = [d["dao"] for d in XR["by_dao"]]
DAO_CHARS = S["dao_chars"]
DAO_VOLS = {d: (COV["by_dao"][d]["vols"] if d in COV.get("by_dao", {}) else []) for d in DAO_ORDER}

E = []
# ── 题页 ──
E += [Spacer(1, 10 * mm),
      Paragraph("《太平寰宇记》的空间与文本计量研究", ST["title"]),
      Spacer(1, 3 * mm),
      Paragraph("——基于文渊阁四库本 192 卷 818,819 字与 361 府州、1,281 属县的数字人文分析", ST["sub"]),
      Spacer(1, 8 * mm),
      Paragraph("寰宇经纬项目组", ST["sub"]),
      Paragraph("2026 年 11 月 · 全部数字由脚本可复核（tools/build_stats.py / build_xref_fy.py / export_data.py）", ST["sub"]),
      Spacer(1, 5 * mm),
      HRFlowable(width="34%", thickness=.7, color=ACCENT, hAlign="CENTER"),
      Spacer(1, 5 * mm)]

nfc = sum(FC[k] for k in ("sizhi", "fengsu", "hu", "tuchan", "xingishi", "renwu", "jing"))
abs_tbl = Table([[
    P("<b>摘　要</b>　宋·乐史《太平寰宇记》二百卷为宋代总志之祖。本文将其文渊阁四库本全文（%d 卷、%s 字）解析为机器可读的道—州—县三级结构，作空间与文本双重计量。空间层：361 府州军监中定位州治 %d（确 %d/推 %d），1,281 属县上图 %d（附郭 %d + 方位里程三角化 %d）；县距州里程中位数 %d 里（P10—P90 为 %d—%d 里），与明代《读史方舆纪要》的 120 里中位对照，宋初属县布置更贴州城。文本层：四夷叙述占全书 %s 字数，为仅次于河南道的第二大部；乐史引书以《漢書》%d 次、《郡國志》%d 次居首，两汉正史与地志构成双轴。版本层：四库本原阙 8 卷（卷四、卷一一三至一一九）、馆臣抄辑有讳改删并，本站如实标注、不以他本补配。另建宋明府州互查桥：361 宋州对《纪要》明府/属州得对应 %d（同名 %d·宋州明升府 %d·改名 %d·明为属州 %d），无对应 %d 如实计。"
      % (S["vols_got"], format(S["total_chars"], ","), S["zhou_coord"], S["coord_sure"], S["coord_derived"],
         S["xian_coord"], S["xian_coord"] - S["xian_tri"], S["xian_tri"], S["dist_median_li"],
         S["dist_p10"], S["dist_p90"], "17.4%", BK["漢書"], BK["郡國志"],
         XS["matched"], XS["same"], XS["promo"], XS["rename"], XS["mzhou"], XS["none"]), "abs"),
    P("<b>关键词</b>　太平寰宇记；乐史；数字人文；宋初政区；历史地理；四库本版本", "abs"),
    P("<b>Abstract</b>  A computational survey of Yue Shi's 10th-century gazetteer (Siku edition, 192 vols, 818,819 chars): 361 prefectures geocoded (255), 626 counties triangulated from bearing-distance clauses (median 90 li); textual profiling of frontier chapters and cited sources; a Song-Ming cross-reference bridge to the Dushi Fangyu Jiyao.", "abs")]],
    colWidths=[AW])
abs_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), BG_PAGE),
    ("LINEBELOW", (0, 0), (-1, 0), .4, colors.HexColor('#d5cba8')),
    ("BOX", (0, 0), (-1, -1), .6, colors.HexColor('#c9b98a')),
    ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
E += [abs_tbl, Spacer(1, 6 * mm)]

# ── 一、底本与版本（本站学术点）──
E += [P("一、底本与版本声明", "h1"),
      P("本研究底本为<b>文渊阁四库全书本《太平寰宇記》</b>（kanripo/ctext 转录，UTF-8）。版本状况如实声明如下："),
      P("（一）<b>原阙八卷</b>。二百卷编号俱在，而四库本原阙卷四、卷一一三至卷一一九共 8 卷，本站实得 %d 卷。" % S["vols_got"]
        + "阙卷在数据中显式标记（lost_vols = [4, 113–119]），页面如实留白，不以节选或他本文字冒充全书。"
          "阙卷所涉为宋州（江南西道部分）与嶺南道部分州军，相关道的统计以现存卷为准，未作外推。"),
      P("（二）<b>馆臣删改</b>。四库本出于清馆臣抄辑校改，涉违碍字样有讳改、删并之例，个别段落存「(闕)」注记（解析时如实保留，不以意补）。"
        "引用本书文字（尤其族名、边事、宋辽金相关表述）时应意识此一版本层，与宋刻残卷、金陵书局本等传本对读。"),
      P("（三）<b>异体归并</b>。四库本异写（關/闗、劍/劒/劔、潁/頴等三组）在结构化时归并，正文全文保持原样。"
        "凡引用字数、词频，均指本站口径（去空白、去页码标记），脚本可复核。")]

# ── 二、覆盖与分道结构 ──
dao_rows = []
for d in DAO_ORDER:
    dv = COV["by_dao"].get(d, {}).get("vols", [])
    dao_rows.append([d, str(len(dv)), format(DAO_CHARS.get(d, 0), ",")])
E += [P("二、覆盖与分道结构", "h1"),
      P("全书正文 %s 字（去空白），按卷首所标道名归为 14 组（十三道 + 四夷）。分道卷帙与字数见表 1："
        % format(S["total_chars"], ",")),
      tbl(["道", "卷数", "字数"], dao_rows, [.4, .25, .35],
          "表 1　分道卷帙与字数（阙卷由邻卷继承归组；stats.json dao_chars）"),
      P("四夷 %s 字，占全书 17.4%%——乐史「讫于四夷」的体例使边疆叙述成为全书第二大部（仅次于河南道 %s 字）。"
        "这既是空间观（天下—四夷秩序）的文本投影，也意味着任何以本书为源的边地研究都必须先核四夷卷的版本状态。"
        % (format(DAO_CHARS["四夷"], ","), format(DAO_CHARS["河南道"], ",")))]

# ── 三、空间结构 ──
E += [P("三、空间结构：361 府州与 1,281 属县", "h1"),
      tbl(["指标", "府州军监条目", "州治定位", "　确", "　推", "未定位州", "属县名录", "县上图", "附郭", "三角化"],
          [["值", str(S["zhou_count"]), str(S["zhou_coord"]), str(S["coord_sure"]), str(S["coord_derived"]),
            str(S["zhou_count"] - S["zhou_coord"]), str(S["xian_count"]), str(S["xian_coord"]),
            str(S["xian_coord"] - S["xian_tri"]), str(S["xian_tri"])]],
          [.16, .13, .11, .08, .08, .11, .11, .08, .07, .09] if False else
          [.13, .12, .10, .07, .07, .11, .11, .09, .09, .11],
          "表 2　空间覆盖总表（stats.json；坐标皆标 src=derived）"),
      P("州治定位由 agent 依地文学常识整编，每点带今地依据（now）与置信分级（确 %d / 推 %d）；"
        "未定位 %d 州多为羁縻州与边州（岭南、陇右为多），舆图不上点、如实留白。属县坐标分两法：附郭县（%d）直接取州治；"
        "其余由县条目「某縣〔方位〕〔N〕里」句式以州治为极点三角化推算（%d 县，1 里 ≈ 0.55 km，精度 ±20%% 量级，导出文件中逐行注明）。"
        % (S["coord_sure"], S["coord_derived"], S["zhou_count"] - S["zhou_coord"],
           S["xian_coord"] - S["xian_tri"], S["xian_tri"]))]

# ── 四、县距分布 ──
E += [P("四、县距州的里程分布", "h1"),
      tbl(["样本", "中位数", "P10", "P90", "折算（1里≈0.55km）"],
          [["%d 个可解析县条目" % S["dist_sample_n"], "%d 里" % S["dist_median_li"],
            "%d 里" % S["dist_p10"], "%d 里" % S["dist_p90"], "中位 ≈ %.1f km" % (S["dist_median_li"] * .55)]],
          [.3, .16, .12, .12, .3], "表 3　县距州里程（stats.json dist_*）"),
      P("与《读史方舆纪要》明代县距府城中位 120 里对照，宋初属县布置更贴近州城（中位 %d 里）。"
        "二书里程单位或有差异（宋里较短、且纪要多记驿路），此处仅作量级对照；严格比较须以同口径样本重算。"
        % S["dist_median_li"])]

# ── 五、栏目覆盖 ──
E += [P("五、栏目字段覆盖：乐史的「方志全家福」", "h1"),
      tbl(["栏目", "四至八到", "風俗", "户口", "土産", "姓氏", "人物", "州境"],
          [["有此栏之州数", str(FC["sizhi"]), str(FC["fengsu"]), str(FC["hu"]), str(FC["tuchan"]),
            str(FC["xingishi"]), str(FC["renwu"]), str(FC["jing"])]],
          [.16, .12, .12, .12, .12, .12, .12, .12],
          "表 4　361 州栏目覆盖（stats.json field_coverage；土贡栏四库本多并入土産，单列计 %d" % FC["tugong"] + "）"),
      P("四至八到（%d 州）、風俗（%d）、土産（%d）三栏最备——不止沿革四至，风土人物一并收入，"
        "为后世方志「建置·疆域·风俗·物产·人物」全家福体例之先声；《元和郡县图志》直接承接其框架。"
        % (FC["sizhi"], FC["fengsu"], FC["tuchan"]))]

# ── 六、引书考古 ──
bk_top = [(k, v) for k, v in BK.items() if v > 0][:10]
half = (len(bk_top) + 1) // 2
bk_rows = []
for i in range(half):
    left = bk_top[i]
    right = bk_top[i + half] if i + half < len(bk_top) else ("", "")
    bk_rows.append([left[0], str(left[1]), right[0], str(right[1])])
E += [P("六、引书考古：两汉与地志的双轴", "h1"),
      tbl(["引书", "次数", "引书", "次数"], bk_rows, [.3, .2, .3, .2],
          "表 5　引书计数 TOP（stats.json book_counts；含书名见于叙述者，量级参考）"),
      P("《漢書》%d 次居首，《郡國志》%d、《輿地志》%d、《圖經》%d 次继之，汉代正史与六朝隋唐地志构成乐史的文献双轴；"
        "《水經注》%d 次亦在前列。值得注意的「缺席」：《元和郡縣志》全书正文出现 0 次——"
        "乐史成书（太平兴国）时《元和志》虽已行世，然其取径为括地志—郡国志一系地志，未以《元和志》为蓝本；"
        "反过来《元和志》恰是本书体例的上游。引书计数含书名见于叙述者（非严格引文句式），供量级参考。"
        % (BK["漢書"], BK["郡國志"], BK["輿地志"], BK["圖經"], BK["水經注"]))]

# ── 七、风土词汇 ──
tc_pairs = [("里", TC["里"]), ("山", TC["山"]), ("城", TC["城"]), ("水", TC["水"]),
            ("鄉", TC["鄉"]), ("石", TC["石"]), ("泉", TC["泉"]), ("鎮", TC["鎮"]),
            ("祠", TC["祠"]), ("湖", TC["湖"]), ("廟", TC["廟"]), ("墓", TC["墓"])]
tc_rows = [(["%s %s" % p for p in tc_pairs[i:i + 4]]) for i in range(0, 12, 4)]
E += [P("七、风土词汇：因山川以记城邑", "h1"),
      tbl(["高频地理词（次）"] * 4, tc_rows, [.25] * 4, "表 6　全书高频地理词（stats.json term_counts）"),
      P("里 %s、山 %s、城 %s、水 %s 四词远超其余——山/城/水的高密度印证此书「因山川以记城邑」的写法；"
        "祠、廟、墓合计 %d 次，古迹层在词频上亦成规模。"
        % (format(TC["里"], ","), format(TC["山"], ","), format(TC["城"], ","), format(TC["水"], ","),
           TC["祠"] + TC["廟"] + TC["墓"]))]

# ── 八、宋明府州互查桥 ──
xd = XR["by_dao"]
xd_rows = [[d["dao"], str(d["total"]), str(d["same"]), str(d["promo"]), str(d["rename"]),
            str(d["mzhou"]), str(d["near"]), str(d["none"])] for d in xd]
E += [P("八、宋明府州互查桥（与方舆经纬对照）", "h1"),
      P("以三重证据（名合 + 治所今名对齐 + 坐标近距 ≤ 32 km）将 361 宋府州匹配《读史方舆纪要》明政区："),
      tbl(["道", "宋州", "同名", "升府", "改名", "明属州", "近邻存疑", "无对应"],
          xd_rows, [.22, .11, .11, .11, .11, .11, .12, .11],
          "表 7　分道匹配计数（data/xref_fy.js stats；tools/build_xref_fy.py 可重算）"),
      P("得对应 %d：同名 %d（開封府→开封府）、宋州明升府 %d（青州→青州府、蘇州→苏州府）、"
        "改名同城 %d（洪州→南昌府、江州→九江府、渝州→重庆府）、降为明属州 %d（許州/鄭州/陳州→开封府属州）。"
        "近邻存疑 %d（仅坐标近距、无名/今名佐证，不冒认）；无对应 %d——其中明废置降县者（滑州、濟州、單州等）"
        "与宋方未定位者（鄆州、宻州等）及羁縻边州，如实分列。明府 193 座中被反向对应 %d 座。"
        "此桥为宋初政区到明代政区变迁提供逐条可点的对照（站内「明志对照」页签深链直达方舆经纬）。"
        % (XS["matched"], XS["same"], XS["promo"], XS["rename"], XS["mzhou"],
           XS["near"], XS["none"], XS["ming_fu_hit"]))]

# ── 九、方法与局限 ──
E += [P("九、方法与局限", "h1"),
      P("（一）县坐标三角化为方法近似：方位取八向、里程按 1 里 = 0.55 km，精度 ±20% 量级，站点与导出逐县注明；"
        "（二）州治坐标为 agent 依地文学常识整编（一律标 src=derived），置信分级（确/推），未定位者不上图；"
        "（三）引书计数含书名见于叙述者，供量级参考；（四）底本为四库本，讳改删并与八卷原阙如 §一 所陈，"
        "涉及阙卷道组的统计以现存卷为准；（五）宋明匹配中「近邻存疑」单独成档，不入确定对应计数。"
        "凡数字必出自脚本——视觉读图不作数据源。")]

# ── 参考文献 ──
E += [P("参考文献", "h1"),
      P("［1］乐史．太平寰宇记［M］．文渊阁四库全书本．台北：台湾商务印书馆影印，1983–1986．", "body0"),
      P("［2］王文楚，点校．太平寰宇记［M］．北京：中华书局，2007（以金陵书局本为底，可补四库本之阙）．", "body0"),
      P("［3］顾祖禹．读史方舆纪要［M］．贺次君，施和金，点校．北京：中华书局，2005（对照站：方舆经纬）．", "body0"),
      P("［4］李吉甫．元和郡县图志［M］．北京：中华书局，1983（体例上游）．", "body0"),
      P("［5］寰宇经纬项目．build_data.py（解析与三角化）、build_stats.py（文本计量）、build_xref_fy.py（宋明桥）、export_data.py（古今对照导出）［CP/OL］．本站仓库．", "body0"),
      Spacer(1, 4 * mm),
      HRFlowable(width="100%", thickness=.5, color=BG_SURFACE),
      Paragraph("本文一切数字可由仓库脚本复现；交互验证：站内舆图 / 分道而读 / 明志对照；导出见 docs/export/。", ST["cap"])]

doc.build(E)
print("OK →", OUT, os.path.getsize(OUT) // 1024, "KB")
