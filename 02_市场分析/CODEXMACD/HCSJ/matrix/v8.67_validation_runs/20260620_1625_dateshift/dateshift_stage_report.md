# v8.67 Dateshift Stage Report

run_id: 20260620_1625_dateshift
module: dateshift
objects: A
windows: 2012-2019 / 2020-2026
scenarios: shift00-shift07

## Executive Decision

Decision: Continue
Reason: Both recent and old windows satisfy green aggregate gates.

## Aggregate Snapshot

- 2020-2026 median_retention: 0.8566
- 2020-2026 min_retention: 0.8566
- 2020-2026 median_pf: 2.07
- 2020-2026 min_trades: 214
- 2012-2019 median_pf: 1.22
- 2012-2019 min_trades: 254
- 2012-2019 max_dd_pct: 34.17

## 2020-2026 Recent Window

| scenario | profit | retention | PF | max_dd_pct | trades | gate | reason |
|---|---:|---:|---:|---:|---:|---|---|
| shift00 | 489512.30 | 1 | 2.07 | 32.41 | 215 | Green | meets row gate |
| shift01 | 489512.30 | 1 | 2.07 | 32.41 | 215 | Green | meets row gate |
| shift02 | 489512.30 | 1 | 2.07 | 32.41 | 215 | Green | meets row gate |
| shift03 | 419292.26 | 0.8566 | 2.07 | 32.38 | 214 | Green | meets row gate |
| shift04 | 419292.26 | 0.8566 | 2.07 | 32.38 | 214 | Green | meets row gate |
| shift05 | 419292.26 | 0.8566 | 2.07 | 32.38 | 214 | Green | meets row gate |
| shift06 | 419292.26 | 0.8566 | 2.07 | 32.38 | 214 | Green | meets row gate |
| shift07 | 419292.26 | 0.8566 | 2.07 | 32.38 | 214 | Green | meets row gate |

## 2012-2019 Old Window

| scenario | profit | retention | PF | max_dd_pct | trades | gate | reason |
|---|---:|---:|---:|---:|---:|---|---|
| shift00 | 133752.99 | 1 | 1.22 | 34.17 | 255 | Green | meets row gate |
| shift01 | 133752.99 | 1 | 1.22 | 34.17 | 255 | Green | meets row gate |
| shift02 | 133752.99 | 1 | 1.22 | 34.17 | 255 | Green | meets row gate |
| shift03 | 133752.99 | 1 | 1.22 | 34.17 | 255 | Green | meets row gate |
| shift04 | 133752.99 | 1 | 1.22 | 34.17 | 255 | Green | meets row gate |
| shift05 | 133752.99 | 1 | 1.22 | 34.17 | 255 | Green | meets row gate |
| shift06 | 141981.65 | 1.0615 | 1.22 | 34.17 | 254 | Green | meets row gate |
| shift07 | 141981.65 | 1.0615 | 1.22 | 34.17 | 254 | Green | meets row gate |

## Artifact Index

