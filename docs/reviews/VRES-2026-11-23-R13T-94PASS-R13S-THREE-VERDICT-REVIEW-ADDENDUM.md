# Vres-OS #185 — R13T 94-PASS evidence addendum to the immutable R13S independent review

**23 November 2026 | OWNER-AUTHORED READ-ONLY REPOSITORY EVIDENCE | NOT INDEPENDENT APPROVAL | NO EXECUTION OR RELEASE AUTHORITY**

## The one application, the two exact source candidates

The product remains the ORIGINAL single-user Windows Vres-OS daily-operations companion. The ORIGINAL Claude Code CLI is primary and the ORIGINAL FastMCP server is integral. Preserve Chairman, Authoritative Repository, explicit task selection, real provider-session-bound task_resume, sessions/results/history/checkpoints, projects, credentials/data-source boundaries, governed learning, original install.ps1/update.ps1/recovery, V-01..V-42, M0..M8, W0..W3, W4 R1..R13T, C2B/K0 and all October/November plans. NO second installation, alternate GUI/Tk, duplicate task/result store or MCP, enterprise IAM, or new installer.

**Formal independent three-verdict review baseline, unchanged:**
- R13S commit: 2f731c13bda265f1b99520d83b2d7c15895caf08
- R13S tree: 9e4e9bef09df6617aef88ec503d2cd8d83d49d8a
- Sole parent: effc61514a4b5916cee39503d60c32feaa5e0301
- [Immutable R13S review request](https://github.com/vosser24/Vres-OS/blob/2e44c6fd9341a215bde63caeddbda408a4edc11b/docs/reviews/VRES-2026-11-23-R13S-EXTERNAL-THREE-VERDICT-REVIEW-REQUEST.md).

**Separately disclosed later R13T candidate (NOT covered by a hypothetical R13S acceptance):**
- R13T commit: 7289e8842696a8fd99db64a06af465f375a192b9
- R13T tree: 927e3cdd3c0001256b6a5ff9081b50c1fe60c9d7
- Sole parent R13S: 2f731c13bda265f1b99520d83b2d7c15895caf08
- [Exact one-commit diff](https://github.com/vosser24/Vres-OS/compare/2f731c13bda265f1b99520d83b2d7c15895caf08...7289e8842696a8fd99db64a06af465f375a192b9): 1 ahead, 0 behind; exactly (1) src/vres_os/install_recovery.py, (2) tests/test_original_recoverable_installer_transaction_r13o.py, (3) docs/INSTALL-WINDOWS.md.
- R13T tightens read-only local recovery-file bounds, Windows path alias rejection, traversal and three original generated .cmd launcher checks. No installer/update.ps1, SQL, host-hook, migration-acceptance or operational authorization changed. Local evidence must NOT be treated as trusted publication, DB, host or Windows proof.

## Actual previously executed limited offline evidence — do not relabel as release acceptance

The owner supplied the exact immutable GitHub R13T ZIP. A prior guarded run verified:
- ZIP SHA-256: 5473bbb5772ae57c18a4493bbdb799b7793a30f6b69a48def810a466dbf116b5.
- Reconstructed complete Git tree 927e3cdd3c0001256b6a5ff9081b50c1fe60c9d7 (matches published R13T); 661/661 regular Git blobs, 39 Git directories, no unsafe entries/symlinks; all 661 originals unchanged after pytest.
- Python 3.13.5, pytest 9.0.2 in a disposable Linux sandbox, UID 65534, sanitized user/data/temp environment, read-only source, seccomp-denied sockets/network/process launch, Python audit guard, original PostgreSQL tripwires, and NO live database/host/Windows opt-in.
- Exactly FIVE original owner-approved tests:
  1. tests/test_original_recoverable_installer_transaction_r13o.py
  2. tests/test_install_rollback_proof.py
  3. tests/test_original_install_recovery_consistency_r13n.py
  4. tests/test_install_contract.py
  5. tests/test_session_lifecycle_contract.py
- Result: **94 selected original pytest PASS / 0 FAIL / 0 ERROR, pytest exit 0; zero external forbidden audit attempts; zero unexpected live-app-data fence refusals**.
- Test log SHA-256: 559a946b6db1edba627ecfe19835da74add220d16acc9d5960c9419ec49aab15.
- Rejected runner setup attempt /usr/local/bin/python did not exist (setpriv exit 127 BEFORE Python/pytest); corrected path /opt/pyvenv/bin/python gave the actual PASS result. This was not a pytest failure.

This addendum REUSES earlier recorded evidence; it does not claim tests rerun today. Do not extend the five-file approval. Prior evidence retains build/scope specificity: R13Q original 66 PASS / 1 FAIL; R13R 67 PASS / 0 FAIL; R13S selected 82 PASS / 0 FAIL; separate R13Q harness 16 PASS / 0 FAIL; historical 732 pytest / 407 compilation PASS only old 9e2b538b. Full repository pytest, current compile/AST as a separate run, native Windows/PowerShell, PostgreSQL even SELECT, actual host/Claude CLI/FastMCP/hooks, native UAT, update/recovery/release all NOT_RUN.

[Canonical R13T exact-ZIP/94-PASS provenance and safety handoff](https://github.com/vosser24/Vres-OS/blob/ceb24c01fd4c9c41dabcf69c0c9dc0fe3f396307/docs/handoffs/VRES-2026-11-23-R13T-94-ORIGINAL-OFFLINE-PYTEST-PASS-CONTINUITY-CHECKPOINT.md).

## Independently reverified Git SOURCE-only migration-lineage collision

Compared immutable Git tree entries in src/vres_os/migrations/ for historical E7 G7 commit d930adfa89617067115d9538e9692945230d9630, tree 1c15a8fcb02093c7f16ea67f5295779ad1e0a107, against R13T tree 927e3cdd3c0001256b6a5ff9081b50c1fe60c9d7:
- All 41 versions 001–041 have exactly matching filenames AND Git blob SHA identities.
- **All seven versions 042–048 have divergent filenames AND divergent Git blob identities**. No version missing from these two source trees.
- 042: historical E7 experience_retrieval_policy_v2 (ea813390); R13T latest_observed_user_input_control_precedence (cd44e524).
- 043: historical E7 experience_observed_episode (2fffa1cd); R13T legacy_observation_commit_quarantine (ce964d89).
- 044: historical E7 experience_retrieval_policy_v3 (100aa8f5); R13T original_current_turn_atomic_cancellation (280187cd).
- 045: historical E7 experience_retrieval_policy_v4 (3ad3be6a); R13T original_bound_task_cancellation_r13a (9b1e88f3).
- 046: historical E7 experience_retrieval_policy_v5 (7334de0c); R13T original_observation_rebind_quarantine_r13b (e44db5cb).
- 047: historical E7 source_trust_ledger (0adb743c); R13T original_cancel_observed_turn_and_validation_r13c (5fb54108).
- 048: historical E7 source_effective_trust (3070f3aa); R13T original_task_terminal_hold_r13f (b0784c84).

[Full source-only historical collision packet](https://github.com/vosser24/Vres-OS/blob/985ec17aeef70c0f6136dfe37eea21b3b151e8d4/docs/reviews/VRES-2026-11-23-R13S-E7-042-048-LINEAGE-COLLISION-RECONCILIATION-HELD.md).

This is a **repository source comparison, not a current live PostgreSQL ledger observation**. The historical 2026-10-13 E7 migration incident is recorded, but the CURRENT installed live ledger, database state, permissions and available recovery points remain UNKNOWN. It is unsafe to treat E7 042–048 as R13 042–048, assume a clean 041 target, edit ledger checksums, rename applied migrations, pin a partial cohort, restore or roll back on guesswork.

The original src/vres_os/release_inputs.py at R13T still sets PERSONAL_RELEASE_MAX_MIGRATION=41, explicitly names the required original strict-host 042–047 cohort, and returns VRES_W4_HELD_RELEASE_COHORT when these are not independently accepted. The original update.ps1 refuses even -PreflightOnly before Git; install.ps1 has separate release/runtime/host holds. Original db.py refuses PostgreSQL at the source gate. R13T install_recovery.py never independently authorizes journal deletion or rollback. No source gate is authorized to be flipped.

A candidate forward-additive coexistence design, **ONLY for later independently accountable review**, would retain every actually applied immutable migration/ledger identity, then design a separate uniquely numbered and ordered original task/host control lineage with explicit E7 coexistence, ACL/default grant, object/function and forward/recovery proof from EACH approved target state. Its precise numbering, SQL, acceptance and deployment are UNDECIDED. Do not implement this candidate or touch a live database while the P0 incident remains open.

## What the independently attributable reviewer must deliver to issue #185

Reviewers should use their **own identifiable, independently attributable GitHub account**, independently read the immutable R13S source baseline and this separately labeled R13T delta, and post an OWN-ACCOUNT comment to https://github.com/vosser24/Vres-OS/issues/185 with date, scope, exact commit/tree and evidence links. No owner-relayed unsigned AI/Fable answer qualifies; an own-account review alone also does not lift separate trusted F1/Fable or incident gates.

**THREAT_MODEL — ACCEPT / REVISE / REJECT.**
Analyze R13S and R13T separately for pre/postpublication recovery, journal/pointer and Windows file identity, local manifest trust, bounded hashing/path normalization/reparse/race, launcher and managed profile changes, native Claude turn provenance, task cancellation, host-hook DB route, source interlocks and evidence preservation. Cite exact paths/lines, P0/P1 defects and conditions for any bounded acceptance.

**RELEASE_DESIGN — DESIGN_ACCEPT / DESIGN_REVISE / DESIGN_REJECT.**
Decide whether one original same-install Windows update path is sound after independent resolution of (1) historical E7 vs candidate 042–048 lineage collision, (2) full original strict-host SQL cohort/dependencies/grants, (3) already-exposed release/journal finalization safety, (4) immutable publisher identity and offline Python/wheel/toolchain trust, (5) original native Claude CLI/FastMCP version, hooks and provider-session binding. Distinguish unknown live facts and independently required evidence; no alternate app/installer.

**OPERATIONS — per-operation ALLOW / CONDITIONAL / BLOCKED.**
Give explicit separate decisions for (a) GitHub source/docs authoring, (b) exact isolated offline tests, (c) native Windows safe read-only tests/PowerShell locks, (d) ordinary native Claude CLI/FastMCP/hooks, (e) ANY PostgreSQL including SELECT, (f) schema/migration/release, (g) actual credentials/profile, (h) same-original-install update.ps1 -PreflightOnly/update/recovery, and (i) Windows integrated UAT/production. At current verified scope only owner-approved source/docs work is permitted, narrowly scoped offline tests require exact separate scope and safeguards, and **(c)–(i) remain BLOCKED**. Reviewer conclusions do not themselves supersede incident or owner permissions.

Provide specific actionable defect/fix evidence and an operational dependency ordering, rather than a claim that 94 offline selected tests certify the Windows system. Distinguish PASS, FAIL, NOT_RUN and UNVERIFIED. [Issue #185](https://github.com/vosser24/Vres-OS/issues/185) had 18 comments at intake, all owner-authored; independent positive THREAT_MODEL/RELEASE_DESIGN/OPERATIONS absent.

## Holds and the one future installation target

- LIVE_SCHEMA_048_INCIDENT=OPEN: **NO PostgreSQL even SELECT, direct OR indirect**.
- HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: **NO ordinary native Claude Code/FastMCP/hooks**.
- Independently trusted positive F1/Fable authority **NOT_GRANTED**; independent #185 three-verdict clearance **ABSENT**.
- **NO PR, draft PR or CI**: .github/workflows/ci.yml provisions PostgreSQL on pull_request (and push to main); this document is authored only on a separate unprotected docs branch.
- NO protected main/R13 changes, Windows install/update/preflight/recovery, journal deletion/rollback, real credentials or profile changes, migration manipulation, legacy/PRISM/TASK-DAY-01 action or release.

Product main remains 9a8acc5d464b96432a93cb95daa9581412fb07ee and original protected R13 remains bcf62460d68caebfdbd0e838d44c5997992c5fbc. The owner-reported existing October Windows release remains 20261022172833-4d82147b (installed source 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c, historical 194/194 staged source hash matches). No Windows machine or installed Vres was accessed here.

**Next integrated milestone:** Obtain real, attributable three-verdict #185 review on immutable R13S, with R13T 94-PASS and its changed paths distinctly evaluated. Preserve incidents. Only after separately documented schema/host/trust/release/recovery clearances AND specifically informed owner approval: obtain a clean approved Git checkout on the ACTUAL original Windows machine, verify exact HEAD/TREE, run the ORIGINAL update.ps1 -PreflightOnly, then ORIGINAL update.ps1 into that SAME October installation, then native ORIGINAL Claude Code CLI + FastMCP integrated UAT. Never another installation.

**Evidence-addendum author status: owner-side, source-only; no independent verdict, P0 resolution, Windows action or release authority is asserted.**
