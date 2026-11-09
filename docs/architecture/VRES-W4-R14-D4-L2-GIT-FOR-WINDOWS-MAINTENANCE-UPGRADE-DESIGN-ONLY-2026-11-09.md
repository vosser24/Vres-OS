# Vres-OS W4 R14-D4 L2 — controlled Git for Windows maintenance upgrade PROPOSAL ONLY
**Date:** 2026-11-09 (Europe/Athens). **Verdict:** DESIGN_ONLY / no owner authorization to download, execute Git, install, upgrade, uninstall, alter credentials or change the Windows host. The prior A1-A4 identity gate remains PREFLIGHT_REFUSED and the R13 operational-stage hold remains absolute.

## Why the proposal exists and actual Windows evidence
The owner submitted the exact earlier 1,803-character L1 fixed-path command from GitHub blob `2f4a39e4600d1a133ff742b8f518aee45c417bfc` in a non-elevated CMD prompt and pasted this output:

`PRESENT=C:\Program Files\Git\cmd\git.exe`
`PRODUCT_VERSION=2.55.0.windows.5`
`PRESENT=C:\Program Files\Git\mingw64\bin\git.exe`
`PRODUCT_VERSION=2.55.0.windows.5`
`UNAVAILABLE=C:\Program Files\Git\ucrt64\bin\git.exe`
`LAYOUT_ONLY_NO_GIT_RUN_NO_TRUST_GRANTED`

Scope of evidence: owner-supplied transcript of successful L1 observation only. ProductVersion is untrusted executable metadata, not an authenticated installer/version, SHA-256, code-signing identity or trust assertion. Output is not independently attested host telemetry; no observed Git executable invocation from the L1 script; no live host inspection by ChatGPT. The old A1-A4 preflight had failed at missing `ucrt64`; its version/signer/hash checks NEVER ran. The owner previously supplied a distinct Claude.ai cloud L1 static DESIGN_ACCEPT report: 0 P0/P1/P2 findings, five nonblocking P3 notes (CMD-vs-PowerShell prompt, broken reparse interpretation, TOCTOU/hardlinks, OS incidental logging/cloud, untrusted version text including control characters). That report is not a separate authenticated HUMAN review, does not close issue #185, and does not retroactively grant Windows permissions.

## Maintained release candidate pinned for planning, not installation
The official git-scm.com Windows download page identified Git for Windows `2.56.0(4)` on 2026-11-09, released 2026-10-26:
- Official page: https://git-scm.com/install/windows
- Official version release: https://github.com/git-for-windows/git/releases/tag/v2.56.0.windows.4
- Exact proposed x64 standalone installer name: `Git-2.56.0.4-64-bit.exe`.
- SHA-256 printed on that official release: `4961a4a8cc778d8b6e00a5819e5fe4d078b754555aff7aedc2d77a5d74c2de80`.
- Official Git for Windows release notes: https://github.com/git-for-windows/build-extra/blob/main/ReleaseNotes.md
- Git Credential Manager v3 change notes: https://github.com/git-ecosystem/git-credential-manager/releases

These are advisory public facts, not user-selected cryptographic trust roots or observations of downloaded bytes. Recheck the official maintained version before any owner decision; NEVER silently change pinned installer/version to an even newer release. Do not use winget/third-party mirrors or auto-update for this plan.

## Real user-impact risks (proportional personal-app scope)
1. Migration `mingw64` -> `ucrt64`: legacy hard-coded internal Git/GCM paths can break; the stable `cmd/git.exe` wrapper is preferred for future invocation, but NO Git invocation is authorized now. Release notes document a compatibility shim for stale GCM paths; it is not proof every custom configuration will work.
2. Bundled Git Credential Manager is v3.0.2, with breaking changes in platform support/authentication experience. There may be new sign-in prompts/broker flows. NO credential-store, auth-token, browser or profile inspection is authorized by this proposal.
3. In-place installer could change Program Files binaries, DLLs, Git Bash, Git LFS, SSH tooling, PATH/registry/shell integration, default components, shortcuts and system caches. Installer could require elevation, close processes and use networking (including certificate revocation/SmartScreen/Defender). Treat these as intended/possible installed-system changes, NOT a read-only P0/P1 step.
4. Git for Windows v2.55.0.windows.5 release notes flag possible changes to previously selected external OpenSSH. Before any future installation, obtain an owner-confirmed choice of bundled vs external OpenSSH. Preserve existing Git editor, line endings, PATH, credential-helper and SSH behavior where practical; do not guess present settings or probe user profiles without separately approved bounded access.
5. Future rollback to `2.55.0.windows.5` may reintroduce known security/compatibility issues. A 'reinstall old Git' step is NOT automatic and is not promised to restore registry, credential-manager or per-user configuration. Protected installed P2, real legacy/PRISM and TASK-DAY-01 remain untouched.

## Explicit staged gates; NO current action approved
**L2-P0 — current planning (allowed, GitHub documentation only).** This proposal; collect no Windows information. Preserve observed L1 transcript with clear provenance. Review upstream changes/expected impacts. No download, host command, registry/credentials read, installer or Git executable run.

