# E7 — E5 v4 deterministic semantic tie-break addendum (2026-10-08)

Status: frozen BEFORE any v4 product change. Supersedes nothing; E5 v1, v2 and v3 stay exactly as they are.
Follows `EXPERIENCE-INTELLIGENCE-E7-E5-V3-LOW-TRUST-ABSTENTION-ADDENDUM-2026-10-08.md`.

## 1. The observed defect

1. Two clean databases A and B ran the real `adv_recurrence` case through candidate-hybrid E5 v3.
   The matrix matched (16 PASS / 0 FAIL / 1 NA / 3 OWNER_GAP) but the schema-2 result digests **differed**.
2. `adv_recurrence` has five observed, `external_untrusted_observation` episodes (`adv_e1`..`adv_e5`) with
   **different objective text**. The low-trust section budget is 3, so E5 returns three of five.
3. When authority tier, scope rank, task/capability match, fusion score and recency epoch all tie, the v1/v2/v3
   sort ends in `memory_key`, a generated physical identity. Which three *semantically different* episodes are
   returned therefore depends on the database. That is a product determinism defect, not noise.

## 2. The rejected workaround

Commit `fdc4fde` made A and B equal by relabelling, after retrieval, the returned episode aliases to positional
aliases of an "interchangeable" security-state class (`surfaced_aliases`, `interchangeable_episodes`).
Rejected: the aliases name different semantic episodes (different objective text), so the substitution reports
episodes E5 did not return. The frozen contract maps each returned runtime key to its *actual* case-local alias;
it never permits alias -> another alias. The schema-2 digest `e5f45a99680b94207dbc6a2f9b1517a4730f38edb4eb25437e402c0e956fe401`
is retained as historical evidence of that workaround only, not as acceptance evidence.

The corpus, expected evidence, low-trust budget (3), security scorers and thresholds are NOT changed to hide this.

## 3. E5 v4

`E5_V4_SCHEMA_VERSION = "176.e5.v4"`. Normal product: `SCHEMA_VERSION = E5_V4_SCHEMA_VERSION`, `POLICY = E5_V4_POLICY`.
v4 = v3 semantics (authority, eligibility, gates, budgets, fusion, low-trust-only abstention) plus ONE rule:
among items that tie on every ranking dimension, order by a semantic digest before the physical key.

```json
{
  "...": "all v3 fields unchanged",
  "version": "176.e5.v4",
  "rank_order": ["section", "authority_tier", "scope_rank", "task_family_or_capability_match",
                 "fusion_rank_score", "recency_epoch", "semantic_tie_digest", "memory_key"],
  "stable_tie_break": {
    "mode": "semantic_digest_before_physical_key",
    "digest": "sha256_canonical",
    "identity": "public_semantics_v1"
  }
}
```

v4 policy digest (sha256 of the canonical JSON): `4e468f39ee775aebe33c0b2774c61b6fb7c3531ffb16be9dafa209b765717b41`.

### 3.1 Semantic tie object (`public_semantics_v1`)

Closed object, canonical JSON, `sha256` hex:

```
section, memory_class, authority_class, status, trust_class, role,
text, why_retrieved (sorted), flags (sorted), applicability
```

Verification that none of these carries physical runtime identity:

| Field | Source | Physical identity? |
| --- | --- | --- |
| section, memory_class, authority_class, status, trust_class, role | closed vocabularies / outcome status | no |
| why_retrieved, flags | closed reason/flag names (e.g. `conflict_reason_<reason>`) | no |
| applicability | task_family, capability keys (registry names), bounded premises/constraints/premise status | no |
| text | bounded sanitized statement / episode objective text | **only for revoked tombstones**, whose text is `Revoked <kind> <memory_key>; content withheld.` |

Refinement: the item's own `memory_key` is replaced by the constant `<key>` inside `text` before hashing, so tombstones
carry no physical key either.

Deliberately excluded: `memory_key`, `project_id`, `evidence` (carries episode/source/decision keys), `provenance`
(source/payload digests, `observed_at`), `signals` (scores, recency), `also_matched`, every `_`-prefixed internal field,
timestamps and UUIDs.

### 3.2 Sort order

v1/v2/v3 keep the exact old tuple ending in `memory_key`. v4 uses the same dimensions through `recency_epoch`, then
`semantic_tie_digest`, then `memory_key`. The physical key remains only the final total-order fallback for items whose whole
public semantics are identical. Conflict members (ordered by structure only, no relevance/recency) use
`(section, tier, scope, 0, 0.0, 0, semantic_tie_digest, memory_key)` in v4.
v4 does not change authority, eligibility, gates, budgets, fusion weights or abstention.

### 3.3 Declared residual limits (not changed here)

- `recency_epoch` is whole seconds of the stored `observed_at`; for observed episodes that is the source
  `ingested_at` (database wall clock). Items ingested in different seconds are ordered by recency by design.
- Raw chunk selection (`select_raw`) and the SQL candidate fetch (`LIMIT 50/200`) still end in a physical key; they are out of
  scope for this tie rule and are not exercised by `adv_recurrence`.

## 4. Preservation

- `_retrieve_frozen_v1`, `_retrieve_frozen_v2` stay; new internal `_retrieve_frozen_v3` replays v3. No public/MCP downgrade selector.
- v1/v2/v3 digests unchanged: `7572cafc…982e9`, `0cd0f10d…d6b5`, `272b10b6…af1a4ad`.
- v3 may still choose by physical key in the tie fixture (historical behaviour). v4 must be stable.

## 5. Migration 045

`src/vres_os/migrations/045_experience_retrieval_policy_v4.sql` replaces only the observation identity pair check
(same constraint name) with four exact (version, digest) pairs v1..v4. No table, column, backfill, UPDATE, trigger,
privilege or writer change. 044 and 042 stay immutable. Head becomes 045; no 046.

## 6. E6

- Observer registry v1..v4 with `FROZEN_E5_V4_POLICY_DIGEST`; v4 pack validation = v3 plus the v4 policy identity.
- E6 policy stays `176.e6.v1`, digest `d61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5`.
- E6 paired replay stays frozen to E5 v1 and activates none of v2 raw-source gate, v3 abstention, v4 tie.

## 7. Acceptance for this addendum

RED: a semantic-tie unit test (five equal-ranked observed items, distinct text, permuted physical keys: v3 differs, v4 equal),
then the real two-DB `adv_recurrence` run with ACTUAL aliases and no relabel. No changes to corpus, expected evidence,
thresholds, held-out or E8. The live participated cohort and Chunk 6 are not started.
