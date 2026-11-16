#!/usr/bin/env python3
"""Draw the trio workflow plate (swimlane flowchart) as PNG and PDF.

Usage:
  python docs/workflow/draw_workflow.py [--lang en|zh] [--out-dir docs/workflow]

Needs matplotlib. Latin fonts come from the canvas-design skill folder and the
Chinese font from Windows DengXian; pass --font-dir / --cjk-font to override.
After drawing, every caption is measured against its card; any overflow is
printed and the script exits 1, so a layout regression cannot go unnoticed.
"""

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402

W, H = 2400, 1290
PAPER, CARD, INK, MUTED, HAIR = "#F4F1EA", "#FFFDF8", "#1C2230", "#6F6C66", "#DCD5C7"
STOP_BAND = "#EDE3D6"
ACCENT = "#C0532F"
LANE_ACCENT = ["#C0532F", "#33478A", "#2C7A6B", "#9C7C2E"]
LABEL_X0, CONTENT_X0, COL_W, CARD_W = 80, 290, 255, 225
PHASE_Y = 268
LANES_Y = [(320, 460), (490, 660), (690, 860), (890, 1010)]
FILES_Y = 1046
RULES_Y = 1150
STOP_COLS = (2, 4, 6)

TEXT = {
    "en": {
        "title": "trio workflow",
        "subtitle": "One plan, end to end. You decide, one agent reviews, another builds, and every state lives in files.",
        "plate": "plate 01 · trio-workflow 0.3",
        "stop": "stop",
        "phases": ["Bootstrap", "Plan", "Contract", "Build", "Review", "UI acceptance", "Final", "Merge"],
        "lanes": [("Operator", "you"), ("Reviewer", "agent A"), ("Builder", "agent B, lead"), ("Workers", "inner layer")],
        "nodes": {
            "O0": (0, 0, 1, "Set the goal", ["roles · phrases · data rules"]),
            "O1": (0, 1, 1, "Answer decisions", ["silence means the default"]),
            "O2": (0, 2, 1, "Confirm prototypes", ["before any code exists"]),
            "O3": (0, 3, 1, "Report problems", ["any time"]),
            "O4": (0, 4, 1, "Relay one line", ["a pointer, never content"]),
            "O5": (0, 5, 1, "Walk through", ["a prepared test copy"]),
            "O7": (0, 7, 1, "Authorize", ["\"merge and push\""]),
            "R0": (1, 0, 1, "Bootstrap", ["handoff folder · rules", "verification recipe"]),
            "R1": (1, 1, 1, "Draft the plan", ["You see · prototype · default", "owners · waves · check_plan"]),
            "R2": (1, 2, 1, "Review the contract", ["contracts · owners", "prototypes confirmed"]),
            "R3": (1, 3, 1, "Change requests", ["light path or REQUEST"]),
            "R4": (1, 4, 1, "Independent review", ["own checks · live · numbers", "verdict bound to a commit"]),
            "R5": (1, 5, 1, "Sort the findings", ["rule · template · test", "or a prototype choice"]),
            "R6": (1, 6, 1, "Final review", ["cross-family visual review", "regression gate"]),
            "R7": (1, 7, 1, "Merge and retro", ["fast-forward · restart", "lessons into checks"]),
            "B2": (2, 2, 1, "Opening checks", ["restate the goal", "baseline · environment"]),
            "B3": (2, 3, 1, "Kick off, integrate", ["playbook · owned files", "one unit first, then waves"]),
            "B4": (2, 4, 1, "Stop material", ["PASS · FAIL · NOT_RUN", "one line back to you"]),
            "B5": (2, 5, 1, "Screenshot matrix", ["pages × states vs main", "visual review, then fix"]),
            "B6": (2, 6, 1, "Final checks", ["full check under lock", "handoff doc committed"]),
            "W3": (3, 3, 2, "Inner layer: one batch, one worktree", ["pstack playbook or built-in rules", "returns commits, a short handoff and evidence"]),
        },
        "files_title": ("Files", "state lives here"),
        "files": ["00_FLOW · 0_RULES", "PLAN · MOCKUP", "DESIGN", "PROGRESS · HANDOFF", "REVIEW · RESULT", "sheet · WALKTHROUGH", "HANDOFF doc", "CLEANUP"],
        "rules_title": ("Always", "every step"),
        "rules": [("Authority", "irreversible steps wait for you"), ("Evidence", "seen on the real artifact"),
                  ("Defaults", "nobody blocks on you"), ("One writer", "per file and branch"),
                  ("One heavy check", "at a time per machine"), ("Synthetic data", "client data stays local")],
        "legend": ["hand-over", "exchange through files", "fix loop"],
    },
    "zh": {
        "title": "trio 工作流",
        "subtitle": "一个方案，从头到尾。你做决定，一个 agent 审查，另一个 agent 执行，所有状态都写在文件里。",
        "plate": "plate 01 · trio-workflow 0.3",
        "stop": "停点",
        "phases": ["搭骨架", "拟方案", "契约", "执行", "审查", "界面验收", "最终", "合并"],
        "lanes": [("操作者", "你"), ("审查者", "agent A"), ("执行者", "agent B · 主 agent"), ("子 agent", "内层")],
        "nodes": {
            "O0": (0, 0, 1, "定目标", ["角色 · 口令 · 数据规矩"]),
            "O1": (0, 1, 1, "回答决定", ["不回答就按默认"]),
            "O2": (0, 2, 1, "确认原型", ["写代码之前"]),
            "O3": (0, 3, 1, "提出问题", ["随时"]),
            "O4": (0, 4, 1, "转一句话", ["只转路径，不转内容"]),
            "O5": (0, 5, 1, "走查", ["预置好的测试副本"]),
            "O7": (0, 7, 1, "授权", ["“合并并推送”"]),
            "R0": (1, 0, 1, "搭骨架", ["交接目录 · 规则", "验证配方"]),
            "R1": (1, 1, 1, "拟方案", ["你会看到 · 原型 · 默认值", "归属表 · 波次 · 检查"]),
            "R2": (1, 2, 1, "审契约", ["契约 · 文件归属", "原型已确认"]),
            "R3": (1, 3, 1, "修改单", ["小改通道或修改单"]),
            "R4": (1, 4, 1, "独立审查", ["自己检查 · 实测 · 核数", "结论绑定提交号"]),
            "R5": (1, 5, 1, "意见分类", ["规则 · 模板 · 测试", "或交你选原型"]),
            "R6": (1, 6, 1, "最终审查", ["跨家族看图审查", "回归门"]),
            "R7": (1, 7, 1, "合并与复盘", ["只快进 · 重启服务", "教训变成检查"]),
            "B2": (2, 2, 1, "开工核对", ["复述目标", "基线 · 环境"]),
            "B3": (2, 3, 1, "派活与集成", ["剧本 · 独占文件", "先跑通一批，再按波次"]),
            "B4": (2, 4, 1, "停点材料", ["PASS · FAIL · NOT_RUN", "只回你一句话"]),
            "B5": (2, 5, 1, "截图对照表", ["页面 × 状态，对比 main", "先看图审查，再修"]),
            "B6": (2, 6, 1, "最终检查", ["完整检查（加锁）", "交接文档入库"]),
            "W3": (3, 3, 2, "内层：一个批次，一个工作树", ["pstack 剧本，或内置规则", "交回提交、简短交接和证据"]),
        },
        "files_title": ("文件", "状态都在这里"),
        "files": ["00_FLOW · 0_RULES", "PLAN · MOCKUP", "DESIGN", "PROGRESS · HANDOFF", "REVIEW · RESULT", "sheet · WALKTHROUGH", "HANDOFF doc", "CLEANUP"],
        "rules_title": ("始终", "每一步都守"),
        "rules": [("授权", "不可逆的事等你说"), ("证据", "在真实产物上看到"), ("默认值", "谁都不因等你停下"),
                  ("一个负责人", "每个文件、每个分支"), ("重检查", "一台机器同时一个"), ("合成数据", "客户数据不出本机")],
        "legend": ["交接", "经文件往返", "修复回路"],
    },
}


