# AIMart v0.3.1 Hotfix + Recovery V9

Use this toolkit only after V8 reached sample execution-pack generation and failed with `End of Central Directory record could not be found`.

V9 fixes the sample-pack recovery path by detecting when `/api/generate` output was saved as JSON containing `zipBase64`, decoding it into a real ZIP, validating the ZIP entries, then completing SHA256, manifest, dogfood evidence, commit, tag, and final completion-gate verification.

Run:

```powershell
& "E:\AIMart_Orchestrator\aimart_v031_hotfix_recovery_v9\aimart_v031_hotfix_recovery_v9_toolkit\START_V0.3.1_HOTFIX_AND_RECOVERY_V9.cmd"
```
