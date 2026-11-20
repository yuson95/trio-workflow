---
name: trio-workflow
description: Trio workflow. An operator decides, a reviewer agent plans and gives independent verdicts at stops, and a builder agent builds in batches with evidence; any agents can take the roles. Use it to set up a project, draft a plan or change request, review a stop, design or small change ("审查…停点N", "复审", "看一下设计", "看一下小改"), merge or clean up ("合并并推送", "只合并不推送", "做收尾"), or run, resume or pause a builder, with or without pull requests.
license: MIT
metadata:
  version: "0.9.0"
  repository: https://github.com/yuson95/trio-workflow
---

# Trio workflow

There are three roles. All state lives in files, so any session can be replaced by a fresh one.

| Role | Owns | Does not do |
| --- | --- | --- |
| **Operator** (human) | Goals, product calls, walkthroughs, authorizing irreversible actions, relaying short pointers between agents | Reading code |
| **Reviewer** (agent) | Plans and change requests written after reading the code; verdicts at stops; the flow file; merges and pushes once authorized | Editing source, tests, config or repo docs, so its verdicts stay independent |
| **Builder** (agent: a lead plus workers) | Implementation in batches, self-checks, the progress file, the decision trail, stop materials | Pushing, merging into `main`, the operator's services, client data |

Each project names who plays which role in `0_RULES`, under "Roles": for example Claude reviews and Codex builds, two Codex sessions, or a Grok bot as builder. When both roles share a model family, apply the independence rules in [review.md](review.md). A **line** is one stream of work run by one builder session; several lines may run at once.

## 1. Locate

1. **Identify your role.**
   - The operator's words decide; otherwise the role table does. If there is neither, ask once.
   - If a branch file assumes a role you do not hold, do only what your role owns.
2. **Find the handoff directory**, in this order: your tool's memory, the repo's `AGENTS.md` or `CLAUDE.md`, the operator's message. If none has it, ask. If no directory exists yet, bootstrap one.
3. **Read the current state.**
   - Reviewer: `00_FLOW` §0, and `0_RULES` for the roles, the lock file and the verification recipe.
   - Builder: `0_RULES`, the plan's general sections, and the progress file.
4. **Restate the goal** in your first message: what the operator wants, the problem behind it, and the smallest change that would meet it. Then carry on without waiting.

Done when you can name each line, its current step, and your next step.

## 2. Branches

| Operator says, or situation | Read |
| --- | --- |
| New project, "set up the workflow" | [bootstrap.md](bootstrap.md) |
| "Draft a plan"; a reported problem or new need; a change request | [planning.md](planning.md) |
| "审查<plan>停点N", "复审", "审查<request>", "看一下设计", "看一下小改" | [review.md](review.md) |
| "合并并推送", "只合并不推送", "做收尾" | [merge.md](merge.md) |
| Builder: start, continue, resume, or pause | [builder.md](builder.md) |
| Code inside a batch, the inner playbook, pstack | [layers.md](layers.md) |
| Pull requests, CI, batch PRs, the plan PR (`Delivery: pr`) | [prs.md](prs.md) |
| Anything the operator will see: prototypes, screenshots, visual review, walkthroughs | [ui-acceptance.md](ui-acceptance.md) |
| Applying a principle | [principles.md](principles.md) |

trio is the outer layer: plans, stops, reviews, merges and the operator's decisions. The inner layer, how a worker writes code inside one batch, is pstack where the project names it and otherwise trio's built-in rules ([layers.md](layers.md)).

**Scripts** in `scripts/` need Python 3.10 or later:

