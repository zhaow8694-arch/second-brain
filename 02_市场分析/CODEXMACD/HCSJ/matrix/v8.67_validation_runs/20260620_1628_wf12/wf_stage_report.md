# WF Stage Report

## Run

- run_id: 20260620_1628_wf12
- module: wf12
- objects: A
- generated: 2026-06-20 16:29:08 +08:00

## Cases

| object | module | window | scenario | profit | retention | PF | max_dd_pct | trades | status | decision |
|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| A | wf12 | 2020-2026 | validate | 489512.30 |  | 2.07 | 32.41 | 215 | FAIL_ELIMINATED | Stop: object failed a required WF threshold. |
| A | wf12 | 2020-2026 | validate | 489512.30 |  | 2.07 | 32.41 | 215 | FAIL_ELIMINATED | Stop: object failed a required WF threshold. |

## Threshold Result

- decision: Stop
- reason: 2 WF case(s) failed threshold or archive checks.

## Decision

- A wf12 2020-2026: Stop: object failed a required WF threshold.
- A wf12 2020-2026: Stop: object failed a required WF threshold.


## Archive Checklist

| case_id | set | ini | html | metrics | notes |
|---|---|---|---|---|---|
| v866_A_wf12_2020-2026_validate_r01_case0001 | True | True | True | True | True |
| v866_A_wf12_2020-2026_validate_r01_case0002 | True | True | True | True | True |