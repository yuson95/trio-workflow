# Review

Role: Reviewer. A review is worth only what you verify yourself. The builder's receipts miss things, so a review that only reads receipts is not a review. Green checks and the builder's summary are inputs; the verdict comes from your own runs.

## Independence

- **Never verify your own code.** An author checks what it meant to build, not what it built.
- **Use a different model family when you can.** When reviewer and builder share a family (two Codex sessions, two Claude sessions):
  - review in a fresh session that holds no build context;
  - read the diff and the evidence, never the builder's summary alone;
  - run the adversarial pass at every stop;
  - for a contested finding or design, get a second opinion with the same prompt on another model if one is available. Agreement across families is a strong signal.
- **State your independence in the `RESULT` header**: your agent and model, whether the session is fresh, and whether a second opinion was obtained. If any same-family safeguard was missing, the verdict is at most `PASS+NOTES`, and the notes say which safeguard.

## Branches

| Operator says | Do |
| --- | --- |
| "审查<plan>停点N", "审查<request>" | A. Stop review |
| "复审" | B. Re-review |
| "看一下设计" | C. Design review |
| "看一下小改" | D. Small-change review |

## A. Stop review

Use the material path the operator gives. The `RESULT` file sits next to it, with the same name plus `_RESULT`.

**Plan and contract stops** (usually stop 1, before business code exists) replace step 3 with these checks:

- every requirement ID lands in a batch and has a checkable "You see" line;
- every requirement that computes numbers or changes stored state names its invariants with their tests, and every new blocking check names the harm it prevents ([planning.md](planning.md) A step 5);
- the contracts (data shapes, interfaces, storage migration, page flow) match the current code; spot-check the key pointers;
- the ownership table is complete and each hotspot has one owner;
- the probe and prototype conclusions hold;
- every review-gated requirement has a prototype, and the operator has confirmed it or picked a variant;
- the builder's opening checks are sound.