| case_id | html | metrics | notes |
|---|---|---|---|
| v866_A_dateshift_2012-2019_shift00_r01_case0001 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift00_r01_case0001\v866_A_dateshift_2012-2019_shift00_r01_case0001.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift00_r01_case0001\v866_A_dateshift_2012-2019_shift00_r01_case0001_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift00_r01_case0001\v866_A_dateshift_2012-2019_shift00_r01_case0001_notes.md |
| v866_A_dateshift_2012-2019_shift01_r01_case0003 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift01_r01_case0003\v866_A_dateshift_2012-2019_shift01_r01_case0003.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift01_r01_case0003\v866_A_dateshift_2012-2019_shift01_r01_case0003_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift01_r01_case0003\v866_A_dateshift_2012-2019_shift01_r01_case0003_notes.md |
| v866_A_dateshift_2012-2019_shift02_r01_case0005 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift02_r01_case0005\v866_A_dateshift_2012-2019_shift02_r01_case0005.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift02_r01_case0005\v866_A_dateshift_2012-2019_shift02_r01_case0005_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift02_r01_case0005\v866_A_dateshift_2012-2019_shift02_r01_case0005_notes.md |
| v866_A_dateshift_2012-2019_shift03_r01_case0007 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift03_r01_case0007\v866_A_dateshift_2012-2019_shift03_r01_case0007.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift03_r01_case0007\v866_A_dateshift_2012-2019_shift03_r01_case0007_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift03_r01_case0007\v866_A_dateshift_2012-2019_shift03_r01_case0007_notes.md |
| v866_A_dateshift_2012-2019_shift04_r01_case0009 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift04_r01_case0009\v866_A_dateshift_2012-2019_shift04_r01_case0009.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift04_r01_case0009\v866_A_dateshift_2012-2019_shift04_r01_case0009_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift04_r01_case0009\v866_A_dateshift_2012-2019_shift04_r01_case0009_notes.md |
| v866_A_dateshift_2012-2019_shift05_r01_case0011 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift05_r01_case0011\v866_A_dateshift_2012-2019_shift05_r01_case0011.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift05_r01_case0011\v866_A_dateshift_2012-2019_shift05_r01_case0011_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift05_r01_case0011\v866_A_dateshift_2012-2019_shift05_r01_case0011_notes.md |
| v866_A_dateshift_2012-2019_shift06_r01_case0013 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift06_r01_case0013\v866_A_dateshift_2012-2019_shift06_r01_case0013.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift06_r01_case0013\v866_A_dateshift_2012-2019_shift06_r01_case0013_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift06_r01_case0013\v866_A_dateshift_2012-2019_shift06_r01_case0013_notes.md |
| v866_A_dateshift_2012-2019_shift07_r01_case0015 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift07_r01_case0015\v866_A_dateshift_2012-2019_shift07_r01_case0015.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift07_r01_case0015\v866_A_dateshift_2012-2019_shift07_r01_case0015_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2012-2019\v866_A_dateshift_2012-2019_shift07_r01_case0015\v866_A_dateshift_2012-2019_shift07_r01_case0015_notes.md |
| v866_A_dateshift_2020-2026_shift00_r01_case0002 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift00_r01_case0002\v866_A_dateshift_2020-2026_shift00_r01_case0002.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift00_r01_case0002\v866_A_dateshift_2020-2026_shift00_r01_case0002_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift00_r01_case0002\v866_A_dateshift_2020-2026_shift00_r01_case0002_notes.md |
| v866_A_dateshift_2020-2026_shift01_r01_case0004 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift01_r01_case0004\v866_A_dateshift_2020-2026_shift01_r01_case0004.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift01_r01_case0004\v866_A_dateshift_2020-2026_shift01_r01_case0004_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift01_r01_case0004\v866_A_dateshift_2020-2026_shift01_r01_case0004_notes.md |
| v866_A_dateshift_2020-2026_shift02_r01_case0006 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift02_r01_case0006\v866_A_dateshift_2020-2026_shift02_r01_case0006.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift02_r01_case0006\v866_A_dateshift_2020-2026_shift02_r01_case0006_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift02_r01_case0006\v866_A_dateshift_2020-2026_shift02_r01_case0006_notes.md |
| v866_A_dateshift_2020-2026_shift03_r01_case0008 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift03_r01_case0008\v866_A_dateshift_2020-2026_shift03_r01_case0008.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift03_r01_case0008\v866_A_dateshift_2020-2026_shift03_r01_case0008_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift03_r01_case0008\v866_A_dateshift_2020-2026_shift03_r01_case0008_notes.md |
| v866_A_dateshift_2020-2026_shift04_r01_case0010 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift04_r01_case0010\v866_A_dateshift_2020-2026_shift04_r01_case0010.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift04_r01_case0010\v866_A_dateshift_2020-2026_shift04_r01_case0010_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift04_r01_case0010\v866_A_dateshift_2020-2026_shift04_r01_case0010_notes.md |
| v866_A_dateshift_2020-2026_shift05_r01_case0012 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift05_r01_case0012\v866_A_dateshift_2020-2026_shift05_r01_case0012.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift05_r01_case0012\v866_A_dateshift_2020-2026_shift05_r01_case0012_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift05_r01_case0012\v866_A_dateshift_2020-2026_shift05_r01_case0012_notes.md |
| v866_A_dateshift_2020-2026_shift06_r01_case0014 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift06_r01_case0014\v866_A_dateshift_2020-2026_shift06_r01_case0014.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift06_r01_case0014\v866_A_dateshift_2020-2026_shift06_r01_case0014_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift06_r01_case0014\v866_A_dateshift_2020-2026_shift06_r01_case0014_notes.md |
| v866_A_dateshift_2020-2026_shift07_r01_case0016 | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift07_r01_case0016\v866_A_dateshift_2020-2026_shift07_r01_case0016.htm | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift07_r01_case0016\v866_A_dateshift_2020-2026_shift07_r01_case0016_metrics.csv | E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\2020-2026\v866_A_dateshift_2020-2026_shift07_r01_case0016\v866_A_dateshift_2020-2026_shift07_r01_case0016_notes.md |

## Next Action

Run A/C/D dateshift comparison batch.