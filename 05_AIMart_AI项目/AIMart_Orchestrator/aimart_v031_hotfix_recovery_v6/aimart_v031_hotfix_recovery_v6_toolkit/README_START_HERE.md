# AIMart v0.3.1 Hotfix + Recovery Toolkit V6

Use this toolkit only for the existing branch:

`feature/v0.3.1-auto-verified-customer-runtime`

V6 fixes the V5 runner issue where `pnpm` was invoked without arguments and only printed pnpm help.
It executes validation through `cmd.exe /d /c "pnpm test"`, `pnpm lint`, and `pnpm build`.

It also reapplies the known v0.3.1 compatibility literals, fixes the TypeScript template-literal parsing issue,
rebuilds the source release ZIP with preserved relative paths, generates the sample execution-pack ZIP, verifies it,
writes SHA256 and RELEASE_MANIFEST, commits, and retags v0.3.1.
