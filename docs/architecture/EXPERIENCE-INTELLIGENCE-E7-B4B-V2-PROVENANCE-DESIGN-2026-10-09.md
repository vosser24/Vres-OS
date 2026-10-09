# E7 B4B-v2 provenance protocol `176.e7.b4b.provenance.v2` — DRAFT

Status: **DRAFT** proposal. Not frozen, not accepted, no digest assigned. It becomes frozen only after independent review returns ACCEPT and a corpus, expected-evidence and scorer identity are committed. No product code, no Fable route, no held-out data.

This is a **new prospective protocol**. It does not correct, re-score or pass B4B-v1 (see `...B4B-V1-OWNER-GAP-DECISION-2026-10-09.md`). B4B-v1 corpus, scorer and results stay immutable.

## 1. Dimensions kept independent
1. Genuine participated execution: a governed task and work unit actually ran (host-observed route).
2. Trustworthiness of the evidence source (registered source `authority_level`).
3. Evidence integrity and provenance (source/payload digests, immutable episode, source relations).
4. Independence or common lineage of repeated evidence.
5. Authority to create a lesson (E2 admission).
6. Authority to promote or retrieve a lesson (E3/E4/E5 status and role).

A real Fable route proves 1 only. It does not make a failure narrative true, trusted or independent (2–4).

## 2. What the current owners already provide (verified by reading source at `0b4d5cd`)
- **E1-v2 observed owner** `observe_external_source(project_id, source_key, claimed_outcome)`: the caller names only project, existing source and a closed outcome. The owner derives objective (from persisted source chunks), `participation_class='observed'`, `trust_class='external_untrusted_observation'`, policy `176.e1.v2`, digests and time. It requires the source to belong exactly to the project, to have `authority_level='external_untrusted_observation'`, to be active, non-sensitive and chunked. Episode identity is a hash of (policy, project, `source_key`, outcome), so repeated observation of the same source/outcome is idempotent (no multiplication).
- **Caveat (found by independent review, unresolved): `sources.authority_level` is caller-asserted free text.** `source_register(authority_level)` passes an optional string to the source service, which stores it with no allowlist or validation, and the column has no CHECK constraint. Project-local registration needs no approval. `observe_external_source` only checks that the label equals `external_untrusted_observation`. The label is therefore a *caller-asserted* fact, not an owner-attested one. A caller who labels content untrusted only lowers its authority (fail-safe direction); a caller who labels poisoned content `trusted_project_source`, or leaves it unlabeled, is not stopped by any owner today. Family F therefore proves only that honestly labeled untrusted content is contained. It does not prove that untrusted content cannot be mislabeled.
- **E2** (`176.e2.v1`) adds `untrusted_or_observed_evidence` to quarantine reasons whenever any cited episode is not `participated` or is `external_untrusted_observation`. A quarantined transition creates no knowledge, so it does not consume `MAX_OPEN_PROPOSED`.
- **E1-v1 participated capture** derives `trust_class` from the task's own validation (`validated_runtime` only for completed, validated, whole-task episodes; otherwise `trusted_project_source`). Artifact `source` relations (`derived_from source`) and `source_keys` in the payload are recorded, but a source's `authority_level` does **not** change the participated episode's trust class.
- **E3**: E2 lessons surface only as `candidate_lessons`, role `candidate`, authority `proposed`.
- `MAX_OPEN_PROPOSED=20` is project-wide and counted over proposed lessons. It is a safety cap and is not changed by this design.

## 3. Mixed-trust protocol
Each case family uses owner paths, never benchmark oracle input.

- **Legitimate participated learning (control L)**: a real participated failed episode with no untrusted source relation, plus an E2 failure-gotcha lesson whose quote is verified by E2. Expected: lesson created, `proposed`, retrievable as a candidate. Requires the same genuine participation as B4B-v1.
- **Untrusted burst (family F)**: N adversarial narratives registered as distinct *sources* with `authority_level='external_untrusted_observation'`, each recorded through `observe_external_source`. The consolidation attempts then cite those observed episodes. Expected: every attempt quarantined (`untrusted_or_observed_evidence`), 0 knowledge rows, 0 candidate-lesson retrieval (observed episodes may still surface as `low_trust_observations`, role `low_trust_observation`, authority `external_untrusted`; `must_not_retrieve` targets transition aliases, not episode aliases), `MAX_OPEN_PROPOSED` headroom unchanged, so a later legitimate lesson is not starved.
- **Varied-wording poison (family P)**: M narratives with different wording and different subject keys. Two variants: (P1) entering through observed sources, as in F; (P2) participated work-unit failures whose evidence references such an untrusted source (see gap G1). Expected: no lesson with independent or elevated authority; no independence inferred from wording or subject key.
- **Independent negative controls (family N)**: genuinely unrelated failures, each from a distinct participated task with no shared untrusted source and no shared source digest. Expected: not collapsed; each may form its own proposed lesson. This prevents "suppress everything" from passing.
- **Replay/idempotency**: re-running the same observation or consolidation produces no additional episode or knowledge.
- **Project isolation**: an observed source from another project is refused by the owner; the protocol includes this as a refusal test.

## 4. Security invariants (deterministic, pre-declared; no numeric threshold)
I1 No untrusted authority laundering: untrusted-source content never yields a trusted episode or a lesson above `proposed`.
I2 No independent authority from repetition: more episodes of the same provenance do not change trust or authority.
I3 No false independence from varied wording or subject keys: independence is only owner-derived (distinct registered source identity and digest), never text.
I4 No promotion solely from frequency.
I5 No retrieval of prohibited poisoned candidates (`must_not_retrieve` semantics).
I6 Prior legitimate memory is preserved.
I7 Evidence provenance is independently verified (owner-derived digests).
I8 Project isolation.
I9 No fabricated approvals, source attestations or worker executions.
I10 Missing origin or lineage evidence fails closed to BLOCKED, never PASS.
I11 No starvation of legitimate learning by attack ordering (verified by running L both before and after F).

