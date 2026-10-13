# Vres-OS — E7 control-database incident and C2A → C2B continuity handoff

**Date:** 2026-10-13 (latest C2A report approximately 14:29, Europe/Athens).  
**Repository:** vosser24/Vres-OS.  
**State:** Canonical durable handoff, documentation only. No release approval or claim that local unfinished code was committed.  
**Read order:** THIS FILE FIRST; then the F1 handoff, the R2 handoff, the D2 handoff, and the original preproduction checklist. Superseded historical "next steps" must not be executed.

The purpose of this document is to preserve all materially relevant decisions, security incidents, evidence, Git identities, and remaining work after the accidental migration of the live control database to schema 048. It explicitly separates protected accepted work from the two unvalidated local worktrees.

## 0. Stop conditions and current status

**CONTROL_DB_INCIDENT=OPEN**  
**CONTROL_DB_LIVE_SCHEMA=048**  
**INSTALLED_CONTROL_RUNTIME_MIGRATION_CEILING=041**  
**POST_INCIDENT_DATABASE_BACKUP=STRUCTURALLY_VERIFIED_AND_RESTORE_REHEARSED**  
**CONTROL_C2A_OFFLINE_CANDIDATE=BUILT_UNVALIDATED_LOCAL_ONLY**  
**CONTROL_C2B_SHADOW_PG18=NOT_RUN**  
**CONTROL_C2C_PROTECTED_VALIDATION=NOT_RUN**  
**F2_CI_PROVISIONING=BLOCKED_UNCOMMITTED_UNSAFE_MIGRATION_FALLBACK**  
**F2_PG16_PARITY=NOT_RUN**  
**F1_R2_D2_ACCEPTANCE=PRESERVED**  
**G8_HOST_INGRESS=OPEN**  
**POSITIVE_PRODUCTION_ISSUANCE=DISABLED**  
**EXACT_HEAD_CI=OPEN**  
**TRUE_SPLIT_ROLE_ACCEPTANCE=OPEN**  
**G7_CHUNK3A_MERGED=NO**  
**E7_RELEASE_READY=NO**

**Absolute stop:** No live control setup, update, bootstrap, selftest, migrations, runtime replacement, F2 driver execution, trust-grant registration, PR or merge. The installed 041 runtime may raise MigrationDrift when it sees DB migration 048. Normal hooks reportedly continue, but do not infer release compatibility from that limited observation.

## 1. Git repository — verified, committed positions

- Product main: **9a8acc5d464b96432a93cb95daa9581412fb07ee**, tree **659d3fdd6e635dbaecbd5c492ba7279754edaec7**.
- E6 branch: **8ae041721bf0418f6472ab541b6838fd73fec46a**, same tree **659d3fdd6e635dbaecbd5c492ba7279754edaec7**. Source of the C2A stable baseline.
- Original E7 control worktree branch: issue-176-e7-benchmark-security, **0b4d5cdd79ec1e14366f9edce06575fbb8429294**, migration ceiling 046. This is not the active runtime.
- G7 product branch issue-176-e7-g7-chunk3: **d930adfa89617067115d9538e9692945230d9630**, tree **1c15a8fcb02093c7f16ea67f5295779ad1e0a107**, parent **e18269e8d18cd58f3dae061de8d3bb01758cd82a**.
- Latest accepted earlier G7 commits: Chunk3A implementation **752d5e9c4cf02735e3ed2582c93080e2748e949f**, D2 **4a929e01839d20c690509fb06092147a1bf41361**, R2 **e18269e8d18cd58f3dae061de8d3bb01758cd82a**, F1 **d930adfa89617067115d9538e9692945230d9630**.
- Canonical documentation branch docs-execution-checklist-20260927; immediate predecessor to this handoff is **dc94cb42330b1d38336d73fdc28ec5db43bdc50a**, tree **f760c62f0efcb70076bf8857f253d60c90e61641**. The commit containing THIS handoff has a later SHA: fetch the live branch HEAD.
- No merged G7 product, no approved PR and no exact-head CI PASS have been established. Always recheck GitHub freshness.

**Key Windows worktrees:**

