# Plans and change requests

Role: Reviewer. Plans and change requests are the builder's only source of requirements, and the only thing the operator can audit without reading code. You own the plan, not the code.

## A. Draft a plan

1. **Route by risk, not by file count.** A one-file change to a calculation can carry more risk than ten display files.
   - **Light path**: display-only changes that meet the light-path conditions (B).
   - **Change request** (B): a contained change with an obvious approach. A change to numbers still names its invariants and expected values (step 5), and a storage-format change still needs its `DESIGN_*.md` answered before code (step 7).
   - **Plan with stops**: cross-cutting work, several dependent changes, or a change that is hard to undo (a migration, deleted data, a contract other lines use).
2. **Read the state**: `00_FLOW`, earlier plans' handoff docs, and the open items in recent `RESULT` files that have no home yet. Open lessons about the checks themselves (a flaky test, the lock, a timeout under load) go into this plan's first batch. Read the operator's earlier declines too (`00_FLOW` decisions, the decision trail, earlier plans' appendix B): re-propose a declined option only with new evidence, and say what changed.
3. **Read the code and verify the facts.** Every "current state" line carries a file or function pointer. Route broad exploration to workers that return file pointers, conventions, test commands and entry points, not dumps.
4. **Settle open questions before writing** (settle forks by running):
   - feasibility questions get a probe in `probes/`; layout questions get a prototype (`*_MOCKUP.html`);
   - keep the evidence (script, output, screenshot) for appendix A;
   - ask the operator only product or preference calls, each with options and a default.

   Done when every "current state" line has a pointer, and every uncertainty has probe evidence or a decision entry.
5. **Write the plan** from the template below. Each requirement has:
   - an ID;
   - a **type**: feature, bug fix, refactoring, perf, hillclimb, visual parity, prototype or investigation. The type picks the inner playbook (see [layers.md](layers.md));
   - a **You see** line: one observable result, such as a page state, a stored value or an output line;
   - **invariants**: for a requirement that computes numbers or changes stored state, the properties that must hold for every input, each with the test that checks it across varied inputs (property-based where the project has such a library, otherwise a table of contrasting cases). Examples: "the site baseline is the same whichever measures a portfolio holds"; "a saving is deducted once along a chain of derived curves". Other requirements write `none`;
   - **expected values**: for a requirement that computes numbers, at least one worked example (inputs and expected outputs) that you compute before any code exists, through a path independent of the code to be written: a hand calculation or a probe script in `probes/`, kept for appendix A. The builder copies the expected values into a test unchanged. When code and example disagree, the builder records both and the reviewer decides at the stop; an expected value changes only through a logged decision, never to turn a test green;
   - for a requirement that adds a **blocking check** (a refused save, a stopped calculation): the harm it prevents and why a visible label would not prevent it. Where a label would do, use the label and let the work continue;
   - for a requirement that **reverses an existing behavior** (a refusal becomes a label, a classification moves, a status flips): the **census** of what asserts the old behavior. Search for its codes and status names, and run the affected suites in every interpreter and test root the project uses, counting skipped tests: a suite skipped in the default interpreter still asserts the old rule. List the test lines and contract cases found; they belong to the batch that flips the behavior;
   - a **prototype** for every review-gated requirement: an HTML mockup, an annotated screenshot or an operator-supplied reference, confirmed at stop 1 (see [ui-acceptance.md](ui-acceptance.md) §1);
   - verification:
     - **unit**: the tests that gain cases;
     - **live**: scenarios driven through the verification recipe, each with its screenshot or output and a pass predicate, including one regression scenario run on both `main` and the candidate;
     - **perf**: when timing matters, the metric, a baseline measured on `main` first, and the number that fails.

   Tests alone do not verify user-visible behavior.
