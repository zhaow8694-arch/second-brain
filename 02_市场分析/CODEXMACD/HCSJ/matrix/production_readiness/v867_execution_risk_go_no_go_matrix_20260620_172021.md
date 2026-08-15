# v8.67 Execution Risk Go/No-Go Matrix

Generated: 2026-06-20 17:20:21 +08:00

## Decision

**Current decision: NO-GO for real-money live. GO only for demo/forward observation.**

## Evidence Matrix

| area | evidence | status | decision impact |
|---|---|---|---|
| 2020-2026 profit anchor | Existing regression keeps 556,052.56 / PF 2.27 / 203 trades | strong | supports demo/forward |
| Near-boundary regression | E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_near_boundary_regression_20260620_171828.md | completed | adds distribution evidence, not live approval |
| Month-cluster A/B/C/D | E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_month_cluster_abcd_summary_20260620_170142.md | structural weakness, active positive rate 0.3043 | blocks promotion without mitigation |
| Fixed-spread probe | E:\CODEXMACD\HCSJ\matrix\production_readiness\spread_probe_v867_20260620_154834.csv | completed but no metric separation across injected values | remains execution-model blocker |
| Slippage harness | E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_155009\slippage_harness_v867_20260620_155009.csv | completed but synthetic/temporary model | remains insufficient for real-money approval |

## Spread Probe Separation Check

| window | rows | min_profit | max_profit | interpretation |
|---|---:|---:|---:|---|
| 2012-2019 | 3 | 55826.12 | 55826.12 | no separation |
| 2020-2026 | 3 | 556052.56 | 556052.56 | no separation |

## Slippage Harness Separation Check

| object/window | rows | min_profit | max_profit | interpretation |
|---|---:|---:|---:|---|
| B, 2012-2019 | 3 | 55826.12 | 55826.12 | no separation |
| B, 2020-2026 | 3 | 556052.56 | 556052.56 | no separation |
| C, 2012-2019 | 3 | 57221.99 | 57221.99 | no separation |
| C, 2020-2026 | 3 | 716968.27 | 716968.27 | no separation |

## Operating Rule

- Continue demo/forward only.
- Do not treat spread/slippage no-change results as proof of safety.
- Real-money approval requires a broker/execution-level spread and slippage model or verified MT5 setting that changes outcomes measurably.
- Month-cluster weakness needs a mitigation plan before any higher-readiness decision.