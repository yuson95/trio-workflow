# Plan 9: sample

## 0. Constraints
UI conventions bind R1.

## 1. Decisions
| ID | Question | Options | Default |
| --- | --- | --- | --- |
| D-1 | Show totals in MWh? | MWh / kWh | MWh |

## 2. Requirements
### R1 Show the yearly total on the summary page
- Type: feature
- Current state (pointer): `web/summary.js` renderTotals
- Change: add a yearly total row
- You see: the summary table ends with "Total 1,234 MWh"
- Verify, unit: `tests/test_summary.py` gains test_yearly_total
- Verify, live: open the summary page of the synthetic project; screenshot; pass when the total row shows
- Review gate: operator walkthrough
- Prototype: `docs/mockups/summary_MOCKUP.html`

### R2 Fix the rounding of negative values
- Type: bug fix
- Current state (pointer): `src/format.py` round_half
- Change: round half away from zero
- You see: -0.5 shows as -1
- Verify, unit: `tests/test_format.py` gains test_negative_half
- Verify, live: the comparison page shows -1 for the sample delta
- Review gate: none

## 3. Batches, parallelism and ownership
| Batch | Requirement IDs | Depends on | Owned files | Runs alongside |
| --- | --- | --- | --- | --- |
| B1 | R2 | none | `src/format.py`, `tests/test_format.py`, `src/i18n.json` | B2 |
| B2 | R1 | B1 | `web/summary.js`, `tests/test_summary.py`, `src/i18n.json` | B1 |

Append-only shared files: `src/i18n.json`.

## Appendix C. Risks, the batch each lands in
None.