Run only the quick check when the code is identical to `main`. The other steps stay the same; findings follow "Before code exists" under [Writing findings](#writing-findings).

**Stops after a data migration** add two checks:

- every item listed in `DESIGN_*_REVIEW.md` for that migration;
- upgrade and rollback on a synthetic copy of each old storage version the operator still has.

1. **Read**:
   - the stop material, the progress file and the batch handoffs for this stop;
   - every earlier `RESULT` of this plan, so open items carry over;
   - this line's constraints and the operator's direct requests in `00_FLOW`;
   - the candidate's diff against its base: `--stat` first, then single files;
   - in `pr` delivery mode, the batch PRs merged since the last stop, with their verdicts and CI links (see [prs.md](prs.md)).
2. **Check the material**:
   - every requirement ID has a status;
   - every check reads PASS, FAIL or NOT_RUN;
   - every acceptance result names the SHA it ran on. A result from an SHA older than the candidate needs the material's reason why the later fixes cannot affect it; otherwise treat it as `NOT_RUN` ([builder.md](builder.md) step 9);
   - the operator's direct requests carry dates;
   - the decision trail is sound: rows match real actions, evidence pointers resolve, forks and pivots are logged.

   Where the work differs from the request, first ask whether the operator asked for it directly, then judge whether it is a deviation.
3. **Verify independently**, as hard as the check tiers below require:
   - **Full check**: rerun it in a separate review worktree (`git worktree add --detach <short path outside the repo> <candidate sha>`), in a quiet environment: no browser runs and no large copies meanwhile, and take the heavy-check lock named in `0_RULES` (`scripts/heavy_lock.py ... run --owner <review session> -- <full check command>`). Keep the worktree until the re-review is done and remove it at cleanup.
   - **Live**: start an isolated instance from the candidate with a synthetic copy, following the verification recipe named in `0_RULES`, and drive the changed pages. Never use the operator's service.
   - **Numbers**: cross-check every new number through an independent path (explain the number).
   - **Invariants**: for each invariant the plan names, break the code it guards with one small edit in the review worktree, confirm its test goes red, then revert the edit. A test that stays green is a finding.
   - **Expand**: chart axis order, empty projects, pages opened directly rather than from history, load time with many runs.
   - **Look at the page** for every UI change: open the builder's contact sheet ([ui-acceptance.md](ui-acceptance.md) §2). Run the visual review (§3) yourself when the builder's pass was same-family or missing. Missing states without a written reason count as findings.
4. **Adversarial pass.** Try to break the change against its stated intent. If pstack is installed in your tool, its interrogate skill runs this pass (see [layers.md](layers.md)); the rules below still decide what counts.
   - A finding counts only when a run shows it: a failing test, a repro script, command output or a screenshot, plus the output the intent requires.
   - Drop what you could not reproduce, and record how many findings you dropped and why.
   - Style remarks do not count, unless they break a convention the project encodes.
   - Merge findings that share a root cause.
5. **Give the verdict**: `PASS`, `PASS+NOTES` or `FAIL`, bound to the candidate SHA.
6. **Write the `RESULT`** from the template below.

   Done when every requirement ID and every carried-over item has a conclusion, and the RESULT states what actually ran and what was not verified.
7. **Reply** in the format of SKILL.md §4. List only the decisions (with defaults), and say which RESULT section holds the text for the builder.
8. **Clean up**: update `00_FLOW` (current step, decisions, open items), stop the instances you started, and remove test by-products.

If the operator told the builder "passed" before the review finished, say once, plainly, what is still unverified.

## B. Re-review

- Mark each ID as fixed, not fixed, or not verifiable yet, then run a regression check.
- A verdict applies to one patch, identified by `git patch-id`. Compare the patch-id at the old verdict SHA with the new head's. If they match, the verdict stands; if not, re-verify the changed parts.
- Whether to rerun the full check follows the check tiers: rerun it when the fix touched the backend, the solver or backend tests.
- New problems found during the fix get new IDs in the re-review's `RESULT`.

## C. Design review

Read only the `DESIGN_*.md` and the code it touches. Answer "go ahead" or list the changes; each change follows "Before code exists" under [Writing findings](#writing-findings). Write the items to check at the final stop into `DESIGN_*_REVIEW.md`.

## D. Small-change review

Read only the diff. No live run and no full check. Check three things:

1. the light-path conditions hold (see [planning.md](planning.md));
2. names and formats follow the project's UI conventions (their path is in `0_RULES`);
3. if anything is off, give the operator one paragraph to forward to the builder.

## Check tiers

| Case | Builder runs | Reviewer does |
| --- | --- | --- |
| Plan and contract stop (code identical to `main`) | opening checks, quick check | check the contracts and the ownership table; quick check |
| Stop, or first review of a request | full check | rerun the full check independently, plus live checks and the adversarial pass |
| Frontend-only fix round | quick checks while fixing, full check before stopping | read the builder's full-check log, run the quick check, live checks; rerun the full check only if the backend changed |
| Small change | quick check, all frontend suites, screenshots | read the diff |
| Pre-merge recheck | backend unchanged since the last full pass: quick check plus all frontend suites; otherwise full check | confirm the results, the scope and the patch-id |
| Final stop | full check plus the regression gate | rerun the full check independently |

## Writing findings

- **Before code exists** (plan and contract stops, design reviews): a finding is one of three things: a contradiction with the current code, with its pointer; the output of a probe or prototype you ran; a decision for the operator, with a default. Settle an imagined risk with a probe, or leave it out. Risks imagined about unbuilt code are where review drifts into nitpicking and speculative scope.
- **Each finding**: ID (`<plan prefix>-NN`) and priority (high, medium, low); location; trigger and evidence (the run that shows it); expected; actual; impact; smallest fix direction; acceptance check. Give a direction, not a patch.
- **Three groups**:
  - confirmed defects;
  - risks to verify, written as investigation tasks;
  - optional improvements, listed apart.

## `RESULT` template

```markdown
# <plan> stop N review
- Candidate: <branch> @ <sha>; base: main @ <sha>; date
- Reviewer: <agent/model>; fresh session yes/no; builder's model family same/different; second opinion <model> / none
- Verdict: PASS / PASS+NOTES / FAIL at <sha>

## 1. Scope and what ran
Checks (summary lines, duration, log path); pages driven live; adversarial pass (verified / dropped with reasons); what was not verified.

## 2. Per requirement
| ID | Conclusion | Evidence |

## 3. Carried-over items
| ID | Fixed / not fixed / not verifiable yet |

## 4. Findings
### Confirmed defects
### Risks to verify
### Optional improvements

## 5. Decisions for the operator
| ID | Question | Options | Default |

## 6. Visual review
Contact sheet path; visual-review findings (page, state, screenshot, broken rule, expected); same-family or cross-family.

## 7. Attention
What the operator should look at first, pointing to rows, pages or files. "No flags" is valid.

## 8. Text for the builder (copy as is)
```
