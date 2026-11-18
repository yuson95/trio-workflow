# Stops and pull requests

trio keeps two kinds of gate, and in PR mode it uses both:

| | Pull request (PR) | Stop |
| --- | --- | --- |
| Gate for | one batch: one change with its own evidence | the plan: a milestone placed in advance |
| How often | many per plan | two or three per plan |
| Checked by | CI on every push, plus a verifier that did not write the code | the reviewer, independently, with its own runs |
| Decided by | the builder lead, once CI and the verifier pass | the operator, from the RESULT and its defaults |
| Answers | did this batch break anything, and does it do what its kickoff said? | is the plan on track, and is the result what the operator wants? |

A PR protects the code; a stop protects the intent. Neither replaces the other.

## Choose the delivery mode

`0_RULES` → "Delivery":

- **`local`** (the default): batches merge locally into `wip/<plan>`, and nothing reaches the remote until the operator's merge. Use it when the repository has no forge, when CI cannot run without client data, or when the project keeps feature branches off the remote.
- **`pr`**: the repository lives on a forge with CI (GitHub, GitLab, Gitea, …), and the operator allows plan branches on the remote.

## Branch layout in PR mode

```text
main  ←  plan PR  ←  wip/<plan>  ←  batch PRs  ←  <plan>/<batch> branches
```

- The builder pushes `wip/<plan>` once, at kickoff, from current `main`.
- Each batch gets a branch `<plan>/<batch>` from `wip/<plan>` and one PR into `wip/<plan>`.
- A batch that depends on an unmerged batch bases on that batch's branch, then retargets to `wip/<plan>` after its parent merges.
- At the final stop, one **plan PR** goes from `wip/<plan>` into `main`.

## Standing authorization (recorded once, in `0_RULES`)

At bootstrap, the operator grants for this repository:

- **builder**: push `wip/<plan>` and batch branches; open, update and merge batch PRs into `wip/<plan>`;
- **reviewer**: post review comments on this repository's PRs.

These still wait for the operator's own words every time:

- anything that writes to `main`;
- a force-push to a shared branch;
- deleting remote branches that are not this plan's batch branches;
- closing or editing other people's PRs.

## Batch PR (builder)

1. **Open the PR as a draft** when the worker starts.
   - Title: `<plan>/<batch>: <change>`.
   - Body: the restated goal, the requirement IDs, the owned files, the evidence list, and a link to the handoff.
2. **CI runs the quick tier on every push.** Heavy checks that need private data or the machine's environments stay local, under the lock; paste their summary lines into the PR body.
3. **Bot reviews are inputs.** Fix real problems; dismiss noise with a one-line reason; ask the reviewer when unsure.
4. **A verifier that did not write the code** posts `PASS`, `PASS+NOTES` or `FAIL` on the PR, with its evidence, for the current head SHA.
5. **Merge into `wip/<plan>`** when CI is green and the verdict still covers the head (same `git patch-id`). Squash, so each batch is one commit on `wip/<plan>`.
6. **Log** the PR number and the merge SHA in the progress file and the decision trail.

UI batches attach their screenshots or contact sheet to the PR ([ui-acceptance.md](ui-acceptance.md)).

## Stop review in PR mode (reviewer)

- **The candidate** is `wip/<plan>` at a SHA. The stop material lists the batch PRs merged since the last stop, each with its verdict and CI link.
- **Review as in [review.md](review.md).** CI results are inputs. Rerun locally, under the lock, what CI cannot run: the full check, solver tests, anything that needs the machine's environments.
- **Read these batch PRs in full**: the ones that touched hotspot files; the ones with dismissed bot findings; the ones merged on `PASS+NOTES`.
- **The `RESULT` file stays the canonical record.** When the standing authorization allows, post a short comment that links it on the plan PR, or on a tracking issue before the plan PR exists.

## Final stop and merge

- **The builder opens the plan PR** `wip/<plan>` → `main` at the final stop. CI runs the full tier where it can.
- **Merge only after** the RESULT reads `PASS` and the operator says "合并并推送" / "merge and push". Then:
  - merge the plan PR with the repository's merge method;
  - read the PR back: it must show as merged into `main`;
  - delete this plan's batch branches, and `wip/<plan>` if the branch policy says so;
  - continue with the restart and retro in [merge.md](merge.md).
