# Changelog

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
