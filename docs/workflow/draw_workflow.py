#!/usr/bin/env python3
"""Draw the trio workflow plate as a metro map, in PNG and PDF.

Each role is a line, each action a station, each stop an interchange where all
three lines meet, and each batch a small PR square on a worker track.

Usage:
  python docs/workflow/draw_workflow.py [--lang en|zh] [--out-dir docs/workflow]

Needs matplotlib. Latin fonts come from the canvas-design skill folder and the
Chinese font from Windows DengXian; pass --font-dir / --cjk-font to override.
After drawing, every label is checked against the canvas and against every
other label; any overflow or overlap is printed and the script exits 1.
"""

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402

W, H = 2400, 1240
PAPER, INK, MUTED, HAIR, WHITE = "#F6F3EC", "#18202E", "#6E6B64", "#DCD4C6", "#FFFFFF"
OPERATOR, REVIEWER, BUILDER, WORKER = "#D2603F", "#3A4FA8", "#1F8A70", "#7DBFAE"
Y_O, Y_R, Y_B = 470, 610, 750
WORKER_Y = (820, 870, 920)
START, S1, S2, S3, MAIN = 230, 760, 1560, 2010, 2270
BRANCH_FROM, BRANCH_TO = 930, 1420
LINE_W = 9

TEXT = {
    "en": {
        "title": "trio workflow",
        "subtitle": "One plan as a journey. You decide, one agent reviews, another builds. Stops are where all three meet.",
        "legend_lines": [("Operator", "you"), ("Reviewer", "agent A"), ("Builder", "agent B")],
        "legend_marks": ["action", "stop", "batch PR with CI (PR mode)"],
        "operator": [(340, "Set the goal"), (560, "Answer decisions"), (1160, "Report problems"), (1780, "Walk through"), (2135, "Authorize")],
        "reviewer": [(340, "Bootstrap"), (560, "Draft the plan"), (1160, "Change requests"), (1780, "Sort findings"), (2135, "Retro")],
        "builder": [(880, "Kick off"), (1470, "Integrate"), (1780, "Screenshots"), (2135, "Plan PR")],
        "stops": [(S1, "Stop 1", "Contract"), (S2, "Stop 2", "Review"), (S3, "Stop 3", "Final")],
        "main": "main",
        "captions": [(S1, 990, "prototypes confirmed, contracts frozen"), (S2, 1030, "independent review; a FAIL loops back"),
                     (S3, 990, "full check, regression gate, walkthrough")],
        "main_caption": "merged on your words",
        "always": "Always",
        "rules": "irreversible steps wait for you  ·  evidence on the real artifact  ·  every decision has a default  ·  one writer per file  ·  one heavy check at a time  ·  synthetic data only",
        "plate": "trio-workflow 0.4 · plate 01",
    },
    "zh": {
        "title": "trio 工作流",
        "subtitle": "把一个方案看作一段旅程。你做决定，一个 agent 审查，另一个 agent 执行；停点是三方交汇的地方。",
        "legend_lines": [("操作者", "你"), ("审查者", "agent A"), ("执行者", "agent B")],
        "legend_marks": ["动作", "停点", "批次 PR，带 CI（PR 模式）"],
        "operator": [(340, "定目标"), (560, "回答决定"), (1160, "提出问题"), (1780, "走查"), (2135, "授权")],
        "reviewer": [(340, "搭骨架"), (560, "拟方案"), (1160, "修改单"), (1780, "意见分类"), (2135, "复盘")],
        "builder": [(880, "派活"), (1470, "集成"), (1780, "截图对照"), (2135, "方案 PR")],
        "stops": [(S1, "停点 1", "契约"), (S2, "停点 2", "审查"), (S3, "停点 3", "最终")],
        "main": "main",
        "captions": [(S1, 990, "原型已确认，契约已冻结"), (S2, 1030, "独立审查；不通过就退回修复"), (S3, 990, "完整检查、回归门、走查")],
        "main_caption": "你说了才合并",
        "always": "始终",
        "rules": "不可逆的事等你说  ·  证据看真实产物  ·  每个决定都有默认值  ·  一个文件一个负责人  ·  重检查一次一个  ·  只用合成数据",
        "plate": "trio-workflow 0.4 · plate 01",
    },
}


