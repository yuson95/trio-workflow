# Changelog

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
