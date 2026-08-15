# v8.67 True Spread Test Path - 2026-06-20

## Goal

Create an honest spread-stress path for B/C without pretending that MT5 ExecutionMode delay is spread widening.

## Current constraints

- Active B/C .set files do not expose Spread, Slippage, Deviation, Cost, Commission, 点差, or 滑点 inputs.
- The inspected source-like file is SniperTrendEA_v8.66_grokbase_structure_risk.mq5, not the exact active compiled expert SniperTrendEA_v8.66_r68_dualperiod_candidate_20260619.ex5.
- The inspected source has hard-coded request deviation lines, for example eq.deviation = 20, but no confirmed spread input.
- The previous slippage batch only tested MT5 ExecutionMode delay and must not be treated as spread validation.

## Recommended path A: custom-symbol spread variants

Use this path first because it does not require changing EA logic.

Proposed symbols:

| Symbol | Purpose |
|---|---|
| XAUUSD_SPRD_BASE | cloned baseline history/control |
| XAUUSD_SPRD_2X | moderate widened spread stress |
| XAUUSD_SPRD_3X | severe widened spread stress |

Required implementation steps:

1. In MT5, create custom symbols cloned from the active XAUUSD source.
2. Copy or import the same historical bars/ticks used by current tests.
3. Set fixed spread or widened spread properties on the custom symbols.
4. Extend un_v867_next_stage.ps1 with a safe -SymbolOverride parameter.
5. Generate run IDs such as 20260620_spread2x_B_recent and 20260620_spread3x_C_recent.
6. Run B/C on 2020-2026 first, then only run 2012-2019 if recent-window report chain is clean.

Pass gates:

| Window | Pass gate | Green gate |
|---|---|---|
| 2020-2026 | retention >= 0.80, PF >= 1.70, trades >= 180 | retention >= 0.90, PF >= 2.00, trades >= 190 |
| 2012-2019 | net profit > 0, PF >= 1.05, trades >= 200 | net profit > 0, PF >= 1.10, trades >= 220 |

## Path B: EA input support

Use only if the exact active source for SniperTrendEA_v8.66_r68_dualperiod_candidate_20260619.ex5 is available.

Required implementation steps:

1. Confirm exact source-to-EX5 lineage.
2. Add explicit inputs such as InpMaxAllowedSpreadPoints or synthetic cost controls.
3. Compile a new named candidate; do not overwrite current B/C expert.
4. Create new set files and rerun precheck before comparing against B/C.

Risk:

This changes the EA candidate and should be treated as a new branch, not as validation of current B/C.

## No-go paths

- Do not call ExecutionMode delay a spread test.
- Do not edit a non-matching source file and assume it represents the active EX5.
- Do not modify broker symbol data destructively.
- Do not overwrite existing B/C .set files.

## Recommendation

Use Path A next. First produce one manual/controlled custom symbol proof with XAUUSD_SPRD_2X on B recent-window only. If artifact chain is clean, expand to B/C and then to old-window validation.