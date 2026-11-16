#!/usr/bin/env python3
"""Draw the trio workflow plate (swimlane flowchart) as PNG and PDF.

Usage:
  python docs/workflow/draw_workflow.py [--lang en|zh] [--out-dir docs/workflow]

Needs matplotlib. Fonts come from the canvas-design skill folder (Latin) and the
Windows DengXian font (Chinese); pass --font-dir / --cjk-font to override.
After drawing, every caption is measured against its cell; any overflow is
printed and the script exits 1, so a layout regression cannot go unnoticed.
"""

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

W, H = 2400, 1600
PAPER, INK, MUTED, HAIR = "#F3EFE6", "#1D2330", "#6B6A66", "#D8D1C3"
ACCENT = "#B5462A"
LANE_COLORS = [("#B5462A", "#F6E7DF"), ("#2F3E73", "#E6E8F1"), ("#2B6B60", "#E2EFEB"), ("#9A7A35", "#F2ECDD")]
LABEL_X0, CONTENT_X0, COL_W, BOX_W = 80, 270, 256, 232
LANES_Y = [(265, 455), (485, 770), (800, 1040), (1070, 1270)]
PAD = 12

TEXT = {
    "en": {
        "title": "trio workflow",
        "subtitle": "One plan, end to end.  Outer layer: plans, stops, verdicts, merges.  Inner layer: how one batch is built.",
        "plate": "plate 01  ·  trio-workflow 0.3.0  ·  2026-11",
        "phases": ["Bootstrap", "Plan", "Stop 1 · contract", "Build in batches", "Stop review", "UI acceptance", "Final stop", "Merge & retro"],
        "lanes": [("Operator", "you · decisions"), ("Reviewer", "plans · verdicts"), ("Builder", "lead · integration"), ("Workers", "inner layer · ×3")],
        "nodes": {
            "O0": (0, 0, 1, "Set the goal", ["roles and tools", "authorization phrases", "where client data lives"]),
            "O1": (0, 1, 1, "Answer decisions", ["each has a default", "silence = the default"]),
            "O2": (0, 2, 1, "Confirm prototypes", ["confirm or pick a variant", "before any code exists"]),
            "O3": (0, 3, 1, "Problems you notice", ["raise them any time"]),
            "O4": (0, 4, 1, "Relay one line", ["\"review plan 3 stop 2\"", "\"result at …RESULT.md\"", "a pointer, never content"]),
            "O5": (0, 5, 1, "Walk through", ["mid-plan and before final", "prepared projects", "results already computed"]),
            "O7": (0, 7, 1, "Authorize", ["\"merge and push\"", "\"clean up\"", "nothing lands without it"]),
            "R0": (1, 0, 1, "Bootstrap", ["handoff directory", "00_FLOW · 0_RULES", "verification recipe", "role table · inner layer"]),
            "R1": (1, 1, 1, "Draft the plan", ["read code, run probes", "prototype every UI item", "IDs · type · You see", "unit · live · perf · gate", "ownership table · waves", "check_plan.py → ok"]),
            "R2": (1, 2, 1, "Stop 1 review", ["contracts match the code", "one owner per hotspot", "prototypes confirmed", "quick check only"]),
            "R3": (1, 3, 1, "Change requests", ["find the cause in code", "display only → light path", "else REQUEST + supplement"]),
            "R4": (1, 4, 1, "Stop review", ["own full check, under lock", "live checks on a copy", "numbers cross-checked", "adversarial pass", "PASS · PASS+NOTES · FAIL", "bound to one sha"]),
            "R5": (1, 5, 1, "Classify findings", ["convention → rule + check", "spec gap → template", "bug → failing test", "taste → prototype choice"]),
            "R6": (1, 6, 1, "Final review", ["cross-family visual review", "regression gate", "handoff doc read"]),
            "R7": (1, 7, 1, "Merge and retro", ["patch-id still matches", "ff-only · ls-remote", "restart the service", "lessons → structure"]),
            "B2": (2, 2, 1, "Opening checks", ["restate the goal", "baseline · environment", "stop-1 material"]),
            "B3": (2, 3, 1, "Kick off, integrate", ["goal · IDs · type → playbook", "owned files · forbidden acts", "evidence to produce", "one unit first, then waves", "ownership check on return", "verifier is not the author"]),
            "B4": (2, 4, 1, "Stop material", ["PASS · FAIL · NOT_RUN", "decisions with defaults", "one line: reached stop N"]),
            "B5": (2, 5, 1, "Screenshot matrix", ["pages × states, beside main", "screenshot_sheet.py", "visual review → fix", "prepared walkthrough"]),
            "B6": (2, 6, 1, "Final stop", ["full check, under lock", "regression gate", "handoff doc committed"]),
            "W3": (3, 3, 2, "Inner layer: one batch, one worktree", [
                "pstack playbook, or built-in rules when pstack is absent",
                "restate · data shape first · smallest change · test behavior",
                "drive the real surface · small commits · log every decision",
                "returns commits · a 30-line handoff · evidence · requests",
                "stall → retry by cause; twice → drop the unit and replan"]),
        },
        "files": ("Files", "state lives here"),
        "writers": ("R", "B"),
        "always": ("Always", "every branch"),
        "rules": [("Authority", "irreversible acts wait for your words"), ("Evidence", "observed on the real artifact"),
                  ("Defaults", "never block on the operator"), ("One writer", "per file and per branch"),
                  ("Heavy-check lock", "one at a time per machine"), ("Synthetic data", "client data stays local")],
        "legend": ["hand-over", "exchange through files", "fix loop: FAIL → fix → re-review by ID", "writer: R reviewer · B builder"],
    },
    "zh": {
        "title": "trio 工作流",
        "subtitle": "一个方案，从头到尾。外层：方案、停点、结论、合并。内层：一个批次怎么写出来。",
        "plate": "plate 01  ·  trio-workflow 0.3.0  ·  2026-11",
        "phases": ["搭骨架", "拟方案", "停点 1 · 契约", "分批执行", "停点审查", "界面验收", "最终停点", "合并与复盘"],
        "lanes": [("操作者", "你 · 目标 · 决定"), ("审查者", "方案 · 结论"), ("执行者", "主 agent · 集成"), ("子 agent", "内层 · ×3")],
        "nodes": {
            "O0": (0, 0, 1, "定目标", ["角色和工具", "授权口令", "客户数据放在哪"]),
            "O1": (0, 1, 1, "回答决定", ["每项都带默认值", "不回答 = 按默认"]),
            "O2": (0, 2, 1, "确认原型", ["确认，或选一个变体", "都在写代码之前"]),
            "O3": (0, 3, 1, "你发现的问题", ["随时提出"]),
            "O4": (0, 4, 1, "转一句话", ["“审查方案三停点2”", "“审查结果见 …”", "只转路径，不转内容"]),
            "O5": (0, 5, 1, "走查", ["中途一次，最终前一次", "预置好的项目", "结果已经算好"]),
            "O7": (0, 7, 1, "授权", ["“合并并推送”", "“做收尾”", "没有它什么都不合并"]),
            "R0": (1, 0, 1, "搭骨架", ["交接目录", "00_FLOW · 0_RULES", "验证配方", "角色表 · 内层"]),
            "R1": (1, 1, 1, "拟方案", ["先读代码、做探针", "界面条目先出原型", "编号 · 类型 · 你会看到", "单元 · 实操 · 性能 · 走查", "归属表 · 波次", "check_plan.py 通过"]),
            "R2": (1, 2, 1, "停点 1 审查", ["契约与代码相符", "热点文件只一个负责", "原型已确认", "只跑快检"]),
            "R3": (1, 3, 1, "修改单", ["在代码里找原因", "只改显示 → 小改通道", "否则写修改单"]),
            "R4": (1, 4, 1, "停点审查", ["自己跑完整检查（加锁）", "在合成副本上实测", "数字换一条路核对", "对抗式审查", "PASS · PASS+NOTES · FAIL", "绑定一个提交号"]),
            "R5": (1, 5, 1, "走查意见分类", ["违反约定 → 规则 + 检查", "规格缺口 → 改模板", "bug → 先写失败测试", "品味 → 交你选原型"]),
            "R6": (1, 6, 1, "最终审查", ["跨家族看图审查", "回归门", "读交接文档"]),
            "R7": (1, 7, 1, "合并与复盘", ["patch-id 仍一致", "只快进 · ls-remote 确认", "重启常驻服务", "教训 → 结构"]),
            "B2": (2, 2, 1, "开工核对", ["复述目标", "基线 · 环境", "停点 1 材料"]),
            "B3": (2, 3, 1, "派活与集成", ["目标 · 编号 · 类型 → 剧本", "独占文件 · 禁止的操作", "要交的证据", "先跑通一批，再按波次", "回收时查文件归属", "验证者 ≠ 作者 · 读 diff"]),
            "B4": (2, 4, 1, "停点材料", ["PASS · FAIL · NOT_RUN", "待决事项带默认值", "只回一句：已到停点 N"]),
            "B5": (2, 5, 1, "截图对照表", ["页面 × 状态，与 main 并排", "screenshot_sheet.py", "看图审查 → 修复", "预置走查服务"]),
            "B6": (2, 6, 1, "最终停点", ["完整检查（加锁）", "回归门", "交接文档入库"]),
            "W3": (3, 3, 2, "内层：一个批次，一个工作树", [
                "pstack 剧本；没装 pstack 时用内置规则",
                "复述 · 先定数据结构 · 最小改动 · 测行为",
                "实际操作页面 · 小步提交 · 每个决定都记录",
                "交回：提交 · ≤30 行交接 · 证据 · 改他人文件的请求",
                "卡住 → 按原因重试；两次不成 → 放弃该单元并重排"]),
        },
        "files": ("文件", "状态都在这里"),
        "writers": ("审", "执"),
        "always": ("始终", "每个分支都守"),
        "rules": [("授权", "不可逆操作等你的原话"), ("证据", "在真实产物上看到"), ("默认值", "不因等你而停下"),
                  ("一个负责人", "每个文件、每个分支"), ("重检查锁", "一台机器同时只跑一个"), ("合成数据", "客户数据不出本机")],
        "legend": ["交接", "经文件往返", "修复回路：不通过 → 修复 → 按编号复审", "写入者：审 = 审查者 · 执 = 执行者"],
    },
}

