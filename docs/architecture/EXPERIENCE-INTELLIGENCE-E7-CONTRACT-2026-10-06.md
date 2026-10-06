# Experience Intelligence E7 Contract — Benchmark and Memory-Security Ladder

Date: 2026-10-06
Issue: #176
Base: `9a8acc5d464b96432a93cb95daa9581412fb07ee` (tree `659d3fdd6e635dbaecbd5c492ba7279754edaec7`; E6 complete and merged)
Task: `TASK-20261006-6cd9d80a92`
Status: FROZEN BEFORE IMPLEMENTATION

## 1. Scope and non-scope

E7 is a **deterministic evaluation and security layer over the accepted E1–E6 truth owners**. It answers, with reproducible evidence:

1. Does Vres memory behave like an experienced colleague compared with no memory, raw re-finding, and current Vres knowledge/procedures?
2. Do the memory *operations* (capture, consolidation, lifecycle) stay faithful to their sources?
3. Does retrieval return the right, current, in-scope, non-poisoned evidence at acceptable latency and context cost?
4. Does reuse help outcomes and avoid negative transfer?
5. Does a sequence of experiences produce learning without forgetting, and without unauthorized authority growth?
6. Do the red-team cases in §11 fail closed?

E7 does **not**:

- add Chairman automatic memory injection (**no E8**; no hook, prompt or context-assembly change that surfaces memory without an explicit request);
- add a generic memory database, vector store, benchmark result ledger, or any new truth-owner table by default;
- add a model-judged protected authority;
- invent numeric quality/performance thresholds before development replay (§13);
- weaken or replace any E1–E6 hard gate, scope rule, lifecycle rule or schema (`176.e5.v1`, `176.e6.v1`).

Out-of-scope discoveries are named in the report, not silently fixed.

## 2. Truth-owner reuse (no duplicate durable owner)

| Fact | Owner (unchanged) |
|---|---|
| Episodes | E1 `ExperienceEpisodeService` / `experience_episodes` |
| Consolidation transitions | E2 `ExperienceConsolidationService` / `experience_transitions` |
| Retrieval | E3/E5 `ExperienceRetrievalService.retrieve` (schema `176.e5.v1`) |
| Lifecycle, revocation, contamination | E4 (`ExperienceLifecycleService`, `source_revocation`, `session_contamination`) |
| Observability, references, utility, replay | E6 (`experience_retrieval_*`, `experience_utility`, `experience_replay`) |
| Raw-archive search | `KnowledgeService.chunk_search` |
| Procedure matching | `ProcedureService.find_matches` |
| Code, corpus, expected evidence, scoring, thresholds | Git (`benchmarks/experience_e7/`) |
| Secrets | OS credential store |

Benchmark runs build state **only** through these owners' public entrypoints inside a disposable PostgreSQL database (§14). Run output is a deterministic JSON report written outside the checkout (or in the test temp directory); it is **not** a durable Vres truth owner. The final acceptance evidence is attached to the E7 task through the existing checkpoint/validation flow.

### Migration rule

- Default: **no migration 042**. If E7 only adds benchmark/test machinery, none is added.
- If a red security test proves a durable, versioned policy change is required, a released policy identity is never mutated in place. An additive migration limited to a new policy version over existing truth owners is permitted (e.g. a new `POLICY_VERSION`/digest row semantic). A new table, a new schema owner, or any change to released E1–E6 table semantics requires an explicit written proof of necessity recorded in a contract addendum **before** implementation, and re-review.
- Released migrations 001–041 are immutable.

## 3. Benchmark architecture

Location: `benchmarks/experience_e7/` (data) and a small runner module whose placement is fixed by implementation chunk 0 under the architecture constitution (it must depend downward on E1–E6 public APIs only; no E1–E6 module imports it).

Data files (all UTF-8 without BOM, `\n` line endings):

