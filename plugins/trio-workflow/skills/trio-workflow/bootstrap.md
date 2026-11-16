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
4. **Create the handoff directory** from the templates below: `00_START_HERE`, `00_FLOW`, `0_RULES`, `PROMPTS`, `batch-notes/`. Fill in every field of `0_RULES`, including the role table, the lock file path and the recipe path.
5. **Specify the repo-side skeleton as part of the first batch**:
   - a one-page `AGENTS.md`: hard rules plus pointers to what to read first;
   - `docs/development/CURRENT_STATUS.md`: current capabilities, known limits and test entry points, each with its source;
   - `.ignore`: skip vendor, generated and history files in searches;
   - a quick check that selects tests by changed paths and prints summary lines only;
   - one configuration entry point for runtime paths;
   - a lock for heavy checks shared by every session on the machine. The skill's `scripts/heavy_lock.py` provides it; name the lock file path in `0_RULES`.
6. **Install the trio-workflow plugin for every agent in the role table**; see the plugin's `README.md`. Install pstack too where the inner layer names it.
7. **Make the handoff path findable** by every agent. Add one line to the repo's `AGENTS.md` (read by Codex, Claude Code, Cursor and most other agents). If your tool has memory, also store the handoff path, the role table, the authorization phrases and the branch policy there, one fact per file.
8. Go to [planning.md](planning.md) and draft the first plan.

## Templates

### `00_START_HERE` (for the operator)

```markdown
# Start here · <project>

For where things stand now, read 00_FLOW §0.

## Roles
| Role | Agent / tool | Session rule |
| Reviewer | <e.g. Claude Code> | a fresh session per stop review |
| Builder | <e.g. Codex> | one session per plan |

## Files
| File | What | Reader |
| 00_FLOW | current state, process, rules, decisions, open items | you and the reviewer |
| 0_RULES | roles, repo rules, verification recipe | builder |
| <N>_PLAN_… | one plan per builder session | builder |
| PROMPTS | kickoff and resume prompts | you copy them |
| batch-notes/ | progress, handoffs, decisions, stop materials, results, requests | at stops |

## Every plan runs the same way
1. Open a builder session and paste the plan's kickoff prompt from PROMPTS.
2. At a stop, the builder replies with one line: "Reached stop N, material at …".
3. Open a fresh reviewer session and say "审查<plan>停点N" with that line. Do not tell the builder it passed yet.
4. Tell the builder: "Review result at <RESULT path>; fix accordingly and continue." Add any decisions; silence means defaults.
5. Before the final stop, walk through the isolated instance the builder gives you and tell the builder what you see.
6. After the final stop passes, tell the reviewer "合并并推送". Restart your service after the merge.
If a session breaks or slows down, open a new one with the resume prompt.

## Phrases
| Say | To | Effect |
| 审查<plan>停点N | reviewer | RESULT written; decisions listed |
| 看一下小改 | reviewer | diff-only check |
| 合并并推送 / 只合并不推送 | reviewer | fast-forward merge, push if asked |
| 做收尾 | reviewer | cleanup list, executed after your OK |
```

### `00_FLOW` (the single current state)

```markdown
# <project> flow and open items

## 0. Overview (<date>)
| Line | Plan | Current step | Your next step |
main = <sha>

## 1. Roadmap
| Order | Plan | Stops | Reviewer session | Handoff doc |

## 2. Current stage (step by step, mark "← here")

## 3. Rules
Roles, stops, merge, check tiers, light path, walkthrough, test rules, branches, data. Point to the trio-workflow skill for generic rules; write only project-specific ones here.

## 4. When it is your turn (situation → action)

## 5. Decisions waiting on you
| When | Item | Default |

## 6. Open items
| # | Item | Goes to | When | Who |

## 7. File index

## 8. Change log
Keep the last 10 entries; move older ones to history/FLOW_LOG.md.
```

### `0_RULES` (read by the builder at the start of every session)

```markdown
# Project rules
Generic process, parallel and token rules: trio-workflow skill, builder.md. Only project-specific rules here.

1. Roles: Reviewer = <agent>, Builder = <agent>; same family: yes/no.
   Inner layer: pstack (installed in <tools>) / built-in.
   Skill scripts: <skill dir>/scripts (heavy_lock.py, log_decision.py, check_plan.py).
2. Baseline and branches: new worktree (short path outside the repo) and local branch from current main; integration branch wip/<plan>; remote policy.
   Delivery: local / pr. In pr mode: forge, CI tiers per PR, standing authorization for the builder and the reviewer.
3. Checks: quick command; full command and duration; heavy checks and their lock file; report summary lines; missing environment = NOT_RUN.
4. Verification recipe: path to Launch / Doctor / Drive / Evidence / Cleanup and the feature map.
5. Data and isolation: data root; isolated instance command (own port, own projects dir); the operator's service port (never touch).
6. Parallel: worker cap (default 3); hotspot files.
7. UI conventions document path.
8. Project-specific: formatting, provenance, path rules, guard tests.
9. Known issues.
```

### `PROMPTS` (the operator copies these to the builder)

```text
Run <plan file path> under the builder flow of the trio-workflow skill, entirely in this session, stopping only at the plan's stops.
Read first: <0_RULES path>; the plan's general sections; earlier plans' handoff docs <names> (in docs/development/history/; if missing, stop and tell me); AGENTS.md and CURRENT_STATUS.md.
Integration branch wip/<key>; progress batch-notes/<KEY>_PROGRESS.md; decisions batch-notes/<KEY>_DECISIONS.tsv; stop material batch-notes/REVIEW_<key>_stop<N>.md.
No push, no merge into main, no client data, never touch <service port>.
Start now and work through to stop 1.
```

Resume prompt:

```text
Continue <plan>. Read batch-notes/<KEY>_PROGRESS.md, the last handoff and the tail of <KEY>_DECISIONS.tsv, then resume under the builder flow of the trio-workflow skill. Do not redo finished batches.
```
