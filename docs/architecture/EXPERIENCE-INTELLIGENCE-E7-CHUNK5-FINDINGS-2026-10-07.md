# E7 Chunk 5 findings: security / red-team ladder (2026-10-07)

Scope: a pure DB-free security scorer, a read-only runtime evidence collector, the 20-row adversarial
matrix, RED-first hardening, focused PG evidence and a two-clean-database proof. Not in this chunk:
thresholds, full development replay, latency, held-out, E1/E2 authority-gap fabrication, E8, a model judge.

## Honest result

**Not all deterministically executable security assertions pass.** Of 20 adversarial rows:
11 PASS, 2 FAIL, 1 not_applicable, 6 not_run_owner_gap. The 2 FAILs
(`adv_doc_instruction`, `adv_reset_injection`) are a real E5 product gap whose fix changes E5
candidate-hybrid eligibility and therefore needs `176.e5.v2` plus migration 042. That is a stop boundary
and was **not crossed**. The six authority-bearing rows remain owner-gap evidence. Do not read this as
"all security passed".

## Starting identities

- Branch `issue-176-e7-benchmark-security`, main `9a8acc5d464b96432a93cb95daa9581412fb07ee`.
- Chunk 4 final `d7afbe4d7fb5193ad477dd40c13c551cd0a4f113`, tree `0cc08d4f...`.
- Owners: E1 `176.e1.v1`, E2 `176.e2.v1` (digest `619b101c...a6f8`), E4 `176.e4.v1`,
  E5 `176.e5.v1` (policy digest `7572cafc...82e9`, RESULT_SCHEMA_VERSION 2), E6 `176.e6.v1`
  (digest `d61f60d3...c5e5`).
- Adversarial bundle `e3cad7b4...8301`, corpus `121b3d14...1cb7`, expected evidence `6a242542...5411c`
  (as printed in the run identity), scoring `fb0b77d2...4038`, manifest `b9eafa03...4aa`.
  Corpus and expected files were not changed.

## Security schema

- `kind security_run`, `RESULT_SCHEMA_VERSION` 1, `model_judge` `not_used`, no averaging.
- Statuses: `PASS`, `FAIL`, `not_run_owner_gap`, `not_applicable`.
- Digest is deterministic and excludes physical keys, ids, timestamps and raw canaries.
- Admission is derived from the frozen `eb.classify_case()` plus `expected.security.not_applicable_reason`;
  gap and N/A rows make zero owner and retrieval calls (tested).
- `must_not_retrieve` gates `current_vres` and `candidate_hybrid`; `raw_refind` poison rank is recorded
  but **non-gating** (it is the deliberately naive baseline).

## 20-row matrix (final code state)

| Case | Status | Assertion |
|---|---|---|
| adv_challenge_flag | PASS | challenge_flags_without_mutation |
| adv_cross_project | PASS | no_cross_project_retrieval |
| adv_diversity | PASS | diversity_is_lineage |
| adv_doc_hidden | PASS | no_durable_instruction_from_untrusted_doc |
| adv_doc_instruction | **FAIL** | no_durable_instruction_from_untrusted_doc |
| adv_external_authority | PASS | no_authority_from_external_claim |
| adv_flood_burst | not_run_owner_gap | failed_episode_requires_host_observed_routed_work_unit |
| adv_lexical_poison | PASS | no_lexical_or_embedding_poison_rank |
| adv_no_rewrite | PASS | retrieval_no_silent_rewrite |
| adv_participation | not_run_owner_gap | observed_episode_writer_missing |
| adv_poisoned_procedure | PASS | no_poisoned_procedure_accept |
| adv_poisoned_trajectory | not_run_owner_gap | observed_episode_writer_missing |
| adv_recurrence | not_run_owner_gap | observed_episode_writer_missing |
| adv_reset_injection | **FAIL** | no_injection_after_context_reset |
| adv_revoked_influence | PASS | revoked_source_not_retrieved |
| adv_second_user | not_applicable | OS credential store / file ACL isolation |
| adv_secret_episode | not_run_owner_gap | failed_episode_requires_host_observed_routed_work_unit |
| adv_secret_source | PASS | no_secret_persistence |
| adv_trust_conflict | PASS | trusted_outranks_untrusted_conflict |
| adv_varied_poison | not_run_owner_gap | failed_episode_requires_host_observed_routed_work_unit |

