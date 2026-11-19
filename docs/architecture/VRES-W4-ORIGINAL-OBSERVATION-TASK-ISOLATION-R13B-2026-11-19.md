# W4 R13B — original observation task-isolation and session rebind quarantine

**2026-11-19. SOURCE ONLY, NOT EXECUTED, NOT APPLIED, NOT RELEASED.**
Dedicated original architecture correction from verified R13A source
`4197b38d424ac751c91768e354aec3e9e0a5a2ba` / tree `45b439d8825e721a65a8074a306c98bc6fe9cd99`.

### Correction
- New prospective migration 046 redefines the existing ORIGINAL 043/044
  `vres.commit_user_inputs` function, not a parallel user-event writer.
  A strict observation is committed only when both observed task ID and
  observed original session ID match the currently locked task and session.
  Unbound, historical and mismatched rows stay uncommitted; no raw
  instruction is silently copied into another task. Original transaction,
  SECURITY DEFINER checks, row locks and existing event/state path remain.
- Original session `task_id` rebind or `ended_at` closure now nulls the
  strict-stage marker on that session's still-uncommitted observations.
  This fences A→B→A reuse; it does not delete raw history or create a store.
  Trigger is SECURITY DEFINER with fixed search_path and PUBLIC revoke;
  real SQL grants, ownership and concurrency remain NOT_VERIFIED.
- Original task_lifecycle Python no longer accepts ambiguous `cancel this`
  as cancel authority, matching 045's narrower SQL. `cancel this task`
  remains classified, subject to the original authoritative SQL checks.
- Added synthetic/static regression tests: **AUTHORED, NOT_RUN**.
  Authoring source-string checks are not Python syntax or SQL parser tests.

### Outstanding blockers
**P1 C-3: same-session, unchanged-task stale cancellation remains unresolved**
when a newer host turn is not observed. Neither task IDs nor the new trigger
establish current-host-turn freshness. No security clearance is claimed.

**P2 028 passed-validation guard:** cancellation's pending reset may be
rejected and the transaction should roll back; no unauthorized override was
introduced. SQL grammar, privileges/owners, trigger lock ordering, 042–046
migration sequence, existing live ledger unknown, legacy observations at
rest, dependency/wheel/NTFS/publisher checks and release pin at 041 remain
review-only/open. No applied schema version inferred from incident name.

**ABSOLUTE HOLDS:** LIVE_SCHEMA_048_INCIDENT OPEN — no PostgreSQL even SELECT.
HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED OPEN — no ordinary native Claude
Code or installed FastMCP/hooks. Independent positive F1/Fable NOT_GRANTED.
Windows Git L2/P3/installed P2, protected main/R13, profile, credentials,
PRISM, real legacy, TASK-DAY-01, install/update/recovery, full UAT HELD.
Python AST/compile/pytest, SQL, host and Windows R13B tests NOT_RUN.
Historical 732/732 pytest PASS applies ONLY old 9e2b538b.

Preserve ONE personal Windows Claude Code CLI companion and ORIGINAL
FastMCP, Chairman, Repository, tasks, sessions, results, projects, history,
credentials, learning and original install.ps1/update.ps1/recovery.
Preserve V-01..V-42, M0..M8, W0..W4 R1..R13A, C2B/K0 and October/November roadmaps.
