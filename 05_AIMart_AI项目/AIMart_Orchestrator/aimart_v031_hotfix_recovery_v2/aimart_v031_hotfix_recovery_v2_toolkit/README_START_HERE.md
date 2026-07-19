
# AIMart v0.3.1 Hotfix + Recovery Toolkit V2

Purpose: apply a narrow host-side hotfix for the remaining v0.3.1 test failures, then re-run the existing Recovery Finalize flow.

Use this only on branch:
feature/v0.3.1-auto-verified-customer-runtime

It patches:
- script-pack.ts bad PowerShell backtick-generated line
- final delivery wording required by tests
- explicit v0.3.0 and adapter literal paths in completion-gate scripts

Then it runs:
- pnpm test
- pnpm lint
- pnpm build

If validation passes, it calls the existing fixed recovery finalizer if found:
E:\AIMart_Orchestrator\aimart_v031_recovery_finalize_fixed_ps51\START_V0.3.1_RECOVERY_FINALIZE_FIXED.cmd

No remote push is performed.
