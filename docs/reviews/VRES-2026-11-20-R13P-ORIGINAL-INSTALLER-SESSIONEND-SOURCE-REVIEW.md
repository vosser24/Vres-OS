# Vres-OS W4 R13P — original installer and SessionEnd review corrections

2026-11-20 | OWNER AUTHORIZED SOURCE-ONLY / NO EXECUTION | ALL TESTS NOT_RUN |
EXTERNAL #185 REVIEW BLOCKED | ACTUAL WINDOWS OCTOBER INSTALLATION UNTOUCHED

## Source and owner objective

New dedicated unprotected feature:
`feature/personal-w4-original-installer-review-corrections-r13p-20261120`

Exact R13O source parent:
`f6ea3ff249b74ae65d262db82e5a3550455eabd8`,
TREE `68eccde5457919f12c74a439ea21364fefd27cae`.
R13N ancestor `9c02ee1f57f445ee05461170ced0ced94c9c658c`.
Source Git commit/tree/changed blobs will be verified after publishing.
These are OWNER source changes, not independently approved review findings.

Build ONE original practical PERSONAL Windows companion to the ORIGINAL
Claude Code CLI, original FastMCP, Chairman/Authoritative Repository,
explicit task selection and genuine provider-session-bound task_resume,
sessions/results/history/checkpoints, projects/credentials/data-sources,
experience retrieval/learning and original install/update/recovery.
Preserve V-01..V-42, M0..M8, W0..W3, W4 R1..R13P, C2B/K0 and
October 22/30/31/November 5 roadmaps. No second GUI/Tk app,
enterprise IAM/multitenancy, alternate runtime/installer or P2 overwrite.

## Unsigned Claude R13O read-only advisory disposition

Claude Fable 5.2, unsigned, no verifiable own GitHub account:
THREAT_MODEL=REVISE; RELEASE_DESIGN=DESIGN_REVISE; OPERATIONS: source
authoring with owner consent, isolated tests conditional, DB/host/Windows/
release blocked. Its advice CANNOT lift #185 independently attributable
three-verdict review, trusted F1/Fable positive authority or P0 incidents.

**O-1 P1 / CONFIRMED BY SOURCE: original `Assert-Managed` missing.**
`install.ps1` called `Assert-Managed $PluginTarget` with no definition
in R13O, causing a future held installer to fail after release clearance.
The exact previously present R13N managed-directory ownership/reparse guard
has been restored ahead of the call. A source contract now checks that
called `Assert-*` functions are defined before invocation. PowerShell
never ran; no execution PASS claimed. Preserve the original function,
not a remove-the-check workaround.

**O-2 P1 / CONFIRMED stale regression contracts.** Historical tests in:
- `tests/test_install_contract.py` expected R13M-style direct catch-profile
  restoration, plugin backup reversal and obsolete journal syntax;
- `tests/test_install_preflight.py` expected old inline-journal creation and
  profile snapshots;
- `tests/test_install_rollback_proof.py` expected unconditionally permitted
  legacy published-recovery and deleted PowerShell catch variables;
- `tests/test_personal_w4_full_original_installer_hold_contract.py`
  expected deleted R13M profile restoration flags;
- `tests/test_session_end_worker_cleanup.py` used original worker directly
  without a synthetic transaction-lock seam.

R13P updates these to assert actual current single-policy source behavior
and preserve tested security expectations. The legacy published runtime
rollback expectations are replaced by explicit, non-mutating refusal
assertions; v2 original snapshot integrity checks remain as synthetic
unit contracts. No test is skipped or removed to suppress disagreement.
`tests/test_original_recoverable_installer_transaction_r13o.py` gains a
synthetic lock seam that works on Windows, corrupted snapshot / backup /
redirected journal / altered pointer cases, interrupted partial rollback and
verified retry, and source-only SessionEnd/initialization checks.
All tests AUTHORED/NOT_RUN, not proof of pass or Windows real sharing.

