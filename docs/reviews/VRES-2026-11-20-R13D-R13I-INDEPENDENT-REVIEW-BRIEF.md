# Vres-OS — R13D–R13I integrated independent security review brief

**2026-11-20 | AUTHOR-SIDE SOURCE PACKAGE ONLY | NOT_RUN | NOT_APPLIED | NOT APPROVED**

This brief is NOT an independent review verdict. A distinct, attributable reviewer must independently verify the actual branch HEAD/tree/parents, exact source/diffs, full issue #185 and its comments; a model's unsigned advisory or owner-relayed posting is not independent approval.

## One original personal Windows product and hybrid target

ONE production-quality PERSONAL Windows companion, one operator. ORIGINAL Claude Code CLI primary and ORIGINAL FastMCP integral. Preserve ORIGINAL Chairman, Authoritative Repository, explicit tasks/selection/session-bound task_resume, sessions/results/history/checkpoints, projects, credentials/data sources, experience retrieval/governed learning, install.ps1/update.ps1/recovery. Preserve ALL original V-01..V-42, M0..M8, W0..W3, W4 R1..R13I, C2B/K0 and October 22/30/31 + November 5 roadmaps. NO parallel GUI/Tk, new installation, duplicate store/Chairman/MCP/installer, or enterprise IAM.

Owner-reported Windows read-only baseline: existing active October release `20261022172833-4d82147b`, source `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c`, tree `205c081277ece483c634e1c801c39595abd4549c`, 194/194 staged SHA-256 matches; NOT runtime/database/UAT proof. The target development loop, only after incidents/review and separate permission: exact trusted source -> verified git fetch in clean Windows SOURCE checkout -> ORIGINAL update.ps1 -> SAME installation -> real original Claude Code CLI + FastMCP UAT -> GitHub fixes. Do not install a second Vres application.

## Exact commit lineage for independent review

Repo: https://github.com/vosser24/Vres-OS, owner vosser24, repository ID 1368577038.

- R13C base `3bd8d8a8fa2bccc87286432657302db34ed13e2b`.
- R13D `39c352aa24153856918f8ce88cdcb4cc79feb2c2`: deny model cancellation BEFORE DB-capable helpers at original MCP and lifecycle. Historical internal SQL cancellation remains dormant.
- R13E `6b71553a1c4f7b2949c22ceb9abeac17dac3f917`: original Claude hook pre-action failure denial and credential suppression; no runtime verification.
- R13F `581a26ee9e29a8864a6f2e174849c2aa5bcf3559`: prospective migration 048 task cancellation/delete/reopen hold and role changes; SQL NOT_APPLIED.
- R13G `673666b88b2aedb4d170d2284197a4926bde5fae`: original task/table/sequence runtime privilege narrowing.
- R13H `08f26e23e044bc866bce442cf1e6ff3d9bbac67d`: revoke blanket runtime/PUBLIC function EXECUTE, restore known original writer/runtime direct calls.
- R13I source branch `feature/personal-w4-original-migration-acl-r13i-20261120`, exact R13H parent. **Reviewer MUST independently resolve/pin current R13I HEAD/TREE/PARENT and three changed blobs; this document is not the authority for SHA identity.** R13I changes ONLY the ORIGINAL `src/vres_os/db.py` migration loop, plus an authored NOT_RUN static test file and this review package.

## R13I specific migration-time correction

