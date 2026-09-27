# Vres Experience Intelligence — Governed Learning Plan

Date: 2026-09-27  
Source issue: #176 — Experience Intelligence: governed agent learning, episodic memory and evidence-based experience reuse  
Planning base: `f0a69c3e471fe25c6547ee1af162019caf290d49`

> This file is the Git-history copy of the complete #176 design plan.  
> It is planning documentation only. It does not authorize implementation, merge, or protected-validation claims.

## Objective

Build a state-of-the-art, governed **Vres Experience Intelligence / Learning Loop** so Vres compounds verified organizational experience across tasks, projects, capabilities and agents without allowing uncontrolled self-modification, memory poisoning, hidden policy drift, cross-project leakage, or “learning” claims unsupported by evidence.

This is a new foundation outside the frozen #163–#170 ledger and separate from #174. It must be integrated before final #169 live acceptance so the first real legacy-project adoption can prove that useful lessons, gotchas, decisions and procedures survive into later work.

Engineering principle:

> **Models are replaceable workers. Vres owns the experience.**

Experience principle:

> **Store evidence richly, retrieve context sparsely, promote authority conservatively.**

## Dependency / sequencing

Do not implement this learning foundation until:
- #163 Credential Broker is merged;
- #164 secret-safe onboarding / pre-model sanitization is merged;
- #174 Engineering Architecture Governance is merged and authoritative.

Reason: persistent memory turns every stored item into future privileged context. External/project content must pass the secret/injection boundary before it can participate in learning.

The learning foundation should land before #168 full project adoption and #169 integrated live acceptance if practical. #168 must consume it rather than inventing a second learning/memory mechanism.

## Research-derived design principles

The design is based on current agent-memory research and operational security guidance, including:

- LongMemEval / LongMemEval-V2: evaluate information/state recall, temporal updates, workflow knowledge, environment gotchas, premise awareness, abstention and accuracy-latency trade-offs.
- MemoryAgentBench / MemBench: evaluate retrieval, test-time learning, long-range understanding, selective forgetting, effectiveness, efficiency and capacity.
- HaluMem / TrustMem / MemTxn: memory extraction/update operations themselves can hallucinate, omit or corrupt; verify memory transitions and source support rather than judging only final answers.
- Agent Workflow Memory / BREW / Voyager / ExpeL / Reflexion: reusable workflow/skill/experience memory can improve future behavior without changing model weights.
- PlugMem / Memora / A-MEM: retrieve compact knowledge/abstractions linked back to specific evidence rather than flooding context with raw trajectories.
- RecMem: consolidate selectively/recurrence-first rather than running expensive reflection after every interaction.
- MAGE: current execution state and long-term experience are different concerns; bad historical branches must not contaminate current state.
- ReFind-style evidence search: preserve the raw/source archive and allow bounded agent-controlled refinding as a fallback instead of assuming every useful detail was perfectly summarized.
- OWASP ASI06 / Agent Security / RAG security and MITRE ATLAS context poisoning: persistent memory is an integrity and confidentiality boundary; untrusted data may never become privileged instructions merely because it was remembered.
- 2026 forgetting/unlearning work: distinguish what is retained from what is eligible to influence the current answer; source revocation must invalidate derived memory rather than deleting only one visible row.

Primary references:
- https://arxiv.org/abs/2605.12493
- https://arxiv.org/abs/2410.10813
- https://arxiv.org/abs/2507.05257
- https://arxiv.org/abs/2506.21605
- https://arxiv.org/abs/2511.03506
- https://arxiv.org/abs/2606.25161
- https://arxiv.org/abs/2607.27834
- https://arxiv.org/abs/2603.03296
- https://arxiv.org/abs/2602.03315
- https://arxiv.org/abs/2511.20297
- https://arxiv.org/abs/2605.16045
- https://arxiv.org/abs/2606.06090
- https://arxiv.org/abs/2603.18272
- https://arxiv.org/abs/2409.07429
- https://arxiv.org/abs/2308.10144
- https://arxiv.org/abs/2303.11366
- https://genai.owasp.org/2026/05/13/memory-is-a-feature-it-is-also-an-attack-surface/
- https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html
- https://d3fend.mitre.org/offensive-technique/attack/AML.T0080/

