# Start here · {{project}}

For where things stand now, read `00_FLOW.md` §0.

## Roles

| Role | Agent / tool | Session rule |
| --- | --- | --- |
| Operator | you | decide, walk through, authorize |
| Reviewer | {{reviewer}} | a fresh session per stop review |
| Builder | {{builder}} | one session per plan |

## Files

| File | What | Reader |
| --- | --- | --- |
| `00_FLOW.md` | current state, process, rules, decisions, open items | you and the reviewer |
| `0_RULES.md` | roles, repo rules, verification recipe | builder |
| `<N>_PLAN_….md` | one plan per builder session | builder |
| `PROMPTS.md` | kickoff and resume prompts | you copy them |
| `batch-notes/` | progress, handoffs, decisions, stop materials, results, requests | at stops |

## Every plan runs the same way

1. Open a builder session and paste the plan's kickoff prompt from `PROMPTS.md`.
2. At a stop, the builder replies with one line: "Reached stop N, material at …".
3. Open a fresh reviewer session and say "review <plan> stop N" with that line. Do not tell the builder it passed yet.
4. Tell the builder: "Review result at <RESULT path>; fix accordingly and continue." Add any decisions; silence means the defaults.
5. Before the final stop, walk through the isolated instance the builder prepares, and tell the builder what you see.
6. After the final stop passes, tell the reviewer "merge and push". Restart your service after the merge.

If a session breaks or slows down, open a new one with the resume prompt.

## Phrases

| Say | To | Effect |
| --- | --- | --- |
| review <plan> stop N | reviewer | RESULT written; decisions listed |
| look at the small change | reviewer | diff-only check |
| merge and push / merge only | reviewer | fast-forward merge, push if asked |
| clean up | reviewer | cleanup list, executed after your OK |
