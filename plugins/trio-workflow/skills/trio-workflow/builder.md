# Builder

Role: Builder. The lead coordinates, integrates and reports, and never writes the feature code itself. Each batch goes to a fresh worker. The operator steps in only at the plan's stops.

**A tool without workers** (some bots or chat agents cannot spawn sub-agents) runs the same steps on its own:

- take batches one at a time, in the dependency order;
- write each kickoff as a checklist at the top of the batch's handoff before starting it;
- start a new session per batch when the tool allows it;
- record in the stop material that no separate verifier ran, so the reviewer's live checks carry that weight.

## Steps

1. **Opening checks** (read-only):
   - `git log -1` confirms the baseline;
   - environment variables and the data root are readable;
   - the check script and the verification recipe run;
   - read `0_RULES`, the plan's general sections, earlier plans' handoff docs, `AGENTS.md` and `CURRENT_STATUS.md`. If an earlier plan's handoff doc is missing, stop and tell the operator; usually that plan has not merged yet.

   Write the results into the stop-1 material and the decision trail.
2. **Restate**: open the progress file with the operator's goal in your own words. Every worker kickoff repeats it.
3. **Kick off each batch** with a fresh worker. The kickoff contains:
   - the goal, restated;
   - the requirement IDs and plan sections for this batch;
   - the batch type and the inner playbook, from [layers.md](layers.md);
   - the files the worker may write (its owned files), and the files it must leave alone;
   - forbidden actions: push, merge into `main`, touching the operator's service or client data;
   - the evidence that proves done: commands with their expected output, live scenarios from the verification recipe, screenshots;
   - the previous handoff.

   If you cannot name the evidence, the batch is not scoped yet. The worker starts by restating its goal, owned files and untouched files at the top of its handoff.
4. **Start with one unit.** Take the first batch all the way through (kickoff, worker, verification, integration) before fanning out. A flawed kickoff then costs one worker instead of many.
5. **Run in parallel by the plan's table.**
   - Start batches that have no dependency and no overlapping owned files together, up to the cap in `0_RULES` (default 3).
   - Each worker gets its own worktree on a short path outside the repo, and its own local branch.
   - One writer per file. A worker that needs another batch's file writes the request into its handoff, and the owner makes the change.
   - Heavy checks (full check, solver tests, browser suites, timing runs, load reproduction) run one at a time, across every session on the machine, under the lock file named in `0_RULES`: `python <skill dir>/scripts/heavy_lock.py --lock <path> run --owner <session> --wait 7200 -- <command>`.
6. **Integrate each batch**:
   - **Ownership check**: compare the changed files with the batch's owned files and the append-only list.
     - A change outside them is taken out of the batch and passed to the owner as a request.
     - Log a `violation` row in the decision trail.
     - A fresh worker redoes anything the removal broke; this does not count as a retry.
   - A verifier that did not write the code runs the quick check and the batch's tests, and drives the batch's live scenarios.
   - Read the diff and the evidence, not the worker's summary.
   - Then merge into `wip/<plan>`, update the progress file and the decision trail, and start the next batch.
   - In `pr` delivery mode, all of this happens through one batch PR into `wip/<plan>`: draft PR, CI on every push, the verifier's verdict on the PR, then a squash merge (see [prs.md](prs.md)).

   Parallel batches merge in the order they finish. The later batch resolves conflicts, reruns the quick check and records the conflicting files and the resolution in its handoff.
7. **Handle stalls by cause**: a smaller scope after a context or memory limit; the same kickoff after a dropped connection; a different model after a tool error. After two retries, drop the unit, replan around it and report it at the next stop. Judge a worker by its commits and outputs, not by its status text.
8. **Keep moving between stops.**
   - A question that changes business meaning: proceed on the plan's default or the most conservative choice, log it, and report it at the next stop.
   - Stop early only for a blocker that halts all remaining work.
   - Requests the operator gives you directly: do them, and mark them "operator's direct request" with the date in the stop material.
9. **Before any walkthrough and before the final stop**, follow [ui-acceptance.md](ui-acceptance.md):
   - capture the screenshot matrix for every changed page and state, on `main` and on the candidate, and build the contact sheet with `scripts/screenshot_sheet.py` (§2);
   - run the visual review and fix its findings, then recapture (§3);
   - start an isolated instance from the candidate with one prepared synthetic project per state (own port, own projects directory). Give the operator the address, the page list in walking order and the contact sheet (§4);
   - fix what the walkthrough finds before the stop.
10. **At a stop**:
    - run the full check in a quiet environment, under the lock;
    - at the final stop, also run the regression gate and commit the handoff doc to the wip branch;
    - optionally, ask a different model family to scan the decision trail and list what the operator should look at;
    - write the stop material from the template, then reply with one line, "Reached stop N, material at <path>", and stop.
11. **On "Review result at …RESULT.md"**: fix by ID on the same branch. Write a fix note per ID (what changed, how it was verified), then continue or stop for the re-review, as the RESULT says.

Boundaries: pushing, merging into `main` and GitHub actions belong to the operator. Tests and live checks use synthetic data only; the operator's service port and client project folders stay untouched. Commits carry no AI attribution lines.

