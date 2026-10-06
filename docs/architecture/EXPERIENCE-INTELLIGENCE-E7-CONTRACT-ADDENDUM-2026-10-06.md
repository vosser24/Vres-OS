# Experience Intelligence E7 Contract Addendum — Independent-Review Corrections

Date: 2026-10-06
Issue: #176
Task: `TASK-20261006-6cd9d80a92`
Amends: `EXPERIENCE-INTELLIGENCE-E7-CONTRACT-2026-10-06.md` at commit `af9939e80d46f6ea9ed0c836d3078dc022c798dd` (blob `456caf2209c81d11dec24942d0de961e6dfec157`)
Status: FROZEN BEFORE IMPLEMENTATION

The original contract plus this addendum are the authoritative frozen E7 contract. The original commit is not amended. Where this addendum is more specific than the original, the addendum governs; where it is silent, the original governs. Nothing here adds E8 scope, a new durable truth owner, or a numeric acceptance threshold.

Section numbers `§N` without prefix refer to the original contract; `A§N` refers to this addendum.

## A1. Deterministic benchmark identities (corrects §3, §5)

Real Vres owners generate task/episode/checkpoint/knowledge keys, database ids and wall-clock timestamps dynamically. The benchmark must still be reproducible.

1. **Aliases.** Every corpus object that a later operation, query or expectation refers to carries a stable, case-local logical alias (`^[a-z][a-z0-9_]{0,62}$`). Aliases are unique within a case. They are benchmark identities only and never become Vres keys.
2. **Real owners.** Scenario construction calls the real public owner APIs (E1 capture, E2 consolidate, E4 lifecycle, knowledge/source registration, procedure registration, etc.). **No direct SQL fixture shortcut** may create, alter or delete owner state to obtain stable keys or states. (Direct SQL is permitted only for read-only evidence collection and for the isolation/reset operations of §14.)
3. **Mapping.** The runner captures each durable runtime key returned by an owner call and records a case-local `alias → runtime_key` map (and its inverse). The map lives in the run process; it is not persisted as a truth owner.
4. **Expected evidence uses aliases.** `expected_evidence.json` refers only to aliases.
5. **Resolution before scoring.** Adapter output (runtime keys) is resolved back to aliases before scoring and result hashing. A returned runtime key with no alias in the case map is an **unmapped item**: it is scored as non-relevant/unknown by the metric rules (A2) and its raw runtime key is never written into the digested result (it is represented by the fixed token `unmapped` plus a per-case ordinal).
6. **Nondeterminism exclusion.** Generated database ids, UUID-derived keys and non-semantic wall-clock timestamps must not enter the normalized case result or the result digest.
7. **Semantic time.** A timestamp that matters for a temporal/update case comes from explicit case timeline semantics: each timeline operation declares an ordinal `t` (non-negative integer, strictly ordered within the case) and, where an owner API accepts an as-of/time input, the harness passes a deterministic timestamp derived solely as `epoch_anchor + t * step` with `epoch_anchor` and `step` declared in `scoring.json`. Where an owner derives time internally with no injectable input, the case is ordered by operation sequence only, and the case may assert only on **order**, never on absolute time. If a temporal case needs injectable time that an owner does not offer, that case is **not admissible** until chunk 0 documents a deterministic mechanism that goes through the owner (not SQL); this is a reported finding, not a silent shortcut.
8. **Proof requirement.** A required test builds the same corpus subset twice in two clean isolated databases (physical runtime keys will differ) and asserts: identical normalized per-case results and identical result digest; and, as a negative control, that the physical runtime key sets of the two builds are **not** asserted equal (so the test fails if keys leak into the digest by coincidence of a stubbed generator). The test also asserts that no runtime key, DB id, or timestamp substring appears in the serialized normalized result.

## A2. Exact scoring semantics (corrects §8, §7, §9)

`scoring.json` encodes these semantics and its parameters verbatim; it must not invent or alter them later. Any semantic ambiguity found during implementation is a contract-correction event (new addendum), not an implementation choice.

### A2.0 Common definitions

