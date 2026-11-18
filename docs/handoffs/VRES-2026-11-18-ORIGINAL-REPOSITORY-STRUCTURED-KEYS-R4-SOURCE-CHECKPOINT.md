# Vres-OS — 2026-11-18 original Repository R-4 structured-key source checkpoint

**SOURCE-ONLY AUTHORED / GITHUB REMOTE VERIFIED / PYTHON, AST, COMPILE, PYTEST NOT_RUN / ISSUE #185 POSITIVE INDEPENDENT SECURITY REVIEW ABSENT / ABSOLUTE HOLDS OPEN.**

## Binding owner's one-original-product direction

Build ONE complete, practical, production-quality PERSONAL Windows companion to the ORIGINAL Claude Code CLI (PRIMARY interface) and ORIGINAL FastMCP (integral) for ONE Windows user. Preserve original Chairman, one authoritative Repository, task/session/result/history, exact explicit task selection, real Claude session-bound task_resume/checkpoints, project/credentials/data source owners, experience retrieval/governed learning, and original install.ps1/update.ps1/journal/recovery.

No second GUI/application, prioritizing or changing Tk Desktop, second Chairman, duplicate task/results store, MCP server, installer, enterprise IAM/multitenancy or architecture drift. Preserve original V-01..V-42, M0..M8, W0..W3, W4 R1..R13, C2B/K0 and October 22/30/31 + November 5 roadmaps. Proportional P0/P1/P2/P3 approvals. No installed/profile/credential/external host changes without separately informed approval. Prioritize coherent useful original capability over endless microtests.

## LIVE authenticated repository verification

Authenticated GitHub `vosser24` (account ID 62554356), https://github.com/vosser24/Vres-OS (repository ID 1368577038), GitHub App installation 85535881, source/docs feature-branch push permissions observed.

- New original-owner source branch: `feature/personal-w4-original-repository-structured-keys-r4-20261118`
- New source HEAD: `32c9cd13b4bb54cbe361d6c78ea9c6aa6dcb9a6b`
- New source TREE: `7a545300d144471976b14f607dff9a303339879a`
- SOLE source PARENT: `12e517630ebf5e7038d43e59688c757b2a884ba2`
- Commit: https://github.com/vosser24/Vres-OS/commit/32c9cd13b4bb54cbe361d6c78ea9c6aa6dcb9a6b
- Compared to previous R-3: exactly **1 ahead / 0 behind**, **3 changed paths** only:
  1. `src/vres_os/redaction.py` — Git blob `a59b21a64445ed824fd02a5ef36442c3b62be564` (modified).
  2. `tests/test_repository_persistence_redaction.py` — Git blob `faac9bd9fdb8760493e6aeabba9cc70178e99fae` (modified).
  3. `docs/architecture/VRES-W4-ORIGINAL-REPOSITORY-STRUCTURED-KEYS-R4-2026-11-18.md` — Git blob `bc5151b3cd3d94b0bcc1b617970b9a72f41e4970` (added).
- Remote ref, commit TREE, SOLE PARENT, three Git blobs and direct compare were independently reread after a nonforce `expected_sha=12e517630ebf5e7038d43e59688c757b2a884ba2` feature ref update.
- Product main HEAD `9a8acc5d464b96432a93cb95daa9581412fb07ee`, TREE `659d3fdd6e635dbaecbd5c492ba7279754edaec7`, two parents `6af7bddf246e0f628c3e52add9528742e85189ca` and `8ae041721bf0418f6472ab541b6838fd73fec46a`.
- Engineering vs main **247 ahead / 0 behind**.
- Protected R13 `feature/personal-w4-r13-universal-staging-hold-20261106`, HEAD `bcf62460d68caebfdbd0e838d44c5997992c5fbc`, TREE `9bbc5615fef4a8f785e9ddb0056e9430ffe25d63`, SOLE parent `0badcd34d1eafbce5f815512a489d70cb240eecd`.
- Engineering vs R13 **DIVERGED, 138 ahead / 13 behind**; merge base `982e77f2f4974b4fbca5da91d3e11aeb56e40271`. NO merge, no protected worktree modifications.
- Canonical docs before this checkpoint: branch `docs/chatgpt-continuity-20261023`, HEAD `f347df916ffb8050f2cf2dc173c2ae3b36fbe8a0`, TREE `4c69b8aaaabad2cb57608cad4ccb23552a860ac0`, SOLE PARENT `1b78199afe73d3ea0885254d8274142b6f1fcd05`, index Git blob `6c437290255c2c7eb05993d6e89007b6cefb72e1`. This is the **pre-publication** docs identity; verify new HEAD/TREE/PARENT/blobs following this handoff publication.
- Local installed Windows P2 identity and unpushed Windows files are **UNKNOWN**, never inferred or accessed.

