# Experience Intelligence E5 Contract — Capability / Procedure Experience Integration

Date: 2026-10-05  
Issue: #176  
Base: `a0a2769b99f4893733568194c0aa68e78e73aeab` (E1–E4 merged; post-main CI #471 green)  
Branch: `issue-176-e5-capability-procedure-experience`  
Frozen plan: commit `34f45afa0fb8d5a6a90bef53dec58d9ecef1093d`, file `docs/architecture/EXPERIENCE-INTELLIGENCE-PLAN-2026-09-27.md` (tranche E5).  
Retrieval policy/schema target: `176.e5.v1`.

## Scope

E5 makes E3/E4 experience retrieval capability-centric and procedure-experience-aware without creating a second capability score, procedure authority system, agent memory, or model-specific expertise profile.

E5 implements exactly:
- capability-centric experience retrieval;
- procedure/episode/feedback links;
- validated success/failure history;
- no opaque self-certified expert score;
- no automatic agent prompt rewriting.

Hard out of scope:
- E6 retrieval observations, cited/used-memory telemetry, utility/causal-credit evidence;
- E7 benchmarks/security ladder;
- E8 automatic Chairman injection;
- E9/#169 physical acceptance;
- procedure creation/rewrite/promotion policy changes;
- capability registration/proof policy changes;
- model/routing/agent prompt changes;
- company authority changes;
- new semantic/vector model policy;
- automatic lifecycle challenge/retire/supersede based on retrieval history.

## Verified current truth owners at the E4 main boundary

E5 MUST reuse these existing authorities.

### Capability authority

`vres.capabilities` owns capability identity/scope/status.  
`vres.capability_proofs` owns demonstrated positive capability proof.

`CapabilityService.mark_proven` already requires:
- an active capability;
- a completed task;
- task `validation_status='passed'`;
- same-project proof for project capabilities.

`capabilities.proven_count` is only a derived count. It is NOT an expert score, truth probability, authority level, or permission signal.

### Procedure authority

`vres.procedures` + `vres.procedure_versions` own procedural memory and the preferred version.  
`vres.procedure_runs` owns individual run records/telemetry.  
`vres.procedure_feedback` owns procedure feedback statements.  
Existing replay/optimization tables own replay-attested procedure optimization and promotion.

E5 MUST NOT alter preferred-version authority, acceptance authority, replay promotion, company promotion, or approval requirements.

A raw `procedure_runs.accepted` value is not by itself protected validation and MUST NOT become a quality score or authority signal.

### Episode authority

`vres.experience_episodes` is the immutable E1 episode ledger.

E1 already captures, in the immutable payload:
- procedure key/version/accepted state from task-linked procedure runs;
- capability keys from governed work units;
- task validation evidence;
- success/failure classification;
- task family, constraints, sources and evidence.

E1 also already writes deterministic semantic relations:
- `episode -> uses -> procedure`;
- `episode -> uses -> capability`;
- `episode -> derived_from -> task/decision/validation/artifact/source`.

E4 lifecycle state and source-revocation gates remain authoritative for whether episode content is eligible for current use.

### Relations and task linkage

`vres.relations` already supports `episode`, `procedure`, and `capability` nodes plus `uses` relations.

Procedure runs and feedback already have `task_id`. Episodes already have `task_id`.

Therefore E5 does not need a duplicate procedure-experience link table.

## Migration decision: NO migration

E5 adds no table, column, trigger, sequence, policy row, or write path.

Reason:
1. E1 already persists immutable procedure/capability references and relations.
2. `capability_proofs` already records validated positive capability evidence.
3. Procedure runs/feedback already join to tasks, and task-level episodes provide immutable experience provenance for those tasks.
4. E5 is a retrieval/integration tranche. Durable retrieval observations belong to E6.

Any implementation proposal that adds a generic capability-experience score table, procedure-experience cache, model expertise table, or E5 retrieval-observation table violates this contract.

## Retrieval contract

The existing `experience_retrieve` surface remains the only public retrieval surface.

Request keys remain unchanged.

In particular:
- `capability_keys` remains an explicit bounded request field;
- no model id, role score, expert score, feedback score, success probability, or authority override is accepted;
- no E5-specific mutation argument is added.

### Capability-key validation

When `capability_keys` are supplied, each requested key must resolve to an active capability visible to the project:
- same project; or
- existing company/global capability under the repository's current grandfathered/company authority semantics.

A foreign-project or inaccessible capability key fails closed with a generic inaccessible/unknown error. Do not leak cross-project existence.

Capability identity is structural. Do not infer capability from:
- model name;
- provider;
- agent shell;
- owner_role alone;
- free-text similarity alone.

### Capability-centric candidate sourcing

Before E5, `capability_keys` affect ranking only after a candidate was already retrieved.

E5 changes that: an explicit requested capability becomes a structured candidate-source signal.

An episode may become a candidate when:
- it already matches the existing lexical/task-family path; OR
- it has a direct E1 `episode uses capability` relation to a requested accessible capability; OR
- its task is the accepted task of a `capability_proof` for a requested capability.

A procedure may become a candidate when:
- it already matches the existing lexical path; OR
- a current-eligible episode directly `uses` that procedure and structurally matches a requested capability by the rules above.

No transitive graph inference is added in E5.

A relation or proof may increase relevance/candidate coverage only. It NEVER changes:
- scope;
- procedure preferred status;
- memory authority;
- validation state;
- lifecycle state;
- company approval.

## Procedure experience history

E5 may attach one bounded `experience_history` extension to an accepted procedure item.

It is evidence, never authority.

Closed shape:

```text
experience_history = {
  validated_success_episode_keys: [episode_key...],
  validated_failure_episode_keys: [episode_key...],
  failure_episode_keys: [episode_key...],
  feedback: [
    {
      feedback_type,
      statement,
      episode_key
    }
  ],
  latest_validated_at
}
```

Bounds:
- at most 3 validated success episode keys;
- at most 3 validated failure episode keys;
- at most 3 additional failure episode keys;
- at most 3 feedback entries;
- feedback statement <= 300 redacted/sanitized characters;
- deterministic ordering: newest evidence first, then stable key.

No counts are used for authority/ranking.
No aggregate “success rate”, “expertise score”, “confidence score”, star rating, probability, or quality grade is emitted.

### Validated procedure success history

A `validated_success_episode_key` requires all of:
- task-level episode (`work_unit_key IS NULL`);
- episode current-eligible under E4 lifecycle/support gates;
- episode trust class = `validated_runtime`;
- immutable episode payload validation status = `passed`;
- immutable episode payload contains the same procedure key with `accepted=true`.

Meaning:
“this procedure run was recorded as accepted inside an immutable task episode whose task passed required validation.”

It does NOT mean:
- the procedure caused the task success;
- the procedure is globally optimal;
- the procedure may be promoted;
- the model using it is an expert.

### Validated procedure failure history

A `validated_failure_episode_key` uses the same requirements except the immutable task episode contains the same procedure key with `accepted=false`.

Meaning:
“this procedure run was recorded as not accepted inside an immutable task episode whose task nevertheless completed with required validation.”

This is negative procedural evidence. It must never be converted into a positive demonstration.

### Other failure history

`failure_episode_keys` may include current-eligible project episodes directly linked to the procedure whose episode outcome is `failed` or `cancelled`.

These remain warning/example evidence under their existing trust class. They are not “validated failure” unless they satisfy the validated-task definition above.

Failure history does not silently deactivate, demote, challenge, retire, or rewrite an accepted procedure. Existing procedure/lifecycle authority remains the only owner of those actions.

## Procedure feedback integration

Procedure feedback is existing procedural evidence, not an instruction/approval channel.

A feedback entry may enter `experience_history.feedback` only when:
- the feedback is task-backed (`procedure_feedback.task_id IS NOT NULL`);
- the matching task has a current-eligible E1 task episode in the same project;
- that episode directly `uses` the same procedure;
- the feedback survives redaction/sensitive-content handling;
- the feedback text is not instruction-shaped under the existing read-time injection heuristic.

Feedback with no task, a foreign task, revoked/dead-support episode, or instruction-shaped text is not injected into the procedure item.

Feedback:
- cannot establish user approval;
- cannot alter preferred procedure version;
- cannot increase authority;
- cannot create a capability proof;
- cannot rewrite prompts;
- cannot trigger automatic optimization.

E5 diagnostics may count excluded/quarantined feedback, but E6 owns retrieval-use observations and utility telemetry.

## Capability experience presentation

E5 does not create a new capability memory class or a capability score section.

Existing episode items remain the concrete capability experience evidence.

For an episode retrieved through explicit capability structure:
- `why_retrieved` includes `capability_match`;
- `applicability.capability_keys` retains the exact bounded capability keys from immutable episode evidence;
- evidence retains `episode:<key>` and `capability:<key>`.

For accepted procedures, `applicability.capability_keys` may be populated only from direct current-eligible episode/capability evidence associated with that procedure.

This makes the existing ranking signal `capability_match` effective for procedures without inventing an expertise score.

## Ranking / authority invariants

E5 keeps the E3/E4 authority-first ordering.

Within the same authority tier:
1. exact structured task-family/capability match;
2. existing lexical/semantic fusion;
3. recency;
4. stable memory key.

The following MUST NOT affect authority tier:
- number of capability proofs;
- `capabilities.proven_count`;
- number of procedure runs;
- `procedure_runs.quality_score`;
- accepted/failed ratio;
- model/provider identity;
- feedback count;
- retrieval frequency.

The following MUST NOT automatically rewrite a procedure or agent:
- repeated success;
- repeated failure;
- capability match;
- feedback;
- retrieval rank.

## Pack schema

Schema version bumps from `176.e4.v1` to `176.e5.v1`.

Top-level sections and budgets remain unchanged.

The only new public item extension is:
- `experience_history`, and only on `memory_class='procedural'`.

Existing pack byte/item budgets remain:
- max 24 items;
- max 16 KiB pack;
- accepted procedures max 3.

History must be truncated before violating the existing pack budget.

No retrieval request, hidden reasoning, raw private transcript, raw chain-of-thought, DB numeric id, vector, credential, path, or URI is exposed.

## Read-only / transaction requirement

E5 retrieval remains read-only.

All new procedure/capability/history reads use the existing E3 read-only transaction or existing SELECT-only semantic signal.

E5 writes:
- no episode;
- no relation;
- no feedback;
- no capability proof;
- no procedure run;
- no lifecycle event;
- no observation.

E6 owns durable retrieval observations.

## Security / scope

Preserve every E3/E4 read gate:
- project isolation before relevance;
- approved company procedure boundary;
- #164 sensitive-content handling;
- read-time injection quarantine;
- E4 lifecycle status gate;
- source-revocation/dead-support gate;
- metadata-only revoked tombstones;
- premise/conflict/staleness handling.

Capability-centric retrieval is never allowed to broaden project scope.

A company/global capability match cannot make a project-local episode visible to another project.

A company procedure may be emitted only if it already satisfies the existing company procedure authority gate.

Feedback is always evidence-only, never an instruction role.

## No agent/model self-learning

E5 does not modify:
- Chairman prompt;
- project-agent prompt;
- specialist prompt;
- routing/model policy;
- model effort;
- agent permissions;
- validator policy.

Experience attaches to durable capability/procedure/task evidence, not a physical model instance.

## Expected implementation surface

Prefer a bounded implementation in:
- `src/vres_os/experience_retrieval.py`;
- `tests/test_experience_retrieval.py`;
- new focused PostgreSQL E5 integration tests.

Modify `procedures.py`, `capabilities.py`, migrations, MCP registration, or other truth owners only if a concrete frozen-contract requirement cannot be met through existing read paths. Such expansion requires explicit review before implementation.

## Required tests

### Unit / pure-contract
1. schema version is `176.e5.v1`;
2. request key set remains closed/unchanged;
3. `experience_history` is accepted only for procedural items and has a closed shape;
4. history bounds are deterministic;
5. capability structural match can outrank comparable same-tier lexical-only candidates;
6. no `proven_count`, run count, quality score, provider/model or feedback count changes authority tier;
7. a procedure with failure history remains an accepted procedure plus negative evidence; it is not auto-demoted;
8. a failed/cancelled episode never becomes a positive demonstration;
9. feedback text is redacted/bounded and instruction-shaped feedback is dropped;
10. no raw hidden/private reasoning field can enter the pack.

### PostgreSQL integration
11. capability-only request retrieves a directly linked eligible episode even when query text does not match it;
12. capability-only request can retrieve an accepted procedure through a direct eligible episode->procedure + episode->capability evidence path;
13. accepted `capability_proofs` can structurally source the task's eligible episode without using `proven_count`;
14. foreign-project capability keys fail closed and do not leak foreign episodes/procedures;
15. company/global capability matching does not cross project-local episode scope;
16. company procedures still require the existing E3 company authority gate;
17. validated success history is produced only from `validated_runtime` task episodes with matching procedure `accepted=true`;
18. validated failure history is produced only from matching validated task episodes with `accepted=false`;
19. ordinary failed/cancelled linked episodes stay warning evidence and never validated success;
20. task-backed procedure feedback links only through a same-task current-eligible episode that uses that procedure;
21. feedback without task identity, foreign task, revoked/dead-support episode or instruction-shaped content is omitted/fail-closed as applicable;
22. E4 revocation of a supporting source removes the affected episode/history from current capability/procedure experience;
23. retrieval performs no durable writes (before/after counts/digests over E1–E4 + procedure/capability truth owners);
24. malformed/corrupt immutable episode payload/digest fails closed;
25. deterministic ordering is stable across repeat reads.

### Regression
26. E3/E4 existing pack sections/budgets/authority roles remain unchanged except the deliberate schema bump/extension;
27. procedure authority/promotion tests remain green;
28. capability proof authority tests remain green;
29. E1 capture still emits the same immutable episode relations;
30. E4 current/historical/revocation tests remain green;
31. #163/#164/#174 security boundaries remain green.

## Acceptance cadence

Development:
- targeted red tests first;
- bounded implementation;
- targeted unit + PostgreSQL + E1–E4 regression;
- commit coherent chunks.

Final candidate:
- fresh isolated PostgreSQL full suite once;
- critical lint + diff hygiene;
- installed-runtime smoke because the public experience pack schema changes;
- release gate once;
- exact-head CI;
- one current-turn freeze checkpoint;
- one protected `vres-os:validator` Fable/high request.

Protected review is mandatory because E5 changes privileged retrieval/instruction context even though it adds no write authority.

Do not begin E6 until E5 is protected-accepted, guarded-merged and post-main CI is green.
