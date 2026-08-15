# Report Parser Enhancement (12h Production-Readiness Wrap-up)

Date: 2026-06-20
Scope: improve metric extraction reliability for monthly/quarterly/walk-forward summaries.

## What changed

- File updated: `E:\CODEXMACD\HCSJ\scripts\robust_search_runner.ps1`
- Function updated: `Get-ReportMetrics`
- Added parsing for:
  - buy_trades (count)
  - sell_trades (count)
  - max_consecutive_wins (amount)
  - max_consecutive_losses (amount, keeps sign)
  - max_consecutive_wins_count
  - max_consecutive_losses_count

## New metric csv columns

New `_metrics.csv` files now write the following appended fields:

- buy_trades
- sell_trades
- max_consecutive_winning_trades
- max_consecutive_losing_trades
- max_consecutive_winning_count
- max_consecutive_losing_count

## Evidence

- Validation sample report:
  - `E:\CODEXMACD\HCSJ\backtest_archive\v8.67\2024-2026H1\v867_near_term_extra_2024_20260630\v867_near_term_extra_2024_20260630.htm`
- Parsed example includes:
  - total_trades: 70
  - buy_trades: 48
  - sell_trades: 22
  - max_consecutive_wins_count: 5
  - max_consecutive_losses_count: 5

## Compatibility note

- Existing historical matrix files are kept unchanged.
- New parser fields are additive. Existing consumers can continue using prior fields (`net_profit`, `profit_factor`, etc.).