## Non-negotiable architecture

### 1. No private agent self-training

Agents/models do not privately mutate their own prompts, policy, routing, role, permissions or validation standard based on experience.

Learning changes durable Vres memory. Changes to:
- Chairman instructions;
- agent definitions;
- architecture rules;
- model/routing policy;
- validation policy;
- company-wide procedures/rules

remain explicit governed changes with their existing authority and protected-review requirements.

### 2. Reuse current Vres truth owners

Do not create a second generic “memory database”.

Existing owners remain authoritative:
- task/checkpoint state -> live execution/continuity;
- task decisions -> decision history and rationale/provenance;
- knowledge_items -> semantic facts/findings/lessons/rules;
- procedures/procedure_versions -> reusable procedural memory;
- procedure_feedback/runs/replay -> corrections and measured procedure evolution;
- capabilities/capability_proofs -> demonstrated capability evidence;
- relations -> semantic/evidence relationships;
- sources/artifacts/task events/work reports/validation -> underlying evidence.

Add only missing experience-specific primitives.

### 3. Separate memory classes

Vres must distinguish at least:

**Execution state**
- what is currently happening;
- checkpoint/current branch/current constraints;
- never replaced by long-term memory retrieval.

**Episodic experience**
- a bounded record of a specific task/work-unit episode;
- context/premises, objective, actions at a summary level, outcome, failures/gotchas, validation and evidence;
- no raw hidden chain-of-thought.

**Semantic memory**
- reusable facts, lessons, environment knowledge, premises, gotchas, exceptions;
- stored through existing knowledge lifecycle.

**Procedural memory**
- accepted reusable workflows/recipes;
- stored through existing procedures lifecycle.

**Decision memory**
- user/team choices, rationale, supersession/retirement;
- existing task decision history remains authoritative.

**Capability experience**
- evidence that a domain/capability has succeeded or failed on certain task families;
- attach to capability, not to one physical model instance.

**Raw evidence archive**
- source/task/artifact/event history retained for provenance and bounded refinding;
- not injected wholesale into model context.

## Target data model

### New: experience_episodes

One immutable/bounded episode per material completed task or material work-unit outcome.

Minimum fields:
- episode_key;
- project_id;
- task_id;
- optional work_unit_key / report_key;
- task_family;
- domain/capability keys;
- objective/goal summary;
- context/premise summary;
- relevant constraints;
- outcome status;
- success/failure classification;
- environment/gotcha signals;
- procedure keys used;
- decision keys used;
- validation request/result reference;
- source/evidence references;
- trust class;
- observed_at;
- applicability tags;
- source digest / episode payload digest;
- security/sensitivity disposition.

Do not persist raw private reasoning. Persist concise decision factors and evidence that can be shown to another worker.

### New: experience retrieval observations

Record what memory the system actually surfaced and whether it was subsequently used/cited.

Minimum:
- task/session/work-unit;
- retrieval policy version;
- query/task signature;
- returned memory keys and ranks;
- reason for retrieval;
- token/latency budget;
- later usage/citation;
- task/validation outcome.

This is evidence for future retrieval-policy evaluation, not proof that a memory caused success.

### New: memory transition audit

Every model-assisted consolidation/update must be represented as a source-bound transition:
- insert/update/supersede/retire candidate;
- before/after digests;
- exact source episode/evidence keys;
- trust/scope;
- deterministic transition checks;
- validation/approval references when required.

Do not let an LLM directly overwrite durable memory without a transactional/source-supported boundary.

Use existing relations/evidence tables rather than adding duplicate link stores where possible.

## Experience lifecycle

```text
work/task evidence
  -> deterministic episode snapshot
  -> materiality / recurrence trigger
  -> candidate consolidation
  -> source-support + security checks
  -> observed project lesson / procedure candidate
  -> independent validation/authority when required
  -> validated/canonical reusable memory
  -> just-in-time retrieval
  -> worker use
  -> outcome/validation evidence
  -> reinforce / challenge / supersede / retire
```

