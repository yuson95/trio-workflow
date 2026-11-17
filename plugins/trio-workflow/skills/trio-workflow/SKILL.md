---
name: trio-workflow
description: Trio workflow for agent-driven delivery. An operator sets goals and walks through the real product, a reviewer agent plans and gives independent verdicts, and a builder agent implements in batches with evidence. Any agent can hold either role, for example Claude, Codex, Grok, or two sessions of one tool. Use it to set up a project's collaboration skeleton; to draft a plan or change request; to review a stop, a re-review, a design or a small change ("审查…停点N", "复审", "看一下设计", "看一下小改"); to merge and clean up ("合并并推送", "只合并不推送", "做收尾"); to run, resume or pause a builder session; to decide how a batch's code is written (built-in rules or pstack playbooks as the inner layer); or to combine stops with pull requests and CI.
---

# Trio workflow

There are three roles. All state lives in files, so any session can be replaced by a fresh one at any time.

| Role | Owns | Does not do |
| --- | --- | --- |
| **Operator** (human) | Goals, product calls, walkthroughs of the real product, authorizing irreversible actions, relaying short pointers between agents | Reading code |
| **Reviewer** (agent) | Plans and change requests written after reading the code; verdicts at stops; the flow file; merges and pushes once authorized | Editing source, tests, config and repo docs, so its verdicts stay independent |
| **Builder** (agent: one lead plus workers) | Implementation in batches, self-checks, the progress file, the decision trail, stop materials | Pushing, merging into `main`, the operator's running services, client data |

Each project sets who plays which role in `0_RULES`, under "Roles". Possible setups:

- Reviewer = Claude Code, Builder = Codex;
- Reviewer and Builder both Codex, in separate sessions;
- Builder = a Grok bot.

When both roles run on the same model family, apply the independence rules in [review.md](review.md).

A **line** is one stream of work run by one builder session, such as a plan, or a line of small fixes. Several lines may run at once.

## 1. Locate

1. **Identify your role.**
   - The operator's words decide; otherwise the project's role table does. If there is neither, ask once.
   - If a branch file assumes a role you do not hold, do only what your role owns. Example: a builder asked to bootstrap drafts the step-1 questions of [bootstrap.md](bootstrap.md) for the operator to hand to the reviewer.
2. **Find the handoff directory.** Look in order:
   - your tool's memory, if it has one;
   - the repo's `AGENTS.md` / `CLAUDE.md`;
   - the operator's message.

   If none of them has it, ask. If no directory exists yet, take the bootstrap branch.
3. **Read the current state.**
   - Reviewer: `00_FLOW` §0, and `0_RULES` for the roles, the lock file and the verification recipe.
   - Builder: `0_RULES`, the plan's general sections, and the progress file.
4. **Restate the goal** in your own words in your first message: what the operator wants, the problem behind it, and, for a change, the smallest change you expect to meet it. Then carry on without waiting. A misreading costs one message to correct here and far more later.

Done when you can name each line, its current step, and your next step.

## 2. Branches

| Operator says, or situation | Read |
| --- | --- |
| New project, "set up the workflow" | [bootstrap.md](bootstrap.md) |
| "Draft a plan"; operator reports a problem or a new need; change request | [planning.md](planning.md) |
| "审查<plan>停点N", "复审", "审查<request>", "看一下设计", "看一下小改" | [review.md](review.md) |
| "合并并推送", "只合并不推送", "做收尾" | [merge.md](merge.md) |
| Builder: start, continue, resume, or pause | [builder.md](builder.md) |
| Writing code inside a batch; choosing the inner playbook; pstack is installed | [layers.md](layers.md) |
| Pull requests, CI, a batch PR or the plan PR (`Delivery: pr` in `0_RULES`) | [prs.md](prs.md) |
| Anything the operator will see: prototypes, screenshot matrix, visual review, walkthrough notes | [ui-acceptance.md](ui-acceptance.md) |
| Applying any principle below | [principles.md](principles.md) |

## Two layers

trio is the **outer layer**: plans, stops, reviews, merges and the operator's decisions. The **inner layer** is how a worker writes and proves the code inside one batch. That is pstack when the project's `0_RULES` names it and the worker's tool has it installed; otherwise it is trio's built-in rules. [layers.md](layers.md) holds the contract between the two layers, the mapping from batch type to playbook, and the pstack steps that change under trio.

