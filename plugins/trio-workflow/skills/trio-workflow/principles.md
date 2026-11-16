# Principles

Each entry gives a trigger ("when") and an action ("do"). Most are adapted from pstack by poteto (MIT licence, <https://github.com/cursor/plugins/tree/main/pstack>). Entries marked "(trio)" come from running this workflow. When a principle changes a decision, name it in the file or reply that records the decision.

## Core

- **Restate first.**
  - When: your first message on a task, every worker kickoff, every stop material.
  - Do: say in plain words the goal, the problem and the smallest change that would meet it. A misreading surfaces here, where it costs one message.
- **Settle forks by running.**
  - When: you are about to ask "which approach?" or "what should this do?".
  - Do: if the answer is observable (behavior, timing, layout, a value), build a throwaway probe or prototype and let the result decide. Ask the operator only product or preference calls, and offer options with a default.
- **Subtract before you add.**
  - When: you are adding to or reshaping existing code or UI.
  - Do: remove the dead weight first, then build on the simpler base.
- **Smallest change.**
  - When: you are sizing a diff or tempted to add a layer, abstraction or option.
  - Do: prefer deletion and the smallest change that solves the stated problem.
- **Fix root causes.**
  - When: debugging.
  - Do: trace the symptom back to the first place the system went wrong and fix it there. When two fixes that share one premise have both failed, write the premise down and test it directly.

## Verification

- **Prove it works.**
  - When: before you call anything done.
  - Do: check the real artifact (the running page, the stored file, the command's output), not a proxy such as "it compiles", a green build or a worker's report. Tests alone do not verify user-visible behavior; drive the real surface as well. Script the check when you can, so a reviewer can rerun it.
- **Explain the number.**
  - When: before you trust, report or act on a number, whether a result, a timing or a count.
  - Do:
    - name the result that would change a decision, and the noise;
    - name what limits the number;
    - list what else the number could be measuring (cached work, a skipped path, errors, defaults) and rule each one out;
    - in domain calculations, cross-check through an independent path: a hand calculation, a conservation residual, or a comparison with an earlier result (trio).
- **Sequence verifiable units.**
  - When: multi-step work, migrations, or runs of similar edits.
  - Do: cut the work into small units that each end in a check, and do not advance on red. Order commits so they read as an argument: failing test then fix, subtraction then reshape, baseline then treatment.
- **Test behavior, not implementation.**
  - When: writing or keeping a test.
  - Do: assert what users of the code can observe, so the test fails when that behavior breaks and survives internal changes.

## Delegation

- **Guard the context window.**
  - When: large outputs, long files, repeated reads, fan-out.
  - Do: route bulk work to workers, cap the scope of each phase, and keep summaries and file pointers in the main thread.
- **Fresh worker per task.**
  - When: new work, a fix round, a retry, the next queue item.
  - Do: start a fresh worker with consolidated scope: the original brief, every later directive, the prior report and the branch. Reuse a worker only for state that lives in it, such as its checkout, uncommitted edits or a running process.
- **Read the diff, not the summary.**
  - When: a worker or a builder reports done.
  - Do: you own its output, so read the diff and the evidence. A verdict covers one commit; a new head needs a new verdict.
- **Never block on the operator.**
  - When: you are tempted to ask "should I do X?" about reversible work.
  - Do: do it, show the result, and let the operator correct course. Always pause for irreversible actions.
- **Separate before serializing.**
  - When: two actors might write the same file, branch, key or service.
  - Do: give each actor its own target first. Where sharing is real, serialize with structure (single owner, sequential phases, lock files), not with conventions alone.
- **One writer per worktree** (trio).
  - When: parallel attempts.
  - Do: give each attempt its own worktree and branch. Agents sharing one checkout overwrite each other, and nobody can tell who changed what.

## Meta

- **Encode lessons in structure.**
  - When: you catch yourself writing the same instruction a second time.
  - Do: turn it into a check, test, lint, script or lock. If it needs judgment and cannot be encoded, make the instruction prominent and add an example of the failure. Once a structural fix exists, drop the instruction.
- **Build the lever** (tools over hand work).
  - When: non-trivial or repeated work.
  - Do: build the script or tool that does or proves the work, such as the project's verification recipe or a harness for a synthetic project. The tool is the artifact a reviewer reruns.
- **Keep a decision trail.**
  - When: long, autonomous or multi-batch work.
  - Do: append one row per fork, pivot, unit result or blocker to the plan's `DECISIONS.tsv`, with an evidence pointer. Supersede wrong rows with new rows; never edit history.
- **Earn the loop** (trio; verification before autonomy).
  - When: about to let a builder run unattended for a long stretch.
  - Do: first make sure it can verify its own work. A builder without a working verification recipe only produces unchecked work faster.
