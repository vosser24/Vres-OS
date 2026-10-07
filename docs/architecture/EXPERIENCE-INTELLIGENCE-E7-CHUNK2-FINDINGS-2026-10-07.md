# E7 Chunk 2 findings (retrieval layer) - 2026-10-07

Scope: issue #176 E7 Chunk 2 only. Chunk 3 is not started. No E1-E6 owner, migration,
held-out or threshold change.

## 1. Approval fixture: trusted-writer architecture

Approval-bound cases (lifecycle retire/challenge/supersede, source revoke) need an owner-checked
approval, and approvals require a persisted `USER_INSTRUCTION` event. That event is protected by the
trigger `protect_user_authority_event`: `session_user` must equal
`provenance_authority.writer_role` (`authority_key='user_event_writer'`).

In a freshly migrated disposable DB the bound writer is `vres_os_writer` while the connecting
role is `postgres`, so the boundary correctly refused the fixture.

**Rejected:** rebinding `writer_role` to `session_user` / `postgres`, or making the bootstrap
superuser the trusted writer. That would let any connecting account forge user authority and would
weaken the provenance boundary. A regression test
(`test_approval_fixture_never_trusts_the_connecting_account`) scans the runtime and the fixture for
any `writer_role = session_user|current_user|postgres` rule and for `record_event` /
`provenance_authority` references in the runtime module.

**Adopted** (mirrors the existing writer-boundary test `test_user_event_writer_boundary_journey`):
`tests/integration/e7_trusted_writer.py::trusted_test_writer`, per disposable `_test` database:

- gated by `check_approval_fixture_gate` (`_test` suffix and `VRES_ALLOW_TEST_DB=1`);
- creates `vres_e7_writer_<nonce>` `LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT` with an
  in-memory random password (never printed or written);
- grants only schema `USAGE` and `EXECUTE` on `stage_user_input`, `latest_pending_user_instruction`
  and `commit_user_inputs`; no table privileges;
- binds `user_event_writer` to that role inside the generated DB only, the trigger and migrations
  are untouched; the original binding is restored and the role dropped (`DROP OWNED`, `DROP ROLE`)
  in `finally`.

The contract chain (`APPROVAL_FIXTURE_CHAIN`) is:

1. the scenario owns a synthetic case task and session;
2. the trusted provenance-writer ingress stages synthetic benchmark user input
   (`session_prompts.stage_user_instruction`);
3. the trusted provenance-writer ingress commits it as a `USER_INSTRUCTION` event
   (`session_prompts.commit_staged_user_instruction_events`, exactly one, actor=user);
4. `ApprovalService.record_latest_user_approval` consumes that persisted instruction;
5. the target owner operation receives the returned `approval_key`.

`Repository.record_event` is not part of the chain (a regression test forbids advertising it). The
restricted writer role itself stays integration-test infrastructure and is not moved into the
production foundation. There is no direct insert into `task_events`, `approval_events` or
`user_input_observations`.

The approval is a **synthetic benchmark user-input provenance fixture**, not real user authority.

## 2. DB-free repairs retained (commit `4aeaec6`)

Near-duplicate counting, premise-awareness supporting-alias semantics, duplicate scoring after the
common budget, and retrieval policy/schema identity in the result identity. Their RED/GREEN tests
remain in `tests/test_experience_benchmark_runtime.py`.

## 3. Retrieval contract and findings from running on real owners

- **Frozen setup status and the explicit `knowledge_observe` operation.** Every benchmark
  knowledge item enters at `proposed` (`INITIAL_STATUS`), exactly as the frozen
  `OPERATION_OWNERS["knowledge_propose"]` says. `_RANK` gives proposed 0, so proposed -> proposed
  supersession is allowed, but a challenged old item (rank 1) cannot be superseded by a proposed
  successor (rank 0): the real E4 owner refuses it. The runtime does NOT repair this implicitly
  (the earlier hidden `_match_successor_maturity` helper was removed; a source-inspection test
  forbids any helper that conditionally promotes a successor). Instead the closed timeline
  vocabulary has the explicit operation `knowledge_observe`: no args, no new alias, no
  caller-supplied status, acts on an already-created knowledge alias, and maps exactly to
  `KnowledgeService.update(<runtime knowledge key>, status="observed")` (owner `KnowledgeService`,
  method `update`, translation `alias -> knowledge_key`, harness `status = observed`, no direct
  SQL; no new owner, no migration). `dev_temporal_refresh` now declares
  `t=6 knowledge_propose dev_b; t=7 knowledge_attach_source dev_b->dev_src; t=8 knowledge_observe
  dev_b; t=9 lifecycle_supersede dev_b supersedes dev_a`. Without the observe step the real owner
  rejects the supersede (PG regression test).
- **Canonical EvidencePack R.** `pack` is R: normalized, content-truncated, cut by the common token
  budget, duplicates preserved. `current_vres` starts collapsed because its frozen merge collapses
  before the budget; `memory_disabled` R is `[]`. Only `pack` and `pack_digest` are stored (no
  `raw_pack`). `score_retrieval(expected, request, pack, signals, scoring)` derives the
  first-occurrence alias order for top-k, recall, precision, coverage and irrelevant rate, and uses R
  itself for exact/near/combined duplicate rates, the token estimate, the digest and worker input.
  `RESULT_SCHEMA_VERSION` is 2 and is bound in the retrieval identity.
