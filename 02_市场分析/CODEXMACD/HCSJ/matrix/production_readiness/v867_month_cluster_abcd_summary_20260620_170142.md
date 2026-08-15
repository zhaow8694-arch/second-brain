# v8.67 Month-Cluster A/B/C/D Summary

Generated: 2026-06-20 17:01:42 +08:00

## Source Runs

- A/D repaired run: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1645_month_cluster\matrix.csv
- B/C repaired run: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1653_month_cluster\matrix.csv

## Summary

| object | total | active | green | red | no_trade | active_positive_rate | total_net_profit | worst | best |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| A | 24 | 23 | 23 | 23 | 23 | 1 | -21091.98 | m201701 -3152.39 | m201501 1800.26 |
| B | 24 | 23 | 23 | 23 | 23 | 1 | -21615.45 | m201701 -3181.82 | m201501 1519.23 |
| C | 24 | 23 | 23 | 23 | 23 | 1 | -23720.62 | m201701 -3506.87 | m201501 1689.26 |
| D | 24 | 23 | 23 | 23 | 23 | 1 | -18540.58 | m201701 -2767.08 | m201501 1301.79 |

## Interpretation

- All four objects have the same active hit profile in this losing-month cluster: 7 profitable active months out of 23 active months, plus 1 no-trade month.
- This confirms the month-cluster weakness is structural to the shared signal family, not only a single-parameter accident in B.
- The result is a stability warning, not an execution-chain blocker: all report/set/ini/metrics/notes artifacts were generated.
- Action: keep readiness at demo/forward level; do not use this evidence to approve real-money live deployment.