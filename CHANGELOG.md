# Changelog

## 0.11.0 (2026-11-24)

The lead no longer stops at a context cap. The cap (350k for Claude Code, 150k for Codex) was set for workers, sized so a worker finishes about 150 calls, and the lead had borrowed it. On one plan the lead stopped twice in a day, and each time the work waited until the operator noticed and opened a new session. Compaction gives the lead a smaller context without a stop, and everything the plan needs is already in files.

- **Lead keeps going** (builder.md token rule 1, `0_RULES` templates): where the tool compacts the context automatically, the lead lets it, then re-reads the progress file, the last rows of the decision trail and the current batches' handoffs before its next action. Only a tool that cannot compact pauses at its cap and continues through Resume.
- **Workers unchanged**: they still hand over at the lifetime in rule 8.

## 0.10.0 (2026-11-23)

Use each usage window fully. What is left when a window resets expires, so holding back never buys more work in a window; it only moves work later. The guard's old defaults (one worker below 30% left, pause below 10%) looked only at the percent left. A builder paused at 4% of its weekly window with a day and a half to the reset, and a lead held back parallel batches to wait for a 5-hour reset. Both times the operator overrode it ("use the quota fully").

- **Defaults** (`usage_guard.py`): `FULL` until 3% left, then `PAUSE`, a reserve just large enough to commit wip and update the handoff and progress file. A window that runs out mid-unit costs at most that unit.
- **Reserve band only on request**: `ONE_WORKER` appears only when a project sets `--reduce-below`, for example to keep quota for a reviewer who shares the window before a stop.
- **Reset-aware**: `--resets-in <hours>` (read from Codex's record when available) waives the reserve band within `--near-hours` (default 24) of the reset.
- builder.md token rule 10 and step 5, the `0_RULES` templates, SKILL.md and the README now say the same: defer no batch and narrow no fan-out to wait for a reset.

## 0.9.0 (2026-11-20)

From the fix round and re-review of one plan's final stop: 30 worker units in about a day, 11 interruptions, 4 workers that spent their lifetime waiting for the heavy-check lock.

- **Lock fix** (`heavy_lock.py`): a second `run` by the same owner no longer starts at once. Before, it ran beside the first, and when the first finished it released the lock while the second was still running, so a third session could start a heavy run. Each acquisition now carries a token, and a run releases only its own.
- **`run-steps`** (`heavy_lock.py`): runs the steps of a JSON file in order under one hold, each into its own log, with one summary line per step (exit code, expected lines found, time, log path). `--dry-run` checks the file without the lock.
- **Workers leave the waiting to the lead** (builder.md step 5, token rule 8): a long wait costs a Claude Code worker one call per ten minutes, so waiting for the lock used up whole worker lifetimes. A worker that finds the lock busy hands back a steps file with `NEEDS_HEAVY_RUN`; the lead runs the files in one queue at integration.
- **Census for a reversal** (planning.md A step 5 and B step 4, builder.md step 3): when a requirement reverses an existing behavior, the plan or request lists the tests and contract cases that assert the old behavior, found by searching for its codes and running the suites in every interpreter, skipped tests included. That batch owns them. In the round behind this release, 9 of 11 interruptions came from tests of the old behavior sitting in other batches' files, and the audit had missed two tests that the default interpreter skips.
- **Re-review scope** (review.md B): IDs that joined a fix round through a change request or the operator's direct requests are reviewed as at a stop. Only the fix IDs follow the lighter re-review.
- **Invariant breaks** (layers.md rule 5, builder.md handoff and stop material, review.md step 3): the builder records each break (edited line, red test, reverted). The reviewer reads the records and breaks, itself, the invariants behind high-severity findings, those without a record and a sample of the rest. 0.8.0 asked the reviewer to break every invariant; with 15 invariants the reviewer broke 5, and the builder's records covered the rest.
- **Check-infrastructure lessons first** (principles.md, planning.md A step 2): a lesson about the checks themselves goes into the next plan's first batch. A load-related timeout deferred to a later plan failed 2 of 4 full checks in the plan between.
- **Smaller rules**: a worker whose tool refuses its handoff file sends the text and the lead saves it (token rule 9); reviewer probes print the code path and commit they ran against (review.md step 3); the lead's cap follows its tool, `0_RULES` is updated when the builder tool changes, and a lead that cannot open a session asks the operator once (token rule 1, `0_RULES` templates).

## 0.8.0 (2026-11-20)

Spend review effort where a run can settle it. pstack warns that adversarial review of a plan with no code behind it invents risks that never happen, and keeps only findings a run proves. trio's adversarial pass already counted only reproduced findings, but its plan and design reviews had no such limit, and plans had no place for the properties a change must keep. At one plan's final stop, the two defects that changed reported numbers (a site-wide baseline that depended on which measures a portfolio held, and a saving that could be deducted twice) passed every unit test and surfaced only in the reviewer's own runs. On the same plan, a provenance rule written at planning time as hard blocks everywhere had to be relaxed to visible labels once the operator ran into it.

- **Before code exists** (review.md, Writing findings): at plan and contract stops and in design reviews, a finding is a contradiction with the current code (with its pointer), the output of a probe or prototype, or a decision for the operator. An imagined risk gets a probe or stays out.
- **Blocking checks** (planning.md A step 5): a requirement that refuses a save or stops a calculation names the harm it prevents and why a visible label would not prevent it.
- **Invariants** (planning.md A step 5 and the plan template): a requirement that computes numbers or changes stored state lists the properties that must hold for every input, each with a test over varied inputs; other requirements write `none`. `check_plan.py` requires the line (`Invariants` / `不变量`). Kickoffs carry the invariants to workers, who see each test go red on a broken version; at stops the reviewer breaks the guarded code once and confirms the test fails.

## 0.7.4 (2026-11-19)

From the first night of a Claude Code builder on one plan: 36 workers in 14 hours. About half of the work came from verification. Most of it fixed real defects, but two things were pure waste: proof checks that ran before the code stopped changing and had to run again, and a hung screenshot run that held the heavy-check lock for two hours.

- **Two passes** (builder step 9): a discovery pass runs early (screenshot matrix, visual review, first-save replay, one regression run) to find defects while batches are open. The builder then freezes the candidate and runs the acceptance pass once on it: the stop's checks, the screenshot matrix and contact sheet, and the walkthrough instance. Each result names the SHA it ran on. A fix after the freeze reruns the acceptance checks that cover its files; the full check runs last, on the final SHA. The reviewer treats a result from an older SHA as `NOT_RUN` unless the material says why the later fixes cannot affect it.
- **Idle stop** (`heavy_lock.py run`): after `--idle-minutes` (default 30) without output, and without growth of any `--watch` log, the command's whole process tree is stopped, the lock released, and the run exits 124. Python children run unbuffered so their progress counts. `--idle-minutes 0` turns it off.

## 0.7.3 (2026-11-18)

Calibrated on a Claude Code builder's first evening: 7 workers, 733 calls. Handover ramp-up cost 7% of their tokens, far less than letting contexts keep growing, but one theme-sized batch ("fix every failure") ran through four workers.

- **Batch size**: the lead sizes each batch so one worker finishes it in about 100 tool calls. Batches are split by module, test group or about 20 list items, never by theme alone. A batch that needs a successor is split before it is handed on.
- **Caps per tool**: context grows about 0.4k tokens per call in Codex and about 1.8k in Claude Code, which also starts near 60k. The context cap is now 150k for Codex and 350k for Claude Code (250k and 500k for bug-fix and investigation batches, which also get about 225 calls). Where the lead cannot read a worker's context, the call count governs.
- **Reuse the quick check**: the handoff records the last quick-check log and its commit. A successor whose branch head matches reuses that log, then makes targeted checks of its predecessor's claims.
- **Usage source**: `usage_guard.py` without `--left` reads Codex's record only. A Claude Code lead reads its plan windows with the desktop app's usage tool and passes the smallest percent left as `--left`.

## 0.7.2 (2026-11-18)

Four handover rules that protect quality under the worker lifetime cap. A fresh worker loses its predecessor's working memory; these keep what matters.

- **Soft cap**: at about 80% of the context or call limit, a worker starts no new unit. It finishes the current one to a green check and a commit, then ends. The cap itself is only the backstop. `usage_guard.py --threads` marks such workers `NEAR` (`--soft` sets the fraction).
- **Read first**: the handoff, now updated at every unit end, names the files the next worker should read first, with line ranges.
- **Successor check**: the fresh worker restates the goal, runs the quick check on the batch branch, and confirms its predecessor's claims on the real artifact before building on them.
- **Committed repro**: a bug-fix batch commits its failing test or repro script early on the batch branch, so a successor starts from the same repro.

## 0.7.1 (2026-11-18)

Fixes to the worker lifetime rule from 0.7.0.

- Wall time no longer ends a worker. Waiting for the lock or a 45-minute check adds no context, so the limit is now about 150 of the worker's own tool calls, with one long wait counting as one call.
- Before it ends, a worker commits its work as `wip:` on the batch branch, and its handoff gains two lines: what it tried and ruled out, and, for bug-fix and investigation batches, the open hypotheses.
- Bug-fix and investigation batches get a 250k-token cap instead of 150k, because their value lies in the hypotheses they have built up.
- `usage_guard.py --threads` lists each live Codex thread with its current context and call count, and marks threads over `--cap`, so the lead retires workers on a measured number. Activity comes from the newest log row, not the file's modified time, which Windows can leave stale while Codex keeps the log open. Worker unit messages carry their call count for tools without such a record.
- CI turns failing tests into error annotations (`.github/scripts/annotate_failures.py`). Job logs need a signed-in browser; annotations can be read from the public API.

## 0.7.0 (2026-11-18)

Usage rules, after a day on which a parallel builder used 28% of a weekly Codex window in eight hours. The skill text itself was 3–4% of that; the rest came from long-lived workers whose contexts reached 300k to 450k tokens, and from 658 messages between agents, each of which costs a call to send and a call to wake the receiver.

- **Worker lifetime** (`builder.md` token rule 8): a worker ends when its batch is integrated, when its context passes 150k tokens, or after about an hour, and hands the rest to a fresh worker through its handoff. The lead renews itself the same way, through Pause and Resume.
- **Message budget** (token rule 9): one message per unit, at its end, carrying the handoff path and `DONE`, `BLOCKED` or `NEEDS_DECISION`. Progress and requests go into the handoff file; the lead does not ask workers for status.
- **Usage guard** (token rule 10, new `scripts/usage_guard.py`): before every fan-out and at every integration, the lead checks the usage left. Below 30% it runs one worker; below 10% it pauses, and Pause now names the usage guard as a trigger. The script reads Codex's own rate-limit record; for other tools it takes `--left <percent>` from the operator.
- The `0_RULES` templates carry the lifetime cap and the thresholds; the kickoff and the batch contract in `layers.md` carry the budget. Six new tests cover the guard.

## 0.6.0 (2026-11-18)

- trio now ships as a plain skill at `skills/trio-workflow/`, the standard layout for skill repositories. The skill's content is unchanged apart from one install line in `bootstrap.md`.
- Install with `npx skills add yuson95/trio-workflow -g -a claude-code -a codex -y --copy`, or without Node.js with `tools/install_local.py`. Existing `npx skills` installs keep updating with `npx skills update -g`, which finds the skill at its new path.
- The version now lives in `SKILL.md` as `metadata.version`, next to `license: MIT`. The skill folder carries the MIT `LICENSE`, so every installed copy keeps the notice.
- The README now covers install, the files inside the skill, the two layers, delivery modes and credits. The self-checks also guard that the repository holds exactly one `SKILL.md`.

## 0.5.0 (2026-11-17)

- Smaller always-loaded footprint: the skill description went from 734 to 429 characters, and `SKILL.md` from 115 to 96 lines, with every rule kept. Section numbers, file names and the `builder.md` sections that running plans refer to are unchanged.
- Added `scripts/bootstrap_handoff.py` and the templates in `templates/en` and `templates/zh`. One command now creates `00_START_HERE`, `00_FLOW`, `0_RULES` and `PROMPTS` with the project's names filled in, and never overwrites. `bootstrap.md` went from 152 to 55 lines.
- Added repository self-checks (`tests/test_repo.py`). They cover version agreement between the manifests and the changelog, marketplace targets, links, the size limits on the description and `SKILL.md`, unreachable branch files or scripts, template parity between languages, and the shipped license. The suite has 30 tests.

## 0.4.3 (2026-11-17)

- Documented npx mode: `npx skills add yuson95/trio-workflow -g -a claude-code -a codex -y --copy`, using Vercel's open `skills` installer, which finds trio's skill unchanged. The full cycle (list, install, check, update, remove) was tested in an isolated home with telemetry off. The installed files match the repository byte for byte.

## 0.4.2 (2026-11-17)

- The marketplace is now named `trio`; it was `trio-local`. Install with `claude plugin marketplace add yuson95/trio-workflow`, then `claude plugin install trio-workflow@trio`.
- The install instructions in both quickstart guides and the README lead with the plugin; copy mode remains for Codex, Cursor and several tools at once.
- The README states when trio fits (expertise, or an idea still taking shape) and its premise: you stay in charge at the key moments. The audience wording is broader and gentler. PR mode is described as optional everywhere, including the plate legend.
- Added installer tests and a GitHub Actions workflow that runs all tests on Linux and Windows with Python 3.10 and 3.13. The stated minimum is now Python 3.10.

## 0.4.1 (2026-11-16)

- Released under the MIT License; the repository is public at https://github.com/yuson95/trio-workflow.
- Manifests list the license, homepage and repository; the plugin README shows how to clone the repository or add the marketplace from GitHub.

## 0.4.0 (2026-11-16)

- Added `prs.md` and the `Delivery: local / pr` setting. In `pr` mode, every batch is a pull request into `wip/<plan>` with CI and a verifier's verdict. Stops stay the plan-level gates for independent review and the operator's decisions, and a plan PR carries `wip/<plan>` into `main` after the final stop.
- Bootstrap, builder, review, merge and layers point to PR mode. pstack's "Opening a PR" becomes the batch PR in `pr` mode.

## Docs (2026-11-16)

- The README opens with the audience, in English and Chinese, and adds an "About the author" section.
- Redrew the plate as a metro map. Roles are lines, actions are stations, and stops are interchanges. Batch PRs sit on worker tracks. The script now also fails on overlapping labels.
- Added "Who it's for" and a quickstart to the README, plus step-by-step guides for non-programmers in English (`docs/QUICKSTART.md`) and Chinese (`docs/QUICKSTART_zh.md`).
- Redrew the workflow plate: content-sized cards, stop columns marked, heavier arrows, one-line file row.
- Added the workflow plate, a swimlane flowchart of one plan end to end, in English and Chinese, as PNG and PDF.
- `docs/workflow/draw_workflow.py` redraws the plate and fails when a caption overflows its cell.

## 0.3.0 (2026-11-16)

- Added `ui-acceptance.md`: prototypes before code for review-gated requirements, a page × state screenshot matrix, a visual review before the operator walks through, and walkthrough findings classed and routed into structure.
- `check_plan.py` reports review-gated requirements without a prototype (`Prototype:` / `原型：`).
- Added `screenshot_sheet.py` with tests; new principle "Look at the page".
- Planning, review, builder, merge and bootstrap now point to the UI acceptance steps.

## 0.2.0 (2026-11-16)

- Packaged as a plugin. One shared `skills/` folder, with manifests for:
  - Claude Code, plus the local marketplace `trio-local`;
  - Codex, plus the local marketplace `trio-local`;
  - Cursor;
  - generic agents.
- Added `layers.md`, which defines two layers: trio is the outer layer and pstack, or the built-in rules, is the inner layer. It covers:
  - the batch contract;
  - the playbook mapping by batch type;
  - the reviewer-side pstack tools;
  - the pstack steps that change under trio;
  - the rule precedence.
- Plans tag every requirement with a type, which selects the inner playbook.
- Added three scripts with behavior tests:
  - `heavy_lock.py`: a machine-wide lock for heavy checks;
  - `log_decision.py`: appends to the decision trail;
  - `check_plan.py`: checks a plan's structure, in English or Chinese.
- Added `tools/install_local.py` for copy-mode installs.

## 0.1.0 (2026-11-16)

- The first version of the skill, in English and not tied to one tool:
  - roles: operator, reviewer and builder;
  - stops and independent verdicts;
  - the parallel design, plus 18 principles adapted in part from pstack;
  - session pickup and safe pause;
  - token rules.
