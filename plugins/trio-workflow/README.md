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
| `skills/trio-workflow/prs.md` | Stops and pull requests together: batch PRs with CI into `wip/<plan>`, stops for independent review, a plan PR into `main` |
| `skills/trio-workflow/principles.md` | The principles, each with a trigger and an action |
| `skills/trio-workflow/ui-acceptance.md` | UI acceptance: prototypes before code, screenshot matrix, visual review, walkthrough findings turned into structure |
| `skills/trio-workflow/scripts/heavy_lock.py` | Machine-wide lock so heavy checks from different sessions never overlap |
| `skills/trio-workflow/scripts/log_decision.py` | Appends one row to a plan's decision trail |
| `skills/trio-workflow/scripts/check_plan.py` | Checks a plan's structure (types, "You see" lines, verification, prototypes for review-gated items, defaults, file ownership) |
| `skills/trio-workflow/scripts/screenshot_sheet.py` | Builds the page × state contact sheet, `main` beside the candidate |

The scripts need Python 3.10 or later and nothing else.

## Install

trio is a plugin that carries one skill, the instructions your agents follow. Pick one install mode per tool: installing both ways makes the tool see trio twice.

### Plugin mode

The repository is a plugin marketplace named `trio`.

**Claude Code**, straight from GitHub:

```bash
claude plugin marketplace add yuson95/trio-workflow
```

```bash
claude plugin install trio-workflow@trio
```

You can also run `/plugin` inside Claude Code and add the marketplace there. To install from a local checkout, give its path instead of `yuson95/trio-workflow`.

**Codex**: clone the repository, add these lines to `~/.codex/config.toml`, then restart Codex.

```bash
git clone https://github.com/yuson95/trio-workflow.git
```

```toml
[marketplaces.trio]
source_type = "local"
source = '<path to your trio-workflow checkout>'

[plugins."trio-workflow@trio"]
enabled = true
```

**Cursor**: the plugin folder carries `.cursor-plugin/plugin.json`, the same format pstack uses. Add it as a local plugin through Cursor's plugin settings, or use copy mode.

### npx mode

The open [`skills`](https://github.com/vercel-labs/skills) installer from Vercel finds trio's skill in this repository and installs it into many agents with one command. It needs Node.js 22.20 or later.

```bash
npx skills add yuson95/trio-workflow -g -a claude-code -a codex -y --copy
```

- Add `-a cursor` for Cursor.
- `npx skills check -g` reports newer versions, `npx skills update -g` installs them, and `npx skills remove trio-workflow -g` uninstalls trio.
- `--copy` writes plain copies instead of symlinks, which avoids symlink permission issues on Windows.
- The installer sends anonymous usage statistics unless `DISABLE_TELEMETRY=1` is set.
- For Codex it installs into `~/.agents/skills/`.

### Copy mode

From the root of a clone of the repository:

```bash
python tools/install_local.py install --target claude codex cursor
```

`check` reports copies that are out of date, and `remove` deletes them before you switch to plugin mode.

## Delivery: local or PR mode

Each project chooses in its `0_RULES`:

- **local** (the default): batches merge on your machine, and nothing reaches the remote until you say "merge and push";
- **pr**: every batch becomes a pull request with CI into `wip/<plan>`, and a plan PR carries the plan into `main`.

Stops work the same in both modes. See `skills/trio-workflow/prs.md`.

### Any other agent (for example a Grok bot)

Put the absolute path of `skills/trio-workflow/SKILL.md` into the agent's system prompt or the repo's `AGENTS.md`, with this line: "Read and follow this skill; open the branch files it names when they apply."

## Using pstack as the inner layer

1. Install pstack in the tools that run the builder's workers, and in the reviewer's tool if you want its interrogate and arena skills.
2. In the project's `0_RULES`, set `Inner layer: pstack (installed in <tools>)`.
3. Tag every requirement in a plan with a type. The builder copies the matching playbook into each batch kickoff.

## Origin and credits

The workflow comes from building a private energy-consulting tool in November 2026: a reviewer agent and a builder agent from different vendors, plans with stops, operator walkthroughs, check tiers, and token rules.

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

## License

MIT. See [LICENSE](LICENSE) in the repository root.
