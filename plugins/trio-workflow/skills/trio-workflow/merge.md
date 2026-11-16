# Merge and clean up

Role: Reviewer, or whichever agent the operator authorizes. Act only on the operator's own words: "合并并推送" (merge and push), "只合并不推送" (merge only) or "做收尾" (clean up).

## Merge

1. **Confirm it may land.** The `RESULT` reads `PASS` or `PASS+NOTES` (for a small change, the "看一下小改" conclusion). If not, stop and tell the operator what is missing.
2. **Confirm the verdict still describes the code.** Compare `git patch-id` at the verdict SHA with the candidate head. A different patch needs a fresh check of what changed.
3. **Pre-merge checks**:
   - `main` equals `origin/main`;
   - the candidate descends from `main`;
   - the main checkout has no uncommitted changes;
   - the pre-merge recheck follows the check tiers in [review.md](review.md).
4. **Merge**, fast-forward only (`merge --ff-only`). In `pr` delivery mode, merge the plan PR instead and read it back as merged (see [prs.md](prs.md)). Push only on "合并并推送", then read the result back with `ls-remote`. A command's success message is not proof. Commits and PR text carry no AI attribution lines.
5. **Restart the operator's service**:
   - confirm no computation is running;
   - restart it with the project's method;
   - confirm the new process started after the merge and serves the new code.

   Page files can update while the backend still runs old code; then the operator sees "new page, old API".
6. **Update** `00_FLOW` §0 with the new `main` SHA, the current step and the next step. Text the operator must forward to other lines also goes into the flow file.

## Clean up (end of a plan, or "做收尾")

1. **List** the worktrees, local branches, temporary instances and remote branches to delete, and the GitHub items to close. Record each item's SHA or number in `batch-notes/CLEANUP_<date>.md`. Act after the operator's OK.
2. **Before deleting**:
   - find directory junctions and remove them without following them;
   - confirm the worktree is clean;
   - stop services whose working directory is inside it;
   - remove only what this project's runs created.

   Prefer the recycle bin. Delete branches against their recorded SHA so nothing else is removed by mistake.
3. **Retro.** Turn every lesson that came up twice in this plan into a test, check, script or lock (encode lessons in structure). Record it in `00_FLOW`'s open items and schedule it into a later plan. Check the walkthrough notes: every finding classed as a convention breach, a spec gap or a bug has its structural fix landed or scheduled (see [ui-acceptance.md](ui-acceptance.md) §4).
4. **Memory.** Keep only facts with lasting value: the `main` SHA, new conventions, the operator's decisions.
