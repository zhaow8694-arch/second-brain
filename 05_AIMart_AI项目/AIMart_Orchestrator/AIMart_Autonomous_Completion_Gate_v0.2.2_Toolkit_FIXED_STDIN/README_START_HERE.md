# AIMart v0.2.2 Autonomous Completion Gate Runner - FIXED STDIN

This package fixes the Codex CLI argument error:

```text
error: unexpected argument 'are' found
```

The fix is to pass the whole prompt through stdin using:

```text
codex ... exec --cd <project> -
```

This avoids splitting prompt words like `You are...` into command-line arguments.

## Default target project

```text
E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack
```

## Usage

1. Extract this ZIP outside the project, for example:

```text
E:\AIMart_Orchestrator\aimart_autonomous_completion_gate_v022_fixed_stdin
```

2. Make sure the project working tree is clean:

```powershell
Set-Location -LiteralPath "E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack"
git status --short --branch
```

3. Double-click:

```text
START_V0.2.2_AUTONOMOUS_COMPLETION_GATE_FIXED.cmd
```

The runner is single-window: it starts Codex, shows status, displays recent logs, checks release output, and shows a final summary.

## Important

Do not run this while another Runner is actively modifying the same project.
