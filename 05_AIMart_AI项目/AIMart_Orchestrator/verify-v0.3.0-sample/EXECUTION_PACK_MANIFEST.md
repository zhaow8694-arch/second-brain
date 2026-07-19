# Execution Pack Manifest

Project: Todo API

## Selected adapters

- Codex (codex) -> agent_adapters/codex
- Claude Code (claude-code) -> agent_adapters/claude-code
- Trae (trae) -> agent_adapters/trae
- Cursor (cursor) -> agent_adapters/cursor

Selecting multiple adapters means generating multiple independent execution options. It does not mean running multiple agents together.

Choose one adapter when executing against a workspace. Do not run multiple agents against the same workspace at the same time unless a human manually coordinates ownership.

## Execution Configuration

- Execution scope: end_to_end_delivery
- Execution mode: end_to_end_autonomous

## Generated Files Summary

- common/ project specifications, task queue, autonomous roadmap, and phase gates
- runtime/ permission policy, run state, current task, phase reports, and completion reports
- scripts/ platform scripts and completion-gate verification
- agent_adapters/ independent adapter directories for selected targets
- docs/ customer-facing run and delivery documentation

Adapter file count: 38

## How To Start One Selected Agent

1. Pick exactly one adapter directory under agent_adapters/.
2. Read that adapter's runbook and task prompt.
3. Read common/AUTONOMOUS_DELIVERY_ROADMAP.md, common/PHASE_GATE_PLAN.md, runtime/END_TO_END_AUTONOMOUS_POLICY.md, and runtime/RUN_STATE.json.
4. Start the selected adapter using its documented supervised, autonomous, or end-to-end autonomous instructions.
5. Continue until runtime/COMPLETION_GATE_REPORT.md reports PASS for the active phase.

## Completion Gate Requirements

- Codex: Codex runbooks and prompts exist.
- Codex: End-to-end autonomous prompt and delivery runbook exist.
- Codex: PowerShell and Bash launchers exist for supervised, autonomous, unified, and end-to-end autonomous modes.
- Claude Code: CLAUDE.md, runbook, task prompt, autonomous prompt, and end-to-end runbook exist.
- Claude Code: settings.example.json exists with project-local safety defaults.
- Claude Code: Run instructions warn not to run multiple agents against the same workspace.
- Trae: Trae runbook, task prompt, autonomous prompt, end-to-end runbook, and config YAML exist.
- Trae: Run instructions keep Trae isolated from other generated adapter options.
- Cursor: Cursor runbook, task prompt, autonomous rules, end-to-end runbook, and project rules exist.
- Cursor: Rules explain adapter selection is independent and not multi-agent collaboration.
- runtime/RUN_STATE.json must be valid JSON.
- runtime/CURRENT_TASK.md must exist.
- runtime/PHASE_GATE_REPORT.md and runtime/COMPLETION_GATE_REPORT.md must be initialized or updated.

## High-Risk Command Policy

High-risk commands are not executed automatically. Record them in runtime/APPROVAL_QUEUE.md with risk, reason, blocking status, and recommendation, then continue safe independent work when possible.