| Script | Use |
| --- | --- |
| `bootstrap_handoff.py --dir <path> --project <name> --reviewer <agent> --builder <agent> --lang zh` | Create the handoff files from the templates |
| `check_plan.py <plan file>` | Check a plan's structure before handing it over |
| `heavy_lock.py --lock <path> run --owner <session> [--watch <log>] -- <command>` | Run a heavy check under the machine-wide lock; a run with no output for 30 minutes is stopped and the lock released |
| `heavy_lock.py --lock <path> run-steps --owner <lead> --steps <file>` | Run a worker's heavy steps file under one hold, each step into its own log; `--dry-run` checks the file without the lock |
| `log_decision.py <file> <phase> <decision> <why> <evidence> <result>` | Append a row to `<KEY>_DECISIONS.tsv` |
| `screenshot_sheet.py <evidence dir> --states empty full many narrow` | Build the page × state contact sheet |
| `usage_guard.py [--left <percent>] [--threads]` | Before a fan-out: `FULL`, `ONE_WORKER` or `PAUSE`, from the usage left; `--threads` lists each worker's context |

## 3. File names

All files live in the handoff directory. A path the operator gives wins over these defaults. `<key>` is the plan's short name in lower case, such as `plan3`; `<KEY>` is the same name in upper case.

| File | Writer |
| --- | --- |
| `00_START_HERE`, `00_FLOW`, `0_RULES`, `PROMPTS`, plan files | Reviewer |
| `batch-notes/<KEY>_PROGRESS.md`, `batch-notes/<batch>_HANDOFF.md`, `batch-notes/<KEY>_DECISIONS.tsv` | Builder |
| `batch-notes/REVIEW_<key>_stop<N>.md` (stop material), `DESIGN_<topic>.md` | Builder |
| `batch-notes/REVIEW_<key>_stop<N>_RESULT.md`, `REQUEST_<topic>.md`, `DESIGN_<topic>_REVIEW.md`, `CLEANUP_<date>.md` | Reviewer |

## 4. Rules for every branch

- **Authority.** Irreversible or outward actions wait for the operator's own words: push, merge into `main`, delete, comment on or close a GitHub item, restart the operator's service, message anyone. Show outgoing text first. Reversible work goes ahead without asking.
- **Defaults.** Every open decision carries a default; if the operator does not answer, proceed on it and report it. Settle factual forks by running a probe; ask only product or preference calls.
- **Evidence.** Done means observed on the real artifact: a command and its output, a page with a screenshot, a stored value. Green checks and self-reports are inputs, never the verdict.
- **Honesty.** A check that did not run is `NOT_RUN`. Label each claim as measured, inferred or guessed.
- **External facts.** Regulations, prices, subsidies and emission factors need a dated, reviewed source-verification document before anyone relies on them.
- **Ownership.** One writer per file and per branch, as the plan's ownership table says. Protect shared resources with structure, such as locks and sequencing.
- **Data.** Tests, live checks and walkthroughs use synthetic copies. Client data stays on the machine.
- **Candor.** "No" is a valid answer; give your real judgment.
- **Language.** Write files and replies in the operator's working language. The templates give structure only.
- **Replies.** The first line, per line of work, reads "state → next step". Chat carries only the operator's decisions; details go into files.

## 5. Principles

Each has a trigger and an action in [principles.md](principles.md). Name the principle wherever it shaped a decision.

- **Core:** restate first, settle forks by running, subtract before you add, smallest change, fix root causes.
- **Verification:** prove it works, look at the page, explain the number, sequence verifiable units, test behavior.
- **Delegation:** guard the context window, fresh worker per task, read the diff not the summary, never block on the operator, separate before serializing.
- **Meta:** encode lessons in structure, build the lever, keep a decision trail.

## 6. Token economy

- Read current-state files first (`00_FLOW` §0, `CURRENT_STATUS.md`); open history by file name only when needed.
- Report summary lines of checks; write full logs to files and give the path.
- Read only the plan sections for this batch or stop; run `diff --stat` before opening single files.
- Review each stop in a fresh session; earlier `RESULT` files carry the open items.
- Route bulk reading to workers; keep summaries in the main thread.
- Every call resends the caller's whole context. Keep workers short-lived and messages few, and check usage before fanning out ([builder.md](builder.md) token rules 8 to 10).