### Capture

Create episode evidence automatically only from mechanically known task/work-unit state:
- objectives/acceptance criteria;
- host-observed worker results;
- deterministic test results;
- user-attributed decisions;
- validation reports;
- procedure/capability references;
- sanitized artifacts/evidence.

A model may summarize those fields but cannot create missing provenance.

Capture meaningful failures and retries as well as successes.

### Consolidation

Do **not** invoke expensive reflective extraction after every chat turn.

Trigger consolidation when materially useful, for example:
- explicit user correction;
- explicit acceptance of a reusable workflow;
- validated task completion with a novel gotcha;
- repeated similar failure/success episodes;
- repeated procedure reuse;
- conflicting/superseding environment state;
- Chairman identifies a lesson likely to matter again.

Initial recurrence/materiality thresholds must be calibrated from Vres replay data; do not invent a universal magic threshold.

### Hindsight / failed trajectories

Failed work is valuable but dangerous.

A failed trajectory:
- may become a negative lesson/gotcha;
- may identify an achieved subgoal through hindsight;
- must never automatically become a positive procedure/demo;
- any salvaged positive lesson must be independently verified against the achieved outcome.

Preserve failure classification so future agents know what not to imitate.

## Memory trust and authority

Every reusable memory carries a trust/source class.

Suggested classes:
- user_authoritative;
- validated_runtime;
- trusted_project_source;
- model_inferred_from_validated_evidence;
- external_untrusted_observation.

External/untrusted content cannot:
- establish approval;
- establish a company rule;
- modify agent/system instructions;
- become a preferred procedure;
- grant permissions;
- weaken validation;
- create credentials;
- cross project/user scope.

Model-derived memories begin below canonical authority.

Promotion ladder:

```text
episode/evidence
 -> proposed/observed project lesson
 -> validated project lesson
 -> capability/domain reusable lesson
 -> company canonical rule/procedure
```

Promotion upward requires stronger evidence and existing scope authority.

## Temporal/conflict model

Memory must be time-aware.

Use/extend existing:
- valid_from;
- valid_to;
- last_verified_at;
- review_after;
- superseded/challenged states;
- relations.

Requirements:
- current-state queries suppress superseded facts;
- historical questions can still retrieve old facts;
- conflicting observations can coexist until resolved;
- contradictions are surfaced, never silently averaged;
- newer does not automatically mean truer;
- old evidence is retained when needed for history/provenance.

A “forget”/retire operation should normally control **use**, not erase history.

Explicit source deletion/revocation must:
1. identify derived memories through provenance relations;
2. invalidate/rebuild affected derived memories and embeddings;
3. prevent revoked evidence from influencing new contexts;
4. require active task/context refresh when contaminated memory may already be loaded.

## Retrieval architecture

Do not build one giant vector search.

Use staged retrieval:

1. determine current project/task/capability/domain/scope and temporal intent;
2. apply hard scope/authority/security filters;
3. retrieve current decisions/rules;
4. retrieve matching accepted procedures;
5. retrieve semantic lessons/gotchas/premise warnings;
6. retrieve a small set of relevant episodes when specific examples add value;
7. detect conflicts/staleness/premise mismatch;
8. use bounded raw-evidence/archive search when structured memory has insufficient coverage;
9. compose one compact experience pack.

Hybrid signals should include where available:
- exact/structured filters;
- lexical search;
- embedding similarity;
- relation/graph links;
- temporal validity/recency;
- applicability/task-family/capability match;
- evidence/authority status;
- diversity/non-duplication.

Do not turn a retrieval score into a probability of truth.

### Experience pack

Workers receive only high-signal memory, e.g.:

```text
Current project decisions
Applicable validated lessons
Accepted procedures
Relevant gotchas / failed approaches
1-3 specific precedent episodes
Conflicts / stale assumptions
Evidence keys for drill-down
```

Every injected memory must retain:
- memory key;
- scope;
- authority/status;
- why it was retrieved;
- source/evidence references.