def col_x(col):
    return CONTENT_X0 + col * COL_W


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
        self.ax.axis("off")
        self.checks = []
        self.cards = {}

    def text(self, x, y, s, font, size, color=INK, ha="left", va="center", bound=None, **kw):
        if font is self.f["mono"] and any(ord(ch) >= 0x2E80 for ch in s):
            font = self.f["sans"]  # the monospace face has no CJK glyphs
        artist = self.ax.text(x, y, s, fontproperties=font, fontsize=size, color=color, ha=ha, va=va, **kw)
        self.checks.append((artist, bound or (40, 40, W - 40, H - 40)))
        return artist

    def arrow(self, a, b, color=INK, both=False, dashed=False, rad=0.0):
        patch = FancyArrowPatch(a, b, arrowstyle="<|-|>" if both else "-|>", mutation_scale=16, lw=1.4, color=color,
                                linestyle=(0, (5, 4)) if dashed else "-", connectionstyle=f"arc3,rad={rad}",
                                shrinkA=0, shrinkB=0, joinstyle="miter", capstyle="butt")
        self.ax.add_patch(patch)

    def polyline(self, points, color=INK):
        xs, ys = zip(*points[:-1])
        self.ax.plot(xs, ys, color=color, lw=1.4, solid_joinstyle="round")
        self.arrow(points[-2], points[-1], color=color)

    def header(self):
        self.text(LABEL_X0, 118, self.t["title"], self.f["title"], 54)
        self.text(LABEL_X0, 188, self.t["subtitle"], self.f["sans"], 14, color=MUTED)
        self.text(W - 80, 96, self.t["plate"], self.f["mono"], 9, color=MUTED, ha="right")
        x = W - 80 - 3 * 300 + 40
        for (label, style) in zip(self.t["legend"], (dict(), dict(both=True), dict(color=ACCENT, dashed=True))):
            self.arrow((x, 150), (x + 64, 150), **style)
            self.text(x + 78, 150, label, self.f["sans"], 11, color=MUTED, bound=(x + 70, 130, x + 290, 170))
            x += 300

    def stop_bands(self):
        for col in STOP_COLS:
            x0 = col_x(col) - 10
            self.ax.add_patch(FancyBboxPatch((x0, PHASE_Y - 34), COL_W - 10, LANES_Y[-1][1] - PHASE_Y + 50,
                                             boxstyle="round,pad=0,rounding_size=14", fc=STOP_BAND, ec="none", zorder=0))

    def phases(self):
        for col, name in enumerate(self.t["phases"]):
            x = col_x(col) + 4
            bound = (x - 6, PHASE_Y - 30, x + CARD_W + 6, PHASE_Y + 30)
            self.text(x, PHASE_Y, f"{col:02d}", self.f["mono"], 10, color=MUTED, bound=bound)
            self.text(x + 40, PHASE_Y, name, self.f["bold"], 14, bound=bound)
            if col in STOP_COLS:
                self.ax.add_patch(FancyBboxPatch((x + CARD_W - 74, PHASE_Y - 13), 70, 26, boxstyle="round,pad=0,rounding_size=13",
                                                 fc=ACCENT, ec="none"))
                self.text(x + CARD_W - 39, PHASE_Y, self.t["stop"], self.f["bold"], 10, color=CARD, ha="center", bound=bound)

    def lanes(self):
        for i, ((y0, y1), (name, sub)) in enumerate(zip(LANES_Y, self.t["lanes"])):
            self.ax.add_patch(Rectangle((LABEL_X0, y0 + 8), 5, y1 - y0 - 16, color=LANE_ACCENT[i], lw=0))
            bound = (LABEL_X0, y0, CONTENT_X0 - 20, y1)
            self.text(LABEL_X0 + 22, (y0 + y1) / 2 - 14, name, self.f["bold"], 15, color=LANE_ACCENT[i], bound=bound)
            self.text(LABEL_X0 + 22, (y0 + y1) / 2 + 16, sub, self.f["sans"], 10.5, color=MUTED, bound=bound)
            if i < len(LANES_Y) - 1:
                y = (y1 + LANES_Y[i + 1][0]) / 2
                self.ax.plot([LABEL_X0, col_x(8) - 30], [y, y], color=HAIR, lw=0.8, zorder=0.5)

    def card(self, key):
        lane, col, span, title, lines = self.t["nodes"][key]
        y0, y1 = LANES_Y[lane]
        height = 54 + 26 * len(lines)
        cy0 = (y0 + y1) / 2 - height / 2
        x0 = col_x(col)
        x1 = x0 + CARD_W + (span - 1) * COL_W
        accent = LANE_ACCENT[lane]
        ghost = key == "O3"
        self.ax.add_patch(FancyBboxPatch((x0, cy0), x1 - x0, height, boxstyle="round,pad=0,rounding_size=10",
                                         fc=PAPER if ghost else CARD, ec=accent if ghost else HAIR, lw=1.1,
                                         ls=(0, (4, 3)) if ghost else "-", zorder=2))
        if not ghost:
            self.ax.add_patch(Rectangle((x0 + 1, cy0 + 12), 4, height - 24, color=accent, lw=0, zorder=3))
        bound = (x0 + 10, cy0 + 4, x1 - 8, cy0 + height - 4)
        self.text(x0 + 20, cy0 + 30, title, self.f["bold"], 13.5, color=accent if ghost else INK, bound=bound, zorder=4)
        for i, line in enumerate(lines):
            self.text(x0 + 20, cy0 + 60 + 26 * i, line, self.f["sans"], 11, color=MUTED, bound=bound, zorder=4)
        self.cards[key] = (x0, cy0, x1, cy0 + height)

    def anchor(self, key, side, shift=0.0):
        x0, y0, x1, y1 = self.cards[key]
        cx, cy = (x0 + x1) / 2 + shift, (y0 + y1) / 2
        return {"top": (cx, y0 - 6), "bottom": (cx, y1 + 6), "left": (x0 - 6, cy), "right": (x1 + 6, cy)}[side]

    def flows(self):
        a, link = self.anchor, self.arrow
        link(a("O0", "bottom"), a("R0", "top"))
        link(a("R0", "right"), a("R1", "left"))
        link(a("O1", "bottom"), a("R1", "top"), both=True)
        link(a("R1", "right"), a("R2", "left"))
        link(a("O2", "bottom"), a("R2", "top"), both=True)
        link(a("R2", "bottom"), a("B2", "top"), both=True)
        link(a("B2", "right"), a("B3", "left"))
        link(a("O3", "bottom"), a("R3", "top"))
        link(a("R3", "bottom"), a("B3", "top"))
        b3 = self.cards["B3"]
        w3 = self.cards["W3"]
        mid = (b3[0] + b3[2]) / 2
        link((mid, b3[3] + 6), (mid, w3[1] - 6), both=True)
        link(a("B3", "right"), a("B4", "left"))
        link(a("B4", "top"), a("R4", "bottom"), both=True)
        link(a("O4", "bottom"), a("R4", "top"), both=True)
        r4 = self.cards["R4"]
        link((r4[0] + 30, r4[3] + 6), (b3[2] - 30, b3[1] - 6), color=ACCENT, dashed=True, rad=0.25)
        link(a("B4", "right"), a("B5", "left"))
        b5, o5 = self.cards["B5"], self.cards["O5"]
        gap_x = col_x(6) - (COL_W - CARD_W) / 2  # the middle of the gutter between columns 05 and 06
        self.polyline([(b5[2] + 6, (b5[1] + b5[3]) / 2), (gap_x, (b5[1] + b5[3]) / 2), (gap_x, (o5[1] + o5[3]) / 2), (o5[2] + 6, (o5[1] + o5[3]) / 2)])
        link(a("O5", "bottom"), a("R5", "top"))
        link(a("R5", "bottom"), a("B5", "top"), color=ACCENT, dashed=True)
        link(a("B5", "right"), a("B6", "left"))
        link(a("B6", "top"), a("R6", "bottom"), both=True)
        link(a("R6", "right"), a("R7", "left"))
        link(a("O7", "bottom"), a("R7", "top"))

    def footer(self):
        for y, (name, sub) in ((FILES_Y, self.t["files_title"]), (RULES_Y, self.t["rules_title"])):
            bound = (LABEL_X0, y - 30, CONTENT_X0 - 20, y + 60)
            self.text(LABEL_X0 + 22, y, name, self.f["bold"], 15, bound=bound)
            self.text(LABEL_X0 + 22, y + 30, sub, self.f["sans"], 10.5, color=MUTED, bound=bound)
        self.ax.plot([CONTENT_X0, col_x(8) - 30], [FILES_Y - 26, FILES_Y - 26], color=HAIR, lw=0.8)
        for col, label in enumerate(self.t["files"]):
            x = col_x(col) + 4
            self.text(x, FILES_Y, label, self.f["mono"], 10, color=INK, bound=(x - 4, FILES_Y - 20, x + CARD_W, FILES_Y + 20))
        tile_w = (8 * COL_W - 30) / 6
        self.ax.plot([CONTENT_X0, col_x(8) - 30], [RULES_Y - 26, RULES_Y - 26], color=HAIR, lw=0.8)
        for i, (title, line) in enumerate(self.t["rules"]):
            x0 = CONTENT_X0 + 4 + i * tile_w
            bound = (x0 - 4, RULES_Y - 20, x0 + tile_w - 12, RULES_Y + 50)
            self.text(x0, RULES_Y, title, self.f["bold"], 12.5, color=ACCENT if i == 0 else INK, bound=bound)
            self.text(x0, RULES_Y + 30, line, self.f["sans"], 11, color=MUTED, bound=bound)

    def overflow(self):
        self.fig.canvas.draw()
        renderer = self.fig.canvas.get_renderer()
        inverse = self.ax.transData.inverted()
        problems = []
        for artist, (bx0, by0, bx1, by1) in self.checks:
            extent = artist.get_window_extent(renderer=renderer)
            (x0, ya), (x1, yb) = inverse.transform([[extent.x0, extent.y0], [extent.x1, extent.y1]])
            top, bottom = min(ya, yb), max(ya, yb)
            if x0 < bx0 - 0.5 or x1 > bx1 + 0.5 or top < by0 - 0.5 or bottom > by1 + 0.5:
                problems.append(f"{artist.get_text()!r} spans x {x0:.0f}-{x1:.0f}, y {top:.0f}-{bottom:.0f}; bound x {bx0:.0f}-{bx1:.0f}, y {by0:.0f}-{by1:.0f}")
        return problems

    def draw(self):
        self.ax.add_patch(Rectangle((40, 40), W - 80, H - 80, fill=False, lw=0.8, ec=INK))
        self.header()
        self.stop_bands()
        self.phases()
        self.lanes()
        for key in self.t["nodes"]:
            self.card(key)
        self.flows()
        self.footer()
        return self.overflow()


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
        print(f"OVERFLOW {problem}")
    print(f"PLATE {args.lang} written to {out}; overflow={len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
