# Experience Intelligence E6 Contract — Retrieval Observability and Utility Evidence

Date: 2026-10-05
Issue: #176
Base: `6af7bddf246e0f628c3e52add9528742e85189ca` (E5 complete, PR #183 merged, post-main CI #473 green)
Task: `TASK-20261005-abb88a1f0e`
Status: FROZEN BEFORE IMPLEMENTATION

## Scope

E6 adds governed evidence about experience retrieval without changing the authority, security, lifecycle, scope, or normal output semantics established by E1–E5.

E6 owns four questions:

1. **What was actually surfaced?** Record one host-observed successful `experience_retrieve` call and the exact memory identifiers/ranks that were returned.
2. **What was explicitly referenced later?** Record only exact returned-memory-key references observed in assistant-authored public output or assistant-authored tool inputs.
3. **What happened afterward?** Join retrieval evidence read-only to existing task, validation, episode and completion truth owners.
4. **How would another bounded retrieval policy have behaved?** Run paired baseline/candidate retrieval-policy replay against the same database snapshot without weakening hard gates and without auto-selecting a winner.

E6 does **not** establish that a retrieved memory caused an outcome.

E6 does **not** automatically inject memory into Chairman context. That remains E8.

E6 does **not** create benchmark thresholds, held-out corpora, negative-transfer thresholds, poisoning campaigns, or scale gates. Those remain E7.

## Verified discovery at the frozen base

At `6af7bddf...`:

- `ExperienceRetrievalService.retrieve()` is explicitly READ ONLY.
- normal retrieval returns schema `176.e5.v1`;
- normal retrieval writes no observation row, task event, episode, relation, procedure evidence, capability evidence, or lifecycle event;
- E1 owns immutable `experience_episodes`;
- E2 owns immutable `experience_transitions`;
- E4 owns lifecycle/revocation evidence;
- task state, task events and validation requests own task/validation history;
- procedures/runs/feedback own procedural evidence;
- capabilities/proofs own capability evidence;
- relations own semantic/evidence links;
- `model_runs` owns model telemetry and is explicitly not retrieval evidence;
- there is no durable truth owner for retrieval observations or explicit post-retrieval memory references.

Claude Code's successful `PostToolUse` hook payload supplies the successful tool's `tool_input`, `tool_response`, `tool_use_id`, and optional `duration_ms`. Plugin hooks also run for subagent tool calls and carry `agent_id` / `agent_type`.

## Architecture decision

### One additive migration is required

E6 introduces exactly one migration:

`041_experience_retrieval_observability.sql`

Released migrations 001–040 remain immutable.

The migration adds only E6 observability/replay objects and privilege functions. It does not change E1–E5 table semantics.

### E6 policy version

Add immutable policy:

`176.e6.v1`

Canonical policy JSON:

```json
{"authority":"no_promotion","capture":"host_posttooluse_successful_experience_retrieve_only","payload":"digest_structural_no_memory_text_no_query_text_no_private_reasoning","policy_version":"176.e6.v1","reference":"exact_returned_memory_key_reference_only","replay":"same_snapshot_hard_gate_frozen_post_gate_variants_only","schema_version":1,"utility":"descriptive_join_no_causal_credit","writer":"trusted_provenance_writer"}
```

Canonical SHA-256:

`d61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5`

The migration must verify the exact policy version/schema/digest after insert, as E1/E2 do.

### Frozen E5 retrieval policy identity

The baseline normal-retrieval policy remains `176.e5.v1`.

Canonical SHA-256 of the existing E5 public `POLICY` object:

`7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9`

E6 must compute/verify this from the existing E5 constant rather than duplicate a divergent policy definition.

## Truth owners

E6 adds no duplicate owner for memory, authority, outcome, validation, procedure, capability, or task state.

Truth remains:

- retrieval eligibility/ranking/pack semantics -> `experience_retrieval.py`;
- memory content/status -> existing decisions/knowledge/procedures/episodes/lifecycle;
- validation -> `validation_requests`;
- task outcome -> `tasks` / `task_state`;
- episode outcome -> `experience_episodes`;
- procedure evidence -> procedure truth owners;
- capability evidence -> capability truth owners;
- host user authority -> existing provenance-writer boundary.

E6 owns only:

- host-observed retrieval event identity;
- exact structural returned-item identity/order;
- explicit post-retrieval exact-key reference evidence;
- immutable paired policy-replay evidence.

## New durable object: experience_retrieval_observations

One append-only row per accepted successful host `PostToolUse` observation of `experience_retrieve`.

Minimum fields:

- `observation_key` — durable public key;
- `idempotency_key` — SHA-256 uniqueness key;
- `project_id`;
- `session_id` — FK to the exact open Vres session observed by the host;
- nullable `task_id` — the task bound at observation time, if any;
- nullable `work_unit_key`;
- nullable `host_agent_id`;
- nullable `agent_type`;
- `provider_session_id_digest` — digest only, never raw provider session id in this ledger;
- `tool_use_id`;
- `policy_version='176.e6.v1'`;
- `retrieval_schema_version='176.e5.v1'`;
- `retrieval_policy_digest`;
- `request_digest`;
- `query_digest`;
- nullable `premises_digest`;
- nullable `task_key`;
- nullable `task_family`;
- bounded `capability_keys`;
- `temporal_intent`;
- nullable `as_of`;
- `include_candidates`;
- `raw_fallback`;
- `pack_digest`;
- `pack_bytes`;
- `estimated_tokens`;
- `item_count`;
- `abstained`;
- nullable bounded `reason`;
- bounded structural `diagnostics`;
- bounded `evidence_keys`;
- nullable `duration_ms`;
- `observed_at`;
- `created_at`.

### Observation idempotency

The same host tool invocation must never create two observations.

The idempotency identity must include at least:

- project;
- Vres session;
- agent identity when present;
- exact `tool_use_id`;
- E6 policy version.

Duplicate delivery returns the already-recorded observation and appends nothing.

A conflicting duplicate with the same idempotency identity but different request/pack digest fails closed.

## New durable object: experience_retrieval_items

Normalized structural rows for items actually returned by the observed pack.

Minimum fields:

- observation FK;
- global ordinal;
- section;
- section ordinal;
- memory key;
- memory class;
- authority class;
- scope;
- status;
- trust class;
- role;
- bounded `why_retrieved`;
- bounded evidence identifiers;
- bounded applicability signature/digest;
- bounded rank signals required for replay/audit;
- item digest.

Unique:

`(observation_id, memory_key)`

No item row may exist for a key absent from the returned host-observed pack.

## No raw content in E6 observability rows

Neither observation nor item tables may persist:

- raw retrieval query;
- raw premise values;
- memory `text`;
- procedure description/method text;
- knowledge statement/title;
- decision text/rationale;
- episode payload;
- raw chunk content;
- source content/path/URI;
- prompt/system prompt;
- assistant message text;
- tool input/output text;
- transcript;
- hidden/private chain-of-thought;
- credential/secret/token values;
- embedding/vector values.

Allowed persistent forms are:

- durable keys already exposed by the E5 pack;
- enum/boolean/count/timestamp fields;
- bounded non-secret structural reason codes;
- SHA-256 digests;
- existing evidence identifiers exposed by the pack.

The hook may inspect host payloads transiently in local process memory only to derive the allowed structural record.

## Host-observed capture boundary

Normal retrieval remains a read-only operation.

E6 MUST NOT insert an observation from inside `ExperienceRetrievalService.retrieve()`.

Flow:

```text
experience_retrieve
  -> existing E5 READ ONLY retrieval transaction
  -> return normal E5 pack
  -> successful Claude Code PostToolUse
  -> local E6 observer parses only required structure
  -> protected provenance-writer function validates host/session binding
  -> append observation/items
```

A failed tool call creates no successful retrieval observation.

An observation-hook failure must not rewrite the already-returned pack or manufacture a task failure. It must fail closed for evidence, emit a bounded local diagnostic without raw payload/secret text, and leave an observable telemetry gap rather than inventing a row.

## Provenance-writer authority

Host retrieval observations and explicit-reference rows are host provenance and cannot be runtime-forgeable.

Migration 041 must follow the migration-023/040 split-role pattern:

- observability tables/sequences/functions: REVOKE from PUBLIC;
- runtime role: no direct INSERT/UPDATE/DELETE on observation/reference tables;
- provenance writer role: no direct table mutation required;
- writer role receives EXECUTE only on exact protected SECURITY DEFINER writer functions;
- SECURITY DEFINER functions verify `session_user` equals the configured `user_event_writer`;
- runtime receives read access required by read-only evidence/replay services, but not writer execution;
- migrator remains schema owner under the established boundary.

`database_boundary.activate_boundary()` must activate migration-041 privileges idempotently after secure setup/migration.

Tests must prove the runtime credential cannot forge host observation/reference rows.

## Session/task attribution

The protected writer resolves the exact open Vres session by:

- project;
- Claude provider;
- host provider-session id supplied by the hook.

The durable ledger stores the Vres session FK plus provider-session digest, not raw provider session id.

If the session has a bound task at observation time, store that exact task FK.

If there is no bound task, task_id remains NULL. E6 must not create/bind a task merely to record telemetry.

## Governed subagent attribution

For a hook with `agent_id`:

1. store the host agent id and agent type;
2. if exactly one current orchestration work unit in this project/task is bound to that `host_agent_id`, store its `work_unit_key`;
3. otherwise leave `work_unit_key` NULL and mark bounded attribution state `unattributed_host_agent`.

Never infer a governed work unit from agent type/name alone.

Main-thread retrieval has NULL agent/work-unit fields unless another mechanically authoritative owner exists.

## Request digest contract

Before storage, reconstruct the closed E5 retrieval request shape and apply the same input normalization rules where possible.

Persist:

- `request_digest = sha256(canonical normalized request)`;
- `query_digest = sha256(normalized query text)`;
- `premises_digest = sha256(canonical normalized premises)` when premises exist.

Do not persist query/premise text.

A host payload that cannot be structurally reconciled with a valid successful E5 pack must not create a durable observation.

## Pack digest contract

Persist:

`pack_digest = sha256(canonical exact tool_response pack)`

The response must pass the existing frozen E5 pack-schema validation before observation.

The observer must reject:

- missing/unknown top-level pack keys;
- internal underscore-prefixed keys;
- unknown item extensions;
- non-E5 schema version;
- duplicate returned memory keys;
- impossible section/role/authority combinations already prohibited by the E5 contract.

Observation code does not repair malformed packs.

## Diagnostics

Store only bounded E5 structural diagnostics needed for evaluation.

Diagnostics must:

- use a closed allow-list;
- contain no raw error string;
- contain no database id;
- contain no path/URI;
- contain no secret-shaped value.

Error class names already emitted by E5 diagnostics may be retained only if already part of the public pack.

## New durable object: experience_retrieval_references

A reference row means only:

> after a specific retrieval observation, host-observed assistant-authored material contained an exact memory key that was actually returned by that observation.

Minimum fields:

- `reference_key`;
- `idempotency_key`;
- observation FK;
- memory key;
- source kind;
- host event identity/digest;
- nullable tool_use_id;
- nullable agent_id;
- observed_at;
- created_at.

Allowed source kinds in v1:

- `assistant_public_text`;
- `assistant_tool_input`;
- `subagent_handback`.

No other source kind may be silently accepted.

## Explicit-reference capture

E6 may transiently inspect:

- assistant-authored public text available to existing bounded transcript/Stop helpers;
- assistant-authored tool inputs from hook payloads;
- `SubagentHandback.message` as assistant-authored handback content.

It must extract only exact memory keys previously surfaced by an eligible prior observation in the same project/session/agent context.

It persists only:

- the exact matched returned memory key;
- source kind;
- event/tool identity;
- digest of the inspected assistant-authored evidence;
- timestamps.

It never persists the inspected text.

Tool responses/results are not reference evidence: external output repeating a key does not show the assistant used it.

User prompts are not reference evidence: a user typing a key is not proof the retrieved memory was used.

## Reference time and ambiguity

A reference must be temporally after the observation.

If the same memory key was surfaced repeatedly in the same session/agent, attribute a later exact-key reference to the most recent eligible observation before the reference.

If attribution is ambiguous or the relevant host evidence is outside the bounded transcript window, write no reference.

No reference row is better than fabricated attribution.

## Absence semantics

No reference rows for a returned item means:

`reference_status = not_observed`

It MUST NOT be labelled:

- unused;
- ignored;
- harmful;
- ineffective.

Models can use content semantically without naming the memory key.

E6 measures explicit reference evidence, not hidden cognition.

## Utility evidence service

E6 adds a read-only utility evidence service over existing truth owners.

For an observation it may report:

- observation identity/time;
- task identity/status/completed_at;
- exact returned memory keys;
- explicit reference rows;
- validation requests completed after the observation;
- terminal task episode created/observed after the observation;
- terminal outcome if mechanically available;
- pack size/token/latency evidence;
- `causal_credit='not_established'`.

It must not copy task/validation/episode truth into a second mutable truth owner.

## Time ordering

Downstream evidence counts only when its authoritative timestamp is after the retrieval observation.

Examples:

- validation completed before retrieval -> not downstream evidence;
- task completed before retrieval -> not downstream evidence;
- validation completed after retrieval -> downstream validation evidence;
- E1 terminal task episode observed after retrieval -> downstream episode evidence.

Unknown/missing timestamps remain unknown.

## No causal-credit overclaim

Every E6 utility/replay public result must preserve this invariant:

`causal_credit = "not_established"`

E6 may say:

- retrieved before;
- explicitly referenced after;
- followed by completed/failed task;
- followed by passed/failed validation;
- correlated in a replay cohort.

E6 may not say:

- caused success;
- improved performance;
- made the worker better;
- proved expertise;
- should increase authority.

Those require controlled E7 evaluation and/or later governed policy decisions.

## No opaque utility/expertise score

E6 adds no single scalar:

- utility score;
- memory importance score;
- expertise score;
- causal score;
- success probability.

Expose component evidence instead.

Existing stored confidence fields remain owned by their existing objects and do not become E6 utility scores.

## New durable object: experience_retrieval_replays

One immutable record for one paired baseline/candidate policy replay.

Minimum fields:

- `replay_key`;
- project id;
- optional task id;
- E6 policy version;
- request digest;
- snapshot timestamp;
- baseline retrieval policy digest;
- candidate policy;
- candidate policy digest;
- baseline pack digest;
- candidate pack digest;
- baseline item keys/order;
- candidate item keys/order;
- added keys;
- removed keys;
- reordered keys;
- baseline/candidate pack bytes;
- baseline/candidate estimated tokens;
- baseline/candidate abstention;
- bounded diagnostics delta;
- `causal_credit='not_established'`;
- created_at.

No replay row is promotion/activation authority.

## Paired replay transaction

A paired replay must derive baseline and candidate from the **same database snapshot**.

Required execution:

1. open one PostgreSQL transaction with `REPEATABLE READ`;
2. set transaction READ ONLY for retrieval reads;
3. validate project/task/capability/request once;
4. collect the hard-gated candidate universe once;
5. compose baseline and candidate from that same universe;
6. close the read-only snapshot;
7. persist only the bounded replay result in a separate append-only transaction.

If the implementation cannot prove the same candidate universe was used, no paired replay evidence is written.

## Frozen hard gates

Candidate replay policy may never parameterize or weaken:

- project isolation;
- approved-company scope;
- capability visibility;
- task/project binding;
- E4 current/historical lifecycle;
- source-revocation/dead-support suppression;
- sensitive-content exclusion/sanitization;
- instruction-shaped low-trust quarantine;
- authority classes;
- authority tier ordering;
- role eligibility;
- conflict no-winner semantics;
- premise mismatch downgrade;
- revoked tombstone content withholding;
- raw-evidence owner/scope gates.

A candidate requesting a change to any hard gate is rejected before replay.

## Candidate policy v1

E6 v1 candidate replay may vary only bounded **post-gate** composition/relevance parameters.

Allowed candidate fields:

- per-section budgets;
- max total items;
- max pack bytes;
- reciprocal-rank fusion `k` within a closed safe numeric range.

It may not add a new ranking signal in E6 v1.

Bounds must be frozen in code/tests before the first candidate replay is accepted.

Baseline is always the exact existing E5 policy.

## Replay interpretation

Replay output is descriptive only.

Allowed statements:

- candidate returned these additional/removal/reordered keys;
- candidate used fewer/more pack bytes;
- candidate changed estimated tokens;
- candidate abstained where baseline did not, or vice versa.

Forbidden:

- candidate is better;
- auto-select candidate;
- update active E5 policy;
- promote memory;
- change model/routing/procedure;
- causal improvement claim.

Policy activation, if ever authorized, is a separate governed change after E7 evidence.

## Normal retrieval regression invariant

The default user-facing `experience_retrieve` result must remain byte-equivalent to the E5 behavior on unchanged database state.

E6 may refactor internals only if tests prove:

- exact same public schema `176.e5.v1`;
- exact same ordering;
- exact same item text;
- exact same authority/status/role;
- exact same diagnostics;
- exact same pack bytes/digest for representative and PostgreSQL journeys.

No E6 observation identifier is added to the E5 pack.

## Hook topology

Preferred bounded hook change:

- add one local command observer for successful `PostToolUse` events;
- specialize the retrieval-observation path when `tool_name` is exact Vres `experience_retrieve`;
- for later PostToolUse events, inspect assistant-authored `tool_input` only for exact surfaced keys;
- extend existing Stop/SubagentStop paths only as needed for public-text / handback exact-key references.

Do not create a second general hook framework.

Do not remove or weaken existing:

- reply guard;
- external capability guard;
- agent preflight;
- validation ingestion;
- credential ingress;
- session lifecycle;
- contamination controls.

## Failure behavior

Observation/reference/replay persistence is evidence, not execution authority.

Therefore:

- retrieval succeeds/fails according to E5, independent of telemetry persistence;
- a telemetry hook failure never changes the already-executed retrieval response;
- telemetry failure must not invent a successful observation;
- protected writer errors are locally logged in bounded form with no raw payload;
- replay persistence failure returns failure to the replay caller and writes no partial replay row.

Database writes are transactional and idempotent.

## Immutability

E6 observations, items, references and replays are append-only.

UPDATE/DELETE must fail at database boundary.

Test-only cleanup may use the established isolated-test teardown mechanisms only where explicitly necessary. Production runtime gets no mutation bypass.

## Lifecycle / revocation interaction

A later E4 revocation does **not** delete historical E6 observation evidence.

Historical observation truth remains:

> this key was surfaced at this time under this policy.

Current utility views must join the item's current lifecycle state separately and must not present a revoked item as currently usable.

E6 never reconstructs or exposes revoked content from its digest/key record.

## Privacy / retention boundary

E6 deliberately stores less than the E5 pack.

It retains structural/digest evidence needed for evaluation.

It does not become a transcript archive.

Retention/physical deletion policy beyond existing project/database lifecycle is deferred unless required by #170 privacy/go-live review.

Project/user/database isolation continues to be the primary confidentiality boundary.

## MCP / public surfaces

E6 may add read-only MCP evidence surfaces only if necessary for governed Chairman/validator inspection.

Any E6 MCP surface must:

- bind project from the current session;
- reject caller-supplied project_id;
- use closed request schemas;
- expose no raw query/premise/text/transcript;
- expose `causal_credit='not_established'`;
- create no authority.

Host writer functions are not exposed as ordinary MCP tools.

The user does not manually record retrieval observations.

## Explicitly out of E6

- automatic E8 Chairman retrieval/injection;
- E7 benchmark corpus or acceptance thresholds;
- streaming-learning benchmark;
- memory-poisoning red-team suite;
- negative-transfer threshold;
- recurrence/materiality promotion threshold;
- E2 recurrence acceptance;
- automatic memory/procedure/company-rule promotion;
- automatic prompt/agent/model/routing changes;
- causal inference;
- per-model personal memory;
- opaque utility/expertise scoring;
- new embedding policy;
- new generic telemetry warehouse;
- raw transcript persistence;
- hidden reasoning persistence.

## Expected implementation surface

Expected new files:

- `src/vres_os/migrations/041_experience_retrieval_observability.sql`;
- `src/vres_os/experience_observability.py`;
- `src/vres_os/experience_replay.py`;
- focused unit/integration tests.

Expected bounded modifications:

- `src/vres_os/database_boundary.py`;
- `src/vres_os/experience_retrieval.py` only for pure replay/refactor hooks that preserve byte-identical normal output;
- `src/vres_os/hooks.py`;
- `src/vres_os/cli.py` if a local hook command is required;
- `plugins/vres-os/hooks/hooks.json`;
- plugin bin script only if needed for bounded host observation launcher;
- `src/vres_os/mcp_server.py` only for read-only E6 evidence/replay inspection surfaces.

Any expansion into procedure/capability/knowledge authority code requires explicit re-review because it is outside the frozen E6 ownership boundary.

## Implementation chunks

### Chunk 1 — migration + host retrieval observation

Deliver:

- policy 176.e6.v1;
- migration 041;
- immutable observation/items ledgers;
- writer-only SECURITY DEFINER record function(s);
- database-boundary activation;
- PostToolUse successful retrieval observer;
- project/session/task/agent/work-unit attribution;
- optional host duration;
- exact pack/item digests;
- no normal retrieval behavior change.

### Chunk 2 — explicit reference + utility evidence

Deliver:

- immutable explicit-reference ledger;
- writer-only reference function;
- exact-key extraction from assistant-authored tool inputs/public text/handback;
- no raw inspected text persisted;
- read-only downstream task/validation/episode evidence view/service;
- `not_observed` absence semantics;
- `causal_credit='not_established'`.

### Chunk 3 — paired policy replay

Deliver:

- same-snapshot candidate universe;
- baseline exact E5 policy;
- bounded candidate post-gate policy;
- immutable replay record;
- deterministic add/remove/reorder/budget deltas;
- no winner/activation/promotion;
- byte-equivalent normal E5 retrieval regression proof.

## Test contract

### Migration / schema / privilege

1. migration count becomes 41; highest is 041;
2. E6 policy version/digest exact;
3. observation/item/reference/replay schema constraints are closed;
4. all E6 ledgers reject UPDATE/DELETE;
5. runtime cannot direct-write host observation/reference rows;
6. runtime cannot execute protected host-writer functions;
7. provenance writer can execute only intended E6 writer functions;
8. PUBLIC cannot execute or mutate protected E6 surfaces;
9. boundary activation is idempotent;
10. fresh install and upgrade from 040 both work.

### Retrieval observation

11. successful MCP `experience_retrieve` PostToolUse creates exactly one observation;
12. duplicate identical hook delivery is idempotent;
13. conflicting duplicate fails closed;
14. failed retrieval creates no successful observation;
15. normal retrieval remains READ ONLY;
16. normal E5 returned pack is byte-identical with E6 observer enabled/disabled;
17. exact item count/order/sections/keys match host tool_response;
18. pack digest matches canonical exact response;
19. request/query/premise digests are deterministic;
20. raw query/premise/memory text is absent from every E6 table;
21. secret-shaped/synthetic credential values cannot persist;
22. hidden reasoning/transcript/tool-response text cannot persist;
23. abstained pack is observable without fabricating items;
24. optional duration_ms persists when present and remains NULL/unknown when absent;
25. caller cannot spoof project through hook payload;
26. foreign/closed session cannot create an observation;
27. unbound session may create observation with task NULL but cannot invent task binding;
28. governed subagent host_agent_id maps only to exact bound work unit;
29. ambiguous/unmatched host agent remains unattributed, not guessed;
30. main-thread observation does not invent an agent/work unit.

### Explicit reference

31. assistant public exact returned key creates one reference;
32. assistant tool-input exact returned key creates one reference;
33. SubagentHandback exact returned key creates one reference;
34. key absent from the referenced observation creates no reference;
35. tool response repeating a key creates no reference;
36. user prompt repeating a key creates no reference;
37. duplicate scan is idempotent;
38. repeated retrieval of same key attributes to latest eligible prior observation;
39. ambiguous/out-of-window reference writes nothing;
40. reference ledger stores evidence digest, never inspected text;
41. thinking/tool-result/private reasoning is never reference evidence;
42. no reference yields `not_observed`, never `unused`.

### Utility evidence

43. completed task after observation is surfaced as downstream;
44. task completion before observation is not downstream;
45. validation completed after observation is downstream;
46. validation completed before observation is not downstream;
47. terminal E1 task episode after observation is joined by authoritative task identity;
48. missing outcome/validation remains unknown;
49. revoked memory can remain historical observation evidence but is marked non-current by live lifecycle join;
50. every utility response states `causal_credit='not_established'`;
51. no opaque utility/expertise/success score exists.

### Paired replay

52. baseline/candidate execute from same REPEATABLE READ snapshot and same hard-gated universe;
53. baseline pack equals ordinary E5 retrieval for the same request/state;
54. candidate cannot alter project/company/capability/lifecycle/revocation/security/authority gates;
55. candidate with unknown field fails closed;
56. candidate bounds fail closed;
57. allowed budget change produces deterministic descriptive delta;
58. allowed RRF-k change can reorder only within already-eligible authority ordering;
59. candidate cannot introduce a new ranking signal;
60. repeated replay on unchanged snapshot/input is deterministic;
61. replay row is immutable/idempotent as designed;
62. replay cannot mutate active retrieval policy;
63. replay cannot mutate memory/procedure/capability/model/routing/validation authority;
64. replay exposes no winner and states `causal_credit='not_established'`.

### Regression / security

65. E1 episode capture unchanged;
66. E2 consolidation unchanged;
67. E4 lifecycle/revocation/contamination unchanged;
68. E5 capability/procedure history behavior unchanged;
69. existing raw fallback/security/injection tests remain green;
70. project isolation across observations/references/replays;
71. company-approved memory key may be observed by an eligible project but observation itself remains project/session bound;
72. no cross-project utility join;
73. hook error logging contains no raw payload/credential/query/memory text;
74. Windows PowerShell hook launcher preserves UTF-8/no-BOM and bounded stdin behavior;
75. installed plugin/runtime includes migration 041 and E6 hook code.

## Acceptance cadence

Implementation is allowed only after this exact contract commit is checkpointed by the E6 Chairman task.

Per chunk:

1. targeted red tests first for the chunk's frozen criteria;
2. smallest implementation;
3. affected unit/static;
4. fresh isolated PostgreSQL integration where durable state changes;
5. critical Ruff;
6. bounded diff-check;
7. explicit Chairman checkpoint only at meaningful chunk boundaries.

After coherent E6 candidate:

- one fresh disposable PostgreSQL full suite;
- isolated `VRES_DATA_DIR`;
- exact migration count/highest proof;
- no use/repair of the historical drifted DB;
- release gate once;
- candidate wheel exact Python/SQL byte proof;
- installed-runtime and hook smoke;
- exact clean Git identity;
- one final-local-acceptance checkpoint;
- PR and exact-head CI;
- one current-turn protected-validation freeze checkpoint;
- `validation_prepare` once for complete E6 scope;
- protected `vres-os:validator`, Fable/high, no model override;
- PASS requires every required check passed and zero not_run;
- guarded expected-head merge;
- exact post-main push CI;
- durable E6 closure;
- E6 task complete exactly once.

Protected Fable/high is mandatory because E6 adds host-observed provenance writes, new database privilege surfaces, telemetry/privacy behavior, and replay evidence.

## Frozen constraints

After this contract is committed:

- do not edit this contract during E6 implementation;
- implementation must conform to it or stop for an explicit contract amendment/re-freeze;
- no silent scope expansion;
- no E7/E8 work;
- no weakening E1–E5 authority/security/lifecycle behavior;
- no causal-credit language stronger than this contract permits.
