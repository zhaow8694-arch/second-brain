# Security And Permissions

## Risk Levels

- L0: read_only - Read-only project inspection such as listing files or checking status. (allow)
- L1: project_safe - Project-local install, lint, test, and build commands. (allow)
- L2: recoverable_project_change - Project-local generated files, formatting, or lockfile updates. (allow)
- L3: environment_change - Docker, database migrations, or system-level dependency changes. (queue_for_approval)
- L4: external_resource_change - Remote Git, deployment, cloud, or PR merge operations. (queue_for_approval)
- L5: destructive_or_secret_access - Destructive commands or commands that read secrets. (deny)

## Command Rules

- `git status`: L0, allow - Allowed project-local verification or read-only command.
- `git diff`: L0, allow - Allowed project-local verification or read-only command.
- `pnpm install`: L1, allow - Allowed project-local verification or read-only command.
- `pnpm lint`: L1, allow - Allowed project-local verification or read-only command.
- `pnpm test`: L1, allow - Allowed project-local verification or read-only command.
- `pnpm build`: L1, allow - Allowed project-local verification or read-only command.
- `node -v`: L1, allow - Allowed project-local verification or read-only command.
- `pnpm -v`: L1, allow - Allowed project-local verification or read-only command.
- `git push`: L4, queue_for_approval - External resource changes require explicit approval.
- `git push --tags`: L4, queue_for_approval - External resource changes require explicit approval.
- `gh pr create`: L4, queue_for_approval - External resource changes require explicit approval.
- `vercel deploy`: L4, queue_for_approval - External resource changes require explicit approval.
- `terraform apply`: L4, queue_for_approval - External resource changes require explicit approval.
- `kubectl apply`: L4, queue_for_approval - External resource changes require explicit approval.
- `rm -rf /`: L5, deny - Secret access or destructive operation is forbidden by default.
- `sudo rm -rf`: L5, deny - Secret access or destructive operation is forbidden by default.
- `cat ~/.ssh/*`: L5, deny - Secret access or destructive operation is forbidden by default.
- `cat ~/.aws/*`: L5, deny - Secret access or destructive operation is forbidden by default.
- `cat .env`: L5, deny - Secret access or destructive operation is forbidden by default.
- `printenv`: L5, deny - Secret access or destructive operation is forbidden by default.
- `terraform destroy`: L5, deny - Secret access or destructive operation is forbidden by default.
- `kubectl delete`: L5, deny - Secret access or destructive operation is forbidden by default.

Commands marked queue_for_approval must be written to runtime/APPROVAL_QUEUE.md before execution.
Commands marked deny must not be executed.