# Vres-OS — 2026-11-19 ORIGINAL Claude Code CLI/FastMCP R-9 outward + validation provenance source checkpoint

**STATUS: GitHub-only R-9 original-owner source PUBLISHED and remote VERIFIED. Current R-9 tests AUTHORED NOT_RUN; Python/AST/compile/pytest, Windows, PowerShell, native Claude/FastMCP/hooks, PostgreSQL even SELECT, installer and full UAT NOT_RUN / HELD. This is NOT independently approved, executable, installed or released.** Genuine current-R-9 #185 three-part independent verdict is ABSENT. BOTH absolute operational incidents remain OPEN.

## Binding single-user original architecture

Build ONE complete production-quality personal Windows companion for ONE Windows user. Claude Code CLI remains PRIMARY, original FastMCP integral. Retain one original Chairman, authoritative Repository, task/session/result/history owner, explicit task selection, real Claude session-bound task_resume, checkpoints, projects, credential/data-source registry, governed experience/learning and existing original install.ps1/update.ps1/journal/recovery. NO alternate GUI, Tk modification or priority, new app/installer/MCP runtime/Chairman/store, enterprise IAM or multitenancy. Preserve V-01..V-42; M0..M8; W0..W3; W4 R1..R13; C2B/K0; original October 22/30/31 and November 5 roadmaps. Use proportional P0/P1/P2/P3 and prioritize useful integration.

## LIVE authenticated GitHub state verified during this checkpoint