PostgreSQL grants PUBLIC EXECUTE on new functions by global default. A per-schema ALTER DEFAULT PRIVILEGES REVOKE cannot remove global defaults (https://www.postgresql.org/docs/current/sql-alterdefaultprivileges.html). PostgreSQL recommends revoking in the same transaction that creates a function (https://www.postgresql.org/docs/current/ddl-priv.html).

For the ORIGINAL split-role `purpose == "migrator"`, R13I calls the EXISTING R13H `_restrict_original_function_execute(conn, cfg.database.user)` immediately after `conn.execute(sql_text)` but before the migration ledger insert, all INSIDE the ORIGINAL `with conn.transaction()` for each unapplied migration. It revokes function EXECUTE from runtime and PUBLIC without creating a second DB route or altering global default privileges. Failure should roll back that migration's SQL and checksum row. Final original `activate_boundary` still re-grants explicit writer, governance and context-refresh/experience functions.

This is source-level intent only, NOT SQL parser/PG transaction execution proof. Existing function exposure before a migration, privileged function ownership, injected per-schema/global grants, inherited effective ACL, PUBLIC/default role memberships, CREATE OR REPLACE privilege inheritance, concurrently operating clients, single-role/test fallback, error recovery across multiple committed migration files, and SQL text containing transaction control must be reviewed. R13I does not create a secure deployment or clear incidents. Historical migrations 001–048 untouched; 042–048 remain NOT_APPLIED; 001–041 release pin unchanged.

## Independent reviewer — three mandatory attributable verdicts

1. **THREAT_MODEL — ACCEPT / REVISE / REJECT.** Assess trusted OS/toolchain vs same-user/admin threats, GitHub compromise, publisher/wheel/source trust, exact Git hashes vs authorization, human-origin non-attestation, credential suppression, path/NTFS trust and legitimate personal scope.
2. **RELEASE_DESIGN — NARROW_DESIGN_ACCEPT / DESIGN_REVISE / STATIC_REJECT.** Check exact R13D-I diff and original modules: `mcp_entrypoint.py`, `task_lifecycle.py`, `hooks.py`, hooks.json/PowerShell, `database_boundary.py`, `db.py`, `release_inputs.py`, original `install.ps1`/`update.ps1`, SQL 018/023/028/030/036/040/041 and held 042–048. Verify run-time function calls/SQL owner privileges, trigger invoker semantics, PostgreSQL ACL object ownership, role default-inheritance, migration transaction/sealing/order and crash recovery, compiler/pytest test provenance, source+wheel integrity and schema migration/release compatibility. The prospective migration **048** is not clearance of LIVE_SCHEMA_048_INCIDENT.
3. **OPERATIONS — PERMITTED / CONDITIONAL / BLOCKED.** Decide *separately* source authoring, isolated offline AST/compile/pytest, PostgreSQL even SELECT, native Claude Code/FastMCP/hooks, read-only Windows Git, original update.ps1 preflight, exact installation and real Windows UAT. Each needs independent evidence and owner authorization; do not infer automatic escalation.

Reviewer must provide independently verifiable real GitHub identity, exact commit/path/line evidence, P0/P1/P2/P3 severity, residual risk, corrections, and PASS/FAIL/NOT_RUN provenance; independently publish full verdict on https://github.com/vosser24/Vres-OS/issues/185. This author-side document is not a reviewer or signoff.

## Unchanged operational holds / test provenance

`LIVE_SCHEMA_048_INCIDENT=OPEN` — NO PostgreSQL EVEN SELECT (including catalog, migration preflight, grants, test DB), direct or indirect. Current live DB ledger and actual grants UNKNOWN.
`HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` — NO ordinary native Claude Code/installed FastMCP/hooks or untrusted host process route. Independently trusted F1/Fable positive authority NOT_GRANTED. #185 remains OPEN with only owner-side comments at last verification; unsigned Claude Fable advisory reports THREAT_MODEL REVISE, RELEASE_DESIGN DESIGN_REVISE, OPERATIONS BLOCKED, NOT independent approval.

Migrations 042–048 NOT_APPLIED, release pin 001–041. Protected product main/R13, installed P2, Windows user profile/credentials, PRISM/real legacy, TASK-DAY-01, release and rollback HELD. #165–170/#176 OPEN; #174 foundation only. R13D–I Python AST NOT_RUN, compile NOT_RUN, pytest NOT_RUN, SQL parse/execution NOT_RUN, PostgreSQL NOT_RUN, native Claude/FastMCP/hooks NOT_RUN, Windows update/preflight NOT_RUN and actual V-01..V-42 UAT NOT_RUN. Old 732/732 pytest and 407/407 compilation apply ONLY to older `9e2b538b`. GitHub commit/tree/blob/diff readback VERIFIED only.

## Next actual operation (not async)

Verify R13I exact HEAD/TREE/parent and source blobs, deliver package to a genuinely separate attributable reviewer. Resolve P0 incidents with evidence but no forbidden DB/host access, then seek separate specific approvals for isolated offline tests and original source/release/Windows update. Only then use git fetch and original update.ps1 to update the SAME October Vres-OS installation and run real original Claude CLI + FastMCP integration. No manual patch files, no second installation, no release bypass.