## Scripts

The scripts live next to this file in `scripts/` and run with Python 3.10 or later.

| Script | Use |
| --- | --- |
| `heavy_lock.py --lock <path> run --owner <session> -- <command>` | Run a heavy check under the machine-wide lock (`status`, `acquire` and `release` are also available) |
| `log_decision.py <file> <phase> <decision> <why> <evidence> <result>` | Append one row to `<KEY>_DECISIONS.tsv` |
| `check_plan.py <plan file>` | Check a plan's structure before handing it over |
| `screenshot_sheet.py <evidence dir> --states empty full many narrow` | Build the page × state contact sheet, `main` beside the candidate |

## 3. File names

All files live in the handoff directory. A path the operator gives wins over these defaults. `<key>` is the plan's short name in lower case, such as `plan3`; `<KEY>` is the same name in upper case, such as `PLAN3`.

| File | Writer |
| --- | --- |
| `00_START_HERE`, `00_FLOW`, `0_RULES`, `PROMPTS`, plan files | Reviewer |
| `batch-notes/<KEY>_PROGRESS.md`, `batch-notes/<batch>_HANDOFF.md`, `batch-notes/<KEY>_DECISIONS.tsv` | Builder |
| `batch-notes/REVIEW_<key>_stop<N>.md` (stop material), `DESIGN_<topic>.md` | Builder |
| `batch-notes/REVIEW_<key>_stop<N>_RESULT.md` (the stop material's name plus `_RESULT`), `REQUEST_<topic>.md`, `DESIGN_<topic>_REVIEW.md`, `CLEANUP_<date>.md` | Reviewer |

## 4. Rules for every branch

- **Authority.** Irreversible or outward actions wait for the operator's own words: push, merge into `main`, delete, comment on or close a GitHub item, restart the operator's service, message anyone. Show outgoing text to the operator first. Reversible work goes ahead without asking.
- **Defaults.** Every open decision carries a default. If the operator does not answer, proceed on the default and report it.
  - Settle factual forks yourself by running a probe.
  - Ask the operator only product or preference calls that no run can settle.
- **Evidence.** Done means observed on the real artifact: a command and its output, a page state with a screenshot, a stored value. Green checks and self-reports are inputs to a verdict, never the verdict.
- **Honesty.** A check that did not run is `NOT_RUN`. Label each claim as measured, inferred or guessed.
- **External facts.** Regulations, prices, subsidies and emission factors need a dated source-verification document that has been reviewed before anyone relies on them.
- **Ownership.** One writer per file and per branch; the boundaries come from the plan's ownership table. Protect shared resources with structure, such as lock files and sequencing, not with conventions alone.
- **Data.** Tests, live checks and walkthroughs use synthetic copies. Client data stays on the machine.
- **Candor.** "No" is a valid answer. When asked whether to do something, give your real judgment.
- **Language.** Write files and replies in the operator's working language (see `AGENTS.md`). The templates here give structure only.
- **Replies.** The first line, per line of work, reads "state → next step". Chat carries only the decisions the operator must make; details go into files.

## 5. Principles

Each principle has a trigger and an action in [principles.md](principles.md). When one shapes a decision, name it in the file or reply where you record that decision.

- **Core:** restate first, settle forks by running, subtract before you add, smallest change, fix root causes.
- **Verification:** prove it works, look at the page, explain the number, sequence verifiable units, test behavior.
- **Delegation:** guard the context window, fresh worker per task, read the diff not the summary, never block on the operator, separate before serializing.
- **Meta:** encode lessons in structure, build the lever, keep a decision trail.

## 6. Token economy

- Read the current-state files first (`00_FLOW` §0, `CURRENT_STATUS.md`). Open history by file name, only when needed.
- Report only the summary lines of checks. Write full logs to files and report the path.
- Read only the plan sections for this batch or stop. Run `diff --stat` first, then open single files.
- Review each stop in a fresh session; the earlier `RESULT` files carry the open items forward.
- Route bulk reading to workers and keep only summaries in the main thread.