- **Supporting aliases follow R.** `signals.supporting_aliases` is intersected with the aliases in R
  after the budget. `premise_mismatch`, `conflict_flagged` and abstention stay separate owner
  diagnostics.
- **Owner-maximum native limits.** raw_refind `chunk_search` 50, current knowledge `search` 50,
  current procedure `find_matches` 20; candidate_hybrid keeps the released E5 budgets. The only
  final cut is the common token budget; there is no item-count limit.
- **Tie order.** The runtime applies public native rank, then alias, and assigns ranks 1..n:
  raw_refind `rank DESC, alias`; current knowledge `rank DESC, confidence DESC NULLS LAST, alias`;
  current procedure `score DESC, alias` (before the interleave; no `updated_at`/`accepted_at`);
  candidate_hybrid keeps the E5 tie-prefix -> alias normalization.
- **`native_owner_e5_pre_adapter_tie_selection_limitation`.** E5 `select_raw` can pick a different
  tied member when a native budget cuts through a physical-key tie before the benchmark sees it.
  E5 is not modified. If later replay shows instability, Chunk 5 starts with a RED and hardens the
  owner there. None of the committed subset hits it.
- **`declared_premise_shape_not_natively_comparable_by_e5`.** The corpus `declared_premises` is a
  list of public free-text statements, and every adapter receives that public field unchanged
  through `public_input`. E5's native `premises` request field requires a structured `{key: value}`
  mapping, and no deterministic, contract-approved mapping exists from the free-text corpus
  representation. CandidateHybrid therefore does NOT populate E5 `premises` from the free-text
  list, and no semantic parser is fabricated. Premise-mismatch diagnostics for this corpus shape are
  consequently unavailable (miss-capable). The corpus is not modified to improve premise-awareness.
- **Native retrieval differences vs the frozen expectations** (reported, not hidden): raw-refind
  eligibility and content differ from knowledge-owned retrieval; knowledge items are richer than
  procedures; candidate-hybrid applies hard gates; conflict diagnostics and the abstention signal are
  derived, not native; native search is lexical AND-match; role/flag support follows a documented
  rule.

## 4. Focused PostgreSQL results (PG 18.6)

`tests/integration/test_experience_benchmark_runtime.py`: **18 passed in each of two clean DBs**
(none xfailed; includes the two `dev_temporal_refresh` explicit-observe tests), covering memory_disabled, raw source chunk, raw knowledge-owned chunk, current_vres
knowledge and procedure, candidate_hybrid, project isolation, revocation, lifecycle challenge, the
approval fixture, ordinary-connection forgery refusal, writer least privilege (not superuser /
CREATEDB / CREATEROLE, no task_events mutation), one-approval-one-target isolation, OWNER_GAP zero
owner calls, candidate_hybrid READ ONLY and deterministic identities. `record_latest_user_approval`
consumes the persisted event. DB-free runtime tests: 22 passed in both runs.

## 5. Two-clean-DB determinism proof

DBs `vres_e7_c2_a_2851064e_test` and `vres_e7_c2_b_2851064e_test`; cases `dev_static_port`,
`dev_source_revoked` (approval-bound), `dev_procedure_reuse`, `dev_temporal_refresh`
(approval-bound, now executing the explicit `knowledge_observe`); run A in ascending case order, B in descending.

- Result digest in both: `5a1ee7b2c88e2eb51d445e026edf028c3b6e23ee90e0bffbe0a470982cfb9136` (changed from the previous
  `effba23f...` only because the development corpus/bundle identity changed).
- EvidencePacks, retrieval metrics, case results and aggregates equal; 4 non-empty packs per DB.
- Physical key fingerprint (runtime/DB keys) **differs** between the DBs; the result bytes contain
  no physical key, DB id or wall-clock timestamp (leak scan empty). Latency is outside the digest.
- Limit of the proof: the DBs' minimum integer ids are both 1 (fresh sequences), so the
  physical-difference evidence is the key fingerprint, not integer ids.

## 6. Cleanup proof

Both DBs dropped, the baseline-diffed `vres_e7_writer_%` role set is empty after the run (temp
roles of this run: `vres_e7_writer_ec9d47804a`, `vres_e7_writer_f0bb1c0700`), canonical DB
untouched (bootstrap used a CREATEDB role, only `_test` databases touched).

## 7. Owner-gap matrix (unchanged)

Development: 18 executable / 6 OWNER_GAP. Adversarial: 14 executable / 6 OWNER_GAP.
Gap reasons: `observed_episode_writer_missing`,
`failed_episode_requires_host_observed_routed_work_unit`. Corpus manifest
`e227221048bbda62d93f8cfe015445e8616ef4b1ab0cda645a94d9a3b614ac81` ok.

Changed identities (only `dev_temporal_refresh` changed): development `corpus.jsonl` file digest
`177b439f...0377` -> `bbf2a240a291bd5e1790fcedc247ca569253da8aace6e80ddde9196da83ba034`; development
bundle digest `3670226e...be0a` -> `ca06efc6531adf5d5294188d90ea656954cc5b940c0946c9847a14476130d7ea`; manifest digest -> above. Unchanged: `expected_evidence.json`, adversarial bundle, `scoring.json` (`9e336646694ab0b87d357506c2be1fb08f7face76050b42e4f635a9b7b30c9c8`); no `thresholds.json`, no held-out.

## 8. Not done (by instruction)

Full PG suite, release gate, protected validation, installed-runtime smoke, held-out and threshold
calibration. Chunk 3 is not started. Chunk 2 is not accepted.
