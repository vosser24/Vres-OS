# VRES-OS — 2026-11-18 canonical READ FIRST R-3 strict Repository persistence checkpoint

**STATUS: ORIGINAL CLAUDE CODE CLI / FASTMCP SOURCE-ONLY R-3 PREVENTIVE WRITE BOUNDARY PUBLISHED AND LIVE GITHUB VERIFIED; NEW TESTS AUTHORED / NOT_RUN; #185 FULL INDEPENDENT THREE-PART REVIEW ABSENT; ALL HOST/DB/INSTALL HOLDS REMAIN.**

## Owner's binding original product and scope

ONE complete, useful, production-quality **PERSONAL Windows Vres-OS companion for ONE Windows user**. Original Claude Code CLI is the **PRIMARY interface**. The original FastMCP is integral. Preserve original Chairman, authoritative Repository tasks/sessions/recorded results/history/explicit task selection and real Claude session-bound task_resume/checkpoints; projects, credentials, data sources, experience retrieval and governed learning; original install.ps1/update.ps1/installation/journal/recovery.

DO NOT develop a second GUI, prioritize/change Tk Desktop, introduce a new Chairman, task/result store, MCP runtime, installer, enterprise IAM/multitenancy, parallel app or architecture redesign. Preserve V-01..V-42, M0..M8, W0..W3, W4 R1..R13, C2B/K0 and October 22/30/31 + November 5 original roadmaps. P0/P1/P2/P3 controls must stay proportional; installed/credential/profile/external modifications require separately informed consent. Prioritize integrated actual capability over disconnected prototypes.

## LIVE authenticated GitHub independent readback — 2026-11-18

Repository https://github.com/vosser24/Vres-OS, ID **1368577038**. Authenticated account **vosser24** ID **62554356**. App installation **85535881**, permission to push feature/docs branches available.

**CURRENT SOURCE BRANCH** feature/personal-w4-original-repository-strict-persistence-r3-20261118:
- HEAD **12e517630ebf5e7038d43e59688c757b2a884ba2**
- TREE **96013a895c95e3990f56eaba14e55b51c8b374bc**
- SOLE PARENT **c170a7abe63bf70ed312161858950866c3e69ae0**
- https://github.com/vosser24/Vres-OS/commit/12e517630ebf5e7038d43e59688c757b2a884ba2
- This follows first corrective commit **c170a7abe63bf70ed312161858950866c3e69ae0**, TREE **470ffe1f044a544cdaf68db870cd16f485f9c004**, SOLE PARENT **c81b0cb30846ea05e90fcf2683151097b4e54f72**; first commit https://github.com/vosser24/Vres-OS/commit/c170a7abe63bf70ed312161858950866c3e69ae0 .
- Both separate non-force expected-SHA branch updates succeeded, followed by live independent remote HEAD/TREE/PARENT/blob/diff readback. First direct step exactly 4 paths, second exactly 3. Relative to last checkpoint c81b0cb: **2 ahead / 0 behind**, exactly FOUR cumulative changed paths.
- CURRENT exact 4 Git blob IDs:
  1. src/vres_os/redaction.py — **fd421f9a8ede5541496963c1cd2bb376ba529656**
  2. src/vres_os/repository.py — **4048ce6debb512a479a7a97bdb030ad8fed3393f**
  3. tests/test_repository_persistence_redaction.py — **ddb214ab63adb5d77b74c5f2c08a69178b925460**
  4. docs/architecture/VRES-W4-ORIGINAL-REPOSITORY-STRICT-PERSISTENCE-R3-2026-11-18.md — **b7c974051ce24ae21e51f8520821b812c40362aa**
- Source is **246 ahead / 0 behind main**; compared with protected R13 **DIVERGED 137 ahead / 13 behind**, merge base 982e77f2f4974b4fbca5da91d3e11aeb56e40271. NO merge.
- Previous R1/R2 source base c81b0cb30846ea05e90fcf2683151097b4e54f72 remains verified (TREE 610f7a83c2703b03d2fc6d3571c6cff4695c0c29; parent 8c722b1db8ecca7950c7efd7333d634e65c19e09).
- Product main HEAD **9a8acc5d464b96432a93cb95daa9581412fb07ee**, TREE **659d3fdd6e635dbaecbd5c492ba7279754edaec7**, PARENTS 6af7bddf246e0f628c3e52add9528742e85189ca and 8ae041721bf0418f6472ab541b6838fd73fec46a.
- Protected R13 feature/personal-w4-r13-universal-staging-hold-20261106 HEAD **bcf62460d68caebfdbd0e838d44c5997992c5fbc**, TREE **9bbc5615fef4a8f785e9ddb0056e9430ffe25d63**, PARENT 0badcd34d1eafbce5f815512a489d70cb240eecd.