## R-4 material source change and audit scope

The original R-3 Repository-only strict write boundary added whole-string suppression but retained original `_is_secret_key` mapping handling. Static inspection found unprotected structured credential families: a dict entry such as `{"ssh_passphrase": "unpatterned-value"}`, `{"db_credential": "..."}` or `{"signing_key": "..."}` could survive unchanged, as could a credential assignment embedded in a dictionary key even if its associated value was harmless.

R-4 enhances **only the existing strict persistence helper**: high-confidence additional structured sensitive key families are fully value-redacted; a raw/ambiguous credential-containing mapping key causes that nested mapping to become `[REDACTED_UNSAFE_FIELD]`, retaining clean siblings in its parent. This is a deliberate conservative context-loss tradeoff. Original `redact()` and `redact_text()` display semantics, original Repository SQL/schema and ownership, FastMCP/Chairman/CLI, Tk source, installer/updater are unchanged. New synthetic parametrized regression tests and fake-DB original `Repository.record_event` call assertion are AUTHORED **NOT_RUN**. No database was touched.

**Important residual R-2/R-3/R-4 inventory OPEN:** historical persisted data not remediated, arbitrary unknown credential forms not detected, project metadata `ensure_project` and task/session/event metadata envelope writes not audited/remediated, other direct SQL/exception/logging/outbound paths unverified; precise task_resume continuity implications of whole nested-context loss need review. This is NOT an independent security verdict, guaranteed leak prevention across product, or release evidence. The original R-3 source `12e51763` and earlier `c81b0cb` remain in ancestry.

## Actual issue and review state

Live GitHub checked #165–170 and #176: **OPEN**; #174 **CLOSED foundation-only**; #185 **OPEN** (full body plus 8 owner-authored comments read as of verification). https://github.com/vosser24/Vres-OS/issues/185 . No actually distinct, attributable, positive THREE-PART current-source review. An older unsigned same-cloud/Claude advisory and author-side static findings are **NOT** independent acceptance. Findings F-1..F-9 remain subject to source-specific external review.

The next independent reviewer must read entire #185 and all comments, canonical index/handoff and current R-4 diff plus D1–D4/source; give (1) THREAT_MODEL **ACCEPT/REVISE/REJECT**, (2) RELEASE_DESIGN **NARROW_DESIGN_ACCEPT/DESIGN_REVISE/STATIC_REJECT**, (3) OPERATIONS explicit permitted/conditional/blocked matrix with severity findings and evidence. New `docs/reviews/VRES-2026-11-18-ORIGINAL-REPOSITORY-STRUCTURED-KEYS-R4-185-INDEPENDENT-REVIEW-REQUEST.md` is REQUEST ONLY.

## Hard operational holds — UNCHANGED

`LIVE_SCHEMA_048_INCIDENT=OPEN`: **NO PostgreSQL even SELECT, direct or indirect.**
`HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`: **NO ordinary native Claude Code, installed FastMCP host or hooks.**
Independent F1/Fable positive authority **NOT_GRANTED**. P3, Windows Git L2, R13 stage, WPR, real Windows install/update/recovery, P2 overwrite and integrated Windows/full V-01..V-42 UAT HELD. NO real credentials/profile changes, original TASK-DAY-01 mutation, PRISM/real legacy projects, global KEEP/DROP, protected main/R13 merge, destructive rollback or release stage.

