# v8.67 B/C WF20 WF12 Comparison - 2026-06-19

## Source runs

| RunId | Object | Module | Window | Status |
|---|---|---|---|---|
| 20260619_1710_wf20_B | B | wf20 | 2012-2019 | GREEN |
| 20260619_1715_wf20_C | C | wf20 | 2012-2019 | GREEN |
| 20260619_1720_wf12_B | B | wf12 | 2020-2026 | GREEN |
| 20260619_1725_wf12_C | C | wf12 | 2020-2026 | GREEN |

## Metrics

| Object | Module | Window | Profit | PF | Trades | Max DD% | Retention | Status | Decision |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| B | wf20 | 2012-2019 | 55826.12 | 1.17 | 250 | 57.35 | 1 | GREEN | Continue: object passed this WF module. |
| C | wf20 | 2012-2019 | 57221.99 | 1.15 | 250 | 60.76 | 1 | GREEN | Continue as challenger only: object passed but is not eligible to replace B yet. |
| B | wf12 | 2020-2026 | 556052.56 | 2.27 | 203 | 26.07 | 1 | GREEN | Continue: object passed this WF module. |
| C | wf12 | 2020-2026 | 716968.27 | 2.29 | 203 | 28.31 | 1 | GREEN | Continue as challenger only: object passed but is not eligible to replace B yet. |

## Cross-object comparison

- B status: GREEN both directions
- C status: GREEN both directions; promote to equal-depth challenger validation
- C recent-window profit advantage vs B: 28.94%
- C old-window DD penalty vs B: 3.41 percentage points

## Decision

- B mainline: keep B as current mainline.
- C challenger: promote C to equal-depth challenger validation, not mainline replacement.
- Next execution: run spread and slippage for B/C first, then quarter and month-core if both stay green.

## Notes

- wf20 is old-window validation: 2012-2019.
- wf12 is recent-window reverse validation: 2020-2026.
- This report is fixed-candidate validation, not optimizer re-selection.
- Final rule applied: Keep B as current mainline. Promote C to equal-depth challenger validation because C passed wf20 and wf12, has material recent-window profit advantage, and old-window DD penalty is not material. Do not replace B yet.