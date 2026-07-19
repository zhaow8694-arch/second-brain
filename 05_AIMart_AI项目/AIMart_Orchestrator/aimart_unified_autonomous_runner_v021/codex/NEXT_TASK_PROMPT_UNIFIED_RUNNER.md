You are the only coding agent for this project.

Current mode:
AIMart Unified Autonomous Execution Mode.

Context:
The user has correctly identified a product flaw: "unattended mode" should not require the user to open multiple windows, run a separate monitor, and manually inspect logs. The next task is to implement a unified one-window/self-monitoring runner capability in AIMart itself.

Current project:
AIMart Orchestrator.

Baseline:
v0.1.1 is completed and tagged.
Do not modify releases/v0.1.0 or releases/v0.1.1.
Do not force-move v0.1.0 or v0.1.1 tags.
Do not push to remote.

Goal for this task:
Implement v0.2.1 Unified Autonomous Runner minimal closed loop.

Core requirement:
A user should be able to start one runner and see enough progress, health, latest log tail, final status, release status, and known issues in the same window or same generated status files. No separate monitoring script/window should be required.

Must implement:

1. Generated execution pack additions for Codex:
   - agent_adapters/codex/run-codex-unified-autonomous.ps1
   - agent_adapters/codex/run-codex-unified-autonomous.sh
   - agent_adapters/codex/CODEX_UNIFIED_AUTONOMOUS_RUNBOOK.md
   - agent_adapters/codex/CODEX_AUTONOMOUS_PROMPT.md

2. Runtime status files in generated execution packs:
   - runtime/AUTONOMOUS_RUN_STATUS.md
   - runtime/AUTONOMOUS_RUN_SUMMARY.md
   - runtime/AUTONOMOUS_HEALTH_CHECK.md

3. The unified runner scripts must:
   - Start Codex in autonomous mode.
   - Write combined logs.
   - Print heartbeat status in the same window.
   - Show last log lines periodically.
   - Perform post-run checks.
   - Print final summary.
   - Avoid requiring a separate monitoring window.
   - Refuse or warn when another Codex run is active unless explicitly overridden.

4. Web UI / docs:
   - Explain that Autonomous Mode is "single-entry, self-monitoring".
   - Avoid telling users to open multiple windows.
   - Clearly distinguish source release ZIP vs generated execution-pack ZIP.
   - Update generated docs/README.md, docs/RUN_APP.md, docs/SECURITY_AND_PERMISSIONS.md.

5. Tests:
   - Verify generated execution-pack ZIP contains the new unified runner files.
   - Verify runtime status files exist.
   - Verify existing generated pack structure still passes.
   - Add tests for unified runner text presence if practical.

6. Version and delivery:
   - Update package.json version to 0.2.1.
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
1. Continue until the task is complete.
2. Do not ask the user before ordinary local commands.
3. Automatically run lint/test/build.
4. If a test fails, fix it up to 3 rounds.
5. If blocked, write it to V0.2.1_KNOWN_ISSUES.md or BLOCKERS.md and continue independent tasks.
6. Update PROGRESS_LOG.md after each major phase.
7. Do not push to remote.
8. Do not modify releases/v0.1.0 or releases/v0.1.1.
9. Do not delete historical release directories.
10. Do not read .env, SSH keys, cloud credentials, or system secrets.
11. Do not perform production deployments, real database migrations, or cloud resource changes.

Allowed automatic commands:
- pnpm install
- pnpm lint
- pnpm test
- pnpm build
- powershell -ExecutionPolicy Bypass -File .\scripts\finalize.ps1
- Start local test server on 127.0.0.1 when needed.
- Read local port PID.
- Read ZIP entries for validation.
- Write releases/v0.2.1.
- Generate v0.2.1 source ZIP.
- Generate v0.2.1 sample execution-pack ZIP.
- Write v0.2.1 SHA256.txt and RELEASE_MANIFEST.txt.
- Create local tag v0.2.1.
- Delete superseded ZIP files inside releases/v0.2.1 only.

Forbidden automatic commands:
- git push
- git tag -f v0.1.0
- git tag -f v0.1.1
- git tag -d v0.1.0
- git tag -d v0.1.1
- Remove-Item releases\v0.1.0
- Remove-Item releases\v0.1.1
- Modify frozen artifacts under releases/v0.1.0 or releases/v0.1.1
- Read .env / ~/.ssh / system credentials
- Production deployment
- Real database migration
- Cloud resource creation or deletion

Final response must include:
- What was completed.
- Tests that passed.
- Release artifact paths.
- Sample execution-pack verification.
- Current git status.
- Whether local tag v0.2.1 exists.
- Known issues, if any.
