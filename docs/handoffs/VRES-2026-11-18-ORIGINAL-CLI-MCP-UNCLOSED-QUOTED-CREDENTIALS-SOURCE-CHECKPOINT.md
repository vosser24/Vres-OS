# 2026-11-18 — Original Claude Code CLI/FastMCP unterminated quoted-credential safety — CANONICAL READ FIRST

**STATUS: NEW original source and tests PUBLISHED on dedicated unprotected GitHub branch; remote exact HEAD/TREE/PARENT/FOUR BLOBS verified. Python/AST/compile/pytest/PowerShell/native Claude/MCP/hooks/PostgreSQL even SELECT/Windows/install/real UAT on current source NOT_RUN or HELD. NO external independent #185 acceptance or operational clearance.**

## Owner's binding product direction

Build ONE complete useful production-quality PERSONAL Windows companion to ORIGINAL Claude Code CLI as PRIMARY interface; original FastMCP is integral. Preserve original Chairman, original Repository task/session/checkpoint/recorded-result/history owner, explicit task selection and real Claude session task_resume, projects, credential/data-source linking, original experience_retrieve and governed learning, original install.ps1/update.ps1/recovery. NO new GUI, no priority Tk Desktop changes (Tk untouched), NO new MCP server, Chairman, store, runtime, installer, enterprise IAM or multitenancy. Preserve ALL original V-01..V-42; M0..M8; W0..W3; W4 R1..R13; C2B/K0; original October 22/30/31 and November 5 plans. Use proportional P0/P1/P2/P3 owner approvals; prioritize practical integrated work, not test-only microphases.

## Authenticated live repository, current source and protected refs

- Repository https://github.com/vosser24/Vres-OS, repository ID 1368577038; authenticated owner vosser24 ID 62554356; GitHub App installation ID 85535881 selected repositories.
- NEW exact engineering branch: feature/personal-w4-cli-mcp-unclosed-quoted-credentials-20261118.
- Verified HEAD: 2a168713bb6de4610456677cc163731add4d5502.
- Verified TREE: 3f862f6dbd667c697a829fd9980226881f57966a.
- SOLE parent: 5c6e00e4f34ba7112ce1aff3580c92e3a4468bea.
- GitHub commit: https://github.com/vosser24/Vres-OS/commit/2a168713bb6de4610456677cc163731add4d5502 .
- Branched from exact verified prior HEAD; Git blob/tree/commit publication via NON-FORCE expected-SHA lease; remotely re-read matching ref, commit, tree, parent and four blobs. Direct parent comparison: 1 ahead/0 behind and exactly four changed paths.
- Product main HEAD 9a8acc5d464b96432a93cb95daa9581412fb07ee, TREE 659d3fdd6e635dbaecbd5c492ba7279754edaec7, parents 6af7bddf246e0f628c3e52add9528742e85189ca and 8ae041721bf0418f6472ab541b6838fd73fec46a.
- Protected R13 branch feature/personal-w4-r13-universal-staging-hold-20261106 HEAD bcf62460d68caebfdbd0e838d44c5997992c5fbc, TREE 9bbc5615fef4a8f785e9ddb0056e9430ffe25d63, parent 0badcd34d1eafbce5f815512a489d70cb240eecd.
- New engineering vs main: 242 ahead/0 behind. Vs R13: DIVERGED, 133 ahead/13 behind, merge base 982e77f2f4974b4fbca5da91d3e11aeb56e40271. Never merge protected main/R13.

### Four current engineering changed files / independently verified exact blobs

1. src/vres_os/redaction.py — 07769589e4e4123576b10df2743bfe64ca610497
2. tests/test_redaction.py — 46115631a00d4164bf02657cfa7c0928faa1f51d
3. tests/test_workday_overview_mcp.py — 50cf3ba3a8bf6e8a6c6f30e07b103c8a3a1d4199
4. docs/architecture/VRES-W4-ORIGINAL-CLAUDE-SELECTED-TASK-CONTINUITY-PREVIEW-2026-11-18.md — 2e6a91a2fa90295f9d1db5b109f00d6540a6e1a6

## Static defect, narrow source correction and provenance

At prior source 5c6e00e4, a credential assignment with an opening but unmatched quote and a whitespace-separated value, e.g. password="synthetic-first synthetic-second, failed the complete-quoted value alternatives in the canonical _KV/_VALUE redactor and fell through to the generic non-whitespace fallback. Only the first token could be masked, leaving the second token visible; the residual postcondition could accept the safely masked prefix. This is a **source-deduced potential leak, NOT an observed pytest failure**.

The SAME canonical redactor now uses a conservative end-of-field unmatched quote fallback, so the complete malformed credential value is masked (possible over-redaction). Already masked placeholder idempotence now requires an exact unquoted value or properly paired quotes. Existing complete multiline quoted-value support is preserved. Two parameterized canonical sanitizer regressions and one existing original FastMCP workday scalar regression AUTHORED NOT_RUN. No new MCP/runtime/Chairman/Repository/task/result store/installer, schema, hook, Tk GUI or host route. Complex ambiguous quote, performance and false-negative boundaries remain reviewer subjects; no universal credential safety claim.

Unchanged ORIGINAL blobs at new engineering HEAD: src/vres_os/mcp_server.py f75f3a4f32dfa2e89b3feb93145088d6edeb0319; src/vres_os/repository.py b975ce796eac5a4334d8a1d998c9e7fddbee5490; install.ps1 4aea9d94794c17ec9c74d28a6b8db108fde73d7d; update.ps1 eb0fc000e15ef3df3823d38ceb31d3b7145127ac; src/vres_os/personal_day_desktop.py 241a7688321a2e65f3e14d99cc7f8c7335315f4d.

