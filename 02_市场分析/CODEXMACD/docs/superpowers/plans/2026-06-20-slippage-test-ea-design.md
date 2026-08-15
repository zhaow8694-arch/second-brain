# Slippage Test EA Design

Goal: design a temporary slippage-pressure method without modifying production v8.66/v8.67 source.

Decision: requires_temp_ea_or_external_execution_model.

Reason: current verified MT5 batch runner does not expose a proven slippage simulation setting. Any direct config-only result would be unreliable until verified.

Temporary EA name if approved later:

`	ext
E:\CODEXMACD\SniperTrendEA_v8.67_slippage_test.mq5
`

Rules:

- Do not replace production EA.
- Keep entry/exit logic equivalent to v8.67 production-ready line.
- Add slippage simulation only around order price assumptions or post-report analysis.
- Test levels: 0, 1, 2, 3, 5.
- Archive every run.
- Compare robust B and aggressive C first.

Deliverable before implementation:

- User approval or explicit unattended instruction allowing temporary test EA creation.