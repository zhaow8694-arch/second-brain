# AIMart v0.3.1 Hotfix + Recovery Finalize Toolkit

This toolkit applies a narrow host-side hotfix for the current v0.3.1 Recovery Finalize failures, then reruns the fixed Recovery Finalize runner.

It is intended for:

- Branch: `feature/v0.3.1-auto-verified-customer-runtime`
- Project: `E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack`

It fixes the known failing gates:

1. TypeScript parser failure in `src/lib/generators/script-pack.ts` caused by PowerShell backticks inside a TypeScript template literal.
2. Missing fixed wording: `Generated execution pack includes docs/README.md and docs/RUN_APP.md`.
3. Missing explicit adapter/runtime path strings in completion-gate scripts:
   - `agent_adapters/claude-code`
   - `agent_adapters/trae`
   - `agent_adapters/cursor`
   - `runtime/RUN_STATE.json`
   - `runtime/CURRENT_TASK.md`
   - `runtime/PHASE_GATE_REPORT.md`
   - `runtime/COMPLETION_GATE_REPORT.md`

After patching, it runs:

- `pnpm test`
- `pnpm lint`
- `pnpm build`

If those pass, it runs the existing fixed Recovery Finalize runner:

`E:\AIMart_Orchestrator\aimart_v031_recovery_finalize_fixed_ps51\START_V0.3.1_RECOVERY_FINALIZE_FIXED.cmd`

The Recovery Finalize runner is responsible for creating `releases/v0.3.1`, source ZIP, sample execution-pack ZIP, SHA256, manifest, commit, and tag.
