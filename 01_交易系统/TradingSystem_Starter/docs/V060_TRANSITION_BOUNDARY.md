# v0.6.0 Transition Boundary

## Purpose

This document defines the v0.6.0 transition boundary.

v0.6.0 is a next-stage boundary planning target only. It does not mean the
v0.6.0 phase has started, and it does not authorize any implementation work by
itself.

The current phase remains:

```text
v0.5.0 official evidence archive policy and reproducibility boundary
```

## Current Closure Basis

v0.5.0 has completed the official evidence archive, official manifest, final
closure, and transition readiness closure loop.

The readiness state is fixed by:

```text
v0.5.26-v060-transition-boundary-definition-readiness-tag-completion
```

This stable tag records readiness for defining the transition boundary. It does
not represent v0.6.0 implementation, live trading readiness, real trading
availability, profitability, or permission to trade.

## Authorization Boundary

Any v0.6.0 implementation task must be separately and explicitly authorized by a
future ChatGPT task.

Codex must not independently enter v0.6.0 implementation.

Trae must not independently trigger v0.6.0 implementation.

MT5 must not be run unless a future task explicitly authorizes it.

MQ5 must not be modified unless a future task explicitly authorizes it.

backtest/sets must not be modified unless a future task explicitly authorizes
it.

The official manifest must not be modified unless a future task explicitly
authorizes it.

External evidence must not be copied unless a future task explicitly authorizes
it.

## Candidate Scope

The v0.6.0 candidate scope is limited to planning and controlled boundary work
unless a future task explicitly authorizes implementation.

Candidate areas:

- reproducibility automation planning
- official evidence archive lifecycle hardening
- manifest validation and reporting automation planning
- transition from manual task closure to a controlled automation boundary
- future tooling that preserves the risk-first policy
- future tooling that preserves metadata-only evidence handling
- future tooling that preserves no-live-trading defaults

## Non-Scope

v0.6.0 does not represent live trading readiness.

v0.6.0 does not represent real trading availability.

v0.6.0 does not represent profitability.

v0.6.0 does not authorize real trading.

v0.6.0 does not authorize profit optimization.

v0.6.0 does not authorize trading without risk controls.

v0.6.0 does not authorize bypassing RiskManager.

v0.6.0 does not authorize SignalEngine to place orders.

v0.6.0 does not authorize copying external evidence.

v0.6.0 does not authorize directly running MT5.

v0.6.0 does not authorize modifying MQ5 strategy logic.

## Entry Conditions

The following conditions must remain true before any future task may define or
authorize v0.6.0 implementation:

- v0.5.0 final closure is fixed by
  v0.5.19-v050-official-evidence-archive-final-phase-closure.
- v0.5.0 final closure documentation / transition boundary is fixed by
  v0.5.21-v050-final-closure-documentation-transition-boundary.
- v0.6.0 transition boundary planning readiness is fixed by
  v0.5.23-v060-transition-boundary-planning-readiness.
- v0.6.0 transition boundary definition readiness is fixed by
  v0.5.25-v060-transition-boundary-definition-readiness.
- v0.6.0 transition boundary definition readiness tag completion is fixed by
  v0.5.26-v060-transition-boundary-definition-readiness-tag-completion.
- The first official evidence manifest exists and is the only official
  manifest.
- The official manifest path is:
  backtest/reports/manifests/TASK-139_external-mt5-eurusd-m5-20240101-20240131-no-trade_manifest.json

## Next Boundary

Do not directly enter v0.6.0 implementation.

Do not directly enter TASK-152.

The next step should be TASK-DOC-201 to synchronize project state after
TASK-151.

Whether to create a v0.6.0 transition boundary stable tag must be explicitly
specified by ChatGPT in a future task.

