# E7 Chunk 3 findings: operation-level memory-faithfulness harness (2026-10-07)

Scope: only the faithfulness harness. No E1-E6 owner change, no migration, no outcome worker, no
streaming runner, no security ladder, no thresholds, no held-out, no E8.

## What was built
- `src/vres_os/experience_benchmark_faithfulness.py`: DB-free scorer. Six metrics (source-support
  precision, omission rate, unsupported-addition rate, dedup correctness, conflict recognition,
  temporal-update correctness) as exact rationals, plus the prior-memory/corruption invariant as a
  separate PASS/FAIL (never averaged; violations report alias/op/t). Claim equivalence is the frozen
  `nfc_collapse_whitespace_exact`. Results kind `faithfulness_run`, `RESULT_SCHEMA_VERSION=1`;
  identity = bundle digests + scoring digest + policy identity (E1/E2 policy digests, E4 version,
  equivalence); no keys, timestamps or latency. Aggregation is per split only (micro/macro, N/A
  excluded); owner-gap cases are counted separately and never PASS.
- Runtime (`experience_benchmark_runtime.py`): `materialize_traced` emits one row per corpus
  timeline operation with public `KnowledgeService.get` snapshots (closed shape, aliases only; an
  unmapped reference fails closed without echoing the key); `run_faithfulness_case`,
  `run_faithfulness`. Untraced `materialize` makes no snapshot reads.
- Annotation correction (3B): dev_dynamic_export claim/source-fact text and dev_temporal_refresh
  source-fact text now equal the canonical corpus proposition. Expected-evidence file digest
  `d908894e...5a1ee` -> `a23097a7489e064175035034938241f283dab7b0c6e50c386336cda33adbf742`;
  development bundle `ca06efc6...d7ea` -> `eb8b2f424363f4c18c16a7b3da8522cd774121854b03748c1c8a2f07734ac7ed`;
  manifest `e2272210...ac81` -> `66c52fe0ce37ebfc635f1789687e58287db622b65ba3cae1b3f70a7265c2b415`.
  Scoring digest unchanged `9e336646694ab0b87d357506c2be1fb08f7face76050b42e4f635a9b7b30c9c8`.

## Cohort
| case | split | status |
|---|---|---|
| dev_dynamic_export | development | executed (real owners) |
| dev_near_duplicate | development | executed |
| dev_temporal_refresh | development | executed |
| dev_recurring_priceexport | development | not_run_owner_gap (successful_episode_requires_protected_or_host_attested_terminal_state) |
| adv_challenge_flag | adversarial | executed |
| adv_no_rewrite | adversarial | executed |
| adv_secret_episode | adversarial | not_run_owner_gap (failed_episode_requires_host_observed_routed_work_unit) |

E1/E2-dependent coverage stays `not_run`; no E1/E2 PASS is claimed.

## Measured outcomes (current owners; data, not defects to patch here)
- dev_dynamic_export (invariant PASS, now a real comparison; see Correction): source-support precision 0/1 (**observed failure**: dev_b has no evidence
  edge); omission 0/1 omitted; unsupported additions 0/1; conflict 1/1; temporal 1/1.
- dev_near_duplicate: dedup correctness 0/1 (**observed failure**: near-duplicate proposals stay
  independent live items; no merge by the current owners).
- dev_temporal_refresh: support 1/1, omission 0/1, additions 0/1, temporal 1/1, conflict 1/1;
  dev_a superseded_by dev_b, dev_b observed.
- adv_challenge_flag: conflict 1/1, invariant PASS. adv_no_rewrite: invariant PASS (no claim metrics).
- Aggregates (invariant semantics corrected below): development source-support micro 1/2, dedup 0/1, conflict 1/1, temporal 1/1,
  omission 0/1, additions 0/1; invariant PASS (1 case). Adversarial: conflict 1/1; invariant PASS (2).
- Result digests (two clean DBs, opposite execution order): development
  `c90eb5be88bfa759893327a636fa08012387f76a51aa884bf3a40096b05a0ea3` (after the correction; the first commit's digest `4227230f...` is superseded), adversarial
  `896c678495a57c0c4ab3fef97ad338ca4a5482e7f07aaab4ba7159b3363e21d1` (identical across DBs).

## Proof
Focused PG: `tests/integration/test_experience_benchmark_faithfulness.py` 10 passed in each of two
fresh DBs `vres_e7_c3_a_5f79b237_test` / `vres_e7_c3_b_5f79b237_test` (PG 18.6; 10 tests after the correction); temp writer roles
`vres_e7_writer_87d8b96a62`, `vres_e7_writer_678c353d7a`, removed; DBs dropped. Physical runtime-key
fingerprints differ; no keys/UUIDs/timestamps in result bytes. Not run: full PG suite, release gate,
held-out, thresholds.

## Correction: vacuous corruption-invariant PASS (found in review of f057bc73)
- The first Chunk 3 commit reported a development invariant PASS for `dev_dynamic_export`. That PASS
  was **vacuous**: its protected alias `dev_d` was created as the *last* timeline step, so no later
  operation existed to compare it against, and `score_invariant` returned PASS on "no violation found".
- The scorer now refuses a zero-comparison PASS. Per protected alias the baseline is its first
  appearance (creation is not a comparison); each later operation that is not authorised to change
  that alias is one comparison. Authorised = the step's own alias, plus `args.supersedes` for
  `knowledge_supersede` / `lifecycle_supersede` only (a plain reference no longer suppresses
  detection). Case level: any violation -> FAIL; no violation and >= 1 comparison across the
  protected set -> PASS; zero comparisons -> NOT_EVALUATED. No numeric threshold; the serialized
  invariant shape is unchanged (status + violations), so `RESULT_SCHEMA_VERSION` stays 1.
- RED first: 3 new tests failed before the scorer change (final-step creation PASS, only-authorised
  ops PASS, plain reference suppressing corruption), then passed.
- `dev_dynamic_export` timeline reordered, no content change: `dev_src`, `dev_a`, `dev_d`, `dev_b`,
  `dev_a<-dev_b` supersede. A corpus test now requires every executable case with a protected set to
  have a real post-creation comparison opportunity.
- Real-owner proof: `dev_d` exists before `dev_b`; its snapshot is identical after `dev_b` creation
  and after the supersession; invariant PASS from two genuine comparisons.
- Identities: development `corpus.jsonl` `bbf2a240...` -> `956a031da88b33be516d6e1f2486d055cd95f425ba3038b5fb9a181fa990459d`;
  development bundle `eb8b2f42...` -> `3306fa15b4fc1dc6a541b235c552c7117dbca089c1caa867b22070c11523fcea`;
  manifest `66c52fe0...` -> `57f73ba59d348ab58c33968a9db8e93fd695d8973e3aead46ab267933136e8b4`.
  Unchanged: `expected_evidence.json` (`a23097a7...`), scoring digest `9e336646...`, adversarial bundle
  `e3cad7b4...`, adversarial faithfulness digest `896c6784...`.
- Unchanged measured owner outcomes: `dev_dynamic_export` source-support 0/1; `dev_near_duplicate`
  dedup 0/1. Development invariant aggregate: 1 case evaluated (`dev_dynamic_export`), PASS.
