# W4 R13C — original observed-turn cancellation and terminal validation preservation

**2026-11-19 — GITHUB SOURCE ONLY. NOT_RUN / NOT_APPLIED / NOT RELEASED.**

## One original personal Windows product
Claude Code CLI remains primary; original Chairman, FastMCP, Repository, tasks,
explicit task selection and real session-bound task_resume, sessions/events/results,
history, projects, credentials, data sources, experience learning, original
install.ps1/update.ps1/recovery unchanged. No Tk, second application/store/installer,
enterprise IAM or multitenancy. Preserve V-01..V-42, M0..M8, W0..W3, W4 R1..R13B,
C2B/K0 and October/November roadmaps.

## Source-only correction
- Prospective migration 047 redefines **original 045 staging and cancellation**, not
  a duplicate store or tool. Immutable 023/028/029/032/042-046 remain untouched.
- Host UserPromptSubmit now creates the existing reply turn **before** strict
  observation staging; if turn issuance fails, strict staging is refused.
- 047 records the original observed turn on the same protected observation,
  then requires matching session/task/turn and a still-unchecked reply gate for
  a writer-authorized, single-transaction cancellation.
- SQL now rejects ambiguous "cancel this", matching original Python. Existing
  narrow "cancel this task" remains recognized subject to provenance checks.
- Terminal cancellation supersedes pending validation requests but preserves
  earlier task_state.validation_status including "passed": no implicit rollback
  through protected 028 and no unauthorized GUC invalidation.
- An unbound first prompt remains unassigned; hook emits an explicit warning
  rather than silently crediting it to a subsequently selected/created task.
  A fresh user prompt after explicit binding remains required.
- Synthetic/static regressions authored NOT_RUN. No tests or SQL executed.

## Residuals — NOT SAFE TO RELEASE
**P1 C-3 CURRENT-HOST-TURN FRESHNESS STILL OPEN:** if a later user prompt
and relevant host lifecycle event are not observed, a matching old recorded
turn is not proof of the actual current host turn. The runtime-owned reply_guard
is a consistency fence, NOT an independent trusted/cryptographic host authority.
Independent reviewer must challenge the need for trusted hook-only immediate
cancellation with fail-closed replay behavior.

**P2 first-prompt usability:** safe unbound quarantine avoids cross-task
misattribution but does not automatically persist first prompt as authoritative
task-specific instruction after later task creation.

**P2 release:** release_inputs.py pins 001-041; prospective SQL 042-047 is
unapplied; live migration ledger UNKNOWN. Trigger owner and grants, SQL grammar,
028 interaction, NOWAIT/locking, runtime/writer permissions, historical inputs,
Python AST/compile/pytest, dependency/wheel closure, SHA-256 publisher,
Windows NTFS/ACL/reparse/ADS/hardlinks, installer/recovery and V-01..V-42 UAT
are NOT_RUN/NOT_VERIFIED. Historical 732/732 pytest PASS applies ONLY to old
source 9e2b538b, never R13C.

**ABSOLUTE HOLDS:** LIVE_SCHEMA_048_INCIDENT OPEN (NO PostgreSQL EVEN SELECT);
HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED OPEN (NO ordinary native Claude/installed
FastMCP/hooks); independent F1/Fable positive NOT_GRANTED; P3/Git L2, installed P2,
protected main/R13, real profile/credentials/PRISM/TASK-DAY-01, Windows
installation/update and integrated UAT HELD. No local machine changes inferred.

Next: genuinely distinct attributable read-only #185 review of exact R13C;
then only separately approved corrections/synthetic tests, incident clearance,
and later original Windows git fetch/update.ps1 installation approval.
