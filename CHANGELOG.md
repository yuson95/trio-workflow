# Changelog

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
