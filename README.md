# trio-workflow

> **For anyone building software with AI agents who would welcome support across the many roles a project needs.**
> 写给借助 AI agent 开发软件、希望在项目的各个角色上都有可靠支持的人。
>
> For example:
>
> - domain experts without a programming background;
> - developers who are strong in code but newer to design and product work;
> - designers with a clear product vision who write little code themselves;
> - people who prefer a dependable review process to checking every line themselves;
> - independent developers and small teams with limited capacity.
>
> 例如：
>
> - 没有编程专业背景的领域专家；
> - 擅长编程、但在设计和产品方面经验较少的开发者；
> - 对产品有清晰构想、但较少亲自写代码的设计师；
> - 希望依靠可靠的审查流程、而不必亲自逐行检查代码的人；
> - 独立开发者，以及人手有限的小团队。
>
> **The premise**: you stay in charge at the key moments: the plan, the prototypes, the decisions at each stop, the walkthrough and the merge. trio is not a way to get a whole app from one sentence.
>
> **前提**：关键环节始终由你把关：方案、原型、每个停点的决定、走查和合并。trio 不是“一句话做出整个应用”的工具。

This repository holds the **trio-workflow** plugin, a delivery workflow with three roles:

- you, the operator, decide;
- one agent plans and reviews;
- another agent builds.

Plan-level **stops** guard your intent: fixed points where an independent review happens and you decide. Projects on GitHub can add batch-level **pull requests** with CI (PR mode) to guard the code between stops. The usage guide is [plugins/trio-workflow/README.md](plugins/trio-workflow/README.md).

## When trio fits

trio is built for two situations.

1. **You bring expertise.** You know a field well (engineering, energy, finance, medicine, research, consulting) and want software that gets that field right. trio turns your knowledge into requirements with checks, cross-checks the numbers another way, and brings the judgment calls to you.
2. **You bring an idea that has not taken shape yet.** You know the problem and roughly what you want, but not yet the form. trio helps the idea take shape:
   - the reviewer reads, probes and drafts a plan with prototypes;
   - you confirm it, or pick between variants;
   - you refine it stop by stop.

**It does not fit** if you want a whole app from one sentence and would rather not take part in decisions and walkthroughs. trio's premise is that **you stay in charge at the key moments**:

| Key moment | What you do | Typical time |
| --- | --- | --- |
| Plan and prototypes | confirm, or pick a variant | 15 to 30 minutes |
| Each stop | answer a few decisions; each has a default | 10 to 30 minutes |
| Walkthrough | try the real pages and say what feels wrong | 1 to 2 hours |
| Merge | say "merge and push" | a minute |

Between those moments, nobody waits on you.

**适合的两种场景**：

1. **你有专业知识**：熟悉某个领域，想做出在这个领域里既算得对、又用得顺的软件。trio 把你的知识变成带检查的需求，数字换一条路核对，需要判断的地方交给你。
2. **你有想法，但还没成型**：知道要解决什么问题、大致想要什么，但具体形态还没想清楚。trio 帮你把想法做成型：
   - 审查者先读代码、先试，再写出带原型的方案；
   - 你确认，或者从几个变体里选一个；
   - 在一个个停点里逐步调整。

**不适合**：想“一句话做出整个应用”、不愿意参与决定和走查的人。trio 的前提是**你始终在关键处把关**，包括：

- 确认方案和原型；
- 回答每个停点的决定；
- 走查真实页面；
- 授权合并。

这些时刻之外，谁都不会停下来等你。

## Who it's for

A software project calls for many roles: planning, design, coding, review and testing. trio-workflow is for **anyone who would welcome support in some of them**:

- **Domain experts** (engineering, energy, finance, medicine, research, consulting) who know what a correct result looks like but have no programming background.
- **Developers** who are strong in code but newer to design and product work.
- **Designers** with a clear product vision who write little code themselves.
- **People who prefer a dependable review process** to checking every line themselves.
- **Independent developers and small teams** with limited capacity.

trio covers the roles you would like support in with agents that check each other, and keeps you in charge of what gets built:

| Where you may want support | trio provides |
| --- | --- |
| The ability to read and review code | A second agent that reviews independently and backs every verdict with evidence |
| Practice in writing product specifications | Plans written for you, where each requirement states what you will see, has a prototype and carries a default |
| A way to tell whether the agent did it right | Fixed stops, live checks on real pages, numbers cross-checked another way |
| Time to supervise every step | Defaults for every decision; nobody waits on you between stops |
| A place for your taste and domain judgment | Prototypes, screenshot sheets and walkthroughs; your findings become rules and tests |
| Rules for client data and regulations | Synthetic data only, client data kept local, sources verified before use |

It also suits consultants and researchers who work with client data on their own machine, small teams whose results must be numerically right, and anyone who wants agents from two vendors to check each other.

