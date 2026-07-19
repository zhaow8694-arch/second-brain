# Run App

Project: Todo API
Selected execution mode: unified_autonomous

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

Unified Autonomous Mode provides the one-window status display. It starts Codex autonomously, shows elapsed time, Git branch, dirty file count, latest log tail, release directory status, and known issues status, then writes a final summary.

```powershell
./agent_adapters/codex/run-codex-unified-autonomous.ps1
```

```bash
bash agent_adapters/codex/run-codex-unified-autonomous.sh
```

## Logs And Approval Queue

Codex launcher logs are written under .aimart/logs for the legacy launchers and codex_runs for the unified autonomous runner. Commands outside the safe policy must be recorded in runtime/APPROVAL_QUEUE.md with the risk, reason, blocking status, and recommendation.

## Final Delivery

Run the platform-specific finalize script:

```powershell
./scripts/finalize.ps1
```

```bash
./scripts/finalize.sh
```