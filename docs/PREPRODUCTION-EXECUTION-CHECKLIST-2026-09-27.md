# Vres Preproduction Execution Checklist

Date: 2026-10-02  
Repository: `vosser24/Vres-OS`  
Authoritative main after #176 E4: `a0a2769b99f4893733568194c0aa68e78e73aeab`

## Governing rule

This checklist is the canonical execution order for the remaining Vres preproduction program.

**Hard invariant: do not start implementation of the next issue until the previous checklist item is fully DONE.**

DONE means, where applicable:

- implementation complete;
- targeted/unit/integration/security tests complete;
- protected Fable/high validation complete when required;
- required Chairman/F-15 or other host smoke complete;
- docs/handoff current;
- PR exact-head CI green;
- PR merged;
- authoritative `main` updated;
- post-merge `main` CI green;
- issue closed with deferred physical criteria explicitly carried forward;
- no unresolved critical blocker from that issue remains.

Planning/research for later items may be preserved in Git/issues, but **implementation does not begin early**.

If an issue changes a reviewed branch/base, its exact-head validation/CI must be rerun before merge.

## Sequential checklist

### 1. #163 — Credential Broker
Status: **DONE — merged, post-merge CI green, issue closed**

Accepted implementation:
- PR #173
- branch: `issue-163-credential-broker`
- validated head: `4baf4fadbbd402a0dd523837924e6436f74f27d1`
- exact-head CI: run **#407** / `36158185554` — SUCCESS
- protected validation: `VAL-52be75fc46484345` — PASS
- host-observed protected validator: `claude-fable-5-1` under pinned Fable/high
- required live regression family: **F-05 PASS, F-06 PASS, F-15 PASS**
- merge commit: `7f9961b5980f1a229cece4902f9e1d709e397e22`
- post-merge main CI: run **#438** / `36420420225` — SUCCESS
- post-merge suite: **1056 passed, 1 skipped**
- installed-runtime smoke: PASS
- local release gate: `PASSED_WITH_EXPLICIT_LIVE_GATES`
- issue #163: **closed / completed** on 2026-09-28

Acceptance completed:
- [x] protected `vres-os:validator` Fable/high PASS on exact candidate;
- [x] required lifecycle live regression family F-05 / F-06 / F-15;
- [x] exact-head CI green;
- [x] merge PR #173;
- [x] post-merge main CI green;
- [x] close #163 while explicitly preserving physical Windows criteria in #169.

Physical Windows/customer-environment criteria remain intentionally deferred to #169 and were **not** claimed by #163:
- real Windows Credential Locker under User A;
- Project A/B reuse without re-entry and unbound Project C denial;
- real child-only environment delivery with parent environment remaining clean;
- actual Claude transcript/debug interception behavior;
- second Windows-user isolation;
- uninstall/reinstall preserving native Claude/Codex authentication.

**#176 remains the only allowed implementation issue; within #176, E1 and E2 are DONE and E3 is the next allowed tranche.**

---

### 2. #174 — Engineering Architecture Governance
Status: **DONE — protected exact-head PASS, merged, post-merge CI green, issue closed**

Accepted implementation:
- PR #175
- branch: `issue-174-engineering-architecture-governance`
- original held head: `9756b44d4ae953db327b10072e70003e51df9404`
- integrated/validated head: `7ded3c16e5e85f5715fb052f403907eec3750628`
- authoritative integration base: `7f9961b5980f1a229cece4902f9e1d709e397e22`
- exact-head CI: run **#439** / `36455460478` — SUCCESS
- final protected validation: `VAL-aa05bb6018e941cc` — PASS
- host-observed protected validator: `claude-fable-5-1` under pinned Fable/high
- merge commit / new authoritative main: `11591b72b3d396a370e315313925e19b8bcb45ec`
- post-merge main CI: run **#440** / `36530581547` — SUCCESS
- post-merge PostgreSQL-backed suite: PASS
- post-merge installed-runtime smoke: PASS
- post-merge local release gate: PASS
- post-merge evidence artifact: `11016787086`
- artifact digest: `sha256:59e506706a168648057860d8e683816940973a512440c09c253228296d5abedf`
- issue #174: **closed / completed** on 2026-09-29

Acceptance completed:
- [x] history-preserving integration of current main;
- [x] integration/security audit with #163 behavior preserved;
- [x] deterministic architecture audit excludes Vres-owned `.vres`, including `.vres/local-secrets`;
- [x] C7 local-terminal credential authority carve-out locked by regression coverage;
- [x] targeted architecture/#163 integration tests green;
- [x] isolated full PostgreSQL-backed local suite green;
- [x] release gate green;
- [x] exact-head CI #439 green;
- [x] canonical protected `vres-os:validator` Fable/high PASS on exact head;
- [x] merge PR #175 with expected-head protection;
- [x] post-merge main CI #440 green;
- [x] close #174.

