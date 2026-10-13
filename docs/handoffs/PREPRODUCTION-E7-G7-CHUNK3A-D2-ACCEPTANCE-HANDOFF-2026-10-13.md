# Vres-OS — E7 / G7 Chunk 3A D2 acceptance durable handoff (2026-10-13)

This handoff records the accepted, committed and pushed D2 pre-merge evidence correction for G7 Chunk 3A. It is additive: it does not edit earlier handoff conclusions, the accepted R3 contract, or any product behavior. Read it BEFORE `PREPRODUCTION-E7-G7-CHUNK3A-IMPLEMENTATION-CHECKPOINT-HANDOFF-2026-10-12.md` (which remains the record of the implementation checkpoint and still lists D2 as OPEN, as it was at that time) and before `PREPRODUCTION-E7-G7-CHUNK3A-RESUME-HANDOFF-2026-10-12.md`.

## 0. Status block

```
G7_CHUNK3A_R3_DESIGN=ACCEPTED
G7_CHUNK3A_IMPLEMENTATION=VALIDATED
D2_PREMERGE_EVIDENCE=PASSED_COMMITTED_AND_PUSHED
G7_CHUNK3A_PRODUCT_CHECKPOINT=PUSHED
G7_CHUNK3A_MERGED=NO
G8_HOST_INGRESS=OPEN
POSITIVE_PRODUCTION_ISSUANCE=DISABLED
E7_RELEASE_READY=NO
NEXT=RESUME_FROM_D2_CANONICAL_HANDOFF
```

Chunk 3A is NOT merged and NOT merge-ready: D2 closure is one of several pre-merge obligations (section G).

## A. Git identities

**Product feature branch `issue-176-e7-g7-chunk3`** (`vosser24/Vres-OS`; NOT merged; NO PR):
- HEAD: **4a929e01839d20c690509fb06092147a1bf41361**
- Tree: **e1407b8068fbd9eca84b0c4be120ba10a2a1b82f**
- Parent: **752d5e9c4cf02735e3ed2582c93080e2748e949f** (implementation checkpoint; tree 28440eea8ee886992335fa6ff4e8d6eda46dc63f; parent ac45967f63690b76d41b7303ad43248afed8751f).
- Subject: `test(g7): complete D2 source trust read-only evidence`.
- Delta vs parent: exactly ONE file, `tests/integration/test_g7_source_trust_read.py`, **+64 insertions, -11 deletions**. Production source, migrations, policy and the R3 contract are not in the diff.
- The commit was created locally by the Chairman; the push was performed by the user through an independently guarded manual operation (the automated push was denied by the permission classifier and was not retried through another route). Remote HEAD, tree, parent and one-file diff were independently retrieved from GitHub before this handoff was written.

**Other positions:**
- Product main: 9a8acc5d464b96432a93cb95daa9581412fb07ee (no G7 branch merged).
- Original E7 security branch `issue-176-e7-benchmark-security`: 0b4d5cdd79ec1e14366f9edce06575fbb8429294, unchanged.
- G7 chain: Chunk 1 03a9897 -> Chunk 1A 99c7300 -> Chunk 2 ac45967 -> Chunk 3A 752d5e9 -> **D2 test commit 4a929e0**.
- Documentation branch `docs-execution-checklist-20260927`: predecessor of this handoff commit was 5052df046bc1899615f5e249d3f395f1c6e7aad6 (tree afe04f6ebf6050e35f874b7d994d9e2500ff5492). Retrieve the new HEAD from the branch; do not expect 5052df0.
- Worktrees: product `C:\Projects\Vres-G7-Chunk3-20261012`; control/Vres context and ignored evidence `C:\Projects\Vres-Issue-176-E7-20261006`; docs `C:\Projects\Vres-E7-B4B-Docs-20261009` (local branch docs-e7-b4b-v2-20261009 tracking the canonical docs branch).

## B. Full G7 acceptance history (preserved, not relabeled)

