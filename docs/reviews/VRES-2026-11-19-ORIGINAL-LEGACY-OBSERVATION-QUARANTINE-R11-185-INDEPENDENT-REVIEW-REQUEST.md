# 2026-11-19 — CURRENT R-11 original writer legacy quarantine issue #185 independent security review request

**REQUEST ONLY / NOT A REVIEW VERDICT.** No distinct attributable positive reviewer has accepted current R11, cleared BOTH incidents, authorized source execution, migration, Windows, native Claude/FastMCP/hooks, credentials, real user-profile, installed P2, release, F1/Fable or main/R13 merges. Current review evidence is owner-authored source/GitHub verification only.

## Verify exact current R-11 immutable source
Repository https://github.com/vosser24/Vres-OS, authenticated account vosser24 ID 62554356, repo ID 1368577038, app installation 85535881. R11 branch feature/personal-w4-original-legacy-observation-quarantine-r11-20261119; [HEAD 50f109feeedd9e6b943e2895035173bbd48e0735](https://github.com/vosser24/Vres-OS/commit/50f109feeedd9e6b943e2895035173bbd48e0735); TREE 8476677da90d220bf224243332a717273516b521, sole R10 parent 9a40dabaabcd1dc647be0cf8847802925dc18ab7. Exactly SIX changed paths, R10→R11 1 ahead/0 behind, nonforce expected-SHA branch update verified; all six blobs:
1. src/vres_os/session_prompts.py 02829b7fa77c13a63f5d62d7cf2ba771825944da
2. src/vres_os/database_boundary.py 5e785fa306c46aa9a450209c5d2062f1eac71cbc
3. tests/test_original_session_provenance_persistence_r8.py d63b90dad42438d66f9499719022b84a8687491a
4. src/vres_os/migrations/043_legacy_observation_commit_quarantine.sql ce964d89de2252a385adfc2adc6722be7c689980
5. tests/test_original_legacy_observation_quarantine_r11.py 1e72d2db79376160a8c0ad935da74ab05720a3d5
6. docs/architecture/VRES-W4-ORIGINAL-LEGACY-OBSERVATION-COMMIT-QUARANTINE-R11-2026-11-19.md 44db1959e8db12280220463d83bffcef380ea3da
Read original applied migration 023 and 029/032, new SOURCE-ONLY 042 and 043, original session_prompts, database_boundary, task_lifecycle, reply_guard, hooks, session_lifecycle, Repository, CLI/FastMCP/Chairman, issue #185 body/all eight owner comments, full canonical handoff/index/roadmaps, and protected D1-D4/R13 source. Protect main 9a8acc5d and held R13 bcf62460.

## Source questions (path/line/SHA and P0/P1/P2/P3 findings required)
- Analyze migration 023 raw historical obs.text/question/tool ID propagation through task_events, task_state, function return and committed metadata. Does prospective R11 043 fail closed for every unverified/old-code observation without erasing old rows? Is the fixed marker safe, does it preserve legitimate continuity, and what other existing raw-at-rest or alternate event/session/outbound paths remain? No actual leak claimed.
- Assess 043 nullable marker semantics, trust and threat boundary: writer-only version tag NOT a cryptographic sanitizer proof; old staging function still callable, old binaries may stage unverified; original 029 active session FOR UPDATE and 043 same-transaction newest-row selection; concurrent observations/duplicate tool-use IDs, schema upgrade order, default privileges, owner and function EXECUTE, PUBLIC/runtime restrictions, absence/failure behavior and user reassertion.
- Verify original activate_boundary formerly lacked migration 042 grant, and R11's to_regprocedure-conditional writer-only 042/043 GRANT/REVOKE semantics under actual original migrator/writer role separation. Check whether grant is installed when expected, fail-closed on earlier ledgers and SQL migration packaging/update recovery behavior.
- Independently challenge R10 control precedence and unresolved original cancellation atomicity: current actual Claude user turn, host/AskUserQuestion provenance, cross-project/session, replaced session, lost prompt, event versus status two-transaction race, timestamp trust, stale pending, replay and other event writer routes. R11 is **not** a fix for atomicity.
- Review remaining original personal product V-01..V-42, M0..M8, W0..W3, W4 R1..R13, C2B/K0, separate default-NO external prerequisite offers, publisher/source SHA-256, Python/Git/wheels, Windows NTFS/ACL/recovery and no-launch protected R13/main release conditions.

## Mandatory three distinct attributable reviewer verdicts
1. THREAT_MODEL: ACCEPT / REVISE / REJECT. Number P0/P1/P2/P3 findings and give exact SHA/path/line, trust assumption, historical exposure, recommended minimum fixes and residual risk.
2. RELEASE_DESIGN: NARROW_DESIGN_ACCEPT / DESIGN_REVISE / STATIC_REJECT. Distinguish future no-execution source migration design from production acceptance; assess 042/043 ordering, original writer/client code compatibility, historical data treatment, full original install/update/recovery and cancellation atomicity.
3. OPERATIONS: explicit PERMITTED / CONDITIONAL / BLOCKED matrix for GitHub-only reads/source/docs, Python/AST/compile/pytest, Windows Git/checkout/staging/packaging, native Claude/FastMCP/hooks, PostgreSQL **even SELECT**, profiles/credentials/protected installed P2, original install/update/recovery, PRISM/real legacy/TASK-DAY-01, global KEEP/DROP, F1/Fable, R13/main merge, real UAT/rollback.

Reviewer must be GENUINELY DISTINCT AND ATTRIBUTABLE. Include observed PASS/FAIL/NOT_RUN, original rejected attempts, minimum viable safe remediation, independent review limitations, conditions/approvals. Owner-side issue comment, unsigned external Claude REVISE/DESIGN_REVISE, or this request alone is NOT independent acceptance.

## Invariant holds and testing provenance
LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL even SELECT. HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: NO ordinary native Claude Code/installed FastMCP/hooks. F1/Fable positive NOT_GRANTED. P3/Windows Git L2/installed P2/credentials/profiles/real legacy/PRISM/TASK-DAY-01/release/rollback/R13/main held. New 043 and older 042 source only NOT_APPLIED, all current R11 Python AST/compile/pytest NOT_RUN, no SQL, Windows, PowerShell, native host, real UAT. Historical old 9e2b538b 732/732 PASS and 407/407 compile do NOT transfer.