Phase 5 initially exposed protected-validation sequencing mistakes, not a #174 code defect. Durable VATT evidence confirmed the existing #42 contract remains correct: freeze/checkpoint before `validation_prepare`, do not mutate task state while validation is in flight, and use `task_reply_gate(advances_state=false)` with `mode=validation_in_flight` for interim status replies. The clean Phase 5B run followed that protocol and produced the authoritative host-attested PASS above.

**#176 remains the only allowed implementation issue; within #176, E1 and E2 are DONE and E3 is the next allowed tranche.**

---

### 3. #164 — Secret-safe onboarding
Status: **DONE — protected exact-head PASS, merged, post-merge CI green, issue closed**

Accepted implementation:
- PR #177
- branch: `issue-164-secret-safe-onboarding`
- validated head: `eddfa35d5418e23d6bac8792df0a6d1877d880a8`
- authoritative base: `11591b72b3d396a370e315313925e19b8bcb45ec`
- governed engineering final: `ORCHFINAL-20260929-9bf6f3cc85` — `decision_ready=true`
- local isolated PostgreSQL suite: **1164 passed / 3 skipped / 0 failed / 0 errors**
- exact-head CI: run **#441** / `36542621233` — SUCCESS
- exact-head evidence artifact: `11021550195`
- exact-head artifact digest: `sha256:0c9409eb517bf70a99949bf45d6a768fabe2a72b1ed3c1ba34f83f99009bf1c6`
- final protected validation: `VAL-f8d685ab3575430c` — PASS
- host-observed protected validator: `claude-fable-5-1`
- merge commit / authoritative main: `fe31e30e593a44b8b5ab565fa0db859bbefec0c6`
- post-merge main CI: run **#442** / `36544341349` — SUCCESS
- post-merge evidence artifact: `11021203984`
- post-merge artifact digest: `sha256:8ab24e44232efa860f2d05e4aec8c2014704dc963920fbe98207326051a7fdc6`
- issue #164: **closed / completed** on 2026-09-29

Acceptance completed:
- [x] deterministic secret-bearing path preflight before ordinary hash/extraction;
- [x] explicit `sensitive_excluded`, `sensitive_sanitized`, `sensitive_review_required` dispositions;
- [x] canonical pre-model/pre-persistence sanitization for mixed useful documents;
- [x] fail-closed uncertain-sensitive handling with value-free review metadata;
- [x] sanitized content does not persist raw secret values or raw-file hashes;
- [x] Credential Broker authority preserved; no second vault / no auto-confirm-bind-save;
- [x] semantic embedding functionality preserved with trusted configured-model local-first acquisition;
- [x] project content cannot choose a model or authorize arbitrary network activity;
- [x] installed-wheel smoke green;
- [x] exact-head CI #441 green;
- [x] protected Fable/high PASS on exact candidate;
- [x] guarded merge of PR #177;
- [x] post-merge main CI #442 green;
- [x] close #164.

Physical/live criteria intentionally remain deferred:
- real first-run SentenceTransformer acquisition with the actual optional runtime;
- sanitized wizzard_9 legacy-project acceptance;
- target Windows/Visual Studio integrated proof.

Those belong to #169 / the applicable live embedding-runtime acceptance and were not falsely claimed by #164.

**#176 remains the only allowed implementation issue; within #176, E1 and E2 are DONE and E3 is the next allowed tranche.**

---

### 4. #176 — Experience Intelligence / Governed Agent Learning
Status: **ACTIVE — E1/E2/E3/E4 DONE; E5 capability/procedure experience integration NEXT**

Durable plan:
- issue #176;
- Git-history plan branch: `docs-176-experience-intelligence-plan-20260927`;
- plan commit: `34f45afa0fb8d5a6a90bef53dec58d9ecef1093d`;
- file: `docs/architecture/EXPERIENCE-INTELLIGENCE-PLAN-2026-09-27.md`.

