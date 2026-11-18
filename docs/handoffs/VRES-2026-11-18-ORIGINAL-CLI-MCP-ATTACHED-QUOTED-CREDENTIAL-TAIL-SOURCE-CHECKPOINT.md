# 2026-11-18 — Original CLI/MCP attached quoted credential-tail correction — CANONICAL READ FIRST

**STATUS: SOURCE PUBLISHED on dedicated unprotected engineering feature branch, remotely VERIFIED exact HEAD/TREE/PARENT and THREE blobs. All exact-source Python/AST/compile/pytest/PowerShell/native Claude/FastMCP/hooks/PostgreSQL including SELECT/Windows/install/recovery/V-01..V-42 UAT NOT_RUN or HELD. Source-derived concern, NOT a runtime test failure or independent security verdict.**

## Binding owner objective and scope

Build ONE practical production-quality PERSONAL Windows companion to Claude Code CLI (PRIMARY interface), with the ORIGINAL FastMCP server as integral capability. Preserve original Chairman, original Repository task/session/result/history/checkpoint authority and real task_resume/current Claude session binding, user-explicit task selection, projects, credential and data-source links, experience_retrieve/governed learning, original install.ps1/update.ps1/recovery. No new GUI, no Tk Desktop priority or mutation, duplicate Chairman/MCP/runtime/task/result store, alternate installer, enterprise IAM, multitenancy or architectural redesign. Preserve V-01..V-42, M0..M8, W0..W3, W4 R1..R13, C2B/K0, October 22/30/31 and November 5 roadmaps. P0/P1/P2/P3 proportionate approvals, integrated useful progress.

## Authenticated repository and source identity

- URL: https://github.com/vosser24/Vres-OS; repository ID 1368577038; live authenticated vosser24 user ID 62554356; GitHub App installation 85535881.
- Engineering branch: feature/personal-w4-cli-mcp-attached-quoted-credential-tail-20261118
- HEAD: 8c722b1db8ecca7950c7efd7333d634e65c19e09
- TREE: d07c3be591574b7d30858cae803ae8320249260a
- SOLE PARENT: 2a168713bb6de4610456677cc163731add4d5502
- Commit: https://github.com/vosser24/Vres-OS/commit/8c722b1db8ecca7950c7efd7333d634e65c19e09
- Non-force expected-SHA update from parent, readback matching ref, raw commit tree/parent, exactly THREE changed file blobs; direct parent compare 1 ahead/0 behind.
- New source compared with main: 243 ahead/0 behind. Compared with protected R13: DIVERGED 134 ahead/13 behind; merge base 982e77f2f4974b4fbca5da91d3e11aeb56e40271. NO MERGE.

### Exact three engineering changed files / Git blob IDs

1. src/vres_os/redaction.py — 09ea436429239031072eb73eb9a55c5a84291d1a (MODIFIED)
2. tests/test_redaction.py — cafdf7cad8a5584611b0fdb4b483971145e3278d (MODIFIED)
3. docs/architecture/VRES-W4-ORIGINAL-CLAUDE-SELECTED-TASK-CONTINUITY-PREVIEW-2026-11-18.md — e0740e08a05ab1fb50ae620b066212db495ca5f5 (MODIFIED)

Original unchanged source blobs at this current HEAD independently re-read: src/vres_os/mcp_server.py f75f3a4f32dfa2e89b3feb93145088d6edeb0319; src/vres_os/repository.py b975ce796eac5a4334d8a1d998c9e7fddbee5490; install.ps1 4aea9d94794c17ec9c74d28a6b8db108fde73d7d; update.ps1 eb0fc000e15ef3df3823d38ceb31d3b7145127ac; src/vres_os/personal_day_desktop.py 241a7688321a2e65f3e14d99cc7f8c7335315f4d.

## Source-derived security finding and narrow correction

