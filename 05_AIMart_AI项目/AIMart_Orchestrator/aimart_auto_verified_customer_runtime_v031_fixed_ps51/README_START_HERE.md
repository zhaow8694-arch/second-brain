# AIMart v0.3.1 Auto-Verified Customer Runtime Toolkit — FIXED PS5.1

This fixed toolkit is for Windows PowerShell 5.1. It avoids `ProcessStartInfo.ArgumentList`, which can be null in Windows PowerShell 5.1 environments, and launches Codex through a generated CMD file using stdin:

```cmd
type prompt.md | codex --cd <project> -c approval_policy=never -c sandbox_mode=workspace-write exec -
```

## Purpose

Target version: `v0.3.1`

Goal: implement customer-side runtime validation so generated AIMart execution packs can be validated as if a customer downloaded and ran them.

## Use

1. Extract this toolkit outside the source project, for example:
   `E:\AIMart_Orchestrator\aimart_auto_verified_customer_runtime_v031_fixed_ps51`
2. Double-click:
   `START_V0.3.1_AUTO_VERIFIED_CUSTOMER_RUNTIME_FIXED.cmd`

The runner will:
- verify or create the `feature/v0.3.1-auto-verified-customer-runtime` branch
- start Codex in autonomous mode
- display status in the same window
- save logs under the project `codex_runs/` folder
- expect Codex to generate `releases/v0.3.1`
- show a post-run summary

Do not run older v0.3.1 toolkits for this task.
