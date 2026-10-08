# E7 Boundary 4A — live participated development cohort: findings (2026-10-08)

Status: the six development cases were run live against a disposable fixture database. This is Boundary 4A
only. Protected validation, release readiness, Chunk 6, held-out, threshold calibration, the adversarial
live cohort and Boundary 4B are **not** claimed and were **not** started.
Baseline: HEAD and origin `3ceae86aedfabaf949f231a5c956803e7d66cadd`. No product code was changed.
Artifact: `benchmarks/experience_e7/results/authority_closure_development_live.json`
(`kind=authority_closure_run`, `phase=development_participated`, `model_judge=not_used`,
sha256 `03b3c9e2c798ccdcabf53a7d1c6fe63e176662e796bae84c0fab146a2edfb661`).

## 1. Scope

In: the six development cases, nine participated E1-v1 captures, one observed E1-v2 episode, and the frozen E2
consolidations. Out: the three adversarial owner gaps (`adv_secret_episode`, `adv_flood_burst`,
`adv_varied_poison`), the other adversarial cases, Boundary-3 protected validation, Chunk 6, held-out,
calibration, E8. The development corpus classification (18 executable, 6 OWNER_GAP) and the owner map are unchanged.
`TASK-20261006-6cd9d80a92` belongs to the canonical control database and was not imported, recreated or
checkpointed in the fixture.

## 2. Fixture topology

A disposable `_test` PostgreSQL database with its own isolated data directory, three distinct non-superuser
role identities, all migrations through 046, one project, and a single open provider session. The launcher owns
fixture, role and data-directory cleanup; nothing was dropped from inside the live session. Physical database
names, DSNs, role passwords and temp paths are deliberately absent from the artifact and this document.

## 3. Startup proof

Run before any live agent and all PASS: configured and ready; test-database opt-in; database name ends in
`_test` and equals the launcher-declared name; isolated data directory; three distinct non-superuser
identities against the same database; migration head `046_experience_retrieval_policy_v5.sql`; one project;
exactly one open session for the real provider session id; git HEAD equals origin and the tree was clean.

## 4. Cases and captures

| Case | Captures | Follow-up |
|---|---|---|
| `dev_recurring_priceexport` | e1, e2 passed | recurrence consolidation |
| `dev_gotcha_delimiter` | e1, e2 failed | failure_gotcha consolidation |
| `dev_trajectory_success` | e passed | none |
| `dev_trajectory_failure` | e failed | failure_gotcha consolidation |
| `dev_capability_precedent` | dev_e, dev_o passed | none |
| `dev_participation` | dev_own passed (participated) | plus observed `dev_seen` |

Nine E1-v1 (`176.e1.v1`) participated captures, all `trusted_project_source`; six passed work units and
three failed. Every capture used one fresh synthetic task whose objective equals the frozen corpus objective
exactly (verified both on the task and in the episode payload); the synthetic marker is in the title only.
No row in `routing_requests`, `work_units`, `worker_runs`, `task_events` or terminal state was inserted or mutated directly.

## 5. Fable route authority

Each capture ran the full chain: repository task, real provider session, `bind_session`, `CapabilityService`,
`discover`, `prepare`, the real `vres-os:routing-arbiter`, route recorded by the host hook, `result`,
`record_plan`, `record_work_graph` (one bounded unit), `ready_work`, `start_work_unit`. Nine routes were
recorded with host-observed model `claude-fable-5-1`. All nine decisions chose a Sonnet execution tier.
The first arbiter attempt used a paraphrased prompt and invented the role `forecasting-analyst`; the hook
rejected it fail-closed and the route stayed `pending`. This was classified as harness misuse (A), retried
with the exact request, and no product code changed. The remaining eight routed on the first attempt.
The binding of one session to one task at a time forced serial execution and a rebind before each step.

## 6. Success worker authority

Six real `vres-os:sonnet-expert` workers ran through the namespaced plugin mechanism. Host-observed model
`claude-sonnet-5-5`; the SubagentStop hook persisted each result (it was never invoked manually); each unit became
`passed` with a report and one attempt before capture. Workers claimed their own unit start.

## 7. Failed work-unit authority

Three units were started by the harness and failed through the public `fail_work_unit`; each was read back as
`failed` before `capture`. The failure episodes carry `outcome_status=failed` and no worker was run.

## 8. dev_participation distinction

- `dev_own`: E1 v1, participated, trusted project authority, task-bound, passed work unit, real Fable route
  and real Sonnet worker. Its route assurance was **protected**; protected validation was not run here
  (outside 4A) and is not claimed.
- `dev_seen`: E1 v2 (`176.e1.v2`), `observed`, `external_untrusted_observation`, built by `observe_external_source`
  from a project-local active source of the same authority level. `task_id`, `work_unit_key` and `report_key`
  are all null, the only relation is `derived_from source`, and no work unit exists for it. It was not converted
  to participated.

## 9. Capability precedent

Through the real `CapabilityService`, the two successful captures preserve exactly `cap_forecasting`
(`dev_e`) and `cap_leadtime` (`dev_o`) as `uses capability` relations. No capability SQL was used.

## 10. E2 outcomes (policy `176.e2.v1`, no threshold set)

| Case | Verdict | Reason |
|---|---|---|
| `dev_recurring_priceexport` | quarantined | `recurrence_threshold_uncalibrated` |
| `dev_gotcha_delimiter` | accepted | `literal_support_verified` |
| `dev_trajectory_failure` | accepted | `literal_support_verified` |

`RECURRENCE_MIN_TASKS` was not set. The quarantine is valid evidence of the policy as frozen; the cohort was not tuned to avoid it.

## 11. Legitimate gaps

- The recurrence case is quarantined pending calibration, which is out of scope.
- `dev_own` is protected-assurance without protected validation.
- Adversarial cohort, Boundary 4B, Chunk 6, held-out, calibration and E8 are not run.
- Host evidence covers this single run in one fixture; it is not a repeated or independent measurement.

## 12. Artifact digest and focused validation

The artifact holds aliases, digests of episode keys, models, statuses and counts only. A leak scan found no physical task,
episode, plan, work-unit or source keys, DSNs, passwords, session ids or machine paths. Counts: 9 Fable routes,
6 Sonnet host-observed workers, 6 passed units, 3 failed units. Focused test and static results are reported with
the hand-off, not asserted here.
