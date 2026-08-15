# v8.67 Spread Feasibility Report - 2026-06-19

## Finding

True spread widening is not executable through the current runner without adding a new mechanism.

## Evidence

- B base set: `v866_2020-2026_control_robust_case0010.set`
- C base set: `v866_2020-2026_control_aggressive_case0005.set`
- Search result: no `Spread`, `Slippage`, `Deviation`, `Cost`, `Commission`, `点差`, or `滑点` input was found in the two active `.set` files.
- Available source-like file found: `D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.66_grokbase_structure_risk.mq5`
- That source file is not the exact active compiled expert name used by B/C: `SniperTrendEA_v8.66_r68_dualperiod_candidate_20260619.ex5`.
- The inspected source has hard-coded trade request deviation lines such as `req.deviation = 20`, but no exposed spread/slippage input parameter.

## Decision

Do not claim spread robustness from the current `slippage` batch.

## Safe next paths

1. Preferred: create controlled MT5 custom symbols with widened spread and run B/C against those symbols.
2. Alternative: add explicit EA inputs for max spread and/or synthetic cost, compile a new candidate, and test that candidate separately.
3. Do not edit the current B/C candidate logic during unattended mode.

## Current unattended action

Proceed to quarter slicing for B/C fixed candidates. This measures time concentration risk and does not require changing EA logic.