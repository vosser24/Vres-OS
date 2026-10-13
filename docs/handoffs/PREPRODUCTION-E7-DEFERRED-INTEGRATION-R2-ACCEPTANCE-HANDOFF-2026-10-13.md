# Vres-OS — E7 deferred PostgreSQL integration R2 acceptance durable handoff (2026-10-13)

This handoff records the accepted, committed and pushed test-only R2 hardening of the two deferred E7/G7 PostgreSQL integration journeys (user-event-writer and E6 observability). It is additive: it does not edit earlier handoff conclusions, the accepted R3 contract, the D2 acceptance, or any production behavior. Read it AFTER `PREPRODUCTION-E7-G7-CHUNK3A-D2-ACCEPTANCE-HANDOFF-2026-10-13.md`, which it extends (that handoff lists these two journeys as an open merge-blocking obligation; this handoff records the local isolated evidence for them, which does NOT close the broader merge gates, see section I).

## 0. Status block

```
DEFERRED_INTEGRATION_HARNESS=VALIDATED_COMMITTED_AND_PUSHED
USER_EVENT_WRITER_JOURNEY=PASSED_ISOLATED
E6_OBSERVABILITY_JOURNEY=PASSED_ISOLATED
RESOURCE_CLEANUP=VERIFIED
REJECTED_VALIDATION_HISTORY=PRESERVED
G7_CHUNK3A_D2=ACCEPTED_AND_PRESERVED
G7_CHUNK3A_MERGED=NO
G8_HOST_INGRESS=OPEN
POSITIVE_PRODUCTION_ISSUANCE=DISABLED
PG16_CI_PARITY=OPEN
TRUE_SPLIT_ROLE_ACCEPTANCE=OPEN
E7_RELEASE_READY=NO
NEXT=RESUME_FROM_R2_CANONICAL_HANDOFF
```

"Passed isolated" means: passed on a disposable, single-admin-role PostgreSQL 18.6 cluster on the operator workstation. It is not PG16 CI, not a split-role production deployment, not exact-head CI and not release readiness.

## A. Product checkpoint

**Product feature branch `issue-176-e7-g7-chunk3`** (`vosser24/Vres-OS`; NOT merged; NO PR):
- HEAD: **e18269e8d18cd58f3dae061de8d3bb01758cd82a**
- Tree: **0456965510a984c248318a3f40598a5c86709923**
- Parent: **4a929e01839d20c690509fb06092147a1bf41361** (D2 test commit; tree e1407b8068fbd9eca84b0c4be120ba10a2a1b82f).
- Subject: `test(e7): harden deferred PostgreSQL integration journeys`.
- Delta vs parent: exactly FOUR test files, **+1397 / -85**:
  - new `tests/integration/pg_run_guard.py` (+543)
  - new `tests/integration/test_pg_run_guard.py` (+780)
  - modified `tests/integration/test_e6_observability_schema.py` (80 lines changed)
  - modified `tests/integration/test_user_event_writer_boundary_journey.py` (79 lines changed)
  Production source, migrations, frozen policy, CI workflow, `conftest.py` and docs are not in the diff.
- The commit was created locally by the Chairman. The automated push was DENIED by the host permission classifier ("Out-of-Place Publication") and was not retried through another route; the user then performed the normal fast-forward push manually. Remote HEAD, tree, parent and the four-file name-status (A/M/A/M) were independently retrieved from the remote before this handoff was written.
- Frozen content identities. Raw working-tree SHA-256 (the two new files carry CRLF in the working tree; the two modified files are LF):
  - pg_run_guard.py `adb6607f6f25666bbbbfb4b6ee29347ed936d8f20d3ccc591f19aa9b5e9f3081`
  - test_pg_run_guard.py `a41cc71c7c2a26010138fc4e8d7bdcc852fddee88128baefd4ae567f9de8b5e3`
  - test_e6_observability_schema.py `9f5a4c9e5a3a3971b23486453f335f87d1c6c8fb3e031e8f5459803afe5bb154`
  - test_user_event_writer_boundary_journey.py `dbac3e3541328f29fd43f01e512452ff59646e0e8ee7994c96f03c7c77bba5d1`
  - Committed (LF-normalized) blob content hashes: pg_run_guard.py `5b77543ff9f16f03c27692c2d492ddca90a60c444e64d90a2e2fd85cab39a9f4`; test_pg_run_guard.py `24ffa4fcf0a5da94d2fa92ff1be21d04f3276f57e53fa82add4e8b9ca0991282`; the two modified files are byte-identical raw and normalized. Do not confuse the CRLF working hashes with the LF blob hashes.
