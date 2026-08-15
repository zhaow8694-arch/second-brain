# v8.67 Dateshift Stage Report

run_id: 20260619_1650_dateshift_D
module: dateshift
objects: D
windows: 2012-2019 / 2020-2026
scenarios: shift00-shift07

## Executive Decision

Decision: Continue
Reason: Both recent and old windows satisfy green aggregate gates.

## Aggregate Snapshot

- 2020-2026 median_retention: 0.9185
- 2020-2026 min_retention: 0.9185
- 2020-2026 median_pf: 2.23
- 2020-2026 min_trades: 200
- 2012-2019 median_pf: 1.19
- 2012-2019 min_trades: 249
- 2012-2019 max_dd_pct: 51.58

## 2020-2026 Recent Window

| scenario | profit | retention | PF | max_dd_pct | trades | gate | reason |
|---|---:|---:|---:|---:|---:|---|---|
| shift00 | 371235.57 | 1 | 2.23 | 22.74 | 203 | Green | meets row gate |
| shift01 | 371235.57 | 1 | 2.23 | 22.74 | 203 | Green | meets row gate |
| shift02 | 371235.57 | 1 | 2.23 | 22.74 | 203 | Green | meets row gate |
| shift03 | 340977.30 | 0.9185 | 2.23 | 22.70 | 200 | Green | meets row gate |
| shift04 | 340977.30 | 0.9185 | 2.23 | 22.70 | 200 | Green | meets row gate |
| shift05 | 340977.30 | 0.9185 | 2.23 | 22.70 | 200 | Green | meets row gate |
| shift06 | 340977.30 | 0.9185 | 2.23 | 22.70 | 200 | Green | meets row gate |
| shift07 | 340977.30 | 0.9185 | 2.23 | 22.70 | 200 | Green | meets row gate |

## 2012-2019 Old Window

| scenario | profit | retention | PF | max_dd_pct | trades | gate | reason |
|---|---:|---:|---:|---:|---:|---|---|
| shift00 | 51100.55 | 1 | 1.19 | 51.58 | 250 | Green | meets row gate |
| shift01 | 51100.55 | 1 | 1.19 | 51.58 | 250 | Green | meets row gate |
| shift02 | 51100.55 | 1 | 1.19 | 51.58 | 250 | Green | meets row gate |
| shift03 | 51100.55 | 1 | 1.19 | 51.58 | 250 | Green | meets row gate |
| shift04 | 51100.55 | 1 | 1.19 | 51.58 | 250 | Green | meets row gate |
| shift05 | 51100.55 | 1 | 1.19 | 51.58 | 250 | Green | meets row gate |
| shift06 | 54152.16 | 1.0597 | 1.20 | 51.55 | 249 | Green | meets row gate |
| shift07 | 54152.16 | 1.0597 | 1.20 | 51.55 | 249 | Green | meets row gate |

## Artifact Index

