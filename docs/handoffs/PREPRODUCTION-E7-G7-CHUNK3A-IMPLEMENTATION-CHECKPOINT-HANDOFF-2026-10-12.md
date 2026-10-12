# Vres-OS — E7 / G7 Chunk 3A implementation checkpoint durable handoff (2026-10-12)

This handoff records the validated, committed and pushed Chunk 3A read-only source-trust implementation checkpoint. It is additive: it does not edit earlier handoffs' conclusions, the accepted R3 contract, or any product bytes. Read it BEFORE `PREPRODUCTION-E7-G7-CHUNK3A-RESUME-HANDOFF-2026-10-12.md`, which remains the chronological record up to R3 acceptance.

## 0. Status block

```
G7_CHUNK3A_R3_DESIGN=ACCEPTED
G7_CHUNK3A_IMPLEMENTATION_VALIDATION=PASSED
G7_CHUNK3A_PRODUCT_CHECKPOINT=COMMITTED_AND_PUSHED
G7_CHUNK3A_MERGED=NO
D2_PREMERGE_EVIDENCE=OPEN
G8_HOST_INGRESS=OPEN
POSITIVE_PRODUCTION_ISSUANCE=DISABLED
E7_RELEASE_READY=NO
NEXT=RESUME_FROM_NEW_DURABLE_HANDOFF
```

Do not mark Chunk 3A merge-ready solely because its feature implementation review passed.

## A. Git identities

**Product feature branch `issue-176-e7-g7-chunk3`** (pushed to `vosser24/Vres-OS`, NOT merged, NO PR):
- HEAD: **752d5e9c4cf02735e3ed2582c93080e2748e949f**
- Tree: **28440eea8ee886992335fa6ff4e8d6eda46dc63f**
- Parent: **ac45967f63690b76d41b7303ad43248afed8751f** (accepted Chunk 2; tree 7a95990fb4413ddf387e90e9cfad5266f266c643)
- Remote HEAD, tree and parent were independently retrieved after the push and equal the local commit. Local branch tracks `origin/issue-176-e7-g7-chunk3`. The remote branch was verified absent immediately before the first push.
- Commit message subject: `feat(g7): add validated read-only source trust status and inspection`.

**Other positions at this checkpoint:**
- Product main: 9a8acc5d464b96432a93cb95daa9581412fb07ee (E6-accepted; no G7 branch merged).
- Original E7 security branch `issue-176-e7-benchmark-security`: 0b4d5cdd79ec1e14366f9edce06575fbb8429294 (tree 49068e09a8a90e80dcffaf44980b5f3348d83c84), unchanged.
- G7 chain: Chunk 1 03a9897 -> Chunk 1A 99c7300 -> Chunk 2 ac45967 -> **Chunk 3A 752d5e9**.
- Documentation branch `docs-execution-checklist-20260927`: predecessor of this handoff commit was f63e0b0cd231948594f93dd613f84aa0186fa100. Retrieve the new HEAD from the branch; do not expect f63e0b0 after this documentation-only commit.
- Worktrees: product `C:\Projects\Vres-G7-Chunk3-20261012` (branch issue-176-e7-g7-chunk3, clean); control/Vres project context and ignored evidence bundles `C:\Projects\Vres-Issue-176-E7-20261006`; docs worktree `C:\Projects\Vres-E7-B4B-Docs-20261009` (local branch docs-e7-b4b-v2-20261009 tracking the canonical remote docs branch).

## B. Complete G7 history

