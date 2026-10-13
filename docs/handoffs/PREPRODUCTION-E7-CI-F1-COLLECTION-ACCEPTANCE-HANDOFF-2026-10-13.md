# Pre-production E7 CI F1 (pytest collection repair) — acceptance handoff, 2026-10-13

Self-contained checkpoint for a new session. Extends (does not replace) `PREPRODUCTION-E7-DEFERRED-INTEGRATION-R2-ACCEPTANCE-HANDOFF-2026-10-13.md`.

## 0. Status block

```
F1_PYTEST_COLLECTION=VALIDATED_COMMITTED_AND_PUSHED
F1_CI_WORKFLOW=CHECKPOINTED_NOT_YET_GREEN
F2_PG16_PROVISIONING=OPEN
POSTGRESQL16_PARITY=OPEN
TRUE_SPLIT_ROLE_ACCEPTANCE=OPEN
EXACT_HEAD_CI=OPEN
R2_ACCEPTANCE=PRESERVED
D2_ACCEPTANCE=PRESERVED
G8_HOST_INGRESS=OPEN
POSITIVE_PRODUCTION_ISSUANCE=DISABLED
E7_RELEASE_READY=NO
NEXT=RESUME_FROM_F1_CANONICAL_HANDOFF
```

## A. Exact Git positions

- Repository `vosser24/Vres-OS`. Product branch `issue-176-e7-g7-chunk3`.
- Product HEAD `d930adfa89617067115d9538e9692945230d9630`, tree `1c15a8fcb02093c7f16ea67f5295779ad1e0a107`, parent `e18269e8d18cd58f3dae061de8d3bb01758cd82a` (R2 head, tree `0456965510a984c248318a3f40598a5c86709923`). Remote head, tree, parent and the one-file diff were verified after a normal fast-forward push (`e18269e..d930adf`).
- Commit subject: `ci(e7): split pytest collection to preserve duplicate test modules`. Changed path: `.github/workflows/ci.yml` only (+7/−2).
- Product worktree `C:\Projects\Vres-G7-Chunk3-20261012`.
- Documentation predecessor: `docs-execution-checklist-20260927` at `4ec60486f03d28e99eb38cc8e3dd176d205ca3b4`, tree `473563ab50797e4bd8dd0d32753031c0c6be39bf` (the commit carrying this handoff has this as its parent). Docs worktree `C:\Projects\Vres-E7-B4B-Docs-20261009`.
- `main` unchanged by this work (remote `9a8acc5d464b96432a93cb95daa9581412fb07ee` when last listed). Feature branch NOT merged. No PR.

## B. F1 task and review

- Task `TASK-20261013-1c26893128` (control project `C:\Projects\Vres-Issue-176-E7-20261006`), still active, not completed.
- Protected validation `VAL-94c5bb86d2fe4a99`: **PASSED, 8/8 host-persisted checks**, observed model `claude-fable-5-1` (Fable/high), agent `ac88f178ce48d82b9`, session `2148760f-1a1d-4af8-8fff-e668c33a2e4b`, completed 2026-10-13T11:58:32+03:00. One request, no ingestion rejection or stale-request event observed in the evidence read.
- **8-versus-9 discrepancy.** The validator's later hand-back message listed a ninth "supporting" check (its own independent unit run: 2974 passed, 4 skipped). The persisted report contains eight checks; its limitations text states the validator's own unit run had not completed and "is not counted as evidence". The persisted report is authoritative: the accepted count is 8/8. The hand-back's unit run is recorded here only as an unverified report with no preserved artifact; it is not part of the acceptance.
- Review context note: the host froze only files inside the control project, so the reviewed workflow was the byte-identical copy `ci.yml.frozen`.
- Check 8 (R2/D2 untouched) was an inference from the file-only change surface, not a database read-back.

## C. RED/GREEN methodology

- Cause: `tests/` and `tests/integration/` share five basenames (`test_experience_benchmark_faithfulness`, `_outcome`, `_runtime`, `_security`, `_streaming`) and neither has `__init__.py`; pytest's default prepend import mode cannot import both.
- RED: `python -m pytest -o addopts= --collect-only -q -ra -p no:cacheprovider tests` → exit 2, 5 "import file mismatch" errors, 3995 tests collected.
- GREEN: unit `... --ignore=tests/integration tests` → exit 0, 2978 tests; integration `... tests/integration` → exit 0, 1154 tests.
- Inventory: 114 + 86 = 200 test modules on disk = 200 collected; 4132 split nodes = 3995 + 137 nodes of the five errored modules; 0 single-process nodes missing; node IDs identical before and after the edit.
- Environment: Python 3.12.10, pytest 9.1.1, DB URL/allow/identity variables unset, scratch `VRES_DATA_DIR`; no PostgreSQL contact.

## D. Test results

- Host-executed (author): unit suite `--ignore=tests/integration tests`: **2974 passed, 4 skipped**, exit 0. The 4 skips are Windows symlink-privilege skips (`test_claude_experiment_producer.py`, `test_experience_benchmark_foundation.py`, `test_local_secrets.py`, `test_release_boundaries.py`); they are not passes.
- Validator-observed (persisted): the collection counts and exits above were independently re-run; the unit result was relayed (see B).
- Critical ruff (`E9,F63,F7,F82` on `src tests scripts`) clean; `git diff --check` clean; YAML structure verified; a failing pytest under `bash -e` exits nonzero (probe exit 4).
- The PostgreSQL integration suite was collected but NOT executed.

