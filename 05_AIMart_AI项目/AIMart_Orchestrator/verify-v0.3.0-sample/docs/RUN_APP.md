# Run App

Project: Todo API
Selected adapters: Codex, Claude Code, Trae, Cursor
Execution scope: end_to_end_delivery
Selected execution mode: end_to_end_autonomous

## Local Setup

```bash
pnpm install
pnpm dev
```

## Verification

```bash
pnpm lint
pnpm test
pnpm build
```

## Start Codex Supervised Mode

Supervised Mode keeps the workspace sandboxed and asks for approval when Codex encounters commands outside the safe policy.

```powershell
./agent_adapters/codex/run-codex-supervised.ps1
```

```bash
bash agent_adapters/codex/run-codex-supervised.sh
```

## Start Codex Autonomous Mode

Autonomous Mode uses workspace-write plus approval never. It must follow runtime/SAFE_COMMANDS.md, runtime/DENIED_COMMANDS.md, and runtime/AUTONOMOUS_EXECUTION_POLICY.md.

```powershell
./agent_adapters/codex/run-codex-autonomous.ps1
```

```bash
bash agent_adapters/codex/run-codex-autonomous.sh
```

## Start Codex Unified Autonomous Mode

Unified Autonomous Mode provides the one-window status display. It starts Codex autonomously, shows target version, Git branch, clean startup state, existing Codex process detection, release artifact status, latest log activity, stalled-log status, and final summary. It runs the Autonomous Completion Gate before reporting PASS.

```powershell
./agent_adapters/codex/run-codex-unified-autonomous.ps1
```

```bash
bash agent_adapters/codex/run-codex-unified-autonomous.sh
```

## Start Codex End-to-End Autonomous Mode

Use End-to-End Autonomous Mode when Codex is the selected agent and should continue through phase gates until final usable delivery.

```powershell
./agent_adapters/codex/run-codex-end-to-end-autonomous.ps1
```

```bash
bash agent_adapters/codex/run-codex-end-to-end-autonomous.sh
```

## Other Adapter Options

Claude Code, Trae, and Cursor adapters are independent execution options when selected. Read their adapter directory and choose only one active adapter for a workspace.

## Logs And Approval Queue

Codex launcher logs are written under .aimart/logs for the legacy launchers and codex_runs for the unified autonomous runner. Commands outside the safe policy must be recorded in runtime/APPROVAL_QUEUE.md with the risk, reason, blocking status, and recommendation.

## Autonomous Completion Gate

The unified runner writes runtime/AUTONOMOUS_VERIFICATION_REPORT.md. If the gate reports FAIL, inspect that report before accepting the run.

## Final Delivery

Run the platform-specific finalize script:

```powershell
./scripts/finalize.ps1
```

```bash
./scripts/finalize.sh
```