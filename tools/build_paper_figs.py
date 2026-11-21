# -*- coding: utf-8 -*-
"""寰宇经纬 · 论文插图生成：python tools/build_paper_figs.py

数据源（口径纪律）：docs/stats.json（tools/build_stats.py 产物，含 dist_raw 558 样本）
——凡数字出自脚本。输出：docs/figs/fig1_dao.png · fig2_dist.png · fig3_books.png
（200dpi 绢本青绿，学 HHH docs/build_paper_figs.py）
build_paper_pdf.py 于插图缺失时自动调用本脚本（管线可重入）。
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "figs")
os.makedirs(OUT, exist_ok=True)

STATS = json.load(open(os.path.join(ROOT, "docs", "stats.json"), encoding="utf-8"))

# ── 绢本青绿版式（沿站点 CSS 与 PDF 配色） ──
SILK, INK, MUTED = "#efe6cf", "#2b2416", "#5a4c34"
TEAL, CINNABAR, GRIDC = "#2f5d70", "#8c2c1c", "#ddd2b2"
plt.rcParams.update({
    "font.family": "Microsoft YaHei", "axes.unicode_minus": False,
    "figure.facecolor": SILK, "axes.facecolor": SILK,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "text.color": INK,
})
KAI = FontProperties(fname=r"C:\Windows\Fonts\simkai.ttf", size=14)


def frame(ax, axis="x"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis=axis, color=GRIDC, lw=.7, alpha=.8)
    ax.set_axisbelow(True)


# ══ 图 1　分道卷帙字数：河南居首 · 四夷第二 ══
dao = sorted(STATS["dao_chars"].items(), key=lambda kv: kv[1])   # stats.json:dao_chars
fig, ax = plt.subplots(figsize=(7.2, 5.4), dpi=200)
frame(ax)
names = [k for k, _ in dao]
vals = [v for _, v in dao]
cols = [CINNABAR if n == "四夷" else TEAL for n in names]
ax.barh(names, vals, color=cols, height=.66, edgecolor=SILK, lw=.5)
for i, v in enumerate(vals):
    ax.text(v + 1500, i, f"{v:,}", va="center", fontsize=8, color=INK)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=9)
ax.set_xlabel("字数", fontsize=9.5)
ax.set_xlim(0, max(vals) * 1.15)
pct = int(dao[[k for k, _ in dao].index("四夷")][1] / STATS["total_chars"] * 1000) / 10  # 截断一口径（ANALYSIS.md 17.4%）
ax.set_title(f"分道卷帙字数——河南道居首，「讫于四夷」占 {pct}%", fontproperties=KAI, pad=12)
ax.legend(handles=[Patch(fc=TEAL, label="十三道"), Patch(fc=CINNABAR, label="四夷（29 卷）")],
          loc="lower right", fontsize=8.5, frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig1_dao.png"))
plt.close(fig)

# ══ 图 2　县距州里程分布：中位 90 里 ══
raw = STATS["dist_raw"]                                       # stats.json:dist_raw（558 样本）
from matplotlib.lines import Line2D
fig, ax = plt.subplots(figsize=(7.2, 4.1), dpi=200)
frame(ax, "y")
ax.hist(raw, bins=range(0, 720, 20), color=TEAL, edgecolor=SILK, lw=.6)
handles = []
for v, lab, c in ((STATS["dist_p10"], "P10", MUTED),
                  (STATS["dist_median_li"], "中位", CINNABAR),
                  (STATS["dist_p90"], "P90", MUTED)):
    ax.axvline(v, color=c, ls="--", lw=1.4)
    handles.append(Line2D([0], [0], color=c, ls="--", lw=1.4, label=f"{lab} {v} 里"))
ax.set_xlabel("县距州里程（里）", fontsize=9.5)
ax.set_ylabel("县条样本数", fontsize=9.5)
ax.legend(handles=handles, loc="upper right", fontsize=9, frameon=True,
          facecolor=SILK, edgecolor=GRIDC)
ax.set_title(f"县距州里程分布（n = {STATS['dist_sample_n']}）——宋初属县贴近州城", fontproperties=KAI, pad=12)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig2_dist.png"))
plt.close(fig)

# ══ 图 3　引书考古 TOP8：两汉与地志双轴 ══
books = list(STATS["book_counts"].items())[:8]                # stats.json:book_counts
fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=200)
frame(ax)
names = [k for k, _ in books][::-1]
vals = [v for _, v in books][::-1]
HIST = {"漢書", "史記", "左傳"}        # 史部三书 vs 地志谱系（文中「两汉书与地志为双轴」）
cols = [CINNABAR if n in HIST else TEAL for n in names]
ax.barh(names, vals, color=cols, height=.62, edgecolor=SILK, lw=.5)
for i, v in enumerate(vals):
    ax.text(v + 4, i, str(v), va="center", fontsize=8.5, color=INK)
ax.set_yticks(range(len(names)))
ax.set_yticklabels([f"《{n}》" for n in names], fontsize=9)
ax.set_xlabel("全书提及次数", fontsize=9.5)
ax.set_xlim(0, max(vals) * 1.13)
ax.set_title("引书考古 TOP8——两汉书与地志的双轴", fontproperties=KAI, pad=12)
ax.legend(handles=[Patch(fc=CINNABAR, label="史部（漢書·史記·左傳）"),
                   Patch(fc=TEAL, label="地志谱系（郡國志·輿地志·圖經·水經注·華陽國志）")],
          loc="lower right", fontsize=8.5, frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig3_books.png"))
plt.close(fig)

print("OK →", OUT, sorted(os.listdir(OUT)))
