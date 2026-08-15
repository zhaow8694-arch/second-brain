# v8.67 B/C Slippage Comparison - 2026-06-19

## Scope

This batch tests MT5 ExecutionMode delay sensitivity only.
It does not test spread widening because the current B/C .set files do not expose a spread input and the MT5 startup config documentation does not provide a direct spread override for tester runs.

## Source runs

| RunId | Object | Window | Scenarios |
|---|---|---|---|
| 20260619_1810_slippage_B | B | 2020-2026 | delay000, delay100, delay500 |
| 20260619_1815_slippage_C | C | 2020-2026 | delay000, delay100, delay500 |

## Metrics

| Object | Scenario | Profit | PF | Trades | Max DD% | Retention | Status |
|---|---|---:|---:|---:|---:|---:|---|
| B | delay000 | 556052.56 | 2.27 | 203 | 26.07 | 1 | GREEN |
| B | delay100 | 556052.56 | 2.27 | 203 | 26.07 | 1 | GREEN |
| B | delay500 | 556052.56 | 2.27 | 203 | 26.07 | 1 | GREEN |
| C | delay000 | 716968.27 | 2.29 | 203 | 28.31 | 1 | GREEN |
| C | delay100 | 716968.27 | 2.29 | 203 | 28.31 | 1 | GREEN |
| C | delay500 | 716968.27 | 2.29 | 203 | 28.31 | 1 | GREEN |

## Interpretation

- All scenarios GREEN: True
- B profit unchanged across delay scenarios: True
- C profit unchanged across delay scenarios: True
- This suggests the current EA/test setup is not materially sensitive to MT5 ExecutionMode delays at 0/100/500 ms.
- Because spread was not actually widened, spread validation remains open.

## Decision

B and C both pass ExecutionMode slippage-delay stress. Keep B as current mainline; keep C as equal-depth challenger. Do not treat this as spread validation.

## Next Action

Build a real spread test path before claiming spread robustness: either add/confirm EA spread input support, or create controlled custom-symbol spread variants in MT5.