# E7 / E5 v3 low-trust-only abstention addendum (2026-10-08)

Status: FROZEN CONTRACT. Written before any product change. Authorised by the reviewer after a genuine
Boundary-3 product RED. Base head `8fcff9a92dcddd4b116bbdb30c74e8c57aa59c37`; RED checkpoint `CP-20261008-2f49242e8b`.

## 1. The RED (preserved)

Case `adv_participation`, assertion `participation_distinct_from_observation`, failed check
`candidate_hybrid_abstained`. Frozen expectation `must_abstain = true`; E5 `176.e5.v2` returned `abstained=false`.

Actual owner evidence: `adv_seen` is E1 `176.e1.v2`, `observed`, `external_untrusted_observation`, `completed`,
grounded. `adv_x` is E2 `quarantined`, no knowledge, `participation_trust_check=fail`, reasons
`untrusted_or_observed_evidence` and `recurrence_threshold_uncalibrated`. `raw_refind` and `current_vres` are empty.
`candidate_hybrid` returned only `adv_seen` in `low_trust_observations` (role `low_trust_observation`, authority
`external_untrusted`, flag `premise_unverified`), `abstained=false`. The owner gap is E5. E1 and E2 are unchanged.

`adv_participation.must_abstain = true` is NOT weakened. The adversarial corpus and expected evidence are unchanged.

## 2. Design decision

Rejected: "abstained=true while low-trust items remain in the pack". The pack invariant `abstained == (no returned
items)` is preserved for every version. Low-trust observations may supplement but may not be the sole returned
experience basis.

## 3. Structural rule (v3 only)

After eligibility/evaluation, conflict handling, exact/group dedupe, section budgets, total-items cap, raw fallback,
raw dedupe, final total-items cap and byte-size trimming, inspect the FINAL selected items. If the selection is
non-empty AND every selected item belongs to `low_trust_observations`, then v3: counts them; removes ALL of them from the
returned pack; returns `abstained=true`, `reason="only_low_trust_observations"`, empty `evidence_keys`, and
`estimated_tokens` recomputed from the actual empty returned pack; no suppressed identity/text appears anywhere.

If ANY final item belongs to another section (accepted procedure, validated lesson, candidate lesson, trusted raw
evidence, ...), the rule does not apply. A zero-item selection keeps `reason="no_eligible_experience"`.

Diagnostic: v3 packs ALWAYS carry `diagnostics.suppressed_low_trust_only`, a non-negative integer (0 for ordinary packs;
N = number of removed low-trust items). It carries no alias, key or text. v1 and v2 packs never carry it; their exact
historical bytes/shape stay reproducible.

## 4. Policy identities

| version | digest |
|---|---|
| `176.e5.v1` (immutable) | `7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9` |
| `176.e5.v2` (immutable, replayable) | `0cd0f10d24e37dd7a9872eced6c18e4962d4740a2d6a8c03a38cea1d8a73d6b5` |
| `176.e5.v3` (new product default) | `272b10b6042a77bb79812ec637ec9296e28867628285165775c5aeee4af1a4ad` |

v3 = v2 plus the closed field `low_trust_only_abstention`. Canonical JSON (sorted keys, compact), digest = SHA-256:

```json
{"budgets":{"accepted_procedures":3,"candidate_lessons":3,"conflicts_and_stale":5,"current_decisions":8,"low_trust_observations":3,"precedent_episodes":3,"raw_evidence_refs":5,"validated_lessons":6},"chunk":"E5","fusion":"reciprocal_rank_k60_lexical_semantic","low_trust_only_abstention":{"diagnostic":"suppressed_low_trust_only","mode":"suppress_if_only_section","reason":"only_low_trust_observations","section":"low_trust_observations"},"max_items":24,"max_pack_bytes":16384,"rank_order":["section","authority_tier","scope_rank","task_family_or_capability_match","fusion_rank_score","recency_epoch","memory_key"],"raw_source_authority":{"mode":"allow_list","values":["trusted_project_source"]},"retrieval_mode":"lexical+optional_semantic; raw_fallback=lexical_only","version":"176.e5.v3"}
```

Normal product: `SCHEMA_VERSION = "176.e5.v3"`, `POLICY = E5_V3_POLICY`. v1 and v2 stay as explicit internal frozen
paths; there is no public or MCP downgrade selector. Decisive fixture: one project-local E1-v2 observed external
episode, nothing else selected. Frozen v2 returns one `low_trust_observation`, `abstained=false`, `reason=None`.
Normal v3 returns zero items, `abstained=true`, `reason=only_low_trust_observations`, `suppressed_low_trust_only=1`.

## 5. E6

- Replay stays `176.e6.v1`; `BASELINE_POLICY_DIGEST` stays the exact v1 digest above; its candidate universe stays the
  frozen E5-v1 hard-gated universe. Candidates vary ONLY section budgets, max items, max pack bytes and RRF k. Neither the
  v2 raw-source gate nor the v3 low-trust-only rule is varied or activated. E6 policy digest stays
  `d61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5`.
- The observer's closed retrieval registry becomes v1, v2, v3; `FROZEN_E5_V3_POLICY_DIGEST` is the digest above and
  `assert_policy_identity()` verifies all three plus the unchanged E6 digest. Unknown/tampered/cross-version policy is
  rejected.
- Version-specific validation: empty-pack reason for v1/v2 must be `no_eligible_experience`; for v3 it may be
  `no_eligible_experience` or `only_low_trust_observations`. For every version `abstained == not items`; a non-empty
  pack has `reason = null`. `suppressed_low_trust_only` is rejected for v1/v2 and required (non-negative int) for v3.

## 6. Migration 044

Exactly `src/vres_os/migrations/044_experience_retrieval_policy_v3.sql`: drop and re-add
`experience_retrieval_observations_e5_identity_pair_check` with three valid pairs (v1+v1 digest, v2+v2 digest, v3+v3
digest). No table, column, backfill, UPDATE, trigger, privilege or writer change. Migration 042 is unchanged. Head
becomes 044; no 045.

## 7. Out of scope

No change to the adversarial corpus, expected evidence, scoring thresholds, held-out, E8, E1, E2 or E4. No live
participated cohort and no Chunk 6.
