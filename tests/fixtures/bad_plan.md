# Plan 9: broken sample

## 1. Decisions
| ID | Question | Options | Default |
| --- | --- | --- | --- |
| D-1 | Show totals in MWh? | MWh / kWh | |
| D-2 | Keep old export? | yes / no | TBD |

## 2. Requirements
### R1 Show the yearly total
- Type: feature
- Verify, unit: `tests/test_summary.py`
- Review gate: none

## 3. Batches, parallelism and ownership
| Batch | Requirement IDs | Depends on | Owned files | Runs alongside |
| --- | --- | --- | --- | --- |
| B1 | R1 | none | `web/summary.js`, `shared/table.js` | B2 |
| B2 | R1 | B7 | `shared/table.js` | B1 |