**CANONICAL DOCS BRANCH BEFORE THIS checkpoint publication:** docs/chatgpt-continuity-20261023 HEAD **1b78199afe73d3ea0885254d8274142b6f1fcd05**, TREE **07486bae537401e065247e6fc8d335c6d5cda8cd**, PARENT **27320c30afcb928ee5d6cf93328d4e7153447e9a**, index blob **0615349f68c2a14c8323d996fb54ae2cbddc9e65**. THIS handoff and index should be published as one new canonical docs commit; inspect its new remote commit/tree/parent/blobs in the publishing result. Do not confuse this pre-publication value with the newest post-commit documentation SHA.

## Exact R-3 new engineering, source-only

Previous unsigned same-cloud-Claude/Fable 5.2 advisory on 8c722b1 had THREAT_MODEL REVISE, RELEASE_DESIGN DESIGN_REVISE, OPERATIONS HOST EXECUTION BLOCKED; source R1/R2 c81b0cb bounded quoted attached tails and suppressed whole unsafe hints only in original workday_overview and task_continuity_preview. That prior fix did NOT protect original Repository writes. Advisory is **not** attributable genuinely independent #185 acceptance.

Observed static source issue: direct original redact() of "password=abc,def" can persist ",def"; "password: correct horse battery" can persist " horse battery". The original Repository calls redact() on task title/objective, state, event JSONB, checkpoint summary/position/action/context, completion summary. This is not adequate as a strict write boundary.

This source milestone adds **redact_for_persistence()** to original redaction.py; it asks canonical sanitize_text() for every original raw string. Any eager replacement count OR residual flag suppresses the **entire tainted string** with value-free [REDACTED_UNSAFE_FIELD], retaining untouched safe strings and siblings inside dict/list/tuple structures. Known secret dict keys remain [REDACTED]. It also conservatively suppresses a **pre-masked canonical assignment followed by any substantive tail**, including credential/authorization families, to avoid re-saving old partial masks such as "password=[REDACTED],def". This may over-redact otherwise harmless compound text. Original redact() and redact_text() display behavior is unchanged.

Original repository.py redirects ALL TEN redact() call sites to strict write helper, including state comparison. Existing SQL, original DB owner, task/session/result model, original FastMCP, Chairman, install/update/Tk sources and schema remain unchanged. No duplicate application, task store, MCP server, UI or runtime. New synthetic tests cover direct/nested cases, previously masked tails, clean field retention, and original Repository begin_task, record_event, update_state and checkpoint through a **fake in-memory connection** — code AUTHORED NOT_RUN, not evidence from any real DB.

**Residual R-2/R-3 remains OPEN outside this narrow preventive boundary:** no guarantee for arbitrary unknown formats, unreviewed write/capture/logging/exception/output paths outside the original Repository, already persisted historical rows or live data. Dangerous already-masked past content can remain in read views. No live DB investigation or mass remediation authorized. Independent review is required for this new source.

## Issue status, release findings and operational hard holds

Live #165, #166, #167, #168, #169, #170 and #176 OPEN. #174 CLOSED for foundation only. #185 OPEN; full original body + all **8 owner-authored comments** read, no genuinely distinct attributable positive three-part reviewer signoff. https://github.com/vosser24/Vres-OS/issues/185 . Do NOT self-issue F1/Fable authority.

Keep P1 F-1..F-3 and P2 F-4..F-8, P3 F-9 under evidence-based independent review:
- F-1: any new unblocking commit changes the exact code reviewed; source-specific tests/approval must match that exact commit.
- F-2: complete independently approved offline wheelhouse/transitive wheel lock/root wheel provenance NOT_VERIFIED.
- F-3: independently owner-held pre-execution source/publisher SHA-256 trust, Python/Git/toolchain trust and kernel/OS isolation NOT_VERIFIED.
- F-4..F-8: native Claude executable/version pin; installer-created profile file recovery; Python DLL/Tk closure; CLAUDE_CONFIG_DIR/reparse; held hook failure/exit handling unresolved.
- F-9: venv isolation, Windows reserved paths, pointer history, Git minimum, L2 and callable original alternate stage routes unresolved. Security severities from unsigned advisory are not independent judgments.

**ABSOLUTE HOLDS:**
- LIVE_SCHEMA_048_INCIDENT = OPEN: **NO PostgreSQL even SELECT**, directly/indirectly, no migrations.
- HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED = OPEN: **NO ordinary native Claude Code, installed FastMCP host, hooks**.
- Independently trusted F1/Fable positive authority NOT_GRANTED. P3 HELD. Windows Git L2 NOT_AUTHORIZED. R13 staging HELD. Windows installation/update/recovery and real FULL original V-01..V-42 UAT HELD.
- Installed Windows P2 state UNKNOWN: do not claim local state or touch it. NO profile/credentials, TASK-DAY-01, PRISM/real legacy, global KEEP/DROP, protected worktrees, destructive rollback or main/R13 merge.
- Do not execute Python source/pytest, PowerShell, source packaging, native host, installer or local release from this handoff without separately validated trust/isolation scope and authorization.