**O-3 / N-2 P2 original SessionEnd alternate-route close.**
`plugins/vres-os/bin/vres-session-end.ps1` no longer inspects the
installed active pointer directly. It calls the ORIGINAL common
`Resolve-VresPython` (with R13O journal+exclusive-install lock refusal)
before starting the detached worker. `src/vres_os/session_end_worker.py`
calls the original `require_w4_native_host_clearance()` before environment,
logs, configuration and DB, and keeps the shared
`hold_install_transaction()` context across the entire authoritative
session-close and credential cleanup. On source hold refusal its `main`
does not log to the installed profile. No native host starts now; original
P0 interlocks are retained; old already-running October processes and
other client bypasses remain unproven. Actual Windows lock timing and
SessionEnd budget are NOT_RUN.

**O-4 / N-3 P2 journal finalization — REVIEW/DIAGNOSTIC ONLY.**
`install_recovery.inspect_finalization_evidence` is an authored read-only
source-held diagnostic. It reports a few individually checked local
conditions (R13O phase/protocol, v2 original snapshot, matching new pointer,
owned plugin, staged manifest file) but ALWAYS:
`journal_removal_approved=False`, `rollback_approved=False`, `actions=[]`.
It cannot verify exact released post-image, current live SQL ledger,
wheel publisher/NTFS trust or native host attestation from a user-writable
journal. No `finalize` command, no deletion, no automatic offline rollback.
Incomplete phase or changed files preserve the journal and hold launches.
This intentionally rejects the unsigned review's proposal that local
file exclusion *alone* proves cross-release rollback safety.

**O-5 P2 residuals.** R13O original in-run prepublication recovery is
still source-held, unexecuted and limited. A crash after active pointer
publication may leave the ONE Vres install held, requiring a future
trusted operator recovery decision. R13O v2 snapshots and local journal
are local evidence, NOT trusted SQL or host origin proof. No Windows
installation claim, SQL compatibility inference or release signoff.

## Tests and gates

Authoring: source/doc/tests only, unprotected R13P branch.
R13D–P Python AST NOT_RUN; compilation NOT_RUN; pytest NOT_RUN;
SQL/PostgreSQL EVEN SELECT NOT_RUN; PowerShell NOT_RUN; Windows
original updater/preflight/install/recovery NOT_RUN; ordinary native
Claude CLI/FastMCP/hooks NOT_RUN; integrated Windows UAT NOT_RUN.
Historical 732/732 pytest and 407/407 compilation only earlier
`9e2b538b`; do not transfer status.

OPEN incidents: `LIVE_SCHEMA_048_INCIDENT=OPEN`, **NO PostgreSQL EVEN
SELECT** direct or indirect; `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`,
**NO ordinary native Claude Code/FastMCP/hooks**. Trusted F1/Fable
positive authority NOT_GRANTED. SQL 001–041 pinned, prospective 042–048
NOT_APPLIED, actual live schema ledger UNKNOWN. Project protected
product main/R13 unchanged, no PR (pull_request CI starts PostgreSQL),
no CI, no merges, no release, no original installer/windows use,
credentials/profile/PRISM/legacy/TASK-DAY-01.

## Review focus and next permitted milestone

Ask Claude for READ-ONLY exact R13P SHA/path/line static analysis, especially
called Assert function closure, original recovery held policy, old test
consistency, native SessionEnd startup budget and lock lifetime, local
finalization diagnostic (verify no hidden journal cleanup), P0 holds and
release pin. Claude's unsigned review is TECHNICAL ADVISORY only, not
three-verdict #185 independently attributable authority. If external
technical review identifies actual defects, fix in ONE integrated milestone
rather than speculative micro-patches. After source review, request
separate informed operator permission for isolated offline fake-root tests
with explicit sandbox trust checks. No Windows operation until verified
independent incident/release/installer compatibility clearances and
target-specific approval. Then original clean SOURCE checkout -> exact
HEAD/TREE -> original `update.ps1 -PreflightOnly` -> original
`update.ps1` into SAME October installation -> CLI/FastMCP UAT.
