# Experience Intelligence E7 Contract Addendum 2 — Final Pre-Implementation Clarifications

Date: 2026-10-06
Issue: #176
Task: `TASK-20261006-6cd9d80a92`
Amends: original contract `af9939e80d46f6ea9ed0c836d3078dc022c798dd` (blob `456caf22…`) and Addendum 1 `115b09a1ba8c27a42ac135d16c9c818fa2c97295` (blob `97ce5dec…`)
Status: FROZEN BEFORE IMPLEMENTATION

The original contract, Addendum 1 and this Addendum 2 together are the authoritative frozen E7 contract. No earlier commit is amended. This document is limited to the five points below; everything else is unchanged. `§N` = original contract, `A§N` = Addendum 1, `B§N` = this addendum. Where this addendum is more specific on these five points it governs. It introduces no numeric acceptance threshold, no E8 behavior and no new durable truth owner.

## B1. Held-out context isolation (extends A3, §4)

Filesystem/open-call isolation (A3.3) remains required but is not sufficient if the development context has already seen held-out answers.

1. **Separate authoring context.** The held-out corpus and expected evidence are authored and finalized in an isolated authoring context that is not the development/debugging context (a fresh session/agent with no shared working memory with development).
2. **Timing.** The held-out bundle is authored/finalized only after: implementation is complete; development and adversarial replay are complete; scoring semantics are frozen; and `thresholds.json` is frozen and checkpointed. A held-out bundle authored earlier is permitted only if it is sealed under items 3–5 and never shown to the development context.
3. **Non-answer metadata only.** The development context may receive only: that the held-out bundle exists; its commit and bundle digest; the case count; and the schema-validation result. It must not receive held-out queries, facts, expected evidence or case narratives before final acceptance.
4. **Consumption on exposure.** If the development agent/session is shown held-out case content and subsequently changes code, policy, scoring, corpus or thresholds, that held-out version is consumed under §4 and A3.6, and a replacement must be frozen before the final acceptance run.
5. **Fresh acceptance context.** Final held-out execution may run in a fresh acceptance context that reads the sealed bundle after thresholds are frozen (A3.4).
6. **Handback.** Any handback from held-out authoring or acceptance to the development context excludes answer-bearing content (queries, facts, expected evidence, per-case results that reveal them) unless the held-out set is simultaneously declared consumed. Aggregate pass/fail and digests may be handed back; a failing aggregate that then drives a change consumes the version under §4.
7. The manifest's `consumed` history (A3.6) records any such declaration; it is stated in final evidence (§20).

## B2. Normalized EvidencePack content (replaces `text_ref` in A4.3)

The normalized evidence-pack item is a **closed schema** with these semantic fields (exact field naming may follow repository style; semantics are fixed):

```
{
  "alias":     <stable benchmark alias>,
  "kind":      "knowledge" | "chunk" | "procedure" | "experience",
  "content":   <bounded sanitized evidence text>,
  "truncated": <boolean>,
  "rank":      <positive integer>
}
```

1. **`content` is evidence.** It is the actual bounded public evidence material that the proxy worker (A5) is allowed to use. Aliases and metadata alone are not evidence content and cannot substitute for the material the worker would actually receive.
2. **Source.** `content` comes only from the public native owner result already eligible for that mode (A4.2). The normalizer adds no eligibility and fetches nothing beyond the owner's returned public fields.
3. **Prohibited material.** No hidden/private field, database id, runtime key, raw secret, path/URI that is not already contractually public in that owner's result, raw chain-of-thought, owner-internal score, or unbounded payload may enter any pack field.
4. **Sanitization.** Where the native owner output is not already guaranteed sanitized, the existing public sanitization/redaction path of that owner is applied before normalization (chunk 0 identifies, per owner, the existing path or states that the owner guarantees sanitized output). The normalizer does not scrub silently: if a prohibited field or a secret canary is present in what would become a pack field, normalization **fails closed** (raises, the case result records the failure and the invariant of §12 is evaluated as violated if the material reached a persisted/returned surface).
5. **Size parameter.** One maximum content size is defined in `scoring.json` as a benchmark configuration parameter (`evidence.content_max_code_points`, a positive integer fixed before development replay). It is not an acceptance threshold.
6. **Deterministic truncation, before budgeting.** Text is Unicode-NFC-normalized, then truncated to at most that many code points (a plain cut at the code-point boundary, no marker appended); `truncated` is `true` iff the cut removed text. Truncation occurs **before** token-budget accounting and before the A4.4 common budget is applied.
7. **One canonical object.** The canonical normalized EvidencePack, including bounded `content`, is exactly what (a) the proxy worker consumes, (b) the common token estimator measures (A4.6), and (c) the deterministic serializer serializes (§5). No other representation of pack content is used for any of the three.
8. **Required tests (RED first, A10):** strict-schema tests that unknown fields are rejected; tests that each prohibited category (database id, runtime key, owner score, non-public path, hidden-reasoning key, secret canary) injected into a native result either does not reach the pack or makes normalization fail closed; a truncation determinism test (same input → same `content`/`truncated`, truncation before token accounting); and a test that two packs differing only in `content` have different token estimates and different serialized bytes.