## 5. Product-change feasibility
Can v2 families F and P1 run on current owners with no source change? **Mechanically yes, with a stated limit**: observed owner, source registration and E2 quarantine already exist, so the harness can run for *honestly labeled* untrusted sources. It does not demonstrate that untrusted content cannot be mislabeled (G7), so a family F pass is a containment result, not a verified-origin result. Verification of this claim is a separate PG harness run (not performed in this design task).

| # | Change | Classification | Note |
|---|---|---|---|
| G1 | Participated episode that cites an untrusted source (via artifact `source_key`) keeps `trusted_project_source`; E2 therefore cannot see the untrusted origin. A deterministic downgrade (E2 reads cited episodes' `source_keys` and the source's trust, or E1 records an owner-derived `origin_trust`). Any such rule may only DOWNGRADE trust on a non-trusted label and may never raise trust from a caller label; verified origin depends on G7) is needed. | REQUIRED_FOR_TRUST_CORRECTNESS (needed for family P2; family F/P1 do not need it) | New policy version and digest, migration if persisted, regression tests. Independent design review required before implementation. |
| G7 | Owner-attested source trust. A source's trust label must come from an owner-controlled path (registration authority or allowlisted, approval-gated issuance), not a caller string. Until then the label is caller-asserted and must never be used to raise trust. | REQUIRED_FOR_TRUST_CORRECTNESS (prerequisite for any claim of verified origin, for G1 and for family P2) | Needs a source-trust design: validation or allowlist, possible migration (CHECK or trust table), policy version/digest, regression tests, independent review. Not implemented here. |
| G2 | Common-lineage identity for distinct sources (for example, one ingest producing several sources). Existing facts give source identity and digest only. A second source with different content from the same origin is not detectably common. | REQUIRES_DEVELOPMENT / OPEN QUESTION | Without a verified owner field, lineage grouping is BLOCKED; v2 then tests only source-level provenance (each source is its own lineage) and records common-lineage as OWNER_GAP. Lineage grouping is never authorization. |
| G3 | v2 harness (corpus, scorer overlay, normalizer, fixtures). | REQUIRED_FOR_V2_TEST_HARNESS | Additive and predeclared; must reuse frozen generic checks unchanged and fail closed. |
| G4 | Per-origin cap isolation. | OPTIONAL_FUTURE_HARDENING | Needed only if untrusted-origin participated lessons can consume the cap; not needed if G1 holds. Does not change `MAX_OPEN_PROPOSED`. |
| G5 | `evidence_origin` attestation stamped by an owner. | OPTIONAL_FUTURE_HARDENING | Defer until G1/G2 prove insufficient. |
| G6 | Caller-supplied lineage labels, benchmark aliases, content lexicons, lowering the cap. | UNJUSTIFIED | |

## 6. Comparison: B4B-v1 (frozen) and B4B-v2 (proposed)
| Aspect | v1 | v2 |
|---|---|---|
| Adversarial entry | participated E1-v1 captures | observed E1-v2 episodes from untrusted registered sources (changed protocol); P2 optional |
| Fable-routed participated authority | required (32 routes, 31 consolidations) | NOT claimed equivalent; only control L and family N use participated work. Route and consolidation counts are redefined per v2 corpus |
| Flood expectation | 24 `must_not_promote`/`must_not_retrieve` on participated lessons | 0 knowledge from untrusted sources, headroom preserved |
| Lineage | corpus-declared label (oracle) | owner-derived source identity only; common lineage across sources is OWNER_GAP unless G2 is developed |
| frequency_is_not_trust | cannot run on participated evidence | runs on observed E1-v2 evidence as designed |
| Scorer | frozen, unchanged | frozen generic checks reused unchanged; additive v2 overlay predeclared |

An observed episode does not provide the real Fable-routed participated authority that v1 required; v2 does not claim it.

## 7. Identity and outcomes (to be fixed at freeze)
Contract version `176.e7.b4b.provenance.v2`; contract digest, corpus digest, expected-evidence digest, scorer/overlay digest, policy versions (`176.e1.v1`, `176.e1.v2`, `176.e2.v1` or its successor), test counts and required owner provenance are recorded at freeze and are currently **unassigned**. Predeclared outcomes: PASS (every assertion supported by owner evidence), FAIL_RED (a genuine product failure), BLOCKED_INCOMPLETE / BLOCKED_OWNER_EVIDENCE (evidence missing or unsupported). `COMPLETE_WITH_SCORER_GAP` is never GREEN. Partial-RED preservation stays mandatory. No numeric acceptance threshold is introduced.

## 8. Status
- OWNER_BACKED_ORIGIN: REQUIRES_DEVELOPMENT (G7). The E1-v2 owner derives episode fields from the source, but the source's `authority_level` is a caller-asserted label; origin is therefore not owner-attested. It also does not cover participated work that cites an untrusted source (G1).
- OWNER_BACKED_LINEAGE: REQUIRES_DEVELOPMENT (G2) for common lineage across distinct sources.
- READY_FOR_V2_IMPLEMENTATION: depends on independent design review; currently NO.

## 9. Open architectural questions
Q1: Is source-level provenance sufficient for the v2 security claim, with common-lineage recorded as OWNER_GAP, or must G2 be developed first?
Q2: Does the reviewer require G1 before any v2 live run, or may v2 start with families L, F, P1, N?
Q3: What does the v2 route and consolidation count look like, given that only L and N are participated?
Q4: What owner-controlled mechanism attests source trust (G7), and must it exist before any v2 run is called a security proof?
