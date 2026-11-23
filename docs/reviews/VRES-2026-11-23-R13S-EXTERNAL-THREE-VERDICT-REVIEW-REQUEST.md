# Vres-OS W4 #185 — R13S independent three-verdict REVIEW REQUEST
2026-11-23 | OWNER-SIDE PREPARATION, NOT INDEPENDENT REVIEW OR APPROVAL | READ-ONLY SOURCE | NO PR / CI / HOST / DB / WINDOWS

## 1. Specific immutable target and provenance

Repository: https://github.com/vosser24/Vres-OS
Product source branch: feature/personal-w4-original-published-recovery-local-evidence-r13s-20261123
Commit: 2f731c13bda265f1b99520d83b2d7c15895caf08
Exact tree: 9e4e9bef09df6617aef88ec503d2cd8d83d49d8a
Sole parent R13R: effc61514a4b5916cee39503d60c32feaa5e0301
Immutable one-commit diff: https://github.com/vosser24/Vres-OS/compare/effc61514a4b5916cee39503d60c32feaa5e0301...2f731c13bda265f1b99520d83b2d7c15895caf08

The independently read GitHub diff is ONE commit ahead, ZERO behind, EXACT FOUR paths:
- src/vres_os/install_recovery.py (blob dce5552491b92ec98e29bc6d1ca40ef73cee2553)
- tests/test_original_recoverable_installer_transaction_r13o.py (blob d3f6e2ee31463d662f2fac3f4e4b24c0fe501d9c)
- install.ps1 (blob 255de511320d9e9a5f50f14c5fe4a275d8c58f6f)
- docs/INSTALL-WINDOWS.md (blob 251155d6fb3ea097912459206f76d7393fb55fde)

The source under review is the ORIGINAL ONE-user Windows Claude Code CLI + FastMCP Vres-OS companion, not a new application. Preserve Chairman / Authoritative Repository, task selection / real Claude session-bound task_resume, tasks/sessions/results/history, projects, credentials/data sources, governed learning, the ORIGINAL install.ps1/update.ps1/recovery, V-01..V-42 and the historical M/W roadmaps. NO second Vres installation, alternate GUI/Tk, enterprise IAM, duplicate data store/MCP/installer, or protected changes.

Other live GitHub identities at intake: product main 9a8acc5d464b96432a93cb95daa9581412fb07ee, original protected R13 branch feature/personal-w4-r13-universal-staging-hold-20261106 at bcf62460d68caebfdbd0e838d44c5997992c5fbc. Both unchanged. Canonical docs index checkpoint at 99e81e455e18a66970dcd7e9a54753ce5205c37e, tree 4c3a8fcfee3fdfce02532c8b187938173396edda, single parent 2c7cf75e8b20942cd4d0a0d468d74326881597d8.

## 2. Recorded evidence, limits, absolute holds

The immediately preceding verified project continuity recorded a full 661/661-file source-tree match at R13Q, R13R test-only correction, locally reconstructed exact R13S tree, and five owner-approved ORIGINAL selected offline pytest files executed in disposable Linux/Python 3.13.5 with 82 PASS, 0 FAIL, 0 ERROR in 1.50 seconds, no audit tripwire hits. Provenance is prior scoped test evidence, NOT a new reviewer-run test and NOT whole-repository or native Windows certification. Earlier R13Q 66 PASS/1 FAIL (stale test contract), R13R 67/0, separate three-module synthetic R13Q 16/0. Historical 732 pytest/407 compilation PASS only old commit 9e2b538b.

NOT_RUN: full original suite, actual Windows PowerShell and FileShare.None, real interrupted update or update.ps1 -PreflightOnly, actual install/update/recovery, native Claude CLI/FastMCP/hooks, PostgreSQL even SELECT, migrations, credentials/real user profile, integrated Windows UAT, release qualification. No original October Windows files changed.

LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL EVEN SELECT, direct or indirect. Actual migration ledger UNKNOWN, installed release pinned SQL 001–041, prospective 042–048 NOT_APPLIED, migration-048 numbering unresolved. HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: NO ordinary native Claude Code/FastMCP/hooks or unverified host routes. Independently trusted F1/Fable positive authority NOT_GRANTED. No release, original Windows operation, host unhold, journal deletion, rollback, protected merge or PR. In this repository pull_request CI provisions PostgreSQL and runs tests: do not create even a draft PR. See issue #185: https://github.com/vosser24/Vres-OS/issues/185 . All 14 existing comments at this intake were owner-authored, not external accountable approvals.

