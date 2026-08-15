# v8.67 Real Artifact Audit

Generated: 2026-06-20 17:02:11 +08:00

Source index: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_validation_result_index_20260620_165308.csv

Total rows: 375
Real rows (non-DRY_RUN): 363
DRY_RUN rows with missing artifacts: 12
Real rows with missing artifacts: 0

## Decision

No missing artifacts were found in real validation rows. The 12 missing rows from the raw index are all historical DRY_RUN placeholders.

## DRY_RUN Missing Rows

| run_id | module | object | case_id |
|---|---|---|---|
| 20260619_1611_dateshift | dateshift | B | v866_B_dateshift_2012-2019_shift03_r01_case0001 |
| 20260619_1611_dateshift | dateshift | B | v866_B_dateshift_2020-2026_shift03_r01_case0002 |
| 20260619_1611_precheck | precheck | B | v866_B_dateshift_2020-2026_shift00_r01_case0001 |
| 20260619_tdd_quarter_old_green | quarter | B | v866_B_quarter_2012-2019_q01_r01_case0001 |
| 20260619_tdd_quarter_recent_green | quarter | B | v866_B_quarter_2020-2026_q01_r01_case0001 |
| 20260619_tdd_slippage_green | slippage | B | v866_B_slippage_2020-2026_delay100_r01_case0001 |
| 20260620_0452_precheck | precheck | A | v866_A_dateshift_2012-2019_shift00_r01_case0001 |
| 20260620_0452_precheck | precheck | A | v866_A_dateshift_2020-2026_shift00_r01_case0002 |
| 20260620_0452_precheck | precheck | D | v866_D_dateshift_2012-2019_shift00_r01_case0003 |
| 20260620_0452_precheck | precheck | D | v866_D_dateshift_2020-2026_shift00_r01_case0004 |
| 20260620_tdd_monthcluster_B_green | month_cluster | B | v866_B_month_cluster_2012-2019_m201407_r01_case0001 |
| 20260620_tdd_monthcluster_C_green | month_cluster | C | v866_C_month_cluster_2012-2019_m201407_r01_case0001 |