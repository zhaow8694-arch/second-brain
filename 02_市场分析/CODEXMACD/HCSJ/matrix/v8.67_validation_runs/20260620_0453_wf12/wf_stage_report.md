# WF Stage Report

## Run

- run_id: 20260620_0453_wf12
- module: wf12
- objects: A/D
- generated: 2026-06-20 04:53:47 +08:00

## Cases

| object | module | window | scenario | profit | retention | PF | max_dd_pct | trades | status | decision |
|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| A | wf12 | 2020-2026 | validate | 489512.30 |  | 2.07 | 32.41 | 215 | FAIL_ELIMINATED | Stop: object failed a required WF threshold. |
| A | wf12 | 2020-2026 | validate | 489512.30 |  | 2.07 | 32.41 | 215 | FAIL_ELIMINATED | Stop: object failed a required WF threshold. |
| D | wf12 | 2020-2026 | validate | 371235.57 |  | 2.23 | 22.74 | 203 | FAIL_ELIMINATED | Stop: object failed a required WF threshold. |
| D | wf12 | 2020-2026 | validate | 371235.57 |  | 2.23 | 22.74 | 203 | FAIL_ELIMINATED | Stop: object failed a required WF threshold. |

## Threshold Result

- decision: Stop
- reason: 4 WF case(s) failed threshold or archive checks.

## Decision

- A wf12 2020-2026: Stop: object failed a required WF threshold.
- A wf12 2020-2026: Stop: object failed a required WF threshold.
- D wf12 2020-2026: Stop: object failed a required WF threshold.
- D wf12 2020-2026: Stop: object failed a required WF threshold.


## Archive Checklist

| case_id | set | ini | html | metrics | notes |
|---|---|---|---|---|---|
| v866_A_wf12_2020-2026_validate_r01_case0001 | True | True | True | True | True |
| v866_A_wf12_2020-2026_validate_r01_case0002 | True | True | True | True | True |
| v866_D_wf12_2020-2026_validate_r01_case0003 | True | True | True | True | True |
| v866_D_wf12_2020-2026_validate_r01_case0004 | True | True | True | True | True |