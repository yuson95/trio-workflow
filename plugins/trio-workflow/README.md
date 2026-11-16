# trio-workflow

A delivery workflow for coding agents with three roles:

- an **operator** (a person) sets goals, makes product calls and walks through the real product;
- a **reviewer** agent turns goals into plans and gives independent verdicts at fixed stops;
- a **builder** agent implements in batches and proves every batch with evidence.

Any agent can take either agent role: Claude, Codex, Grok, Cursor, or two sessions of one tool. Each project records its pairing in `0_RULES` under "Roles".

## Two layers

| Layer | Decides | Provided by |
| --- | --- | --- |
| Outer | what gets built, when work stops for review, whether it lands, what the operator decides | trio |
| Inner | how a worker writes and proves the code inside one batch | [pstack](https://github.com/cursor/plugins/tree/main/pstack) when installed, otherwise trio's built-in rules |

The contract between the layers is in `skills/trio-workflow/layers.md`:

- the kickoff a batch receives and what it returns;
- which pstack playbook each batch type uses (feature, bug fix, refactoring, perf, hillclimb, visual parity, prototype, investigation);
- which pstack steps are switched off under trio, such as opening PRs, merging, or using cloud VMs with client data.

## What is inside

| Path | Content |
| --- | --- |
| `skills/trio-workflow/SKILL.md` | Entry point: roles, routing, rules, principles index, scripts |
| `skills/trio-workflow/bootstrap.md` | Set up a project: handoff directory, role table, verification recipe |
| `skills/trio-workflow/planning.md` | Plans and change requests, including the parallel design (ownership table, hotspots, waves) |
| `skills/trio-workflow/review.md` | Stop reviews, re-reviews, design reviews, small changes; independence rules; verdicts bound to a commit |
| `skills/trio-workflow/merge.md` | Merge, push, restart, cleanup, retro |
| `skills/trio-workflow/builder.md` | Builder lead and workers: kickoff, integration, stalls, stops, resume, pause, token rules |
| `skills/trio-workflow/layers.md` | Outer/inner contract and the pstack adapter |
| `skills/trio-workflow/principles.md` | The principles, each with a trigger and an action |
| `skills/trio-workflow/scripts/heavy_lock.py` | Machine-wide lock so heavy checks from different sessions never overlap |
| `skills/trio-workflow/scripts/log_decision.py` | Appends one row to a plan's decision trail |
| `skills/trio-workflow/scripts/check_plan.py` | Checks a plan's structure (types, "You see" lines, verification, defaults, file ownership) |

The scripts need Python 3.9 or later and nothing else.

## Install

Pick one mode per tool. Installing both ways makes the tool see the skill twice.

### Plugin mode

The repository is a local marketplace for Claude Code and for Codex.

**Claude Code**:

```bash
claude plugin marketplace add D:\Projects\trio-workflow
```

```bash
claude plugin install trio-workflow@trio-local
```

You can also run `/plugin` inside Claude Code and add the marketplace there.

**Codex**: add these lines to `~/.codex/config.toml`, then restart Codex.

```toml
[marketplaces.trio-local]
source_type = "local"
source = 'D:\Projects\trio-workflow'

[plugins."trio-workflow@trio-local"]
enabled = true
```

**Cursor**: the plugin folder carries `.cursor-plugin/plugin.json`, the same format pstack uses. Add it as a local plugin through Cursor's plugin settings, or use copy mode.

### Copy mode

```bash
python tools/install_local.py install --target claude codex cursor
```

`check` reports copies that are out of date, and `remove` deletes them before you switch to plugin mode.

### Any other agent (for example a Grok bot)

Put the absolute path of `skills/trio-workflow/SKILL.md` into the agent's system prompt or the repo's `AGENTS.md`, with this line: "Read and follow this skill; open the branch files it names when they apply."

## Using pstack as the inner layer

1. Install pstack in the tools that run the builder's workers, and in the reviewer's tool if you want its interrogate and arena skills.
2. In the project's `0_RULES`, set `Inner layer: pstack (installed in <tools>)`.
3. Tag every requirement in a plan with a type. The builder copies the matching playbook into each batch kickoff.

## Origin and credits

The workflow comes from running the EnergyCompass project in November 2026: a reviewer agent and a builder agent from different vendors, plans with stops, operator walkthroughs, check tiers, and token rules.

Several practices are adapted from pstack by poteto (MIT licence, <https://github.com/cursor/plugins/tree/main/pstack>):

- restate first;
- prove it works;
- explain the number;
- sequence verifiable units;
- separate before serializing;
- encode lessons in structure;
- fresh workers;
- verdicts bound to a commit;
- adversarial review;
- the verification recipe;
- the decision trail.

The wording here is our own. pstack itself is not bundled; install it from its own source.
