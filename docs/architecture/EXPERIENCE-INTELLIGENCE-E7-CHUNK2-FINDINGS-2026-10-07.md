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

## 3. Findings from running on real owners

- **Maturity convention.** `check_supersession` rejects a replacement less mature than the
  superseded item (`_RANK`), so every benchmark item enters at `observed`
  (`INITIAL_STATUS`), the lowest status keeping all frozen cases executable.
- **E5 native tie-break nondeterminism.** E5 ranking ties end in the physical `chunk_key` /
  `memory_key` (random uuids), so identical corpora gave different order across DBs. The runtime
  now orders items tied on every E5 ranking signal (authority tier, scope rank, family and
  capability match, fusion, recency) by alias, permuting only runs with an identical prefix.
  Caveat: tied raw chunks inside `select_raw` can still change *selection* if a per-source or total
  budget cuts through a tie; none of the committed subset hits this.
- **Native retrieval differences vs the frozen expectations** (reported, not hidden): raw-refind
  eligibility and content differ from knowledge-owned retrieval; knowledge items are richer than
  procedures; candidate-hybrid applies hard gates; the premise signal is free text, so
  `premise_mismatch` is always empty for key->value premises; conflict diagnostics and the
  abstention signal are derived, not native; native search is lexical AND-match; role/flag support
  follows a documented rule.

## 4. Focused PostgreSQL results (PG 18.6)

`tests/integration/test_experience_benchmark_runtime.py`: **16 passed in each of two clean DBs**
(none xfailed), covering memory_disabled, raw source chunk, raw knowledge-owned chunk, current_vres
knowledge and procedure, candidate_hybrid, project isolation, revocation, lifecycle challenge, the
approval fixture, ordinary-connection forgery refusal, writer least privilege (not superuser /
CREATEDB / CREATEROLE, no task_events mutation), one-approval-one-target isolation, OWNER_GAP zero
owner calls, candidate_hybrid READ ONLY and deterministic identities. `record_latest_user_approval`
consumes the persisted event. DB-free runtime tests: 13 passed in both runs; all DB-free benchmark
tests: 616 passed, 1 skipped.

## 5. Two-clean-DB determinism proof

DBs `vres_e7_c2_a_e823b3bb_test` and `vres_e7_c2_b_e823b3bb_test`; cases `dev_static_port`,
`dev_source_revoked` (approval-bound), `dev_procedure_reuse`, `dev_temporal_refresh`
(approval-bound); run A in ascending case order, B in descending.

- Result digest in both: `df810ef77e9627b5b2d3738e97a22a3ddd25e410809db62657bdd90634e4e022`.
- EvidencePacks, retrieval metrics, case results and aggregates equal; 4 non-empty packs per DB.
- Physical key fingerprint (runtime/DB keys) **differs** between the DBs; the result bytes contain
  no physical key, DB id or wall-clock timestamp (leak scan empty). Latency is outside the digest.
- Limit of the proof: the DBs' minimum integer ids are both 1 (fresh sequences), so the
  physical-difference evidence is the key fingerprint, not integer ids.

## 6. Cleanup proof

Both DBs dropped, the baseline-diffed `vres_e7_writer_%` role set is empty after the run (temp
roles of this run: `vres_e7_writer_11fbbaeccf`, `vres_e7_writer_7a316e6fbe`), canonical DB
untouched (bootstrap used a CREATEDB role, only `_test` databases touched).

## 7. Owner-gap matrix (unchanged)

Development: 18 executable / 6 OWNER_GAP. Adversarial: 14 executable / 6 OWNER_GAP.
Gap reasons: `observed_episode_writer_missing`,
`failed_episode_requires_host_observed_routed_work_unit`. Corpus manifest
`9558edb2bc61a691f2afdce2c9d444b01e23d069bfdb5a56b1e6a6798391edb7` ok.

## 8. Not done (by instruction)

Full PG suite, release gate, protected validation, installed-runtime smoke, held-out and threshold
calibration. Chunk 3 is not started. Chunk 2 is not accepted.
