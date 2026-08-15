# Workflow Simplification Boundary

## Purpose

This document defines the workflow simplification boundary for TASK-163.

The project now enters an efficient workflow mode for future task routing, review, validation, and state synchronization.

This boundary only changes workflow rules and project state documentation. It does not enter v0.6.0 implementation.

## Role Routing

Future tasks must start with role routing:

- GPT defines task boundaries and issues instructions.
- Codex modifies only the files explicitly allowed by the task, and does not commit unless the task explicitly says so.
- Trae reviews, validates, commits, creates tags, and performs read-only audit tasks when instructed.

Codex instructions may remain complete when full boundaries are needed.

Trae instructions must be compressed and focused on review, validation, commit, tag, or read-only audit duties.

Each instruction must clearly start with either:

- `发给：Codex`
- `发给：Trae`

## Task Routing Rules

- TASK-DOC modification tasks go to Codex first.
- Codex completion review, validation, and commit may then go to Trae.
- TASK-TAG stable tag creation goes to Trae.
- TASK read-only audit goes to Trae.
- Do not repeatedly ask whether to continue; by default, generate the next instruction when the next boundary is clear.
- If the next boundary is not clear, GPT must define it first.

## Milestone Limit

Each milestone should allow at most:

- one modification or boundary definition task
- one review / validation / commit task
- one stable tag when necessary
- one state synchronization task when necessary

Do not continue infinite chains such as:

- tag completion audit stable tag completion audit
- completion audit stable tag completion audit
- repeated meta-audit after a closed completion

## Numbering And Boundary Rules

- Do not reuse old TASK-DOC ids.
- Do not let old task ids appear as the latest task in a new chain.
- Do not redefine a boundary that has already been fixed by a stable tag.
- If a task-id anomaly is found, record it through reconciliation only.
- Reconciliation must not rewrite Git history.
- Reconciliation must not amend commits.
- Reconciliation must not move tags.

## Validation Rules

Future validation should use the unified release validation bundle by default:

```text
py tools/run_release_validation_bundle.py
```

When the Python launcher is unavailable, the same script may be run with the local Python interpreter.

Only expand into individual validators when a failure needs localization.

The release validation bundle must not:

- run MT5
- modify files
- create reports
- create manifests
- create directories
- copy external evidence

## Current Baseline

- current HEAD is f8f8d1f TASK-DOC-220 reconciliation / workflow simplification boundary
- current stable tag remains v0.5.35-v060-implementation-planning-boundary-tag-completion-audit-stable-tag-completion-audit
- v0.5.35 points to 1bcc4fc TASK-DOC-217 update state after TASK-159
- v0.5.34 points to 0ed0ebc
- v0.5.33 points to 33e2f47
- v0.5.32 points to 02ea6b4
- v0.5.31 points to 07c817e
- v0.5.30 points to 5f416da
- v0.5.29 through v0.5.10 historical stable tags were not moved
- current phase remains v0.5.0
- docs/V060_IMPLEMENTATION_PLANNING_BOUNDARY.md exists and was not modified by this task
- docs/V060_TRANSITION_BOUNDARY.md exists and was not modified by this task
- official manifest exists, was not modified, and remains the only manifest
- official manifest path: backtest/reports/manifests/TASK-139_external-mt5-eurusd-m5-20240101-20240131-no-trade_manifest.json
- release validation bundle exists and is tracked / committed
- workflow/process gap was recorded by TASK-DOC-220
- current engineering gap: none
- current safety boundary gap: none
- current manifest gap: none

## Efficiency Rules

- Future ordinary docs updates should not fully expand v0.5.10 through the current stable tag unless explicitly required.
- Future ordinary review / commit instructions should list only the current stable tag, recent key tags, forbidden items, validation commands, and commit information.
- Future tag tasks should confirm only the current tag, target tag, recent key historical tags, and that old tags were not moved.
- Future audit tasks should remain read-only and must not produce follow-up meta-audit chains.
- After a completion is closed, do not continue creating completion audit stable tag completion audit chains.

## Safety Boundary

This workflow simplification boundary does not authorize:

- v0.6.0 implementation
- MT5 execution
- MQ5 modification
- forbidden tools modification
- new manifest creation
- official manifest modification
- external evidence copying
- real trading
- profit optimization
- bypassing RiskManager
- SignalEngine order placement
- enabling InpEnableTrading=true

## Next Step Boundary

- Do not directly enter TASK-164.
- Do not directly enter v0.6.0 implementation.
- The next step should first be Trae review and commit for this task.
- After this task is committed, GPT may define the first real low-risk tooling task for v0.6.0 implementation planning.
- The next task boundary must be defined by ChatGPT.