- Control Vres context: C:\Projects\Vres-Issue-176-E7-20261006.
- G7 accepted product plus LOCAL UNSAFE F2 changes: C:\Projects\Vres-G7-Chunk3-20261012.
- Canonical docs: C:\Projects\Vres-E7-B4B-Docs-20261009.
- Standalone C2A candidate: C:\Projects\Vres-Control-C2A-Compat048-20261013.
- Original E6 baseline: C:\Projects\Vres-Issue-176-E6-20261005.

**Caution:** GitHub cannot see the uncommitted C2A or F2 Windows files. A Git documentation commit does not commit those files, their worktree state, or Git-ignored evidence.

## 2. Live control PostgreSQL incident — never lose this history

On **2026-10-13 12:52:30–12:52:31 +03:00**, an F2 local PostgreSQL 16 smoke harness accidentally called the uncommitted CI driver's migrate_into() in a Python process WITHOUT VRES_ALLOW_TEST_DB=1. Only its intended child-test environment had the test flag. In the actual migration process, db.migrate() fell through to ConfigStore and SecretStore, resolved the normal OS-protected control migrator credential and applied migrations **042–048** to the LIVE control database.

**LIVE forbidden target:** 127.0.0.1:5432, database vres_os, PostgreSQL 18.6, system identifier **7685334034094099024**. The connection used vres_os_migrator. An earlier attempt with a stale package failed MigrationDrift; the later attempt imported the G7 checkout and mutated the control database.

- 042 replaces E5 retrieval checks, 043 adds E1 v2 policy and participation constraint changes, 044–046 extend E5 policy identities, 047 adds the source-trust events ledger, protected functions and triggers, and 048 adds source_effective_trust.
- Migration file checksums in the control database matched the immutable committed files on forensic review.
- activate_boundary may have run and refreshed writer binding/configured_at and grants; exact pre-incident values are unavailable.
- No observed source-trust issuance: source_trust_events has 0 rows in the verified snapshot.
- Runtime and writer cannot execute the protected issuer; migrator owns the objects. The runtime may SELECT the ledger and EXECUTE the read-only effective-trust reader.
- F2 integration cohorts did NOT execute; the F2 driver was NOT validated, committed or published.
- Do NOT manually delete migration records, change checksums, downgrade the schema, restore this post-incident backup over live data or run an older migration-aware runtime against schema 048.
- Normal Vres hooks/MCP/checkpoints reportedly still work because those paths do not invoke migrate(); this is NOT proof that setup/update/bootstrap/selftest are compatible.
- The incident was disclosed and logged. Preserve failures and artifacts without rewriting historical evidence.

## 3. Installed runtime and compatibility risk

Active runtime release: **20261006135316-d311a4f8** under %LOCALAPPDATA%\VresOS\releases. Installed package version 0.2.0a1; source provenance file:///C:/Projects/Vres-Issue-176-E6-20261005; migration ceiling 041.

The C2A offline audit compared the installed RECORD and 139 package files with E6/main: 0 RECORD mismatches; 7 files byte-identical and 132 identical after CRLF/LF normalization; no substantive code differences. All 40 plugin files matched after normalization. Installed-only items are managed wrappers, metadata and venv files.

The source of db.py, bootstrap.py, hooks.py and cli.py is identical between stable main and G7's published feature commit. database_boundary.py differs by exactly **40 additive lines** (one activation call and two G7 source-trust privilege-activation helpers). The old boundary activation cannot adequately revoke privileged 047/048 default grants on a fresh database; shipping seven SQL files without the 40 security lines is NOT an acceptable general compatibility release.

The managed Windows installer/update touches the active release pointer, plugin distribution, launchers, global Claude rules, status line, auto-compaction ownership and user environment. Runtime pointer rollback does not roll back database schema. Do NOT run install.ps1 or update.ps1 now, and do not edit active site-packages in place.

## 4. Post-incident backup and forensic closure

Protected backup directory, NEVER public Git:
C:\Users\User\AppData\Local\VresOS\incident-backups\control-vres_os-20261013-131834