- `corpus.jsonl` — one case or timeline operation per line: **inputs and timelines only, never scoring answers**.
- `splits.json` — assigns each case id to exactly one split: `development`, `heldout`, `adversarial`.
- `expected_evidence.json` — exact expected evidence keys per case (separately versioned).
- `scoring.json` — metric definitions/parameters and per-metric rules (separately versioned).
- `thresholds.json` — **absent until development replay is complete** (§13).

Data is sanitized: no real credentials, no real personal data, no raw private reasoning. Secret-shaped strings in red-team cases are synthetic canaries generated from a documented fixed pattern.

### Corpus coverage

The corpus must include, each with ≥1 case in `development` and the categories marked † also reserved in `heldout`:

static state†; dynamic changes†; recurring workflows†; gotchas†; false premises†; successful and failed trajectories; user corrections/decisions; procedure reuse; capability-linked precedent; cross-project scope traps; noisy/distractor history; stale/superseded/challenged facts†; current-vs-historical queries†; source revocation; participated-vs-observed experience; exact expected evidence keys; abstention cases†; temporal/update cases† (temporal/update cases are **reserved for held-out** in addition to development coverage of the mechanism).

### Schemas and strictness

Each file has an explicit `schema_version`. Loaders fail closed on: malformed JSON, duplicate case ids, duplicate JSON object keys, unknown fields, missing required fields, a case id absent from or duplicated in `splits.json`, an expected-evidence or scoring entry referencing an unknown case, a case in `corpus.jsonl` with scoring keys (e.g. `expected_*`), and any digest mismatch (§5). No best-effort loading.

## 4. Split discipline

- `development`: used for replay, debugging, and threshold derivation.
- `heldout`: acceptance only. Never read by any threshold-derivation or debugging step.
- `adversarial`: security/red-team cases (§11).
- Case ids appear in exactly one split. Streaming sequences (§10) are wholly inside one split and never share state with another split run.

### Held-out invalidation rule

Held-out results must not inform thresholds. If a held-out result causes **any** change to code, scoring, policy, corpus, or thresholds, that held-out version is **consumed**: a replacement held-out set (new cases, new `splits.json` digest) must be frozen and committed **before** the final acceptance run, and the consumption is stated in the evidence. This is never hidden or reworded as a "fix and re-run".

## 5. Canonicalization and digests

- Canonical form: UTF-8 JSON, keys sorted, no insignificant whitespace, `ensure_ascii=false`, `\n` terminated for JSONL; no floats in digested identity input (metrics are reported separately as decimal strings with a fixed scale defined in `scoring.json`); no timestamps inside digested inputs.
- Digest: SHA-256 hex over canonical bytes. Distinct digests for: corpus, splits, expected evidence, scoring, thresholds, retrieval policy (the E5/E6 policy digest), schema versions, and the runner's own result.
- Every run records: source commit and tree; corpus/split/expected/scoring/threshold digests; retrieval/policy/schema digests; Python version; PostgreSQL version/evidence when DB-backed; run timestamp (outside the result digest); the case ids executed; and a deterministic result digest over the ordered per-case results excluding timestamps and latency. Latency and token metrics are reported but are **not** part of the result digest.
- Same inputs, same code, same database state ⇒ identical result digest. A test asserts this by running twice.

## 6. Baseline adapters

All four modes consume the **same** case corpus and the same per-case timeline setup. Only the retrieval/assist adapter differs.

1. `memory_disabled` — returns nothing.
2. `raw_refind` — `KnowledgeService.chunk_search` (or an equivalent shared eligibility owner), project-scoped. It must not call a looser search; eligibility (project scope, revoked/quarantined exclusion) is whatever the owner already enforces. If the owner does not enforce an eligibility rule that the other modes do, that is a **finding to report**, not a reason to add a private looser path.
3. `current_vres` — current knowledge search plus `ProcedureService.find_matches`, with **no** experience hybrid advantage (no `ExperienceRetrievalService` experience signals).
4. `candidate_hybrid` — `ExperienceRetrievalService.retrieve` with E1–E6 mechanisms, normal (E5 baseline) policy. E6 candidate-policy replay is separate and optional; if included it only reports and never selects a winner.