## B3. Performance connection semantics and repeat divisibility (corrects A6.3, A6.4, A6.5, A6.7)

1. **Comparison cohort conditions.** A latency/token comparison among modes requires: same process; same OS, Python and PostgreSQL environment; same database state; and the same **production-normal connection behavior for each owner**. Modes are **not** required to share one physical PostgreSQL connection. No benchmark-only persistent-connection or pooling optimization may be applied to any single mode.
2. **Timed boundary (replaces the connection-sharing wording).** The A4.7 boundary includes the native public owner invocation — including whatever normal connection acquisition that owner performs — plus normalization, through completion of the normalized pack.
3. **Warm-up (clarifies A6.3).** Warm-up means exercising the same production-normal call path immediately before the measured calls. It does not imply physical connection reuse where an owner normally reconnects. The cold/warm labelling rule of A6.3 is otherwise unchanged. Wherever A6.7 says "same … connection pool configuration", read "same production-normal connection behavior per owner".
4. **Repeat divisibility.** `latency.repeats` must be a **positive integer divisible by 4**, because the four-mode Latin-square rotation (A6.5) promises each mode occupies each order position equally often. Scoring-configuration validation rejects, before any replay, a missing, non-integer, non-positive, boolean, or non-multiple-of-four value. Required RED test: configurations with values 0, −4, 3, 6, `true`, `"8"` and `8.0` are rejected; 4 and 8 are accepted.

## B4. Near-duplicate labeling (formalizes A2.1)

`near_duplicate_of` is part of the **closed** `expected_evidence` per-case schema as a structured relation:

`near_duplicate_of: <canonical alias>`

1. **Validity.** The target must be an alias that exists in the same case; self-reference is invalid; cycles are invalid. The target must itself be canonical (carry no `near_duplicate_of`), so clusters are flat: one canonical alias plus the aliases that point to it. Violations fail closed at load.
2. **Cluster.** A near-duplicate cluster = the canonical alias plus every alias whose `near_duplicate_of` names it.
3. **Corpus truth.** Near-duplicate labels are corpus truth authored in `expected_evidence`. They are never model-generated or similarity-computed during protected scoring. Distinct relevant facts are never collapsed merely for semantic similarity; absent a label they are distinct.
4. **Separate visibility.** Per-case evidence reports two counts separately, even if a combined metric is also reported:
   - `exact_duplicate_extra` = sum over returned aliases of (occurrences − 1) [exact alias repeat, including distinct runtime keys that resolve to one alias];
   - `near_duplicate_extra` = sum over clusters of (number of **distinct** aliases of that cluster present in the raw returned list − 1), for clusters with at least one returned alias.
5. **Duplicate-memory rate.** Combined numerator = `exact_duplicate_extra + near_duplicate_extra`; denominator = `|R|_raw`; N/A when `|R|_raw = 0` (unchanged from A2.1). Both component rates (each over the same denominator) are reported alongside the combined rate.
6. **Other metrics unchanged.** Near-duplicate aliases are distinct aliases for Recall/Precision/coverage (A2.1 collapses only exact alias repeats); labelling does not change which aliases are `relevant`.
7. **Required tests (RED first):** load rejects missing target, self-reference, cycle and chained (non-canonical) target; a pack with three exact repeats of one alias, a pack with two distinct aliases of one cluster, and a pack with distinct non-clustered similar-looking facts yield `exact_duplicate_extra`/`near_duplicate_extra` of (2,0), (0,1) and (0,0) respectively.

