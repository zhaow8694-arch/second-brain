# Codex Task Prompt

You are working on Todo API MVP. Follow the generated task queue exactly.

## Tasks

### TASK-001 Initialize target project

- Phase: setup
- Risk: L1
- Dependencies: none
- Done criteria: Project dependencies install successfully.; Lint, test, and build commands are available.
- Test command: `pnpm build`

### TASK-002 Implement v0.1 core MVP

- Phase: core
- Risk: L2
- Dependencies: TASK-001
- Done criteria: MVP behavior is implemented without expanding scope.; Explicit requirements from PROJECT_SPEC are traceable in code or docs.
- Test command: `pnpm test`

### TASK-003 Apply runtime and permission boundaries

- Phase: runtime
- Risk: L2
- Dependencies: TASK-001
- Done criteria: Runtime policy files are present.; High-risk operations are documented instead of executed automatically.
- Test command: `pnpm test`

### TASK-004 Add focused tests

- Phase: qa
- Risk: L1
- Dependencies: TASK-002, TASK-003
- Done criteria: Core behavior has automated tests.; Regression-prone script or adapter output is covered.
- Test command: `pnpm test`

### TASK-005 Write delivery documentation

- Phase: docs
- Risk: L1
- Dependencies: TASK-003
- Done criteria: README, RUN_APP, ENV_SETUP, and security docs are complete.; Known assumptions and open questions are documented honestly.
- Test command: `pnpm lint`

### TASK-006 Finalize local delivery artifact

- Phase: finalize
- Risk: L2
- Dependencies: TASK-004, TASK-005
- Done criteria: Finalize script completes locally.; Release notes and final delivery check are present.; Remote push or deployment is not performed.
- Test command: `pnpm build`


## Permission Actions

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

Use scripts/finalize.ps1 or scripts/finalize.sh for final delivery.