# AIMart v0.2.2 Autonomous Completion Gate Runner — FIXED V5 STDIN

This toolkit starts Codex in a single visual console window and passes the full prompt through stdin using `codex exec -`.

Why V5 exists:
- Earlier runners accidentally passed the prompt as command-line arguments, causing errors such as `unexpected argument 'are'`.
- V5 never uses the PowerShell automatic `$Args` variable for Codex arguments.
- V5 invokes Codex with an explicit `$CodexArgList` and sends the prompt through stdin.
- V5 tries two compatible argument layouts and shows the active attempt in the same window.

Default target project:
`E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack`

Start:
Double-click `START_V0.2.2_AUTONOMOUS_COMPLETION_GATE_V5.cmd`.

Do not run older v0.2.2 runner folders after using this one.