- Other positions (unchanged): product main 9a8acc5d464b96432a93cb95daa9581412fb07ee; original E7 security branch `issue-176-e7-benchmark-security` 0b4d5cdd79ec1e14366f9edce06575fbb8429294; G7 chain Chunk 1 03a9897 -> 1A 99c7300 -> Chunk 2 ac45967 -> Chunk 3A 752d5e9 -> D2 4a929e0 -> **R2 test commit e18269e**.
- Worktrees: product `C:\Projects\Vres-G7-Chunk3-20261012`; control/Vres context and ignored evidence `C:\Projects\Vres-Issue-176-E7-20261006`; docs `C:\Projects\Vres-E7-B4B-Docs-20261009` (local branch docs-e7-b4b-v2-20261009; publish with `HEAD:docs-execution-checklist-20260927`).

## B. Documentation checkpoint

Canonical documentation branch `docs-execution-checklist-20260927`. Predecessor of this handoff commit: **f34a06f684a61715578a79d4844b69ede4c4c226** (tree 9634d359b8f5cafa7e808d0c0116e905a69fbf5b). The new HEAD must be retrieved from the branch; do not expect f34a06f. This commit adds this file and appends one superseding pointer each to `PREPRODUCTION-RESUME-HANDOFF-2026-09-27.md` and `PREPRODUCTION-E7-G7-CHUNK3A-D2-ACCEPTANCE-HANDOFF-2026-10-13.md` (append-only).

## C. Validation history

- Dedicated task: **TASK-20261013-e0f2073d4a**, status active (not completed, not recreated). Chunk 3A task `TASK-20261012-3201f6f610` and `VAL-b2d40c623c3143bb` (PASSED 9/9) are preserved and untouched.
- **R1 review `VAL-773140a7956346c8` — REJECTED (preserved, not reclassified).** Host ingestion attempt **`VATT-7a9c06e23a1a45cd`**, disposition `rejected`, exact reason **"A skipped or failed check cannot establish PASS"** (parser `parse_validator_report`, `src/vres_os/validation.py`: outcome `passed` with any check whose status is not `passed` raises). Root cause: the validator returned outcome `passed` while listing `not_run` entries (CI/PG16, split-role) inside `checks`. It was not a bad request key or JSON shape. The host stored no verdict, model, agent or session for it; the validator's own hand-back text was not host-attested and did not count. The task's validation status then read pending.
- **R2 review `VAL-e61c7405f22c42c7` — PASSED, 9/9 mandatory checks, 0 failed, 0 not_run.** Created 2026-10-13 11:07:00 +03:00; completed 11:15:00 +03:00. Host-observed model **claude-fable-5-1**; agent **a2cc3feef68244cc7**; session 46ef6c93-de2e-40f7-96bd-fb73f2eb2a05 (the Chairman session id; a future session must use its own id). The mandatory checks were: (1) configuration isolation; (2) cleanup failure semantics; (3) old-incident reconciliation accuracy; (4) Journey A; (5) Journey B; (6) negative controls and RED-first proof; (7) scope; (8) cleanup verified; (9) rejected history preserved. The open program obligations were required to be listed under `limitations`, outside `checks` (section I); that is what made the report parser-valid. This was not a weakening of the check: the validator was instructed to report truthfully and not to alter findings to satisfy the parser.
- A checkpoint after the PASS is rejected by the database trigger (`protect_passed_validation_state`). Do NOT invalidate the PASS or edit database records to tidy state.