- **Design history before Chunk 3A:** G7 design revisions rejected (VAL-ea1520bbb051493f, VAL-ada05e213965497f, VAL-168d073866974f8d, VAL-b3ea906804df4cce); revision 5 PASSED (VAL-ca09c908c83247e2); freeze docs reviewed VAL-4364e4279c8f4123.
- **Chunk 1 / 1A:** accepted (VAL-1b1af80955f84d42; VAL-716368e0a41f4d75). Migration 047 ledger, fixture safety.
- **Chunk 2** (ac45967): accepted after a correction chain (VAL-7af7ef84a950484c rejected; VAL-0c47a21a33be462f passed then invalidated for a real post-review security finding; VAL-c08e1ab8b7ca4ef8; VAL-e9fb387e3cce48e4 failed; VAL-3017ca2614ef44ed rejected; VAL-33498ab977c247f4 passed; VAL-ecd30ab4144a4f3b rejected for unbound validator session; final VAL-b3d1bf2428fc4b0f passed). Migration 048 reader `vres.source_effective_trust`.
- **Chunk 3A design (task TASK-20261012-3201f6f610):** R1 **VAL-397fb4037e9546df** FAILED; R2 **VAL-f49f4752ef064749** FAILED; R3 **VAL-86c382ece1b34e02** PASSED 15/15 (claude-fable-5-1). Accepted contract `docs/architecture/EXPERIENCE-INTELLIGENCE-E7-G7-CHUNK3A-SOURCE-TRUST-INTERFACE-CONTRACT-R3-2026-10-12.md`, SHA-256 `ce6ef7c40f1263367c1202aa8e795ca41384810e62582899a3fca2adaf208c38`, unchanged.
- **Chunk 3A implementation:** first review **VAL-8b8d89240b814c0c** FAILED (S3/S4 began with WITH; PG matrix rows missing; PG evidence relayed only); final review **VAL-52ec36f2f6624300** PASSED 17/17 (claude-fable-5-1, agent adea8ff33eaa2eadf).
- **D2 evidence closure:** the implementation checkpoint handoff recorded the D2 gap (test counted only source_trust_events, sources, knowledge_chunks; plus a meaningless `pg_current_wal_lsn()` truthiness assertion). Closed by the test-only commit 4a929e0 and review **VAL-b2d40c623c3143bb PASSED**. To make the edit, validation was explicitly invalidated with the reason "D2 test evidence is being extended after the accepted implementation review" (the historical VAL-52ec36f2f6624300 PASS is preserved in the history); a checkpoint (CP-20261012-96657f946b) was recorded before the new request was prepared.

## C. D2 validation VAL-b2d40c623c3143bb