Use progressive disclosure: the agent can retrieve deeper evidence only when needed.

## Premise awareness

Before reusing a prior workflow, check whether its premises match the current environment.

Examples:
- framework/version differs;
- Windows vs Linux;
- database/provider differs;
- legacy vs fresh project;
- permission/tool availability differs;
- prior lesson was project-specific.

If premises materially conflict, the memory becomes a warning/example, not an instruction.

This is a first-class acceptance area, not a best-effort prompt hint.

## Agent/capability learning

Do not create per-model “personal memory”.

Experience attaches primarily to:
- project;
- domain;
- capability;
- procedure;
- technology/environment;
- task family.

A future Sonnet/Opus/Fable/other governed worker receives relevant proven experience for the capability it is executing.

Capability proof remains grounded in completed validated work.

Do not create an opaque “expert score”. Expose evidence such as:
- validated tasks;
- task families;
- recency;
- relevant procedure/lesson keys;
- known failure/gotcha history.

## Procedure learning

Keep the existing accepted-procedure system as procedural memory.

Enhance it by linking:
- episodes that motivated/used the procedure;
- corrections/rejected alternatives;
- retrieved lessons;
- validation outcomes;
- measured replay evidence.

User acceptance remains the baseline authority.

Automatic procedure replacement remains limited to the existing bounded, replay-attested path. General natural-language self-rewrite stays prohibited.

## Security: memory is privileged context

Add a dedicated memory-security boundary.

At write time:
- secret/sensitive-content guard;
- prompt-injection/memory-poisoning classification;
- source trust label;
- scope enforcement;
- payload/source digest;
- deterministic schema validation;
- no external text interpreted as policy instructions;
- quarantine suspicious candidate memories.

At read time:
- scope/permission filters before semantic retrieval;
- trust-aware retrieval;
- no cross-project/company leakage;
- treat retrieved external-derived content as data, not instruction;
- output/tool guardrails remain active;
- log memory retrieval identifiers for incident analysis.

Add adversarial cases based on OWASP ASI06 / MITRE context poisoning / current memory-poisoning literature.

## Cost and consolidation discipline

Avoid “reflect on everything”.

Use:
- deterministic snapshots;
- recurrence/materiality triggers;
- deduplication;
- compact abstractions with evidence links;
- bounded retrieval;
- lazy/raw evidence drill-down;
- optional embeddings rather than embedding as the only index.

Track construction cost, retrieval latency and tokens.

Memory that improves accuracy but makes every task dramatically slower is not automatically better.

## Evaluation program

### A. Write/consolidation quality

Measure:
- source-support precision;
- omission;
- unsupported additions/hallucinations;
- corruption of prior memory;
- deduplication;
- conflict recognition;
- temporal update correctness;
- secret/injection persistence rate.

Adopt HaluMem/TrustMem-style operation-level tests, not final-QA-only tests.

### B. Retrieval quality

Measure:
- Recall@k / Precision@k on known relevant memories;
- relevant evidence coverage;
- irrelevant-memory rate;
- duplicate-memory rate;
- stale-memory suppression;
- contradiction retrieval;
- premise-awareness accuracy;
- abstention when no useful precedent exists;
- retrieval latency;
- context-token cost.

### C. Agent outcome

On the same held-out task set compare:
- memory disabled;
- raw archive/refinding only;
- structured memory only;
- hybrid memory.

Measure:
- task success/criterion pass;
- retries/rework;
- tool/API call count;
- token/runtime cost;
- validation failures;
- harmful/negative transfer;
- unnecessary use of prior solutions.

### D. Streaming learning

Run tasks sequentially and evaluate:
- forward transfer;
- retained competence;
- new gotcha acquisition;
- stale knowledge update;
- selective forgetting;
- negative transfer;
- learning curve over time.

Use Evo-Memory / MemoryAgentBench style streaming protocols.

### E. Vres-specific experienced-colleague benchmark

