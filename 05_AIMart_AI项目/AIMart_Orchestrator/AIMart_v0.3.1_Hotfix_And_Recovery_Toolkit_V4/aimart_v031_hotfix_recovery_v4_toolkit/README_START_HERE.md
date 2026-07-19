# AIMart v0.3.1 Hotfix + Recovery V4

Purpose: finish the current `feature/v0.3.1-auto-verified-customer-runtime` branch after V3 fixed tests but Recovery Finalize failed while starting Next.js with the wrong hostname argument order.

Run:

```powershell
& "E:\AIMart_Orchestrator\aimart_v031_hotfix_recovery_v4\aimart_v031_hotfix_recovery_v4_toolkit\START_V0.3.1_HOTFIX_AND_RECOVERY_V4.cmd"
```

This toolkit:
- applies the remaining compatibility literals safely,
- runs pnpm test/lint/build,
- starts Next.js with `pnpm exec next start . -p <port> -H 127.0.0.1`,
- generates the sample execution-pack ZIP through `/api/generate`,
- verifies source ZIP and sample ZIP,
- writes SHA256 and RELEASE_MANIFEST,
- commits and tags v0.3.1 locally.
