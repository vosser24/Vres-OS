# E7 Chunk 1 — repair findings (2026-10-06)

Scope: Chunk 1 execution-fidelity repair (review Message G, R1–R11). Benchmark data/config,
the benchmark foundation/schema, Chunk 1 tests/audit and this document only. No E1–E6 runtime
owner was modified. Chunk 2 has not started.

## F1. OWNER GAP — NO PUBLIC OBSERVED-EPISODE WRITER CURRENTLY EXISTS

- The E1 episode table supports `participation = observed`.
- The public E1 capture path (`ExperienceEpisodeService.capture`) is participated-only.
- No public owner entry exists for observed or imported episodes.
- Direct SQL into the episode table is forbidden for the harness (it would bypass the owner).

Consequences recorded in Chunk 1:

- `episode_capture` is always participated and carries an explicit `validation: none|passed`.
- `episode_observe` is a distinct timeline op, listed in `OPERATION_OWNERS` with
  `owner_gap=true`, `owner=null`, `method=null` and a gap record.
- Cases that need an observed episode (dev participated-vs-observed, adv participation forgery
  and the observed-episode poisoned trajectory) use `episode_observe`.
- An observed episode can never support a `validated_novel` consolidation (tested).
- **E7 execution of any case containing `episode_observe` stays fail-closed until a governed
  owner change adds a public observed-episode writer.** That change is outside E7 and is not
  made here.

## F2. Approval-key ambiguity (carried to Chunk 2)

Lifecycle ops, `source_revoke`, `procedure_accept` and possibly `source_add` require an
`approval_key` at the public owner. The harness must not fabricate user approval. Chunk 2 must
record this as an isolated-runtime approval fixture (not a user approval) or leave those ops
unexecuted. Not resolved in Chunk 1.

## F3. Repairs

- R1: `scoring.json` carries closed, versioned `metric_semantics` (no formulas/thresholds).
- R2: immutable op→owner map `OPERATION_OWNERS`, alias-kind/order ledger.
- R3: `experience_consolidate` matches E2 (polarity, trigger, subject_key, title, statement,
  1..10 evidence with episode alias + RFC-6901 pointer + literal quote).
- R5: `knowledge_attach_source` → `SourceService.attach_evidence`; revocation requires an
  explicit source→knowledge edge, attached before revocation.
- R6: closed `knowledge_type`; `dev_temporal_refresh` attaches a source before refresh.
- R7: security cases 6 (baseline + `procedure_candidate`), 12 (flood through E2),
  13 (varied poison through E2, one lineage), 17 (`lifecycle_challenge` before retrieval).
- R8 accepted unchanged: `capability` arg, `<<CANARY_1>>`, the 19 security assertion names.
