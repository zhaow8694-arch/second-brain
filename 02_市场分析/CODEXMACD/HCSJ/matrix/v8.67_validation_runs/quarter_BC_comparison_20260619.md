# v8.67 B/C Quarter Comparison - 2026-06-19

## Scope

Fixed-candidate quarter slicing after B/C passed wf20/wf12 and ExecutionMode slippage-delay checks.
This report does not claim true spread validation.

## Summary

| Object | Window | RunId | Cases | Positive rate | Losing quarters | Failed | Total profit | Worst quarter | Worst profit | Best quarter | Best profit | Min trades |
|---|---|---|---:|---:|---:|---:|---:|---|---:|---|---:|---:|
| B | 2012-2019 | 20260619_1830_quarter_B_old | 32 | 0.5938 | 13 | 0 | 39112.85 | q03 | -6266.12 | q06 | 13368.51 | 2 |
| B | 2020-2026 | 20260619_1840_quarter_B_recent | 26 | 0.8077 | 5 | 0 | 81307.56 | q15 | -5411.61 | q01 | 15162.31 | 5 |
| C | 2012-2019 | 20260619_1850_quarter_C_old | 32 | 0.5938 | 13 | 0 | 42257.45 | q03 | -6743.74 | q06 | 14424.27 | 2 |
| C | 2020-2026 | 20260619_1900_quarter_C_recent | 26 | 0.8077 | 5 | 0 | 89279.74 | q15 | -5875.11 | q01 | 16796.17 | 5 |

## Interpretation

- B old-window positive rate: 0.5938
- C old-window positive rate: 0.5938
- B recent-window positive rate: 0.8077
- C recent-window positive rate: 0.8077
- Old-window result: both B and C are borderline, not clean enough for unattended month expansion.
- Recent-window result: both B and C are strong, with C keeping the higher-profit challenger profile.

## Decision

Stop before month_core. Keep B as current mainline and C as challenger, but quarter slicing shows old-window concentration risk for both B and C. Do not expand to month_core until losing-quarter clusters are reviewed.

## Next action

1. Review old-window losing-quarter clusters for B and C.
2. Build a true spread path before claiming live-cost robustness.
3. Only after those reviews, run month_core as a controlled follow-up.