Original fresh install.ps1 must DETECT and OFFER missing Claude Code, PostgreSQL 17, optional Node.js LTS and npm Codex with EACH separate informed **DEFAULT-NO** external package consent. -WithCodex NOT blanket consent. Maintenance -Update MUST NEVER silently acquire packages. Eventual Windows preference only after independent release/incident review and informed separately scoped owner consent: separate clean Windows Git checkout -> independently approved exact source SHA/TREE -> original update.ps1 preflight -> original install/update/journal/recovery -> integrated real Claude CLI/FastMCP/PostgreSQL/V-01..V-42 UAT. DO NOT RUN NOW.

## Precise test and failed-attempt provenance

Current source **12e517630ebf5e7038d43e59688c757b2a884ba2** remote Git commit/ref/TREE/PARENT/changed blobs and ancestry **VERIFIED**. **No Python AST/compile/pytest run**, new regressions AUTHORED NOT_RUN. PowerShell NOT_RUN. Native Claude/FastMCP/hooks NOT_RUN/HELD. PostgreSQL NOT_RUN/PROHIBITED. Windows install/recovery/Tk/full original UAT NOT_RUN/HELD. No ZIP/install artifacts created. Historical 732/732 guarded PASS and 407/407 compile belong only to older **9e2b538b**, NOT current code. Preserve earlier 727/730 (3 fixture FAIL), 9 deselected child cases, 3 psycopg modules not collected, rejected incomplete-stub 11 FAIL and separate corrected 11/11 PASS, rejected SessionEnd assertion, rejected prerequisite-removal d620c67956b95957196e07c121b0bead19a6e844, unpublished rejected c56847b8276581ee66a7aae5b512a94a341a5248, original JS draft SyntaxError before write, older orchestration tool-call cap AFTER successful publication later verified via readback. None of these historical facts is proof of current tests.

This chat authored source on an authorized dedicated unprotected feature branch only, with two safe non-force expected-SHA publications and separate remote readbacks. No local PC commands, Windows files, host hooks, DB, packages or credentials. No unfinished operation claimed to run asynchronously. Current tests **PENDING/NOT_RUN by hold**, not PASS.

## NEXT EXACT OPERATION on a fresh chat

1. Reconnect to LIVE authenticated GitHub, independently verify canonical docs HEAD/TREE/PARENT/blob/index, current new SOURCE HEAD **12e517630ebf5e7038d43e59688c757b2a884ba2**, TREE **96013a895c95e3990f56eaba14e55b51c8b374bc**, PARENT c170a7abe63bf70ed312161858950866c3e69ae0 and four blobs; protected main/R13/installation identity, ancestry, issue statuses.
2. Read THIS FULL HANDOFF, newest index, current #185 review request, **full original #185 body and ALL comments**, D1–D4, V-01..V-42/M0..M8/Nov 5 and source.
3. Obtain a genuinely distinct, attributable **FULL independent** current-source #185 THREAT_MODEL ACCEPT/REVISE/REJECT; RELEASE_DESIGN NARROW_DESIGN_ACCEPT/DESIGN_REVISE/STATIC_REJECT; OPERATIONS explicit permitted/held matrix. The latest source supersedes c81 for purposes of exact current review. No same-author self-review accepted.
4. Audit remaining R-2/R-3 consumers/legacy persisted hint boundaries on an authorized dedicated source branch only; develop evidenced narrow fixes, not more disconnected prototypes. Current source compilation and tests remain NOT_RUN until separately authorized safe isolation.
5. Independently resolve BOTH operational incidents before any PostgreSQL/native Claude/installed FastMCP; obtain source publisher SHA-256, trusted wheelhouse/toolchain, Windows NTFS/recovery and F1/Fable independent gates, then explicit owner Windows consent.
6. Eventually deliver original Git-fetch/approved-SHA original update.ps1/install.ps1, integrated real Windows Claude/FastMCP/PostgreSQL task/session/results, projects, credentials, learning, original V-01..V-42 FIRST-FULL acceptance.

**AUTO-CHECKPOINT RULE:** At/before 20 completed assistant replies since last verified checkpoint, or conservative 50%-context risk, stop new phases; reverify/publish authorized source/docs via exact expected-SHA non-force lease; publish a dated handoff + prepend READ FIRST index; verify remote SHA/TREE/PARENT/blobs; include full fresh-chat resume prompt inline, END this session and recommend starting a new chat. No background work, invented context meter, Windows claims or incident clearance.