- **Case evidence labels** (in `expected_evidence.json`, by alias, per case): `relevant` (should be returned), `acceptable` (neither required nor penalized), `irrelevant` (should not be returned), `stale` (superseded/retired/revoked-lineage item that must not be returned as current), `conflict_pair` (alias groups that contradict each other), `premise` (declared false-premise alias set), `must_abstain` (boolean).
  Any returned item with no label is `unlabeled`; it is treated as **irrelevant** for irrelevant-memory rate and as non-relevant for precision, and is also listed in the case record so a corpus gap is visible.
- **Returned list** `R`: the normalized evidence pack (A4) after alias resolution, **in the adapter's native rank order**, truncated to the common budget. **Ordering/ties:** the pack is already totally ordered by the normalizer (rank, then a deterministic tie-break on alias string); metrics use that order. Metrics never re-sort.
- **Duplicates:** an alias appearing more than once in `R` counts **once** at its first position for relevance-based metrics (Recall, Precision@k set membership, coverage) and the extra occurrences are counted only by the duplicate-memory rate. Distinct runtime keys that resolve to the same alias are duplicates.
- **Top-k:** `R_k` = the first `min(k, |R|)` entries after duplicate collapse **preserving first occurrence order**. Values of `k` are listed in `scoring.json`.
- **N/A:** a metric whose denominator is zero for a case is `N/A` for that case: excluded from that metric's aggregates and counted in `n_excluded` with the reason `zero_denominator`. N/A is never imputed as 0 or 1.
- **Aggregation:** every metric reports both **micro** (sum numerators / sum denominators across non-excluded cases) and **macro** (unweighted mean of per-case values over non-excluded cases) and the aggregate lists `n_cases`, `n_excluded` and per-reason exclusion counts. Both are reported in every report; which one a later threshold gates is chosen at calibration time (§13) and recorded in `thresholds.json`, never changed afterward. Per-split aggregates are never pooled across splits.
- **Fractions** are exact rationals (integer numerator/denominator) in the digested result; decimal rendering to the scale in `scoring.json` is display-only.

### A2.1 Retrieval metrics

| Metric | Per-case numerator | Per-case denominator | Excluded (N/A) when | Notes |
|---|---|---|---|---|
| Recall@k | `\|R_k ∩ relevant\|` | `\|relevant\|` | `relevant` empty (e.g. abstention case) | unique aliases only |
| Precision@k | `\|R_k ∩ relevant\|` | `\|R_k\|` — number actually returned, **not** k | `R_k` empty | fewer-than-k does **not** pad the denominator to k; an empty return is N/A for precision and is scored by abstention/recall instead |
| Relevant-evidence coverage | `\|R ∩ relevant\|` (whole budgeted pack, not top-k) | `\|relevant\|` | `relevant` empty | measures pack completeness vs ranking quality |
| Irrelevant-memory rate | `\|{r ∈ R_k : r is irrelevant or unlabeled}\|` | `\|R_k\|` | `R_k` empty | `acceptable` items are in neither numerator nor excluded from the denominator |
| Duplicate-memory rate | `\|R\|_raw − \|unique(R)\|` | `\|R\|_raw` (before collapse) | `R` empty | counts exact alias repeats only; near-duplicate wording with different aliases is a **separate** label `near_duplicate_of` in expected evidence and is counted by the same rate only where that label is present |
| Stale-memory suppression | `\|stale \ R\|` (stale items **not** returned) | `\|stale\|` | `stale` empty | applies to current-intent queries; for explicitly historical-intent queries stale items are labeled `relevant` instead and this metric is N/A |
| Contradiction retrieval | `\|conflict_pairs where all members of the pair ∈ R_k, or the pair is surfaced as an explicit conflict by the owner's diagnostics\|` | `\|conflict_pairs\|` | no `conflict_pair` | a pair with only one side returned silently is a **miss** (and counts against operation conflict-recognition) |
| Premise-awareness accuracy | cases where the output flags the false premise per the owner's premise diagnostics and does not return premise-asserting items as supporting | cases with a non-empty `premise` set | no `premise` | boolean per case; only micro/macro coincide |
| Abstention correctness | cases where `\|R\| = 0` (or only items labeled `acceptable`) **and** `must_abstain` | cases with `must_abstain = true`; plus the symmetric false-abstention check: cases where `must_abstain = false` and `\|R\| = 0` are reported as `false_abstention` count | none; reported as two numbers: correct-abstention fraction and false-abstention fraction | a must-abstain case that returns any item labeled other than `acceptable` (including `unlabeled`) is an incorrect abstention |

