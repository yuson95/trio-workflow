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
   - the requirement IDs, their invariants, and the plan sections for this batch;
   - the batch type and the inner playbook, from [layers.md](layers.md);
   - the files the worker may write (its owned files), and the files it must leave alone. A batch that reverses an existing behavior owns every test line and contract case that asserts the old behavior: rerun the census from the plan or request (planning.md A step 5) on the integration head first, since later batches may have added assertions. Code and tests that must change together go to one batch;
   - forbidden actions: push, merge into `main`, touching the operator's service or client data;
   - the evidence that proves done: commands with their expected output, live scenarios from the verification recipe, screenshots;
   - the previous handoff;
   - the lifetime cap and the message budget (token rules 8 and 9).

   If you cannot name the evidence, the batch is not scoped yet. The worker starts by restating its goal, owned files and untouched files at the top of its handoff.
4. **Start with one unit.** Take the first batch all the way through (kickoff, worker, verification, integration) before fanning out. A flawed kickoff then costs one worker instead of many.
5. **Run in parallel by the plan's table.**
   - Start batches that have no dependency and no overlapping owned files together, up to the cap in `0_RULES` (default 3).
   - Check usage before every fan-out and at every integration, and follow the verdict (token rule 10).
   - Each worker gets its own worktree on a short path outside the repo, and its own local branch.
   - One writer per file. A worker that needs another batch's file writes the request into its handoff, and the owner makes the change.
   - Heavy checks (full check, solver tests, browser suites, screenshot runs, timing runs, load reproduction) run one at a time, across every session on the machine, under the lock file named in `0_RULES`: `python <skill dir>/scripts/heavy_lock.py --lock <path> run --owner <session> --wait 7200 -- <command>`. Each run holds the lock alone, even against its own owner; commands that must run under one hold go into one steps file.
     - **Workers leave the waiting to the lead.** A worker runs a heavy check with `--wait 0`. When the lock is busy (exit 3), it writes the runs into `batch-notes/<batch>_heavy-steps.json` (command, log, expected summary lines; see `heavy_lock.py --help`), checks the file with `run-steps --dry-run`, and hands back `NEEDS_HEAVY_RUN` with the path. The lead runs the files in one queue at integration: `heavy_lock.py --lock <path> run-steps --owner <lead> --steps <file> --wait 7200`, reading only the `STEP` summary lines. A failed step goes to a fix worker with its log path.
     - A hung run must not hold the lock. `run` stops the command's whole process tree and releases the lock after 30 minutes without output, and exits 124. A command that writes to its own log file gets `--watch <log>`, so the log's growth counts as output. For a command that is legitimately quiet for longer, raise `--idle-minutes`; never turn it off for browser or screenshot runs.
     - An idle stop is a failed run: record it as `NOT_RUN` with the reason, find what hung, and rerun.
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
9. **Verify in two passes.** A check either finds defects or proves the candidate the reviewer will see. A proof run before the code stops changing has to run again, so the two kinds run at different times.
   - **Discovery pass**, early: as soon as the batches that change a page or a form are integrated, and before any walkthrough in the middle of the plan:
     - capture the screenshot matrix and run the visual review ([ui-acceptance.md](ui-acceptance.md) §2–3);
     - replay the first save of each new or changed form;
     - run the regression gate once, so breaks surface while batches are still open.

     Fix the findings in normal batches. These results guide the work; they are not stop evidence.
   - **Freeze**: once every batch for the stop is integrated, the discovery fixes and the handoff doc included, record the candidate SHA in the progress file and add a `decision` row "freeze <sha>". After the freeze, only fixes for findings of the acceptance pass or the walkthrough go in.
   - **Acceptance pass**, once per stop, on the frozen candidate:
     - the checks the plan lists for the stop; at the final stop, the regression gate and every independent recomputation, first-save replay and release build the plan or the stop-1 `RESULT` asks for;
     - for a stop that changes UI, the screenshot matrix and the contact sheet (ui-acceptance §2), the visual review of the new captures (§3), and the isolated instance for the walkthrough, with one prepared synthetic project per state (own port, own projects directory). Give the operator the address, the page list in walking order and the contact sheet (§4).

     Each result names the SHA it ran on.
   - **A fix after the freeze** makes a new candidate SHA. Rerun every acceptance check that covers a file the fix changed. A result from the earlier SHA stays valid only where the stop material says why the fix cannot affect it. Fix what the walkthrough finds before the stop.
