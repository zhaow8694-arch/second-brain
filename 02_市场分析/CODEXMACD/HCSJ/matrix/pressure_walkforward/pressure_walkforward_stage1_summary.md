# Pressure Walk-Forward Stage 1 Summary

Generated: 2026-06-20 01:54:45 +08:00

## Paths
- Master matrix: $Master
- Date shift: $DateCsv
- Reverse walk-forward: $RevCsv
- Forward walk-forward: $FwdCsv
- Spread feasibility: $SpreadCsv

## Run counts
- Total rows: 163
- Smoke: 1
- Date shift: 64
- Reverse walk-forward: 48
- Forward walk-forward: 48
- Spread feasibility: 2

## Smoke
- RunId: v866_B_smoke_2020-2026_20260620_012138_case0001
- Status: completed
- Net profit: 556052.56
- PF: 2.27
- Trades: 203

## Date shift
- High sensitivity groups: 0
- Medium sensitivity groups: 7
- Object B high sensitivity groups: 0
- Object C high sensitivity groups: 0

## Walk-forward
- Reverse rows: 48
- Forward rows: 48
- Use validation and sensitivity rows for final decisions, not training profit only.

## Spread feasibility
Result: inconclusive/blocker for true fixed-spread stress. The second run is metadata-only and must not be treated as spread-stress evidence.

## Decisions
- Main candidate: keep v8.66 robust case0010 as main candidate pending spread/slippage/monthly validation
- Aggressive candidate: keep aggressive as observation only; do not promote yet
- Conservative candidate: keep as risk reference.
- v8.6 candidate: keep as reference.

## Next recommended block
Review these summaries first. Then either verify a real MT5 fixed-spread config hook, or move to quarterly breakdown before any v8.67 code changes.