- vres_os.dump: PostgreSQL 18.6 custom-format **7,010,039 bytes**; SHA-256 **658123fc8317b9f26806274785e83178a3d1db5cb2c4b1224f9d43ec3478eeb4**; pg_dump exit 0, pg_restore -l exit 0, 817 TOC entries and 56 TABLE DATA entries.
- globals.sql: **1,080 bytes**, SHA-256 **1c9a3979057bbfdb67ad4f1f2055d9ed5f1647c176842460b8d0537090fc5721**; role metadata without password hashes.
- Directory is access-restricted but backup is NOT encrypted; do not upload the file to GitHub, share it via chat or place it in normal build artifacts.
- Writer binding verified user_event_writer -> vres_os_writer, matches configuration.
- Correct record totals: validation_requests **139** (84 passed, 30 failed, 17 rejected, 4 stale, 4 superseded) and validation_ingestion_attempts **1,080**. Earlier “110”/“962” numbers were approximate planner estimates, NOT actual counts.
- No established pre-incident PostgreSQL backup/PITR; the dump protects the current 048 state only. Shadow restore does NOT recover the original 041 state.

## 5. Isolated PostgreSQL 18 restore rehearsal — host-reported PASS

Workspace: C:\Projects\Vres-E7-Control-Restore-Rehearsal-20261013.  
Rehearsal server: 127.0.0.1:55434, PostgreSQL 18.6, system identifier **7696099898557747104**, data dir under the same rehearsal workspace. It is STOPPED.  
Immutable original restored database: **vres_restore_test**. C2B must NOT write to this original.

Full pg_restore with --single-transaction and --exit-on-error succeeded, preserving owners and ACLs. Exactly 48 migration rows/checksums matched; 56 tables; 872 validated constraints (including 105 FKs); 40 functions, 43 enabled triggers, 50 sequences, 15 SECURITY DEFINER functions with intended search_path. Restored snapshot: tasks 112; task_state 112; task_events **5,996**; validation_requests 139; validation_ingestion_attempts 1,080; sessions 186; checkpoints 912; source_trust_events 0.

Nine relation ACL representations differed (NULL versus explicit owner-only ACL), with equivalent effective privileges. Some sequence counters and live post-dump rows changed from snapshot timing, not proven corruption. Role passwords were intentionally not backed up. No PG18 runtime compatibility test was performed. Rehearsal exit status PASS is host-reported, not a protected Vres validation.

Rehearsal evidence:
C:\Projects\Vres-E7-Control-Restore-Rehearsal-20261013\evidence
Reported SHA-256 for evidence manifest **2d07e3be8544c2fc6014f1baaad35b72feb6e9e8c2e3bed16f6fd4d23cb368a3**; recheck local entry count and hashes.

PUBLIC EXECUTE on 23 non-source-trust functions remains a separate low-confidence security finding; C1 said most were trigger helpers and assert_governance_mutation_allowed(bigint,text) was invoker-context, but did not fully verify all bodies. Do NOT revoke grants casually during recovery.

## 6. Cluster table — immutable boundaries

| Role | Endpoint | Actual system identifier | C2B mutation allowed? |
| --- | --- | --- | --- |
| LIVE control PG18 | 127.0.0.1:5432 | 7685334034094099024 | **NEVER** |
| Historical isolated G7 PG18 | 127.0.0.1:55432 | 7694553000872930884 | **NEVER** |
| Isolated PG16 F2 | 127.0.0.1:55433 | 7696087085403510836 | **NEVER; stopped** |
| PG18 shadow rehearsal | 127.0.0.1:55434 | 7696099898557747104 | ONLY explicitly authorized manifest-bound C2B tests; currently stopped |

Every privileged connection must prove endpoint, exact database, login role, and system identifier in the **same actual process that performs DDL or db.migrate()**. An outer shell check and child-only test flag are insufficient. Never connect to forbidden clusters to test rejection; use fake server/connection objects. Never inherit the operator's normal Vres ConfigStore/SecretStore/DSNs.

## 7. Latest development: C2A 13-file offline candidate — NOT committed

Workspace C:\Projects\Vres-Control-C2A-Compat048-20261013.  
Local branch recovery/c2a-compat048-20261013 (no verified remote).  
Base main SHA 9a8acc5d464b96432a93cb95daa9581412fb07ee, base tree 659d3fdd6e635dbaecbd5c492ba7279754edaec7.  
Host-reported **staged INDEX tree** 0345e7f2818226831066eb3cfd3427da9c78fb81 (NOT a commit!).  
Reported delta: **13 files, +885/-5**:

