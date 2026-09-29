# Experience Intelligence E2 Contract — Transition Verifier + Safe Consolidation

Date: 2026-09-29
Issue: #176
Base: `407c4a323f4f65c8f28c422789508bb7ce128682` (E1 merged, PR #179)
Branch: `issue-176-e2-consolidation`
Plan: `docs/architecture/EXPERIENCE-INTELLIGENCE-PLAN-2026-09-27.md` (tranche E2)

## Scope

E2 adds exactly two things on top of the immutable E1 episode ledger:

1. a **deterministic transition verifier** that decides whether a candidate lesson is supported by cited episode evidence;
2. **safe consolidation** that turns a verified candidate into a *proposed* project-local knowledge item plus an immutable, auditable transition record.

Nothing else. E2 has no retrieval, no Chairman injection, no capability scoring, no retrieval-utility credit, no lifecycle/revocation/forgetting behaviour, no procedure promotion, no company-wide promotion, and no model/prompt/policy mutation.

## Truth owners (unchanged)

- Semantic lessons live only in `knowledge_items` (existing lifecycle, redaction, statuses). E2 creates no second lesson store.
- Evidence links live only in `relations` / `relation_evidence`.
- Episodes remain immutable E1 rows. E2 never updates, deletes, or re-captures them.
- The only new durable object is `experience_transitions`: an append-only audit of *how* a memory transition was verified. It is not a memory store and is never a retrieval source.

## Inputs

A candidate is caller-supplied **data**, never authority:

```
project_id       int (required; project-local only)
polarity         "positive" | "negative"
trigger          "failure_gotcha" | "validated_novel" | "recurrence"
subject_key      normalized slug naming what the lesson is about
title, statement bounded text
evidence[]       {episode_key, pointer, quote}   (1..N)
```

`pointer` is an RFC 6901 JSON pointer into the cited episode `payload`; `quote` is text that must appear in the value at that pointer. Callers (including a model) may propose wording, but cannot create provenance: every claim must point at persisted episode content.

## Verifier checks (all mechanical, all fail closed)

Structural / integrity failures **raise and persist nothing**:

- malformed candidate (types, enums, bounds, empty text, unknown keys);
- hidden/private-reasoning keys anywhere in the candidate (same key set as E1);
- residual credential-like content (#164 sanitizer `SENSITIVE_REVIEW_REQUIRED`); safely sanitizable content persists sanitized only;
- unknown episode, or episode outside `project_id` scope (cross-project/NULL-project episodes are never consolidated);
- episode integrity: `payload_digest` recomputed from stored row + its policy version/digest must equal the stored digest (corruption ⇒ raise);
- pointer does not resolve, or quote is not contained in the resolved value (unsupported claim ⇒ raise);
- trigger/polarity/outcome rules violated (see below).

Rules:

- **Failure integrity.** `positive` polarity requires every cited episode outcome in `{completed, passed}`. Failed/cancelled evidence may only support `negative` lessons. Failure never becomes a positive lesson.
- **Triggers**:
  - `failure_gotcha`: polarity negative, at least one failed/cancelled episode;
  - `validated_novel`: every episode `validated_runtime` and completed;
  - `recurrence`: the frozen Experience Intelligence plan requires replay calibration before a recurrence/materiality threshold may authorize acceptance. E2 v1 therefore ships with no accepting recurrence threshold. A recurrence candidate is recorded as **quarantined** with `recurrence_threshold_uncalibrated` until a later governed policy version supplies a replay-calibrated distinct-task threshold. Recurrence never raises authority.
- **Participation/trust.** Only `participated` episodes with trust other than `external_untrusted_observation` may support an accepted lesson. Observed/untrusted evidence yields a **quarantined** transition, never a knowledge item.
- **Injection heuristics.** Instruction/authority-shaped candidate text (approval, permission, policy, "ignore previous", credential requests, etc.) is **quarantined**. This is a heuristic on top of, not instead of, the structural rule below.
- **Flood control.** A conservative per-project safety cap on creation of new open experience-derived proposed lessons; over the cap ⇒ **quarantined**. This is a denial/safety bound, not a materiality calibration claim, and it does not block deduplication into an existing lesson.

Verdicts persisted in `experience_transitions`: `accepted`, `deduplicated`, `quarantined`.

## Consolidation outcome

- `accepted`: one `knowledge_items` row, `knowledge_type='lesson'`, **`status='proposed'` always** (never validated/canonical), project-local, deterministic key from the candidate digest; `derived_from` relations to every source episode; metadata carries lineage (transition key, policy version/digest, source episode keys with source/payload digests, derived trust class, polarity, subject).
- `deduplicated`: an existing experience-derived item for the same project has the same normalized statement digest **and the same polarity**; no new item, new episodes are linked as additional evidence; existing status/authority unchanged.
- `quarantined`: audit row only; no knowledge item. An exact same-statement candidate with the opposite polarity is quarantined as `same_statement_opposite_polarity` rather than creating two identical lesson texts with contradictory classification.
- **Conflicts are preserved.** An existing experience-derived item with the same subject and opposite polarity is recorded in the transition (`conflicts`) and linked with `related_to` provenance when a new distinct lesson is accepted; exact-statement/opposite-polarity conflicts are preserved in the quarantined transition. No merge, no overwrite, no supersession (E4).
- Derived trust class: `model_inferred_from_validated_evidence` when every source episode is `validated_runtime`; otherwise `trusted_project_source`. Derived knowledge never gains authority; status stays `proposed`.

## Transition audit

`experience_transitions` (append-only, DB-immutable like episodes): transition key, project, policy version/digest, kind, polarity, trigger, subject, verdict, reason codes, candidate + digest, before/after digests, source episode snapshots (key + source/payload digest + trust + outcome), resulting/deduplicated knowledge key, conflicts, per-check results. Lineage is sufficient for E4 to find and invalidate derived items when a source is later revoked/superseded/stale; E2 itself performs no invalidation.

Policy: publishes new immutable policy version `176.e2.v1` (E1's `176.e1.v1` row is untouched; E1 capture keeps using its own version).

## Atomicity, idempotency, concurrency

- One PostgreSQL transaction: transition row + knowledge item + relations commit or roll back together.
- Identical candidate (same digest) returns the existing transition (unique `(project_id, candidate_digest)`); advisory lock over the candidate digest serializes races; unique constraint is the final boundary.
- Consolidation uses `KnowledgeService`'s existing insert path (extracted to an in-connection form) so redaction/validation is reused, not duplicated.

## Explicitly out of E2

E3 retrieval/ranking/experience packs; E4 supersession/retirement/revocation/forgetting/refresh; E5 capability/procedure integration; E6 retrieval observations; E7 benchmarks; E8 Chairman use; MCP/CLI tool surface for consolidation (service-level only in E2); promotion above `proposed`; any change to E1 capture, episodes, or E1 policy; #165 and later.

## E2 evidence gate

Not DONE until: targeted unit tests; migration contract; PostgreSQL integration; idempotency + concurrency + rollback; malformed/corrupt fail-closed; scope isolation; digest/lineage checks; secret/injection negatives; failure-integrity negatives; no chain-of-thought; conflict-preserved and dedupe proofs; no authority promotion; full suite; release gate; exact-head CI; protected Fable/high validation (governance/security boundary); guarded merge; post-merge main CI.

## Known limits (stated, not hidden)

- The verifier proves *provenance and literal support* (episode integrity, pointer resolution, quote containment, polarity/outcome/trust rules). It cannot prove semantic entailment of the statement; accepted output is therefore only a **proposed** lesson requiring later governed promotion.
- Injection-shape detection is heuristic. The structural defence is that E2 output can never exceed `proposed` and never becomes approval/permission/policy.
- Recurrence acceptance is deliberately disabled in E2 v1 until a threshold is calibrated from replay evidence, as required by the frozen plan. The flood cap (20) is a provisional safety-only denial bound, not a claim of calibrated materiality.


## Post-freeze alignment note

After the initial contract commit `3a6a3fd`, isolated CI and semantic review found two contract-level ambiguities before protected validation. This additive correction does not broaden E2 scope:

- the frozen Experience Intelligence plan explicitly forbids inventing an uncalibrated recurrence/materiality threshold, so E2 v1 now quarantines recurrence until replay calibration exists;
- same-statement/opposite-polarity candidates are now fail-safe quarantined rather than creating duplicate lesson text with contradictory classification.

The original contract commit remains durable history; this note records the bounded correction rather than rewriting it.
