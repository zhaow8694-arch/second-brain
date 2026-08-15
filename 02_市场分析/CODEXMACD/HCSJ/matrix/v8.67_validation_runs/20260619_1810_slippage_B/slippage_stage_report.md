# WF Stage Report

## Run

- run_id: 20260619_1810_slippage_B
- module: slippage
- objects: B
- generated: 2026-06-19 16:55:41 +08:00

## Cases

| object | module | window | scenario | profit | retention | PF | max_dd_pct | trades | status | decision |
|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| B | slippage | 2020-2026 | delay000 | 556052.56 | 1 | 2.27 | 26.07 | 203 | GREEN | Continue: object passed this WF module. |
| B | slippage | 2020-2026 | delay100 | 556052.56 | 1 | 2.27 | 26.07 | 203 | GREEN | Continue: object passed this WF module. |
| B | slippage | 2020-2026 | delay500 | 556052.56 | 1 | 2.27 | 26.07 | 203 | GREEN | Continue: object passed this WF module. |

## Threshold Result

- decision: Continue
- reason: All WF cases reached GREEN threshold.

## Decision

- B slippage 2020-2026: Continue: object passed this WF module.
- B slippage 2020-2026: Continue: object passed this WF module.
- B slippage 2020-2026: Continue: object passed this WF module.


## Archive Checklist

| case_id | set | ini | html | metrics | notes |
|---|---|---|---|---|---|
| v866_B_slippage_2020-2026_delay000_r01_case0001 | True | True | True | True | True |
| v866_B_slippage_2020-2026_delay100_r01_case0002 | True | True | True | True | True |
| v866_B_slippage_2020-2026_delay500_r01_case0003 | True | True | True | True | True |