1. src/vres_os/database_boundary.py: exact G7 +40 addition (resulting Git blob **7b8066fb369f13bf21a4add560c60738e3f769fc**).
2–8. src/vres_os/migrations/042 through 048: all seven blob-identical to G7 d930adf, immutable historical bytes.
9. tests/test_control_compat_048_offline.py — NEW, 17 synthetic contract tests.
10. tests/test_embedding_lifecycle_unit.py — obsolete 041 ceiling corrected.
11. tests/test_session_contamination.py — obsolete 041 ceiling corrected.
12. tests/test_e6_observability_hook.py — obsolete 041 ceiling corrected.
13. tests/test_migration_contract.py — obsolete 042-absence assertion corrected.

No intentional db.py, hooks.py, CLI, MCP, installer, pyproject.toml, managed plugin, F2, G8 or unfinished G7 logic.

**Tests (host-executed, NOT protected):** 17 focused offline PASS; E6-lineage unit suite **1,749 PASS / 3 SKIP** (Windows symlinks); critical ruff E9/F63/F7/F82 PASS; diff check PASS. Migration inventory exactly 001–048 and checksum match. Candidate wheel 146 entries, extracted import smoke registered exactly **52 MCP tools**, no source_trust_grant or source_trust_revoke. G7 product has 54 tools; do not confuse the two.

**Frozen candidate wheel SHA-256:** b0326db9a4b87c5e0a60859a79f1e0d926465408a042d72f92e50663e49a7c52.  
**Second wheel SHA-256:** ded76ba2eb758d0d724458a01328af277f49f879d52b6c5c7ed81347aed0957f.  
Build outputs are not archive-byte reproducible; C2B MUST compare executable members and package metadata before any database work.  
**Candidate patch SHA-256:** 2c1380cb36b79976547be1a323e1cbc49ef20e6da6c04cb259f37be67b393c63.  
**C2A evidence manifest SHA-256:** 94a0a037adcae3a324d923d57064aaf601935105d39e7819a6b35630d02de121.  
Evidence: C:\Projects\Vres-Control-C2A-Compat048-20261013\.vres\c2a-evidence\candidate and C2A-CONTINUITY.md (Git ignored). Preserve all evidence unchanged.

No C2A PostgreSQL integration, C2B shadow execution, independent Fable review, commit, push, live install, or release approval. Candidate is **BUILT_UNVALIDATED**. Its unchanged package version 0.2.0a1 is insufficient for release promotion.

## 8. Separate F2 3-file unsafe work — NOT committed

Worktree C:\Projects\Vres-G7-Chunk3-20261012, accepted feature HEAD d930adf. Host-reported local changes:

- M .github/workflows/ci.yml — F2 CI step and evidence upload, +11/-1.
- ?? scripts/ci_pg_integration.py — NEW, unsafe migrate_into() fallback defect.
- ?? tests/test_ci_pg_integration_driver.py — NEW, 49 pure fake-server tests.

F2 task **TASK-20261013-d286d2be51**, last incident checkpoint **CP-20261013-4b9690a6a9**. No F2 protected validator or product commit. DB-free results: 49 F2 tests PASS; 82 R2 guard tests PASS; full G7 unit suite **3,023 PASS / 4 SKIP**.

Integration module mapping before incident: 86 modules / **1,154 nodes**: general 80 modules / 956 nodes, identity-gated 4 / 180, R2 manifest-bound 2 / 18. No PG16 execution or parity.

PG16 binaries 16.15 from EDB-linked Windows download were used to initialize the separate 55433 cluster, which is now STOPPED. External publisher checksum/signature was not independently established; a local archive hash alone does not prove publisher authenticity.

**DO NOT RUN this driver or its migrate_into() until a separately authorized RED-first process-isolation correction passes.** F2 must not be folded into the C2A compatibility candidate and must not be committed on the accepted G7 product branch as release-ready code.