Original _VALUE regex in canonical src/vres_os/redaction.py at parent 2a168713 accepted a balanced quoted credential without testing what came immediately after its closing quote. Input password="synthetic-first"synthetic-attached could redact only the quoted first value and leave synthetic-attached visible in standalone redact_text or nested redact. The existing original FastMCP sanitize_text residual gate can refuse some such complete scalar outputs, but it does not guard every direct redactor consumer. This was derived by static regex inspection, not demonstrated through executed Python or observed pytest.

The SAME original canonical _VALUE regex now requires a right-hand field boundary after a balanced quoted value: end-of-string, whitespace, comma, semicolon, closing brace or bracket. A quote with immediately attached bytes instead uses the existing conservative malformed-field fallback through end of persisted field, deliberately allowing over-redaction. Two parameterized new tests cover four malicious attached-tail shapes and four valid separate-field controls; direct redact_text, nested redact and sanitize_text expected behavior, AUTHORED NOT_RUN. No separate sanitizer/MCP/Chairman/store, no installer/schema/Tk/host change, no universal credential-proof claim.

### Rejected draft and provenance

The first JS source-publishing script draft failed at PARSE TIME with SyntaxError (an unescaped JavaScript template quote in the documentation string), BEFORE any GitHub repository write, blob creation or Python execution. A corrected script subsequently created the three blobs, exact-base Git tree and one commit; created a new branch at source parent; nonforce expected-SHA lease advanced it; remote ref/raw commit/three blobs/direct diff independently read back. Do not call the draft error a pytest/runtime failure. It did not produce source code or a rejected Git commit.

## Protected branches and issue states

Protected product main HEAD 9a8acc5d464b96432a93cb95daa9581412fb07ee, TREE 659d3fdd6e635dbaecbd5c492ba7279754edaec7, parents 6af7bddf246e0f628c3e52add9528742e85189ca and 8ae041721bf0418f6472ab541b6838fd73fec46a. Protected R13 feature/personal-w4-r13-universal-staging-hold-20261106 HEAD bcf62460d68caebfdbd0e838d44c5997992c5fbc, TREE 9bbc5615fef4a8f785e9ddb0056e9430ffe25d63, parent 0badcd34d1eafbce5f815512a489d70cb240eecd.

Live issue readback: #165, #166, #167, #168, #169, #170 and #176 OPEN; #174 CLOSED FOR FOUNDATION ONLY; #185 OPEN, eight issue comments each authored by vosser24. Complete issue #185 and all eight comment payloads inspected. No genuinely distinct attributable independent THREAT_MODEL / RELEASE_DESIGN / OPERATIONS positive reviewer verdict, no assigned reviewer proven. Prior owner-uploaded unsigned external Claude note was THREAT_MODEL REVISE, RELEASE_DESIGN DESIGN_REVISE, OPERATIONS CONDITIONAL/BLOCKED, and explicitly did not read all #185; not independent acceptance.

## Absolute hard holds and consent

- LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL whatsoever, even SELECT, direct or indirect. No DB tests, migrations or catalog reads.
- HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: NO ordinary native Claude Code, installed FastMCP host or hooks; no host access disguised as read-only.
- Independently trusted positive F1/Fable authority NOT_GRANTED; original P3 HELD, Windows Git L2 NOT_AUTHORIZED, R13 staging HELD; no release, installer, Windows UAT or P2 overwrite.
- Actual installed Windows P2 current state UNKNOWN; inaccessible unpushed PC files UNKNOWN. Do not claim changes there.
- No credentials/user profile/machine changes, no protected main/R13/worktrees, PRISM/real legacy, original TASK-DAY-01, global KEEP/DROP, destructive rollback, task resumption or real learning promotion.
- Original fresh install.ps1 must OFFER separately missing Claude Code, PostgreSQL 17, optional Node.js LTS and optional npm Codex, each separately informed DEFAULT-NO acquisition consent. -WithCodex is not blanket consent. Original maintenance -Update must NEVER silently install missing external packages.
- Eventual owner-selected route: after separately approved source SHA+TREE and trust/incident clearance, separately clean Windows Git fetch/checkout, original update.ps1 preflight then original updater/installer/journal/recovery and full integrated CLI/FastMCP/PostgreSQL V-01..V-42 UAT. Do NOT initiate yet.
- Resolve independent publisher/source SHA-256 trust root; official native Git executable and dependencies, GCM/SSH, Python/native/Tcl/Tk provenance; complete offline transitive SHA-256 hash-locked wheelhouse; NTFS path/reparse/junction/ADS/hardlink/case/ACL/object identity/race/recovery protections; incident closure and individual operator consent.