- Repository: https://github.com/vosser24/Vres-OS, ID `1368577038`; authenticated user `vosser24` ID `62554356`, GitHub App installation `85535881`.
- NEW dedicated source branch: `feature/personal-w4-original-provenance-outward-validation-r9-20261119`.
- FINAL R-9 HEAD: **`372f28897fcd9cf8ef012348db90aa9dd471ca84`**. Git TREE **`f4d5f62757f5644a06d16f04a9cf049030365f9f`**; sole PARENT **`f66555ead2ce00f48bdbc44073d813569ab58b88`**. [Final R-9 commit](https://github.com/vosser24/Vres-OS/commit/372f28897fcd9cf8ef012348db90aa9dd471ca84).
- First R-9 source commit `f66555ead2ce00f48bdbc44073d813569ab58b88`; tree `accbcde596113f0018b10424f486528280ae7d67`; parent FINAL R-8 `34374850fe1befdb3533f0c1c659dac9bb56d8d1` tree `7b93cf9186dc1c1f42d2e11fb4965842c9f4063e`. Second R-9 nonforce correction preserved without rewriting history: reject oversized `VAL-...` prose fallback request keys before SQL, not only oversized canonical JSON or explicit request keys.
- R-8 → FINAL R-9: **2 ahead / 0 behind, exactly FIVE paths**, both source commits published with nonforce expected-SHA branch leases; final remote branch/ref, Git commit TREE/PARENT, path comparison and all FIVE final blobs VERIFIED.
- Five final R-9 blobs:
  1. `src/vres_os/session_prompts.py` `5d01d9106dff41958fd5a239fe4f707a70e4432a`
  2. `src/vres_os/hooks.py` `a2af2b70d3ce4dc7fd0417d58067f05998e32429`
  3. `src/vres_os/validation_audit.py` `cb97515c251035f4d8206484d94960c7ebc0644d`
  4. `tests/test_original_provenance_outward_validation_r9.py` `e6083811027d93edeb0432d467c43c028c2fa115` — synthetic, AUTHORED NOT_RUN
  5. `docs/architecture/VRES-W4-ORIGINAL-PROVENANCE-OUTWARD-VALIDATION-R9-2026-11-19.md` `dc5ed68365e6c83fd302ca689172dc7903c3dbd0`.
- FINAL R-8 still `34374850fe1befdb3533f0c1c659dac9bb56d8d1`, whose two commits corrected display-redacted input staging plus one early suppressed-as-control flaw. R-6 original session-bound task_resume atomicity and R-7 reason persistence corrections retained by R-9 ancestry.
- Protected main HEAD `9a8acc5d464b96432a93cb95daa9581412fb07ee`, tree `659d3fdd6e635dbaecbd5c492ba7279754edaec7`, parents `6af7bddf246e0f628c3e52add9528742e85189ca`, `8ae041721bf0418f6472ab541b6838fd73fec46a`.
- Protected R13 branch `feature/personal-w4-r13-universal-staging-hold-20261106` HEAD `bcf62460d68caebfdbd0e838d44c5997992c5fbc`, tree `9bbc5615fef4a8f785e9ddb0056e9430ffe25d63`, sole parent `0badcd34d1eafbce5f815512a489d70cb240eecd`; R-8 was divergent 143 ahead/13 behind, merge base `982e77f2f4974b4fbca5da91d3e11aeb56e40271`. Recompute R-9 comparison fresh on resume; no protected merge, release staging or worktree change.
- Pre-new-checkpoint canonical docs branch `docs/chatgpt-continuity-20261023` HEAD `15bac319122b4a10973acdf03286edf55eb8e3f6`, TREE `2529746971d8239f89ff584d9f131d3fc8628284`, sole parent `d7c5e7f54e85a0627541cd104fab02f315003a64`. New docs HEAD/TREE/PARENT and three blobs must be verified separately AFTER publication, never use this old SHA as final.

## Integrated R-9 authored original source changes

1. Original `session_prompts.pending_user_entries` previously returned historical SQL metadata queue entries raw, including `text`, `question`, unexpected JSON keys and legacy raw text; `committed_user_input_tool_ids` surfaced unchecked old tool IDs; read-only hold reason/timestamp raw. Existing strict `redact_for_persistence` now protects outward mirrored entries, drops structurally tainted maps, refuses unsafe or oversized old tool IDs, protects hold fields. No SQL mutation, no claimed retroactive storage clean.
2. Original `hooks._log_hook_error` wrote exception bodies using display `redact_text` to persistent hook-errors.log, which may leave credential tails; original `validator_stop` emitted display-redacted error to stderr. Both changed to strict `redact_for_persistence` while keeping existing fixed event context and validation refusal semantics.
3. Original direct `validation_audit.record_validation_ingestion_attempt` wrote display-redacted rejection reasons, agent text, raw JSON payload key names and potentially truncated raw session/request identities through SQL into audit/event records. R-9 uses strict persistence redaction on descriptive values, checks authority join identities before DB connection (reject rather than redact/truncate), checks historical SQL-returned keys before reuse and removes early canonical/prose request-key truncation. The same original transaction and tables remain. There is no new schema, runtime or alternative authority.
4. First R-9 author commit forgot the old `extract_request_key` **prose** fallback slice `[:200]`. Second R-9 source commit explicitly removed it and added an overlong prose request-key regression. Preserve BOTH commits and the original rejected/uncorrected intermediate behavior in history; never describe the first commit as final.

## Still unresolved and not independently reviewed

- Migration 023's `vres.commit_user_inputs` inserts **historical raw `obs.text` and `obs.question`** into task_events, and latest user instruction into task_state. R-8 stage-time sanitizer and R-9 outward read safety **do not** retrofit old committed/uncommitted rows. No real DB leak demonstrated; no PostgreSQL queries. SQL migration/change design must be independently reviewed, preserve real provenance and no destructive history changes without separate consent.
- Migration 029 reclassifies inspection-only prompts from stored text; migration 032 latest-observed filters `kind='instruction'`. An intervening read-only/control turn can leave a prior cancellation instruction as latest substantive user instruction. Need genuine same-turn/current-intent proof and host authority review; R-8's corrected suppressed-normal-instruction classification is only partial.
- Possible older validation/task/session/event metadata and legacy staged observations still unsafe, unrecognized credential formats, direct non-Repository writers/loggers/outward CLI/FastMCP/Chairman, historical event readers, provider request-key provenance, transaction concurrency and source import/cycle paths need review. R-9 code/tests are NOT_RUN and no independent security acceptance.
- Publisher/source SHA-256/trust, 001–041 migration pins and any proposed 042+ boundary, original D1–D4, Windows NTFS reparse/ADS/hardlinks/case/ACL/races, Python/Git/wheel dependencies, first-FULL installation/updater/journal/recovery, original 248-file INERT source carrier (not runnable) and real user V-01..V-42 UAT remain OPEN.

## Review issue #185 and connected issues

- [#185](https://github.com/vosser24/Vres-OS/issues/185) LIVE OPEN; issue body and EIGHT owner comments retrieved during this session. Latest comments are requests or author-side source evidence, NOT a genuinely distinct attributable positive THREAT_MODEL/RELEASE_DESIGN/OPERATIONS review of CURRENT R-9. No distinct reviewer assigned. Earlier owner-submitted unsigned external Claude advisory THREAT_MODEL REVISE, RELEASE_DESIGN DESIGN_REVISE; it did not read full issue and is not acceptance. Trusted F1/Fable independent positive authority NOT_GRANTED.
- Updated R-9 full reviewer request in `docs/reviews/VRES-2026-11-19-ORIGINAL-PROVENANCE-OUTWARD-VALIDATION-R9-185-INDEPENDENT-REVIEW-REQUEST.md` must be read along with all issue text/comments and R-2..R-9, migration 023/029/032, original CLI/FastMCP/Chairman/Repository and D1–D4.
- #165–170 OPEN, #176 OPEN, #174 CLOSED for foundation only, #185 OPEN.

## Tests, failed attempts, incident provenance

- R-9 GitHub source commits and exact remote ref/git tree/parent/five blobs: VERIFIED. R-9 synthetic tests: AUTHORED **NOT_RUN**. Python/AST/compile/pytest for exact R-9: **NOT_RUN**; no PowerShell/Windows, native Claude/hooks/FastMCP, PostgreSQL, installer, recovery or full UAT. Do not backdate PASS.
- Historical 732/732 PASS + 407/407 compile apply ONLY OLD `9e2b538b`, NOT R-8 or R-9. Preserve NINE deselected child cases; THREE uncollected psycopg modules; historical 727/730 with three fixture FAIL; initial rejected 11-fail stub, rejected SessionEnd assertion, rejected prerequisite removal `d620c679`, unpublished `c56847b8`, previous JavaScript authoring error and other rejected attempts. Preserve R-8 first-commit suppression-as-control defect (subsequently corrected) and R-9 first-commit prose fallback truncation (subsequently corrected).
- `LIVE_SCHEMA_048_INCIDENT=OPEN` — **NO PostgreSQL even SELECT**, direct or indirect.
- `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` — **NO ordinary native Claude Code, installed FastMCP or hooks**. Independent clearance for each incident absent; F1/Fable positive authority NOT_GRANTED; P3 HELD.
- No local Windows Git L2, Python, test, PowerShell, downloads, real localhost/system calls; no installed protected P2 changes or proof, identity UNKNOWN; no real user-profile/credential changes, PRISM/legacy/TASK-DAY-01, global KEEP/DROP, protected main/R13 merge, destructive rollback, unauthorized source staging/extraction, real UAT, installer update or release. No claiming local unpushed work captured in GitHub.

## Owner's original installation decision, eventually (DO NOT EXECUTE YET)

Owner prefers separate clean Windows `git fetch` checkout at independently approved exact SHA/TREE then original `update.ps1` preflight and `install.ps1 -Update` journal/recovery, with Claude CLI, FastMCP, original PostgreSQL integrated full UAT. Fresh `install.ps1` must detect and OFFER each missing Claude Code, PostgreSQL 17, optional Node.js LTS, optional npm Codex with SEPARATE informed DEFAULT-NO consent for EACH external package. `-WithCodex` is not blanket consent; `-Update` must not silently install external packages. This Windows workflow remains HELD until genuine independent review, BOTH incident clearances, exact trusted source/publisher/toolchain/dependency/NTFS/recovery evidence and new informed owner authorization.

## Exact next operation and checkpoint

1. Reconnect authenticated GitHub. Independently verify latest canonical docs/ref HEAD/TREE/PARENT plus newest handoff/index/review blobs; FINAL R-9 branch HEAD/TREE/PARENT, all FIVE blobs and exact diffs; main/R13 and #165–170/#174/#176/#185 live status. Do not trust this note's SHA without fresh readback.
2. Read newest COMPLETE R-9 handoff, R-9 review request, index, ENTIRE issue #185/comments and original architecture/SQL/source/scope. Obtain an actual distinct attributable **three-part CURRENT R-9 independent security review** with exact lines, severity and operations matrix. Self-review or unsigned advisory is not independent.
3. Prioritize historical staged-row `commit_user_inputs` strict persistence and cancellation freshness across instruction/control/host turn, then broader original validation/hook/CLI/FastMCP/Chairman/direct SQL source review. Author P0/P1/P2/P3 minimal GitHub-only corrections if separately authorized, preserving source/installation authority.
4. Independently resolve BOTH incidents with real separate evidence before any DB/native-host operations, publisher/source/toolchain/wheel/NTFS/recovery gate and new consent before any Windows installation/real UAT.
5. Deliver ONE complete useful original Claude Code CLI + FastMCP companion, not a GUI rewrite.

HARD AUTO-CHECKPOINT at/before 20th completed assistant reply OR conservative >half-context risk, whichever first: stop new phases, verify GitHub, publish authorized completed source/docs nonforce expected-SHA lease, date handoff + READ FIRST index, remotely recheck exact SHA/tree/parent/blobs, give FULL inline fresh-chat resume prompt and links; END chat and recommend fresh chat. Never claim exact context %, Windows changes, undocumented execution, clearance or asynchronous future work.