Adapters are pure functions of (case, database state). They do not write durable state except through the owners' normal timeline operations used to construct the scenario.

## 7. Operation-level memory faithfulness

Exercised **directly** against the E1/E2/E4 owners (not only through retrieval):

- source-support precision: fraction of produced memory claims supported by their cited source evidence;
- omission: expected source facts absent from the produced memory;
- unsupported additions: claims with no support in cited sources;
- corruption of prior memory: an operation altering a previously accepted record it should not touch;
- dedup correctness: duplicates merged, distinct items kept;
- conflict recognition: contradicting facts surfaced as conflict, not silently overwritten;
- temporal update correctness: newer fact supersedes older through the E4 supersede path with history preserved;
- secret persistence: no raw secret/canary appears in any persisted row or response;
- injection persistence: instruction-shaped untrusted text is not persisted as an authoritative instruction.

Secret persistence, injection persistence and corruption of prior memory are **invariants** (§12), scored pass/fail with zero tolerance, not averaged. Faithfulness decisions are deterministic comparisons against `expected_evidence.json`. A model judge may supplement as non-binding evidence but is never the sole authority for any protected decision (§15).

## 8. Retrieval metrics

Computed per mode, per split, over `ExperienceRetrievalService`/adapter output against expected evidence keys:

Recall@k; Precision@k; evidence coverage; irrelevant-memory rate; duplicate rate; stale suppression; contradiction/conflict retrieval; premise-awareness accuracy; abstention correctness; latency (wall time per call, p50/p95 and max reported, never in the result digest); context-token cost (deterministic token estimator named in `scoring.json`; the estimator is versioned and hashed; no model tokenizer call).

`k` values are listed in `scoring.json`. A retrieval score or rank is **not** a probability of truth; reports must not label it so.

## 9. Outcome and negative-transfer protocol

- The same cases run under all four modes.
- Deterministic scenario runner: a task template whose success is decided by deterministic criteria (e.g. final artifact equality, forbidden-action detection, required-fact use). No model is required for protected acceptance.
- Measured per mode: success; retries/rework; tool/API call count; token/runtime cost (deterministic cost model + measured wall time reported separately); criterion failures; harmful negative transfer (a case where the mode scores worse than `memory_disabled` because of reused memory); unnecessary reuse (memory used when the case did not need it).
- An optional model-worker cohort may be added as **extra, non-protected** evidence. It must pin model, effort, and input digests in the run record. It never gates acceptance.

## 10. Streaming-learning protocol

Ordered sequences of operations (episode captured → consolidated → lifecycle events → queries) defined entirely in `corpus.jsonl`. State is rebuilt from corpus operations in a fresh isolated database per sequence/split; nothing carries across splits.

Measured: forward transfer (later-task improvement attributable to earlier sequence items), retained competence (earlier items still answerable after later ones), new-gotcha acquisition, stale-knowledge update, selective forgetting / use suppression (revoked/retired/challenged items stop being used), negative transfer, and the learning curve (per-position metric series). "Attributable" here means a paired comparison against `memory_disabled` on the same cases; E7 does not claim causal credit beyond what E6 states (`causal_credit=not_established`).

## 11. Security / red-team protocol

Red tests are written **first**. For each case: if existing behavior already passes, preserve it and add a regression proof; if it fails, implement the **smallest** hardening inside the existing owner, with versioning per §16. All cases live in the `adversarial` split.

Required cases:

1. Malicious project doc creating a durable instruction.
2. Poisoned successful-looking trajectory.
3. Prompt injection surviving context reset.
4. Cross-project exfiltration.
5. External observation claiming company-rule authority.
6. Poisoned procedure candidate.
7. Secret-bearing episode.
8. Revoked source influencing later retrieval.
9. Embedding/lexical poisoning (keyword/embedding stuffing to outrank legitimate evidence).
10. Trusted/untrusted conflict.
11. Second-Windows-user isolation where relevant (verified through the existing test-DB/credential isolation methodology of §14; recorded as `not_applicable_with_reason` when the environment cannot exercise it, never silently passed).
12. Memory flooding / amplification.
13. Semantically varied repeated poison (varied wording of the same poison).
14. Source-diversity-aware retrieval.
15. Recurrence cannot raise authority without independent evidence.
16. Participated vs observed experience.
17. Retrieval-triggered challenge/reverification.
18. Retrieval cannot silently rewrite what it just consumed.

