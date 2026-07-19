# Next Steps

## Immediate

End-to-End autonomous delivery continues through phase gates until final usable delivery.

1. Review PROJECT_SPEC.md for accuracy.
2. Execute TASK_QUEUE.md from the first pending task.
3. Choose one adapter from Codex, Claude Code, Trae, Cursor before working in a workspace.
4. Use runtime/RUN_STATE.json, runtime/CURRENT_TASK.md, and common/PHASE_GATE_PLAN.md to continue across phases.
5. Run scripts/finalize.* before delivery.
6. Review runtime/AUTONOMOUS_VERIFICATION_REPORT.md and runtime/COMPLETION_GATE_REPORT.md; accept delivery only when the Autonomous Completion Gate reports PASS.

## Known Limitations

- v0.3.0 is local-only.
- v0.3.0 does not include a cloud runner.
- v0.3.0 does not perform production deployment.
- v0.3.0 does not read secrets or production credentials.

## Deferred Ideas

Future versions can expand adapter coverage after Todo API v0.1 is stable.