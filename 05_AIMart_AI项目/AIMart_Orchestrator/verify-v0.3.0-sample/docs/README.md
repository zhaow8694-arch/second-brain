# Todo API

This generated execution-pack ZIP describes the local v0.3.0 End-to-End delivery plan for Todo API. It is different from an AIMart source release ZIP: source release ZIPs contain the generator source, while generated execution-pack ZIPs contain common/runtime/scripts/agent_adapters/docs for a target project.

Selected adapters: Codex, Claude Code, Trae, Cursor
Execution scope: end_to_end_delivery
Selected execution mode: end_to_end_autonomous

Selecting multiple adapters creates multiple independent execution options. It does not run multiple agents together; choose one adapter for one workspace.

## MVP Scope

- Todo CRUD endpoints
- local tests
- generated run docs

## Forbidden items

- No SaaS accounts
- no cloud runner
- no payment
- no production deploy
- no external API integration

## Task Queue

- TASK-001: Initialize target project
- TASK-002: Implement v0.1 core MVP
- TASK-003: Apply runtime and permission boundaries
- TASK-004: Add focused tests
- TASK-005: Write delivery documentation
- TASK-006: Finalize local delivery artifact

## Autonomous Completion Gate

Unified autonomous runs must finish with the Autonomous Completion Gate before reporting success. Review runtime/AUTONOMOUS_COMPLETION_GATE.md and runtime/AUTONOMOUS_VERIFICATION_REPORT.md after every unattended run.

Start with docs/RUN_APP.md, then follow common/TASK_QUEUE.md in order.