## Test and historical evidence provenance

Current source 8c722b1: LIVE Git object integrity, exact changed blobs and ancestry VERIFIED. Current Python/AST/compile/pytest/PowerShell/native host/MCP/hooks/DB even SELECT/Windows installer/recovery/full V-01..V-42 UAT NOT_RUN/HELD. All new tests AUTHORED NOT_RUN, no new PASS. Historical 732/732 eligible guarded PASS and 407/407 source compile are ONLY from 9e2b538b, not transferred. Preserve 727/730 three fixture failures, nine deselected child cases, three uncollected psycopg test modules, rejected incomplete-stub 11 FAIL and corrected distinct 11/11 PASS, rejected SessionEnd assertion, prior rejected prerequisite-removal SHA d620c67956b95957196e07c121b0bead19a6e844 and unpublished rejected c56847b8276581ee66a7aae5b512a94a341a5248. Preserve earlier docs draft SyntaxError before write as separate historical event.

## Canonical documentation publication and EXACT NEXT operation

Canonical docs branch docs/chatgpt-continuity-20261023 PRE-publication HEAD c146526f395fdbf397847efa45e0c7a1c41147ed, TREE 26569c2db1a7c50482fbcd76b108654b562fe504, sole parent bf889c11527ddf51d6489a0b8132b82bfc8e48f8. PRE index blob 4a8d659a6365b217c3c381c036c227eb90a6edcc. Publish EXACTLY three docs paths: THIS new handoff, new exact-current-source #185 reviewer request, and PREPEND READ FIRST index; verify actual new docs HEAD/TREE/PARENT/THREE blobs and nonforce expected-SHA lease.

1. New Chat must first LIVE authenticate GitHub and reverify current newest docs/engineering/main/R13 HEAD/TREE/PARENT/blob identities, ancestry, issue statuses and all #185 comments. Read newest complete handoff, review request and index, not pasted SHAs blindly.
2. PRIORITIZE genuinely independent, distinct and attributable #185 read-only THREE-VERDICT assessment of this CURRENT source. Require full issue/comments and D1..D4, threat model ACCEPT/REVISE/REJECT, release design NARROW_DESIGN_ACCEPT/DESIGN_REVISE/STATIC_REJECT, OPERATIONS full PERMITTED/BLOCKED/CONDITIONAL matrix, severity/file-line evidence, explicit PASS/FAIL/NOT_RUN. Author-side fix/review does not grant acceptance.
3. Close BOTH incidents with independent evidence before any PostgreSQL or ordinary native host; resolve toolchain/publisher/wheel/NTFS/recovery and F1 authority gaps.
4. Only after genuinely independent acceptance and separate informed owner consent pursue original Windows clean-checkout Git fetch and ORIGINAL update.ps1/installed P2 recovery route, full integrated original CLI/FastMCP/PostgreSQL V-01..V-42 UAT. No new app.
5. Hard continuity checkpoint at/before 20 assistant replies or conservative half-context risk; publish authorized work with nonforce lease and remote readback, handoff/index and ONE complete inline resume prompt; end session after checkpoint. Never claim background processing or exact context percentage without meter.

**NEXT MILESTONE: independent issue #185 reviewer evidence + both incident closures; no operational clearance in this checkpoint.**
