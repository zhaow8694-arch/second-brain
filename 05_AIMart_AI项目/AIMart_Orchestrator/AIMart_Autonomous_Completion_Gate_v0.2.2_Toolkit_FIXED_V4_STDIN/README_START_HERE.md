# AIMart v0.2.2 Autonomous Completion Gate Runner V4

This toolkit fixes the Codex CLI prompt-argument issue by feeding the prompt through stdin using `codex exec -`.

Target project:

```text
E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack
```

Use:

1. Put this toolkit outside the project source directory.
2. Ensure the project worktree is clean.
3. Double-click:

```text
START_V0.2.2_AUTONOMOUS_COMPLETION_GATE_V4.cmd
```

The runner uses one visible window and shows:

- job state
- elapsed time
- git branch
- dirty-file count
- latest log activity
- release output status
- recent progress
- latest Codex log tail
- known issues file status

It does not push to remote and must not modify historical releases v0.1.0, v0.1.1, or v0.2.1.
