# Project rules · {{project}}

Generic process, parallel and token rules live in the trio-workflow skill (`builder.md`). Only project-specific rules belong here; they win over the skill when the two conflict.

1. **Roles**: Reviewer = {{reviewer}}; Builder = {{builder}}; same model family: {{same_family}}.
   - Inner layer: built-in (or `pstack`, installed in <tools>).
   - Skill: {{skill_dir}}. If your tool's skill list does not show it, read `SKILL.md` and `builder.md` there.
2. **Baseline and branches**: a new worktree on a short path outside the repo and a local branch from current `main`; integration branch `wip/<plan>`; remote policy: <main plus release branches>.
   - Delivery: {{delivery}}. In `pr` mode: forge, CI tiers per PR, standing authorization for the builder and the reviewer.
3. **Checks**: quick command <…>; full command <…> and its duration; report summary lines only; a missing environment is `NOT_RUN`.
   - Heavy checks run one at a time under the lock `{{lock}}` (`scripts/heavy_lock.py`).
4. **Verification recipe**: path to Launch / Doctor / Drive / Evidence / Cleanup and the feature map: <…>.
5. **Data and isolation**: data root <…>; isolated instance command <own port, own projects folder>; the operator's service: {{service}} (never touch it).
6. **Parallel**: worker cap 3; hotspot files: <…>.
   - Worker lifetime: one batch, at most 150k tokens of context (250k for bug-fix and investigation batches) or about 150 tool calls; waiting does not count. At 80% a worker starts no new unit.
   - Usage (`scripts/usage_guard.py`): one worker below 30% left; pause below 10% left.
7. **UI conventions document**: <path>.
8. **Project-specific rules**: formatting, provenance, path rules, guard tests.
9. **Known issues**.
