# AGENTS.md - Codex Target Adapter

Codex is the target coding agent for this generated execution pack.

## Project Facts

- Project: Todo API MVP
- MVP scope: 只做后端 API, 不做前端界面
- Forbidden items: 只做后端 API, 不做前端界面
- Security boundaries: Do not read .env, SSH keys, or production credentials

## Rules

1. Do not expand the MVP scope.
2. Execute tasks in TASK_QUEUE order.
3. Update PROGRESS_LOG after each completed task.
4. Put high-risk commands in runtime/APPROVAL_QUEUE.md before execution.
5. Do not read secrets, local credential files, or production resources.
6. Run scripts/finalize.ps1 or scripts/finalize.sh before final delivery.