# v8.67 Dateshift A/B/C/D Comparison

Generated: 2026-06-19 16:28:23 +08:00
Runs: 20260619_1600_dateshift_B, 20260619_1630_dateshift_ACD, 20260619_1640_dateshift_C, 20260619_1650_dateshift_D

## Summary Table

| object | window | shift00_profit | median_profit | min_profit | median_retention | min_retention | median_pf | min_trades | max_dd_pct | pass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 2012-2019 | 133752.99 | 133752.99 | 133752.99 | 1 | 1 | 1.22 | 254 | 34.17 | 8/8 |
| B | 2012-2019 | 55826.12 | 55826.12 | 55826.12 | 1 | 1 | 1.17 | 249 | 57.36 | 8/8 |
| C | 2012-2019 | 57221.99 | 57221.99 | 57221.99 | 1 | 1 | 1.15 | 249 | 60.76 | 8/8 |
| D | 2012-2019 | 51100.55 | 51100.55 | 51100.55 | 1 | 1 | 1.19 | 249 | 51.58 | 8/8 |
| A | 2020-2026 | 489512.3 | 419292.26 | 419292.26 | 0.8566 | 0.8566 | 2.07 | 214 | 32.41 | 8/8 |
| B | 2020-2026 | 556052.56 | 501650.99 | 501650.99 | 0.9022 | 0.9022 | 2.26 | 200 | 26.07 | 8/8 |
| C | 2020-2026 | 716968.27 | 642304.43 | 642304.43 | 0.8959 | 0.8959 | 2.28 | 200 | 28.31 | 8/8 |
| D | 2020-2026 | 371235.57 | 340977.3 | 340977.3 | 0.9185 | 0.9185 | 2.23 | 200 | 22.74 | 8/8 |

## Ranking

Recent window 2020-2026 by median_profit:
- C: median_profit=642304.43, median_pf=2.28, min_retention=0.8959, min_trades=200
- B: median_profit=501650.99, median_pf=2.26, min_retention=0.9022, min_trades=200
- A: median_profit=419292.26, median_pf=2.07, min_retention=0.8566, min_trades=214
- D: median_profit=340977.3, median_pf=2.23, min_retention=0.9185, min_trades=200

Old window 2012-2019 by median_profit:
- A: median_profit=133752.99, median_pf=1.22, min_retention=1, min_trades=254
- C: median_profit=57221.99, median_pf=1.15, min_retention=1, min_trades=249
- B: median_profit=55826.12, median_pf=1.17, min_retention=1, min_trades=249
- D: median_profit=51100.55, median_pf=1.19, min_retention=1, min_trades=249

## Interpretation

- A is strongest on 2012-2019 but materially weaker than B/C on 2020-2026.
- C is strongest on 2020-2026 and close to B on 2012-2019, but it is still the aggressive observation candidate and should not replace B without walk-forward confirmation.
- B remains a balanced mainline candidate: not the top recent profit, but passes all dateshift gates and keeps old-window behavior stable.
- D is stable but lower-profit; it remains useful as conservative reference, not as a main replacement.

## Recommended Next Step

Run wf20/wf12 on B and C first. Use B as current mainline, C as challenger. Do not promote C until both walk-forward directions pass.