Fresh original install.ps1 must DETECT and OFFER missing Claude Code, PostgreSQL 17, optional Node.js LTS and optional npm Codex with INDIVIDUAL informed default-NO package consent. -WithCodex is NOT blanket approval. Maintenance -Update must NEVER silently install packages. Owner's eventual preference, only AFTER independent gates and separate exact owner permission: separate clean Windows Git checkout, independently approved SHA/TREE, original update.ps1 preflight, original install/update/recovery, then original Claude CLI/FastMCP/PostgreSQL and full V-01..V-42 real UAT. DO NOT EXECUTE NOW.

## Test provenance, historical rejected attempts, work ledger

Current `32c9cd13b4bb54cbe361d6c78ea9c6aa6dcb9a6b`: GitHub commit/tree/parent/3 changed blobs and ancestry **VERIFIED**. NO Python interpreter, AST/compile/pytest/test runner or PowerShell executed for R-4; **all current regression tests AUTHORED NOT_RUN**, native Claude/installed FastMCP/hooks/PostgreSQL/Windows installs/recovery/UAT NOT_RUN/HELD. No source ZIP, Windows files, user-profile modifications or DB access. Historical 732/732 guarded PASS and 407/407 compile belong solely to OLD source `9e2b538b`, not current. Retain historical 727/730 (3 fixture FAIL), 9 deselected child tests, 3 psycopg modules not collected, rejected 11 FAIL stub vs corrected 11/11, rejected SessionEnd assertion, rejected prerequisite-removal source `d620c67956b95957196e07c121b0bead19a6e844`, unpublished rejected `c56847b8276581ee66a7aae5b512a94a341a5248`, initial JS draft SyntaxError before write, and older post-publication orchestration call cap. None grants current PASS.

This turn authored and published one narrow GitHub-only source commit with exact parent nonforce expected-SHA lease and independently confirmed remote readback. No local PC, native host, DB, executable or installed user state touched. No asynchronous work claimed. Current independently reviewed/tested source remains **PENDING**.

## Next required milestone / start of next chat

1. Authenticated LIVE GitHub readback of repo/account/App, canonical docs latest HEAD/TREE/PARENT and newest handoff/index/review blobs; R-4 source `32c9cd13b4bb54cbe361d6c78ea9c6aa6dcb9a6b`, TREE `7a545300d144471976b14f607dff9a303339879a`, PARENT `12e517630ebf5e7038d43e59688c757b2a884ba2`, three blobs; compare main/R13/issue states. Do NOT assume SHAs stable.
2. Read FULL newest handoff and index; current #185 body ALL comments; D1–D4, V-01..V-42/M0..M8/W4 R1..R13, original Claude CLI/FastMCP/Chairman/Repository and original install/update.
3. Obtain independent attributable #185 full three-part review of CURRENT R-4, not original-author/self-Claude endorsement. Use exact evidence and preserve adverse findings.
4. Continue priority ORIGINAL R-2/R-3/R-4 write/read/logging inventory **only with authorized source-only review/engineering**; no duplicate architecture. Exact current source Python/AST/pytest remain NOT_RUN pending genuinely trusted isolation and approval.
5. Resolve both incidents independently, source/publisher SHA-256, toolchain/wheelhouse provenance, NTFS and recovery, F1/Fable, then separate exact owner consent before any Windows/DB/native Claude operations. Eventually deliver integrated original first-FULL companion and full real UAT.

**Hard automatic checkpoint rule:** At/before 20 replies or conservative estimated half-context risk, stop new phases, reverify refs, publish authorized GitHub source/docs on correct feature/docs branches with nonforce expected-SHA lease, create dated handoff/prepend index, independently read back HEAD/TREE/PARENT/blobs, include complete inline fresh-chat resume prompt, END session. Do not claim exact context percentage or background task.
