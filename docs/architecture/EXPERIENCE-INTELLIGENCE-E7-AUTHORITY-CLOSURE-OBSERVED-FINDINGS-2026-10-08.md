# E7 Boundary 3 — observed authority closure: findings (2026-10-08)

Status: Boundary 3 code is committed and locally verified. The live participated cohort and Chunk 6 have **not** been started.
The frozen contract for the product change is
`EXPERIENCE-INTELLIGENCE-E7-E5-V3-LOW-TRUST-ABSTENTION-ADDENDUM-2026-10-08.md` (`1e24e4a`).

## 1. What was observed

1. **Scorer RED.** The first run of the new observed-episode assertions failed 42 scorer tests before any
   runtime existed. That was the intended test-first RED.
2. **Product RED.** With the scorer and runtime written, `adv_participation` failed on real PostgreSQL rows.
   The case requires `must_abstain=true`: a lone observed (external, untrusted) episode must not be returned
   as experience. E5 v2 returned it as one `low_trust_observations` item with `abstained=false`.
3. The expectation was **not** weakened and the adversarial corpus and expected evidence were **not** changed.
   `adv_poisoned_trajectory` and `adv_recurrence` stayed PASS throughout.

## 2. Why not a non-empty abstained pack

An abstained pack that still carries items breaks the E5/E6 invariant `abstained == no returned items`
(which the E6 observer and the migration 041 table check both enforce). Reinterpreting `abstained` for
that one case would have changed the meaning of a field every consumer relies on. Rejected.

## 3. The structural v3 rule (`176.e5.v3`)

After all selection steps, including byte trimming: if the **final** selection is non-empty and every item
is in `low_trust_observations`, v3

- counts them into `diagnostics.suppressed_low_trust_only`;
- removes them all;
- returns `abstained=true`, `reason="only_low_trust_observations"`, empty `evidence_keys`, and
  `estimated_tokens` recomputed from the empty pack;
- leaks no suppressed identity or text.

Any item in another section means the rule does not apply. Zero items keeps `no_eligible_experience`.
`suppressed_low_trust_only` (int >= 0) is present in every v3 pack and never in v1/v2 packs.

v3 policy = v2 policy plus `version: "176.e5.v3"` and

```json
"low_trust_only_abstention": {
  "mode": "suppress_if_only_section",
  "section": "low_trust_observations",
  "reason": "only_low_trust_observations",
  "diagnostic": "suppressed_low_trust_only"
}
```

| Policy | Digest (sha256 of canonical JSON) |
| --- | --- |
| `176.e5.v1` | `7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9` |
| `176.e5.v2` | `0cd0f10d24e37dd7a9872eced6c18e4962d4740a2d6a8c03a38cea1d8a73d6b5` |
| `176.e5.v3` | `272b10b6042a77bb79812ec637ec9296e28867628285165775c5aeee4af1a4ad` |

## 4. Compatibility proof

- v1 and v2 digests are unchanged and still asserted by the E6 observer; v1 and v2 packs keep their exact
  shapes (no `suppressed_low_trust_only`, a lone low-trust item is still returned).
- They remain replayable only through explicit **internal** frozen paths (`_retrieve_frozen_v1`,
  `_retrieve_frozen_v2`). There is no public or MCP downgrade selector (test-covered).
- E6 replay stays `176.e6.v1`; its baseline digest is still the v1 digest and the E6 digest is unchanged
  (`d61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5`).
- E6 observer: closed registry v1/v2/v3 with version-specific abstention reasons and diagnostics; the rule
  `reason == only_low_trust_observations  <=>  suppressed_low_trust_only > 0` is enforced.

## 5. Migration 044

`044_experience_retrieval_policy_v3.sql` replaces only the 042 pair check
`experience_retrieval_observations_e5_identity_pair_check` with three valid (schema version, digest) pairs.
No table, column, backfill, trigger, privilege or writer change. 042 is immutable; head is 044; there is no 045.
Table check 041 (`abstained AND item_count=0 AND reason NOT NULL`) already accepts the new reason.

## 6. Second finding: evidence depended on E5 tie-break survivors

The first two-clean-DB attempt after v3 matched on the matrix (16/0/1/3) but **A and B digests differed**.
Cause: `adv_recurrence` has five same-class observed episodes and E5 keeps three. Which three survive is decided
by recency seconds and the physical key, both different per database, so alias identities in the evidence differed.
That is not an E5 defect; it is evidence that was not independent of physical identity.

Fix (benchmark runtime only): surfaced episodes of one security-state class (project, policy version,
participation, trust, outcome, lifecycle state, usability) are labelled canonically by position when E5 kept fewer
than exist. E5, the corpus, thresholds and held-out data are untouched. Classes with no truncation, and episodes
of differing state (for example revoked), are never relabelled (unit-tested).

## 7. Final observed results