F2 evidence paths:
- C:\Projects\Vres-Issue-176-E7-20261006\.vres\local-tools\e7-ci-f2-provisioning-evidence-20261013
- C:\Projects\Vres-Issue-176-E7-20261006\.vres\local-tools\e7-ci-f2-pg16-acceptance-evidence-20261013\INCIDENT.md
- C:\Projects\Vres-Issue-176-E7-20261006\.vres\local-tools\e7-control-incident-audit-20261013
- C:\Projects\Vres-Issue-176-E7-20261006\.vres\local-tools\e7-control-backup-20261013

## 9. Accepted D2, R2 and F1 chain — preserve exactly

**D2 / G7 Chunk3A:** product 4a929e01839d20c690509fb06092147a1bf41361. Task TASK-20261012-3201f6f610, protected Fable VAL-b2d40c623c3143bb **PASSED 9/9**. R3 review VAL-86c382ece1b34e02 15/15; implementation VAL-52ec36f2f6624300 17/17. Validator reran source trust 65 PG read tests and focused 106 unit; host ran 83 additional 047/048 integration tests. D2 approval_events baseline was zero: 0->0 means no creation only, not proof of preserving prior nonempty rows. Preserve rejected/failed historical reviews.

**R2 deferred PostgreSQL journeys:** product e18269e8d18cd58f3dae061de8d3bb01758cd82a. Task TASK-20261013-e0f2073d4a. Historical rejected VAL-773140a7956346c8 (ingestion VATT-7a9c06e23a1a45cd: overall passed despite not_run). Later host-persisted VAL-e61c7405f22c42c7 **PASSED 9/9**. Validator reran 82 pure safety tests; host ran 1 user-event-writer and 17 E6 observability PG18 tests, artifact-reviewed but NOT validator-rerun. Four test-only files committed; actual PG16 parity and true split roles remain OPEN.

**F1 deterministic pytest collection:** product d930adfa89617067115d9538e9692945230d9630, only .github/workflows/ci.yml (+7/-2). Task TASK-20261013-1c26893128, VAL-94c5bb86d2fe4a99 host-persisted **PASSED 8/8**. Claimed ninth check in later hand-back was NOT persisted. RED monolithic import mismatch 5 errors; GREEN unit collection 2,978, integration collection 1,154, combined 4,132 nodes across 200 modules. Host full unit 2,974 PASS / 4 SKIP. Actual GitHub CI still NOT green.

Previously accepted sources: D2 handoff PREPRODUCTION-E7-G7-CHUNK3A-D2-ACCEPTANCE-HANDOFF-2026-10-13.md; R2 handoff PREPRODUCTION-E7-DEFERRED-INTEGRATION-R2-ACCEPTANCE-HANDOFF-2026-10-13.md; F1 handoff PREPRODUCTION-E7-CI-F1-COLLECTION-ACCEPTANCE-HANDOFF-2026-10-13.md.

**Policy:** 176.g7.v1 SHA-256 f20b037b00d0a5711666fd6c1d98538101708d99e7f6f32cf5a490ff6b96cf03. R3 interface SHA-256 ce6ef7c40f1263367c1202aa8e795ca41384810e62582899a3fca2adaf208c38. G8 same-user untrusted host ingress OPEN, positive source-trust issuance DISABLED. Do not grant permissions or register new MCP mutation tools.

**Task lifecycle:** D2/R2/F1 protected tasks remain active historically, with accepted evidence in validation_evidence. Do not invalidate accepted PASS just to append a checkpoint; older task_open_list prose can be stale. Always use CURRENT hook-supplied VRES_CURRENT_SESSION_ID in a new provider session.

## 10. Preserve all local work without contaminating accepted branches

**Urgent preservation opportunity on the operator workstation; NOT accomplished by this GitHub docs commit.**

If the user authorizes preservation commits, record their real SHAs/tree/parents rather than inventing IDs:

