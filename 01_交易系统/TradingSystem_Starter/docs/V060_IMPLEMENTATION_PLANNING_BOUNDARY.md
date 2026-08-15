# v0.6.0 Implementation Planning Boundary

## Purpose

This document defines the v0.6.0 implementation planning boundary for TASK-DOC-218.

v0.6.0 implementation planning is only a next-phase implementation boundary plan. It does not mean v0.6.0 has started, and it does not authorize v0.6.0 implementation.

The current phase remains v0.5.0: official evidence archive policy and reproducibility boundary.

## Current Baseline

- current latest commit: be28400 TASK-DOC-217 update state after TASK-161
- TASK-161 completed: workflow simplification validation bundle implemented
- current stable tag remains v0.5.31-v060-implementation-planning-boundary -> 07c817e
- docs/V060_TRANSITION_BOUNDARY.md exists and must not be modified by this task
- docs/V060_IMPLEMENTATION_PLANNING_BOUNDARY.md is the only file allowed to be modified by this task
- the first official evidence manifest exists and remains the only manifest
- official manifest path: backtest/reports/manifests/TASK-139_external-mt5-eurusd-m5-20240101-20240131-no-trade_manifest.json
- the official manifest must not be modified by this task

## Candidate Scope

The v0.6.0 implementation planning boundary may include future planning for:

- implementation task sequencing
- release validation bundle usage and follow-up hardening
- reproducibility automation
- official evidence archive lifecycle automation
- manifest validation and reporting automation
- project state docs validation hardening
- controlled engineering toolchain automation
- dry-run-only validation workflows
- manual-to-controlled-automation transition
- workflow simplification for local agent validation and reporting
- preservation of risk-first policy
- preservation of metadata-only evidence handling
- preservation of no-live-trading defaults
- preservation of explicit authorization boundaries

## Non-Scope

This boundary does not authorize:

- starting v0.6.0 implementation
- Codex entering v0.6.0 implementation on its own
- Trae entering or triggering v0.6.0 implementation on its own
- modifying MQ5
- modifying tools
- modifying backtest/sets
- running MT5
- creating a new manifest
- modifying the official manifest
- copying external evidence
- creating fixtures
- creating unauthorized reports
- creating unauthorized directories
- real trading
- profit optimization
- no-risk trading
- bypassing RiskManager
- SignalEngine order placement
- enabling InpEnableTrading=true
- changing strategy logic
- live trading readiness claims
- real trading availability claims
- profitability claims

## Future Implementation Authorization Gate

Any future v0.6.0 implementation task must be separately authorized by ChatGPT.

Every future implementation task must explicitly define:

- allowed paths
- forbidden paths
- whether tools modification is allowed
- whether docs modification is allowed
- whether MQ5 modification is allowed
- whether backtest/sets modification is allowed
- whether MT5 execution is allowed
- whether official manifest modification is allowed
- whether external evidence copying is allowed

Every future implementation task must default to:

- no MT5 run
- no MQ5 modification
- no backtest/sets modification
- no official manifest modification
- no external evidence copying
- no new official manifest creation unless explicitly authorized
- no live trading readiness claim
- no real trading availability claim
- no profitability claim
- no real trading authorization

Every future implementation task must pass the corresponding validator, self-test, and engineering toolchain checks.

Future tasks involving manifests must continue to use the evidence manifest schema validator and the official manifest path policy validator.

Future tasks involving the official manifest must state whether `--no-check-overwrite` is used.

## Entry Conditions

The v0.6.0 implementation planning boundary depends on these completed entry conditions:

- current phase remains v0.5.0
- v0.5.0 official evidence archive final phase closure fixed by v0.5.19
- v0.5.0 final closure documentation / transition boundary fixed by v0.5.21
- v0.5.0 to v0.6.0 transition boundary planning readiness fixed by v0.5.23
- v0.6.0 transition boundary definition readiness fixed by v0.5.25
- v0.6.0 transition boundary definition fixed by v0.5.27
- v0.6.0 transition boundary definition tag completion fixed by v0.5.28
- v0.6.0 implementation planning boundary readiness fixed by v0.5.29
- v0.6.0 implementation planning boundary readiness tag completion fixed by v0.5.30
- v0.6.0 implementation planning boundary fixed by v0.5.31
- docs/V060_TRANSITION_BOUNDARY.md exists
- first official evidence manifest exists and is the only manifest
- official manifest path: backtest/reports/manifests/TASK-139_external-mt5-eurusd-m5-20240101-20240131-no-trade_manifest.json

## Safety Boundary

This task does not:

- enter v0.6.0 implementation
- modify MQ5
- modify tools
- modify docs/CURRENT_TASK.md
- modify docs/HANDOFF_PROMPT.md
- modify docs/PROJECT_STATE.md
- modify docs/V060_TRANSITION_BOUNDARY.md
- modify docs/EVIDENCE_ARCHIVE_AND_MANIFEST.md
- modify backtest/sets
- modify backtest/reports/generated
- modify backtest/reports/samples
- modify the official manifest
- run MT5
- create a new manifest
- create a fixture
- create an unauthorized report
- create a directory
- copy external evidence
- enter real trading
- perform profit optimization

## Next Step Boundary

- Do not directly enter v0.6.0 implementation.
- Do not directly enter TASK-219.
- Future tasks must be specified by ChatGPT.
- Codex must not self-authorize implementation work.
- Trae must not self-trigger implementation work.