Create a sanitized deterministic Vres corpus modeled on LongMemEval-V2:
- static project/environment state;
- dynamic state changes;
- recurring workflows;
- project gotchas;
- false premises;
- successful and failed tranches;
- user corrections/decisions;
- procedure reuse;
- cross-project scope traps.

The benchmark must include distractor/noisy history and exact expected evidence keys.

### F. Security/red-team suite

At minimum:
- malicious project document attempts to create a durable instruction;
- successful-looking poisoned trajectory;
- memory prompt injection after context reset;
- cross-project memory exfiltration;
- external observation trying to become company rule;
- poisoned procedure candidate;
- secret-bearing episode;
- stale revoked source still retrievable;
- embedding/lexical poisoning;
- trusted/untrusted conflict;
- second Windows-user isolation where relevant.

## Acceptance metrics

Do not choose universal numeric thresholds from intuition.

First establish:
1. memoryless baseline;
2. raw-archive/refinding baseline;
3. current Vres knowledge/procedure baseline;
4. candidate hybrid memory.

Freeze thresholds only after representative replay.

The final acceptance contract must require:
- no security/scope/provenance regression;
- measurable net outcome benefit on relevant tasks;
- no material negative-transfer increase;
- bounded latency/token overhead;
- improved or non-inferior memory-operation faithfulness;
- exact reproducible evidence.

## Implementation tranches

### E1 — contracts + episode ledger
- versioned experience policy/schema;
- immutable bounded episode snapshots from task/work-unit evidence;
- no raw chain-of-thought;
- source/trust/scope/digests;
- relations to existing decisions/procedures/capabilities/validation.

### E2 — transition verifier + safe consolidation
- candidate lesson consolidation;
- source-support checks;
- before/after transition digests;
- dedupe/conflict detection;
- recurrence/materiality triggers;
- quarantine path;
- failures/gotchas/hindsight rules.

### E3 — unified experience retrieval
- multi-store retrieval over existing decisions/knowledge/procedures + episodes;
- structured/lexical/optional semantic/graph/time signals;
- experience-pack budget;
- premise/conflict/staleness output;
- bounded raw archive search fallback.

### E4 — temporal lifecycle + revocation
- current vs historical use;
- supersession/challenge;
- review-after/refresh;
- selective “use” forgetting;
- provenance-driven invalidation after source revocation;
- embedding/retrieval rebuild;
- contaminated-session refresh contract.

### E5 — capability/procedure experience integration
- capability-centric experience retrieval;
- procedure/episode/feedback links;
- validated success/failure history;
- no opaque self-certified expert score;
- no automatic agent prompt rewriting.

### E6 — observability + experience utility evidence
- retrieval observations;
- cited/used memory;
- outcome/validation joins;
- no causal-credit overclaim;
- baseline/candidate retrieval-policy replay.

### E7 — benchmark + security ladder
- Vres experienced-colleague benchmark;
- operation-level memory hallucination tests;
- streaming tests;
- negative-transfer tests;
- memory poisoning/red-team tests;
- scale/latency/token tests.

### E8 — Chairman integration and protected acceptance
- Chairman automatically retrieves the smallest relevant experience pack;
- user never runs memory commands;
- user authority only when promotion/action requires it;
- protected Fable/high review for governance/security and company promotion surfaces;
- docs/handoff;
- exact-head CI/post-merge CI.

### E9 — integrated physical live acceptance (#169)
From the actual Windows/Visual Studio workflow prove:
- task A produces a validated project lesson;
- later task B automatically retrieves it without user reminder;
- the worker cites/uses the right lesson;
- a conflicting/stale lesson is surfaced rather than silently followed;
- a failed approach becomes a gotcha, not a positive recipe;
- a user correction supersedes the prior rule with provenance;
- a reusable accepted procedure is discovered on a later task;
- another project does not inherit project-only experience;
- company-canonical memory is reusable only under its authority contract;
- poisoned/untrusted external content cannot persist as privileged memory;
- a revoked source stops influencing later work;
- model/provider replacement still uses the same Vres institutional memory.

## Tests required per tranche

