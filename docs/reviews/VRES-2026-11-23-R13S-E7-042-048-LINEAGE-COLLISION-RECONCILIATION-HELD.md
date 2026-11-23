# Vres-OS W4 R13S — historical E7 versus original task-control SQL 042–048: immutable source lineage collision

**2026-11-23 | AUTHOR-SIDE GITHUB SOURCE EVIDENCE ONLY | NO DATABASE / HOST / WINDOWS / TEST / APPROVAL | Issue #185 three-verdict independent review pending**

## Exact subject and non-authorization

This is evidence for ONE original PERSONAL Windows Vres-OS companion: original Claude Code CLI primary, original FastMCP integral, Chairman, Authoritative Repository, explicit user task selection, real Claude provider-session-bound task_resume, tasks/sessions/results/history, projects, credentials/data-source handles, governed learning and ORIGINAL install.ps1/update.ps1/recovery. Keep the original October installation as the later SAME-install target. No second application, alternate GUI/Tk, enterprise IAM/multitenancy, new installer, protected branch changes, PR/CI or live activity.

**Current original R13S source**: immutable commit [2f731c13bda265f1b99520d83b2d7c15895caf08](https://github.com/vosser24/Vres-OS/commit/2f731c13bda265f1b99520d83b2d7c15895caf08), TREE \`9e4e9bef09df6617aef88ec503d2cd8d83d49d8a\`, sole R13R parent \`effc61514a4b5916cee39503d60c32feaa5e0301\`. Product source unchanged by this note.

**Historical E7 G7 source lineage**: immutable commit [d930adfa89617067115d9538e9692945230d9630](https://github.com/vosser24/Vres-OS/commit/d930adfa89617067115d9538e9692945230d9630). This Git commit is source evidence, NOT current deployed/installed identity and NOT a live-ledger read.

**Historical incident description, not new observation**: [2026-10-13 control-DB incident handoff](https://github.com/vosser24/Vres-OS/blob/99e81e455e18a66970dcd7e9a54753ce5205c37e/docs/handoffs/PREPRODUCTION-E7-C2A-C2B-CONTROL-INCIDENT-RESUME-HANDOFF-2026-10-13.md) records an accidental 2026-10-13 migration of the then-live control PostgreSQL from 041 to the **E7 G7** migration series 042–048, through a smoke-harness process that lacked the child-only test opt-in and fell through to actual configuration/credential resolution. It also records a post-incident backup and isolated restore rehearsal, but **no established pre-incident 041 backup/PITR**. The [2026-11-04 P3 readiness handoff](https://github.com/vosser24/Vres-OS/blob/99e81e455e18a66970dcd7e9a54753ce5205c37e/docs/handoffs/VRES-2026-11-04-PERSONAL-P3-INCIDENTS-AND-RELEASE-CANDIDATE-READINESS-NO-ACTIVATION.md) carries forward the hold. Historical live state does NOT establish the presently deployed ledger, target, roles, permissions, effective data or any new authorization.

## Immutable migration file evidence from read-only GitHub repository content

Compared files in \`src/vres_os/migrations/\` by immutable Git blob SHAs at the exact two commits:

- **001–041:** all 41 filenames AND all 41 Git blob IDs are identical between E7 G7 and original R13S.
- **042–048:** all SEVEN filenames differ, and all SEVEN Git blob IDs differ. It is a full seven-version lineage collision, not just a shared migration number 048.

| Version | Historical E7 G7 filename (blob abbreviation) | Original R13S prospective filename (blob abbreviation) |
|---|---|---|
| 042 | \`042_experience_retrieval_policy_v2.sql\` (\`ea813390\`) | \`042_latest_observed_user_input_control_precedence.sql\` (\`cd44e524\`) |
| 043 | \`043_experience_observed_episode.sql\` (\`2fffa1cd\`) | \`043_legacy_observation_commit_quarantine.sql\` (\`ce964d89\`) |
| 044 | \`044_experience_retrieval_policy_v3.sql\` (\`100aa8f5\`) | \`044_original_current_turn_atomic_cancellation.sql\` (\`280187cd\`) |
| 045 | \`045_experience_retrieval_policy_v4.sql\` (\`3ad3be6a\`) | \`045_original_bound_task_cancellation_r13a.sql\` (\`9b1e88f3\`) |
| 046 | \`046_experience_retrieval_policy_v5.sql\` (\`7334de0c\`) | \`046_original_observation_rebind_quarantine_r13b.sql\` (\`e44db5cb\`) |
| 047 | \`047_source_trust_ledger.sql\` (\`0adb743c\`) | \`047_original_cancel_observed_turn_and_validation_r13c.sql\` (\`5fb54108\`) |
| 048 | \`048_source_effective_trust.sql\` (\`3070f3aa\`) | \`048_original_task_terminal_hold_r13f.sql\` (\`b0784c84\`) |

GitHub historical E7 048:
[immutable file](https://github.com/vosser24/Vres-OS/blob/d930adfa89617067115d9538e9692945230d9630/src/vres_os/migrations/048_source_effective_trust.sql). It creates/controls \`vres.source_effective_trust(bigint)\`, a SECURITY DEFINER read function for the E7 source-trust ledger and associated privilege sweeps.

GitHub current R13S 048:
[immutable file](https://github.com/vosser24/Vres-OS/blob/2f731c13bda265f1b99520d83b2d7c15895caf08/src/vres_os/migrations/048_original_task_terminal_hold_r13f.sql). Explicitly source-only/NOT_APPLIED; creates \`vres.refuse_unapproved_task_terminal_mutation()\` and a \`vres.tasks\` BEFORE UPDATE/DELETE trigger. A completely different SQL contract.

This is a verified **repository-source divergence**, not a newly executed SQL or runtime finding. All current 042–048 R13S files are prospective/NOT_APPLIED as original R13 engineering, not proof of live state.

## Why the original same-install update cannot simply be unheld

1. [R13S \`release_inputs.py\`](https://github.com/vosser24/Vres-OS/blob/2f731c13bda265f1b99520d83b2d7c15895caf08/src/vres_os/release_inputs.py#L35-L50) still pins **accepted 001–041 only**, and names original strict Claude staging migration dependencies 042–047. [Its validator](https://github.com/vosser24/Vres-OS/blob/2f731c13bda265f1b99520d83b2d7c15895caf08/src/vres_os/release_inputs.py#L134-L151) deliberately fails \`VRES_W4_HELD_RELEASE_COHORT\` while those prerequisites are not accepted. Simply flipping a hold, naming 048 as accepted, or pinning just one middle file would be unsafe.
2. [R13S original \`db.py\`](https://github.com/vosser24/Vres-OS/blob/2f731c13bda265f1b99520d83b2d7c15895caf08/src/vres_os/db.py) \`_check_ledger\` rejects applied ledger rows whose migration names are not present in the package, and rejects checksum drift. **Conditional inference only**: if the historical E7 042–048 rows remain in a target ledger, a package with R13S's names cannot simply treat them as the same versions. We have NOT queried any ledger and do NOT assert the present state of any database.
3. The two 048 SQL files alter DIFFERENT objects. Even if an alternative numbering were assigned, an independently reviewed dependency ordering, existing schema/permission reconciliation and original 042–047 host contract would still be needed. File renaming, old-ledger deletion/checksum rewrite, fake applied state, or direct SQL replay are NOT acceptable fixes.
4. The [original \`update.ps1\`](https://github.com/vosser24/Vres-OS/blob/2f731c13bda265f1b99520d83b2d7c15895caf08/update.ps1) refuses even \`-PreflightOnly\` before Git; [original \`install.ps1\`](https://github.com/vosser24/Vres-OS/blob/2f731c13bda265f1b99520d83b2d7c15895caf08/install.ps1) separately holds the release/interpreter/wheels/native host. [\`db.py\`](https://github.com/vosser24/Vres-OS/blob/2f731c13bda265f1b99520d83b2d7c15895caf08/src/vres_os/db.py#L14-L42) refuses PostgreSQL EVEN SELECT before driver or config; [\`install_recovery.py\`](https://github.com/vosser24/Vres-OS/blob/2f731c13bda265f1b99520d83b2d7c15895caf08/src/vres_os/install_recovery.py#L671-L772) never grants journal deletion or rollback. Source constants are refusal mechanisms, not permission grants.

## Proportionate, independently reviewable compatibility decision matrix (DESIGN ONLY)

| Actual target schema state (NOT CURRENTLY KNOWN) | Meaning | Allowed now |
|---|---|---|
| Verified original 001–041 only | Later strict Claude host calls still require independently reviewed 042–047 successor contracts; no assumption that original source is usable | GitHub source-only study; NO live action |
| Historical E7 042–048 still applied | Must preserve E7 ledger and re-evaluate additive later R13 task controls, trust grants and functional interactions; cannot overlay same-number R13 SQL | GitHub source-only study; NO DB/host/release |
| Mixed, foreign, missing ledger or uncertain state | Cannot infer compatibility or safe rollback | HOLD and preserve evidence |
| Future independently reconciled target | Requires trusted incident resolution, exact migration/ACL/postimage evidence, complete original-host release and recovery review | Only separately approved operations, no automatic clearance |

**Candidate reconciliation direction for an independent release designer, NOT a decision:** preserve all already-applied immutable E7 migration identities; design a correctly ordered future additive/coexistence series for original task/session controls, with unique numbers, explicitly reviewed dependencies and ACL/default-grants, tested from *every* accepted previous state. If source E7 history is not the actual target, design must be revised to real evidence. The current incident record says a known clean pre-incident 041 restore/PITR point is unavailable, so proposing an "easy downgrade to 041" is unsupported. Do not infer that one generic script can safely repair every lineage.

## Reviewer decisions and evidence required BEFORE any live contact

1. **Independent attributable review via own GitHub account on #185**: THREAT_MODEL ACCEPT/REVISE/REJECT; RELEASE_DESIGN DESIGN_ACCEPT/DESIGN_REVISE/DESIGN_REJECT; operation-by-operation OPERATIONS verdict. Include whether E7 trust-object functions and R13 cancellation SQL can coexist safely and how to prove it without privilege regression. A reviewer comment is not incident clearance or trusted F1/Fable authorization by itself.
2. **Schema-048 incident separately closed by accountable evidence** before any database contact. Preserve 2026-10-13 forensic baseline/postincident backup, avoid exposing identities/credentials publicly, establish precise approved target identity and inside-same-process nonincident containment (original failure was an outer-child flag mismatch), obtain explicit owner scope. Do not run even SELECT before clearance. A historical backup/restore report is not new live compatibility proof.
3. **Release cohort, host and security**: design a coherent exact migration/package contract encompassing accepted existing E7 lineage if present; validate protected writer/runtime grants, immutable ledger semantics, task terminal operations, host native Claude/FastMCP hooks, fail-closed staging, real session binding, and original release source/wheel identities. Original 048 cancellation hold may itself require new operator-only cancellation design; do not introduce an alternate store or compiler.
4. **Postpublication original Windows recovery**: preserve journal, exact pre/post snapshot and mutable-profile change evidence; all R13S local integrity pass flags remain NON-authoritative. Independently prove whether release was ever exposed to a process and whether forward-only repair/finalization is justified. No automatic rollback or manual journal deletion. Only AFTER separate release and owner authorization may original same-install update.ps1 -PreflightOnly, original update.ps1 into the existing October install and native CLI/FastMCP UAT be considered.

## Verified versus unknown (do not conflate)

- **VERIFIED STATIC GITHUB:** exact R13S and E7 repository refs, 41 identical 001–041 Git blobs, seven differing 042–048 filenames and blobs, different E7-vs-R13 048 SQL semantics, original source-held validator and DB/Windows/recovery guards.
- **HISTORICALLY REPORTED, NOT RECHECKED:** October 13 actual E7 042–048 live migration incident, postincident backup/restore rehearsal, no established preincident 041 backup, October Windows original installation release \`20261022172833-4d82147b\` and staged 194/194 source hash history.
- **PRIOR SCOPED TESTS ONLY:** R13S five selected ORIGINAL Python modules on synthetic Linux/Python 3.13.5, 82 PASS/0 FAIL; no new test performed for this note.
- **UNKNOWN/NOT_RUN:** actual current live DB target/ledger/roles, E7/R13 coexistence against real PostgreSQL, full R13S test suite, native Windows PowerShell/FileShare.None, original update/preflight/recovery, installed Python/wheel/toolchain, real Claude/FastMCP/hooks, credentials/profile/UAT/production readiness.
- **OPEN:** LIVE_SCHEMA_048_INCIDENT, HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED, #185 independent review, trusted positive F1/Fable authority NOT_GRANTED. No PR including draft, CI PostgreSQL, protected main/R13 merge, installed P2 overwrite, credential/profile mutation or real legacy/PRISM/TASK-DAY-01 action.

**Owner-side evidence report only. Not an independent verdict, release design approval, executable migration plan, PostgreSQL permission, Windows authorization or incident closure.**
