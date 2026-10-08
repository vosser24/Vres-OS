# E7 - E5 v5 observed-episode rank determinism addendum (2026-10-08)

Status: frozen BEFORE any v5 product change. E5 v1, v2, v3 and v4 stay exactly as they are.
Follows `EXPERIENCE-INTELLIGENCE-E7-E5-V4-DETERMINISTIC-TIE-ADDENDUM-2026-10-08.md` (head `209a599`).

## 1. The measured RED

`adv_recurrence` has five semantically distinct observed episodes (`adv_e1`..`adv_e5`). Across two clean databases the
security matrix, assertions, invariants and leak scan match and physical identities differ as expected, but
`candidate_hybrid` returns different ACTUAL aliases (A `{adv_e2, adv_e4, adv_e5}`, B `{adv_e3, adv_e4, adv_e5}`, three of
three runs), so the normalized schema-2 digest differs. This is a protected reproducibility FAIL. Aliases are not
normalized, exact reproducibility is not weakened, corpus labels are not changed.

## 2. Two nondeterministic mechanisms ahead of the v4 tie

A. **Lexical / fusion position.** `collect_universe` calls `_positions(episode_rows, "episode_key")`, which orders lexical hits
by `(-lexical_score, episode_key)` and assigns ordinal positions 1,2,3,... Equal lexical scores therefore get DIFFERENT
positions decided by the generated physical `episode_key`; RRF turns that into different `fusion_rank_score`.

B. **Recency.** `recency_epoch = int(observed_at.timestamp())`. For observed episodes `observed_at` is the source
`ingested_at` (real DB persistence time). Operations are fractions of a second apart, so runs cross integer-second
boundaries differently and tie groups differ.

Both rank dimensions precede `semantic_tie_digest`, so the v4 tie-break is never reached.

## 3. Rejected: recency quantization

No second/minute/hour/day bucket: any fixed bucket adds another arbitrary wall-clock boundary. v5 keeps the real semantic
order (later persisted observation > earlier) using the exact `observed_at` instant internally. Absolute timestamps may
differ across databases; their RELATIVE order must be stable. Exact timestamps are never serialized into benchmark identity.

## 4. Principle (low-trust observed episodes only)

1. equal lexical relevance gets equal lexical fusion contribution;
2. exact persisted observation order provides recency;
3. the semantic digest breaks genuine remaining ties;
4. the physical `memory_key` is only the final fallback.

No authority, eligibility, budget or security-gate change. Semantic digest orders; it never manufactures a different
relevance score.

## 5. E5 v5 policy

`E5_V5_SCHEMA_VERSION = "176.e5.v5"`; normal product `SCHEMA_VERSION`/`POLICY` become v5. v5 = v4 plus ONE closed field:

```json
"observed_episode_ranking": {
  "scope": "low_trust_observations",
  "lexical_score_ties": "shared_competition_rank",
  "recency": "exact_observed_at_desc",
  "recency_tie": "semantic_digest_then_memory_key"
}
```

Exact canonical JSON (sorted keys, compact), mechanically produced from `E5_V4_POLICY` + `version` + that field:

```
{"budgets":{"accepted_procedures":3,"candidate_lessons":3,"conflicts_and_stale":5,"current_decisions":8,"low_trust_observations":3,"precedent_episodes":3,"raw_evidence_refs":5,"validated_lessons":6},"chunk":"E5","fusion":"reciprocal_rank_k60_lexical_semantic","low_trust_only_abstention":{"diagnostic":"suppressed_low_trust_only","mode":"suppress_if_only_section","reason":"only_low_trust_observations","section":"low_trust_observations"},"max_items":24,"max_pack_bytes":16384,"observed_episode_ranking":{"lexical_score_ties":"shared_competition_rank","recency":"exact_observed_at_desc","recency_tie":"semantic_digest_then_memory_key","scope":"low_trust_observations"},"rank_order":["section","authority_tier","scope_rank","task_family_or_capability_match","fusion_rank_score","recency_epoch","semantic_tie_digest","memory_key"],"raw_source_authority":{"mode":"allow_list","values":["trusted_project_source"]},"retrieval_mode":"lexical+optional_semantic; raw_fallback=lexical_only","stable_tie_break":{"digest":"sha256_canonical","identity":"public_semantics_v1","mode":"semantic_digest_before_physical_key"},"version":"176.e5.v5"}
```

v5 policy digest: `7b5422cf9201bb195b12e9b08ae2f7048b9fbb075951ab598e0e486cfba0dcbf`.
`rank_order` is unchanged (the public `recency_epoch` signal stays); for low-trust observed items the recency dimension
is the exact instant (private `_recency_instant`, never emitted).

Historical digests: v1 `7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9`,
v2 `0cd0f10d24e37dd7a9872eced6c18e4962d4740a2d6a8c03a38cea1d8a73d6b5`,
v3 `272b10b6042a77bb79812ec637ec9296e28867628285165775c5aeee4af1a4ad`,
v4 `4e468f39ee775aebe33c0b2774c61b6fb7c3531ffb16be9dafa209b765717b41`.

## 6. Rules

- **Lexical:** competition rank among low-trust lexical hits: `lex_pos = 1 + count(hits with STRICTLY greater score)`
  (0.8,0.8,0.5,0.5,0.2 -> 1,1,3,3,5). Other episode classes keep the v4 `_positions` behavior. v1-v4 `_positions` untouched.
- **Recency:** low-trust observed items sort by the exact `observed_at` instant descending (integer microseconds),
  then `semantic_tie_digest`, then `memory_key`. Conflict members keep the v4 structural order.
- **SQL pre-limit (LIMIT 50):** for v5 the order is `rank DESC, observed_at DESC` (relative persisted order, stable across DBs)
  then bounded stable semantics (`policy_version`, `participation_class`, `trust_class`, `outcome_status`, `task_family`,
  objective text, all `COLLATE "C"`), and only then `episode_key` as the final identical-semantics fallback. No project id,
  source/payload digest or key participates before that.
  Residual: rows identical in every listed dimension and in `observed_at` fall to `episode_key`; such rows are
  semantically indistinguishable to the pack.
- `public_semantics_v1` is reused unchanged.
- `_retrieve_frozen_v4` reproduces v4 exactly (ordinal ties by key, integer-second epoch). No public/MCP selector.

## 7. Migration 046 / E6

`046_experience_retrieval_policy_v5.sql` replaces only the pair check with five exact pairs. 045 immutable; head 046; no 047.
E6 observer registry v1..v5 with `FROZEN_E5_V5_POLICY_DIGEST`; E6 policy `176.e6.v1`
(`d61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5`) unchanged; E6 replay stays frozen to E5 v1.

## 8. Acceptance

RED/GREEN unit tests (shared lexical rank, second-boundary recency, combined selection), then two independent real
two-clean-DB repetitions with ACTUAL aliases, exact list equality, no relabel. No corpus, scorer, threshold, held-out or E8
change. The live cohort and Chunk 6 are not started.
