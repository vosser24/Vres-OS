# Experience Intelligence E1 Contract — Episode Ledger

Date: 2026-09-29  
Issue: #176  
Base: `fe31e30e593a44b8b5ab565fa0db859bbefec0c6`  
Branch: `issue-176-e1-experience-ledger`

## Scope

E1 adds only the missing episodic-experience primitive and its evidence links. It does not add consolidation, retrieval, promotion, lifecycle/revocation, capability scoring, Chairman prompting, or any later E2–E8 behavior.

Existing truth owners remain authoritative:
- tasks/checkpoints: current execution state;
- task_decisions: decision history;
- knowledge_items: semantic facts/lessons/rules;
- procedures/procedure_versions: procedural memory;
- capabilities/capability_proofs: capability evidence;
- sources/artifacts/events/work reports/validation: raw evidence;
- relations/relation_evidence: evidence links.

## Durable objects

### experience_policy_versions
A versioned, immutable description of the episode schema/security contract. E1 ships one active policy version and its SHA-256 digest. Update/delete is blocked at the database boundary; a future policy change must publish a new version.

### experience_episodes
One immutable bounded snapshot for a completed task or terminal material work unit. The episode is derived from mechanically known Vres state only.

Required identity/provenance:
- episode_key;
- project_id and task_id;
- optional work_unit_key/report_key;
- task_family;
- policy_version;
- participation_class;
- trust_class;
- observed_at;
- source_digest;
- payload_digest;
- security_disposition.

Bounded payload:
- objective;
- acceptance criteria when a work unit owns them;
- constraints;
- task/work-unit outcome;
- host-observed worker/report facts when available;
- deterministic decisions by key;
- procedure/capability references;
- validation request/result references;
- source/artifact references;
- applicability context/tags;
- failure/gotcha state.

No raw assistant transcript, hidden/private chain-of-thought, scratchpad, model reasoning, or arbitrary caller-authored narrative is accepted.

## Capture contract

Capture reads existing persisted truth owners inside one PostgreSQL transaction. Callers provide only identity/selection inputs; they do not provide the episode payload.

A task episode is eligible only when the task is terminal (`completed` or `cancelled`). A work-unit episode is eligible only when the work unit is terminal (`passed` or `failed`).

For work-unit episodes, E1 persists only evidence mechanically attributable to that work unit plus stable task identity/objective and direct capability references. It does not copy or relation-link task-wide decisions, procedure runs, validation, artifacts, sources, or mutable task constraints as if they were direct work-unit evidence. Those remain available to the terminal task episode unless a future truth owner provides explicit work-unit attribution.

Idempotency:
- one task episode per task;
- one work-unit episode per task/work_unit_key;
- a repeated capture returns the existing episode only when the recomputed source/payload digests match;
- drift against an already captured immutable episode fails closed.

Concurrency:
- capture uses a transaction-scoped advisory lock over the task/work-unit identity;
- uniqueness constraints are the final race boundary.

## Security contract

All text and structured payload fields pass the #164 canonical sanitizer before persistence.

- safely redacted content may persist with `sensitive_sanitized`;
- residual credential-like content causes capture to fail closed and no episode is written;
- raw credential values/spans and raw sensitive hashes are never persisted;
- source files remain untouched.

E1 also rejects payload keys associated with hidden/private reasoning (including chain-of-thought, scratchpad, reasoning, hidden_reasoning, internal_monologue and close variants) even if such keys somehow appear in mechanically sourced JSON.

External/untrusted observations remain data, never policy/approval/permission. E1 performs no authority promotion.

## Trust and participation

Participation is explicit:
- `participated`: Vres/worker executed or directly host-observed the governed task/work unit;
- `observed`: imported/external evidence only.

E1 capture from Vres task/work-unit state is `participated`.

Trust is derived, not caller-selected:
- `validated_runtime` only for a completed task episode whose current task validation state is passed and whose latest terminal validation request is passed;
- E1 work-unit episodes do **not** inherit task-level validation authority; without a direct work-unit validation truth owner they remain `trusted_project_source`;
- cancelled/unvalidated task episodes remain `trusted_project_source`.

E1 does not create `user_authoritative` or company-canonical authority.

## Failure semantics

Meaningful failures remain failures:
- failed work units persist `outcome_status=failed`;
- cancelled tasks persist `outcome_status=cancelled`;
- failure/gotcha signals may be retained as bounded evidence;
- E1 never converts failure into a positive procedure or lesson.

## Evidence links

The episode ledger reuses `relations` + `relation_evidence` and may link an episode to:
- task;
- task decision;
- procedure;
- capability;
- validation request;
- source;
- artifact.

Relation creation must enforce project/scope compatibility. No separate generic link store is added.

## Digests

`source_digest` is SHA-256 over the canonical, mechanically sourced evidence identity and complete accepted source content before compact episode projection, after sanitization. Source evidence has explicit fail-closed size/count budgets; it is not silently truncated for the digest. Therefore a material change outside the compact payload window still changes the source digest.

`payload_digest` is SHA-256 over the canonical persisted compact episode payload plus immutable provenance fields.

Canonical JSON uses sorted keys, UTF-8, and deterministic separators.

## Explicitly out of E1

- memory consolidation or model-assisted lesson extraction;
- recurrence/materiality thresholds;
- semantic/lexical/vector episode retrieval;
- memory transition audit;
- supersession/revocation/forgetting;
- retrieval observations;
- procedure promotion/replacement;
- capability scoring;
- Chairman automatic experience injection;
- company-wide promotion;
- E2 or later implementation.

## E1 evidence gate

E1 is not DONE until all are green:
- targeted unit tests;
- migration contract tests;
- PostgreSQL integration;
- idempotency/concurrency/rollback;
- malformed/corrupt fail-closed cases;
- project/scope isolation;
- digest/provenance verification;
- secret/injection negative proofs;
- explicit no-chain-of-thought persistence proof;
- failure/gotcha semantics;
- proof of reuse of existing truth owners;
- issue-specific handoff/evidence.

Only after that boundary may E2 be considered.
