# AIMart v0.3.1 Hotfix + Recovery Toolkit V5

This toolkit fixes the remaining v0.3.1 recovery failures:

- Preserves source ZIP relative paths so `src/lib/generators/script-pack.ts` is present.
- Reapplies the v0.3.1 completion-gate compatibility literals.
- Runs host-side `pnpm test`, `pnpm lint`, and `pnpm build`.
- Creates `releases/v0.3.1`.
- Generates the sample execution-pack ZIP through the local Next.js API.
- Verifies customer-side runtime files and multi-agent adapter files.
- Writes SHA256, RELEASE_MANIFEST, dogfood evidence, and recovery report.
- Commits and tags v0.3.1 locally.

Run:

`START_V0.3.1_HOTFIX_AND_RECOVERY_V5.cmd`
