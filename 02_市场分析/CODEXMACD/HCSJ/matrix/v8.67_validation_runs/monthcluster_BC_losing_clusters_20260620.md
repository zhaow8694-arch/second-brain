# v8.67 B/C Month Cluster Losing Clusters - 2026-06-20

## Status

STOPPED_AFTER_B_ZERO_TRADES

## Why C was not run

The agreed stop condition was triggered during the B month-cluster batch: any zero-trade month stops expansion.

- B run: 20260620_1010_monthcluster_B_old
- B cases completed: 24
- Zero-trade months: 1
- Losing months: 16
- Green months: 7
- Red months: 16
- Failed months: 1

The zero-trade month is:

- 2014-08 / m201408: profit=0.00, PF=0.00, trades=0, status=FAIL_ZERO_TRADES


## B monthly cluster table

| Month | Scenario | B Profit | PF | Trades | Status | Decision |
|---|---|---:|---:|---:|---|---|
| 2014-07 | m201407 | -2046.09 | 0.00 | 3 | RED | Losing month. |
| 2014-08 | m201408 | 0.00 | 0.00 | 0 | FAIL_ZERO_TRADES | Stop: zero-trade month. |
| 2014-09 | m201409 | -433.68 | 0.33 | 4 | RED | Losing month. |
| 2014-10 | m201410 | 253.52 | 1.18 | 5 | GREEN | Profitable month. |
| 2014-11 | m201411 | -1947.95 | 0.00 | 2 | RED | Losing month. |
| 2014-12 | m201412 | -304.38 | 0.70 | 3 | RED | Losing month. |
| 2015-01 | m201501 | 1519.23 | 16.04 | 2 | GREEN | Profitable month. |
| 2015-02 | m201502 | -2350.26 | 0.04 | 5 | RED | Losing month. |
| 2015-03 | m201503 | -952.45 | 0.06 | 3 | RED | Losing month. |
| 2015-04 | m201504 | -1887.46 | 0.20 | 4 | RED | Losing month. |
| 2015-05 | m201505 | -1452.03 | 0.26 | 3 | RED | Losing month. |
| 2015-06 | m201506 | 120.56 | 0.00 | 1 | GREEN | Profitable month. |
| 2017-01 | m201701 | -3181.82 | 0.16 | 5 | RED | Losing month. |
| 2017-02 | m201702 | 824.36 | 1.83 | 2 | GREEN | Profitable month. |
| 2017-03 | m201703 | -373.76 | 0.00 | 1 | RED | Losing month. |
| 2017-04 | m201704 | 401.63 | 1.18 | 3 | GREEN | Profitable month. |
| 2017-05 | m201705 | -3062.67 | 0.08 | 5 | RED | Losing month. |
| 2017-06 | m201706 | -2452.92 | 0.02 | 4 | RED | Losing month. |
| 2019-07 | m201907 | 434.19 | 1.42 | 2 | GREEN | Profitable month. |
| 2019-08 | m201908 | -968.38 | 0.69 | 5 | RED | Losing month. |
| 2019-09 | m201909 | -1039.13 | 0.00 | 1 | RED | Losing month. |
| 2019-10 | m201910 | -2000.80 | 0.00 | 3 | RED | Losing month. |
| 2019-11 | m201911 | -900.10 | 0.10 | 3 | RED | Losing month. |
| 2019-12 | m201912 | 184.94 | 1.81 | 2 | GREEN | Profitable month. |

## Worst B months

| Rank | Month | Scenario | Profit | PF | Trades |
|---:|---|---|---:|---:|---:|
| 1 | 2017-01 | m201701 | -3181.82 | 0.16 | 5 |
| 2 | 2017-05 | m201705 | -3062.67 | 0.08 | 5 |
| 3 | 2017-06 | m201706 | -2452.92 | 0.02 | 4 |
| 4 | 2015-02 | m201502 | -2350.26 | 0.04 | 5 |
| 5 | 2014-07 | m201407 | -2046.09 | 0.00 | 3 |
| 6 | 2019-10 | m201910 | -2000.80 | 0.00 | 3 |
| 7 | 2014-11 | m201411 | -1947.95 | 0.00 | 2 |
| 8 | 2015-04 | m201504 | -1887.46 | 0.20 | 4 |

## Interpretation

The old-window weak clusters are not only loss clusters; they also include a signal/sampling gap month (m201408) with zero trades. That makes full month_core expansion unsafe until we decide whether zero-trade months should be treated as acceptable inactivity or as a strategy coverage failure.

## Decision

- Do not run C month_cluster automatically.
- Do not run full month_core.
- Keep B as current mainline, but mark old-window losing clusters as requiring manual review.
- Keep C as challenger; C month_cluster should only run after the zero-trade rule is clarified.

## Next choices

1. Treat zero-trade month as hard failure and stop this branch for manual strategy review.
2. Treat zero-trade month as acceptable inactivity, then explicitly approve running C month_cluster.
3. Run a narrower manual replay around 2014-08 to inspect why B produced no trades.