## Canonical docs before this checkpoint / new reviewer request

Canonical docs branch docs/chatgpt-continuity-20261023 PRE-UPDATE HEAD bf889c11527ddf51d6489a0b8132b82bfc8e48f8, TREE 24a2c198789711c7fc482c3873591272ca1b7904, sole parent 2a91310c36162067a77139c205bb5460790ddc9a. PRE-update index blob 1194fde03b3c7a6ff6fce970ed56ff33f031b338. Intended EXACT THREE docs path modifications: this NEW handoff, NEW source-pinned independent-review evidence request at docs/reviews/VRES-2026-11-18-ORIGINAL-CLI-MCP-UNCLOSED-QUOTED-CREDENTIALS-185-REVIEW-REQUEST.md, and PREPEND canonical continuity index. Verify ACTUAL new docs SHA/TREE/PARENT and all three blobs after remote publication. A first JS draft-composition SyntaxError happened BEFORE ANY docs write; corrected publication must not be mistaken for Python test execution.

Issue #185 https://github.com/vosser24/Vres-OS/issues/185 OPEN; entire body and all eight comments read. All eight comments authored by owner vosser24; NO genuinely distinct attributable positive THREAT_MODEL / RELEASE_DESIGN / OPERATIONS reviewer verdict or F1/Fable approval. Earlier unsigned external Claude report: THREAT_MODEL REVISE / RELEASE_DESIGN DESIGN_REVISE / OPERATIONS conditional-blocked; explicitly did not read whole #185, not signoff. Source-specific read-only reviewer packet published; request is NOT review. Other issue states: #165–170 OPEN, #176 OPEN, #174 CLOSED FOR FOUNDATION ONLY.

## Absolute safety holds and original Windows installer

- LIVE_SCHEMA_048_INCIDENT=OPEN: absolutely NO PostgreSQL including SELECT, direct or indirect, no migrations or DB tests.
- HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: absolutely NO ordinary native Claude Code/installed FastMCP/hook execution.
- Independently trusted F1/Fable positive authority NOT_GRANTED; original P3, Windows Git L2, R13 staging/WPR, Windows install/update/recovery/real UAT all HELD. Protected installed Windows P2 state UNKNOWN; unpushed Windows files UNKNOWN, no local PC access performed.
- No original TASK-DAY-01 mutation, no credentials, user profile, PRISM/real legacy, protected worktrees, global KEEP/DROP, destructive rollback, real task adoption, protected main/R13 merge.
- Original fresh install.ps1 must detect and separately offer missing Claude Code, PostgreSQL 17, optional Node.js LTS and optional npm Codex with individual informed DEFAULT-NO operator consent. -WithCodex is NOT blanket package permission. Maintenance -Update must NEVER silently acquire external packages; preserve original fetch/checkout, preflight, installer journal, rollback/recovery.
- Before owner-selected clean Windows Git fetch/checkout and original update.ps1 preflight/update, independently approve exact source COMMIT/TREE, independent publisher/source SHA-256 trust root, Git.exe/native DLL/GCM/SSH and Python.exe/native/Tk SHA-256 provenance, COMPLETE offline transitive hash-locked wheelhouse, Windows NTFS path/reparse/ADS/hardlink/alias/ACL/object identity/interrupted recovery protections; closure of both incidents and separate informed operator consent. NEVER overwrite installed P2 without approval.

## Exact current test provenance and rejected history

Current source 2a168713: remote GitHub integrity VERIFIED. Python/AST/compile/pytest/PowerShell/native CLI/FastMCP/hooks/PostgreSQL even SELECT/Windows/install/recovery/FULL V-01..V-42 UAT NOT_RUN or HELD. New tests AUTHORED NOT_RUN; no current functional PASS. Historic 732/732 eligible guarded PASS and 407/407 static compile belong ONLY to older 9e2b538b; preserve earlier 727/730 with three fixture failures, nine child cases deselected, three psycopg test modules not collected, rejected incomplete-stub 11 FAIL vs separately corrected 11/11 PASS, rejected SessionEnd assertion, rejected prerequisite-removal SHA d620c67956b95957196e07c121b0bead19a6e844 and unpublished rejected provenance c56847b8276581ee66a7aae5b512a94a341a5248. Do not transfer older PASS to this source.

## EXACT NEXT operation / hard checkpoint

1. NEW CHAT: fresh authenticated LIVE GitHub verification of current newest source/docs/main/R13 HEAD/TREE/PARENT, source FOUR blobs, new docs THREE blobs, compares, account/app, issue statuses, full #185 and eight comments. Read latest COMPLETE handoff, reviewer request and canonical READ FIRST index before new action.
2. PRIORITIZE genuinely independent, attributable source-specific #185 read-only three-verdict THREAT_MODEL, RELEASE_DESIGN and OPERATIONS review; demand severity/file-line evidence, observed PASS/FAIL/NOT_RUN and minimal corrections. No author self-review as independent acceptance.
3. Resolve BOTH operational incidents with independently verified evidence before any DB or native host path; resolve publisher/toolchain/wheelhouse/NTFS/F1 trust gaps.
4. Only after separate, informed owner authorization, advance to original separately clean Windows Git fetch/approved exact checkout, original update.ps1 preflight/update/install/recovery, integrated original Claude Code CLI/FastMCP/PostgreSQL UAT covering all V-01..V-42. No second app or architecture drift.
5. Checkpoint at/before 20 replies or conservative context-risk half: stop feature phases, verify GitHub and publish permitted changes on correct branches, detailed handoff/index, remote readback, FULL inline fresh-chat prompt and end session. No precise context percent claim, no asynchronous handoff.

**Next milestone: actually independent #185 3-part review and evidence-backed incident closure, not a Windows install.**
