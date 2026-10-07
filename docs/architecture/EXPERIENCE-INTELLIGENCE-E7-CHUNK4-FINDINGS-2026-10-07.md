# E7 Chunk 4 findings: proxy worker, outcome scoring, B5, streaming learning (2026-10-07)

Scope: the deterministic proxy worker, deterministic outcome scoring, B5 paired harmful-negative-transfer
classification, unnecessary-reuse and unattributed-regression metrics, the streaming-learning runner,
their run identities, and a focused two-clean-database proof. Not in this chunk: the security ladder,
full development replay, latency calibration, `thresholds.json`, held-out, E1/E2 gap closure,
model-worker authority, E8. No E1-E6 owner, migration or accepted semantic was changed. Poor measured
outcomes below are data about the current product; none was repaired and no mode is declared the winner.

## Proxy worker (policy `176.e7.proxy.v1`)

- Digest `09b6290010238801ed6be6afecdbfb8ba5353e820e8c586fb76d3917afefbfd5` (SHA-256 of the canonical
  policy), `max_trace_steps` 16.
- Pure stdlib (`hashlib`, `re`, `unicodedata`, `typing`). Signature `run_worker(query, request, task, pack,
  config)`. It cannot open files, reach the database or import a benchmark module.
- Separation proof (all mechanically tested): an AST test limits imports and forbids file/OS/eval names
  and the words expected, criteria, outcome, threshold, relevant, `dev_`, `adv_`, corpus, psycopg and
  anthropic in the source; a runtime spy shows the worker receives only query, request, task and the
  pack, and that no criterion id appears in its arguments; the public input is identical across the four
  modes and only the pack differs.
- Actions are chosen from the pack alone; ties break on the smallest SHA-256 of the action id; abstain and
  retry follow the symbolic semantics frozen in `scoring.json` (`retry_when` is `never` or
  `ambiguous_nonzero`).

## Changed identities (development split)

| Item | Digest |
|---|---|
| corpus | `6a6f86847388243c8e0b54916050f2a6059ac47cd4b5c1e65739c150318243bd` |
| expected_evidence.json (file sha) | `e67ea9196ee80502715f060246fa7c391a9b5648610ebc3d9a16ac7a34732351` |
| expected (canonical, run identity) | `c36a927d1773e7a463ff9632df204ba70b4c1ab5921c998f3ce068e70b088eab` |
| development bundle | `1e79d7cfc08b8b131d998f27a43e9b0be61bc33d9c6e34a905dad4c499f5a066` |
| adversarial bundle (unchanged) | `e3cad7b40164b9b5abc22f1f0db57f4f63183077d257b718898352804d688301` |
| scoring | `fb0b77d29f0efe0dee682107d6b27456f34f8503ddc52b08052fff0ce8b14038` |
| manifest | `b9eafa033932cbe481f9be6af0d792842a826f50f93199644c460016e22484aa` |

Run identities: `outcome_run` and `streaming_run`, each `RESULT_SCHEMA_VERSION` 1, `model_judge`
`not_used`, no timings, keys or ids in the digest.

## Cohort matrices

| Case | Outcome | Streaming |
|---|---|---|
| dev_memory_not_needed | executable | - |
| dev_procedure_reuse | executable | executable (t0, t1) |
| dev_temporal_refresh | - | executable (t2, t9) |
| dev_challenged_rule | - | executable (t2, t4) |
| dev_trajectory_success | OWNER_GAP | - |
| dev_trajectory_failure | OWNER_GAP | OWNER_GAP |

Gap cases ran zero owner, adapter and worker calls (spy-verified) and are `not_run_owner_gap`, never
PASS. The new-gotcha-acquisition measure therefore stays `not_run`: the failed-episode writer is an
E1/E2 owner gap.

## Outcome results, development (four modes, real owners)

`dev_memory_not_needed`: every mode succeeded (0 criterion failures) choosing `do_math` with no
memory used; B5 `no_event` for the three non-reference modes; unnecessary reuse 0/1.

`dev_procedure_reuse`: every mode failed both criteria (`activate_immediately`, no aliases used).
Cause measured in the pack: `candidate_hybrid` retrieved the right procedure alias `dev_p` (plus `dev_n`)
but its content is only the registry title and description (`supplier-account-opening: Opening a new
supplier account.`), so the worker has no step text to act on. `current_vres`, `raw_refind` and
`memory_disabled` returned empty packs. B5 for this case is `not_applicable` (reference worst possible,
2 of 2 criteria failed), so it is excluded, not counted as clean.

Aggregates (per mode, 2 executed cases): success 1/2 in all four modes; retries 0; tool-call equivalents
2; token cost total `candidate_hybrid` 69, `current_vres` 4, `raw_refind` 4, `memory_disabled` 4.
Harmful negative transfer 0/1 (one pair excluded), unattributed regression 0/1, unnecessary reuse 0/1 for
each non-reference mode; primary causes empty.

