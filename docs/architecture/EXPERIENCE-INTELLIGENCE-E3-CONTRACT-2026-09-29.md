# Experience Intelligence E3 Contract — Unified Experience Retrieval

Date: 2026-09-29
Issue: #176
Base: `74c6445228a922db2622806f27e3c49a6c3454a7` (E1 PR #179 and E2 PR #180 merged)
Branch: `issue-176-e3-unified-experience-retrieval`
Frozen plan: branch `docs-176-experience-intelligence-plan-20260927`, commit `34f45afa0fb8d5a6a90bef53dec58d9ecef1093d`, file `docs/architecture/EXPERIENCE-INTELLIGENCE-PLAN-2026-09-27.md` (tranche E3). The plan is intentionally not duplicated here.

## Scope

E3 adds exactly one thing: a **read-only, staged, scope-first, trust-aware retrieval service** that reads the existing truth owners and returns one bounded, evidence-linked **experience pack**.

E3 has no schema change, no new store, no durable write of any kind, no Chairman/hook injection (E8), no revocation/supersession/refresh mutation (E4), no capability/procedure experience scoring (E5), no retrieval observations or utility credit (E6), no benchmark thresholds (E7), no #165+ work.

## Status of discovery (verified in the tree at the base commit)

| Area | Current owner / behaviour |
|---|---|
| Lexical knowledge | `KnowledgeService.search`: `search_vector` FTS + ILIKE over `knowledge_items`; excludes only `rejected`/`superseded`; **`project_id=None` returns every project**; no `valid_from/valid_to/review_after` filtering; no company-approval gate on `project_id IS NULL`. |
| Chunk / semantic | `chunk_search`, `EmbeddingService.semantic_search` over `knowledge_chunks`; exclude `challenged`; source must be `active`; project filter admits `project_id IS NULL` items without checking `scope_approval_event_id`; local-cosine fallback is capped at 5000 rows and reports `possibly_truncated`. Embeddings are optional (`EmbeddingUnavailable`). |
| Fusion | `KnowledgeService.hybrid_search`: reciprocal-rank fusion over lexical/chunk/semantic. Exposed as MCP `knowledge_search`. No authority, temporal, premise, conflict or budget logic. |
| Procedures | `ProcedureService.find_matches`: `status='active'` procedure + preferred version, FTS/ILIKE, project-first ordering, `task_family` filter. No company-approval gate; "same/again" fallback returns arbitrary active procedures. MCP `procedure_match`. |
| Decisions | `task_decisions` are per-task (`active/superseded/retired`, provenance `source_kind`). No project-wide decision search exists; only `TaskDecisionService.list_active(task_key)`. |
| Episodes | `experience_episodes` (E1): immutable, project-scoped, `trust_class`, `participation_class`, `outcome_status`, bounded `payload`, `payload_digest`. **No retrieval API** other than `get(episode_key)`. Payload `applicability` carries only `task_family` and `project_id`; there are no environment/premise fields. |
| E2 lessons | `knowledge_items` with `knowledge_type='lesson'`, `status='proposed'`, `source_owner='experience:176.e2.v1'`, `scope.origin='experience_consolidation'`, `metadata.{polarity,subject_key,statement_digest,experience_transition_key}`, `derived_from` episode relations, `related_to` conflict relations. |
| Relations | `relations` + `relation_evidence`; `relations.impact` = bounded typed traversal, fails loud on budget overflow. |
| Raw evidence | `sources`, `source_locations`, `knowledge_chunks`; #164 sanitizes before persistence. |
| Company authority | New `project_id IS NULL` rows in `knowledge_items/procedures/sources/capabilities` carry `scope_approval_event_id`; pre-migration-010 seed rows are grandfathered and cannot be distinguished by schema alone. |
| Chairman injection | Hooks inject only continuity/resume state. There is **no** automatic experience retrieval today. |
| Ranking/budgets | Only RRF in `hybrid_search` and per-call `limit` clamps (≤50, procedures ≤20). No token/byte budget. |
| Persisted retrieval observations | None. |

### Missing-primitive analysis

1. A single **eligibility gate** applying scope + company-authority + status + temporal rules uniformly. Existing search paths each apply a different, weaker subset. **Missing → new pure code.**
2. **Episode retrieval.** **Missing → new read query.**
3. **Project decision retrieval** across tasks. **Missing → new read query** over existing `task_decisions` ⋈ `tasks`.
4. Premise / conflict / stale evaluation and the pack composer/budget. **Missing → new pure code.**
5. Vector store: **not needed.** `knowledge_chunks` embeddings already exist and stay optional.
6. Schema: **none proven missing.** No migration in E3. If implementation proves one is needed it must be justified in this file before being written.

## Inputs (data, never authority)

```
project_id        int, required, must exist. None is rejected (fail closed; never "all projects").
query             str, required, bounded
task_key          optional; if given must belong to project_id
task_family       optional str
capability_keys   optional list[str], bounded
temporal_intent   "current" (default) | "historical"
as_of             optional timestamp; only with "historical"; default = now
premises          optional dict[str, str], bounded: caller-asserted current environment
                  (e.g. platform, runtime, db_provider, project_lifecycle). E3 does not sniff the environment.
raw_fallback      bool, default true
```

Unknown keys, wrong types, oversize values, hidden-reasoning keys, or residual credential-like content (#164 detector) raise before any read. The query is treated as data.

## Required staged flow

1. **Resolve context.** Load project, optional task (must be in project), task family; normalize temporal intent.
2. **Hard filters before ranking** (single gate, below). Ineligible rows are never scored or shown.
3. **Decisions/rules.** Active decisions of the current task (exact, authoritative for that task); `knowledge_type in {decision,rule}` items that pass the gate; active decisions of other tasks in the same project that lexically match, labelled `task_scoped_prior`. Under `historical` intent, superseded/retired decisions are additionally eligible and labelled.
4. **Accepted procedures.** `procedures.status='active'` with a preferred accepted version, passing scope gate. Precedence over lessons and episodes in ordering. Under `historical` intent, superseded versions are not surfaced by E3 (E5 owns procedure history).
5. **Semantic lessons/gotchas/premise warnings.** Knowledge of types `lesson/fact/finding/observation/hypothesis`, ranked by lexical (+ optional embedding) fusion.
6. **Precedent episodes.** At most a small bounded number; success/failure classification preserved.
7. **Conflicts, staleness, premise mismatch** evaluated over the surviving candidate set; represented explicitly.
8. **Raw-evidence fallback** only when structural coverage is insufficient (below).
9. **Compose one pack** within budget, with per-item metadata and evidence keys.

## Eligibility gate (hard, before ranking)

An item is eligible only if **all** apply:

- **Project scope.** `item.project_id == request.project_id`, or `item.project_id IS NULL` **and** it carries a non-null `scope_approval_event_id`. Unapproved `NULL`-project rows (including grandfathered seed rows) are excluded and counted in `diagnostics.excluded_unapproved_company`. (Recorded decision: fail closed; grandfathered rows cannot be proven company-approved from schema. Revisit only with evidence.) Another project's rows are invisible and never counted.
- **Episodes** are project-local only; `project_id IS NULL` episodes are never eligible.
- **Status/temporal.**
  - `current`: exclude `rejected`, `superseded`, `retired`; exclude `valid_to <= now`; exclude `valid_from > now`. `challenged` items are not instructions: they go to the conflicts section.
  - `historical`: `superseded`/expired/retired items are eligible **only** with `as_of` validity satisfied (`valid_from <= as_of` and `valid_to` null or `> as_of`) and are labelled `historical`; `rejected` remains excluded always.
- **Integrity.** Episode `payload_digest` must recompute (E2 `episode_payload_digest`); payload must be a JSON object; enums must be known. Failing rows are dropped and counted in `diagnostics.rejected_corrupt`; they are never emitted.
- **Security.** Any emitted text is redacted; instruction/authority-shaped text from a non-user-authoritative, non-validated source (E2 `_INJECTION` heuristic) is not emitted as an instruction and is counted in `diagnostics.quarantined_injection`.

## Authority / status: what E3 may surface, and as what

Every item has a **role**: `instruction`, `candidate`, `warning_example`, `low_trust_observation`, `conflict`, `stale_assumption`, `evidence_ref`. Only `instruction` items are phrased as guidance, and only items meeting *all* of the following may be `instruction`: eligible, `authority_class in {user_authoritative_decision, accepted_procedure, validated_or_canonical_knowledge}`, not stale, no premise mismatch, not challenged, no unresolved conflict.

| Store | Surfaces as |
|---|---|
| Current-task active decision | `instruction`, authority `decision_current_task` |
| Other-task active decision, same project | `candidate`, label `task_scoped_prior`; never an `instruction` (task decisions are not project rules) |
| `decision/rule` knowledge `validated`/`canonical` | `instruction` |
| Accepted active procedure | `instruction`, authority `accepted_procedure`; ordered ahead of lessons |
| Knowledge `validated`/`canonical` lesson/fact/finding | `instruction` if all conditions hold; else the demoted role |
| Knowledge `proposed`/`observed` (**includes all E2 lessons**) | `candidate` only: labelled low-authority, `authority=proposed`, project-local, in a separate `candidate_lessons` section, hard-capped. They never appear in `instruction` sections and never outrank validated/accepted items. `negative` polarity ones present as gotchas. (Decision: include, clearly labelled, because a project gotcha is high-value and the label prevents authority inflation; recorded as reversible by the caller passing `include_candidates=false`, default true.) |
| Knowledge `challenged` | `conflict` (with reason `challenged`) |
| Knowledge with `trust_class=external_untrusted_observation` (metadata) or episode `observed`/untrusted | `low_trust_observation` with provenance; never `instruction`, never promoted |
| Episodes | `evidence_ref`/example only, with `outcome_status`, `failure_classification`, trust. A `failed`/`cancelled` episode is emitted as a **failure/gotcha example**, never as a recipe; its text is never phrased as a procedure. |
| Raw fallback chunks | `evidence_ref` only, `trust=unspecified_raw`, no authority |

Relevance and rank are **not** truth or authority. No emitted field may be named or documented as probability/confidence-of-truth; the stored `confidence` of a knowledge item is passed through labelled `stored_confidence` (author-asserted, not verified).

## Temporal / conflict model

- Current-vs-historical is an explicit request field, not inferred from text.
- `last_verified_at`, `review_after` are surfaced. `review_after <= now` marks the item `stale`; stale items are demoted to `stale_assumption` (still evidence, not silently current).
- **Conflicts** are surfaced, never resolved or averaged. Sources of a conflict flag:
  1. two surviving knowledge items with the same `metadata.subject_key` and opposite `metadata.polarity` (E2 semantics);
  2. `related_to` relations between two surviving knowledge items whose provenance marks an experience-consolidation conflict;
  3. `status='challenged'`;
  4. a surviving item that has a `supersedes`/`superseded_by` relation to another surviving item (current intent: the successor is preferred and the edge noted; the superseded item stays suppressed).
- A conflict entry lists both/all member keys, the reason, and each member's authority. Neither member is promoted or dropped by E3.
- Newer is not truer: recency is a late tie-break only.

## Premise awareness

- Item premises are read from `knowledge_items.scope.premises` / `metadata.premises` (dict of string → string or list of strings). Procedures: `input_contract.premises` if present. Episodes carry none today.
- Only keys present in **both** item and request are compared, case/whitespace-normalized. Any differing key ⇒ `premise_status=mismatch`: the item is demoted to `warning_example` with the mismatching keys listed. Item premises unstated or request premises unstated ⇒ `premise_status=unverified` (surfaced in its normal role but flagged; never silently "matched").
- Project identity is enforced by the scope gate, not premises. Task-family/capability match is a ranking signal and a labelled applicability field, not a mismatch trigger.
- E3 does not add premise fields to episodes (E1 immutable). It does not infer premises from prose.

## Ranking (inspectable, deterministic)

No opaque score. Within each section items are ordered by this tuple (documented components are all emitted per item as `signals`):

1. authority tier (fixed enumerated order: current-task decision, accepted procedure, validated/canonical, candidate, low-trust);
2. scope specificity (project-local before approved-company);
3. task-family / capability match (exact flag);
4. reciprocal-rank fusion of lexical and (if available) embedding ranks, as in `hybrid_search`, reported as `fusion_rank_score`, rounded to 6 dp;
5. recency (`last_verified_at`, else `updated_at`) as late tie-break;
6. stable key ascending (deterministic final tie-break).

Ties are therefore fully determined. Embedding results are re-resolved through the E3 eligibility gate by `knowledge_id`/`source_id`; E3 never trusts the filters inside `semantic_search`. If embeddings are unavailable, retrieval degrades to lexical with `diagnostics.embedding="unavailable"`; if the result reports `possibly_truncated`, `diagnostics.embedding_truncated=true` is emitted.

**Diversity/duplicates.** Deduplicate by normalized-text digest across sections (highest authority kept, others recorded as `also_matched`), collapse multiple episodes from one task to one, and suppress episodes already cited via `derived_from` by a surfaced lesson unless they are the failure precedent. No fuzzy-similarity threshold is invented.

## Experience pack and budget

Pack (schema-versioned `176.e3.v1`), sections in fixed order:

`current_decisions`, `accepted_procedures`, `validated_lessons`, `candidate_lessons`, `conflicts_and_stale`, `precedent_episodes`, `low_trust_observations`, `raw_evidence_refs`, plus `abstained`, `diagnostics`, `evidence_keys`, `policy`.

Every item: `memory_key` (knowledge/procedure/decision/episode/chunk key), `memory_class` (`decision`, `procedural`, `semantic`, `episodic`, `raw_evidence`), `project_id`/`scope` (`project` | `company_approved`), `authority_class`, `status`, `trust_class` (or `unspecified`), `role`, `applicability` (task family/capabilities/premises + premise_status), `why_retrieved` (structured list of signal names, not free prose), `evidence` (source/episode/relation keys), `flags` (`stale`, `conflict`, `challenged`, `historical`, `premise_mismatch`, `premise_unverified`), `signals`, and bounded `text`.

Safety bounds (structural caps, **not** quality thresholds): per-section item caps (decisions 8, procedures 3, validated lessons 6, candidates 3, conflicts 5, episodes 3, low-trust 3, raw refs 5); per-item text ≤ 600 chars; pack canonical-JSON size ≤ 16 KiB with an estimated-token field (`bytes/4`). Over budget: drop lowest-priority items in reverse section priority, then reverse rank, and record `diagnostics.truncated` counts; never split or cut mid-item. These caps are policy-versioned and may only change by a new policy version.

**Abstention.** If no eligible item survives in any section and raw fallback returns nothing, return `abstained=true` with `reason="no_eligible_experience"` and empty sections. Diagnostics never reveal other projects' existence or counts.

## Bounded raw-evidence fallback

Trigger (structural, not a score): zero items in `current_decisions ∪ accepted_procedures ∪ validated_lessons`. May also be disabled by `raw_fallback=false`. Behaviour:

- lexical `knowledge_chunks` search only, through the **same eligibility gate** (active source, project or approved-company scope, chunk's knowledge not rejected/superseded/challenged);
- returns ≤5 references: `chunk_key`, `source_key`, `section`, ≤300-char redacted snippet, role `evidence_ref`, trust `unspecified_raw`;
- never dumps the archive, never creates knowledge, never persists hits, never bypasses #164 (persisted chunks are already sanitized; output is redacted again);
- `possibly_truncated` and any fallback error are reported, not hidden.

## Hard invariants (each has a test)

1. No second memory store; no schema change; no persisted retrieval observation.
2. Retrieval is **read-only**: it runs under a read-only database transaction and must leave every experience/knowledge/relation/transition/task table byte-identical.
3. No promotion, supersession, reconsolidation, prompt/policy/routing/model mutation.
4. No hidden chain-of-thought: episode output is a **whitelist** of fields (objective, outcome, failure classification, constraints, applicability, validation status, source/decision/procedure/capability keys); any other payload key is never emitted even if present in a row.
5. External/untrusted observations are data with provenance, never `instruction`.
6. Project-only experience never crosses projects; company items obey the approval gate.
7. Relevance ≠ truth; newer ≠ truer; conflicts surface, are not averaged.
8. Premise mismatch demotes to `warning_example`.
9. Current execution state (checkpoint/next_action) is never read into, replaced by, or merged into the pack.
10. Malformed/corrupt inputs and rows fail closed (raise for the request; drop-and-count for rows).

## Test contract (frozen before implementation)

Pure unit tests (`tests/test_experience_retrieval.py`) and PostgreSQL integration (`tests/integration/test_experience_retrieval_journey.py`). Letters map to the E3 required matrix:

- **A project isolation**; **R no cross-project leakage** (episode/knowledge/procedure/decision/raw chunk each in a second project, and `project_id=None` rejected).
- **B company/global**: approved `NULL`-project item surfaces labelled `company_approved`; unapproved `NULL` row excluded and counted.
- **C current vs historical**; **D superseded/expired suppression** (current) and label (historical, `as_of`).
- **E contradictory memories** surfaced as a conflict entry with both members retained (polarity + challenged + relation cases).
- **F premise mismatch** demotes to `warning_example`; unverified flagged; matching stays `instruction`.
- **G trusted vs untrusted** ordering and role; injection-shaped text not emitted as instruction.
- **H proposed E2 lesson**: appears only in `candidate_lessons`, never `instruction`, never outranks validated; `include_candidates=false` removes it.
- **I failure episode** emitted as failure/gotcha example, never phrased as recipe; cancelled likewise.
- **J accepted procedure precedence** over lessons/episodes in ordering.
- **K exact/lexical** retrieval including exact-key/title hits.
- **L optional embedding**: stubbed embedding results add fusion signal; unavailable degrades with diagnostic; embedding results for ineligible/other-project chunks are dropped by the gate; truncation flag propagated.
- **M deterministic tie-break**: identical inputs ⇒ identical pack (byte-equal canonical JSON) across repeated and shuffled-insertion runs.
- **N duplicate suppression/diversity**.
- **O pack size/token budget** and truncation accounting; no mid-item cuts.
- **P abstention** on no eligible experience; diagnostics leak nothing cross-project.
- **Q bounded raw fallback**: triggered only when structure is empty; ≤5 refs; gated; not persisted; disabled by flag.
- **S no retrieval-time writes**: row-count/digest snapshot of `knowledge_items, relations, relation_evidence, experience_episodes, experience_transitions, task_decisions, procedures, embedding_jobs` unchanged; a write attempt inside the retrieval transaction fails read-only.
- **T no hidden CoT**: row seeded (via privileged SQL) with `chain_of_thought`/reasoning payload keys — never emitted.
- **U secret/injection negatives**: secret-shaped query rejected; secret-shaped stored text redacted; instruction-shaped external text quarantined.
- **V malformed/corrupt fail closed**: bad request shapes raise; tampered episode digest, non-object payload, unknown trust enum are dropped-and-counted, never emitted.
- Additional: execution-state isolation (invariant 9), policy version/digest pinning, and that `KnowledgeService`, `ProcedureService`, `EmbeddingService`, `relations` behaviour is unchanged (existing suites stay green).

No universal numeric quality thresholds are asserted; those belong to E7 calibration.

## Proposed implementation chunks

1. **Pure core** `src/vres_os/experience_retrieval.py`: request normalizer, policy/digest, eligibility gate (pure predicates over row dicts), role/authority classification, premise + conflict + stale evaluation, deterministic ranking, dedupe, pack composer/budget, abstention. Unit tests A–V pure parts. No DB.
2. **Read-only PostgreSQL retrievers** in the same module or a sibling: read-only transaction, per-store queries (decisions, procedures, knowledge lexical, episodes with digest verification, relation lookups), embedding integration through the gate. Integration tests for scope/temporal/status/isolation/no-write.
3. **Conflict/premise/relation integration + fallback**: relation-based conflict, raw chunk fallback, evidence keys. Integration tests E, F, Q.
4. **Determinism, budget, security negatives, corrupt-row and CoT tests** (M, N, O, T, U, V).
5. **Read-only MCP tool** `experience_retrieve` bound to the session project (no Chairman/hook injection), docs (`KNOWN-LIMITATIONS`, handoff), targeted + full suite, installed-runtime smoke (MCP surface changes), release gate. Then exact-head CI, protected Fable/high validation (governance/security surface), guarded merge.

E4 does not begin until E3 is implemented, tested, evidenced, protected-reviewed, merged and post-merge green.
