# AIMart Codex v0.2 Autonomous Runner - Fixed English Prompt

This package starts Codex in autonomous mode for AIMart Orchestrator v0.2.0 development.

Why this fixed package exists:
- The previous runner displayed Chinese prompt text as mojibake in the Codex log.
- This package uses an English-only prompt to avoid Windows console encoding issues.
- It launches Codex through a child PowerShell process and redirects stdout/stderr to log files.
- It uses `codex exec --cd <project> --sandbox workspace-write --ask-for-approval never -`.

Default project root:
E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack

How to run:
1. Extract this ZIP anywhere, for example:
   E:\AIMart_Orchestrator\aimart_autonomous_v02_runner_fixed
2. Double-click:
   START_V0.2_AUTONOMOUS_FIXED.cmd

Logs will be written to:
E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack\codex_runs\autonomous_v0_2_fixed

The script does not commit, push, or delete historical release folders.
Codex is instructed not to modify releases/v0.1.0 or releases/v0.1.1.