## Streaming results, development

Candidate-hybrid packs by checkpoint: procedure_reuse `[dev_p]` then `[dev_p, dev_n]`; temporal_refresh
`[dev_a, dev_old]` then `[dev_b, dev_old, dev_src]`; challenged_rule `[dev_b, dev_a]` then
`[dev_c, dev_b]`. The other three modes returned empty packs at every checkpoint.

| Measure | candidate_hybrid | current_vres | raw_refind | memory_disabled |
|---|---|---|---|---|
| learning curve, relevant coverage (all checkpoints) | 1/1 each | 0/1 each | 0/1 each | 0/1 each |
| forward transfer (procedure_reuse) | 0/2 | 0/2 | 0/2 | reference |
| retained competence | 1/1 | 0/1 | 0/1 | 0/1 |
| stale knowledge update | 1/1 | 0/1 | 0/1 | 0/1 |
| selective forgetting | 2/2 | 2/2 | 2/2 | 2/2 |
| negative transfer (harmful, unattributed) | n/a (reference worst) | n/a | n/a | reference |
| new gotcha acquisition | not run (owner gap) | | | |

Reading notes: selective forgetting is perfect for empty-pack modes only because nothing stale is
surfaced; it is not evidence of learning and must be read with coverage. Forward transfer is 0 because
the registry-description procedure content gives the worker nothing to act on, not because retrieval
missed. Each checkpoint was rebuilt from a fresh prefix under its own namespaced id; no state carried
between checkpoints, cases or splits (verified by the per-checkpoint materialization spy).

## Two-clean-database determinism

DBs `vres_e7_c4_a_d056a47e_test` (ascending order) and `vres_e7_c4_b_d056a47e_test` (descending order),
PostgreSQL 18.6, new writer roles `vres_e7_writer_ad7fe32b6d` and `vres_e7_writer_faabda26f1`. Case
results, worker traces, negative-transfer events, aggregates, streaming positions and series were
equal. Digests, A and B identical:

- outcome development `72366a3b46414223018f734a2ae13e73d83fa121ea06afb460dbca9a9db7bda1`
- streaming development `7843edefbae70569cdb5b3504f349ef75c7ea2f5e791b739149a061fc2a30e1c`

Physical runtime-key fingerprints differ (`ac0d4aba...` versus `159c5fd1...`); no runtime key, id, UUID or
timestamp appears in the deterministic bytes; both databases dropped and both temporary writer roles
removed (cleanup PASS, zero leftover roles). Timings stay outside the digest.

## Product observations (data, not repaired)

1. Procedure retrieval returns title and description only; a worker that follows steps cannot use it.
2. `current_vres` and `raw_refind` return empty packs for every outcome and streaming cohort case measured here.
3. `candidate_hybrid` surfaced the relevant alias at every executable checkpoint, at roughly 17x the
   token cost of the empty-pack modes on the outcome cohort (69 vs 4).
4. Failed-episode and successful-episode writers remain owner gaps (E1/E2).

## Correction: outcome timing (2026-10-07)

- The initial Chunk 4 implementation double-counted adapter latency in the ephemeral `run_outcome_case`
  timing field: it added the adapter's own `elapsed_ns` to an outer interval that already contained the
  adapter call plus the worker.
- `build_outcome_run` then dropped that field (`case_identity`), so deterministic results were NOT
  contaminated. Every previously reported deterministic pack, worker trace, criterion result, B5 event,
  token cost and the streaming digest remain valid and unchanged. The measured product observations
  above are unchanged.
- Outcome wall-time evidence was therefore missing, not falsely part of the protected identity.
- Repair: each executed case/mode now records `retrieval_elapsed_ns` (the adapter's own elapsed, not
  remeasured), `worker_elapsed_ns` (one interval around `run_worker` only) and `combined_elapsed_ns`
  (their integer sum). The `outcome_run` exposes them in a closed top-level `measurement_sidecar`
  (`method` `retrieval_plus_proxy_worker_v1`, `cases` only for executed cases; owner-gap cases get none).
- The sidecar is outside `result_digest`, which is computed from the deterministic body only.
  `RESULT_SCHEMA_VERSION` for the outcome run is now 2, so the outcome result digest changed; the
  development outcome digest above (`72366a3b...`) is superseded by the schema-2 digest. The retrieval,
  faithfulness and streaming schemas, the worker policy digest and every corpus/scoring/manifest
  identity are unchanged.
- Wall time is measurement evidence only, with no threshold, and is kept apart from the deterministic
  `token_cost` (pack token estimate plus tool-call equivalents). A/B equality is required for the
  deterministic body, not for timing values.
- Chunk 6 still owns the repeated Latin-square p50/p95/max latency methodology and the
  measurement-record digest.