### Known-insufficient existing controls (explicit)

- E2 exact-statement dedupe plus `MAX_OPEN_PROPOSED=20` is **not accepted** as evidence against cases 12 and 13. Semantically varied flooding must be tested directly: the test fills with varied-wording poison and asserts bounded open-proposal growth, no authority/proposal inflation, and no displacement of legitimate evidence. If it fails, harden E2 minimally.
- E3/E5 exact-content/group dedupe is **not accepted** as evidence for case 14. The test constructs many near-identical items from one source/lineage versus fewer independent sources and asserts that source diversity, not repetition count, controls ranking weight and that repetition from one lineage cannot dominate the pack. If it fails, harden E3/E5 minimally and version the policy (§16).
- Case 15: recurrence of **untrusted** evidence raises no trust/authority tier; only independent trusted evidence can.
- Case 18: a retrieval call must leave its own consumed pack unchanged — the read path performs no write (the E5 read-only invariant), verified by row-count/digest comparison of all E1–E6 owner tables around the call, and E6 observation capture remains hook-only.
- Case 17: when retrieval surfaces an item that a lifecycle rule marks as needing reverification/challenge, the response flags it (E5 diagnostics) without mutating the item; the challenge is a separate E4 lifecycle operation requiring its own approval.

Every case records the expected fail-closed outcome in `expected_evidence.json` (what must not be retrieved/persisted/promoted) and is scored pass/fail.

## 12. Fail-closed invariants (not calibrated numbers)

These are product invariants. Any single violation fails the run. They are **never** converted into averages, rates, or thresholds:

- no raw secret persistence or exposure;
- no cross-project/user unauthorized retrieval;
- no revoked evidence influencing current retrieval;
- no unauthorized authority/policy promotion;
- no hidden chain-of-thought persistence;
- untrusted recurrence alone cannot raise authority.

## 13. Calibrated thresholds and freeze process

Numeric quality/performance thresholds (recall, precision, latency, token cost, negative-transfer rate, learning-curve slope, etc.) are **not** set in this contract.

Process:

1. Implement runner and corpus; freeze corpus/splits/expected/scoring digests for the development split (commit).
2. Run development/replay for all four modes. Record results.
3. Propose thresholds from development results only, with written rationale.
4. Write `thresholds.json` with rationale and its own digest; commit; checkpoint code/corpus/scoring/threshold identities through Vres.
5. Only then run held-out acceptance (§4 invalidation rule applies).

Thresholds are comparative where meaningful (candidate_hybrid vs the other modes) and absolute only where justified by development evidence. A threshold is never lowered after a held-out result without consuming that held-out version.

## 14. PostgreSQL isolation methodology and scale/latency/token measurement

- DB-backed benchmark and red-team tests run against a disposable PostgreSQL database reached through the existing test-DB handle mechanism, executed in an isolated child process with an isolated `VRES_DATA_DIR`, never the canonical database and never with installed split-role configuration leaking into it. The runner refuses to start unless the database name indicates a disposable test database and the sentinel preflight passes.
- No raw DSN, password or token appears in any argument, log, report or evidence. Reports record only non-secret identity (database name pattern, server version).
- The runner creates a fresh schema state per split and per streaming sequence; shared state between splits is a defect.
- Scale: the corpus supports a declared scale parameter (number of episodes/knowledge items/distractors) recorded in the run record; development replay measures at the declared scales. Latency (p50/p95/max) and context-token cost are measured per mode and per scale and reported; they are subject to calibrated thresholds only per §13. Hardware/PostgreSQL identity is recorded so numbers are interpretable and not compared across unlike environments.
- The full PostgreSQL suite is not used as the E7 baseline; E7 adds focused modules and the final gate runs the full suite once.