Security schema 2. Public evidence keys for the observed cases: `episodes`, `transitions`,
`candidate_hybrid_abstained`, `candidate_hybrid_reason`. No physical ids, keys, timestamps or digests.

| Case | Result | Notes |
| --- | --- | --- |
| `adv_participation` | PASS | abstained, reason `only_low_trust_observations`, 0 hybrid items |
| `adv_poisoned_trajectory` | PASS | not abstained; observed episode never promoted |
| `adv_recurrence` | PASS | not abstained; five-episode lineage never promoted or trusted |

Matrix: **16 PASS / 0 FAIL / 1 NOT_APPLICABLE / 3 OWNER_GAP** (20 rows).
Invariants: cross-project, hidden-reasoning and revoked-influence PASS; `raw_secret_persistence_or_exposure`,
`unauthorized_authority_or_policy_promotion` and `untrusted_recurrence_authority` remain NOT_RUN_OWNER_GAP.

## 8. Two-clean-DB proof

Two new `_test` databases with new restricted writer roles; case order ascending in A, descending in B
(PostgreSQL 18.6, run twice). Both runs: A == B on case results, episode and transition evidence, v3 abstention
reason, invariants and the schema-2 digest
`e5f45a99680b94207dbc6a2f9b1517a4730f38edb4eb25437e402c0e956fe401`; physical fingerprints differ; leak scan
empty; cleanup PASS; writer roles removed. The first attempt (before section 6) is retained as the failing history.

## 9. Remaining owner gaps (3)

`adv_secret_episode`, `adv_flood_burst`, `adv_varied_poison` — no owner exists yet. They stay
NOT_RUN_OWNER_GAP and are not scored.

## 10. Verification run

DB-free: 2643 passed, 4 skipped (`tests/test_*.py`). PostgreSQL (opt-in harness): observability schema 17,
retrieval observation 19, retrieval journey 77, retrieve surface 37, v3 journey 3, migrator resume 1, security 18 — all passed.
Not run (by instruction): the full repository PG suite, the release gate, protected validation, the live cohort.

## 11. Correction (2026-10-08, added after independent review; sections 6 and 8 above are retained as history)

1. **Misclassification.** Section 6 treated the A/B digest mismatch as evidence "not independent of physical identity"
   and fixed it in the benchmark runtime by relabelling. Independent review rejected that: the five episode aliases name
   *different semantic text*, so the relabel reported episodes E5 had not returned and violated actual alias resolution.
2. **Invalid evidence.** The section 8 digest `e5f45a99680b94207dbc6a2f9b1517a4730f38edb4eb25437e402c0e956fe401`
   is invalid as protected reproducibility evidence. It documents the workaround only.
3. **Product fix.** The final tie in E5 ended in the physical `memory_key`. `176.e5.v4` (see
   `EXPERIENCE-INTELLIGENCE-E7-E5-V4-DETERMINISTIC-TIE-ADDENDUM-2026-10-08.md`) orders equal-ranked items by a digest of
   public semantics before the key. v1/v2/v3 digests are unchanged; migration 045 admits the v4 identity; the relabel code
   and its tests are deleted; `hybrid_view` now reports the actual aliases of the returned runtime keys.
4. **Result of the new two-clean-DB proof: NOT reproducible.** Three runs (A ascending, B reversed, new DBs and writer
   roles each time) matched on the 16 PASS / 0 FAIL / 1 N/A / 3 OWNER_GAP matrix, invariants, leak scan (empty), cleanup
   (PASS) and physical-key difference, but **every run's schema-2 digest differed**, only in
   `adv_recurrence` `hybrid`/`packs.candidate_hybrid` (which three of the five tied episodes are returned).
   No relabel or normalization was added to hide this.
5. **Measured cause (probe, not committed).** The five observed sources are registered ~0.3-0.4 s apart
   (e.g. `ingested_at` 47.07, 47.44, 47.85, 48.19, 48.48 s), so they land in different wall-clock seconds. Two E5 inputs are
   derived from that clock: `recency_epoch` (whole seconds of `observed_at` = source `ingested_at`) and the lexical
   candidate position used for `fusion_rank_score` (SQL `ORDER BY rank DESC, e.observed_at DESC, e.episode_key`). Returned
   scores differed per episode (0.016393 / 0.016129 / 0.015873). Both rank dimensions precede the v4 semantic digest, so the
   digest tie-break is not reached. The addendum declared `recency_epoch` as a residual limit; the fusion-position
   dependency was not declared and is a second, equal-grade source.
6. **Status.** Boundary 3 reproducibility is still RED. Fixing it needs a decision outside the frozen v4 contract (for
   example, a v5 rule that breaks lexical-tie positions and recency among equal-text observed items by the semantic digest, or a
   benchmark-controlled clock). Not applied; the corpus, expected evidence, thresholds, security scorers and low-trust budget
   are unchanged. The live cohort and Chunk 6 are not started.
