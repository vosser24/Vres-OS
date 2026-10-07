# E7 Chunk 5 addendum: E5 v2 raw-source authority hardening (frozen 2026-10-07)

Status: FROZEN CONTRACT. Committed before any runtime change. Scope is bounded to the two REDs below.

## The two REDs (candidate_hybrid, evidence from the accepted Chunk 5 baseline)

- `adv_doc_instruction`: `no_durable_instruction_from_untrusted_doc` fails on
  `must_not_retrieve:candidate_hybrid:adv_doc`.
- `adv_reset_injection`: `no_injection_after_context_reset` fails on
  `absent_from_candidate_hybrid:adv_doc` and `must_not_retrieve:candidate_hybrid:adv_doc`.

Cause: E5 `_raw` / `raw_chunk_item` ignore `sources.authority_level`
(`external_untrusted_observation` in the corpus), so raw chunks of an untrusted source enter the pack.

## Decision: fail-closed allow-list

`RAW_SOURCE_AUTHORITY_ALLOWLIST_V2 = {"trusted_project_source"}`.
A chunk with a source owner is raw-eligible in v2 only if `sources.authority_level` is in that set.
`external_untrusted_observation`, NULL, empty and any unknown value are excluded. A deny-list was rejected:
`authority_level` is free text and SourceService accepts arbitrary/None values, so a deny-list would
automatically trust unknown values. No SourceService schema/enum change; no legacy row rewrite.

## Provenance shape rule (v2)

- source-only: existing scope/status/sensitivity gates AND the allow-list.
- source + knowledge: BOTH owner gates must pass; the less permissive wins.
- knowledge-only: unchanged. Orphan: still fail closed.
- Applies under current and historical intent.

## Identities

- v1 (preserved byte-for-byte): `E5_V1_SCHEMA_VERSION="176.e5.v1"`, `E5_V1_POLICY` = the existing POLICY object,
  `E5_V1_POLICY_DIGEST=7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9`.
- v2: `E5_V2_SCHEMA_VERSION="176.e5.v2"`, `E5_V2_POLICY` = v1 policy with `version` set to v2 and one added
  closed field `"raw_source_authority": {"mode": "allow_list", "values": ["trusted_project_source"]}`.
  Canonical SHA-256 (computed with the repository `_sha256`, not hand-authored):
  `0cd0f10d24e37dd7a9872eced6c18e4962d4740a2d6a8c03a38cea1d8a73d6b5`.
- Product defaults `SCHEMA_VERSION` / `POLICY` point to v2; explicit v1 constants remain.
- E6 stays `176.e6.v1`, digest `d61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5`.

## No public downgrade

`ExperienceRetrievalService.retrieve()` and MCP `experience_retrieve` always use v2. No `policy_version`
argument is added. v1 exists only as an internal compatibility/replay path (explicit policy argument used by
E6 replay and tests).

## v2 raw eligibility is the only behavior change

Only the `_raw` SQL gets one parameterized predicate on the source branch. No change to structured
knowledge eligibility, authority tiers, sections, fusion, budgets, raw lexical ranking, scope/approval,
lifecycle, sensitivity or knowledge-support gates. No new public diagnostic or pack field beyond the
policy identity field.

## E6 replay stays frozen v1

`BASELINE_POLICY_DIGEST` stays `7572cafc...82e9`. Replay collects its single candidate universe with the v1
hard gates and composes baseline and candidate from it; candidate policies stay post-gate composition
variations (budgets, max items, max pack bytes, rrf_k) and cannot touch the raw-source gate.

## E6 observability supports both identities

A closed registry `{176.e5.v1: (policy, digest), 176.e5.v2: (policy, digest)}`. `validate_pack` selects by the
pack's `schema_version`, requires `pack.policy` to equal that exact policy, and returns the actual version
and digest (never supplied by the pack). Unknown version or mismatch fails closed.
`assert_policy_identity` verifies E6, E5 v1 and E5 v2 digests.

## Migration 042 (the only one)

`src/vres_os/migrations/042_experience_retrieval_policy_v2.sql`. No new table or column, no backfill, no
UPDATE, no trigger/privilege/writer change, 041 untouched. It drops only the two 041 equality checks on
`experience_retrieval_observations` and adds ONE named paired constraint:
`(version='176.e5.v1' AND digest=<v1 digest>) OR (version='176.e5.v2' AND digest=<v2 digest>)`.
Cross-pairs, unknown versions and unknown digests are rejected. Existing v1 rows stay valid.
The sequence ends at 042; there is no 043.

## Not changed

Corpus, expected evidence, scoring, thresholds, held-out; earlier Chunk 2-4 findings stay as historical
E5-v1 evidence. Chunk 6 is not started.