It adds little for teams that already staff every role with people and run their own review process (pstack or similar tools may suit them better), and for throwaway prototypes where stops and documents cost more than they save. See [When trio fits](#when-trio-fits) for the one-sentence case.

**What it asks of you**: patience for a little process, basic comfort with folders and a terminal, usually two agent subscriptions, and synthetic sample data.

## Quickstart

New to trio? Read the step-by-step guide: **[docs/QUICKSTART.md](docs/QUICKSTART.md)** · **[中文版 docs/QUICKSTART_zh.md](docs/QUICKSTART_zh.md)**. In short:

1. Install trio in both tools. With Node.js: `npx skills add yuson95/trio-workflow -g -a claude-code -a codex -y --copy`. Claude Code alone: `claude plugin marketplace add yuson95/trio-workflow`, then `claude plugin install trio-workflow@trio`. Other ways are in the guide.
2. In the reviewer, say "Set up the trio workflow for this project", and answer its questions; the defaults are fine.
3. Describe what you want; confirm the prototypes in the plan.
4. Paste the kickoff prompt into the builder; it works until the first stop.
5. At each stop, open a fresh reviewer session and say "review plan 1 stop 1"; answer its decisions, then pass the result path to the builder.
6. Walk through the prepared test copy when asked; say what feels wrong.
7. When the final review passes, say "merge and push".

## The workflow at a glance

![trio workflow plate](docs/workflow/trio-workflow.png)

The plate is drawn as a metro map:

- each role is a line;
- each action is a station;
- each stop is an interchange where all three lines meet;
- during building, the builder's line splits into worker tracks; in PR mode each square on them is one batch pull request with CI.

- English: [PNG](docs/workflow/trio-workflow.png) · [PDF](docs/workflow/trio-workflow.pdf)
- 中文: [PNG](docs/workflow/trio-workflow_zh.png) · [PDF](docs/workflow/trio-workflow_zh.pdf)

The plates are drawn by [docs/workflow/draw_workflow.py](docs/workflow/draw_workflow.py), which needs matplotlib. It fails when a label leaves the canvas or overlaps another label, so redraw and commit the plates whenever the workflow changes. The visual language is described in [docs/workflow/DESIGN_PHILOSOPHY.md](docs/workflow/DESIGN_PHILOSOPHY.md).

## About the author

I am **Yusheng Chen (Dr.-Ing.)**, an energy systems engineer and consultant in Berlin. I work on decarbonization and renewable integration for industrial and commercial clients.

- **Education**:
  - B.Eng. in building services engineering, Tongji University and FH Münster;
  - M.Sc. in sustainable energy supply, RWTH Aachen;
  - Dr.-Ing. in renewable energy systems, Technical University of Munich, with a thesis on optimizing biomass heating networks with heat pumps and on-site power generation.
- **Work**:
  - energy supply concepts and transformation plans for companies;
  - earlier, research on heat pumps, combined heat and power and heat storage;
  - energy management for public buildings;
  - hydrogen supply-chain studies.
- **Tools**: energy system modeling and mathematical optimization, with Python and MATLAB as engineering tools. I am not a professional software developer or product manager.

That last point is why trio exists. I built an energy-concept tool for my consulting work with two AI agents from different vendors, one reviewing and one building. trio is the workflow that kept the result correct and the way I wanted it.

My longer profile is at [yuson95.github.io](https://yuson95.github.io); parts of it are out of date.

## Layout

| Path | Content |
| --- | --- |
| `plugins/trio-workflow/` | The plugin: the skill, its scripts, and manifests for Claude Code (`.claude-plugin`), Codex (`.codex-plugin`), Cursor (`.cursor-plugin`) and generic agents (`plugin.json`) |
| `.claude-plugin/marketplace.json` | Claude Code marketplace `trio` |
| `.agents/plugins/marketplace.json` | Codex marketplace `trio` |
| `tools/install_local.py` | Copy mode: install, check or remove the skill in `~/.claude`, `~/.codex` and `~/.cursor` |
| `tests/` | Behavior tests for the scripts and the installer, with sample plans |
| `.github/workflows/tests.yml` | Runs the tests on Linux and Windows for every push and pull request |
| `docs/QUICKSTART.md`, `docs/QUICKSTART_zh.md` | Step-by-step guides in English and Chinese |
| `docs/workflow/` | The workflow plate in English and Chinese (PNG, PDF) and the script that draws it |
| `CHANGELOG.md` | Versions |
| `LICENSE` | MIT |

## Development

Run the tests:

```bash
python -m unittest discover -s tests
```

Release a new version:

1. Edit the skill under `plugins/trio-workflow/skills/trio-workflow/`.
2. Raise `version` in the four manifests.
3. Add a `CHANGELOG.md` entry.
4. If the workflow changed, redraw the plates with `python docs/workflow/draw_workflow.py --lang en` and `--lang zh`.
5. Run the tests and `claude plugin validate plugins/trio-workflow`.
6. Commit and push. CI runs the tests on Linux and Windows.

If you use copy mode, then run:

```bash
python tools/install_local.py install
```

## License

MIT, see [LICENSE](LICENSE). Practices adapted from pstack are credited in the plugin README; pstack is MIT-licensed as well.