FILES = [
    [("00_FLOW", 0), ("0_RULES", 0), ("PROMPTS", 0)],
    [("PLAN_<n>", 0), ("*_MOCKUP.html", 0)],
    [("DESIGN_*", 1), ("DESIGN_*_REVIEW", 0)],
    [("PROGRESS", 1), ("HANDOFF", 1), ("DECISIONS.tsv", 1)],
    [("REVIEW_stopN", 1), ("…_RESULT", 0)],
    [("index.html", 1), ("WALKTHROUGH", 0)],
    [("*_HANDOFF_CN.md", 1), ("regression log", 1)],
    [("CLEANUP_<date>", 0)],
]


def col_x(col):
    return CONTENT_X0 + col * COL_W + 8


class Plate:
    def __init__(self, lang, font_dir, cjk_font):
        self.lang = lang
        self.t = TEXT[lang]
        latin = Path(font_dir)
        if lang == "zh":
            sans = FontProperties(fname=cjk_font)
            bold = FontProperties(fname=str(Path(cjk_font).with_name("Dengb.ttf")))
            serif = bold
        else:
            sans = FontProperties(fname=str(latin / "InstrumentSans-Regular.ttf"))
            bold = FontProperties(fname=str(latin / "InstrumentSans-Bold.ttf"))
            serif = FontProperties(fname=str(latin / "InstrumentSerif-Regular.ttf"))
        self.f = {"sans": sans, "bold": bold, "serif": serif,
                  "mono": FontProperties(fname=str(latin / "IBMPlexMono-Regular.ttf"))}
        self.fig = plt.figure(figsize=(W / 100, H / 100), facecolor=PAPER)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, W)
        self.ax.set_ylim(H, 0)
        self.ax.axis("off")
        self.checks = []  # (text artist, (x0, y0, x1, y1)) captions that must stay inside a cell
        self.boxes = {}

    def text(self, x, y, s, font, size, color=INK, ha="left", va="center", bound=None, **kw):
        if font is self.f["mono"] and any(ord(ch) >= 0x2E80 for ch in s):
            font = self.f["sans"]  # the monospace face has no CJK glyphs
        artist = self.ax.text(x, y, s, fontproperties=font, fontsize=size, color=color, ha=ha, va=va, **kw)
        self.checks.append((artist, bound or (40, 40, W - 40, H - 40)))
        return artist

    def frame(self):
        self.ax.add_patch(Rectangle((40, 40), W - 80, H - 80, fill=False, lw=0.6, ec=INK))
        self.ax.add_patch(Rectangle((48, 48), W - 96, H - 96, fill=False, lw=0.3, ec=HAIR))
        self.text(LABEL_X0, 112, self.t["title"], self.f["serif"], 46)
        self.text(LABEL_X0, 172, self.t["subtitle"], self.f["sans"], 13, color=MUTED)
        self.text(W - 80, 100, self.t["plate"], self.f["mono"], 9, color=MUTED, ha="right")
        for x in range(CONTENT_X0, CONTENT_X0 + 8 * COL_W + 1, 32):
            tall = (x - CONTENT_X0) % COL_W == 0
            self.ax.plot([x, x], [252 - (10 if tall else 4), 252], color=INK if tall else HAIR, lw=0.6 if tall else 0.5)
        self.ax.plot([CONTENT_X0, CONTENT_X0 + 8 * COL_W], [252, 252], color=INK, lw=0.6)
        for col, name in enumerate(self.t["phases"]):
            x = col_x(col)
            self.text(x, 214, f"{col:02d}", self.f["mono"], 9, color=ACCENT)
            self.text(x + 34, 214, name, self.f["bold"], 11.5, bound=(x, 195, x + BOX_W, 245))

    def lanes(self):
        for i, ((y0, y1), (name, sub)) in enumerate(zip(LANES_Y, self.t["lanes"])):
            stroke, _ = LANE_COLORS[i]
            self.ax.add_patch(Rectangle((LABEL_X0, y0), 6, y1 - y0, color=stroke, lw=0))
            self.text(LABEL_X0 + 20, y0 + 26, name, self.f["bold"], 13, bound=(LABEL_X0, y0, CONTENT_X0 - 10, y1))
            self.text(LABEL_X0 + 20, y0 + 52, sub, self.f["mono"], 8.5, color=MUTED, bound=(LABEL_X0, y0, CONTENT_X0 - 10, y1))
            self.ax.plot([LABEL_X0, CONTENT_X0 + 8 * COL_W], [y1 + 15, y1 + 15], color=HAIR, lw=0.4, ls=(0, (1, 3)))
            for col in range(9):
                x = CONTENT_X0 + col * COL_W - 4
                for y in (y0 - 15, y1 + 15):
                    self.ax.plot([x - 5, x + 5], [y, y], color=HAIR, lw=0.6)
                    self.ax.plot([x, x], [y - 5, y + 5], color=HAIR, lw=0.6)

    def node(self, key):
        lane, col, span, title, lines = self.t["nodes"][key]
        y0, y1 = LANES_Y[lane]
        x0 = col_x(col)
        x1 = x0 + BOX_W + (span - 1) * COL_W
        by0, by1 = y0 + PAD, y1 - PAD
        stroke, wash = LANE_COLORS[lane]
        ghost = key == "O3"
        self.ax.add_patch(FancyBboxPatch((x0, by0), x1 - x0, by1 - by0, boxstyle="round,pad=0,rounding_size=6",
                                         fc=PAPER if ghost else wash, ec=stroke, lw=0.6 if ghost else 0.9,
                                         ls=(0, (3, 3)) if ghost else "-"))
        bound = (x0 + 8, by0 + 4, x1 - 8, by1 - 4)
        self.text(x1 - 12, by0 + 18, f"{key[0]}·{col:02d}", self.f["mono"], 7.5, color=stroke, ha="right", bound=bound)
        self.text(x0 + 16, by0 + 26, title, self.f["bold"], 12, bound=bound)
        for i, line in enumerate(lines):
            self.text(x0 + 16, by0 + 58 + i * 25, line, self.f["sans"], 10, color=INK if not ghost else MUTED, bound=bound)
        self.boxes[key] = (x0, by0, x1, by1)

    def arrow(self, points, color=INK, both=False, dashed=False):
        style = "<|-|>" if both else "-|>"
        ls = (0, (4, 3)) if dashed else "-"
        for (xa, ya), (xb, yb) in zip(points[:-2], points[1:-1]):
            self.ax.plot([xa, xb], [ya, yb], color=color, lw=0.9, ls=ls, solid_capstyle="butt")
        start = points[-2] if len(points) > 2 else points[0]
        if len(points) > 2 and both:
            style = "-|>"
            self.ax.annotate("", xy=points[0], xytext=points[1],
                             arrowprops=dict(arrowstyle="-|>", color=color, lw=0.9, shrinkA=0, shrinkB=0, mutation_scale=11, ls=ls))
        self.ax.annotate("", xy=points[-1], xytext=start,
                         arrowprops=dict(arrowstyle=style, color=color, lw=0.9, shrinkA=0, shrinkB=0, mutation_scale=11, ls=ls))

    def edge(self, a, side_a, b, side_b, **kw):
        def anchor(key, side):
            x0, y0, x1, y1 = self.boxes[key]
            return {"top": ((x0 + x1) / 2, y0 - 4), "bottom": ((x0 + x1) / 2, y1 + 4),
                    "left": (x0 - 4, (y0 + y1) / 2), "right": (x1 + 4, (y0 + y1) / 2)}[side]
        self.arrow([anchor(a, side_a), anchor(b, side_b)], **kw)

    def flows(self):
        e = self.edge
        e("O0", "bottom", "R0", "top")
        e("R0", "right", "R1", "left")
        e("O1", "bottom", "R1", "top", both=True)
        e("R1", "right", "R2", "left")
        e("O2", "bottom", "R2", "top", both=True)
        e("B2", "top", "R2", "bottom", both=True)
        e("B2", "right", "B3", "left")
        e("O3", "bottom", "R3", "top")
        e("R3", "bottom", "B3", "top")
        b3, w3 = self.boxes["B3"], self.boxes["W3"]
        mid = (b3[0] + b3[2]) / 2
        self.arrow([(mid, b3[3] + 4), (mid, w3[1] - 4)], both=True)
        e("B3", "right", "B4", "left")
        e("B4", "top", "R4", "bottom", both=True)
        e("O4", "bottom", "R4", "top", both=True)
        r4, b3 = self.boxes["R4"], self.boxes["B3"]
        self.arrow([(r4[0] + 30, r4[3] + 3), (b3[2] - 30, b3[1] - 3)], color=ACCENT, dashed=True)
        e("B4", "right", "B5", "left")
        b5, o5 = self.boxes["B5"], self.boxes["O5"]
        gap_x = b5[2] + 12
        self.arrow([(b5[2] + 4, b5[1] + 30), (gap_x, b5[1] + 30), (gap_x, o5[3] - 30), (o5[2] + 4, o5[3] - 30)])
        e("O5", "bottom", "R5", "top")
        e("R5", "bottom", "B5", "top", color=ACCENT, dashed=True)
        e("B5", "right", "B6", "left")
        e("B6", "top", "R6", "bottom", both=True)
        e("R6", "right", "R7", "left")
        e("O7", "bottom", "R7", "top")

    def files(self):
        y0, y1 = 1290, 1395
        name, sub = self.t["files"]
        self.ax.add_patch(Rectangle((LABEL_X0, y0), 6, y1 - y0, color=INK, lw=0))
        self.text(LABEL_X0 + 20, y0 + 22, name, self.f["bold"], 13, bound=(LABEL_X0, y0, CONTENT_X0 - 10, y1))
        self.text(LABEL_X0 + 20, y0 + 48, sub, self.f["mono"], 8.5, color=MUTED, bound=(LABEL_X0, y0, CONTENT_X0 - 10, y1))
        for col, chips in enumerate(FILES):
            x0 = col_x(col)
            for i, (label, writer) in enumerate(chips):
                cy = y0 + 4 + i * 34
                stroke = LANE_COLORS[1 + writer][0]
                self.ax.add_patch(FancyBboxPatch((x0, cy), BOX_W, 26, boxstyle="round,pad=0,rounding_size=4", fc=PAPER, ec=stroke, lw=0.6))
                bound = (x0 + 2, cy, x0 + BOX_W - 2, cy + 26)
                self.text(x0 + 12, cy + 13, self.t["writers"][writer], self.f["bold"], 8.5, color=stroke, bound=bound)
                self.text(x0 + 34, cy + 13, label, self.f["mono"], 8.5, bound=bound)

    def footer(self):
        y0, y1 = 1418, 1500
        name, sub = self.t["always"]
        self.ax.add_patch(Rectangle((LABEL_X0, y0), 6, y1 - y0, color=ACCENT, lw=0))
        self.text(LABEL_X0 + 20, y0 + 22, name, self.f["bold"], 13, bound=(LABEL_X0, y0, CONTENT_X0 - 10, y1))
        self.text(LABEL_X0 + 20, y0 + 48, sub, self.f["mono"], 8.5, color=MUTED, bound=(LABEL_X0, y0, CONTENT_X0 - 10, y1))
        tile_w = (8 * COL_W - 8) / 6
        for i, (title, line) in enumerate(self.t["rules"]):
            x0 = CONTENT_X0 + 8 + i * tile_w
            x1 = x0 + tile_w - 16
            self.ax.plot([x0, x1], [y0, y0], color=INK, lw=0.6)
            bound = (x0, y0, x1, y1)
            self.text(x0, y0 + 24, title, self.f["bold"], 11, bound=bound)
            self.text(x0, y0 + 52, line, self.f["sans"], 9.5, color=MUTED, bound=bound)
        ly = 1535
        x = CONTENT_X0 + 8
        samples = [dict(), dict(both=True), dict(color=ACCENT, dashed=True)]
        for label, sample in zip(self.t["legend"][:3], samples):
            self.arrow([(x, ly), (x + 54, ly)], **sample)
            self.text(x + 66, ly, label, self.f["sans"], 9.5, color=MUTED)
            x += 330
        self.text(x + 140, ly, self.t["legend"][3], self.f["mono"], 8.5, color=MUTED)

    def overflow(self):
        self.fig.canvas.draw()
        renderer = self.fig.canvas.get_renderer()
        inverse = self.ax.transData.inverted()
        problems = []
        for artist, (bx0, by0, bx1, by1) in self.checks:
            extent = artist.get_window_extent(renderer=renderer)
            (x0, y_a), (x1, y_b) = inverse.transform([[extent.x0, extent.y0], [extent.x1, extent.y1]])
            top, bottom = min(y_a, y_b), max(y_a, y_b)
            if x0 < bx0 - 0.5 or x1 > bx1 + 0.5 or top < by0 - 0.5 or bottom > by1 + 0.5:
                problems.append(f"{artist.get_text()!r} spans x {x0:.0f}-{x1:.0f}, y {top:.0f}-{bottom:.0f}; cell x {bx0}-{bx1}, y {by0}-{by1}")
        return problems

    def draw(self):
        self.frame()
        self.lanes()
        for key in self.t["nodes"]:
            self.node(key)
        self.flows()
        self.files()
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
    plate = Plate(args.lang, args.font_dir, args.cjk_font)
    problems = plate.draw()
    suffix = "" if args.lang == "en" else f"_{args.lang}"
    out = Path(args.out_dir)
    plate.fig.savefig(out / f"trio-workflow{suffix}.png", dpi=200, facecolor=PAPER)
    plt.rcParams["pdf.fonttype"] = 42
    plate.fig.savefig(out / f"trio-workflow{suffix}.pdf", facecolor=PAPER)
    for problem in problems:
        print(f"OVERFLOW {problem}")
    print(f"PLATE {args.lang} written to {out}; overflow={len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