Existing owner-reported October installed release: 20261022172833-4d82147b; source commit 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c / tree 205c081277ece483c634e1c801c39595abd4549c; historical read-only staged-source hash matches 194/194. No native or DB/UAT inference.

## 3. Source review: what R13S does, and what it does not do

New Python helpers _read_local_release_manifest, _local_tree_equals, and _local_published_release_evidence (install_recovery.py approximately lines 534–667) parse bounded manifest metadata and compare LOCAL staged-source, installed package, managed-plugin and .ps1 launcher file sets and SHA-256 to the SAME LOCAL manifest. Reject malformed paths, missing files, changed bytes, unexpected ordinary files, links/junctions and nonordinary entries. Updated inspect_finalization_evidence checks previous-release pointer equality and adds those diagnostic flags (approximately lines 670–760). Source-held require_w4_install_recovery_clearance remains first. The current implementation returns journal_removal_approved=False, rollback_approved=False and actions=[] on the actual journal-present diagnostic route; no finalize or repair command was added. Early no-journal/malformed-journal returns have no actions field: reviewers may flag that as API-shape inconsistency; it does not itself authorize any action.

The local manifest is mutable and NOT trusted publisher provenance. The parser syntactically checks git_blob and source_commit/source_tree fields but these checks do NOT independently fetch/compare signed or trusted remote Git objects. The file comparer reads the entire local file before checking size/hash, so the 2 MB manifest bound and per-entry declared 64 MB maximum do not bound real read-size/memory use of every member. Its comparisons are point-in-time, not a Windows transactional NTFS snapshot; .cmd launchers, external wheels/dependency closure, live SQL ledger, Claude profile state, active processes and host provenance are not independently attested. This is an explicit review challenge, not evidence of an exploited defect or a reason to weaken a hold. Also assess Windows path normalization, case aliases/reparse behaviour, large or hostile on-disk trees, immutable evidence capture, TOCTOU and the ordering of multiple independent observations.

Original install.ps1 remains source-held at the top and changes only its pending-journal guidance: preserve journal, refuse recovery/retry/manual deletion. The existing original publication sequence still includes active pointer publication before Claude-profile changes (install-global/statusline/autocompact) and before durable verified_commit_pending_cleanup + journal deletion. Published interruption safety is consequently not established merely by file equality. Review real Windows exclusive FileShare.None lock behavior and original _require_inrun_installer_lock, but do NOT execute on Windows under present holds.

## 4. Independent three-verdict response REQUIRED

A genuinely independent technically qualified reviewer must use their OWN attributable GitHub account, identify role, scope, date and immutable source SHA/tree, and post findings themselves to issue #185. Owner-relayed material, a Claude/Fable unsigned advisory, or an AI post via owner credentials is NOT attributable independent review. Separate trusted F1/Fable and incident clearance must not be inferred merely from a posted review.

### THREAT_MODEL
Choose ACCEPT / REVISE / REJECT, cite exact source paths/lines and attack/failure conditions. Analyze journal/pointer/source/snapshot trust boundaries, previous-release publication ambiguity, hostile local manifest, race/link/Windows NTFS/ACL/file-lock and partial profile mutation, rollback of already-used runtime, DB/host bypasses, and source-held route completeness. Treat unknown state as HOLD. Explicitly identify any P0/P1 fix needed before an operator may be exposed.

### RELEASE_DESIGN
Choose DESIGN_ACCEPT / DESIGN_REVISE / DESIGN_REJECT. Review only the original same-install Windows updater/recovery architecture, offline interpreter/wheel/source identity, pin to SQL 001–041 vs unapplied 042–048, unknown actual live ledger, native Claude/FastMCP version/hook route clearance, transaction durable journal, profile and launcher ownership, and fully safe postpublication operator finalization. Distinguish trusted provenance of bytes from local equality. State minimum evidence, alternative outcomes and whether an integration milestone is feasible without a new app/installer.