Accepted E1 implementation:
- PR #179;
- branch: `issue-176-e1-experience-ledger`;
- exact protected-reviewed head: `bc03707c9cef77967cc1abd2ffe0733d4393b42c`;
- E1 acceptance task: `TASK-20260929-7e344a1e68`;
- freeze checkpoint: `CP-20260929-7c91c106e4`;
- protected validation: `VAL-b7d08edab1c74e98` — PASS;
- host-observed protected validator/model: `vres-os:validator` / `claude-fable-5-1` under Fable/high;
- exact-head CI: run **#454** / `36557839748` — SUCCESS;
- exact-head PostgreSQL-backed suite: **1186 passed / 1 skipped**;
- exact-head installed-runtime smoke: PASS;
- exact-head release gate: `PASSED_WITH_EXPLICIT_LIVE_GATES`;
- exact-head evidence artifact: `11029410541`;
- exact-head artifact digest: `sha256:8d74efb2fd4cf9e0b72e639448c50c7b447eb3576ceac4b151717b26d26b8ac8`;
- merge commit / authoritative main: `407c4a323f4f65c8f28c422789508bb7ce128682`;
- post-merge main CI: run **#455** / `36560731741` — SUCCESS;
- post-merge PostgreSQL-backed suite: **1186 passed / 1 skipped**;
- post-merge installed-runtime smoke: PASS;
- post-merge release gate: `PASSED_WITH_EXPLICIT_LIVE_GATES`;
- post-merge evidence artifact: `11028544812`;
- post-merge artifact digest: `sha256:047cbd0fa0ed34c38ab14e98f44fa07f0a7ca22d4039ff265a07340405f841a0`.

E1 acceptance completed:
- [x] E1 contract frozen before implementation;
- [x] immutable bounded episode ledger and versioned policy;
- [x] existing truth owners reused instead of creating a second generic memory authority;
- [x] #164 secret-safe sanitization/fail-closed behavior preserved;
- [x] hidden/private reasoning persistence rejected;
- [x] project/scope, provenance/digest, idempotency/concurrency and rollback evidence;
- [x] work-unit provenance narrowed to directly attributable evidence;
- [x] failure trajectories remain failures;
- [x] exact-head CI #454 green;
- [x] canonical protected `vres-os:validator` Fable/high PASS on the exact candidate;
- [x] guarded merge of PR #179 with expected-head protection;
- [x] post-merge main CI #455 green;
- [x] durable E1 closure evidence posted to #176 and #179.

Accepted E2 implementation:
- PR #180;
- branch: `issue-176-e2-consolidation`;
- final protected-reviewed head: `c1dccfa800381b1f5b01fd054cb3819720600e2a`;
- E2 task: `TASK-20260929-9fdfbe76eb`;
- historical failed protected request: `VAL-84afc8fa56a245bf` — FAILED and preserved;
- final protected validation: `VAL-58bb131a10b54abd` — PASS;
- host-observed protected validator/model: `vres-os:validator` / `claude-fable-5-1`;
- exact-head CI: run **#461** / `36585887143` — SUCCESS;
- exact-head PostgreSQL integration: PASS;
- exact-head installed-runtime smoke: PASS;
- exact-head release gate: PASS;
- exact-head evidence artifact: `11042340684`;
- exact-head artifact digest: `sha256:afb432d024f1647586b0d0d2e239c34fda2845344f1549ab973ce8996d82eaa8`;
- merge commit / authoritative main: `74c6445228a922db2622806f27e3c49a6c3454a7`;
- post-merge main CI: run **#462** / `36589408835` — SUCCESS;
- post-merge PostgreSQL integration: PASS;
- post-merge installed-runtime smoke: PASS;
- post-merge release gate: PASS;
- post-merge evidence artifact: `11042962873`;
- post-merge artifact digest: `sha256:082fdc00743b212dd7f3fb30c9de451b943274e755d8f6b81bc4624a3e0a1ab6`.

E2 acceptance completed:
- [x] transition-verifier + safe-consolidation contract frozen before implementation;
- [x] existing `knowledge_items`, relations and E1 episodes retained as truth owners;
- [x] append-only immutable `experience_transitions` audit added without becoming a retrieval store;
- [x] literal source support, pointer/quote checks and payload/source digest integrity enforced;
- [x] failure integrity preserved; failed/cancelled evidence cannot become positive lessons;
- [x] recurrence acceptance disabled until later replay-calibrated policy;
- [x] participation/trust quarantine remains independent from unrelated quarantine reasons;
- [x] accepted output is always proposed + project-local with no automatic authority promotion;
- [x] dedupe and opposite-polarity conflict semantics preserved;
- [x] atomicity, rollback, idempotency and concurrency evidence;
- [x] #163/#164/#174/E1 boundaries preserved;
- [x] exact-head CI #461 green;
- [x] canonical protected Fable/high PASS on the final candidate;
- [x] guarded merge of PR #180 with expected-head protection;
- [x] post-merge main CI #462 green;
- [x] durable E2 closure evidence posted to issue #176 and PR #180.