## B5. Negative transfer (replaces the harmful-negative-transfer and unnecessary-reuse rows of A2.3)

Harm is defined from the deterministic **paired trace**, not from the memory's label.

1. **Pairing.** For every (case, mode ≠ `memory_disabled`), the A5 proxy-worker traces of that mode and of `memory_disabled` on the same case are compared. `memory_disabled` is the reference and has no negative-transfer value of its own.
2. **Outcome worse (frozen paired comparison rule).** The mode's outcome is *worse* iff, comparing in this order: (a) `success` is false where `memory_disabled` is true; else (b) `success` is equal and the mode has strictly more criterion failures. Retries/rework, tool-call counts and cost are reported separately (A2.3) and are not part of this rule.
3. **Memory involvement (mechanical).** The mode's trace *demonstrably involves memory* iff at least one of: (a) `used_aliases` in the trace is non-empty; (b) the action sequence differs from the `memory_disabled` trace at any step (the worker is deterministic and identical across modes, A5.2, so any action delta is attributable to the pack). This is read from the traces only; no hidden-reasoning inference.
4. **Classification.**
   - Outcome worse **and** memory involvement ⇒ a **harmful-negative-transfer event**.
   - Outcome worse **without** memory involvement ⇒ recorded as `unattributed_regression`, **not** proven negative transfer; reported and counted separately, and visible in the per-case record and the aggregates (it is neither hidden nor relabelled as harm).
5. **Cause classes.** Each harmful event is classified by a closed set derived from the expected-evidence labels of the aliases in `used_aliases` and from the case flags: `irrelevant_or_unlabeled`, `stale`, `premise_mismatch`, `relevant_misapplied`, `unnecessary_reuse` (the case is labelled `memory_not_needed`). An event may carry several causes; a deterministic precedence (`premise_mismatch`, `stale`, `irrelevant_or_unlabeled`, `relevant_misapplied`, `unnecessary_reuse`) selects the single primary cause for the per-cause counts, and all matching causes are also listed. If memory involvement is only an action delta with empty `used_aliases`, the cause is `relevant_misapplied` only when the pack contained `relevant` aliases, otherwise `irrelevant_or_unlabeled`. A `relevant`-labelled alias can therefore still be the cause of negative transfer when its use makes the paired outcome worse.
6. **Metrics.**
   - *Harmful negative transfer rate*: numerator = cases with a harmful event; denominator = cases where the `memory_disabled` outcome is not already the worst possible (`success = false` with every criterion failed); N/A when the denominator is zero. Reported micro and macro, plus per-primary-cause counts.
   - *Unnecessary reuse*: numerator = `memory_not_needed` cases whose trace has non-empty `used_aliases` or an action delta; denominator = `memory_not_needed` cases; N/A when none. This is a usage metric; whether it also produced harm is captured by the harmful-event rule above, not double-counted into the harm rate unless the event also meets B5.2–B5.3.
   - *Unattributed regression rate*: numerator = cases classified `unattributed_regression`; same denominator as harm.
7. **Sequence/streaming use.** The paired rule applies per case; streaming-learning negative transfer (§10) uses the same event definition per ordered position.
8. **Required tests (RED first):** a relevant-labelled alias whose use worsens the outcome yields a harmful event with cause `relevant_misapplied`; an outcome regression with identical trace and empty `used_aliases` yields `unattributed_regression`, not harm; a stale-alias use yields cause `stale`; a case where the mode is not worse yields no event even if it used irrelevant aliases (that is reported only via the retrieval irrelevant-memory rate).

## B6. Frozen constraints of this addendum

- No numeric acceptance threshold. The new parameters (`evidence.content_max_code_points`, the divisibility rule for `latency.repeats`) are configuration/validation rules fixed in `scoring.json` before development replay.
- No E8; no automatic memory injection.
- No new durable truth owner; alias maps, manifests, packs and traces remain Git artifacts or ephemeral process state.
- No implementation code or benchmark data is created by this addendum.
- No reopening of settled sections beyond B1–B5.
