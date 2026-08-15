# Month Cluster Stage Report

## Run

- run_id: 20260620_1110_monthcluster_C_m201408_diag
- module: month_cluster
- objects: C
- windows: 2012-2019
- generated: 2026-06-20 01:05:40 +08:00

## Aggregate

- completed_cases: 1 / 1
- green_months: 0
- losing_months: 0
- failed_months: 1
- positive_rate: 0
- total_profit: 0
- min_trades: 0

## Decision

- decision: Stop
- reason: 1 month_cluster case(s) failed report/archive or zero-trade checks.
- next_action: Stop and review failed month artifacts.

## Cases

| scenario | profit | PF | max_dd_pct | trades | status | decision |
|---|---:|---:|---:|---:|---|---|
| m201408 | 0.00 | 0.00 | 0.00 | 0 | FAIL_ZERO_TRADES | Stop: zero-trade month. |