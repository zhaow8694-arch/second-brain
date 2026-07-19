You are the only coding agent for this repository. Do not delegate to Trae, Claude Code, Cursor, Copilot, or any other AI.

Current mode: AIMart Unified Autonomous Execution Mode.

Repository: AIMart Orchestrator.
Previous stable versions: v0.1.0, v0.1.1, and any completed v0.2.0 work already present in the repository.
Next target: v0.2.1 Unified Autonomous Visual Runner integration.

Primary goal:
Make AIMart-generated execution packs include a single-window autonomous runner experience. The user should not need separate runner, log, and monitor windows. A generated pack should provide one entrypoint that starts Codex, displays live status, tails recent logs, checks release output, reports progress, and prints a final summary.

Read first:
- AGENTS.md
- PRODUCT_SPEC.md
- TASK_QUEUE.md
- PROGRESS_LOG.md
- RELEASE_NOTES.md
- IMPLEMENTATION_REPORT.md
- FINAL_DELIVERY_CHECK.md
- V0.2.0_IMPLEMENTATION_REPORT.md if present
- V0.2.0_KNOWN_ISSUES.md if present
- V0.2.0_RELEASE_NOTES.md if present

Scope for v0.2.1:
1. Add generated Codex unified visual runner files to generated execution packs:
   - agent_adapters/codex/run-codex-unified-autonomous.ps1
   - agent_adapters/codex/run-codex-unified-autonomous.sh
   - agent_adapters/codex/CODEX_UNIFIED_AUTONOMOUS_RUNBOOK.md
   - runtime/AUTONOMOUS_RUN_STATUS.md
   - runtime/AUTONOMOUS_RUN_SUMMARY.md
   - runtime/AUTONOMOUS_HEALTH_CHECK.md

2. The generated PowerShell runner must be single-window:
   - Start Codex autonomously.
   - Show a live dashboard in the same window.
   - Show elapsed time, Git branch, dirty file count, latest log tail, release directory status, and known issues status.
   - Save logs under codex_runs/.
   - At completion, show exit code, release artifacts, sample execution pack status, Git status, and next recommended action.

3. The generated Bash runner should provide a comparable single-terminal experience for Unix-like environments.

4. Keep safety boundaries:
   - Do not push remote Git.
   - Do not read .env, SSH keys, cloud credentials, or system secrets.
   - Do not modify frozen release directories from older versions.
   - Do not perform production deployment, real database migrations, or cloud resource creation/deletion.
   - Write high-risk items to APPROVAL_QUEUE.md or KNOWN_ISSUES and continue other tasks.

5. Update Web UI/generation model if needed:
   - The execution mode choice should make it clear that Unified Autonomous Mode includes one-window status display.
   - Existing Supervised and Autonomous modes must keep working.

6. Update tests:
   - Packager tests should assert the new generated Codex unified runner files exist.
   - Runtime-pack tests should assert AUTONOMOUS_RUN_STATUS, AUTONOMOUS_RUN_SUMMARY, and AUTONOMOUS_HEALTH_CHECK exist.
   - Add tests for any new schema or UI field if changed.

7. Version and delivery:
   - Update package version to 0.2.1.
   - Update UI version display to v0.2.1.
   - Generate:
     - V0.2.1_IMPLEMENTATION_REPORT.md
     - V0.2.1_RELEASE_NOTES.md
     - V0.2.1_FINAL_DELIVERY_CHECK.md
     - V0.2.1_KNOWN_ISSUES.md
   - Generate releases/v0.2.1 source ZIP.
   - Generate releases/v0.2.1/samples/todo-api-generated-execution-pack.zip.
   - Generate SHA256.txt and RELEASE_MANIFEST.txt.

Execution rules:
- Continue until the task is complete or a real blocker is reached.
- Do not stop for ordinary commands.
- Automatically run tests and fix failures, up to 3 repair rounds.
- Update PROGRESS_LOG.md at key milestones.
- Do not push remote Git.
- Do not force or delete v0.1.0, v0.1.1, or v0.2.0 tags.
- Do not modify releases/v0.1.0 or releases/v0.1.1 frozen artifacts.
- If v0.2.0 release artifacts exist, preserve them unless the change is explicitly only documenting v0.2.1.

Allowed automatic commands:
- pnpm install
- pnpm lint
- pnpm test
- pnpm build
- powershell -ExecutionPolicy Bypass -File .\scripts\finalize.ps1
- start a local 127.0.0.1 test server
- read local port PID
- read ZIP entries for structure verification
- write releases/v0.2.1
- generate v0.2.1 source ZIP
- generate v0.2.1 sample execution-pack ZIP
- write v0.2.1 SHA256.txt
- write v0.2.1 RELEASE_MANIFEST.txt
- create local tag v0.2.1
- delete superseded old ZIP files only inside releases/v0.2.1

Forbidden automatic actions:
- git push
- git tag -f v0.1.0
- git tag -f v0.1.1
- git tag -f v0.2.0
- git tag -d v0.1.0
- git tag -d v0.1.1
- git tag -d v0.2.0
- Remove-Item releases\v0.1.0
- Remove-Item releases\v0.1.1
- Remove-Item releases\v0.2.0
- modify frozen artifacts under releases/v0.1.0 or releases/v0.1.1
- read .env, ~/.ssh, system credentials, or cloud credentials
- production deployment
- real database migration
- cloud resource creation or deletion

Final summary must include:
- Which v0.2.1 features were completed.
- Which tests passed.
- What artifacts exist under releases/v0.2.1.
- Whether the sample execution-pack ZIP contains the new unified autonomous runner files.
- Whether local tag v0.2.1 exists.
- Current git status.
- Remaining known issues, if any.
