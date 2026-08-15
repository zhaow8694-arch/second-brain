# V060 TASK-260 First Observability Extension Plan

## Purpose

- TASK-DOC-260 is planning-only.
- TASK-DOC-260 is a future candidate planning packet.
- TASK-DOC-260 defines a no-trade observability extension boundary.
- TASK-DOC-260 is not implementation authorization.
- TASK-DOC-260 does not authorize TASK-261 implementation.
- TASK-261 must not be entered directly; GPT must define a separate future task boundary.

## Current Baseline

- current HEAD: 6451e78 TASK-259 implement read-only decision rejection reason snapshot contract
- current tag: v0.5.61-task-259-read-only-decision-rejection-reason
- MQ5 inventory remains 7 files.
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false.
- Inventory only; no MT5 run; no trading authorization.

## Candidate Scope For Future TASK-261

Future TASK-261 may be considered only after GPT defines a separate boundary. Candidate directions may include:

- extend no-trade observability output fields
- strengthen telemetry / metrics aggregation
- strengthen controller state observability
- refine logger output contract
- strengthen validator coverage
- keep all authorization / intent / execution / dispatch values false
- keep MQ5 inventory 7 files

## Non-Scope And Safety Boundary

- no MQ5 modification in TASK-DOC-260
- no MT5 run
- no trading authorization
- no backtest execution
- no simulated trading
- no real trading
- no manifest creation
- no fixture creation
- no report creation
- no external evidence copy
- no official manifest modification
- no backtest/sets modification
- no Buy / Sell / OrderSend / PositionOpen / CTrade introduction

## Exit Criteria

- docs/V060_TASK_260_FIRST_OBSERVABILITY_EXTENSION_PLAN.md exists.
- project-state-docs PASS.
- project-state-docs-self-test PASS.
- mq5-inventory PASS with MQ5 inventory remains 7 files.
- mq5-no-trade-observability PASS.
- git diff --check PASS.
- MQ5 / MQH files remain unmodified.
- stable V060 / workflow docs remain unmodified.
- official manifest remains unmodified.
