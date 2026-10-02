# Experience Intelligence E4 Contract — Temporal Lifecycle and Revocation

Date: 2026-09-30
Issue: #176
Base: `ddb0719d130fd45b12b6bdc9e1682378ace7ae64` (E1–E3 merged; E3 CI #466 green)
Branch: `issue-176-e4-temporal-lifecycle-revocation`
Frozen plan: commit `34f45afa0fb8d5a6a90bef53dec58d9ecef1093d`, file `docs/architecture/EXPERIENCE-INTELLIGENCE-PLAN-2026-09-27.md` (tranche E4). The plan is not duplicated here.
Policy version: `176.e4.v1` (E1/E2/E3 policy constants are not edited).

## Scope

E4 makes memory **temporal and revocable**: what may influence *current* work, what remains *historically* visible, and what must stop influencing anything when its evidence is revoked.

Invariant from the plan: **forget/retire controls USE, not history.** Nothing E4 does deletes provenance, ledger rows, episodes, sources, or evidence rows.

Out of scope (hard): E5 capability/procedure experience integration, E6 retrieval observations/utility, E7 benchmark, E8 automatic Chairman retrieval/injection, #169 live acceptance, company-scope lifecycle, physical byte erasure of sources.

## Verified discovery (tree at base)

| Fact | Evidence |
|---|---|
| `knowledge_items.status` CHECK has 7 values, no retired/revoked | migration 001:100-110 |
| `valid_from/valid_to/last_verified_at/review_after` exist; `valid_*` never written; nothing consumes `review_after` | audit + `knowledge.py` |
| `supersede()` has no lock, no idempotency, no reason, no `valid_to` | `knowledge.py` |
| `sources.status` is free text; only `'active'` is ever written; no revoke writer | grep: only writer is the `scope_approval_event_id` UPDATE (`sources.py:113`) |
| Readers filtering `status='active'`: `knowledge.py:335`, `embeddings.py:235,256`, `experience_retrieval.py:1166`, `sources.py:104` | grep |
| `embeddings.queue_missing` selects every chunk with no source/knowledge status filter | `embeddings.py:88-105` |
| `knowledge_evidence` is the only knowledge→source link; `source_id` is SET NULL on delete; no uniqueness | migration 001:132-143 |
| `relations` has no FKs; type/kind allow-lists are Python-only | migration 001:145-158, `relations.py` |
| `experience_episodes` immutable by trigger (GUC bypass only for ledger delete) | migration 037 |
| No durable record of what a session consumed; hooks inject only task state | audit; E3 is read-only; E6 forbidden |
| Pre-tool enforcement pattern exists (`sessions.metadata.vres_read_only_hold` + `control_preflight`) and its key is trigger-protected (029) | `control_preflight.py`, migration 029 |
| Latest migration is 038 | `migrations/` |

## Migration decision: ONE additive migration (039) — required

"No migration" is **rejected**, because three invariants have no existing owner:

1. **Append-only lifecycle audit.** Episodes are immutable and task-bound; `task_events` is task-bound; `relation_evidence` is relation-bound. Nothing can durably record "X was revoked because Y, under approval Z" for a project-scoped target with its own idempotency key.
2. **State vocabulary.** The knowledge status CHECK cannot express `retired`/`revoked`. Overloading `rejected`/`challenged` would conflate use-forgetting/revocation with human rejection/open conflict and would silently re-enter readers that treat `challenged` as visible-in-conflicts.
3. **Episodes cannot be mutated** (immutable trigger), so their use-state must be derived from an append-only ledger.

Migration 039 contains exactly:
- `vres.experience_lifecycle_events` (append-only; UPDATE/DELETE blocked by trigger, no bypass GUC).
- Extension of the knowledge status CHECK with `retired` and `revoked` (drop/re-add constraint; no data rewrite).
- Grants/boundary entries needed so the provenance-writer split-role boundary (migration 023) keeps working.

Not migrated (deliberately): `sources.status` (already free text; `'revoked'` needs no DDL); the session metadata trigger (contamination is **derived from the ledger**, so no new protected metadata key is introduced); `embedding_jobs` (existing `skipped` state + `error` text suffices); `relations` allow-lists (Python only).

### `experience_lifecycle_events` (append-only)
`id`, `event_key` (unique), `idempotency_key` (unique), `project_id` (NOT NULL, FK), `policy_version`, `action`, `target_kind`, `target_key`, `prior_state`, `new_state`, `cause_kind`, `cause_key`, `approval_event_id`, `task_id` (nullable), `session_key` (nullable), `reason` (≤500 chars, sanitized), `detail` jsonb (bounded ≤8 KiB; keys/digests/counts only), `created_at` (server clock).
Actions: `retire`, `reinstate`, `supersede`, `challenge`, `refresh`, `expire_observed`, `revoke_source`, `invalidate_derived`, `restore_derived`, `context_contaminated`, `context_refreshed`.
Rows never hold statement text, source content, secrets, or model reasoning.

## Lifecycle states and semantics

Owner of current state: `knowledge_items.status` for knowledge; `sources.status` for sources; the **ledger** for episodes (derived: an episode is revoked iff its latest `revoke`/`restore` event says so). The ledger is the audit for all three; it is authoritative only for episodes. Status writes and ledger append occur in one transaction.

| State | Meaning | Current retrieval | Historical retrieval | Reversible |
|---|---|---|---|---|
| active (`proposed/observed/validated/canonical`) | in force | yes (existing trust rules) | yes | — |
| `challenged` | open dispute, not resolved | only in `conflicts_and_stale` (existing E3) | yes | by explicit resolve |
| `superseded` | replaced by a named successor; `valid_to` set | no | yes, flagged `superseded`, directed to successor | no (new supersede edge instead) |
| `retired` | use-forgetting; owner chose to stop using | no | yes, statement visible, flagged `retired` | yes (`reinstate`, needs approval) |
| expired (`valid_to` past) | validity window ended | no | yes | via `refresh`/new window |
| stale (`review_after` past) | needs re-verification | yes, flagged `stale_assumption` (E3 behavior kept) | yes | `refresh` |
| `revoked` | evidence gone/untrusted; support insufficient | **never** | **tombstone only** (key, state, time, reason class; no statement/payload) | only via `restore_derived` after source restoration, with approval |

Distinctions: **challenge** never auto-resolves a conflict and never suppresses. **Supersession** is directed and never proves the successor truer; newer ≠ truer, so supersession requires an explicit successor key and approval, never inferred from timestamps. **Retirement** is a use decision by an authorised owner and is not a claim of falsity. **Expiry** is time-derived and non-destructive. **Revocation** is evidence-driven and is the only state that hides content from historical queries, because the content may be poisoned or unauthorised.

## Provenance traversal and multi-source rule

Support graph edges: `knowledge_evidence(source_id)`; `derived_from` relations from knowledge→{knowledge, episode, source}; from episode→{task, decision, validation, artifact, source}; artifact→source through the artifact's source link. Traversal is bounded: depth ≤ 4, nodes ≤ 500 per operation. Budget overflow **fails the whole operation closed with rollback**; nothing is partially invalidated.

Grounded-support rule (mechanical, cycle-safe): a node is *supported* iff a path exists to at least one `active` source root through nodes that are not `revoked`/`retired`/`superseded`-for-support purposes. A visited set breaks cycles; a cycle never supports itself. Support is counted as **distinct active `source_id` roots** (independence = distinct source rows). Minimum surviving support = **1**. So:
- one of several independent sources revoked ⇒ item **stays current**, a `refresh_recommended` detail is recorded; not invalidated;
- last surviving root revoked ⇒ item becomes `revoked` (`invalidate_derived`), transitively;
- nodes that never had any evidence (no provenance at all) are **not** touched by revocation (they were never derived from sources) — unrelated memory is not invalidated;
- evidence with `source_id NULL`, dangling relation endpoint, or unknown kind is *not counted as support* and is recorded in `detail.corrupt_provenance` counts. Corrupt provenance never grants support and never aborts revocation of the healthy part.

E2 lessons: support = non-revoked episodes via `derived_from`, each episode grounded per above. A lesson whose supporting episodes are all revoked/ungrounded becomes `revoked`. E2 has no minimum support count and E4 does not add one.

Cross-scope: E4 mutates **only rows of the acting project**. A `project_id IS NULL` (company) item with support in a revoked project source is **not mutated**; it is listed in the result as `unresolved_cross_scope` and E3 must treat that support as absent when it computes grounding for display flags. Company lifecycle authority is deferred (company publication flow is held).

## Operations, authority, transactions

All mutating operations: project scope only (`_require_node(write=True)`), require an `approval_event_id` bound to the exact `(action, target_key)` (approval type `e4_lifecycle`; latest USER_INSTRUCTION must be an unconditional acceptance, as for existing approvals), and never derive approval from a decision record or from a source's own content (untrusted source can never gain authority through revocation or reconsolidation; revoke can only *reduce* trust).

| Operation | Effect |
|---|---|
| `retire` / `reinstate` knowledge | status ⇄ `retired`, prior status recorded in ledger; reinstate restores recorded prior status |
| `supersede` (existing service, hardened) | `FOR UPDATE` both rows, explicit reason, sets `valid_to`, writes ledger + `superseded_by`, idempotent on repeat |
| `challenge` (existing update path, hardened) | reason required, ledger append; no state cascade |
| `refresh` | sets `last_verified_at`, new `review_after`, ledger append; never changes status |
| `revoke_source` | `sources.status='revoked'`, traversal, cascade to derived memory (below), embedding invalidation, contamination marking |
| `restore_source` is **not** provided in E4 | recovery is a new source + `reinstate`/`restore_derived` with approval |

Transaction boundary: one Postgres transaction per operation containing status writes, ledger appends, embedding clears and contamination events. `pg_advisory_xact_lock(project_id)` serialises lifecycle operations per project; target rows taken `FOR UPDATE` in ascending id order. Concurrent revoke/refresh on the same project therefore serialise deterministically; a refresh that loses to a revoke sees the revoked state and no-ops with `already_revoked`.

Idempotency: `idempotency_key = sha256(policy | action | target_kind | target_key | cause_key)`. Replaying a completed operation returns the original result with `replayed=true` and appends nothing. A retry after failure is safe because a failure rolled everything back.

Fail-closed: any exception, budget overflow, missing approval, cross-project target, or unreadable provenance aborts with no state change.

## Embeddings, chunks, raw evidence

- Revoked source ⇒ its `knowledge_chunks`: embedding columns set NULL, pending/running `embedding_jobs` set `skipped` with `error='source_revoked'`; chunk rows and source rows are **retained** for audit but are unreachable: every raw/semantic/chunk reader already joins `sources.status='active'` (verified list above) and E4 adds the same guard where absent.
- Revoked derived knowledge ⇒ chunks with that `knowledge_id`: embeddings cleared, jobs skipped, excluded by status in `chunk_search`/`semantic_search`/E3.
- `queue_missing` gains a guard: never queue chunks whose source is not `active` or whose knowledge status is `retired`/`revoked`/`superseded`.
- Rebuild is the existing `embeddings_process_pending`; after `reinstate`/`restore_derived` the affected chunks are re-queued. Rebuild is idempotent (existing `UNIQUE(chunk_id, model)`).
- Physical erasure of source bytes is **not** E4 (would conflict with "provenance stays auditable"); documented as a known limitation.

## E3 retrieval integration (schema bumps to `176.e4.v1`)

- Current intent: exclude `retired`, `revoked`, `superseded`, expired; flag `stale`; never return revoked/retired episodes or lessons; a lesson or episode grounded only in revoked sources is excluded.
- Historical intent: include `superseded`/`retired`/expired with `not_current` flags and successor pointer, **not** re-authorising them as premises; `revoked` appears only as tombstone.
- Episodes gain the revocation gate (ledger-derived) and source-status check that E3 lacked; `decision_item`, `_raw`, `_knowledge`, `_episodes` SQL gain the same conditions.
- FLAGS closed set gains: `retired`, `revoked`, `expired`, `not_current`, `cross_scope_unresolved`. Diagnostics gain exclusion counters.
- Retrieval remains read-only. No observation writes (E6 remains forbidden).

## Contaminated-session contract

There is no record of what a session consumed, and E4 will not create one (E6). Contract is therefore **conservative and honest**:

1. On `revoke_source`/`invalidate_derived`, every **open session** (`ended_at IS NULL`) of the project, including the acting session, gets a `context_contaminated` ledger event (`session_key`, revoked keys). Detection is "may have loaded", per the plan's wording.
2. Contamination is **derived**: session S is contaminated iff it has a `context_contaminated` event with no later `context_refreshed` event. No mutable marker, no protected-metadata trigger change.
3. Enforcement: `control_preflight` adds a check, following the `read_only_hold` pattern: while contaminated, only the safe tools plus `context_refresh_ack` are allowed; other tools are denied with the revoked keys named. Stop-guard reports the condition. Failure semantics mirror the existing hold check and are pinned by a test.
4. Refresh: the Chairman re-derives context from Vres state (`task_resume` output carries a `contamination_notice`) excluding revoked keys, then calls `context_refresh_ack`, which appends `context_refreshed` (digest of the exclusion list). A **new** session (after `clear`) has no contaminated event and starts clean; `resume_context` still lists revoked keys as "do not use".
5. Limits (documented, not hidden): task_state/checkpoint prose and transcript text are not scanned; the ack is a Chairman attestation, not proof of absence; a refresh does not retroactively cleanse artifacts already written.

## MCP surfaces (project scope only)

New tools (registered count 48 → 51):
- `source_revoke` (mutating, approval-bound)
- `knowledge_lifecycle` (`action`: retire|reinstate|refresh; mutating, approval-bound except `refresh` by an authorised project owner with approval)
- `context_refresh_ack` (mutating ledger append; allowed while contaminated)

Existing `knowledge_supersede` is hardened (not renamed). `experience_retrieve` keeps its contract with the new schema. New tools are added to the hooks matcher; only `context_refresh_ack` joins `_SAFE_VRES_TOOLS`.

## Security / injection / secrets

- `reason` and all free text pass the existing sensitive-text sanitizer and length bounds before persistence; rejection on secret patterns, no partial write.
- Ledger `detail` holds keys, digests and counts only; never statement or source content; never chain-of-thought.
- Tool results and source text are untrusted data; they cannot supply `approval_event_id`, action, or target.
- Poisoned sources: revocation removes influence; nothing in E4 raises the trust class of anything.

## Evidence / audit

Every state change ⇒ one ledger row (plus per-cascade rows sharing `cause_key`). `orchestration/task` evidence links by `task_id`. Result payloads report counts: `revoked`, `retained_with_support`, `unresolved_cross_scope`, `corrupt_provenance`, `chunks_cleared`, `sessions_marked`, `replayed`.

## Rollback / recovery

Operation-level: transactional. Product-level: `reinstate` (retired), `restore_derived` (revoked, only after a new active source grounds it, with approval), re-queue embeddings. Migration 039 is additive; its rollback is a new forward migration (released migrations are immutable).

## Implementation chunks (dependency order)

- **A** migration 039 + ledger + append-only trigger + status vocabulary + status-reader exclusions (`KnowledgeService.search`, chunk/semantic readers). Tests: migration contract, append-only, CHECK, reader exclusion.
- **B** lifecycle primitives: retire/reinstate/refresh, hardened supersede/challenge, idempotency, advisory lock, authority.
- **C** provenance traversal + `source_revoke` cascade (multi-source, cycles, corrupt provenance, lessons, cross-scope, budget overflow rollback).
- **D** embedding/chunk invalidation + `queue_missing` guard + rebuild.
- **E** E3 retrieval integration (`176.e4.v1`): current vs historical, tombstones, episode gate, flags.
- **F** contamination detection, preflight enforcement, refresh ack, resume notice.
- **G** MCP tools, hooks matcher, safe-list, tool-count test, end-to-end hardening, docs/limitations/handoff.

Each chunk: tests first where practical, targeted unit + PostgreSQL integration tests on a fresh disposable `_test` DB, critical Ruff, diff inspection for E5+ leakage, commit only when green, checkpoint before the next chunk.

## Deferrals

E5 (capability/procedure experience, procedure lifecycle retire path), E6 (consumption records, utility), E7 (benchmarks), E8 (automatic retrieval/injection), company-scope lifecycle, byte-level erasure, and #169 live acceptance are explicitly not in E4.

## Acceptance

Mandatory tests are the E4 list in the program instruction (suppression, historical visibility, challenge non-resolution, newer≠truer, use-forgetting without history loss, review_after, revocation, transitive and multi-source, unrelated untouched, embeddings, idempotency, partial failure, rollback, concurrency, project isolation, company non-leak, untrusted-source authority, secrets, corrupt provenance, cycles, contamination detection/enforcement/refresh, no chain-of-thought, no E6 writes). Final sequence: manifest + worktree hash, full suite with PostgreSQL, critical lint, release gate, installed-runtime check (MCP tools change), docs closure, exact-head PR CI, protected Fable/high validation, guarded merge, exact post-merge CI.
