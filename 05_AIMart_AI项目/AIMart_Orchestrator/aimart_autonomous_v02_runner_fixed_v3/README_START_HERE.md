# AIMart Codex v0.2 Autonomous Runner - FIXED V3

This package starts the AIMart Orchestrator v0.2.0 autonomous development run.

## Why V3 exists

Codex CLI v0.137.0 rejects this form:

```powershell
codex exec --ask-for-approval never ...
```

V3 uses the compatible form:

```powershell
codex --cd <project> --sandbox workspace-write --ask-for-approval never exec <prompt>
```

If that still fails on your Codex CLI, the runner automatically retries with config overrides:

```powershell
codex --cd <project> -c approval_policy="never" -c sandbox_mode="workspace-write" exec <prompt>
```

## Usage

1. Extract this ZIP to a folder, for example:

```text
E:\AIMart_Orchestrator\aimart_autonomous_v02_runner_fixed_v3
```

2. Double-click:

```text
START_V0.2_AUTONOMOUS_FIXED_V3.cmd
```

Default project root:

```text
E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack
```

Logs will be written to:

```text
<project-root>\codex_runs\autonomous_v0_2_fixed_v3
```

## Safety boundaries

The prompt forbids:

- git push
- modifying releases/v0.1.0 or releases/v0.1.1
- deleting historical release folders
- reading .env, SSH keys, cloud credentials, or system secrets
- production deployment
- real database migration
- cloud resource creation or deletion

The runner uses workspace-write sandbox and approval policy never for uninterrupted execution inside the workspace.