10. **At a stop**:
    - run the full check last, on the final candidate SHA, in a quiet environment, under the lock;
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

## Pause (on an explicit pause, going offline, an imminent context limit, or a `PAUSE` from the usage guard)

1. Finish the current atomic step or back out of it. Start nothing new, and stop running workers.
2. Take no irreversible action to pause.
3. Commit uncommitted edits as one `wip:` commit on the current branch. If the tree is broken, say so in one line of the commit body.
4. Update the progress file as the resume note: intent, progress, what is verified, current state, next steps, key files and gotchas. Point to the decision trail rather than duplicating it.
5. Add a `pause` row to the decision trail with the reason. For a usage pause, tell the operator in one line how much is left and when the window resets.

"Keep going" never triggers a pause.

## Token rules

Every model call resends the whole context of the agent that makes it. A call at 400k tokens of context costs about twice one at 200k, and a message costs two calls: one to send, one to wake the receiver. Rules 8 to 10 keep contexts small and calls few.

1. One lead session per plan. When the lead's own context passes the cap for its tool in rule 8, it pauses and continues in a fresh session through Resume. When the builder tool changes mid-plan, update the caps in `0_RULES` to the new tool's row. Where the lead cannot open a session itself, it writes the resume prompt into the progress file and asks the operator once: a fresh session, or continue here. Workers are disposable; the lead keeps only handoffs and summaries.
2. A batch handoff is at most 30 lines and is saved as `batch-notes/<batch>_HANDOFF.md`. The next worker reads only that handoff.
3. The progress file is at most 60 lines. After compaction or a break, read it first.
4. Read `CURRENT_STATUS.md` first; open history files by name, only when needed.
5. The quick check selects tests by changed paths. Report summary lines only; on failure, report only the test names and a few assertion lines.
6. Write logs to files and report their paths. Read only the plan sections for this batch.
7. Searches respect `.ignore`. Never read single-line giant files whole.
8. **Worker lifetime.** A worker ends at the first of these:
   - its batch is integrated;
   - about 150 of its own tool calls. Wall time does not count, but a long wait costs as many calls as the tool needs to keep waiting (in Claude Code a command waits at most ten minutes), which is why heavy runs go back to the lead (step 5);
   - its context passes the cap in `0_RULES`. Context grows at different rates per tool, so the defaults differ:

     | Builder tool | Context cap | Bug-fix or investigation batch |
     | --- | --- | --- |
     | Codex (starts near 30k, grows about 0.4k per call) | 150k | 250k |
     | Claude Code (starts near 60k, grows about 1.8k per call) | 350k | 500k |

     Bug-fix and investigation batches also get about 225 calls, because their value lies in the hypotheses they have built up. Where the lead cannot read a worker's context (Claude Code sub-agents), the call count governs and the context cap is the backstop.

   **Soft cap.** At about 80% of either limit, the worker starts no new unit. It finishes the current one to a green check and a commit, then ends. The cap itself is only the backstop: a worker that passes it mid-unit commits `wip:` on the batch branch and ends.

   The lead reads each worker's context with `usage_guard.py --threads` where the tool records it (Codex): `NEAR` marks the soft cap, `OVER` the cap. Elsewhere it goes by the call count in the worker's unit messages.

   **Handover.** The worker updates its handoff at every unit end, so ending at any point loses at most one unit. The handoff names:
   - what was tried and ruled out;
   - the files the next worker should read first, with line ranges;
   - the last quick-check log and the commit it ran on;
   - for a bug fix or an investigation, the open hypotheses and the committed repro (a failing test or script, added early on the batch branch).

   **Successor.** The rest of the batch goes to a fresh worker. It reads the handoff and the read-first files, and restates the goal. If the branch head is the commit of the handoff's quick-check log, it reuses that log; otherwise it runs the quick check. Then it confirms the predecessor's claims with targeted checks on the real artifact before building on them. It does not repeat what the handoff rules out.

   **Batch size.** Size each batch so one worker finishes it in about 100 tool calls, well inside the limit. Split by module or test group, or by about 20 items of a list; never by theme alone ("fix every failure", "cover every endpoint"). A batch that needs a successor was cut too large: split what remains before handing it on, so each successor gets a batch it can finish. Never keep a worker alive to save its context.
