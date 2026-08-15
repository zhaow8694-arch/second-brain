# 2026-06-20 Fixed-Spread & Slippage Execution Continuation Plan

## 1. Why continuation is needed

The current 12-hour production-readiness block finished with:
- fixed-spread blocker as unresolved/inconclusive
- slippage test as requires-temp-ea or external execution simulation

No synthetic result was used to claim spread/slippage pass.

## 2. Objective

Deliver verifiable and reproducible evidence for two missing execution-risk dimensions before any live deployment step.

## 3. Phase A - Verified fixed-spread route (priority)

1. Verify MT5 tester accepts explicit fixed-spread settings in environment.
2. Document exact validated variable in:
   - terminal config
   - `.ini` / CLI args
   - report evidence path
3. If verified, run a minimal spread matrix for object B:
   - v8.67 candidate set (`...v8.67_grokbase_production_ready_default_case0010.set`)
   - levels: 1.0x, 1.5x, 2.0x
   - windows: 2012-2019, 2020-2026
   - export per-run metrics + note changes in win/loss behavior

## 4. Phase B - Slippage model route

1. Implement temporary slippage simulation harness (do not change production EA logic):
   - fixed input seed
   - explicit slippage injection before order placement/closure
   - log fields: intended price, filled price, slippage pips, signal direction, reject/retry counts
2. Run the following levels first:
   - 0, 1, 2, 3, 5
3. Keep v8.67 core logic unchanged in main `.mq5` during this phase.

## 5. Decision gates

- If both execution-risk controls are verified and B candidate stability remains acceptable:
  - prepare for micro-lot observation review
- If either route fails:
  - stay at demo-only and keep execution-risk notes open

## 6. Output artifacts

- fixed-spread test matrix CSV + notes
- slippage harness EA (temp) and test matrix CSV + notes
- `WORK_LOG.md` entries per run
- `HANDOFF_NEXT_WINDOW.md` updated decision gate result