**L2-P1 — separately requested OWNER consent for download and isolated file trust evidence, NOT_GRANTED.** Before requesting that consent, finalize target version/bitness and official source. Provide a vetted exact read-only inspection plan including any local output location, downloaded bytes, permitted network/Defender/AMSI/cache side effects and no access to user profiles. A separately approved action may download only the specific official x64 installer, verify its full SHA-256 against independently rechecked release digest and observe Authenticode status/chain/signer with accepted revocation/network effects. Hash and signer are complementary, neither alone proves all downstream safety. Windows 5.1 Restricted-policy compatibility must be reviewed; avoid `Get-FileHash` script-module assumptions. No download or host checks now.

**L2-P2 — separately requested OWNER consent for an interactive installer and explicit system changes, NOT_GRANTED.** Require favorable P1 file evidence and an owner-approved exact host change list first. The installer may require admin. Identify actual Windows OS/architecture by separately approved non-sensitive observation; avoid assuming x64 from path alone. Record owner's existing Git usage dependencies and selected installer options WITHOUT exposing secrets. Review GCM v3 transition, PATH scope, SSH selection, git-lfs, shell integration, default editor, line-endings, and Windows restart/rollback conditions. Never silently install or use unattended/silent switches, winget, a credential migration, programmatic restoration or force. Stop on unexpected installer options or trust results.

**L2-P3 — separately authorized verification after installation (NOT_GRANTED).** First narrow read-only post-install comparison for fixed `cmd/git.exe` and `ucrt64/bin/git.exe`: actual file existence, reparse refusal, intended ProductVersion, trusted digital signatures and SHA-256s of both binaries. Such comparison requires an exact new reviewed owner-approved command, and independently selected trust criteria; published installer hash does NOT constitute binary-file hash pins. A later distinct approval is required to INVOKE Git or create an inert source archive. No operational W4 R13 staging, importer, Python, original release stage, installer-driven Vres launch or protected P2 activation.

**Emergency halt / recovery (NOT_AUTHORIZED).** If downloaded file, signer, checksum, version or installer choice is inconsistent: STOP; no install. If an installation fails: do not auto-run repair/uninstall/rollback; preserve only operator-visible error descriptions and seek a separate owner-approved bounded recovery plan. A previous installer is not yet selected/authenticated or known available. Do not back up, export, inspect or alter real credentials, user-profile settings or P2. A future local rollback is a distinct P2/P3 operation, not a guaranteed reversible transaction.

## Evidence/status matrix
- L1 CMD transcript: OWNER_REPORTED_OBSERVATION; command reached marker, three path statuses reported, two matching `2.55.0.windows.5` resource strings; no version authenticity asserted.
- L1 external cloud STATIC DESIGN_ACCEPT: OWNER_SUPPLIED, NOT authenticated human/#185 signoff; Windows parser independently by reviewer NOT_RUN.
- GitHub L1 blob: `2f4a39e4600d1a133ff742b8f518aee45c417bfc`, previous docs HEAD `dabe3b2567b83f2a801347bd1889d12d175b028b`, previous docs tree `329b369e515be13d1102bc37488da88b1d54bf21` reported by reviewer, previous sole parent `32948a6a4a28f68fe94c55d8d78b75209551a549` reported by reviewer.
- New release download/installer checksum/Authenticode, Windows OS identity, actual app config/credentials, installed-state readback: NOT_RUN / NOT_VERIFIED.
- R13 authored tests: 47, actual R13 pytest NOT_RUN; original-owner ZIP, NTFS gate, wheels, installer, VS UAT #169 and personal pilot #170 NOT_RUN.

## Binding safety holds and preserved roadmap
`LIVE_SCHEMA_048_INCIDENT=OPEN` — no PostgreSQL even SELECT. `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` — no native Claude Code or installed hooks. Original P3 OPEN; F1/Fable independent positive authority NOT_GRANTED. Never touch installed protected P2 (historical source `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c`; physical identity NOT_REVERIFIED), its historical Sonnet/high Chairman, real credentials, any real legacy/PRISM project, protected worktrees, original TASK-DAY-01 note/Personal Desk, native hooks, migrations, user-profile changes, runtime, operational staging/rollback, sandbox R2, or product main.
Preserve original V-01..V-42, M0..M8, issue #163/#164/#165-170/#174/#176/#185, W0 integration, narrow W1/W2/W3, R1-R13 evidence and rejected attempts, 232 file/41 inert migrations 001-041 and SHA-256 inventory `c6dab3be2ad86cf0fca2586b870665bc20ad8830c9e76e2f677f0ec8801b13c6`; hooks.json and .mcp.json remain inert and unsafe-to-activate. D3 independent publisher architecture remains OPTIONAL.

## Next permitted milestone
Obtain focused read-only external STATIC review of this L2 maintenance upgrade plan's risks, official artifact identity and boundaries, **not** of any installer command. Then present a separate precise P1 file-acquisition/verification consent request only if warranted. Current user 'proceed' authorizes planning and docs continuity only, NOT Windows downloading, executing or changing. All resulting execution steps remain blocked without independently informed owner consent.