9. **Message budget.** A worker sends the lead one message per unit, when the unit ends: the handoff path, one status (`DONE`, `BLOCKED`, `NEEDS_DECISION` or `NEEDS_HEAVY_RUN`) and its tool-call count so far. It sends nothing in between.
   - A worker whose tool refuses to write its handoff file (Claude Code sub-agents may not write report files) puts the full handoff text in that one message. The lead saves it unchanged and adds a last line saying so.
   - Progress goes into the handoff file.
   - Requests to another batch's owner go into the handoff's request list; the lead passes them on at integration.
   - The lead does not ask workers for status. It reads their handoff files and commits.
10. **Usage.** Use each usage window fully and stop cleanly. What is left when a window resets expires, so holding back only moves work later. Before every fan-out and at every integration, run `python <skill dir>/scripts/usage_guard.py` with the thresholds in `0_RULES` (default: full speed until 3% left, then pause).
    - `FULL`: run up to the worker cap. Defer no batch and narrow no fan-out to wait for a reset.
    - `PAUSE`: follow Pause, and resume after the reset. A window that runs out mid-unit costs at most that unit, because handoffs are updated at every unit end.
    - `ONE_WORKER` (one batch at a time) comes only from a reserve band that `0_RULES` sets with `--reduce-below`, for example to keep quota for a reviewer who shares the window before a stop. With `--resets-in` the band is waived within 24 hours of the reset (`--near-hours`), since what it would keep expires anyway.
    - Add `--threads` to list each live worker's context. A worker marked `NEAR` finishes its current unit and ends; one marked `OVER` commits `wip:` and ends now (rule 8).
    - Without `--left`, the script reads Codex's own usage record, which says nothing about any other tool. A Claude Code lead in the desktop app reads the plan's windows (5-hour and weekly) with the app's usage tool, takes the smallest percent left, and passes it as `--left`, with the hours until that window resets as `--resets-in`. For other tools, pass the numbers the operator reads from the tool's usage page. If no number is available, write "usage unknown" in the progress file and keep to one worker.

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
- Invariant breaks: <invariant → edited file:line → test that went red; reverted> / none
- Requests for other owners' files:
- Tried and ruled out: <approach → why it failed, one line each>
- Read first: <file:line ranges the next worker needs, at most 8>
- Last quick check: <log path> @ <commit>, <summary line>
- Open hypotheses and repro (bug fix, investigation):
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
- Frozen candidate @ <sha>; fixes after the freeze: <sha, files, which checks reran> / none
## 1. Goal (restated)
## 2. Requirement IDs and status (implemented and verified / implemented, not verified / not done or limited); for each invariant, the handoff with its break record
## 3. Checks, each PASS / FAIL / NOT_RUN, with the SHA it ran on, summary lines and log paths
## 4. Live evidence (scenario → screenshot or output → pass/fail)
## 5. Main changed files
## 6. Operator's direct requests (dates)
## 7. Questions settled by default
## 8. Decisions for the operator (with defaults)
## 9. Screenshot sheet and visual review (path; states not reachable and why; findings fixed; same-family or cross-family)
## 10. Attention (optional cross-model scan of the decision trail)
## 11. Walkthrough address and page list
```