- **Design history before Chunk 3A:** G7 design revisions rejected (VAL-ea1520bbb051493f, VAL-ada05e213965497f, VAL-168d073866974f8d, VAL-b3ea906804df4cce); revision 5 PASSED (VAL-ca09c908c83247e2); freeze docs reviewed VAL-4364e4279c8f4123.
- **Chunk 1** (03a9897) and **Chunk 1A** (99c7300): accepted (VAL-1b1af80955f84d42; VAL-716368e0a41f4d75). Migration 047 ledger, fixture safety.
- **Chunk 2** (ac45967): accepted after a correction chain (VAL-7af7ef84a950484c rejected; VAL-0c47a21a33be462f passed then invalidated for a real post-review security finding; VAL-c08e1ab8b7ca4ef8; VAL-e9fb387e3cce48e4 failed; VAL-3017ca2614ef44ed rejected; VAL-33498ab977c247f4 passed; VAL-ecd30ab4144a4f3b rejected for unbound validator session; final VAL-b3d1bf2428fc4b0f passed). Migration 048 reader `vres.source_effective_trust`.
- **Chunk 3A design, task TASK-20261012-3201f6f610:**
  - R1 review **VAL-397fb4037e9546df** FAILED (single-active-grant recovery model wrong; incomplete test matrix).
  - R2 review **VAL-f49f4752ef064749** FAILED.
  - R3 review **VAL-86c382ece1b34e02** PASSED 15/15, observed model claude-fable-5-1. Accepted contract: `docs/architecture/EXPERIENCE-INTELLIGENCE-E7-G7-CHUNK3A-SOURCE-TRUST-INTERFACE-CONTRACT-R3-2026-10-12.md`, SHA-256 `ce6ef7c40f1263367c1202aa8e795ca41384810e62582899a3fca2adaf208c38` (unchanged).
- **Chunk 3A implementation:**
  - First review **VAL-8b8d89240b814c0c** FAILED: S3/S4 began with `WITH` (SELECT-only breach), PG matrix rows L1-L6, L9, I3, C3 lacked tests, PG evidence was relayed only. Preserved as history.
  - Correction round, then final review **VAL-52ec36f2f6624300** PASSED 17/17, observed model claude-fable-5-1, agent adea8ff33eaa2eadf.
  - **Dispatch history:** the first dispatch of the final review's validator hit an HTTP 529 before producing any report. The SAME frozen validation request was then redispatched once and produced the accepted report. There was one successful independent review, not two.

## C. Product implementation

Exactly six committed paths (blob ids in the commit tree):
1. `src/vres_os/source_trust_read.py` (new) — read-only service. Blob fce2c3a1…
2. `src/vres_os/mcp_server.py` (modified) — adapters `source_trust_status`, `source_trust_inspect`. Blob 69b39ef7…
3. `tests/test_source_trust_read.py` (new, 49 unit tests). Blob d9aa61ec…
4. `tests/test_runtime_surfaces.py` (modified, registry 52 -> 54). Blob ce6973d2…
5. `tests/test_source_revocation_unit.py` (modified; readers allowlist). Blob d6eaf352…
6. `tests/integration/test_g7_source_trust_read.py` (new, 64 PG tests). Blob ad51a75e…

Totals: 1557 insertions, 1 deletion.

- **Tools:** exactly two new read-only MCP tools; total registered MCP tools **54**. No grant or revoke tool is registered; the `mutation` field is a static `{available:false, reason:"g8_host_ingress_open"}`.
- **Transaction model:** one REPEATABLE READ + READ ONLY transaction (psycopg attributes set before the first statement). S0 `current_setting` check; S1 sources lookup; S2 reader; S3 ledger aggregate; S4 inventory page. S3/S4 are SELECT-leading with inlined derived tables (no WITH). Statement counts: status 4, inspect 5, source-not-found 2, transaction-state mismatch 1, validation failure 0 with zero connections.
- **Isolation:** every ledger scan is scoped by project and source; sources are resolved inside the current project; foreign project data is never returned (I3 test).
- **Event/revocation semantics:** `vres.source_effective_trust` (048) is the sole positive-trust authority; the service never recomputes digests. `newest_event` is `{ordinal, event_key, action, created_at}`, ordered by ledger id descending. Trust-ledger revoke is distinct from source-lifecycle revocation; the new modules never call `source_revoke` (C3 test: a ledger revoke leaves the source active; a lifecycle revoke appends no ledger event).
- **Bounded inventories / no partial elevation:** schema-impossible corruptions are rejected by the database; schema-permitted corruptions make the service fail closed with exactly "source trust inventory inconsistent"; unknown source returns "source not found in the current project". Errors are value-free.
- **No new issuer authority:** the 047 issuer `record_source_trust_decision` is invoked only by the test fixture through the migrator DSN, never by the service.

