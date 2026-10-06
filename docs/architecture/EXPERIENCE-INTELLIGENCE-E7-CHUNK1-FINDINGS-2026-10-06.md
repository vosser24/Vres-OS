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
`dev_trajectory_success` uses the successful precedent episode itself as evidence.

## F1c. `passed` work units are host-hook-only (contract ambiguity)

The requested "success -> work unit passed" mapping cannot be run: `passed` is written only by the
host SubagentStop ingress (`RoutingService.record_worker_from_hook`), which needs transcript-attested
model evidence. The public non-host terminal path is `OrchestrationService.fail_work_unit`.
Decision: failure -> failed work unit; success without capability -> synthetic task completed via
`Repository.complete_task` + task-level capture; success with a capability is
`OWNER_GAP:work_unit_passed_host_hook_only` (`dev_capability_precedent`).

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

| split | executable | owner gap | owner-gap cases (reason) |
|---|---|---|---|
| development | 22 | 2 | dev_capability_precedent (work_unit_passed_host_hook_only), dev_participation (observed_episode_writer_missing) |
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