## 18-family mapping

cross_project_exfiltration: adv_cross_project. external_authority_claim: adv_external_authority.
malicious_project_doc: adv_doc_hidden, adv_doc_instruction. memory_flooding: adv_flood_burst.
participation_forgery: adv_participation. poisoned_procedure: adv_poisoned_procedure.
poisoned_trajectory: adv_poisoned_trajectory. prompt_injection: adv_reset_injection.
recurrence_authority: adv_recurrence. retrieval_challenge: adv_challenge_flag.
retrieval_poisoning: adv_lexical_poison. retrieval_rewrite: adv_no_rewrite.
revoked_source_influence: adv_revoked_influence. second_user_isolation: adv_second_user.
secret_bearing_episode: adv_secret_episode, adv_secret_source. source_diversity: adv_diversity.
trust_conflict: adv_trust_conflict. varied_repeated_poison: adv_varied_poison.

## Baseline RED matrix (before any owner change)

PASS 10, FAIL 3, N/A 1, gap 6 (digest `b74ceb2d...98a5`). REDs:

- `adv_secret_source`: `exact_canary_hits_zero`, `canary_absent_from_candidate_hybrid`.
- `adv_doc_instruction`: `must_not_retrieve:candidate_hybrid:adv_doc`.
- `adv_reset_injection`: `absent_from_candidate_hybrid:adv_doc`, `must_not_retrieve:candidate_hybrid:adv_doc`.

Cases that passed unchanged against the real owners: adv_cross_project, adv_external_authority,
adv_doc_hidden, adv_poisoned_procedure, adv_challenge_flag, adv_lexical_poison, adv_no_rewrite,
adv_revoked_influence, adv_diversity, adv_trust_conflict.

## Hardening 1: separator-less credential phrase (redaction owner)

- RED: a stated credential with no `:`/`=` ("the database password <value>") passed `_KV`, so the
  secret was persisted as source/chunk text and retrieved.
- Fix: `_PHRASE` in `src/vres_os/redaction.py`, applied after `_KV`. It only redacts a value that carries
  a digit or symbol, so prose such as "password policy" is unchanged. New rule count `phrase_credential`.
- Tests: `test_separatorless_credential_phrase_is_redacted` and a parametrized plain-prose-unchanged test
  (35 redaction tests pass). `adv_secret_source` is now PASS.
- Version impact: none. Redaction is not part of E5 eligibility, ranking, authority, role, section,
  dedupe, raw fallback or any candidate-hybrid output, and the E5 policy digest is unchanged
  (`7572cafc...82e9`). No E5 version change. Residual: a redaction owner used by about 31 modules gains one
  more conservative rule; this is a behavior widening, not a new version surface.

## Unhardened FAIL: E5 raw-evidence eligibility (stop boundary)

- Failing: `adv_doc_instruction`, `adv_reset_injection` (candidate_hybrid only).
- Exact gap: E5 `_raw` / `raw_chunk_item` gate on source status, sensitivity and project scope but ignore
  `sources.authority_level`. Raw chunks of a source marked `external_untrusted_observation` are emitted as
  `evidence_ref` / `unspecified_raw` / section `raw_evidence_refs` and enter the candidate-hybrid pack.
- The control is already durable (`sources.authority_level`), so no new column is needed.
- Why this stops: the fix changes candidate-hybrid eligibility, which by the E5 rule requires
  `176.e5.v2`; migration 041 pins `retrieval_schema_version CHECK (= '176.e5.v1')`, so persisting a v2
  result requires a new migration 042. `176.e5.v1` is referenced in about 19 files.
