# E7 Chunk 0 findings (2026-10-06)

Scope: owner discovery (0A), placement (0B), temporal admissibility (0H). Read-only on owners; no owner file was modified.

## 0A. Owner signatures and legal public EvidencePack `content`

| Surface | Signature | Public fields usable as B2 `content` | Excluded (non-public / non-semantic) |
|---|---|---|---|
| E3/E5 retrieval | `ExperienceRetrievalService.retrieve(request: dict \| RetrievalRequest) -> dict`; `RetrievalRequest(project_id, query, task_key, task_family, capability_keys, temporal_intent="current", as_of, premises, include_candidates=True, raw_fallback=True)` | item text (already sanitized, re-redacted, <=300 chars, instruction-shaped text quarantined) | DB ids, paths, URIs |
| Knowledge | `KnowledgeService.search(query, limit=8, project_id=None)` | `title`, `statement` | `rank`, `confidence`, timestamps, scope |
| Chunks | `KnowledgeService.chunk_search(query, limit=8, project_id=None)` | `section`, `content` | `source_id`, `knowledge_id`, `path_or_uri`, `rank` |
| Procedures | `ProcedureService.find_matches(query, task_family=None, limit=5, project_id=None)` | `name`, `description`, `method`, `invariants` | `updated_at`, `score`, `accepted_*` |
| E1 | `ExperienceEpisodeService.capture(task_key, *, work_unit_key=None)` | n/a (write path) | `EXP-<date>-<uuid>` key is random |
| E2 | `ExperienceConsolidationService.consolidate(candidate: dict)`; closed candidate keys `project_id, polarity, trigger, subject_key, evidence[{episode_key, pointer, quote}]` | n/a (write path) | |
| E4 | `ExperienceLifecycleService(clock=None)`: `retire/reinstate/challenge(key, *, project_id, approval_key, reason, task_key=None)`, `supersede(old, new, ...)`, `refresh(key, ..., review_after)` | n/a | |
| E4 | `SourceRevocationService(clock=None).revoke_source(source_key, *, project_id, approval_key, reason, task_key=None)` | n/a | |

Sanitizer findings:
- Retrieval: sanitization guaranteed by the owner (`sanitize_extracted_text`, review-required text excluded, 300-char cap).
- `knowledge.propose` and `sources` redact on **write** (`redact_text`), but `knowledge.search` / `chunk_search` do not re-sanitize on **read**. **Finding:** the benchmark must not trust these surfaces' read output as sanitized. `build_evidence_item` therefore applies the sanitizer itself and fails closed on secret-shaped text before truncation. No runtime change is needed for bounded content, because the 300-char cap and truncation are applied by the benchmark.
- Chunk and knowledge results carry DB ids/paths; only the fields in the table may enter a pack. Case-local aliases replace all runtime keys.

## 0B. Placement decision

`src/vres_os/experience_benchmark.py`, a flat module (no package).
- Matches the existing flat `experience_*.py` convention; no new hierarchy for one module.
- Depends downward only on `sensitive_policy.sanitize_extracted_text`.
- No SQL, no CLI/MCP, no state. Tests assert no `src/vres_os` module imports it and that it contains no CLI/MCP/SQL.
- Benchmark data will live outside the package in `benchmarks/experience_e7/` (not created in Chunk 0).
- Caveat: the module ships in the installed package. It is inert (no entry point).

## 0H. Temporal admissibility (A1.7)

Classes: (a) deterministic via an existing public time/as-of parameter; (b) testable by operation ordering only; (c) inadmissible.

| Planned temporal operation | Class | Basis |
|---|---|---|
| Historical retrieval (`temporal_intent="historical"`, `as_of`) | a | public parameter on `RetrievalRequest` |
| Lifecycle retire/reinstate/challenge/supersede (E4) | a | injectable `clock` |
| `refresh(review_after=...)` | a | explicit tz-aware `review_after`, compared to the injected clock |
| Source revocation (E4) | a | injectable `clock` |
| E1 capture then E2 consolidate sequencing | b | no time input; `datetime.now` / `uuid4` internal. Order only |
| Knowledge `propose`/`update` then retrieve | b | ordering only |
| Any assertion on `last_verified_at`, `updated_at`, `valid_from`, source registration time | c | DB `now()`, no public input |
| Procedure `updated_at` / `score` | c | non-semantic; excluded |

Owner/API gaps (recorded, not fixed; no owner change in Chunk 0):
1. E1 capture and E2 consolidate have no injectable clock; episode keys are random.
2. Knowledge `last_verified_at`/`updated_at`/`valid_from` are DB `now()`; no as-of write input.
3. `knowledge.search` / `chunk_search` have no read-side sanitizer guarantee.

Consequence for the corpus: timeline steps may only use class (a) and (b) operations; assertions must not depend on class (c) values.
