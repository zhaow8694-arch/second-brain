# v8.67 B/C Quarter Losing Cluster Review - 2026-06-20

## Inputs

- B old-window matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1830_quarter_B_old\matrix.csv
- C old-window matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1850_quarter_C_old\matrix.csv
- Window: 2012-2019
- Scope: fixed-candidate quarter slicing only

## Executive finding

B and C have the same losing-quarter topology in the old window.

- B losing quarters: 13 / 32
- C losing quarters: 13 / 32
- Shared losing quarters: 13 / 32
- B-only losing quarters: 0
- C-only losing quarters: 0
- B total old-window quarter profit: 39112.85
- C total old-window quarter profit: 42257.45
- B total losing-quarter damage: -42347.31
- C total losing-quarter damage: -46278.36

Interpretation: C is not solving B's old-window weak regimes. C mostly amplifies the same pattern: slightly more profit in strong quarters, but also slightly deeper loss in the same weak quarters.

## Shared losing quarters

| Scenario | Period | B Profit | B PF | B Trades | C Profit | C PF | C Trades | C-B Difference |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| q01 | 2012Q1 | -2533.06 | 0.45 | 10 | -2822.54 | 0.43 | 10 | -289.48 |
| q03 | 2012Q3 | -6266.12 | 0.01 | 9 | -6743.74 | 0.02 | 9 | -477.62 |
| q11 | 2014Q3 | -3025.54 | 0.06 | 8 | -3319.36 | 0.06 | 8 | -293.82 |
| q12 | 2014Q4 | -1985.81 | 0.53 | 10 | -2180.18 | 0.53 | 10 | -194.37 |
| q13 | 2015Q1 | -1920.56 | 0.48 | 10 | -2079.89 | 0.49 | 10 | -159.33 |
| q14 | 2015Q2 | -5047.4 | 0.1 | 8 | -5462.46 | 0.1 | 8 | -415.06 |
| q19 | 2016Q3 | -3325.47 | 0.23 | 9 | -3640.09 | 0.23 | 9 | -314.62 |
| q21 | 2017Q1 | -3204.54 | 0.35 | 8 | -3547.15 | 0.34 | 8 | -342.61 |
| q22 | 2017Q2 | -4849.68 | 0.38 | 12 | -5274.38 | 0.38 | 12 | -424.7 |
| q25 | 2018Q1 | -1048.57 | 0 | 2 | -1152.56 | 0 | 2 | -103.99 |
| q29 | 2019Q1 | -4252.12 | 0.46 | 13 | -4668.08 | 0.46 | 13 | -415.96 |
| q31 | 2019Q3 | -2237.68 | 0.56 | 8 | -2475.51 | 0.55 | 8 | -237.83 |
| q32 | 2019Q4 | -2650.76 | 0.15 | 8 | -2912.42 | 0.14 | 8 | -261.66 |

## Consecutive losing clusters

| Cluster | Quarters | Count | B total | C total | Worst B | Worst C |
|---|---|---:|---:|---:|---|---|
| 2014Q3 to 2015Q2 | q11,q12,q13,q14 | 4 | -11979.31 | -13041.89 | 2015Q2 | 2015Q2 |
| 2017Q1 to 2017Q2 | q21,q22 | 2 | -8054.22 | -8821.53 | 2017Q2 | 2017Q2 |
| 2019Q3 to 2019Q4 | q31,q32 | 2 | -4888.44 | -5387.93 | 2019Q4 | 2019Q4 |
| 2012Q1 to 2012Q1 | q01 | 1 | -2533.06 | -2822.54 | 2012Q1 | 2012Q1 |
| 2019Q1 to 2019Q1 | q29 | 1 | -4252.12 | -4668.08 | 2019Q1 | 2019Q1 |
| 2018Q1 to 2018Q1 | q25 | 1 | -1048.57 | -1152.56 | 2018Q1 | 2018Q1 |
| 2012Q3 to 2012Q3 | q03 | 1 | -6266.12 | -6743.74 | 2012Q3 | 2012Q3 |
| 2016Q3 to 2016Q3 | q19 | 1 | -3325.47 | -3640.09 | 2016Q3 | 2016Q3 |

## Year concentration

| Year | B Profit | C Profit | B Losing Q | C Losing Q | Shared Losing Q |
|---|---:|---:|---:|---:|---:|
| 2012 | -227.29 | -237.6 | 2 | 2 | 2 |
| 2013 | 20148.7 | 21827.63 | 0 | 0 | 0 |
| 2014 | 2105.75 | 2108.02 | 2 | 2 | 2 |
| 2015 | -4132.34 | -4515.03 | 2 | 2 | 2 |
| 2016 | 14338.65 | 15790.59 | 1 | 1 | 1 |
| 2017 | -3036.54 | -3404.32 | 2 | 2 | 2 |
| 2018 | 14324.4 | 15615.83 | 1 | 1 | 1 |
| 2019 | -4408.48 | -4927.67 | 3 | 3 | 3 |

## Worst 5 quarters by B

| Rank | Scenario | Period | B Profit | C Profit | Shared? |
|---:|---|---|---:|---:|---|
| 1 | q03 | 2012Q3 | -6266.12 | -6743.74 | True |
| 2 | q14 | 2015Q2 | -5047.4 | -5462.46 | True |
| 3 | q22 | 2017Q2 | -4849.68 | -5274.38 | True |
| 4 | q29 | 2019Q1 | -4252.12 | -4668.08 | True |
| 5 | q19 | 2016Q3 | -3325.47 | -3640.09 | True |

## Worst 5 quarters by C

| Rank | Scenario | Period | C Profit | B Profit | Shared? |
|---:|---|---|---:|---:|---|
| 1 | q03 | 2012Q3 | -6743.74 | -6266.12 | True |
| 2 | q14 | 2015Q2 | -5462.46 | -5047.4 | True |
| 3 | q22 | 2017Q2 | -5274.38 | -4849.68 | True |
| 4 | q29 | 2019Q1 | -4668.08 | -4252.12 | True |
| 5 | q19 | 2016Q3 | -3640.09 | -3325.47 | True |

## Decision

Do not promote C to mainline from quarter evidence.

B remains current mainline. C remains a same-depth challenger because recent-window returns are stronger, but the old-window losing clusters are structurally shared.

## Next action

1. Do not run unattended month_core yet.
2. Review the shared clusters first: 2014Q3-2015Q2, 2017Q1-2017Q2, and 2019Q3-2019Q4.
3. If month slicing is run later, run it only on these cluster ranges first, not on the full history.
4. Build true spread testing before any live-readiness conclusion.