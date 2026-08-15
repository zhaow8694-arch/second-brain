# v8.67 Dateshift Stage Report

run_id: 20260619_1600_dateshift_B
module: dateshift
objects: B
windows: 2012-2019 / 2020-2026
scenarios: shift00-shift07

## Executive Decision

Decision: Continue
Reason: Both recent and old windows satisfy green aggregate gates.

## Aggregate Snapshot

- 2020-2026 median_retention: 0.9022
- 2020-2026 min_retention: 0.9022
- 2020-2026 median_pf: 2.26
- 2020-2026 min_trades: 200
- 2012-2019 median_pf: 1.17
- 2012-2019 min_trades: 249
- 2012-2019 max_dd_pct: 57.36

## 2020-2026 Recent Window

| scenario | profit | retention | PF | max_dd_pct | trades | gate | reason |
|---|---:|---:|---:|---:|---:|---|---|
| shift00 | 556052.56 | 1 | 2.27 | 26.07 | 203 | Green | meets row gate |
| shift01 | 556052.56 | 1 | 2.27 | 26.07 | 203 | Green | meets row gate |
| shift02 | 556052.56 | 1 | 2.27 | 26.07 | 203 | Green | meets row gate |
| shift03 | 501650.99 | 0.9022 | 2.26 | 26.07 | 200 | Green | meets row gate |
| shift04 | 501650.99 | 0.9022 | 2.26 | 26.07 | 200 | Green | meets row gate |
| shift05 | 501650.99 | 0.9022 | 2.26 | 26.07 | 200 | Green | meets row gate |
| shift06 | 501650.99 | 0.9022 | 2.26 | 26.07 | 200 | Green | meets row gate |
| shift07 | 501650.99 | 0.9022 | 2.26 | 26.07 | 200 | Green | meets row gate |

## 2012-2019 Old Window

| scenario | profit | retention | PF | max_dd_pct | trades | gate | reason |
|---|---:|---:|---:|---:|---:|---|---|
| shift00 | 55826.12 | 1 | 1.17 | 57.35 | 250 | Green | meets row gate |
| shift01 | 55826.12 | 1 | 1.17 | 57.35 | 250 | Green | meets row gate |
| shift02 | 55826.12 | 1 | 1.17 | 57.35 | 250 | Green | meets row gate |
| shift03 | 55826.12 | 1 | 1.17 | 57.35 | 250 | Green | meets row gate |
| shift04 | 55826.12 | 1 | 1.17 | 57.35 | 250 | Green | meets row gate |
| shift05 | 55826.12 | 1 | 1.17 | 57.35 | 250 | Green | meets row gate |
| shift06 | 60042.63 | 1.0755 | 1.17 | 57.36 | 249 | Green | meets row gate |
| shift07 | 60042.63 | 1.0755 | 1.17 | 57.36 | 249 | Green | meets row gate |

## Artifact Index