6. **Mark the review gates.** A requirement that changes what the operator sees or does is review-gated: the operator walks through it on an isolated instance before the final stop. Plans whose UI changes span several pages also schedule a walkthrough after the first UI batch. Name the screenshot states each changed page needs (see [ui-acceptance.md](ui-acceptance.md) §2).
7. **Set the stops**, usually two or three:
   - Stop 1, before code: the plan and contracts (data shapes, interfaces, storage migration, page flow) and the ownership table.
   - Storage-format changes and migrations need a `DESIGN_*.md` that the reviewer answers with "go ahead" before code is written.
   - Middle stops: after a data migration or a large phase.
   - Final stop: full check, regression gate, handoff doc, and the operator's walkthrough beforehand.
   - Name which checks prove the stop (acceptance) and which only find defects early (discovery). Acceptance checks run once on the frozen candidate ([builder.md](builder.md) step 9), so a plan that asks for independent recomputation, first-save replay or a release build lists them under the stop, not under a batch.
8. **Design for parallel work.** Parallelism comes from boundaries drawn in advance, not from resolving conflicts afterwards.
   - When the operator asks for "faster" or "more parallel" without saying where, ask whether that means batches inside one plan, or two plans coding at once.
   - Two plans may code at once only when their ownership tables do not overlap. If they overlap, name the files that would conflict and propose the pipeline below instead.
   - Estimate the gain after queueing: the worker cap in `0_RULES` (default 3; the reviewer owns `0_RULES` and changes the cap there) and one heavy check at a time.
     - Example: six independent one-day batches with a cap of 3 take about two days of building instead of six. Their six 40-minute full checks still queue, which adds about four hours.
   - For a plan that is already running, deliver changes to its parallel design as a revision block in the plan file, plus a "supplement" paragraph for the same builder session (B.5). The builder applies the change at its next batch boundary, not in the middle of a batch.
   - The plan states:
     - **Dependency graph**: which batch waits for which. Batches with no dependency and no shared files may run at once.
     - **Ownership table**: the files each batch writes. Each hotspot (shared component, job layer, storage format) has one owner batch. Often the best move is a small early batch that makes all hotspot changes first. Other batches that need a hotspot change write it into their handoff for the owner to make.
     - **Append-only shared files**: files several batches may only append to, such as route lines, translation keys or the provenance manifest. The batch that merges later resolves conflicts.
     - **Contract first**: stop 1 freezes the interfaces. After that, frontend and backend batches run in parallel against the contract, the frontend on fixed sample data.
     - **Mount points**: where one batch's UI or logic plugs into a hotspot another batch owns. The owner adds the empty mount point early.
     - **Start with one unit**: the first batch goes end to end (kickoff, worker, verification, integration) before fan-out, so a flawed kickoff costs one worker.
     - **Waves**: which batches start together, within the cap.
     - **Between plans**: correlated plans write code in sequence. The next plan's preparation (code reading, probes, prototypes, design, synthetic data) may overlap the current plan's coding. Prepare in parallel; write code in sequence.
     - **Independent lines**: work unrelated to any plan (tooling, test infrastructure, docs) may run as its own line. That line's items are implemented only there, and other lines only merge `main`.

   Done when every batch has owned files and dependencies, and every hotspot has exactly one owner.
9. **Check the plan's structure**: run `python <skill dir>/scripts/check_plan.py <plan file>` and fix every line it prints until it reports `CHECK_PLAN ok`.
   - It checks that every requirement has a type, a "You see" line, invariants (or `none`), unit and live verification and a review gate; that every review-gated requirement has a prototype; that every decision has a default; and that every file has one owner batch unless it is marked append-only.
   - It recognizes these labels in a Chinese plan: 类型, 你会看到, 不变量, 单元验证, 实际操作验证, 走查, 原型; and in section titles: 需求, 决定, 批次, 独占文件, 依赖, 追加型.
10. **Get a challenge for a high-risk plan.** A plan that changes a storage format, a core calculation, a security boundary or a contract between lines gets one challenge before stop 1, so its author is not the only judge of its design.
    - Write a prompt into `PROMPTS` that gives the plan and its code pointers, not your reasoning, and asks what would make the plan fail. The operator runs it on another model family, or on a fresh session when no other family is available.
    - Findings follow "Before code exists" in [review.md](review.md). Save the answer as `<plan>_CHALLENGE.md` next to the plan, and answer every point: revise the plan, or record it in appendix B with the reason.
