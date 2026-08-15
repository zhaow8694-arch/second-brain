# v8.67 Dateshift A/B/C/D Summary

Generated: 2026-06-20 17:04:17 +08:00

## Selected Runs

- A: 20260620_1625_dateshift
- B: 20260619_1600_dateshift_B
- C: 20260619_1640_dateshift_C
- D: 20260619_1650_dateshift_D

## Summary

| object | window | cases | min_profit | max_profit | min_pf | min_trades | max_dd_pct | rating |
|---|---|---:|---:|---:|---:|---:|---:|---|
| A | 2012-2019 | 8 | 133752.99 | 141981.65 | 1.22 | 254 | 34.17 | medium |
| A | 2020-2026 | 8 | 419292.26 | 489512.3 | 2.07 | 214 | 32.41 | low |
| B | 2012-2019 | 8 | 55826.12 | 60042.63 | 1.17 | 249 | 57.36 | medium |
| B | 2020-2026 | 8 | 501650.99 | 556052.56 | 2.26 | 200 | 26.07 | low |
| C | 2012-2019 | 8 | 57221.99 | 61819.05 | 1.15 | 249 | 60.76 | medium |
| C | 2020-2026 | 8 | 642304.43 | 716968.27 | 2.28 | 200 | 28.31 | low |
| D | 2012-2019 | 8 | 51100.55 | 54152.16 | 1.19 | 249 | 51.58 | medium |
| D | 2020-2026 | 8 | 340977.3 | 371235.57 | 2.23 | 200 | 22.74 | low |

## Interpretation

- No selected dateshift group produced non-positive total-window profit.
- Older 2012-2019 windows generally carry weaker PF than 2020-2026, so the strategy family remains regime-sensitive.
- Dateshift evidence does not by itself prove severe fixed-year overfit, but it also does not remove the monthly-cluster warning.