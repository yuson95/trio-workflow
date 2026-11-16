# Layers: trio outside, the inner layer inside

The work has two layers.

- **Outer layer (trio)** decides what gets built, when the work stops for review, and whether it lands.
- **Inner layer** decides how one batch's code is written and proven inside one worker's worktree.

The inner layer is either pstack (poteto's agent workflow, <https://github.com/cursor/plugins/tree/main/pstack>) or the built-in rules at the end of this file.

## Who owns what

| Concern | Outer layer (trio) | Inner layer |
| --- | --- | --- |
| Goal, requirement IDs, acceptance, "You see" lines | the plan file | restates them; does not redefine them |
| Batch scope, owned files, forbidden actions, evidence to produce | the kickoff | obeys it |
| How the code inside the batch is designed | — | owns it (data shape first; pstack's architect or arena when installed) |
| Writing the code and proving it inside the batch | — | owns it |
| Evidence format: handoff, `<KEY>_DECISIONS.tsv`, stop material | defines it | produces it |
| Integration into `wip/<plan>`, stops, verdicts, merge, push | owns it | never does it |
| Operator decisions | collected at stops, each with a default | proceeds on the default and records it; asks mid-batch only about a blocker |

**Precedence when rules conflict**, highest first:

1. the operator's own words;
2. the project's rules (`AGENTS.md`, `0_RULES`, the plan);
3. trio;
4. pstack.

Record every conflict you resolve in the decision trail.

## Configure

`0_RULES`, under "Inner layer", names one of:

- `pstack`, with the tools it is installed in (for example "Cursor, Claude Code");
- `built-in`.

A worker running in a tool where pstack is not installed uses the built-in rules, even when the project names pstack. Note the fallback in its handoff.

## The batch contract

**In: the kickoff** (written by the builder lead, see [builder.md](builder.md) step 3):

- the goal, restated;
- the requirement IDs and their "You see" lines;
- the **batch type** and the **inner playbook** taken from the mapping below;
- owned files, untouched files, append-only files;
- forbidden actions: push, PR, merge, touching the operator's service or client data;
- the evidence to produce: commands with their expected output, live scenarios from the verification recipe, a perf rule if one applies;
- the previous handoff, and the lock file path for heavy checks.

**Out: what the worker returns**:

- commits on the batch branch only, ordered so they read as an argument (failing test then fix, subtraction then reshape, baseline then treatment);
- a handoff of at most 30 lines in the template of [builder.md](builder.md);
- rows in `<KEY>_DECISIONS.tsv` (columns `ts phase decision why evidence result`, the same as pstack's decision log);
- the evidence files at the paths the kickoff named;
- requests for changes to files the batch does not own;
- open questions, each with the default the worker applied.

## Playbook mapping (when pstack is installed)

The plan tags every requirement with a **type**. The lead copies that type and its playbook into the kickoff.

| Batch type | pstack playbook or skill | What changes under trio |
| --- | --- | --- |
| feature: new or changed behavior | Feature | Its parallel breakdown happens inside the batch's owned files; use arena for implementation shapes that are contested. |
| bug fix: a reported defect | Bug fix | Reproduce on the real surface first, through the verification recipe. |
| refactoring: structure only, behavior unchanged | Refactoring | Capture behavior baselines before and after the change. |
| perf: slowness with a baseline | Perf issue, plus benchmark-checklist | Measure the baseline on `main` first; heavy runs take the lock. |
| hillclimb: push a metric toward a target | Hillclimb | One commit per accepted win, logged in the decision trail. |
| visual parity: UI equivalence or a style migration | Visual parity | Screenshots go into the stop material. |
| prototype: an open design or behavior question | Prototype | The result goes back to the reviewer, or into the stop material. A prototype never lands as is. |
| investigation: a read-only question | Investigation | The answer goes into the handoff with its sources. |

**Reviewer-side pstack tools**, used when installed in the reviewer's tool:

| Need | pstack tool |
| --- | --- |
| Adversarial pass at a stop | interrogate |
| Second opinion on a plan or design | arena |
| The project's verification recipe | create-verification-skill and maintain-verification-skill |
| Vetting a number | benchmark-checklist |
| Auditing the decision trail | the audit section of show-me-your-work |
| A mistake that keeps coming back | correct |

## Overrides: pstack steps that change under trio

| pstack | Under trio |
| --- | --- |
| "Opening a PR" at the end of every playbook | `local` delivery: commit on the batch branch, write the handoff and return; no PR, no push. `pr` delivery: the playbook's PR becomes the batch PR into `wip/<plan>`, never into `main` ([prs.md](prs.md)). |
| Babysit, Shipping, Autopilot-full, Autopilot-stack, Orchestrate | In `pr` delivery, Babysit may drive a batch PR to green. The others are not used: landing on `main` follows [merge.md](merge.md), on the operator's words. |
| Cloud agents and cloud VMs | Only where `0_RULES` allows them. Client data never leaves the machine; only synthetic data goes out. |
| A swarm with ten live lanes per PR | Size the lanes to trio's check tiers and worker cap. Heavy runs take the lock. |
| Model slugs per role | Use them only in tools that offer them; otherwise use the tool's default. Keep the verifier on a different model family where possible. |
| Decision log at `decisions.tsv` | Write to `<KEY>_DECISIONS.tsv` instead; the columns are the same. |
| Asking the operator a product call mid-run | Proceed on the default and record it for the next stop. Stop early only for a blocker. |
| Session overrides such as "going to bed" | Not needed: trio's stops already define when the builder waits. |
| A PR body that opens with "Why" | The commit message body and the handoff carry the why. |
| Writing skills (unslop, technical-writing, no-comments, deslop) | Allowed. The project's coding standards win on conflict. |
| The skill-authoring playbook | Use it when editing trio or the project's skills. |

## Built-in inner rules (no pstack)

1. **Restate** the batch goal and scope at the top of the handoff.
2. **Name the data shape** before you write logic: the types, the table or state machine, what concurrent actors share.
3. **Smallest change, subtract first.** Remove dead weight before you add to it.
4. **Bugs**:
   - reproduce on the real surface;
   - write a failing test first when a cheap test path exists;
   - fix the root cause, not the symptom.
5. **Test behavior**: assert what a user of the code can observe.
6. **Drive the real surface** through the verification recipe for every "You see" line.
7. **Performance**: measure the baseline on `main` first and explain the number. Heavy runs take the lock.
8. **Commit** in small units, each ending in a check, in an order that reads as an argument.
9. **Log** forks, pivots and unit results to the decision trail with `scripts/log_decision.py`.
10. **Before handing back**, compare your diff with the batch's owned files and move anything outside them into a request.
