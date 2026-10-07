# E7 Pre-Chunk-6 Authority-Closure Addendum (frozen 2026-10-07)

Frozen BEFORE any runtime change. Starting point: HEAD `a162533066c5ae4dfcf8feaa037ee6e11eba285a`,
tree `0dffd9d17199c1de9b1be77def58190454e1c69b`, task `TASK-20261006-6cd9d80a92`.
Chunk 5 is accepted and sealed (13 PASS / 0 FAIL / 1 N/A / 6 owner_gap). Chunk 6 has NOT started.

## 1. Frozen scope

1. The six adversarial owner gaps: `adv_poisoned_trajectory`, `adv_recurrence`, `adv_participation`
   (observed owner missing) and `adv_secret_episode`, `adv_flood_burst`, `adv_varied_poison`
   (participated `episode_capture` terminal authority).
2. The six development owner-gap cases: `dev_recurring_priceexport`, `dev_gotcha_delimiter`,
   `dev_trajectory_success`, `dev_trajectory_failure`, `dev_capability_precedent`, `dev_participation`.
3. E1 v1 (`176.e1.v1`, digest `49e5d6eb17940baf5e1d9c239f9355dd8a65bab60e62e30c81787334ddda519a`,
   capture `mechanically_known_terminal_task_or_work_unit_only`) is immutable and replayable. Migration
   037 and old rows are not modified.
4. New observed-import semantics require E1 v2; `ExperienceEpisodeService.capture` keeps v1 semantics.
5. `episode_observe` uses persisted external SOURCE evidence, never caller narrative directly.
6. Participated `episode_capture` stays E1 v1 and requires genuine routed/host terminal provenance
   (real Fable routing, `fail_work_unit`, host-observed passed worker). No SQL, private routing calls,
   fabricated reports/validation/passed units/USER_INSTRUCTION.
7. Deterministic evidence and live (host-attested) evidence remain separate cohorts.
8. No benchmark thresholds are set. 9. No held-out is read. 10. No E8.
11. One additive migration 043 is permitted, only for the E1-v2 representation below.
12. Any further schema need STOPS for review (no migration 044 without a genuine RED).

## 2. E1 v2 policy (immutable)

Canonical JSON (sorted keys, compact separators, `ensure_ascii=False`):

```
{"authority":"no_promotion","capture":"external_source_observation_only","participation":"observed_only","payload":"bounded_sanitized_no_private_reasoning","policy_version":"176.e1.v2","provenance":"active_project_source_required","relations":"existing_relations_and_relation_evidence","schema_version":2,"trust":"external_untrusted_observation_only"}
```

SHA-256 policy digest: `66e11e1319dd85b6d01fc74e4ad3f2fa4a7ee9857ab5d72fe5016e781b88efa0`
(schema_version 2). v1 constants/digest remain exactly unchanged.

## 3. Migration 043 (`043_experience_observed_episode.sql`)

No new table, no backfill. `experience_episodes.task_id` becomes nullable; one named CHECK:
participated => `task_id IS NOT NULL`; observed => `project_id IS NOT NULL AND task_id IS NULL AND
work_unit_key IS NULL AND report_key IS NULL AND trust_class='external_untrusted_observation' AND
policy_version='176.e1.v2'`. Fails closed if any pre-existing `observed` row exists that does not conform.
Inserts the immutable `176.e1.v2` policy row and verifies schema/digest/policy. `episode_key` UNIQUE remains
the final race boundary.

## 4. Public owner

`ExperienceEpisodeService.observe_external_source(project_id, source_key, claimed_outcome)`.
Caller supplies only project, existing source key and closed outcome (`completed`|`failed`). The owner reads
the source independently: it must exist, belong to exactly the project, be `active`, carry
`authority_level='external_untrusted_observation'`, have at least one chunk, and pass the E1 sensitive and
hidden-reasoning protections. Company-wide sources and null/unknown authority fail closed. Payload is built
mechanically (objective = chunk content in ordinal order, outcome_status, source_keys, applicability.project_id,
failure_classification). `observed_at` is the source persistence time. Idempotency: advisory lock over
project/source/outcome plus a deterministic episode key from the identity digest; UNIQUE is the race boundary;
a changed immutable source/payload fails closed. Relation: `episode derived_from source` only; no task relation.

## 5. Benchmark mapping

`episode_observe` = `SourceService.register` + `SourceService.add_chunks` (project-local,
`authority_level=external_untrusted_observation`) + `observe_external_source`. `result` success->completed,
failure->failed. `lineage` stays a benchmark-only grouping label. Expected movement (not forced): adversarial
13/0/1/6 -> 16/0/1/3; `dev_participation` loses `observed_episode_writer_missing` but stays a gap.

## 6. Live participated cohort

Disposable `_test` DB only; one scenario task per `episode_capture` alias; task OBJECTIVE exactly the frozen
corpus objective; synthetic nature in title/project/run docs. Real Fable `routing-arbiter` route recorded via
the public host-hook path; failure episodes via `fail_work_unit`; success episodes via a real governed Sonnet
worker reaching `passed`. If real host execution cannot be launched without weakening authority, the
deterministic portion is committed and a durable resume handoff is produced; no SQL substitute.

## 7. Result kind

`authority_closure_run`, git/document artifact only, `model_judge=not_used`, physical keys only as digests.
Expected effective acceptance if all GREEN: 19 PASS / 0 FAIL / 1 N/A / 0 unresolved; wording: "All executable
and authority-bearing E7 security cases have passing evidence; second-user isolation remains not applicable
in this environment."