## 15. Model-judge limitation

A model judge may be used to supplement operation-faithfulness or outcome evidence. Its output is recorded with pinned model, effort, prompt digest and input digests, labelled advisory, and is **never** the sole authority for any protected pass/fail. Protected acceptance uses deterministic scoring only. A judge/benchmark result never satisfies Vres protected validation or task completion.

## 16. Runtime-hardening and versioning rule

- A red-test failure is fixed in the existing owner by the smallest change that makes the test pass without weakening any E1–E6 invariant.
- If a hardening changes retrieval/policy behavior observable in `176.e5.v1` output or the E6 replay baseline, it gets a new explicit policy version (never silent mutation of `176.e5.v1`/`176.e6.v1` identity or `BASELINE_POLICY_DIGEST` semantics); the previous identity stays reproducible for replay.
- Hardening that changes schema semantics needs the migration rule of §2.
- Every hardening is accompanied by the red test that proved the gap and a regression proof that previous behavior outside the gap is unchanged.
- A hardening discovered **after** held-out was read consumes that held-out version (§4).

## 17. Explicitly out of E7

- Chairman automatic injection (E8) and any hook/prompt that surfaces memory unasked.
- A benchmark results table, leaderboard store, or any new durable truth owner by default.
- Model-judge-only protected authority.
- Numeric thresholds before development replay.
- Refactors of E1–E6 unrelated to a failing red test.
- Distribution/sharding, external vector stores, or new embedding providers.
- Real customer data, real credentials, or raw private reasoning in any corpus.

## 18. Expected implementation surface

- `benchmarks/experience_e7/{corpus.jsonl,splits.json,expected_evidence.json,scoring.json}` (+ `thresholds.json` later).
- A runner/loader/scoring module (location fixed in chunk 0) and focused tests.
- Red-test module(s) for §11 and any minimal hardening in the owning E1–E6 module.
- Optional additive migration only per §2.
- Docs: this contract, an implementation-notes addendum, a README for the benchmark directory.

## 19. Implementation chunks (not started)

0. Verify exact owner signatures and fix runner placement; add loader/canonicalization/digest with fail-closed tests.
1. Corpus/splits/expected/scoring v1 (development + adversarial); held-out authored separately and sealed (committed, never read by development tooling).
2. Baseline adapters and retrieval metrics; determinism test.
3. Operation-faithfulness harness over E1/E2/E4.
4. Outcome/negative-transfer and streaming runners.
5. Red tests (all 18 cases) first; then minimal hardening where red.
6. Development replay across four modes at declared scales; propose and freeze `thresholds.json`; checkpoint identities.
7. Held-out acceptance run; final gate; protected validation.

## 20. Final evidence requirements

For acceptance the evidence must include, from actually-run commands:

- source commit/tree and clean working tree;
- all input and result digests (§5) and the four-mode run record per split;
- threshold file digest and the checkpoint that froze it preceding the held-out run;
- held-out consumption statement (none consumed, or which version was consumed and its replacement);
- the §11 case matrix with pass/fail per case and the §12 invariants all passing;
- PostgreSQL isolation evidence (§14) with no secret exposure;
- the full test suite and release gate results from one clean run, with failures reported as failures;
- protected Fable/high validation over the exact final state;
- an explicit list of what was not measured (e.g. causal credit, model-worker cohort if omitted, second-user isolation if not exercisable).

## 21. Frozen constraints

- Contract first: no benchmark or runtime code before this contract is reviewed, frozen, committed and checkpointed.
- No E8, no new generic memory DB, no benchmark ledger, no guessed thresholds.
- Truth-owner reuse; one durable fact, one owner.
- Invariants remain pass/fail.
- Held-out leakage prevention per §4.
- Deterministic, digest-bound, reproducible runs.