11. **Write the kickoff prompt** into `PROMPTS`, and update `00_FLOW`: roadmap, current step, decisions.
12. **Reply**: the plan path, the checker's summary line, the decisions with their defaults, what the probes proved and what remains unproven, the challenge's state for a high-risk plan, and the operator's next step (which prompt to paste where).

### Plan template

```markdown
# Plan <X>: <name>
- Baseline: main @ <sha>; depends on handoff docs: <names>
- Author: <reviewer>, <date>

<Under ten lines: what changes, for whom, the requirement IDs in order.>

## 0. Constraints
Which general rules bind this plan; which items the UI conventions bind; what is out of scope.

## 1. Decisions
| ID | Question | Options | Default |

## 2. Requirements
### <ID> <task as a verb phrase>
- Type: feature / bug fix / refactoring / perf / hillclimb / visual parity / prototype / investigation
- Current state (pointer):
- Change:
- You see: <one observable result>
- Invariants: <property; the test that checks it over varied inputs> / none
- Expected values (numbers only): <inputs → expected outputs; probe path or hand calculation>
- Blocking check (only if one is added): <the harm it prevents; why a label would not do>
- Reverses (only if it reverses an existing behavior): <the old behavior; the census command; the test lines and contract cases it found>
- Verify, unit: <test file and the case it gains>
- Verify, live: <scenario via the verification recipe; screenshot or output; pass when …> plus one regression scenario on main and the candidate
- Verify, perf (if relevant): <metric; baseline on main first; failing number>
- Review gate: operator walkthrough / none
- Prototype (review-gated only): <path to mockup or annotated screenshot>

## 3. Batches, parallelism and ownership
| Batch | Requirement IDs | Depends on | Owned files | Runs alongside |
Hotspots: <file> → <batch>. Append-only shared files: …. Mount points: …. Waves: …

## 4. Stops
Stop N: what the builder delivers, what the reviewer checks.

## 5. Checks
Per batch: quick check plus the batch's tests. Per stop: full check. Final stop: plus the regression gate.

## 6. Handoff doc
Written before the final stop to docs/development/history/<yyyy-mm>/<name>_HANDOFF.md, committed on the wip branch, merged with the code: what changed, interface and data changes, known limits, what the next plan must know.

## Appendix A. Probe and prototype evidence
## Appendix B. Alternatives rejected, and why
## Appendix C. Risks, the batch each lands in, what the owner watches
```

## B. Change request (the operator reports a problem or a new need)

1. **Restate** the problem in plain words before touching anything.
2. **Find the cause.** Read the code first and locate the file and function. Start an isolated instance with a synthetic project only when reading does not explain it. Decide which line of work and which plan the change belongs to.
3. **Choose the route.** All edits go to the builder, even one-line ones.
   - **All light-path conditions hold**: give the operator one line to forward: "Small change: <page> <table or area>, now <…>, should be <…>; display only; run the quick check and all frontend suites; send screenshots." After the builder is done, the operator says "看一下小改" and the review follows branch D of [review.md](review.md). Several small changes may merge together.
   - **Otherwise**: write `REQUEST_<topic>.md`.
4. Write the request from the template below, with the operator's words and the date in the background section. A change to numbers or stored state names its invariants in the Verification column, a change to numbers also its expected values computed before code, a new blocking check names its harm, and a reversal of existing behavior carries its census, as in A step 5.
5. For an addition while the builder is mid-work, write a "supplement" paragraph for the **same** builder session and mirror it in the request.
6. Update `00_FLOW`. Requests go into the current step and the open items; small changes get one line when they merge.

### Light-path conditions (all must hold; when unsure, write a request)

- display only: layout, text, translation, column order, style;
- no change to numbers, calculations, storage format, interfaces or export columns;
- no change to functions or components shared by several pages;
- small scope: one or two tables, or one page area.

### Request template

```markdown
# Change request: <topic> (<prefix>-01..NN)
- Date; belongs to: <line / plan>; baseline: main @ <sha>

## 1. Background
The operator's words and date; where it was seen.

## 2. Cause
Files and functions; how to reproduce.

## 3. Requirements
| ID | Change | You see | Verification |

## 4. Default decisions
| ID | Question | Default |

## 5. Order and conflicts
Which plans touch the same files; what goes first.

## 6. Text for the builder (copy as is)
```
