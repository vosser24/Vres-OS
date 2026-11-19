# #185 — R13B ORIGINAL observation task-isolation independent READ-ONLY review request

**2026-11-19. REVIEW REQUEST ONLY, NOT AN INDEPENDENT VERDICT OR PERMISSION TO EXECUTE.**

Repository https://github.com/vosser24/Vres-OS; authenticated vosser24.
NEW candidate exact commit `f3411367f1596ac7b03817da20fb4351a207cc83`,
tree `133db36a16ccacca67954714c5011157bd342f56`, SOLE R13A parent `4197b38d424ac751c91768e354aec3e9e0a5a2ba`;
branch `feature/personal-w4-original-observation-task-isolation-r13b-20261119`. R13A→R13B precisely 1 ahead/0 behind,
FOUR changed paths, remote HEAD/TREE/PARENT/blob readback OBSERVED MATCH:
- `src/vres_os/task_lifecycle.py` blob `a0af1fd0840c2ea9f3f709ea0e1ee4bf3ba8fc58`.
- `src/vres_os/migrations/046_original_observation_rebind_quarantine_r13b.sql` blob `e44db5cb1fb3f5d02a83aec8fef4d26df4e2ac8d`.
- `tests/test_original_observation_task_isolation_r13b.py` blob `c936e21792c1efee487cfc60fe1c33d6f1549fc0`.
- `docs/architecture/VRES-W4-ORIGINAL-OBSERVATION-TASK-ISOLATION-R13B-2026-11-19.md` blob `7454c6552e1a6dffdc09cb1acf937d43c761655a`.

**Read ALL of issue #185 body and NINE owner comments** (at 2026-11-19
snapshot), the current docs handoff/index, original product charter,
V-01..V-42/M0..M8/W4 roadmap, source/migrations 023/028/029/032/042/
043/044/045/046, original Repository, task_lifecycle, session_prompts,
session_lifecycle, db/migrator/database_boundary, validation and release_inputs.
Do not treat previous unsigned incomplete Claude report as positive authority.

## Required exact three independent verdicts

1. **THREAT_MODEL ACCEPT / REVISE / REJECT.** Can 046 correctly prevent
   a raw strict observation staged on A from becoming a B event, including
   concurrent bind, A→B→A, same provider session, replaced session, ended
   session, prior unchecked/historical observations, nullable identity
   refs, hostile model/tool input, same-task stale uncommitted cancel when
   host missed another prompt, and READ ONLY controls? C-3 is OPEN; do
   not claim current-turn proof from task equality alone.
2. **RELEASE_DESIGN NARROW_DESIGN_ACCEPT / DESIGN_REVISE / STATIC_REJECT.**
   Verify SQL 046 CREATE OR REPLACE function signature and owner/grants,
   trigger SECURITY DEFINER/search_path and row locking, 023/029/032/
   042–045 invariants, 028 passed-validation trigger, 044 event writer
   transaction rollback, NOWAIT/deadlock/sibling snapshots, source
   migration pin 041 vs prospective 042–046, source SHA-256/publisher,
   Python/wheels, NTFS/ACL/reparse/ADS/hardlink/recovery. Report minimum
   changes and exact SHA/path/line evidence. Do not silently install/apply.
3. **OPERATIONS PERMITTED / CONDITIONAL / BLOCKED.** Separate GitHub
   read-only and authorized source-only modifications from isolated Python
   AST/compile/pytest requiring new exact informed owner consent;
   PostgreSQL including SELECT, SQL migration, ordinary Claude Code/
   FastMCP/hooks, Windows/PowerShell/Git L2, installed P2, profile and
   credentials, PRISM/legacy/TASK-DAY-01, F1/Fable authority, main/R13
   merge, installer/update/recovery, stage and real integrated UAT BLOCKED.

Severity P0/P1/P2/P3 findings, observed PASS/FAIL/NOT_RUN, minimum
corrections and remaining assumptions required. Distinct attributable
reviewer, not author-side verdict or AI attribution without provenance.

Current author-side source-only GitHub REF/TREE/PARENT/4 blob checks OBSERVED,
JavaScript source-string checks OBSERVED. R13B Python AST/compile/pytest,
SQL/PG, Windows/host/FastMCP/installer/UAT NOT_RUN. Historical 732/732 PASS
only older 9e2b538b. No protected branch merge/Windows/host/PG activity.

**ABSOLUTE HOLDS OPEN:** LIVE_SCHEMA_048_INCIDENT (NO PostgreSQL even SELECT);
HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED (NO native Claude/installed hooks);
independent F1/Fable positive NOT_GRANTED, P3/Git L2/installed P2/main/R13/
credentials/profile/PRISM/legacy/TASK-DAY-01/installation/release all HELD.
Preserve one personal ORIGINAL Claude Code CLI + FastMCP companion.
