# v0.3.2 Recovery Finalize Checklist

- Verify branch is `feature/v0.3.2-autonomous-runner-hardening`
- Verify frozen historical releases are untouched
- Run test/lint/build from host PowerShell
- Write v0.3.2 delivery documents
- Create source release ZIP with normalized entry verification
- Create sample execution-pack ZIP and normalize JSON zipBase64 if needed
- Validate sample pack contents and multi-adapter entries
- Write SHA256.txt and RELEASE_MANIFEST.txt
- Write dogfood/RUNNER_HARDENING_VALIDATION.md
- Commit v0.3.2 changes
- Tag v0.3.2
- Run `scripts/verify-autonomous-completion.ps1 -TargetVersion v0.3.2`