## D. Test evidence (what was run by whom)

Distinguish three classes. Do NOT claim the validator reran the PostgreSQL journeys: it did not.

1. **Independently re-executed by the Fable validator (pure, no PostgreSQL server):** `tests/integration/test_pg_run_guard.py` — **82 passed, 0 skipped, exit 0** (validator's own run with `PYTHONPATH=src`; host JUnit `negative_controls.junit.xml` 82/0/0/0 as well). Also its own read-only checks: HEAD/tree/parent, `git status`, empty diff for src/migrations/.github/scripts/conftest, `cmp` of the four review copies against the worktree, `sha256sum -c`, `ruff --select E9,F63,F7,F82` clean.
2. **Host-executed (Chairman) on the isolated cluster; validator reviewed JUnit/log/hash/manifest evidence only:**
   - **Journey A (user-event-writer):** `tests/integration/test_user_event_writer_boundary_journey.py::test_runtime_sql_cannot_forge_user_authority_but_writer_can` — **1 passed, 0 skipped, exit 0** (JUnit timestamp 2026-10-13T11:03:27+03:00). Database `vres_e7_uew_r2_110323_test`, run `a6d5e31593fa471ca3449a0e4b602b1d`.
   - **Journey B (E6 observability):** `tests/integration/test_e6_observability_schema.py` — **17 passed, 0 skipped, exit 0** (JUnit 11:03:54). Database `vres_e7_e6_r2_110350_test`, run `2e67928f0b244ee18e6352c1c1516b75`. Node ids: test_policy_row_and_frozen_digests, test_migration_count_and_latest, test_valid_observation_inserts_and_checks_reject_bad_rows, test_append_only_for_update_delete_truncate_even_for_owner, test_restrict_foreign_keys_protect_the_ledger_from_cascades, test_boundary_runtime_reads_but_cannot_write_or_record, test_n_boundary_activation_is_repeatable_without_broadening_grants, test_k_real_040_to_041_upgrade_preserves_seeded_state, test_m_same_version_policy_row_with_wrong_json_fails_the_migration, test_reference_table_has_no_raw_text_columns_and_a_closed_shape, test_reference_checks_uniqueness_and_item_integrity, test_reference_ledger_is_append_only_and_restricts_cascades, test_writer_role_may_execute_the_reference_recorder_only, test_replay_table_is_closed_content_free_and_writer_function_is_not_public, test_replay_writer_refuses_non_writer_unknown_keys_and_bad_shapes, test_046_accepts_v1_to_v5_pairs_and_rejects_cross_unknown_pairs, test_042_constraint_shape_and_no_other_schema_change.
   - Total host-executed PostgreSQL journey tests: **18**. Executable exit codes recorded in `journeyA.exitcode` and `journeyB.exitcode` (both 0).
3. **Static review / host-script evidence:** RED-first comparison — the 80 then-present new tests run against the OLD R1 guard (shim) gave **46 failed, 34 passed** (exit 1), proving the new tests detect the missing protections. Disclosed limitation: `test_relative_manifest_path_refused_so_the_run_area_is_unambiguous` was added after the RED run and was NOT executed against the old guard. Real-cluster refusal outputs (`negconfig_real.txt`: unset / relative / outside_run_area / contaminated_config / non_empty / purpose_env_wrong_cluster; `negreal.txt`: wrong_id / control_id / no_confirm / bad_name) were all REFUSED before any statement with the inventory unchanged; they were produced BEFORE the final save of `pg_run_guard.py` (before the absolute-manifest fix), and the same cases are covered by the final pure tests.

**Environment:** local PostgreSQL **18.6**, isolated cluster `127.0.0.1:55432` (the endpoint is recorded in earlier handoffs; it was not re-recorded in the R1/R2 artifacts), system identifier **7694553000872930884**; the shared/control identifier **7685334034094099024** is refused unconditionally. Python 3.12.10, pytest 9.1.1. Pre/post inventories equal: databases `['postgres']`, roles `['vres_e7_b4b_admin']`. Baseline writer role `vres_e7_b4b_admin` restored after each journey; zero non-admin sessions.

**Evidence directories (git-ignored, local, MUST be preserved, never rewritten):**
- R2: `C:\Projects\Vres-Issue-176-E7-20261006\.vres\local-tools\e7-deferred-harness-evidence-r2-20261013\` — `SHA256SUMS.txt` sha256 `926af52d2c45ff3d41b7f641edcd2eef7ea66837fe55f8d0337b838949f59fd8` (60 entries, `sha256sum -c` all OK); `INDEX_AND_ACCEPTANCE_MATRIX.md` `cdf6fead296228f97d192571842d857e167c6749fa8ea9b32ed2f6accd81799f`; `test_only.diff` `8a7bbbb4d93e084d48f490a86805e5b346990d131780a8431ae0d1085f918109`; `review_copies/` and `review_copies.sha256`; `attempt0_relative_manifest/`; ops.py/run.sh; journey and negative-control JUnit, verbose logs and exit codes; manifests, identity/inventory/writer/teardown files.
- R1 (historical): `...\e7-deferred-harness-evidence-20261013\` — `SHA256SUMS.txt` `5ee501f11130727e088ce0fc95189de040444104804d31de7902229dbc917974`; `sha256sum -c` gives 38 OK and **four unresolved relative-path entries** (`tests/integration/...`; the reviewed copies live in the R2 `review_copies/`). Preserved as-is; it was not "normalized". Includes `run1_failed/`.
- Post-acceptance read-only reconciliation: `...\e7-post-acceptance-reconciliation-20261013\inventory_readonly.json` (sha256 `832d22fd3d0d0bb2308a2087a0723272c303ad1d9fcdf206f0c395e20b7987ab`).

## E. Security design of the harness

- **Cluster identity first:** a mutation is allowed only after the connected server's `system_identifier` equals the approved id (env `VRES_TEST_CLUSTER_SYSTEM_ID`); the control id is rejected unconditionally; database names must end `_test`; `VRES_ALLOW_TEST_DB=1` gate.
- **Config isolation (`VRES_DATA_DIR`):** must be non-empty, absolute, free of `..`, a strict descendant of the run area (the manifest's resolved parent), without symlink/junction/reparse component, not overlapping the normal Vres user-data directory, containing no `config.json`, empty at provisioning, and only real `logs`/`runtime` top-level entries afterward; it is bound into the run manifest and re-checked equal to the manifest binding. The manifest path itself must be absolute.
- **Purpose DSN checks:** `VRES_DATABASE_URL`, `VRES_PROVENANCE_WRITER_DATABASE_URL`, `VRES_MIGRATION_DATABASE_URL` that resolve to another cluster/database are refused before any connection, with value-free messages (no raw DSN printed). Credentials come only through `vres secret run --env VRES_TEST_DATABASE_URL=pg_e7_b4b_isolated_dsn`; never printed.
- **Run manifest:** per-run id, database, system identifier, data_dir, resource states, expected writer role, events.
- **Cleanup semantics (`RunLedger.cleanup`, `finish()`):** manifest reloaded and bound (run_id/database/system_identifier) before any DROP; every independent step is attempted and every failure recorded; a still-bound temporary writer role is never dropped; drops refuse a foreign comment tag; incomplete cleanup raises `CleanupIncomplete` (a pytest ERROR, never PASS); with an original test failure in flight the cleanup failure is attached as a note and the original propagates.
- **Interruption recovery:** the manifest-based `recover`/`teardown` operator steps; the finalizer path is verified by code and fake-server tests, NOT by a hard kill of a live PostgreSQL.

## F. Historical incidents (evidence preserved, nothing rewritten)

1. **R1 control-configuration inheritance.** The first R1 provisioning attempt (database `vres_e7_uew_102834_test`, run `4c970d5ee6db4e6aab2268bd7e6dfd3e`) ran `db.migrate()` against the isolated cluster while inheriting the operator Vres configuration (`provenance_writer_user` set), which failed in `activate_boundary` with a missing-role error (`role "vres_os" does not exist`, relayed by the operator; the literal text is not in a surviving artifact). The database was torn down via the manifest (`manifest_A_failed_first_attempt.json`: resource `dropped`, status `torn_down`); `teardown_A_partial.txt` shows databases `['postgres']`, roles `['vres_e7_b4b_admin']`. The recovery ran on the pre-freeze harness version (about 11 s before the final guard save) and is NOT relabeled R2. **Unverified:** the exact SQL reached before failure; the literal endpoint in the artifacts; and that the control database was untouched (the control database was deliberately not queried; the failing statement referenced a role on the isolated cluster and the isolated inventory was unchanged — indirect support only). The fix was demonstrated in R2 by an empty isolated `VRES_DATA_DIR` staying empty through provisioning and both journeys.
2. **R1 stale expectation.** The first R1 Journey B run (`run1_failed/`) gave 16 passed / 1 failed (`test_k_real_040_to_041_upgrade_preserves_seeded_state`), a stale test expectation about the post-migration state (the final test expects the `source_trust_events` ledger of migration 047). It was corrected before the reviewed state; the precise failing assertion is not re-derived here.
3. **R2 relative-manifest incident.** The first R2 provisioning (database `vres_e7_uew_r2_110159_test`, run `370feaff7bd54f9b8fc3d57286b6016f`) used a relative manifest path; `vres secret run` changed the working directory, so the manifest was written at the control-project root and the guard's run-area check wrongly accepted the data dir. The pytest gate refused (manifest missing) before any mutation. The guard now requires an absolute manifest path (with a test). The stray database was torn down via the manifest (`attempt0_relative_manifest/manifest_attempt0_root_cwd.json`: dropped / `torn_down`; `teardown_attempt0.json` inventory at baseline). No stray manifest remains in the control project root and its `git status` was clean.
4. **R1 manifest metadata discrepancy.** `recover_A_partial.txt` printed the failed R1 resource as `provisioned`, while the manifest file itself says `dropped`/`torn_down`. Read-only reconciliation (below) found no live resource: this is stale printed state, not a leak. Not rewritten.
5. **Post-acceptance read-only reconciliation (2026-10-13, after the R2 acceptance, before the product commit).** Read-only transaction on the isolated cluster (identity gate required `7694553000872930884`, control id refused): PostgreSQL 18.6; databases `postgres`, `template0`, `template1`; the only role `vres_e7_b4b_admin`; no `vres_e7*` databases; no `vres*` roles other than the admin; no other client sessions. Equal to the recorded baseline. No new cleanup was performed.

## G. Production-versus-test distinction

The evidence comes from a disposable single-admin-role PostgreSQL 18.6 cluster where one administrative role plays the migrator, the writer and (for the journeys) the baseline writer role; temporary runtime/writer roles are created and removed per run. It is NOT a real split-role production deployment (separate migrator, provenance-writer and runtime roles with real credentials and network separation), NOT PostgreSQL 16 (the GitHub CI image is `postgres:16`), and NOT exact-head CI. The journeys demonstrate boundary behavior on the harness cluster only.

## H. Existing accepted architecture (unchanged)

Policy `176.g7.v1` digest `f20b037b00d0a5711666fd6c1d98538101708d99e7f6f32cf5a490ff6b96cf03`; migrations 047 and 048 and `source_trust_policy.py` unchanged; accepted R3 contract `docs/architecture/EXPERIENCE-INTELLIGENCE-E7-G7-CHUNK3A-SOURCE-TRUST-INTERFACE-CONTRACT-R3-2026-10-12.md` (SHA-256 `ce6ef7c40f1263367c1202aa8e795ca41384810e62582899a3fca2adaf208c38`) unchanged; accepted D2 evidence (`VAL-b2d40c623c3143bb`) preserved; exactly 54 registered MCP tools, `source_trust_status`/`source_trust_inspect` read-only; `source_trust_grant`/`source_trust_revoke` NOT registered; mutation remains the static `{available:false, reason:"g8_host_ingress_open"}`. The R2 change touches only test files.

## I. Open obligations (do not delete)

- **PostgreSQL 16 CI parity** (local evidence is PG 18.6): OPEN.
- **True production split-role acceptance:** OPEN.
- **Exact-head CI:** not observed for ac45967, 752d5e9, 4a929e0 or e18269e (not green, not claimed).
- Harness limitations: NULL-comment resources can be dropped without tag match inside the CREATE-to-COMMENT window (bounded by the manifest); finalizer path not hard-kill tested; symlink/junction refusal proven by fake-server tests on real filesystem links, not by a live destructive PostgreSQL run; real-cluster refusal outputs predate the final absolute-manifest save; one late RED-first test not run against the old guard; R1 bundle holds four unresolved relative-path manifest entries; the exact SQL of the R1 incident is unrecorded.
- S2 SQL alias observation (separate bounded correction only if literal conformance is required).
- Four Windows symlink skips (pytest.skip; not re-run).
- G8 host-ingress security architecture and grant/revoke issuer execution: OPEN. Positive production issuance DISABLED.
- G7 Chunk 4 / E5 v6 (prospective raw-evidence eligibility via ledger-verified trust; v2–v5 byte-identical replay; same-snapshot trust/content consistency).
- G7 Chunk 5: read-only legacy source audit, no grandfathering.
- G1/G2: owner-derived trust downgrade; verifiable common lineage.
- B4B-v1 unresolved adversarial gaps (live adv_secret_episode RED artifact sha256 aea04d4e3a7b67d19a8b7aea092b18f53c3300afc805d350b29f517e60480693 preserved; deterministic matrix 16 PASS / 0 FAIL / 1 N/A / 3 OWNER_GAP; flood and varied-poison BLOCKED_OWNER_EVIDENCE); prospective B4B-v2 design (DRAFT, not acceptance).
- Chunk 6 development-only benchmark replay; threshold freeze; held-out acceptance only after freeze.
- Final E7 ladder: full fresh PostgreSQL suite, release gate, packaging smoke if MCP/packaging changed, exact-head CI, protected final validation, guarded merge, post-main evidence, complete canonical E7 task.
- E8/E9, physical acceptance and later production-readiness tasks (#169, #170) remain held.

## J. Vres lifecycle

- Task `TASK-20261013-e0f2073d4a` active; latest protected review `VAL-e61c7405f22c42c7` PASSED; history `VAL-773140a7956346c8` REJECTED (VATT-7a9c06e23a1a45cd). Task `TASK-20261012-3201f6f610` active with `VAL-b2d40c623c3143bb` PASSED. Neither was completed or recreated.
- Stale prose may appear in `task_open_list`; `task_resume` and `validation_evidence` derive the PASS. A post-PASS checkpoint is rejected by the trigger; do not invalidate or edit records.
- Do not reuse any old provider session id; take the id from the newest lifecycle hook.

## K. Next controlled step

The next session must first verify the committed Git identities (product remote e18269e / tree 0456965 / parent 4a929e0; docs HEAD) and the host Vres validation evidence for both tasks, report state, then STOP and wait for a separately authorized instruction. It must not automatically start G8, E5 v6, G1/G2, B4B, Chunk 6, PG16 CI, split-role work, a PR or a merge, must not modify the GitHub CI workflow, and must not treat Chunk 3A or E7 as merge- or release-ready.

**Recommendation for the next separately authorized gate:** the smallest evidence-bearing step is exact-head CI observation on the pushed product head (including PG16 parity); the largest design dependency is the G8 host-ingress security architecture, which gates any positive trust issuance.