| case_id | html | metrics | notes |
|---|---|---|---|
| v866_D_dateshift_2012-2019_shift00_r01_case0001 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift00_r01_case0001\v866_D_dateshift_2012-2019_shift00_r01_case0001.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift00_r01_case0001\v866_D_dateshift_2012-2019_shift00_r01_case0001_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift00_r01_case0001\v866_D_dateshift_2012-2019_shift00_r01_case0001_notes.md |
| v866_D_dateshift_2012-2019_shift01_r01_case0003 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift01_r01_case0003\v866_D_dateshift_2012-2019_shift01_r01_case0003.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift01_r01_case0003\v866_D_dateshift_2012-2019_shift01_r01_case0003_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift01_r01_case0003\v866_D_dateshift_2012-2019_shift01_r01_case0003_notes.md |
| v866_D_dateshift_2012-2019_shift02_r01_case0005 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift02_r01_case0005\v866_D_dateshift_2012-2019_shift02_r01_case0005.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift02_r01_case0005\v866_D_dateshift_2012-2019_shift02_r01_case0005_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift02_r01_case0005\v866_D_dateshift_2012-2019_shift02_r01_case0005_notes.md |
| v866_D_dateshift_2012-2019_shift03_r01_case0007 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift03_r01_case0007\v866_D_dateshift_2012-2019_shift03_r01_case0007.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift03_r01_case0007\v866_D_dateshift_2012-2019_shift03_r01_case0007_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift03_r01_case0007\v866_D_dateshift_2012-2019_shift03_r01_case0007_notes.md |
| v866_D_dateshift_2012-2019_shift04_r01_case0009 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift04_r01_case0009\v866_D_dateshift_2012-2019_shift04_r01_case0009.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift04_r01_case0009\v866_D_dateshift_2012-2019_shift04_r01_case0009_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift04_r01_case0009\v866_D_dateshift_2012-2019_shift04_r01_case0009_notes.md |
| v866_D_dateshift_2012-2019_shift05_r01_case0011 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift05_r01_case0011\v866_D_dateshift_2012-2019_shift05_r01_case0011.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift05_r01_case0011\v866_D_dateshift_2012-2019_shift05_r01_case0011_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift05_r01_case0011\v866_D_dateshift_2012-2019_shift05_r01_case0011_notes.md |
| v866_D_dateshift_2012-2019_shift06_r01_case0013 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift06_r01_case0013\v866_D_dateshift_2012-2019_shift06_r01_case0013.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift06_r01_case0013\v866_D_dateshift_2012-2019_shift06_r01_case0013_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift06_r01_case0013\v866_D_dateshift_2012-2019_shift06_r01_case0013_notes.md |
| v866_D_dateshift_2012-2019_shift07_r01_case0015 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift07_r01_case0015\v866_D_dateshift_2012-2019_shift07_r01_case0015.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift07_r01_case0015\v866_D_dateshift_2012-2019_shift07_r01_case0015_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2012-2019\v866_D_dateshift_2012-2019_shift07_r01_case0015\v866_D_dateshift_2012-2019_shift07_r01_case0015_notes.md |
| v866_D_dateshift_2020-2026_shift00_r01_case0002 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift00_r01_case0002\v866_D_dateshift_2020-2026_shift00_r01_case0002.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift00_r01_case0002\v866_D_dateshift_2020-2026_shift00_r01_case0002_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift00_r01_case0002\v866_D_dateshift_2020-2026_shift00_r01_case0002_notes.md |
| v866_D_dateshift_2020-2026_shift01_r01_case0004 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift01_r01_case0004\v866_D_dateshift_2020-2026_shift01_r01_case0004.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift01_r01_case0004\v866_D_dateshift_2020-2026_shift01_r01_case0004_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift01_r01_case0004\v866_D_dateshift_2020-2026_shift01_r01_case0004_notes.md |
| v866_D_dateshift_2020-2026_shift02_r01_case0006 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift02_r01_case0006\v866_D_dateshift_2020-2026_shift02_r01_case0006.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift02_r01_case0006\v866_D_dateshift_2020-2026_shift02_r01_case0006_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift02_r01_case0006\v866_D_dateshift_2020-2026_shift02_r01_case0006_notes.md |
| v866_D_dateshift_2020-2026_shift03_r01_case0008 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift03_r01_case0008\v866_D_dateshift_2020-2026_shift03_r01_case0008.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift03_r01_case0008\v866_D_dateshift_2020-2026_shift03_r01_case0008_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift03_r01_case0008\v866_D_dateshift_2020-2026_shift03_r01_case0008_notes.md |
| v866_D_dateshift_2020-2026_shift04_r01_case0010 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift04_r01_case0010\v866_D_dateshift_2020-2026_shift04_r01_case0010.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift04_r01_case0010\v866_D_dateshift_2020-2026_shift04_r01_case0010_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift04_r01_case0010\v866_D_dateshift_2020-2026_shift04_r01_case0010_notes.md |
| v866_D_dateshift_2020-2026_shift05_r01_case0012 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift05_r01_case0012\v866_D_dateshift_2020-2026_shift05_r01_case0012.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift05_r01_case0012\v866_D_dateshift_2020-2026_shift05_r01_case0012_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift05_r01_case0012\v866_D_dateshift_2020-2026_shift05_r01_case0012_notes.md |
| v866_D_dateshift_2020-2026_shift06_r01_case0014 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift06_r01_case0014\v866_D_dateshift_2020-2026_shift06_r01_case0014.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift06_r01_case0014\v866_D_dateshift_2020-2026_shift06_r01_case0014_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift06_r01_case0014\v866_D_dateshift_2020-2026_shift06_r01_case0014_notes.md |
| v866_D_dateshift_2020-2026_shift07_r01_case0016 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift07_r01_case0016\v866_D_dateshift_2020-2026_shift07_r01_case0016.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift07_r01_case0016\v866_D_dateshift_2020-2026_shift07_r01_case0016_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\2020-2026\v866_D_dateshift_2020-2026_shift07_r01_case0016\v866_D_dateshift_2020-2026_shift07_r01_case0016_notes.md |

## Next Action

Run A/C/D dateshift comparison batch.