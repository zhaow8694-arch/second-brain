# AIMart v0.3.1 Recovery Finalize Toolkit — FIXED PS5.1

This toolkit is for finishing an interrupted v0.3.1 run.

It does not ask Codex to do more coding. It lets the host PowerShell perform the final validation and freeze steps:

1. run tests, lint, and build
2. create `releases/v0.3.1`
3. create source release ZIP
4. generate a sample execution-pack ZIP via the local app API
5. verify source ZIP and sample execution-pack ZIP
6. write SHA256 and RELEASE_MANIFEST
7. write V0.3.1_RECOVERY_FINALIZE_REPORT.md
8. commit and tag v0.3.1 locally

Target project:

`E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack`

Run:

`START_V0.3.1_RECOVERY_FINALIZE_FIXED.cmd`

Do not run older v0.3.1 recovery toolkits.
