# v8.67 Validation Artifact Audit

Generated: 2026-06-20 16:53:08 +08:00

Index CSV: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_validation_result_index_20260620_165308.csv

Total indexed rows: 375
Rows with missing artifacts: 12

## Module Counts

| module | rows | pass_rows | rows_with_missing_artifacts |
|---|---:|---:|---:|
| dateshift | 82 | 80 | 2 |
| month_cluster | 123 | 121 | 2 |
| precheck | 9 | 4 | 5 |
| quarter | 118 | 116 | 2 |
| slippage | 7 | 6 | 1 |
| wf12 | 18 | 18 | 0 |
| wf20 | 18 | 18 | 0 |

## Latest repaired evidence

- WF A rerun: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1632_wf12\wf_stage_report.md
- WF A/D rerun: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1635_wf12\wf_stage_report.md
- WF A/D old-window rerun: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1636_wf20\wf_stage_report.md
- Month-cluster A/D repaired rerun: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1645_month_cluster\month_cluster_stage_report.md

## Missing Artifact Rows

| run_id | module | object | case_id | missing |
|---|---|---|---|---|
| 20260619_1611_dateshift | dateshift | B | v866_B_dateshift_2012-2019_shift03_r01_case0001 | artifact_html |
| 20260619_1611_dateshift | dateshift | B | v866_B_dateshift_2020-2026_shift03_r01_case0002 | artifact_html |
| 20260619_1611_precheck | precheck | B | v866_B_dateshift_2020-2026_shift00_r01_case0001 | artifact_html |
| 20260619_tdd_quarter_old_green | quarter | B | v866_B_quarter_2012-2019_q01_r01_case0001 | artifact_html |
| 20260619_tdd_quarter_recent_green | quarter | B | v866_B_quarter_2020-2026_q01_r01_case0001 | artifact_html |
| 20260619_tdd_slippage_green | slippage | B | v866_B_slippage_2020-2026_delay100_r01_case0001 | artifact_html |
| 20260620_0452_precheck | precheck | A | v866_A_dateshift_2012-2019_shift00_r01_case0001 | artifact_html |
| 20260620_0452_precheck | precheck | A | v866_A_dateshift_2020-2026_shift00_r01_case0002 | artifact_html |
| 20260620_0452_precheck | precheck | D | v866_D_dateshift_2012-2019_shift00_r01_case0003 | artifact_html |
| 20260620_0452_precheck | precheck | D | v866_D_dateshift_2020-2026_shift00_r01_case0004 | artifact_html |
| 20260620_tdd_monthcluster_B_green | month_cluster | B | v866_B_month_cluster_2012-2019_m201407_r01_case0001 | artifact_html |
| 20260620_tdd_monthcluster_C_green | month_cluster | C | v866_C_month_cluster_2012-2019_m201407_r01_case0001 | artifact_html |