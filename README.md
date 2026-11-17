# trio-workflow (repository)

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

This repository holds the **trio-workflow** plugin, a delivery workflow with three roles:

- you, the operator, decide;
- one agent plans and reviews;
- another agent builds.

Plan-level **stops** and batch-level **pull requests** work together: PRs with CI guard the code, and stops guard your intent. The usage guide is [plugins/trio-workflow/README.md](plugins/trio-workflow/README.md).

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

It is a poor fit for professional engineering teams that already run pull requests, CI and code review on GitHub (pstack or similar tools fit them better), for throwaway prototypes where stops and documents cost more than they save, and for anyone who wants an app from one sentence without taking part in decisions and walkthroughs.

**What it asks of you**: patience for a little process, basic comfort with folders and a terminal, usually two agent subscriptions, and synthetic sample data.

## Quickstart

New to trio? Read the step-by-step guide: **[docs/QUICKSTART.md](docs/QUICKSTART.md)** · **[中文版 docs/QUICKSTART_zh.md](docs/QUICKSTART_zh.md)**. In short:

1. Install the skill in both tools: `python tools/install_local.py install --target claude codex`.
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
- during building, the builder's line splits into worker tracks, and each square on them is one batch pull request with CI.

- English: [PNG](docs/workflow/trio-workflow.png) · [PDF](docs/workflow/trio-workflow.pdf)
- 中文: [PNG](docs/workflow/trio-workflow_zh.png) · [PDF](docs/workflow/trio-workflow_zh.pdf)

The plates are drawn by [docs/workflow/draw_workflow.py](docs/workflow/draw_workflow.py), which needs matplotlib. It fails when a caption overflows its cell, so redraw and commit the plates whenever the workflow changes. The visual language is described in [docs/workflow/DESIGN_PHILOSOPHY.md](docs/workflow/DESIGN_PHILOSOPHY.md).

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
| `.claude-plugin/marketplace.json` | Local Claude Code marketplace `trio-local` |
| `.agents/plugins/marketplace.json` | Local Codex marketplace `trio-local` |
| `tools/install_local.py` | Copy mode: install, check or remove the skill in `~/.claude`, `~/.codex` and `~/.cursor` |
| `tests/` | Behavior tests for the scripts, with sample plans |
| `docs/workflow/` | The workflow plate in English and Chinese (PNG, PDF) and the script that draws it |
| `CHANGELOG.md` | Versions |

## Development

Run the tests:

```bash
python -m unittest discover -s tests
```

Release a new version:

1. Edit the skill under `plugins/trio-workflow/skills/trio-workflow/`.
2. Raise `version` in the four manifests.
3. Add a `CHANGELOG.md` entry.
4. Run the tests.
5. Commit.

If you use copy mode, then run:

```bash
python tools/install_local.py install
```

## License

MIT, see [LICENSE](LICENSE). Practices adapted from pstack are credited in the plugin README; pstack is MIT-licensed as well.