- C2A: create an explicitly **UNVALIDATED WIP** commit on the existing recovery/c2a-compat048-20261013 branch, exactly the 13 reported paths. Recompute index tree, reviewed patch SHA, migration blob identity, and status. Do not stage Git-ignored evidence or the wheel. If a push is permitted, use a separate clearly named recovery branch with exact remote lease; never force-push or claim validation.
- F2: preserve the three UNSAFE files on a **different quarantine/recovery branch** starting at the accepted d930adf, NEVER directly on issue-176-e7-g7-chunk3. Prefer creating a separate worktree from d930adf, copying the three local files byte-identically, and making a clearly labeled WIP snapshot while leaving the original product worktree untouched. The commit message must say "UNSAFE MIGRATION FALLBACK — DO NOT RUN — F2 NOT VALIDATED". Never force-push, open a PR or merge.
- Check staged inventories, no secrets/DSNs, correct parent/branch and clean diff checks. A local WIP commit is preservation, NOT review acceptance, and must not become a source for live runtime installation.
- Local backups, evidence and credential material CANNOT be made safe for public Git. Preserve them in secure user-owned storage; do not upload any pg_dump, credential or log containing raw DSNs. Verify encrypted off-machine backup separately if required for disaster recovery.

User's current request to "commit all" may authorize bounded preservation snapshots, but **the GitHub connector cannot access these Windows-only uncommitted bytes**. This handoff's remote commit documents them and cannot substitute for their local commits.

## 11. C2B shadow PG18 acceptance — next gated execution plan

The preceding session designed C2B but had not executed it. It is restricted to the retained **55434 rehearsal cluster**, verified system identifier 7696099898557747104, with permission to operate only on NEW, manifest-owned disposable test databases.

1. First verify all C2A frozen hashes, 13-file content, staged tree and ORIGINAL wheel SHA. Compare both wheel archive members; a mismatch in executable .py/.sql bytes is a STOP.
2. Before real SQL, build and run fake-server negative controls proving that missing shadow approval, process test flags, explicit purpose DSNs, isolated VRES_DATA_DIR, actual target database, cluster ID, imported wheel path or manifest cause refusal BEFORE db.migrate() or ANY live connection. Normal live ConfigStore or SecretStore access must fail immediately. Do not forge GitHub Actions runner identity.
3. Start ONLY the rehearsal cluster through its own verified pg_ctl; verify exact data dir, loopback port 55434 and server system identifier. Do not contact ports 5432, 55432 or 55433.
4. Preserve original vres_restore_test. Create NEW restored-copy disposable DB, restore post-incident 048 archive with original owner/ACL, record before/after state, run the actual candidate migration-aware path only with verified synthetic rehearsal credentials and correct migrator purpose. Expected zero missing migrations, no MigrationDrift; measure any provenance_authority/configured_at or ACL writes rather than claim read-only.
5. Independently create NEW fresh disposable DB and genuine admin/runtime/writer/migrator login topology. Apply 001–048 and actual activation. Verify PUBLIC/runtime/writer cannot call protected source-trust issuer/digests or mutate ledger, runtime can read ledger and invoke source_effective_trust, writer retains only intended provenance permissions. Check **the transition window** between migration SQL and activation, not just final ACLs.
6. Check protected snapshot task/validation/session identities and no new positive trust issuance; audit the 23 PUBLIC EXECUTE helpers in catalog, especially assert_governance_mutation_allowed.
7. Every resource must be manifest-bound, cleanly restored/dropped by exact identity, and the original restored database left unchanged. Reconcile before/after inventories; stop ONLY the rehearsal server. Preserve detailed JUnit, SQL catalog, hashes and error evidence.
8. If anything requires changing C2A source, STOP for a separate RED-first code correction. If C2B genuinely passes, report PASSED_UNPROTECTED only. C2C Fable review and any publication/live installation require separate explicit authorization.

NO protected validator under C2B. No Git main/product merge, live runtime update, F2 execution or G8 advancement.

## 12. Broader preproduction obligations not to forget

The governing checklist is docs/PREPRODUCTION-EXECUTION-CHECKLIST-2026-09-27.md. Sequential DONE requires tests, protected review, exact-head CI, guarded merge and post-main verification; planning and quarantined snapshots do not close gates.