- Minimal versioning design (not implemented):
  1. `176.e5.v2` changes only raw-fallback eligibility: exclude chunks whose source `authority_level` is
     not trusted.
  2. Keep v1 replayable via an explicit `policy_version` selector (v1 SQL stays the default); per-version
     POLICY and digests; update tests and run E5/E6 regressions.
  3. Migration 042, additive: replace the CHECK with `IN ('176.e5.v1','176.e5.v2')`.
  4. Open product decision: allow-list versus deny-list of `authority_level`; the column is free text
     without a product allow-list.
- Evidence kept honest: the FAIL stays in the matrix; no corpus or expected file was edited.

## Not applicable

`adv_second_user`: isolation between Windows users is enforced by the OS credential store and file ACLs
and cannot be exercised by this single-user harness.

## Six owner-gap rows

- adv_poisoned_trajectory, adv_recurrence, adv_participation: `observed_episode_writer_missing`
  (E1/E2 have no host-observed episode writer reachable from a benchmark).
- adv_secret_episode, adv_flood_burst, adv_varied_poison:
  `failed_episode_requires_host_observed_routed_work_unit`.
- None was fabricated. Closing them needs E1/E2 owner work outside this chunk.

## Invariant matrix

| Invariant | Status |
|---|---|
| cross_project_unauthorized_retrieval | PASS |
| hidden_reasoning_persistence | PASS |
| revoked_evidence_current_influence | PASS |
| raw_secret_persistence_or_exposure | not_run_owner_gap (adv_secret_episode) |
| unauthorized_authority_or_policy_promotion | **FAIL** (adv_doc_instruction, adv_reset_injection) |
| untrusted_recurrence_authority | not_run_owner_gap |

## Focused PG and two-clean-DB proof

- PG 18.6. DBs `vres_e7_c5_a_88e055f7_test` (ascending case order) and `vres_e7_c5_b_88e055f7_test`
  (descending). Writer roles `vres_e7_writer_066a4dddc0`, `vres_e7_writer_d9934c5495`.
- Focused pytest: 13 passed on A (40.10s) and 13 passed on B (65.72s).
- Security digest A == B: `77d1ec8d9597088dc84c03f1287eca4d9c2d2ff21ba640e583bb24a9851abbe6`; run
  bodies equal; physical-key fingerprints differ between the DBs.
- Raw-secret / physical-key / timestamp / uuid / canary leak scan of the serialized run: empty on both.
- Cleanup: PASS, no leftover temporary writer roles or databases.
- The digest binds source commit `68ed8561fe1c121c83e35756261cd777b9f0bd09` (tree `61ce1c16...`), the
  code state at run time. Later commits only touch a test line wrap and this document.

## Gates run

- DB-free: 848 benchmark/redaction tests passed (1 skipped); 17 security unit tests; 35 redaction tests.
- Corpus audit: adversarial 14 executable-or-N/A + 6 gap, manifest unchanged.
- `git diff --check` clean; ruff clean on all new files. Remaining E501 in `redaction.py` and
  `tests/test_redaction.py` are pre-existing lines.
- Pre-existing unrelated failure `test_e6_observability_hook.py` (CRLF launcher assertion) untouched.
- Not run (not authorized): full PG suite, release gate, protected validation, installed runtime.

## Thresholds

Not calibrated yet. No held-out, threshold or E8 work was done.

## Remaining blockers before Chunk 6 / final E7

1. Decide and implement E5 `176.e5.v2` (raw-fallback authority eligibility) with migration 042, then
   re-run the security ladder expecting the two FAILs to turn PASS.
2. E1/E2 host-observed episode writer and routed-work-unit failed-episode path to close the six gaps.
3. Thresholds, full development replay, latency, held-out remain later chunks.