- Task: TASK-20261012-3201f6f610. Created 2026-10-12 18:52:19 +03:00; completed 2026-10-12 18:59:38 +03:00.
- Host-observed model **claude-fable-5-1**; agent **a677a093f618a9011**; session 6e4e2b2a-7c57-455b-9e51-2067d6ce6016 (this was the Chairman session id; a future session must use its own id).
- Result **PASSED, 9/9 checks, 0 failed, 0 not_run.** Checks: (1) six-table counts; (2) ledger max(id); (3) serialized source-row equality; (4) measurement validity incl. service-vs-MCP coverage statement; (5) negative control; (6) removed WAL assertion is no loss; (7) scope (one file, no production change, line endings, no secrets); (8) D1/D3 not conflated with D2; (9) persisted evidence binding.
- **Frozen test file (working-tree, CRLF) SHA-256: `e95b0d4668f92d03383efa40f942d870b58a840f5c985946634121184b82938b`.** LF-normalized SHA-256 `a883e9b6243cb1ef393559a51a1d6c5cbdfb58f162616de499b4802f351bc5d4` equals the committed Git blob content (verified after staging). The pre-change HEAD blob was `981b688240382b76aa2589353bc5f922b4627c0217d2e83baf7ba1a63afbf90a` (LF). Do not confuse the CRLF working hash with the LF blob.
- **Evidence directory (ignored, local):** `C:\Projects\Vres-Issue-176-E7-20261006\.vres\local-tools\g7-chunk3a-d2-evidence-20261012\`. `MANIFEST.sha256` (itself sha256 `23534143e9f68065ab3947e70e2dfae583ad12e790158fa360170f175af3aef8`) lists **27 entries**, all verified OK by `sha256sum -c` (by the validator and again by the Chairman before commit): INDEX.md (a065c983…f39f), snapshot/test_g7_source_trust_read.py, snapshot/d2_test.diff (aaef70fd…830a), JUnit d2_node (80461c08…0759), read (988d25d6…cd5), reg047048 (039f8bec…2b), unit (5e2e4edc…b9f), verbose logs, exit-code and start/finish files, cluster_identity before/after (both 9130e86f…e8d9), collect.txt, versions_and_import_path.txt, run_pg.sh, cluster_identity.py. Raw logs are referenced by that manifest; nothing missing was reconstructed. The directory is not committed and must be preserved, not overwritten.
- **Reviewer limitations (verbatim in substance):** cluster identity files and the 047/048 result were relayed, not independently verified; the validator did not run the full unit suite; the frozen unit run has no start/finish files (only JUnit timestamp 18:51:06 +03:00); MCP-surface D2 is a code-review inference; PERSISTED artifact binding was checked against the on-disk manifest because the tool exposes no registry-held artifact list.

## D. D2 PostgreSQL proof

`test_reads_write_nothing` (service level, `SourceTrustReadService`):
- Setup (grant and revoke through the migrator fixture, two ledger events) completes BEFORE the first snapshot.
- Each snapshot is one SQL statement on a **fresh autocommit connection**: counts of `source_trust_events`, `sources`, `knowledge_chunks`, `task_events`, `approval_events`, `tasks`; `max(id)` of `vres.source_trust_events`; and all `vres.sources` rows serialized as `to_jsonb(s)::text` ordered by id (UTF-8 bytes).
- Between the snapshots only the real read operations run: `status`, `inspect`, `inspect(limit=1)` (asserted truncated), `status`, `inspect`, and a not-found `status` raising "source not found in the current project".
- Non-empty preconditions asserted: source_trust_events>=2, sources>=1, knowledge_chunks>=2, tasks>=2, task_events>=1. Observed in the D2 node run: 2 / 1 / 2 / 2 / 0 / 2 (events/sources/chunks/task_events/approval_events/tasks); in the full-file run (validator): 36/22/42/36/0/44.
- Assertion: the diff of before/after is empty. The meaningless WAL truthiness assertion was removed; the D1 tests (read-only REPEATABLE READ, no xid; write inside a read-only transaction rejected) remain the transactional evidence and are untouched.
- **Negative control** `test_d2_comparator_detects_every_kind_of_change`: pure test showing the comparator detects each of the six count changes, a changed/added/removed source row, and a changed or missing ledger max(id); identical snapshots yield no diff. It proves the comparator, not the SQL; the SQL is proven live by the non-empty precondition assertions.
- **`approval_events` limitation:** the fixture contained ZERO approval_events rows. That table's 0 -> 0 proves only that no rows were created, NOT preservation of pre-existing rows. The reviewer accepted this because the service reads only vres.sources, vres.source_effective_trust and vres.source_trust_events. Do not describe it as preservation.
- **Service vs MCP:** the D2 test measures the service only. The MCP tools `source_trust_status`/`source_trust_inspect` add pure validation, `_closed_request` and one `SELECT id FROM vres.projects` before calling the same service methods; "no write path in the MCP layer" is a code-review inference, not measured.

## E. Test execution provenance

Isolated cluster 127.0.0.1:55432, system id 7694553000872930884 (never the control cluster 7685334034094099024); gates VRES_ALLOW_TEST_DB=1, VRES_TEST_CLUSTER_SYSTEM_ID, `_test` database naming; credential handle `vres secret run --env VRES_TEST_DATABASE_URL=pg_e7_b4b_isolated_dsn`; no DSN printed; Python 3.12.10, psycopg 3.3.6, pytest 9.1.1; imports resolved from the Chunk 3 worktree `src`. The isolated cluster had been killed earlier by a console CTRL_C and was restarted by the Chairman (own data directory C:\Projects\Vres-E7-B4B-PG\data; the Windows-service control cluster was not touched). Before and after the runs the cluster held only the `postgres` database and the role `vres_e7_b4b_admin`.

- **Validator-rerun (by the Fable validator, exit 0):** D2 tests 2 passed; complete `tests/integration/test_g7_source_trust_read.py` 65 passed (JUnit 0 failures/errors/skips); focused unit tests (`tests/test_source_trust_read.py`, `tests/test_runtime_surfaces.py`, `tests/test_source_revocation_unit.py`) 106 passed.
- **Host-executed (Chairman), exit codes 0, JUnit 0 failures/errors/skips:** D2 nodes 2 passed (2026-10-12 15:48:08Z–15:48:14Z); read suite 65 passed (15:48:19Z–15:49:43Z); 047/048 regressions (`test_g7_source_trust_ledger.py` + `test_g7_source_effective_trust.py`) **83 passed** (15:49:48Z–15:50:58Z); focused unit 106 passed. The 047/048 regression is host-executed ONLY (the validator's own rerun of it did not complete and is not claimed).
- **Not independently verified by the D2 validator:** the full unit suite, the cluster identity artifacts, unit-run timestamps. The full unit suite was not re-run for D2 (production untouched; baseline from the implementation checkpoint: 2974 passed / 4 skipped, host-executed, unchanged and not re-established here).
- **Collection methodology:** run unit tests with `--ignore=tests/integration` and PG suites per file; repository-wide `python -m pytest` cannot collect because of pre-existing duplicate basenames (test_experience_benchmark_*).

## F. Frozen security architecture

- Policy `176.g7.v1`, digest `f20b037b00d0a5711666fd6c1d98538101708d99e7f6f32cf5a490ff6b96cf03` — unchanged.
- Migrations 047 and 048 and `source_trust_policy.py` — unchanged (not in the diff).
- Exactly **54** registered MCP tools; `source_trust_status` and `source_trust_inspect` are the only new source-trust interfaces; `source_trust_grant`/`source_trust_revoke` are NOT REGISTERED; mutation is the static `{available:false, reason:"g8_host_ingress_open"}`.
- **G8 host ingress OPEN. Positive production issuance DISABLED.** No migrator credential is exposed.
- R3 contract unchanged.

## G. Remaining obligations (do not delete)

- **S2 SQL alias observation** (S2 aliases its returned column, slightly beyond the contract's literal SQL; reviewed implementation preserved; separate bounded correction with validation only if literal conformance is required).
- **Four Windows symlink skips** (pytest.skip, symlink privilege unavailable on this host; not re-run).
- **Two deferred production-shaped PostgreSQL integration journeys** (e6 observability schema; user-event-writer) — both merge-blocking.
- **Exact-head CI unverified** for ac45967, 752d5e9 and 4a929e0 (none observed; not green).
- G8 host-ingress security architecture and full grant/revoke issuer execution.
- G7 Chunk 4 / E5 v6: prospective source raw-evidence eligibility via ledger-verified trust; v2–v5 byte-identical replay; SAME-SNAPSHOT trust/content consistency (the 048 reader is atomic only within its own statement).
- G7 Chunk 5: read-only legacy source audit, no grandfathering.
- G1/G2: owner-derived trust downgrade; verifiable common lineage.
- Original B4B-v1 adversarial evidence: live adv_secret_episode RED artifact sha256 aea04d4e3a7b67d19a8b7aea092b18f53c3300afc805d350b29f517e60480693 preserved; deterministic matrix 16 PASS / 0 FAIL / 1 N/A / 3 OWNER_GAP; flood and varied-poison BLOCKED_OWNER_EVIDENCE.
- Prospective B4B-v2 design (DRAFT, not acceptance).
- Chunk 6 development-only benchmark replay; threshold freeze; held-out acceptance only after freeze.
- Final E7 ladder: full fresh PostgreSQL suite, release gate, packaging smoke if MCP/packaging changed, exact-head CI, protected final validation, guarded merge, post-main evidence, complete canonical E7 task.
- E8/E9, physical acceptance and later production-readiness tasks (#169, #170) remain held.

## H. Task continuity

- Task `TASK-20261012-3201f6f610` remains **active** and was NOT completed or recreated.
- Latest protected review: **VAL-b2d40c623c3143bb PASSED** (2026-10-12 18:59:38 +03:00); `validation_status` passed. History preserved: VAL-397fb4037e9546df FAILED, VAL-f49f4752ef064749 FAILED, VAL-86c382ece1b34e02 PASSED, VAL-8b8d89240b814c0c FAILED, VAL-52ec36f2f6624300 PASSED, VAL-b2d40c623c3143bb PASSED.
- Stale prose: `task_open_list` shows the older checkpoint text (CP-20261012-96657f946b records the pre-validation state "awaiting one fresh protected validation"), while `task_resume` and `validation_evidence` correctly derive the protected PASS. A checkpoint after a PASS is rejected by the DB trigger. Do NOT invalidate the PASS or edit database records to tidy this.
- Do not reuse any old provider session id; use the session id from the newest lifecycle hook with `task_resume(task_key=TASK-20261012-3201f6f610)`.

## I. Exact next controlled step

The next session must first verify the committed Git identities (product remote 4a929e0 / tree e1407b8 / parent 752d5e9; docs HEAD) and the host Vres validation evidence, report state, then STOP and wait for a separately authorized instruction for the remaining merge-gate work. It must not automatically start G8, E5 v6, G1/G2, B4B, Chunk 6, a PR or a merge, and must not treat Chunk 3A as merge-ready.