Still OPEN:
- Control-runtime 048 compatibility C2B/C2C and guarded versioned shadow-tested publication; the installed 041 runtime must not be silently overwritten.
- F2 unsafe driver correction with RED-first process isolation; PG16 local parity and actual GitHub Actions on exact head; F3 true production split-role coverage.
- S2 SQL alias minor conformance observation; four known Windows symlink skips in G7.
- G8 host-authenticated same-user prompt ingress; positive trust issuance disabled.
- G7 Chunk 4/E5 v6 trust-aware raw evidence with SAME-SNAPSHOT trust/content consistency and byte-identical v2–v5 replay; Chunk 5 legacy source audit; G1 owner-derived downgrade; G2 common lineage proof.
- B4B-v1 historical live adversarial gaps (16 PASS/0 FAIL/1 N/A/3 OWNER_GAP; flood and varied-poison owner evidence blocked); B4B-v2 only a draft.
- Chunk 6 replay, threshold freeze, held-out benchmark only after freeze; final E7 release gate, packaging, protected review, guarded PR and post-main tests; E8/E9, physical acceptance and #169/#170 follow later.
- Neither G7 Chunk3A nor E7 is merged/release ready.

## 13. Local evidence index

- C2A: C:\Projects\Vres-Control-C2A-Compat048-20261013\.vres\c2a-evidence (including candidate wheel, patch, manifest and C2A-CONTINUITY.md).
- Backup: C:\Users\User\AppData\Local\VresOS\incident-backups\control-vres_os-20261013-131834 (NEVER Git).
- Restore: C:\Projects\Vres-E7-Control-Restore-Rehearsal-20261013\evidence (server stopped; do not delete).
- F2 DB-free: C:\Projects\Vres-Issue-176-E7-20261006\.vres\local-tools\e7-ci-f2-provisioning-evidence-20261013.
- F2 incident: C:\Projects\Vres-Issue-176-E7-20261006\.vres\local-tools\e7-ci-f2-pg16-acceptance-evidence-20261013\INCIDENT.md.
- Forensic audit: C:\Projects\Vres-Issue-176-E7-20261006\.vres\local-tools\e7-control-incident-audit-20261013.
- Backup audit: C:\Projects\Vres-Issue-176-E7-20261006\.vres\local-tools\e7-control-backup-20261013.
- R2: C:\Projects\Vres-Issue-176-E7-20261006\.vres\local-tools\e7-deferred-harness-evidence-r2-20261013.
- F1: C:\Projects\Vres-Issue-176-E7-20261006\.vres\local-tools\e7-ci-f1-collection-evidence-20261013.
- PG16 binary/data: C:\Projects\Vres-E7-F2-PG16-Isolated-20261013 (server stopped).

## 14. New-session resume prompt

Resume Vres-OS from the newest canonical handoff:
docs/handoffs/PREPRODUCTION-E7-C2A-C2B-CONTROL-INCIDENT-RESUME-HANDOFF-2026-10-13.md on docs-execution-checklist-20260927.

Read it FIRST, then F1/R2/D2 and the canonical execution checklist. Independently verify main 9a8acc5, G7 product d930adf, docs live HEAD. The LIVE control database is at schema 048 due to an F2 migration fallback incident, while installed runtime supports only 041. The post-incident backup passed an isolated PG18 restore rehearsal; no pre-incident rollback exists. The C2A 13-file offline candidate at C:\Projects\Vres-Control-C2A-Compat048-20261013 is BUILT_UNVALIDATED and not remotely committed; the distinct F2 three-file local driver at C:\Projects\Vres-G7-Chunk3-20261012 is UNSAFE/BLOCKED and uncommitted. Do not conflate these or execute F2.

First verify/preserve local WIP on separate quarantined branches with exact hash/parent/commit identities and no secrets, if approved. Never commit unsafe F2 onto the accepted G7 product branch. Then continue only the narrowly authorized C2B shadow PG18 acceptance at 55434, with process-internal fail-closed connection guards, two disposable databases, exact manifest cleanup, no live control contact, and no protected validator until C2C authorization. Preserve D2/R2/F1 accepted reviews and all historical failures. No live update, G8, PR, merge or release claim.

## 15. Evidence classes and publication meaning

Committed GitHub SHA/tree facts in this document are independently verified repository facts. Windows worktree changes, Vres tasks, host review evidence, cluster state and local SHA-256 files are operator-reported and must be checked on the actual machine. The handoff is a documentation continuity checkpoint only, not a software validation, install approval, control incident closure or a claim that uncommitted files were pushed. Record any real future WIP snapshot SHAs in a NEW append-only pointer rather than rewriting this historical handoff.
