# Bootstrap a project

Role: whichever agent the operator names as reviewer. The goal is a working handoff directory, an agreed role table, a verification recipe and a first plan. The reviewer specifies the repo-side files in the first plan, and the builder writes them. Any other agent asked to bootstrap drafts the step-1 questions for the operator and stops there.

## Steps

1. **Ask everything in one message**, each question with a default:
   - project goal and scope;
   - repository path;
   - handoff directory location (default: outside the repo, next to the data root);
   - **roles**: which agent and tool plays Reviewer and which plays Builder, and whether they belong to the same model family;
   - **inner layer**: pstack, and in which tools it is installed, or the built-in rules (see [layers.md](layers.md));
   - how messages travel between agents (default: the operator relays a one-line pointer to a file);
   - **delivery**: `local` (default) or `pr`, meaning batch PRs into `wip/<plan>` with CI and a plan PR into `main`; in `pr` mode, also the standing authorization (see [prs.md](prs.md));
   - the operator's authorization phrases (defaults: "合并并推送", "只合并不推送", "做收尾");
   - the operator's running service: port and restart method;
   - where client data lives, and how synthetic data is produced;
   - remote branch policy (default: `main` plus release branches only).
2. **Read the repo**:
   - existing `AGENTS.md` / `CLAUDE.md`;
   - check commands (package scripts, Makefile, `tools/`) and the test layout;
   - time one quick check and one full check, while nothing else heavy runs on the machine; note when there is no quick check.

   Done when every cell of the check-tier table in [review.md](review.md) has a command and a duration.
3. **Write the verification recipe** into the first plan as the builder's first batch (build the lever). If pstack is installed in the builder's tool, its create-verification-skill skill generates the recipe as a project skill. It must cover:
   - **Launch**: the exact command that starts an isolated instance from an empty data directory with synthetic data, and the log line that means it is ready.
   - **Doctor**: one read-only check that the instance is the right build, on its own port, and usable.
   - **Drive**: how an agent exercises a feature the way a user would, with the repo's real selectors, routes or commands.
   - **Evidence**: what to capture (screenshots, response bodies, stored files) and where it is kept.
   - **Cleanup**: stop only what this run started; the evidence survives cleanup.
   - **Feature map**: one short file per main feature, covering how to reach it, how to drive it, the end state that proves it works, and gotchas.
   - **Screenshot states**: how to reach each default state of [ui-acceptance.md](ui-acceptance.md) §2 (empty, full, many, narrow, second language) with prepared synthetic projects, and how to save `<page>__<state>.png`.

   The recipe is done only after the builder has run it once end to end.
4. **Create the handoff directory** with the script, in the operator's language:

   ```bash
   python <skill dir>/scripts/bootstrap_handoff.py --dir <handoff dir> --project <name> --reviewer <agent> --builder <agent> --lang zh --delivery local --service "port 8766"
   ```

   It writes `00_START_HERE.md`, `00_FLOW.md`, `0_RULES.md`, `PROMPTS.md` and `batch-notes/` from [templates/](templates/) (`en` or `zh`), and never overwrites an existing file. Then fill every remaining `<…>` in `0_RULES.md`: the check commands, the recipe path, the data root and the hotspot files.
5. **Specify the repo-side skeleton as part of the first batch**:
   - a one-page `AGENTS.md`: hard rules plus pointers to what to read first;
   - `docs/development/CURRENT_STATUS.md`: current capabilities, known limits and test entry points, each with its source;
   - `.ignore`: skip vendor, generated and history files in searches;
   - a quick check that selects tests by changed paths and prints summary lines only;
   - one configuration entry point for runtime paths;
   - a lock for heavy checks shared by every session on the machine. The skill's `scripts/heavy_lock.py` provides it; name the lock file path in `0_RULES`.
6. **Install the trio-workflow skill for every agent in the role table**, for example `npx skills add yuson95/trio-workflow -g -a <agent> -y --copy`; other ways are in the repository README. Install pstack too where the inner layer names it.
7. **Make the handoff path findable** by every agent. Add one line to the repo's `AGENTS.md` (read by Codex, Claude Code, Cursor and most other agents). If your tool has memory, also store the handoff path, the role table, the authorization phrases and the branch policy there, one fact per file.
8. Go to [planning.md](planning.md) and draft the first plan.

## Templates

The templates live in [templates/en/](templates/en/) and [templates/zh/](templates/zh/), one file per handoff file. Edit them there; the script fills the `{{placeholders}}`.