Current E3 checkpoint (local Windows worktree; not yet pushed):
- worktree: `C:\Projects\Vres-Issue-176-E3-20260929`;
- branch: `issue-176-e3-unified-experience-retrieval`;
- E3 task: `TASK-20260929-9c9d52b7e5`;
- authoritative base: `74c6445228a922db2622806f27e3c49a6c3454a7`;
- frozen E3 contract commit: `c03b2c269c4118d47b39c4c3236fc106412b4d3b` (local only);
- Chunk 1 implementation commit: `ff025a8a738062c3453d34cb045c5abf005db7f3` (local only);
- remote E3 branch: **not created / not pushed yet**;
- routing for Chunk 1: one Sonnet worker executing routed role `cto`, routine assurance, no work graph;
- Chunk 1 files: new `src/vres_os/experience_retrieval.py`, `tests/test_experience_retrieval.py`, `tests/integration/test_experience_retrieval_journey.py`;
- targeted unit/regression rerun: **97 passed** (39 new + 58 regression);
- fresh isolated PostgreSQL E3 journey: **14 passed**;
- existing E1/E2 integration journeys in the same fresh DB: **19 passed**;
- repository-critical lint for the changed surface: PASS;
- `git diff --check`: PASS;
- no migration added;
- no-write proof: 11-table row-count + md5-digest snapshot unchanged before/after retrieval, and attempted INSERT/UPDATE on the retrieval connection fail under read-only transaction semantics;
- current bounded defect: E3 reused E2's broad write-time `_INJECTION` regex at read time, so benign words such as `policy` / `approved` may suppress legitimate memory. This must be hardened before Chunk 2;
- procedure retrieval currently uses one scoped read query because `ProcedureService.find_matches` opens its own connection and lacks the required E3 scope gate; review for semantic duplication during hardening;
- remaining E3 features intentionally deferred to later chunks: challenged/conflict surfacing, premise evaluation, semantic/embedding signal, raw-chunk fallback, MCP surface and Chairman integration.

**Immediate E3 action: finish the already-dispatched Chunk 1 hardening prompt, review its exact test/commit report, and do not begin Chunk 2 until the read-time injection/trust behavior is closed and the 1–20 Chunk 1 test matrix is accounted for.**

Implementation tranches:
- [x] E1 contracts + episode ledger;
- [x] E2 transition verifier + safe consolidation;
- [x] E3 unified experience retrieval;
- [x] E4 temporal lifecycle + revocation;
- [ ] E5 capability/procedure experience integration;
- [ ] E6 observability + experience utility evidence;
- [ ] E7 benchmark + security ladder;
- [ ] E8 Chairman integration + protected acceptance;
- [ ] carry E9 physical acceptance into #169;
- [ ] protected Fable/high as required for each consequential governance/security tranche;
- [ ] final #176 exact-head CI/merge/post-merge sequence after the remaining tranches;
- [ ] close #176 only after all required E2–E8 acceptance and E9 carry-forward are complete.

**E3 — unified experience retrieval is now the only allowed implementation tranche inside #176. Do not begin E4 until E3 is bounded, implemented, tested and evidenced.**

**Do not start #165 implementation until #176 is DONE.**
---

### 5. #165 — Chairman model policy
Status: **NOT STARTED**

- [ ] build;
- [ ] targeted/model-policy tests;
- [ ] protected validation;
- [ ] docs/handoff;
- [ ] exact-head CI;
- [ ] merge;
- [ ] post-merge main CI;
- [ ] close #165.

**Do not start #166 until #165 is DONE.**

---

### 6. #166
Status: **NOT STARTED**

- [ ] read the full issue before work;
- [ ] implement only #166 scope;
- [ ] required tests/validation;
- [ ] docs/handoff;
- [ ] exact-head CI;
- [ ] merge;
- [ ] post-merge main CI;
- [ ] close #166.

**Do not start #167 until #166 is DONE.**

---

### 7. #167
Status: **NOT STARTED**

- [ ] read the full issue before work;
- [ ] implement only #167 scope;
- [ ] required tests/validation;
- [ ] docs/handoff;
- [ ] exact-head CI;
- [ ] merge;
- [ ] post-merge main CI;
- [ ] close #167.

**Do not start #168 until #167 is DONE.**

---

### 8. #168 — Project adoption and canonical Claude scaffold
Status: **NOT STARTED**

Must consume merged:
- #163 Credential Broker;
- #164 secret-safe onboarding;
- #174 Engineering Architecture Governance;
- #176 Experience Intelligence.

