# Vres Preproduction Execution Checklist

Date: 2026-09-29  
Repository: `vosser24/Vres-OS`  
Authoritative main after #176 E2: `74c6445228a922db2622806f27e3c49a6c3454a7`

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
Status: **ACTIVE — E1 DONE; E2 DONE; E3 NEXT**

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

Implementation tranches:
- [x] E1 contracts + episode ledger;
- [x] E2 transition verifier + safe consolidation;
- [ ] E3 unified experience retrieval;
- [ ] E4 temporal lifecycle + revocation;
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

**#176 E3 — unified experience retrieval is the only allowed implementation next step. Start from authoritative main `74c6445228a922db2622806f27e3c49a6c3454a7`. Read issue #176 and the frozen Experience Intelligence plan in full, inspect merged E1 episode semantics and merged E2 proposed-lesson / transition-audit semantics, then freeze E3's smallest bounded retrieval contract before source edits. E3 must build staged, scope-first, trust-aware retrieval across existing decisions/knowledge/procedures plus episodes, using structured/lexical/optional semantic/graph/time signals, explicit conflict/staleness/premise output and bounded raw-evidence fallback. It must not create a second truth store, must not treat relevance as truth/authority, must not mutate memory during retrieval, and must preserve #163/#164/#174/E1/E2 boundaries. Do not begin E4 until E3 implementation/tests/evidence are complete. Do not start #165 until #176 is fully DONE.**