A retrieval score or rank is never reported as a probability of truth.

### A2.2 Operation-faithfulness metrics (E1/E2/E4 direct)

Atomic unit: a **claim** (statement/field produced by an owner operation, identified by alias via the case's expected-claim list) and a **source fact** (an expected fact the cited source supports, by alias).

| Metric | Numerator | Denominator | N/A when |
|---|---|---|---|
| Source-support precision | produced claims whose expected-evidence entry marks them `supported` by a cited source alias | all produced claims | no claims produced |
| Omission (rate) | expected source facts **absent** from produced memory | all expected source facts | no expected source facts |
| Unsupported additions (rate) | produced claims with no support entry (`unsupported`) | all produced claims | no claims produced |

Equivalence of a produced claim with an expected claim/fact is decided **deterministically** by the comparison rule named in `scoring.json` (exact normalized-string equality on the canonical form defined there, or alias-keyed structured equality for structured fields). A model judge never decides equivalence for a protected result (A7). Dedup correctness, conflict recognition, temporal-update correctness and corruption-of-prior-memory are per-operation booleans aggregated as pass counts with the same N/A and macro/micro rules; corruption of prior memory, secret persistence and injection persistence are invariants (§12) and are never aggregated into rates.

### A2.3 Outcome metrics

Defined over the deterministic proxy worker (A5) per case and mode:

| Metric | Per-case value | Aggregation / N/A |
|---|---|---|
| Success | boolean: all deterministic criteria passed | success rate; N/A only if the case has no criteria (disallowed: such a case is inadmissible as outcome evidence) |
| Retries/rework | integer count of retry/rework actions in the trace | mean and distribution; paired difference vs `memory_disabled` |
| Tool/API-call equivalents | integer count of declared tool-call actions in the trace | as above |
| Criterion failures | integer count of failed criteria | as above |
| Harmful negative transfer | boolean: the mode failed (or incurred more failures) on a case where `memory_disabled` succeeded (or incurred fewer), **and** the trace shows use of a returned item labeled `irrelevant`, `stale` or `unlabeled` | rate over cases where `memory_disabled` was not already failing; N/A otherwise |
| Unnecessary reuse | boolean: the trace used a returned item on a case labeled `memory_not_needed` | rate over `memory_not_needed` cases |
| Token/runtime cost | token cost from the deterministic estimator over the normalized pack plus declared action cost units; wall time per F | reported separately; wall time never in the result digest |

## A3. Mechanical held-out isolation (corrects §3, §4)

Logical filtering is insufficient. The layout is physically separated:

```
benchmarks/experience_e7/
  manifest.json                  # immutable top-level manifest (below)
  scoring.json                   # shared, versioned, hashed; contains no case answers
  development/{corpus.jsonl, expected_evidence.json}
  heldout/{corpus.jsonl, expected_evidence.json}
  adversarial/{corpus.jsonl, expected_evidence.json}
  thresholds.json                # absent until calibration
```

`splits.json` from the original contract is replaced by `manifest.json`.

1. **Manifest.** Lists, per split bundle: relative file paths, a SHA-256 for each file, the set of case ids, and a bundle digest. It lists **no expected answers**. It is committed with the bundles. A bundle whose files or digests disagree with the manifest fails closed.
2. **Disjoint ids.** Case ids and every alias namespace are unique across bundles (alias prefix `dev_`, `held_`, `adv_` enforced by the loader).
3. **Development tooling never opens held-out bytes.** The loader API is `load_bundle(split, ...)`. The development/threshold-derivation entry point accepts only `development` and `adversarial` and **must reject**, before opening any file: the `heldout` split name, any path under `heldout/`, any case id registered to the held-out bundle, and the held-out bundle/expected-evidence digests. It resolves paths from the manifest, canonicalizes them, and refuses symlinks/path traversal/junctions that escape the split directory. Tests assert (a) that those rejections occur, and (b) with an open-call spy that a development run performs **zero** file opens under `heldout/`.
4. **Held-out loading only after threshold freeze.** The held-out loader requires a verified, committed `thresholds.json` whose digest matches the checkpointed identity, and refuses otherwise. During development the held-out bundle may exist only as sealed bytes: it is authored and committed in a **separate commit** by a step that does not run development replay, and its expected-evidence file is never read by any development, scoring-calibration or debugging command.
5. **Temporal/update discipline.** Development may test temporal/update **mechanisms** using different labelled fixtures. The specific held-out temporal/update acceptance cases and their expected evidence appear **only** in `heldout/` and must not be semantically copied (same scenario shape with renamed aliases counts as a copy) into development. The author must record, in the sealed commit message, that no held-out scenario text was copied; a test checks that no held-out query string or fact string appears verbatim in development/adversarial bundles.
6. **Consumed-version rule unchanged (§4).** A held-out version that influenced any code/scoring/policy/corpus/threshold change is consumed and must be replaced before the final run; the manifest records `heldout_version` and `consumed` history.

## A4. Fair four-mode normalization (corrects §6)

One adapter output contract serves `memory_disabled`, `raw_refind`, `current_vres`, `candidate_hybrid`.

1. **Same inputs.** Each mode receives exactly the case's public task/query input (query text, project scope, temporal intent/as-of, declared premises, capability keys where the case declares them). No mode receives extra hints.
2. **Native retrieval through real owners.** Each mode calls its own real owner with its native gates intact: `raw_refind` → `KnowledgeService.chunk_search`; `current_vres` → knowledge search plus `ProcedureService.find_matches`; `candidate_hybrid` → `ExperienceRetrievalService.retrieve`; `memory_disabled` → none. Native eligibility, scope, revocation and lifecycle gates are **not weakened or replaced** by the benchmark.
3. **Benchmark-only normalizer.** A single normalizer converts each owner's *eligible* results to one **closed** `EvidencePack` shape: ordered list of `{alias, kind, text_ref, rank}` where `kind ∈ {knowledge, chunk, procedure, experience}`; no raw owner payloads, scores, or runtime keys survive; the shape is validated strictly (unknown fields rejected). The normalizer does not filter on relevance and does not add eligibility beyond the owner's; it only maps, orders, de-aliases and truncates.
4. **Common budget.** All modes are evaluated at the same top-k list (from `scoring.json`) and truncated to the same maximum normalized evidence/context budget measured in the deterministic token estimator's units (budget value from `scoring.json`, fixed before development replay, not a threshold). Truncation is applied by the normalizer after native ordering; no mode gets extra budget.
5. **`current_vres` combination rule.** Knowledge results and procedure matches are merged deterministically: concatenated in a fixed order defined in `scoring.json` (default: ordered by each source's native rank, interleaved one-for-one starting with knowledge, ties by alias string), duplicates collapsed, then subjected to the same common budget as every other mode. `current_vres` does not receive more items or tokens than `candidate_hybrid` merely because it has two native calls, and `candidate_hybrid` does not receive more because its native API returns more fields.
6. **Same serializer and estimator.** One canonical serializer (A1/§5 canonical JSON) renders the pack; one versioned deterministic token estimator (named and hashed in `scoring.json`) measures it. The estimator input is the canonical normalized pack, never native owner output.
7. **Same timing boundary.** Latency covers the native owner call(s) **plus** normalization, from immediately before the first owner call to the completion of the normalized pack, for every mode (including `memory_disabled`, which times only the no-op path). Setup is excluded (A6).
8. Any native-gate difference that disadvantages a mode (for example an owner not enforcing a scope rule that others do) is reported as a finding; it is not equalized by loosening or tightening one mode privately.

## A5. Deterministic outcome proxy worker (corrects §9)

1. **Inputs.** The proxy worker consumes only (a) the public case/task input and (b) the normalized `EvidencePack` of its mode. It cannot access `expected_evidence`, scoring rules that reveal answers, `thresholds.json`, or any other split's data **while acting**; the runner passes it a value object that physically does not contain them, and a test asserts the worker module has no import/path access to those artifacts (the worker is invoked in a function whose arguments are the only data source; the answer files are loaded by the scorer after the trace is complete).
2. **Identity across modes.** The same worker code and policy run for all four modes. Modes differ only by the pack they supply.
3. **Decision contract.** The worker applies a fixed, versioned, pure decision procedure over a declared task template: for each template step it either takes a declared action, chooses among declared options using only information present in the task input or the pack, retries a step per the template's declared retry rule, or abstains/asks per the template. It emits a bounded trace (maximum steps declared in `scoring.json`) of `{step, action, used_aliases[], retry:bool, tool_call:bool}`.
4. **Mechanical recording.** Required-fact use (which pack aliases were used), forbidden actions, retries/rework and tool/API-call equivalents are recorded mechanically from the trace, not inferred.
5. **Scoring afterward.** After the trace is complete, the scorer loads the private expected evidence/criteria for the case and computes the A2.3 metrics.
6. **Admissibility.** A deterministic outcome case that cannot satisfy this separation cannot be used as protected outcome evidence. It may be retained as non-protected supplementary evidence only if labeled so.
7. The optional real model-worker cohort remains extra, advisory and non-gating (§9, A7).

## A6. Performance methodology (corrects §8, §14)

These are measurement rules, frozen before development replay; they are not acceptance thresholds.

1. **Timer.** `time.perf_counter_ns` (monotonic, high-resolution) for all latency.
2. **Excluded from retrieval latency:** migrations, database creation/reset, corpus load, scenario construction, alias mapping, scoring. Only the A4.7 boundary is timed.
3. **Warm-up.** For each (mode, case, scale) one **unrecorded warm-up call** immediately precedes the measured repeats, in the same process and connection as the measured calls. Additionally, the process performs one unrecorded pass over all modes before measurement begins. Cold measurements (first call in a fresh process/connection, no warm-up) are an optional separate series labelled `cold`; warm series are labelled `warm`. Cold and warm values are never mixed or averaged together.
4. **Repeat count.** Read from `scoring.json` (`latency.repeats`, an integer fixed in the versioned scoring configuration before development replay). It is a measurement parameter, not a pass/fail value. The value used is recorded in every run.
5. **Order.** Mode order is **rotated** per (case, repeat): a fixed Latin-square rotation over the four modes defined in `scoring.json`, so each mode occupies each position equally often; no mode always runs first. The rotation is deterministic (no RNG).
6. **Statistics.** Over the measured repeat samples of a cohort, **p50** and **p95** use the nearest-rank method on ascending-sorted samples (`rank = ceil(p/100 · n)`, 1-based); **max** is the maximum; also report `n` and `min`. Per-case latency is the nearest-rank p50 over repeats; split-level latency statistics are computed over the pooled per-repeat samples of the cohort and over per-case values separately, both labeled.
7. **Same conditions.** All four modes in a comparison cohort run in the same process, same environment and same database state/connection pool configuration, interleaved per A6.5. Cross-run/cross-machine comparisons are labelled incomparable unless the environment identity matches.
8. **Token cost.** The deterministic estimator (A4.6) is applied to the canonical normalized pack; no model tokenizer.
9. **Identity.** Hardware (CPU model/cores, RAM), OS version, Python version, PostgreSQL server version/settings that affect planning, and DB scale parameters are recorded in the run record.
10. Latency and token values are excluded from the result digest (§5) but are covered by a separate `measurement_record` digest; the measurement record is reproducible-in-method, not value-identical.

## A7. Model-judge calibration (corrects §15)

1. If any model judge is used, before it is used on any benchmark output it is **calibrated** against deterministic and/or human-labelled **development** samples. The calibration record contains: calibration-set digest, judge model identifier, effort, prompt digest, and the agreement/error result (counts and rates against the labels).
2. Held-out acceptance answers/expected evidence are never used for calibration.
3. The judge's output is advisory and never the sole authority for any protected pass/fail; deterministic scoring remains protected authority.
4. If no model judge is used, the run record states `model_judge: not_used`. Absence of that field is a malformed record.

## A8. Final acceptance dimensions (extends §13, §20)

Final E7 acceptance requires **all** of the following dimensions, each independently evidenced; none may be removed, waived or averaged into another:

1. No security/scope/provenance regression (all §11 cases and all §12 invariants hold; E1–E6 existing suites unaffected).
2. Measurable **net outcome benefit** on relevant tasks (`candidate_hybrid` versus the baselines on the outcome metrics of A2.3, on relevant — non-`memory_not_needed` — cases).
3. **No material negative-transfer increase** (harmful negative transfer and unnecessary reuse vs the baselines).
4. **Bounded latency/token overhead** (per A6, against calibrated limits from `thresholds.json`).
5. **Improved or non-inferior memory-operation faithfulness** (A2.2, against the baselines/prior behavior as defined at calibration).
6. **Exact reproducible evidence** (A1 proof, digests, run records, result digest reproducibility).

`thresholds.json` later supplies calibrated numeric gates where numeric gates are appropriate for dimensions 2–5. It cannot delete or bypass any dimension; a dimension without a numeric gate must be justified in writing in `thresholds.json` and is then judged by the comparative rule recorded there. Every fail-closed invariant (§12) remains independently zero-tolerance and is not part of any dimension average.

## A9. Flood / amplification subcriteria (extends §11 cases 12–15)

The red tests for cases 12–15 must prove, beyond the original text:

1. **Frequency is not trust.** Repeated retrieval or use frequency alone cannot raise trust, authority, importance or ranking weight of an item.
2. **Varied poison from one lineage.** Semantically varied repeated poison from one source/task/lineage cannot dominate retrieval or consolidation through recurrence (varied wording is built from a fixed corpus of paraphrases in `adversarial/`, not generated at run time).
3. **Burst/flood fails closed.** Suspicious burst/flood patterns quarantine or fail closed (rejected/held for review through an existing owner path) rather than becoming useful consolidation merely by volume.
4. **Budgets are labelled.** Any per-source/task/lineage write or influence budget adopted **after** RED evidence is explicitly distinguished from the pre-existing global `MAX_OPEN_PROPOSED=20` safety cap, with its own name, scope and test. The global cap is not evidence for the new control and is not removed or reinterpreted.
5. **Authority needs independent trusted evidence.** Recurrence cannot raise authority without independent trusted evidence (case 15).
6. **Diversity = independent lineage.** Source diversity means independent evidence/lineage, not merely differently worded rows; the test builds rows with differing text from one lineage and asserts they count as one lineage for diversity.
7. **No invented budget.** No numeric budget is chosen until the RED fixture shows what behavior needs bounding. A budget value, once chosen, is a product-safety control recorded in the hardening addendum for that chunk (§16) with its RED evidence; quality thresholds still follow development calibration (§13).

## A10. Red-first per chunk (extends §16, §19)

Every implementation chunk — loader/canonicalization, corpus validation, adapters/normalizer, scoring, outcome runner, streaming runner, performance harness, and any hardening — starts with its contract test written and observed **RED** (failing for the intended reason), then the smallest implementation that turns it **GREEN**. Chunk evidence records the RED observation (test name + failure reason) and the GREEN result. Security hardening of an E1–E6 owner additionally requires the explicit adversarial RED before any modification to that owner's behavior (§11, §16).

## A11. Cross-reference: requirement ownership

| Requirement | Owning clause |
|---|---|
| Local isolated worktree/identity, no migration by default | §2, §21 |
| Four baseline modes | §6, A4 |
| Benchmark assets, separate hashed bundles | §3, A3 |
| Deterministic identity/reproducibility | §5, A1 |
| Corpus coverage and temporal reserved for held-out | §3, A3.5 |
| Operation faithfulness | §7, A2.2 |
| Retrieval metrics | §8, A2.1 |
| Outcome / negative transfer | §9, A2.3, A5 |
| Streaming learning | §10 |
| Security / red team cases 1–18 | §11, A9 |
| Invariants vs thresholds | §12, A8 |
| Threshold calibration/freeze, held-out invalidation | §13, §4, A3.4, A3.6 |
| Latency/token/scale | §14, A6 |
| Model judge limitation and calibration | §15, A7 |
| Hardening/versioning | §16, A10 |
| No E8, no new truth owner | §1, §2, §17 |
| Final evidence requirements | §20, A8 |

## A12. Frozen constraints of this addendum

- No numeric acceptance threshold is introduced. Parameters named here (`latency.repeats`, budgets, k values, step caps, epoch anchor/step) are measurement/configuration parameters that `scoring.json` fixes before development replay; none is a pass/fail gate.
- No E8: no automatic memory injection into Chairman context.
- No new durable truth owner: alias maps, manifests and run records are Git artifacts or ephemeral process state.
- No implementation code, data or benchmark files are created by this addendum.