| case_id | html | metrics | notes |
|---|---|---|---|
| v866_B_dateshift_2012-2019_shift00_r01_case0001 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift00_r01_case0001\v866_B_dateshift_2012-2019_shift00_r01_case0001.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift00_r01_case0001\v866_B_dateshift_2012-2019_shift00_r01_case0001_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift00_r01_case0001\v866_B_dateshift_2012-2019_shift00_r01_case0001_notes.md |
| v866_B_dateshift_2012-2019_shift01_r01_case0003 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift01_r01_case0003\v866_B_dateshift_2012-2019_shift01_r01_case0003.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift01_r01_case0003\v866_B_dateshift_2012-2019_shift01_r01_case0003_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift01_r01_case0003\v866_B_dateshift_2012-2019_shift01_r01_case0003_notes.md |
| v866_B_dateshift_2012-2019_shift02_r01_case0005 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift02_r01_case0005\v866_B_dateshift_2012-2019_shift02_r01_case0005.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift02_r01_case0005\v866_B_dateshift_2012-2019_shift02_r01_case0005_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift02_r01_case0005\v866_B_dateshift_2012-2019_shift02_r01_case0005_notes.md |
| v866_B_dateshift_2012-2019_shift03_r01_case0007 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift03_r01_case0007\v866_B_dateshift_2012-2019_shift03_r01_case0007.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift03_r01_case0007\v866_B_dateshift_2012-2019_shift03_r01_case0007_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift03_r01_case0007\v866_B_dateshift_2012-2019_shift03_r01_case0007_notes.md |
| v866_B_dateshift_2012-2019_shift04_r01_case0009 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift04_r01_case0009\v866_B_dateshift_2012-2019_shift04_r01_case0009.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift04_r01_case0009\v866_B_dateshift_2012-2019_shift04_r01_case0009_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift04_r01_case0009\v866_B_dateshift_2012-2019_shift04_r01_case0009_notes.md |
| v866_B_dateshift_2012-2019_shift05_r01_case0011 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift05_r01_case0011\v866_B_dateshift_2012-2019_shift05_r01_case0011.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift05_r01_case0011\v866_B_dateshift_2012-2019_shift05_r01_case0011_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift05_r01_case0011\v866_B_dateshift_2012-2019_shift05_r01_case0011_notes.md |
| v866_B_dateshift_2012-2019_shift06_r01_case0013 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift06_r01_case0013\v866_B_dateshift_2012-2019_shift06_r01_case0013.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift06_r01_case0013\v866_B_dateshift_2012-2019_shift06_r01_case0013_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift06_r01_case0013\v866_B_dateshift_2012-2019_shift06_r01_case0013_notes.md |
| v866_B_dateshift_2012-2019_shift07_r01_case0015 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift07_r01_case0015\v866_B_dateshift_2012-2019_shift07_r01_case0015.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift07_r01_case0015\v866_B_dateshift_2012-2019_shift07_r01_case0015_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2012-2019\v866_B_dateshift_2012-2019_shift07_r01_case0015\v866_B_dateshift_2012-2019_shift07_r01_case0015_notes.md |
| v866_B_dateshift_2020-2026_shift00_r01_case0002 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift00_r01_case0002\v866_B_dateshift_2020-2026_shift00_r01_case0002.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift00_r01_case0002\v866_B_dateshift_2020-2026_shift00_r01_case0002_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift00_r01_case0002\v866_B_dateshift_2020-2026_shift00_r01_case0002_notes.md |
| v866_B_dateshift_2020-2026_shift01_r01_case0004 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift01_r01_case0004\v866_B_dateshift_2020-2026_shift01_r01_case0004.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift01_r01_case0004\v866_B_dateshift_2020-2026_shift01_r01_case0004_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift01_r01_case0004\v866_B_dateshift_2020-2026_shift01_r01_case0004_notes.md |
| v866_B_dateshift_2020-2026_shift02_r01_case0006 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift02_r01_case0006\v866_B_dateshift_2020-2026_shift02_r01_case0006.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift02_r01_case0006\v866_B_dateshift_2020-2026_shift02_r01_case0006_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift02_r01_case0006\v866_B_dateshift_2020-2026_shift02_r01_case0006_notes.md |
| v866_B_dateshift_2020-2026_shift03_r01_case0008 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift03_r01_case0008\v866_B_dateshift_2020-2026_shift03_r01_case0008.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift03_r01_case0008\v866_B_dateshift_2020-2026_shift03_r01_case0008_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift03_r01_case0008\v866_B_dateshift_2020-2026_shift03_r01_case0008_notes.md |
| v866_B_dateshift_2020-2026_shift04_r01_case0010 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift04_r01_case0010\v866_B_dateshift_2020-2026_shift04_r01_case0010.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift04_r01_case0010\v866_B_dateshift_2020-2026_shift04_r01_case0010_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift04_r01_case0010\v866_B_dateshift_2020-2026_shift04_r01_case0010_notes.md |
| v866_B_dateshift_2020-2026_shift05_r01_case0012 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift05_r01_case0012\v866_B_dateshift_2020-2026_shift05_r01_case0012.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift05_r01_case0012\v866_B_dateshift_2020-2026_shift05_r01_case0012_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift05_r01_case0012\v866_B_dateshift_2020-2026_shift05_r01_case0012_notes.md |
| v866_B_dateshift_2020-2026_shift06_r01_case0014 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift06_r01_case0014\v866_B_dateshift_2020-2026_shift06_r01_case0014.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift06_r01_case0014\v866_B_dateshift_2020-2026_shift06_r01_case0014_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift06_r01_case0014\v866_B_dateshift_2020-2026_shift06_r01_case0014_notes.md |
| v866_B_dateshift_2020-2026_shift07_r01_case0016 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift07_r01_case0016\v866_B_dateshift_2020-2026_shift07_r01_case0016.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift07_r01_case0016\v866_B_dateshift_2020-2026_shift07_r01_case0016_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\2020-2026\v866_B_dateshift_2020-2026_shift07_r01_case0016\v866_B_dateshift_2020-2026_shift07_r01_case0016_notes.md |

## Next Action

Run A/C/D dateshift comparison batch.