Required:
- [ ] full fresh/legacy/adoption state machine;
- [ ] architecture audit + alignment plan;
- [ ] exact audit/plan digests;
- [ ] mandatory protected Fable/high validation before architecture-changing adoption activation;
- [ ] KEEP/DROP and canonical scaffold activation;
- [ ] credential/data-source linking;
- [ ] Experience Intelligence integration;
- [ ] interruption/rollback;
- [ ] tests/validation/docs;
- [ ] exact-head CI;
- [ ] merge;
- [ ] post-merge main CI;
- [ ] close #168.

**Do not start #169 live acceptance until #168 is DONE and all build prerequisites are merged.**

---

### 9. #169 — Integrated Windows / Visual Studio live acceptance
Status: **NOT STARTED**

Run only after all implementation tranches are merged and main is green.

- [ ] dirty PRISM/current-user Claude setup;
- [ ] fresh Vres install over established Claude;
- [ ] global adoption acceptance;
- [ ] real legacy-project adoption;
- [ ] architecture-governance live proof;
- [ ] Credential Broker live proof;
- [ ] secret-safe onboarding live proof;
- [ ] Experience Intelligence live proof;
- [ ] second-user/project isolation;
- [ ] interruption/recovery;
- [ ] host-observed model/validator evidence;
- [ ] final integrated acceptance verdict;
- [ ] close #169 only with no critical unresolved defect.

Any defect creates a bounded implementation issue; fix/merge it before resuming only the impacted live-acceptance surface.

**Do not start #170 until #169 is DONE.**

---

### 10. #170 — Production Readiness / Go-Live
Status: **NOT STARTED**

- [ ] exact release artifact + hashes/manifest;
- [ ] target Windows production install;
- [ ] PostgreSQL least privilege/auth/provenance review;
- [ ] credential/security/storage/logging review;
- [ ] backup/restore proof;
- [ ] update/rollback/interrupted-update recovery;
- [ ] adoption rollback/recovery;
- [ ] monitoring/health/operator escalation;
- [ ] capability inventory;
- [ ] staged real-world pilot;
- [ ] final go-live gate;
- [ ] post-release evidence/handoff;
- [ ] close #170 only when production-ready evidence is complete.

## Session-start rule

At the beginning of every future implementation session:

1. read this checklist;
2. verify authoritative `origin/main`;
3. identify the first item not marked DONE;
4. work only that item;
5. do not start implementation of any later item;
6. update this checklist/handoff when the current issue changes state.

## Current next action

**#176 E5 — capability/procedure experience integration is the first unfinished implementation boundary. E4 is accepted, protected-reviewed, merged, and green on authoritative main `a0a2769b99f4893733568194c0aa68e78e73aeab`. Start E5 only from that exact main after reading the frozen Experience Intelligence plan and section 13 below. E5 scope is capability-centric experience retrieval; procedure/episode/feedback links; validated success/failure history; no opaque self-certified expert score; and no automatic agent prompt rewriting. Freeze a bounded E5 contract before implementation and preserve the targeted-test/full-suite/release-gate/protected-validation cadence.**

**Execution cadence from this boundary:** use targeted tests for bounded corrections; do not rerun the full suite/release gate without changed candidate bytes or a concrete evidence gap. ChatGPT becomes the primary architecture/code/repository/PR/CI/handoff coordinator. Local Claude Code is reserved for Windows/local PostgreSQL/pgvector/installed-runtime/Visual Studio/live acceptance and machine-specific corrections. Never edit the same branch concurrently: transfer ownership only at an exact clean/pushed SHA.
---

### 11. Post-#170 queued backlog — Organizational Architecture & Specialist Intelligence
Status: **QUEUED — DO NOT INTERRUPT CURRENT PIPELINE**

Sequencing rule: new product requests discovered during the active frozen program are appended after #170 unless they are a defect/blocker in the current tranche.

After #170, perform a forensic restoration/audit of the original Vres Agent Board design against the implemented organization. Do **not** infer the target board from the current agent files alone.

Required backlog scope:
- recover the original project-conversation/design artifacts for the complete department -> Director -> role -> specialist hierarchy;
- specifically recover the original full Technology/IT/software organization, including software design/architecture, product-owner/product roles, database, backend/frontend, security, DevOps/platform, QA/reliability and other originally defined specialists;
- compare original design vs current shipped executive roster vs dynamic project-agent/capability model;
- identify intentionally consolidated roles vs accidentally lost roles;
- formalize department_key -> role_key -> capability_key hierarchy;
- keep organizational role identity distinct from execution tier and physical model;
- surface human-facing specialist names (e.g. Database Engineer) instead of generic `vres-os:sonnet-expert` / `vres-os:opus-expert` as the primary worker identity;
- add role/department/capability usage and performance attribution using only mechanically supported metrics: run counts, host-observed model, task family, validated outcome, rework/reroute/repair counts, runtime/tokens/cache/cost where trustworthy;
- do not fabricate quality scores or auto-promote/demote roles/models from telemetry;
- define when a recurring project specialist may be proposed for stable product-role graduation under explicit governance.

