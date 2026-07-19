# AIMart Unified Autonomous Visual Runner v0.2.1

This toolkit is an external single-window runner for the AIMart Orchestrator project.

## Where to unzip

Unzip this package to:

```text
E:\AIMart_Orchestrator\aimart_unified_autonomous_visual_runner_v021
```

Do not place it inside the project repository.

## Target project

By default, it controls this project:

```text
E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack
```

## How to run

Double-click:

```text
START_UNIFIED_AUTONOMOUS_VISUAL_RUNNER.cmd
```

The runner opens one PowerShell window, starts Codex in autonomous mode, and displays a live status dashboard in that same window.

## What the dashboard shows

- Codex job state and uptime
- Codex process count
- Current Git branch and dirty file count
- Latest log file path, size, and recent log lines
- Current target release directory status
- Recent PROGRESS_LOG.md entries
- Known issues file status
- Final exit code and post-run summary

## Important rules

This runner is meant for the next task after v0.2.0 is stable. It is designed to reduce manual monitoring. Do not run multiple autonomous runners against the same project at the same time.

It does not push to remote Git. It does not modify frozen release directories unless the task prompt explicitly targets the current version release folder.