## E. CI change

- One file; the single repository-wide pytest step became two separate steps: `python -m pytest -o addopts= -q -ra --ignore=tests/integration tests` and `python -m pytest -o addopts= -q -ra tests/integration`.
- No `continue-on-error`, `|| true`, `if:`, `-k` or deselection. Triggers (push to `main`, `pull_request`), the `postgres:16` service, Python 3.12, lint, import smoke, release gate and artifact upload are unchanged. If the unit step fails, the integration step does not run (intentional fail-fast).
- Working-tree file uses CRLF (`core.autocrlf=true`); the committed blob is LF and equals the frozen copy after CR removal (normalized sha256 `f4798dbf7964b597d9ea331803c7019fe5b9941e8c4ddb1225f5b309fa50c61f`).

## F. Frozen evidence

- Local ignored directory `C:\Projects\Vres-Issue-176-E7-20261006\.vres\local-tools\e7-ci-f1-collection-evidence-20261013` (not in Git).
- `MANIFEST.sha256` sha256 `28b3b6b8a807ab4388f72e946937927a8e48dafae1d416f458a3e433ddf86adb`, 32 entries, all verified OK before commit.
- Working workflow sha256 `174d6ca517eaebcf65ce6b118df64f0536899e0b8a63ed1f82da88f31dbcff54` (CRLF working copy), byte-identical to `ci.yml.frozen`; prior `ci.yml.before` sha256 begins `0cb8424a`.
- Reviewer snapshot artifacts: `ci.yml.frozen` (174d6ca5…), `INDEX_AND_ACCEPTANCE_MATRIX.md` (0c5462b7…), `ci_yml.diff` (5c315b28…), `MANIFEST.sha256`.

## G. Known limitations

- The workflow has never run on GitHub; no exact-head CI run exists for `d930adf` or any earlier R2/D2 head.
- The CI integration step will still hit the safety gate and fail until F2 provisioning exists: the R2 and G7 fixtures require `VRES_TEST_CLUSTER_SYSTEM_ID`, a provisioned run manifest and an isolated `VRES_DATA_DIR`, none of which CI supplies. The workflow is therefore NOT green and must not be reported as ready.
- Nothing here establishes PG16 parity or split-role acceptance; the R2 evidence remains PG 18.6 with a single admin role.

## H. Preserved architecture

R2 test hardening (`VAL-e61c7405f22c42c7`), D2 (`VAL-b2d40c623c3143bb`), G7 policy `176.g7.v1`, frozen migrations (047/048 unchanged), the accepted R3 interface contract, the read-only source-trust MCP surface (`source_trust_grant`/`source_trust_revoke` unregistered), G8 host-ingress restriction, and disabled positive production trust issuance are all unchanged by F1.

## I. Remaining roadmap (carry forward; nothing deleted)

F2 PostgreSQL 16 CI provisioning (guard-compatible driver, server-confirmed cluster id, manifest, data dir); PG16 parity; F3 true split-role security acceptance (real `provision_boundary`/`activate_boundary` roles at head, role-flag and membership assertions); exact-head GitHub CI (a draft PR or separately approved trigger change is needed because feature-branch pushes do not trigger CI); S2 SQL alias observation; the four Windows symlink skips; G8 host ingress; G7 Chunk 4 / E5 v6; G7 Chunk 5 legacy audit; G1/G2; B4B-v1 historical gaps; prospective B4B-v2; Chunk 6 benchmark replay; threshold freeze / held-out; E7 final release, CI and guarded merge ladder; E8/E9 and production-readiness obligations.

## J. Task continuity

`TASK-20261013-1c26893128` (F1), `TASK-20261013-e0f2073d4a` (R2, PASSED `VAL-e61c7405f22c42c7`; historical rejection `VAL-773140a7956346c8` and ingestion attempt `VATT-7a9c06e23a1a45cd` preserved) and `TASK-20261012-3201f6f610` (D2, `VAL-b2d40c623c3143bb`) all remain active and uncompleted. A new session must bind to its own host-supplied session id and must not reuse historical provider session ids.

## K. Next controlled step

Recommend, without starting it: a bounded F2 design-then-implementation task for PG16 CI provisioning. It would add a CI driver that reads `pg_control_system()` from the throwaway service, refuses control id `7685334034094099024`, calls the existing provisioning/teardown, and leaves every guard refusal intact. Needs separate authorization, RED-first tests, and one protected validation before any exact-head CI observation.

## Superseding pointer (appended 2026-10-13, control incident / C2A continuity)

Newest incident and offline-candidate state: see **PREPRODUCTION-E7-C2A-C2B-CONTROL-INCIDENT-RESUME-HANDOFF-2026-10-13.md** in this handoffs directory. The live Vres control database was inadvertently migrated from 041 to 048 by F2 migration-credential fallback; its installed runtime still supports only 041. A post-incident backup was successfully restored in isolation, but there is no pre-incident rollback. C2A built a 13-file offline schema-048 compatibility candidate with 17 focused and 1,749 unit PASS / 3 SKIP, but the candidate remains UNVALIDATED and Windows-local; the distinct F2 three-file CI driver is unsafe, BLOCKED and uncommitted. Published product head d930adfa89617067115d9538e9692945230d9630; F1/R2/D2 protected history preserved. No C2B run, C2C protected review, live runtime update, PR or merge. G8 OPEN; positive issuance DISABLED; E7 NOT release ready. All preceding historical sections are unchanged.