This backlog item is **after #170** and must not alter #176/#165/#166/#167/#168/#169/#170 sequencing.


---

### 12. 2026-10-02 authoritative continuation override — #176 E4 pre-validation boundary
Status: **ACTIVE — E4 PRODUCT DEVELOPMENT FROZEN; EXACT-HEAD CI / PROTECTED ACCEPTANCE NEXT**

This section supersedes the older E3/E4 status text above for current execution state. Historical evidence remains valid and must not be deleted.

Current product/repository boundary:
- authoritative remote `main`: `ddb0719d130fd45b12b6bdc9e1682378ace7ae64` (E3 merge);
- E4 branch: `issue-176-e4-temporal-lifecycle-revocation`;
- remote E4 branch head verified by ChatGPT on 2026-10-02: `ce9067ab36716cb1f729466db168d002e1029c93`;
- final E4 tree: `5cf813f19feb36e23f59dc6ddf632c38ac09e869`;
- E4 Vres task: `TASK-20260930-2c7198e394`;
- latest local Vres checkpoint: `CP-20261002-b2e09a2047`;
- frozen E4 base contract remains byte-identical to commit `a69b836fa3fbf6a97c00f830b05495c48c5af563`;
- dated E4 contract addendum authorizes migration 040 for protected context-refresh attestation;
- schema: 40 migrations, latest 040;
- MCP surface: 51 tools;
- remote PR: none at the ChatGPT handoff check.

Final local acceptance already completed on the candidate bytes:
- JSON-backed full suite: real `PYTEST_EXIT=0`; only the known three Windows symlink skips plus one pgvector-only skip;
- real-pgvector affected acceptance: company-support eligibility and affected vector-mode surfaces green; the known JSON-only `test_semantic_jsonb_path_and_hybrid_exclude_non_use` remains intentionally JSON-mode-specific and reproduces the same mismatch on the prior base when forced onto a pgvector DB;
- targeted ACK/public-adapter/split-role security suite: 72 passed;
- critical Ruff + `git diff --check`: green;
- local release gate: exit 0 / `PASSED_WITH_EXPLICIT_LIVE_GATES`; its DB skips are not PostgreSQL acceptance evidence.

Migration-040 closure owns two final security fixes:
- context-refresh ACK requires a protected attestation row that ordinary runtime cannot mint plus host `claudecode/toolUseId` correlation; missing host correlation fails closed;
- a company item whose only applicable support is revoked no longer re-enters current use through get/search/chunk-hybrid/JSON semantic/pgvector semantic/E3 structured/raw readers.

Residual risks are evidence for validator/live/production review, not automatic new development loops unless they violate a frozen MUST/NEVER:
- `toolUseId` host correlation was observed on Claude Code 2.1.286 and fails closed if absent;
- a same-user process with transcript access plus runtime DB credential could replay the current nonce once within its short TTL;
- runtime/writer credentials share the same OS credential store; single-role disposable DBs make role separation nominal;
- transitive company-support analysis remains limited;
- no fresh ACK latency re-measurement was required after the final closure.

Remaining E4 acceptance sequence:
- [ ] open/verify PR from exact E4 head;
- [ ] exact-head CI SUCCESS on `ce9067ab...`;
- [ ] capture CI run/id/steps/artifact/digest;
- [ ] one final material Vres freeze checkpoint after CI and before `validation_prepare`;
- [ ] exactly one protected `vres-os:validator` acceptance on the frozen exact candidate;
- [ ] guarded expected-head merge;
- [ ] post-merge push CI on the exact new main SHA;
- [ ] durable E4 task/issue evidence closure;
- [ ] only then begin E5.

Accelerated execution policy:
- targeted/unit/PostgreSQL tests for bounded corrections;
- full suite once per coherent final candidate, not after every small fix;
- local release gate once per coherent final candidate;
- protected validation once per frozen exact-head candidate;
- no automatic retry of protected validation;
- no duplicate expensive evidence unless candidate bytes changed or a specific gap exists.

Tool ownership / handoff rule:
- **ChatGPT primary:** architecture decisions, repo/code changes when working against remote GitHub state, PR/CI/merge, documentation/checklist/handoff maintenance, evidence audit and tranche sequencing;
- **Local Claude Code:** Windows-only/local machine execution, PostgreSQL/pgvector/installed-runtime proof, Credential Locker/Visual Studio/legacy-project/live acceptance, host-hook/session behavior, and bounded corrections that require the local environment;
- **single writer:** ChatGPT and Claude must never edit the same branch concurrently. Before switching writers, commit/push/verify an exact clean SHA. The receiving side must fetch/read back that exact SHA before editing.