### OPERATIONS
Supply separate and specific ALLOW / CONDITIONAL / BLOCKED for (a) read-only GitHub source authoring, (b) narrowly scoped disposable offline tests, (c) real Windows PowerShell/lock tests, (d) native Claude/FastMCP/hooks, (e) any PostgreSQL including SELECT, (f) migration/release/schema work, (g) user profile/credentials, (h) original Windows same-install preflight/update/recovery, and (i) production release/UAT. Based on current evidence, (a) is allowed under owner consent, (b) is conditional on separately approved scope; all (c) through (i) are BLOCKED. A reviewer may disagree with technical reasoning but cannot clear separate owner, schema, host, trust and release gates by assertion.

Reviewer must explicitly list PASS, FAIL, NOT_RUN, UNVERIFIED and unknown-risk provenance; no manufactured full-suite PASS or Windows verification. Provide findings with severity, exact repro reasoning not requiring unsafe host execution, recommended integrated minimal correction, and evidence demanded for eventual clearance.

## 5. Trustworthy postpublication finalization / recovery DECISION PROCEDURE — PROPOSED ONLY

This is a human-reviewed decision framework, NOT an implemented finalizer, recovery instruction, execution permission or local-marker shortcut.

1. Preserve and independently record the entire pending journal, original and target release trees, original snapshotted pointer, managed profile/plugin/launcher bytes, Windows event/process chronology, and trusted external published Git commit/tree/wheel evidence. Do not delete, edit or replay a pending journal. Record chain of custody, time, file identities and whether any runtime could have started.
2. Obtain an independent reviewer-signed threat/release assessment against exact source SHA/tree, resolve BOTH open incidents through accountable separate evidence, and obtain separate owner authorization for each proposed operation. Independent positive F1/Fable authority remains a separate gate. A local pass flag is never an authorization primitive.
3. Establish independent publisher/source/toolchain closure: immutable exact Git source and wheelhash/toolchain/host identity, Python and binary dependency inventory, actual launchers including generated .cmd files, managed plugin marker, native Claude version/hook configuration and real profile changes. Verify Windows-specific file-sharing, process quiescence and original lock/ACL/symlink behavior under separately authorized test conditions. Treat any mismatch/unknown as HELD.
4. Do NOT query or otherwise touch PostgreSQL during LIVE_SCHEMA_048_INCIDENT=OPEN. After an explicitly documented and independently authorized incident path, establish the ACTUAL target/ledger and migration 048 numbering, runtime read/write compatibility and rollback-forward safety; identify whether original SQL 001–041 and any prospective 042–048 have actually applied, rather than assuming NOT_APPLIED from source pin. No automatic migrations.
5. Classify state from independently corroborated prepublication/published/phase evidence: PREPUBLICATION_UNDER_LIVE_ORIGINAL_LOCK, PUBLISHED_PARTIAL_HELD, PUBLISHED_FINALIZATION_HELD, or UNKNOWN_TRANSACTION_HELD. If unable to prove prepublication or identity, classify UNKNOWN. A journal phase or active pointer alone never proves "safe to revert."
6. PREPUBLICATION: even if verified untouched runtime/profile and original in-run FileShare.None provenance, do not use R13O restorative code until independently reviewed and specifically owner-approved. PUBLISHED_PARTIAL: preserve journal and runtime; do not roll back a potentially exposed release. PUBLISHED_FINALIZATION: even all local R13S booleans true are insufficient; require independent trusted release/post-install/profile/schema/host compatibility and operator authorization before designing any one-time journal cleanup. UNKNOWN: preserve evidence, block original launch/update and escalate.
7. Before any eventual approved action, use a written operator checklist specifying exact machine/release IDs, external evidence, backup/restore rehearsal, post-action verification, abort strategy and separate rollback-versus-forward decision. No "cleanup if locally matching", no source constant flip, no automatic journal removal. Record final outcome and re-run approved native Windows UAT only after distinct operational clearance.

Any future action must target the SAME original October installation with ORIGINAL update.ps1, no new Vres instance, and only after fresh separately informed consent.

## 6. Requested next reviewer artifact

Post an independently attributable OWN-ACCOUNT comment in https://github.com/vosser24/Vres-OS/issues/185 referencing this brief and exact R13S commit/tree/parent with all THREE verdicts, specific blocking findings (or explicitly bounded acceptance), immutable evidence references, operating matrix, and outstanding gates. Do not run commands, post PRs, trigger CI, access PostgreSQL/native Claude/Windows, or mutate credentials/profile for this source-only review.

**Document author status:** owner-side review preparation; no independently attributable verdict obtained here. Nothing in this document clears the schema-048 incident, host incident, trusted F1/Fable gate or original Windows upgrade hold.
