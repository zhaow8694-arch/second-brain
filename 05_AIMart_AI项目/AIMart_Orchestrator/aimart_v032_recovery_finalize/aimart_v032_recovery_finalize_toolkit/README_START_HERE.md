# AIMart v0.3.2 Recovery Finalize Toolkit

Use this toolkit only after v0.3.2 source changes pass:

- `pnpm test`
- `pnpm lint`
- `pnpm build`

It finalizes `feature/v0.3.2-autonomous-runner-hardening` from the local working tree by generating release artifacts, validating source/sample ZIPs, committing, tagging `v0.3.2`, and running the Autonomous Completion Gate.

Do not use any v0.3.1 V1-V9 runners for v0.3.2.

Run:

```powershell
& "E:\AIMart_Orchestrator\aimart_v032_recovery_finalize\START_V0.3.2_RECOVERY_FINALIZE.cmd"
```
