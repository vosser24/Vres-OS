# Vres Preproduction Execution Checklist

Date: 2026-09-29  
Repository: `vosser24/Vres-OS`  
Authoritative main after #164: `fe31e30e593a44b8b5ab565fa0db859bbefec0c6`

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

**#176 is now the first and only allowed implementation/acceptance item.**

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

**#176 is now the first and only allowed implementation/acceptance item.**

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

**#176 is now the first and only allowed implementation/acceptance item.**

---

### 4. #176 — Experience Intelligence / Governed Agent Learning
Status: **ACTIVE NEXT — plan complete, implementation not started**

Durable plan:
- issue #176;
- Git-history plan branch: `docs-176-experience-intelligence-plan-20260927`;
- plan commit: `34f45afa0fb8d5a6a90bef53dec58d9ecef1093d`;
- file: `docs/architecture/EXPERIENCE-INTELLIGENCE-PLAN-2026-09-27.md`.

Implementation tranches:
- [ ] E1 contracts + episode ledger;
- [ ] E2 transition verifier + safe consolidation;
- [ ] E3 unified experience retrieval;
- [ ] E4 temporal lifecycle + revocation;
- [ ] E5 capability/procedure experience integration;
- [ ] E6 observability + experience utility evidence;
- [ ] E7 benchmark + security ladder;
- [ ] E8 Chairman integration + protected acceptance;
- [ ] carry E9 physical acceptance into #169;
- [ ] protected Fable/high as required per governance/security tranche;
- [ ] exact-head CI green;
- [ ] merge;
- [ ] post-merge main CI green;
- [ ] close #176.

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

**#176 Experience Intelligence / Governed Agent Learning is the only allowed implementation next step. Start from authoritative main `fe31e30e593a44b8b5ab565fa0db859bbefec0c6`. Read issue #176 and the frozen Experience Intelligence plan in full before source edits. Implement sequentially from E1 contracts + episode ledger, preserving existing truth owners, #163/#164 security boundaries, #174 architecture governance, no private model self-training, and no hidden chain-of-thought persistence. Do not start #165 until #176 is fully DONE.**
