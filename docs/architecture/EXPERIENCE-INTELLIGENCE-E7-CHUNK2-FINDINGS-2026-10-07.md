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

The runtime stages and commits the instruction through the existing production wrapper
(`session_prompts.stage_user_instruction` / `commit_staged_user_instruction_events`) on the
restricted writer connection, requires exactly one committed `USER_INSTRUCTION` (actor=user), then
calls `ApprovalService.record_latest_user_approval` and passes the key to the owners. There is no
direct insert into `task_events`, `approval_events` or `user_input_observations`.

The approval is a **synthetic benchmark user-input provenance fixture**, not real user authority.

## 2. DB-free repairs retained (commit `4aeaec6`)

Near-duplicate counting, premise-awareness supporting-alias semantics, duplicate scoring after the
common budget, and retrieval policy/schema identity in the result identity. Their RED/GREEN tests
remain in `tests/test_experience_benchmark_runtime.py`.

## 3. Retrieval contract and findings from running on real owners

- **Frozen setup status.** Every benchmark knowledge item enters at `proposed`
  (`INITIAL_STATUS`), exactly as the frozen `OPERATION_OWNERS["knowledge_propose"]` says. `_RANK`
  gives proposed 0, so proposed -> proposed supersession is allowed. Only the exact frozen case that
  *challenges* the old item first (`dev_temporal_refresh`: challenged = rank 1) needs its successor
  at rank >= 1: that successor takes the single legal public-owner step proposed -> observed
  (`KnowledgeService.update`) immediately before the approved supersede. No global maturity raise.
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
- **`declared_premise_shape_not_natively_comparable_by_e5`.** `public_input(case)` carries
  `declared_premises` unchanged to every adapter; E5 consumes free text, and no semantic parser or
  fabricated key/value premise is added. `premise_mismatch` is therefore empty for key->value
  premises in candidate_hybrid. The corpus is unchanged.
- **Native retrieval differences vs the frozen expectations** (reported, not hidden): raw-refind
  eligibility and content differ from knowledge-owned retrieval; knowledge items are richer than
  procedures; candidate-hybrid applies hard gates; conflict diagnostics and the abstention signal are
  derived, not native; native search is lexical AND-match; role/flag support follows a documented
  rule.

## 4. Focused PostgreSQL results (PG 18.6)

`tests/integration/test_experience_benchmark_runtime.py`: **16 passed in each of two clean DBs**
(none xfailed), covering memory_disabled, raw source chunk, raw knowledge-owned chunk, current_vres
knowledge and procedure, candidate_hybrid, project isolation, revocation, lifecycle challenge, the
approval fixture, ordinary-connection forgery refusal, writer least privilege (not superuser /
CREATEDB / CREATEROLE, no task_events mutation), one-approval-one-target isolation, OWNER_GAP zero
owner calls, candidate_hybrid READ ONLY and deterministic identities. `record_latest_user_approval`
consumes the persisted event. DB-free runtime tests: 21 passed in both runs (retrieval: 50).

## 5. Two-clean-DB determinism proof

DBs `vres_e7_c2_a_7122e1db_test` and `vres_e7_c2_b_7122e1db_test`; cases `dev_static_port`,
`dev_source_revoked` (approval-bound), `dev_procedure_reuse`, `dev_temporal_refresh`
(approval-bound); run A in ascending case order, B in descending.

- Result digest in both: `effba23f7405bf9d5b6be62d07835ad58c1481a64b1e47319041a7565f665b35`.
- EvidencePacks, retrieval metrics, case results and aggregates equal; 4 non-empty packs per DB.
- Physical key fingerprint (runtime/DB keys) **differs** between the DBs; the result bytes contain
  no physical key, DB id or wall-clock timestamp (leak scan empty). Latency is outside the digest.
- Limit of the proof: the DBs' minimum integer ids are both 1 (fresh sequences), so the
  physical-difference evidence is the key fingerprint, not integer ids.

## 6. Cleanup proof

Both DBs dropped, the baseline-diffed `vres_e7_writer_%` role set is empty after the run (temp
roles of this run: `vres_e7_writer_cdaba879e2`, `vres_e7_writer_b6f02db1eb`), canonical DB
untouched (bootstrap used a CREATEDB role, only `_test` databases touched).

## 7. Owner-gap matrix (unchanged)

Development: 18 executable / 6 OWNER_GAP. Adversarial: 14 executable / 6 OWNER_GAP.
Gap reasons: `observed_episode_writer_missing`,
`failed_episode_requires_host_observed_routed_work_unit`. Corpus manifest
`9558edb2bc61a691f2afdce2c9d444b01e23d069bfdb5a56b1e6a6798391edb7` ok.

## 8. Not done (by instruction)

Full PG suite, release gate, protected validation, installed-runtime smoke, held-out and threshold
calibration. Chunk 3 is not started. Chunk 2 is not accepted.