## D. Test evidence

- **RED-first:** the Chunk 3A tests were written first and observed failing before the implementation (earlier session record); the corrected round added the missing PG matrix rows against the corrected SELECT-only queries.
- **Host-executed (reviewed by the validator, not validator-rerun):**
  - Unit suite: `python -m pytest tests --ignore=tests/integration -p no:cacheprovider -rs -v` — **2974 passed, 4 skipped**, exit 0.
  - PostgreSQL integration `tests/integration/test_g7_source_trust_read.py` — **64 passed**, exit 0.
  - PostgreSQL 047/048 regression (`test_g7_source_trust_ledger.py` + `test_g7_source_effective_trust.py`) — **83 passed**, exit 0.
- **Validator-rerun:** 106 unit tests passed; hashes recomputed. The validator did **NOT** rerun PostgreSQL. Do not describe the PG results as validator-executed.
- **Skips (verified from `unit_full.junit.xml`):** all four are `pytest.skip` symlink-privilege skips on this Windows host: "symbolic links are not available"; "symlink creation not permitted on this host"; "Windows symlink creation may require elevated developer-mode privileges"; "Windows symlink privilege is unavailable on this host". They are skipped, not passed. They were not re-run.
- **Evidence bundle (ignored, local):** `C:\Projects\Vres-Issue-176-E7-20261006\.vres\local-tools\g7-chunk3a-impl-evidence-r2-20261012\` (EVIDENCE_INDEX.md sha256 2904a844…1656; REQUIREMENT_MAP.md sha256 c69539e1…5cd8; 41 section-8 IDs all PASS, generated from JUnit). JUnit sha256: read b1421f5d…12ac, regress 963437be…58b9, unit_full 9070a0de…2d0f. Full list in `artifact_sha256.txt`. The older bundle `g7-chunk3a-impl-evidence-20261012\` is the failed first round; both are untouched.
- **Frozen snapshot hashes (raw working-tree/CRLF bytes validated):** source_trust_read.py a4aa7337…1beb; mcp_server.py cb7d71ba…de52; test_source_trust_read.py d6fc8813…ab3b; test_runtime_surfaces.py 058141fe…c0c; test_source_revocation_unit.py 14678b1c…5393; test_g7_source_trust_read.py 981b6882…f90a. Committed Git blobs are LF-normalized (core.autocrlf=true); before commit each staged blob was compared with its snapshot with CR removed and all six matched. Raw-byte hashes of blobs differ from snapshot hashes where CRLF applies.
- **PG safety:** isolated cluster 127.0.0.1:55432, system id 7694553000872930884 (not the control cluster 7685334034094099024); gate `VRES_ALLOW_TEST_DB=1`, `VRES_TEST_CLUSTER_SYSTEM_ID`, `_test` database name, credential handle via `vres secret run --env VRES_TEST_DATABASE_URL=pg_e7_b4b_isolated_dsn`; no DSN printed. After the runs only the `postgres` database remained.
- **Collection methodology:** a repository-wide `python -m pytest` cannot collect because `tests/` and `tests/integration/` share some pre-existing duplicate basenames (test_experience_benchmark_*). Run the unit suite with `--ignore=tests/integration` and PG suites per file. The validator did not independently reproduce the duplicate-basename claim.
- **Caveats:** D2, S2 and the skips are in section F.

## E. Frozen boundaries

- Policy `176.g7.v1`, digest `f20b037b00d0a5711666fd6c1d98538101708d99e7f6f32cf5a490ff6b96cf03` — unchanged.
- Migrations 047 and 048 and `source_trust_policy.py` — byte-identical to the parent (CR-normalized) and absent from the commit.
- R3 contract — unchanged.
- **G8 host ingress OPEN.** **Positive production issuance DISABLED.** Grant/revoke tools NOT REGISTERED.

## F. Outstanding program obligations

**Chunk 3A pre-merge acceptance follow-ups (from the reviewer's non-blocking observations):**
- **D2 evidence gap (OPEN):** R3 D2 requires unchanged row counts in source_trust_events, sources, knowledge_chunks, task_events, approval_events and tasks, plus unchanged source row contents. The existing D2 PG test counts only three tables. Do not describe it as full literal D2 proof unless other independently identified tests complete it. Closing it needs a separately scoped test change and new validation.
- **S2 alias observation:** S2 aliases its returned column, going slightly beyond the contract's literal SQL example. Reviewed implementation preserved unchanged. If literal conformance is later required, handle via a separate bounded correction with validation.
- **Four Windows symlink skips** as in section D.
- PG suites were host-executed only.

**Program obligations (do not delete):**
- Two deferred production-shaped integration journeys (e6 observability schema; user-event-writer) — both merge-blocking.
- Full grant/revoke execution blocked on an independently secured G8 path.
- G7 Chunk 4 / E5 v6: prospective source raw-evidence eligibility via ledger-verified trust; preserve v2-v5 byte-identical replay; SAME-SNAPSHOT source-trust/content consistency (the 048 reader is atomic only within its own statement).
- G7 Chunk 5: read-only legacy source audit, no grandfathering.
- G1/G2: owner-derived trust downgrade; verifiable common lineage.
- Original B4B-v1 adversarial evidence: live adv_secret_episode RED artifact sha256 aea04d4e3a7b67d19a8b7aea092b18f53c3300afc805d350b29f517e60480693 preserved; deterministic matrix 16 PASS / 0 FAIL / 1 N/A / 3 OWNER_GAP; flood and varied-poison BLOCKED_OWNER_EVIDENCE.
- Prospective B4B-v2 design (DRAFT, not acceptance).
- Chunk 6 development-only benchmark replay and threshold freeze; held-out acceptance only after freeze.
- Final E7 ladder: full fresh PostgreSQL suite, release gate, packaging smoke if MCP/packaging changed, exact-head CI (none observed for ac45967 or 752d5e9 — not green, unverified), protected final validation, guarded merge, post-main evidence, complete canonical E7 task.
- E8/E9 and later production-readiness tasks (#169, #170) remain held.

## Task and validation state

- Task `TASK-20261012-3201f6f610` remains **active**; it was NOT completed. Latest persisted validation: VAL-52ec36f2f6624300 passed (2026-10-12 17:46 +03:00). A non-material checkpoint after the pass is rejected by the DB protection trigger, so the persisted `next_action` still reads "Protected validation is current and passed. Continue from the validated state without dispatching another validation; explicitly invalidate validation before any material change." Do not invalidate the pass merely to tidy this.
- Validation history is preserved: VAL-397fb4037e9546df FAILED, VAL-f49f4752ef064749 FAILED, VAL-86c382ece1b34e02 PASSED (design), VAL-8b8d89240b814c0c FAILED, VAL-52ec36f2f6624300 PASSED.
- Do not reuse the old provider session ID; use the session id from the newest lifecycle hook with `task_resume(task_key=TASK-20261012-3201f6f610)`.

## G. Exact next controlled step

The next session must verify the committed feature checkpoint (local and remote 752d5e9, tree 28440eea, parent ac45967; docs HEAD) and Vres task/validation evidence, report state, then WAIT for a separate governed instruction to address the outstanding acceptance obligations (starting with D2 closure) . It must not automatically begin G8, E5 v6, B4B, a PR or a merge, and must not treat Chunk 3A as merge-ready.