Full remaining frozen pipeline after E4:
- E5 capability/procedure experience integration;
- E6 observability + experience utility evidence;
- E7 benchmark + security ladder;
- E8 Chairman integration + protected acceptance;
- E9 physical Experience Intelligence criteria carried into #169;
- #165 Chairman model policy;
- #166;
- #167;
- #168 project adoption + canonical Claude scaffold;
- #169 integrated Windows / Visual Studio live acceptance;
- #170 production readiness / go-live;
- post-#170 Organizational Architecture & Specialist Intelligence / full-team enhancement backlog.


---

### 13. 2026-10-02 authoritative continuation override — #176 E4 CLOSED / E5 NEXT
Status: **E4 DONE — E5 IS THE ONLY NEXT #176 IMPLEMENTATION TRANCHE**

This section supersedes section 12 and all older E3/E4 current-action text. Historical evidence remains historical and must not be rewritten.

#### E4 accepted repository boundary

- authoritative main before E4: `ddb0719d130fd45b12b6bdc9e1682378ace7ae64`;
- E4 branch: `issue-176-e4-temporal-lifecycle-revocation`;
- PR: **#182** — merged;
- exact protected-reviewed head: `553e9d1398073b4cf0a4a4b282b2f3f3ff86ec2b`;
- exact reviewed tree: `6eb856f2c075b2194ccabb59b4a6e906110e4a1d`;
- full E4 review scope: **65 files — 41 added / 24 modified / 0 deleted**;
- frozen E4 base contract commit: `a69b836fa3fbf6a97c00f830b05495c48c5af563`;
- migration-040 addendum retained;
- schema: 40 migrations, latest 040;
- MCP surface: 51 tools.

#### Exact-head CI

- Vres-OS CI: **#470**;
- run id: `37018126950`;
- event: `pull_request`;
- attempt: 1;
- exact workflow head: `553e9d1398073b4cf0a4a4b282b2f3f3ff86ec2b`;
- conclusion: **SUCCESS**;
- full PostgreSQL-backed suite: **2196 passed / 3 skipped**;
- installed-runtime smoke: **PASS**;
- release gate: `PASSED_WITH_EXPLICIT_LIVE_GATES`;
- release-gate unit/static suite: **1517 passed / 682 expected DB/live skips**;
- evidence artifact: `11231412578`;
- artifact name: `release-gate-evidence`;
- artifact digest: `sha256:764ac4524c32681f96cc4e550ddffb54c4d48eca16832340105d5391324c1d5c`.

CI discovered three acceptance-harness corrections after the earlier docs-complete candidate `ce9067ab...`. They changed only:
- `tests/test_control_preflight.py`;
- `tests/integration/test_validation_reply_guard_journey.py`.

No E4 product/runtime file changed in those corrections.

#### Protected validation

Historical protected lifecycle failure is preserved:
- checkpoint: `CP-20261002-ce4cd17ce2`;
- request: `VAL-72e66d088bec405a`;
- terminal status: **rejected**;
- no E4 candidate defect established.

Final protected acceptance:
- retry freeze checkpoint: `CP-20261002-836cb0cf41`;
- request: `VAL-4dbf9f69b1744e6b`;
- result: **PASS**;
- task validation status: **passed**;
- completed_at: `2026-10-02T18:46:55+03:00`;
- canonical validator: `vres-os:validator`;
- host-observed model: **`claude-fable-5-1`**;
- host agent id: `a757f62be54532130`;
- report: **14/14 checks passed**, no failed or `not_run` checks;
- all 65 reviewed artifact hashes matched the frozen candidate.

The successful retry used a current-turn freeze checkpoint so the reply gate correctly returned `validation_in_flight`. The validator was instructed to avoid background/nested work and to return its canonical JSON report before terminal stop.

#### Guarded merge and post-main acceptance

