# trio-workflow (repository)

This repository holds the **trio-workflow** plugin, a delivery workflow for coding agents with an operator, a reviewer and a builder. The usage guide is [plugins/trio-workflow/README.md](plugins/trio-workflow/README.md).

## Who it's for

trio-workflow is built for **people who are experts in another field** (engineering, energy, finance, medicine, research, consulting) and want AI agents to build software for that field, without being professional programmers or product managers. You know what a correct result looks like; trio supplies the parts of software practice you do not have time to learn:

| You may not have | trio provides |
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

New to software projects? Read the step-by-step guide: **[docs/QUICKSTART.md](docs/QUICKSTART.md)** · **[中文版 docs/QUICKSTART_zh.md](docs/QUICKSTART_zh.md)**. In short:

1. Install the skill in both tools: `python tools/install_local.py install --target claude codex`.
2. In the reviewer, say "Set up the trio workflow for this project", and answer its questions; the defaults are fine.
3. Describe what you want; confirm the prototypes in the plan.
4. Paste the kickoff prompt into the builder; it works until the first stop.
5. At each stop, open a fresh reviewer session and say "review plan 1 stop 1"; answer its decisions, then pass the result path to the builder.
6. Walk through the prepared test copy when asked; say what feels wrong.
7. When the final review passes, say "merge and push".

## The workflow at a glance

![trio workflow plate](docs/workflow/trio-workflow.png)

Who acts (lanes) against when (phases), with the files every step writes and the rules every step keeps.

- English: [PNG](docs/workflow/trio-workflow.png) · [PDF](docs/workflow/trio-workflow.pdf)
- 中文: [PNG](docs/workflow/trio-workflow_zh.png) · [PDF](docs/workflow/trio-workflow_zh.pdf)

The plates are drawn by [docs/workflow/draw_workflow.py](docs/workflow/draw_workflow.py), which needs matplotlib. It fails when a caption overflows its cell, so redraw and commit the plates whenever the workflow changes. The visual language is described in [docs/workflow/DESIGN_PHILOSOPHY.md](docs/workflow/DESIGN_PHILOSOPHY.md).

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

The repository has no licence yet: it is private and all rights are reserved until a licence is chosen.