class Plate:
    def __init__(self, lang, font_dir, cjk_font):
        self.t = TEXT[lang]
        latin = Path(font_dir)
        mono = FontProperties(fname=str(latin / "IBMPlexMono-Regular.ttf"))
        if lang == "zh":
            sans = FontProperties(fname=cjk_font)
            bold = FontProperties(fname=str(Path(cjk_font).with_name("Dengb.ttf")))
            title = bold
        else:
            sans = FontProperties(fname=str(latin / "InstrumentSans-Regular.ttf"))
            bold = FontProperties(fname=str(latin / "InstrumentSans-Bold.ttf"))
            title = FontProperties(fname=str(latin / "InstrumentSerif-Regular.ttf"))
        self.f = {"sans": sans, "bold": bold, "title": title, "mono": mono}
        self.fig = plt.figure(figsize=(W / 100, H / 100), facecolor=PAPER)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, W)
        self.ax.set_ylim(H, 0)
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self.labels = []

    def text(self, x, y, s, font, size, color=INK, ha="center", va="center", **kw):
        if font is self.f["mono"] and any(ord(ch) >= 0x2E80 for ch in s):
            font = self.f["sans"]
        artist = self.ax.text(x, y, s, fontproperties=font, fontsize=size, color=color, ha=ha, va=va, zorder=10, **kw)
        self.labels.append(artist)
        return artist

    def line(self, xs, ys, color, width=LINE_W, z=2):
        self.ax.plot(xs, ys, color=color, lw=width, solid_capstyle="round", solid_joinstyle="round", zorder=z)

    def station(self, x, y, color, hollow=False):
        self.ax.add_patch(Circle((x, y), 15, fc=PAPER if hollow else WHITE, ec=color, lw=3.5,
                                 ls=(0, (2, 1.5)) if hollow else "-", zorder=5))

    def interchange(self, x, filled=False, bottom=Y_B):
        self.ax.add_patch(FancyBboxPatch((x - 23, Y_O - 36), 46, bottom - Y_O + 72, boxstyle="round,pad=0,rounding_size=23",
                                         fc=INK if filled else WHITE, ec=INK, lw=3.5, zorder=6))

    def pr(self, x, y):
        self.ax.add_patch(Rectangle((x - 12, y - 12), 24, 24, fc=WHITE, ec=BUILDER, lw=2.5, zorder=5))

    def header(self):
        self.text(110, 140, self.t["title"], self.f["title"], 76, ha="left")
        self.text(112, 228, self.t["subtitle"], self.f["sans"], 15, color=MUTED, ha="left")
        x = 1420
        for (name, sub), color in zip(self.t["legend_lines"], (OPERATOR, REVIEWER, BUILDER)):
            self.line([x, x + 58], [130, 130], color)
            self.text(x + 76, 130, name, self.f["bold"], 12.5, ha="left")
            self.text(x + 76, 158, sub, self.f["sans"], 10.5, color=MUTED, ha="left")
            x += 270
        x = 1420
        marks = self.t["legend_marks"]
        self.station(x + 29, 214, MUTED)
        self.text(x + 76, 214, marks[0], self.f["sans"], 11.5, color=MUTED, ha="left")
        self.ax.add_patch(FancyBboxPatch((x + 270 + 8, 196), 42, 36, boxstyle="round,pad=0,rounding_size=18", fc=WHITE, ec=INK, lw=3, zorder=6))
        self.text(x + 270 + 76, 214, marks[1], self.f["sans"], 11.5, color=MUTED, ha="left")
        self.pr(x + 540 + 29, 214)
        self.text(x + 540 + 76, 214, marks[2], self.f["sans"], 11.5, color=MUTED, ha="left")

    def network(self):
        self.line([START, MAIN], [Y_O, Y_O], OPERATOR)
        self.line([START, MAIN], [Y_R, Y_R], REVIEWER)
        self.line([S1, MAIN], [Y_B, Y_B], BUILDER)
        for y in WORKER_Y:
            dy = y - Y_B
            self.line([BRANCH_FROM, BRANCH_FROM + dy, BRANCH_TO - dy, BRANCH_TO], [Y_B, y, y, Y_B], WORKER, width=5, z=1.5)
        for track, xs in zip(WORKER_Y, ((1070, 1300), (1120, 1250), (1160, 1215))):
            for x in xs:
                self.pr(x, track)
        loop = FancyArrowPatch((S2 - 26, Y_B + 44), (1470, Y_B + 22), connectionstyle="arc3,rad=-0.55", arrowstyle="-|>",
                               mutation_scale=16, lw=2, color=OPERATOR, linestyle=(0, (4, 3)), zorder=7)
        self.ax.add_patch(loop)

    def stations(self):
        for (x, name) in self.t["operator"]:
            self.station(x, Y_O, OPERATOR, hollow=(x == 1160))
            self.text(x, Y_O - 42, name, self.f["sans"], 13)
        for (x, name) in self.t["reviewer"]:
            self.station(x, Y_R, REVIEWER)
            self.text(x, Y_R - 42, name, self.f["sans"], 13)
        for (x, name) in self.t["builder"]:
            self.station(x, Y_B, BUILDER)
            self.text(x, Y_B - 42, name, self.f["sans"], 13)
        for x, tag, name in self.t["stops"]:
            self.interchange(x)
            self.text(x, Y_O - 104, tag, self.f["mono"], 11, color=MUTED)
            self.text(x, Y_O - 72, name, self.f["bold"], 16)
        self.interchange(MAIN, filled=True)
        self.text(MAIN, Y_O - 72, self.t["main"], self.f["bold"], 16)
        for x, y, caption in self.t["captions"]:
            self.text(x, y, caption, self.f["sans"], 12, color=MUTED)
        self.text(W - 80, 1030, self.t["main_caption"], self.f["sans"], 12, color=MUTED, ha="right")

    def footer(self):
        self.ax.plot([110, W - 80], [1095, 1095], color=HAIR, lw=1, zorder=1)
        self.text(110, 1142, self.t["always"], self.f["bold"], 13, ha="left")
        self.text(230, 1142, self.t["rules"], self.f["sans"], 12, color=MUTED, ha="left")
        self.text(W - 80, 1192, self.t["plate"], self.f["mono"], 9, color=MUTED, ha="right")

    def problems(self):
        self.fig.canvas.draw()
        renderer = self.fig.canvas.get_renderer()
        inverse = self.ax.transData.inverted()
        boxes = []
        for artist in self.labels:
            extent = artist.get_window_extent(renderer=renderer)
            (x0, ya), (x1, yb) = inverse.transform([[extent.x0, extent.y0], [extent.x1, extent.y1]])
            boxes.append((artist.get_text(), x0, min(ya, yb), x1, max(ya, yb)))
        found = [f"{name!r} leaves the canvas" for name, x0, y0, x1, y1 in boxes if x0 < 60 or x1 > W - 60 or y0 < 40 or y1 > H - 20]
        for i, (a, ax0, ay0, ax1, ay1) in enumerate(boxes):
            for b, bx0, by0, bx1, by1 in boxes[i + 1:]:
                if ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1:
                    found.append(f"{a!r} overlaps {b!r}")
        return found

    def draw(self):
        self.header()
        self.network()
        self.stations()
        self.footer()
        return self.problems()


def main(argv=None):
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lang", choices=sorted(TEXT), default="en")
    parser.add_argument("--out-dir", default=str(here))
    parser.add_argument("--font-dir", default=str(Path.home() / ".claude" / "skills" / "canvas-design" / "canvas-fonts"))
    parser.add_argument("--cjk-font", default="C:/Windows/Fonts/Deng.ttf")
    args = parser.parse_args(argv)
    plt.rcParams["pdf.fonttype"] = 42
    plate = Plate(args.lang, args.font_dir, args.cjk_font)
    problems = plate.draw()
    suffix = "" if args.lang == "en" else f"_{args.lang}"
    out = Path(args.out_dir)
    plate.fig.savefig(out / f"trio-workflow{suffix}.png", dpi=200, facecolor=PAPER)
    plate.fig.savefig(out / f"trio-workflow{suffix}.pdf", facecolor=PAPER)
    for problem in problems:
        print(f"LAYOUT {problem}")
    print(f"PLATE {args.lang} written to {out}; problems={len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
