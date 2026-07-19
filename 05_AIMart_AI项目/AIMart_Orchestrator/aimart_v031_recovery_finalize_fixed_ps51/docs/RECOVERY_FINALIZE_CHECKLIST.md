# v0.3.1 Recovery Finalize Checklist

The fixed runner should end with `RECOVERY FINALIZE PASS`.

It must create:

- releases/v0.3.1/aimart-orchestrator-v0.3.1-source.zip
- releases/v0.3.1/samples/todo-api-generated-execution-pack.zip
- releases/v0.3.1/SHA256.txt
- releases/v0.3.1/RELEASE_MANIFEST.txt
- V0.3.1_RECOVERY_FINALIZE_REPORT.md
- local commit
- local tag v0.3.1

It must not modify historical releases v0.1.0, v0.1.1, v0.2.1, v0.2.2, or v0.3.0.