## Resume (session pickup)

Use this when the operator pastes the resume prompt or says "continue <plan>". It replaces step 1. Run only these opening checks: `git log -1` and the lock. The earlier handoff docs were confirmed at the start and are recorded in the progress file.

1. **Read** `0_RULES`, the progress file, the last handoff, and the tail of the decision trail. The trail is authoritative. Do not re-derive it, and do not redo finished work.
   - If the progress file or the trail is missing or damaged, rebuild it from `git log` of the batch branches and the handoff files, and say so in the `start` row.
2. **Reconcile with git, which wins**:
   - check `git worktree list`, the batch branches, the head of `wip/<plan>`, and the uncommitted changes in each worktree;
   - where the progress file disagrees with git, correct the progress file first;
   - add a `start` row to the decision trail that names this new session.
3. **Unfinished batch**: give it to a fresh worker to inspect.
   - The changed files are within the batch's owned files and the quick check passes on that worktree: continue the batch.
   - Otherwise: commit the uncommitted work as `wip:` on the batch branch, record that SHA in the trail, then reset the batch to its last good commit and redo it. Nothing is lost.
4. **Leftovers**: stop only the instances and processes the previous session started. The progress file's "Running instances" line lists their ports and run directories. Confirm that no other heavy check holds the lock before you start one.
5. **Verify inherited claims** on the real artifact before you build on them. A passing self-report from the previous session is not proof.
6. Continue from step 3 of the main steps. Step 4 (start with one unit) applies only if no batch has been integrated yet.

## Pause (on an explicit pause, going offline, or an imminent context limit)

1. Finish the current atomic step or back out of it. Start nothing new, and stop running workers.
2. Take no irreversible action to pause.
3. Commit uncommitted edits as one `wip:` commit on the current branch. If the tree is broken, say so in one line of the commit body.
4. Update the progress file as the resume note: intent, progress, what is verified, current state, next steps, key files and gotchas. Point to the decision trail rather than duplicating it.

"Keep going" never triggers a pause.

## Token rules

1. One session per plan. Workers are disposable; the lead keeps only handoffs and summaries.
2. A batch handoff is at most 30 lines and is saved as `batch-notes/<batch>_HANDOFF.md`. The next worker reads only that handoff.
3. The progress file is at most 60 lines. After compaction or a break, read it first.
4. Read `CURRENT_STATUS.md` first; open history files by name, only when needed.
5. The quick check selects tests by changed paths. Report summary lines only; on failure, report only the test names and a few assertion lines.
6. Write logs to files and report their paths. Read only the plan sections for this batch.
7. Searches respect `.ignore`. Never read single-line giant files whole.

## Templates

### Progress `<KEY>_PROGRESS.md` (at most 60 lines)

```markdown
# <plan> progress (updated <time>)
Goal (restated): <one or two sentences>
- Baseline main @ <sha>; integration wip/<key> @ <sha>
- Now: <batch>, <state>; next: <…>
| Batch | IDs | State | Owned files | Commit | Handoff |
- Running instances: <port, run directory, started by which session> / none
- For the next stop: <questions decided by default>
```

### Batch handoff `<batch>_HANDOFF.md` (at most 30 lines)

```markdown
# <batch> handoff
Restatement: <goal, owned files, untouched files; 3–5 sentences>
- IDs and status:
- Commits and branch:
- Evidence: <commands and summary lines; live scenarios and screenshot paths>
- Requests for other owners' files:
- Open issues:
- Interface or contract changes the next batch must know:
```

### Decision trail `<KEY>_DECISIONS.tsv` (append-only)

```text
ts	phase	decision	why	evidence	result
```

One row per fork, pivot, unit result, blocker or retry. Keep each cell to one line. Evidence is a pointer (SHA, path, `file:line`), never prose. A wrong row gets a new row that supersedes it; history is never edited.

`phase` takes one of these values: `start` (a new session), `opening`, `kickoff`, `unit`, `integrate`, `decision`, `retry`, `violation`, `blocker`, `stop`, `fix`, `pause`.

Append with `python <skill dir>/scripts/log_decision.py <file> <phase> <decision> <why> <evidence> <result>`. It stamps the time, writes the header on first use, keeps each cell to one line and rejects unknown phases.

### Stop material `REVIEW_<key>_stop<N>.md`

```markdown
# <plan> stop N material
- Integration wip/<key> @ <sha>; base main @ <sha>
## 1. Goal (restated)
## 2. Requirement IDs and status (implemented and verified / implemented, not verified / not done or limited)
## 3. Checks, each PASS / FAIL / NOT_RUN, with summary lines and log paths
## 4. Live evidence (scenario → screenshot or output → pass/fail)
## 5. Main changed files
## 6. Operator's direct requests (dates)
## 7. Questions settled by default
## 8. Decisions for the operator (with defaults)
## 9. Screenshot sheet and visual review (path; states not reachable and why; findings fixed; same-family or cross-family)
## 10. Attention (optional cross-model scan of the decision trail)
## 11. Walkthrough address and page list
```