- expected-head merge guard: `553e9d1398073b4cf0a4a4b282b2f3f3ff86ec2b`;
- merge method: merge commit;
- new authoritative main / merge commit: **`a0a2769b99f4893733568194c0aa68e78e73aeab`**;
- post-merge Vres-OS CI: **#471**;
- run id: `37029621024`;
- event: **push**;
- attempt: 1;
- exact main head: `a0a2769b99f4893733568194c0aa68e78e73aeab`;
- conclusion: **SUCCESS**;
- full PostgreSQL-backed suite: **2196 passed / 3 skipped**;
- installed-runtime smoke: **PASS**;
- release gate: `PASSED_WITH_EXPLICIT_LIVE_GATES`;
- release-gate unit/static suite: **1517 passed / 682 expected DB/live skips**;
- release-gate git commit: `a0a2769b99f4893733568194c0aa68e78e73aeab`;
- dirty: false;
- evidence artifact: `11236608634`;
- artifact name: `release-gate-evidence`;
- artifact digest: `sha256:0da77dfb4357f4b6d1413702192365cc15c11c2d0aa0305fdac433ecc6690758`.

#### E4 shipped boundary

E4 now provides:
- append-only temporal lifecycle audit;
- retire/reinstate/challenge/supersession/refresh controls;
- provenance-driven source revocation;
- bounded multi-source survival analysis;
- JSON + pgvector embedding invalidation/rebuild fencing;
- lifecycle-aware E3 retrieval under `176.e4.v1`;
- contaminated-session enforcement;
- protected context-refresh attestation through migration 040;
- revoked-only company-support exclusion across current reader paths;
- MCP surfaces `source_revoke`, `knowledge_lifecycle`, and `context_refresh_ack`.

Documented residual risks remain carried forward into E5–E8 / #169 / #170 as appropriate and do not reopen E4 unless new evidence proves a frozen-contract/security/data-integrity violation.

#### E5 next boundary

**E5 — capability/procedure experience integration is now the only allowed #176 implementation tranche.**

Frozen-plan scope:
- capability-centric experience retrieval;
- procedure/episode/feedback links;
- validated success/failure history;
- no opaque self-certified expert score;
- no automatic agent prompt rewriting.

Execution requirements:
1. start from authoritative main `a0a2769b99f4893733568194c0aa68e78e73aeab`;
2. read issue #176 and the frozen Experience Intelligence plan before implementation;
3. freeze a bounded E5 contract before code;
4. preserve existing E1–E4 truth owners and authority boundaries;
5. use targeted tests for bounded defects/corrections;
6. run full suite + release gate once on the coherent final E5 candidate;
7. use protected Fable/high acceptance if the E5 contract classifies the tranche as consequential governance/security;
8. guarded merge + post-main CI before E6;
9. do not begin E6 before E5 is fully accepted and closed.

**#165 and later program items remain blocked until #176 E5–E8 are complete and E9 physical criteria are carried into #169.**


---

### 14. 2026-10-05 #176 E5 contract freeze / implementation start boundary
Status: **E5 CONTRACT FROZEN — IMPLEMENTATION NOT YET STARTED**

This section supersedes older E5-next prose for the exact implementation start boundary.

Authoritative main:
`a0a2769b99f4893733568194c0aa68e78e73aeab`

E5 branch:
`issue-176-e5-capability-procedure-experience`

Frozen E5 contract commit:
`a06d32801a22a9c17439a0e03c081dae57ba2367`

Frozen E5 contract tree:
`5cd55b7f4cd6bf9885187af5f179db18018f29c8`

Contract:
`docs/architecture/EXPERIENCE-INTELLIGENCE-E5-CONTRACT-2026-10-05.md`

Retrieval schema target:
`176.e5.v1`

Architecture decision:
- **NO migration**;
- reuse `capabilities/capability_proofs`;
- reuse `procedures/procedure_versions/procedure_runs/procedure_feedback`;
- reuse immutable E1 episodes;
- reuse E1 `episode uses capability/procedure` relations;
- preserve E4 lifecycle/revocation gates.

Bounded E5 implementation:
- make explicit `capability_keys` a structured candidate-source signal, not only a ranking-after-retrieval signal;
- surface bounded procedure experience history derived from existing immutable/validated evidence;
- link task-backed feedback to the same-task eligible episode/procedure evidence path;
- preserve validated success/failure distinction;
- no expert score;
- no model-specific learning;
- no prompt rewriting;
- no procedure/lifecycle automatic mutation;
- no E6 retrieval-observation writes.

Before code:
1. create a fresh E5 Vres task from a correctly rooted E5 worktree;
2. checkpoint the frozen contract/base/branch identity;
3. do not alter the frozen contract;
4. then implement in bounded chunks with targeted red tests first.

Final E5 acceptance requires:
- targeted/unit/PostgreSQL/security/regression evidence;
- one coherent full suite;
- installed-runtime smoke because the pack schema changes;
- release gate;
- exact-head CI;
- current-turn freeze checkpoint;
- protected `vres-os:validator` Fable/high;
- guarded merge;
- post-main CI.

Do not begin E6 until E5 is fully accepted and closed.
