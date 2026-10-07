# E7 Chunk 1 — repair findings (2026-10-06)

Scope: Chunk 1 execution-fidelity repair (review Message G, R1–R11). Benchmark data/config,
the benchmark foundation/schema, Chunk 1 tests/audit and this document only. No E1–E6 runtime
owner was modified. Chunk 2 has not started.

## F1. E7 BLOCKER — NO PUBLIC OBSERVED-EPISODE WRITER EXISTS

- The E1 episode table supports `participation = observed`.
- The public E1 capture path (`ExperienceEpisodeService.capture`) is participated-only.
- No public owner entry exists for observed or imported episodes; direct SQL is forbidden.
- This is an **E7 blocker**, not an issue outside E7: the cases that need observed episodes
  (`dev_participation`, `adv_poisoned_trajectory`, `adv_recurrence`, `adv_participation`) test
  mandatory memory-security criteria.
- Chunk 2 may run these cases only as `not_run_owner_gap`: excluded from every denominator, never
  PASS, with the count and reason recorded in every run record.
- Before FINAL E7 acceptance the gap must be resolved by a governed runtime-owner tranche;
  otherwise the mandatory E7 criteria stay `not_run` and E7 cannot pass.
- Not solved here; no SQL and no E1-E6 owner change.

## F1b. `validated_runtime_fixture = unavailable_by_design`

A `validated_runtime` episode needs real protected-validator provenance. The benchmark must not
forge it, so `validation="passed"` and `validated_novel` consolidations are removed from the
corpus (a `validated_novel` step is rejected). This is distinct from the observed-writer gap.
`dev_trajectory_success` uses the successful precedent episode itself as evidence (OWNER_GAP, see F1c).

## F1c. Successful episodes are an OWNER GAP (F4 ruling, supersedes the earlier mapping)

`Repository.complete_task()` requires `task_state.validation_status == "passed"`, i.e. the real
protected validation chain. A work unit becomes `passed` only through host-observed worker ingress
(`RoutingService.record_worker_from_hook`) after transcript/model/acceptance verification. The
benchmark must manufacture neither authority: no manual validation status, no fabricated validation
request/report, no fabricated passed work unit.

- `episode_capture(result="failure")` is EXECUTABLE: synthetic unfinished scenario task, real
  governed work unit started normally, `OrchestrationService.fail_work_unit`, then
  `capture(task_key, work_unit_key=...)` (participated, failed, `trusted_project_source`).
- `episode_capture(result="success")`, with or without a capability, is
  `OWNER_GAP:successful_episode_requires_protected_or_host_attested_terminal_state`. A capability
  does not change the authority rule. No normal deterministic replay may clear this gap.
- `episode_observe` adds `observed_episode_writer_missing`. A case may carry several reasons
  (comma-joined, sorted).
- A task-level `validated_runtime` success needs genuine protected-validator provenance;
  `validated_runtime_fixture = unavailable_by_design`.

### Final-acceptance closure strategy (documented, not implemented)

Later E7 closes the gap either by governed runtime-owner work (another provenance-safe public
episode entry) or by a small explicit LIVE protected acceptance cohort (real protected validation
for task-level success and/or real host-attested work-unit completion), kept separate from
deterministic calibration and never faked. Until then the dependent criteria stay `not_run_owner_gap`
and contribute no PASS.

### Corpus consequences (every success episode reviewed)

- Kept, whole case OWNER_GAP (the case truly needs a successful episode): `dev_recurring_priceexport`,
  `dev_trajectory_success`, `dev_capability_precedent`, `dev_participation` (also observed).
- Rewritten to an already-supported owner: `dev_recurring_recount` (accepted procedure
  `recount-before-adjusting` is the relevant evidence; failed episode stays irrelevant),
  `adv_reset_injection` (trusted knowledge replaces the success episode),
  `adv_secret_episode` (failed aborted-deployment episode still carries the canary).
- E2 recurrence is uncalibrated, so recurrence is not used as a substitute for success evidence.

## F2. Synthetic benchmark approval fixture

Approval-bound ops (`procedure_accept`, `lifecycle_retire|reinstate|challenge|supersede|refresh`,
`source_revoke`) require the closed case field `approval_fixture: true`. Public chain, no SQL:
synthetic case task -> `Repository.record_event(USER_INSTRUCTION)` ->
`ApprovalService.record_latest_user_approval` -> returned `approval_key` to the owner op.
Subjects: lifecycle `e4_lifecycle` + `approval_subject(...)`; source revoke `e4_lifecycle` +
`revoke_source:<source key>`; procedure accept `procedure_accept` + procedure key.
Safety gates: fresh disposable DB whose name ends `_test`, `VRES_ALLOW_TEST_DB=1`, never the
canonical DB, never a user approval, excluded from measured evidence, never auto-created.

## F2b. Executable vs owner-gap matrix

| split | executable | owner gap | owner-gap cases (reasons) |
|---|---|---|---|
| development | 20 | 4 | dev_recurring_priceexport, dev_trajectory_success, dev_capability_precedent (successful_episode_requires_protected_or_host_attested_terminal_state); dev_participation (observed_episode_writer_missing + the success reason) |
| adversarial | 17 | 3 | adv_poisoned_trajectory, adv_recurrence, adv_participation (observed_episode_writer_missing) |

Approval-bound ops are EXECUTABLE only with the fixture. Recurrence is uncalibrated in E2
(`recurrence_threshold_uncalibrated`): recurrence consolidations are transition results, expected
quarantined, never labelled retrievable; `RECURRENCE_MIN_TASKS` is not calibrated.

## F3. Repairs (Message G)

- R1: `scoring.json` carries closed, versioned `metric_semantics` (no formulas/thresholds).
- R2: immutable op→owner map `OPERATION_OWNERS`, alias-kind/order ledger.
- R3: `experience_consolidate` matches E2 (polarity, trigger, subject_key, title, statement,
  1..10 evidence with episode alias + RFC-6901 pointer + literal quote).
- R5: `knowledge_attach_source` → `SourceService.attach_evidence`; revocation requires an
  explicit source→knowledge edge, attached before revocation.
- R6: closed `knowledge_type`; `dev_temporal_refresh` attaches a source before refresh.
- R7: security cases 6 (baseline + `procedure_candidate`), 12 (flood through E2),
  13 (varied poison through E2, one lineage), 17 (`lifecycle_challenge` before retrieval).
- R8 accepted unchanged: `capability` arg, `<<CANARY_1>>`, the 19 security assertion names.
