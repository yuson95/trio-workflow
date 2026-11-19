# Project rules · {{project}}

Generic process, parallel and token rules live in the trio-workflow skill (`builder.md`). Only project-specific rules belong here; they win over the skill when the two conflict.

1. **Roles**: Reviewer = {{reviewer}}; Builder = {{builder}}; same model family: {{same_family}}.
   - Inner layer: built-in (or `pstack`, installed in <tools>).
   - Skill: {{skill_dir}}. If your tool's skill list does not show it, read `SKILL.md` and `builder.md` there.
2. **Baseline and branches**: a new worktree on a short path outside the repo and a local branch from current `main`; integration branch `wip/<plan>`; remote policy: <main plus release branches>.
   - Delivery: {{delivery}}. In `pr` mode: forge, CI tiers per PR, standing authorization for the builder and the reviewer.
3. **Checks**: quick command <…>; full command <…> and its duration; report summary lines only; a missing environment is `NOT_RUN`.
   - Heavy checks run one at a time under the lock `{{lock}}` (`scripts/heavy_lock.py`). A run with no output for 30 minutes is stopped and the lock released (`--idle-minutes`; `--watch <log>` for commands that write their own log).
   - Final stop: discovery checks run early; acceptance checks (regression gate, recomputation, first-save replay, release build, screenshot matrix, full check) run once on the frozen candidate, each with the SHA it ran on.
4. **Verification recipe**: path to Launch / Doctor / Drive / Evidence / Cleanup and the feature map: <…>.
5. **Data and isolation**: data root <…>; isolated instance command <own port, own projects folder>; the operator's service: {{service}} (never touch it).
6. **Parallel**: worker cap 3; hotspot files: <…>.
   - Batches sized for about 100 tool calls each, split by module, test group or about 20 list items.
   - Worker lifetime: one batch, at most about 150 tool calls (waiting does not count) or the context cap (Codex 150k, Claude Code 350k; bug-fix and investigation batches 225 calls and 250k / 500k). At 80% a worker starts no new unit.
   - Usage (`scripts/usage_guard.py`): one worker below 30% left; pause below 10% left.
7. **UI conventions document**: <path>.
8. **Project-specific rules**: formatting, provenance, path rules, guard tests.
9. **Known issues**.
