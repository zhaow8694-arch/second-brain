# Safe Autonomous Commands

These commands are considered acceptable for AIMart autonomous runs when confined to the project workspace:

- pnpm install
- pnpm lint
- pnpm test
- pnpm build
- powershell -ExecutionPolicy Bypass -File .\scripts\finalize.ps1
- Start local Next.js server on 127.0.0.1 for verification
- Get-NetTCPConnection for local test port PID lookup
- Read ZIP entries for artifact validation
- Write artifacts under the current release directory, for example releases/v0.2.0
- Generate SHA256.txt and RELEASE_MANIFEST.txt
- Create the current version local tag
- Delete superseded ZIP files inside the current release directory only
