# Prompts · {{project}}

Copy a block into a new builder session ({{builder}}). Replace the `<…>` parts.

## Kickoff

```text
Run <plan file path> under the builder flow of the trio-workflow skill (builder.md), entirely in this session, stopping only at the plan's stops.
The skill is at {{skill_dir}}; if your skill list does not show it, read SKILL.md and builder.md there.
Read first: 0_RULES.md; the plan's general sections; earlier plans' handoff docs <names> (if missing, stop and tell me); AGENTS.md and CURRENT_STATUS.md.
Integration branch wip/<key>; progress batch-notes/<KEY>_PROGRESS.md; decisions batch-notes/<KEY>_DECISIONS.tsv; stop material batch-notes/REVIEW_<key>_stop<N>.md.
Delivery: {{delivery}}. No push to main, no merge into main, no client data; never touch {{service}}. Heavy checks wait for the lock {{lock}}.
Start now and work through to stop 1.
```

## Resume

```text
Continue <plan>. Read batch-notes/<KEY>_PROGRESS.md, the last handoff and the tail of batch-notes/<KEY>_DECISIONS.tsv, then resume under the "Resume" section of builder.md in the trio-workflow skill ({{skill_dir}}). Git wins over the progress file; do not redo finished batches; commit unfinished work as wip: before deciding what to keep.
```
