# #176 E1 — Experience Episode Ledger Contract

Date: 2026-09-29  
Issue: #176 — Experience Intelligence: governed agent learning, episodic memory and evidence-based experience reuse  
Base: `fe31e30e593a44b8b5ab565fa0db859bbefec0c6`  
Policy version: `176.e1.v1`

## Scope

E1 adds only the missing episodic-experience primitive. It does not add retrieval,
consolidation, promotion, self-training, prompt/policy mutation, or a second generic
memory subsystem.

Existing truth owners remain authoritative:

- tasks/checkpoints/task events: execution continuity and underlying task evidence;
- task_decisions: decision history;
- knowledge_items: semantic facts/lessons/rules;
- procedures/procedure_versions/runs/feedback: procedural memory;
- capabilities/capability_proofs: capability evidence;
- validation_requests: independent validation evidence;
- sources/artifacts: underlying source evidence;
- relations/relation_evidence: typed evidence links.

## Episode identity

Two mechanically grounded episode origins are supported:

1. `task` — one immutable snapshot of a terminal `completed` task.
2. `work_unit` — one immutable snapshot of a terminal `passed` or `failed`
   orchestration work-unit attempt.

Work-unit identity includes `work_unit_key + attempt_count` so a failed attempt can
remain a failure even when a later retry succeeds.

Capture is idempotent. Re-capturing the same origin returns the existing row only when
its source and payload digests match; divergent recapture fails closed.

## Stored episode contract

Every row preserves at least:

- episode key and schema/policy version;
- project and task identity;
- optional work-unit/report/attempt provenance;
- participated/observed mode;
- task family and capability/domain applicability;
- bounded objective, context/premise, constraints and outcome summaries;
- outcome status plus explicit success/failure classification;
- bounded gotcha/failure signals;
- procedure and decision references;
- validation reference when one exists;
- source/evidence manifest;
- trust class;
- observed time;
- applicability tags;
- source digest and payload digest;
- security/sensitivity disposition and bounded security flags.

The episode payload is immutable after insert. Update/delete is denied except for the
explicit transaction-local fixture-cleanup bypass used by disposable integration tests.

## Provenance and trust

E1 never accepts caller-authored free-form episode objects. Capture is reconstructed
inside Vres from existing database facts.

Trust is derived, not caller supplied:

- a completed task with current protected PASS -> `validated_runtime`;
- other governed local task/work-unit outcomes -> `trusted_project_source`.

E1 automatic capture creates `participated` episodes only. The schema reserves
`observed` for a later governed path; imported/external observations are not promoted
during E1.

Relations are written through the existing relation graph to the task and, when
mechanically present, decisions, procedures, capabilities, validation requests,
sources and artifacts. The immutable episode also retains the reference manifest so
relation-table navigation is not the sole provenance record.

## Security boundary

All text selected for episode persistence is re-checked through the canonical #164
sanitizer before insert.

- Sanitizable credential material is persisted only in sanitized form.
- Residual suspicious credential forms fail closed and the episode is not written.
- Known hidden/private reasoning field names (for example `chain_of_thought`,
  `hidden_reasoning`, `private_reasoning`, `reasoning_trace`, `scratchpad`)
  are rejected recursively if found in selected evidence.
- Instruction-like untrusted text is stored only as inert data and may add a bounded
  security flag; it never changes authority, policy, permissions, validation, routing,
  procedures or company rules.
- No raw source-file credential hash is introduced.
- Existing Credential Broker and secret-safe onboarding remain the only credential
  and ingestion authorities.

This is deterministic hardening, not a claim of universal secret or injection detection.

## Digest contract

`source_digest` is SHA-256 over canonical JSON of the mechanically selected source
manifest after safety checks.

`payload_digest` is SHA-256 over canonical JSON of the normalized episode payload
excluding generated row identity/timestamps/digests.

Canonical JSON uses stable key ordering, UTF-8, finite JSON values and compact
separators.

## Lifecycle integration

Work-unit episodes are captured in the same database transaction that records the
host-observed terminal `passed` or `failed` outcome.

Task episodes are captured in the same database transaction that changes the task to
`completed`. A capture failure rolls back the terminal lifecycle write rather than
leaving an unevidenced terminal outcome.

No E1 write occurs on an unfinished task/work unit.

## E1 validation boundary

Before E2, E1 requires:

- migration contract coverage;
- unit coverage for canonicalization, bounded safety and no-hidden-reasoning rules;
- PostgreSQL integration for task and work-unit success/failure episodes;
- idempotency and concurrent duplicate protection;
- transaction rollback on invalid/cross-scope/unsafe evidence;
- project isolation;
- source/payload digest verification;
- secret and instruction-poisoning negative proofs;
- relation reuse rather than duplicate authority/link stores;
- explicit proof that failed attempts remain failures after later success;
- existing suite/CI green;
- protected Fable/high acceptance before E1 is declared DONE.

E2 is not authorized by this contract.