Every implementation tranche requires:
- targeted unit tests;
- PostgreSQL integration;
- concurrency/idempotency/rollback where it writes durable state;
- malformed/corrupt payload fail-closed;
- project/scope isolation;
- provenance/source-digest checks;
- secret/injection negative proofs;
- retrieval determinism where deterministic;
- explicit test for no raw chain-of-thought persistence;
- exact installed-runtime smoke if MCP/packaging changes;
- protected Fable/high for security/governance/procedure-promotion changes.

## Out of scope for first release

- fine-tuning foundation-model weights from Vres history;
- silent autonomous changes to Chairman/agent prompts;
- automatic company-wide rule promotion;
- machine/company-wide sharing of private project experience;
- storing hidden chain-of-thought;
- claiming causal skill improvement from retrieval correlation alone;
- replacing the raw source/evidence archive with summaries;
- unlimited background reflection loops;
- arbitrary retention of secret/private raw conversations.

## Design validation completed before implementation

This plan has been checked against:

1. **Current Vres primitives:** reuses decisions, knowledge, procedures, feedback/runs/replay, capabilities/proofs, relations, sources/artifacts and validation instead of introducing a second authority system.
2. **Memory architecture:** separates execution state, episodic evidence, semantic lessons, procedures and raw archive.
3. **State-of-the-art retrieval:** supports compact abstractions plus specific evidence and bounded raw refinding rather than vector-only RAG.
4. **Temporal correctness:** explicit update/supersession/history/premise model.
5. **Failure learning:** failed/near-miss trajectories are useful evidence but cannot automatically become positive demonstrations.
6. **Memory transition reliability:** source-bound transactional verification is required.
7. **Security:** poisoning, indirect injection, cross-scope leakage, secret persistence and retrieval exfiltration are first-class.
8. **Cost:** recurrence/materiality consolidation and context budgets prevent “reflect on everything”.
9. **Evaluation:** write quality, retrieval quality, downstream outcome, streaming learning, negative transfer and security all have separate tests.
10. **Governance:** no private self-modification; authority promotion stays explicit; protected Fable/high remains required for consequential promotion/governance.
11. **Architecture:** incremental tranches with one truth owner and no giant parallel memory subsystem.
12. **Live evidence:** #169 receives concrete integrated acceptance criteria.

Protected Fable/high remains a mandatory implementation/merge gate for this governance/security-sensitive foundation. This research/design validation does not pretend to substitute host-observed protected validation.


## Red-team hardening additions

### Memory flooding / amplification control

The system must defend not only against one poisoned write, but against repeated semantically varied writes intended to dominate retrieval.

Controls:
- per-source/per-task write budgets;
- duplicate and near-duplicate suppression;
- source-diversity-aware retrieval;
- no “importance” boost merely because one memory is repeatedly retrieved;
- recurrence cannot increase authority without independent evidence;
- suspicious burst/flood patterns quarantine rather than consolidate;
- retrieved-memory frequency is utility evidence at most, never truth evidence.

### Participated vs observed experience

Every episode/lesson candidate must distinguish:
- **participated** — Vres/worker actually executed or directly observed the governed task;
- **observed** — information came from an external source, imported history, document, website, tool output or another system.

Observed external material begins at lower trust and cannot be promoted simply because it resembles a successful local episode.

### Retrieval-triggered reconsolidation

Retrieving a memory may reveal that it is stale, contradicted or incomplete.

Retrieval may therefore create:
- challenge candidate;
- reverification request;
- consolidation candidate;
- supersession proposal.

Retrieval must **not** silently rewrite the memory it just consumed.

### Held-out evaluation discipline

Memory policy tuning must not train/evaluate on the same experience stream.

Maintain:
- frozen development/replay corpus;
- held-out acceptance corpus;
- adversarial security corpus;
- temporal/update cases that appear only in held-out evaluation.

Any model judge used for non-deterministic criteria must be calibrated against deterministic/human-labelled samples and cannot be the sole authority for protected acceptance.

Benchmark examples, expected evidence keys and scoring rules are versioned and hashed so retrieval-policy changes cannot silently change the test.

