# v8.67 Unattended 1h Month Cluster Scope - 2026-06-20

## Goal

Run targeted monthly slices for the B/C shared losing quarter clusters found in the 2012-2019 old window.

## Scope

Only these months are allowed:

- 2014.07 through 2015.06
- 2017.01 through 2017.06
- 2019.07 through 2019.12

## Non-goals

- Do not run full `month_core`.
- Do not edit EA trading logic.
- Do not create or modify custom-symbol spread data.
- Do not promote C to mainline from this batch.

## Expected runs

- `20260620_1010_monthcluster_B_old`
- `20260620_1020_monthcluster_C_old`

## Expected artifacts

- 48 total monthly cases.
- Per-case five-piece archive.
- Per-run `matrix.csv`.
- Per-run `month_cluster_stage_report.md`.
- Combined `monthcluster_BC_losing_clusters_20260620.md`.
- `WORK_LOG.md` entry.

## Stop conditions

- Two consecutive no-report failures.
- Any zero-trade month.
- Any completed case missing five-piece archive.
- `terminal64.exe` remains after timeout cleanup.
- Dry-run dates are incorrect.
