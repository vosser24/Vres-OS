# Vres Preproduction Execution Checklist

Date: 2026-09-27  
Repository: `vosser24/Vres-OS`  
Planning base: `f0a69c3e471fe25c6547ee1af162019caf290d49`

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
Status: **IN PROGRESS — implementation built, not accepted/merged**

Current candidate:
- PR #173
- branch: `issue-163-credential-broker`
- head: `4baf4fadbbd402a0dd523837924e6436f74f27d1`
- automated CI: green

Remaining before DONE:
- [ ] protected `vres-os:validator` Fable/high PASS on exact candidate;
- [ ] required Chairman / F-15 smoke for changed lifecycle surface;
- [ ] update final handoff if acceptance state changes branch head;
- [ ] exact-head CI green after any final doc/head change;
- [ ] merge PR #173;
- [ ] post-merge main CI green;
- [ ] close #163 while explicitly preserving physical Windows criteria in #169.

**Do not start #174 merge/rebase or #164 implementation until #163 is DONE.**

---

### 2. #174 — Engineering Architecture Governance
Status: **BUILT IN PARALLEL / HELD — not merged**

Current candidate:
- PR #175
- branch: `issue-174-engineering-architecture-governance`
- head: `d0b59289e443dab14dd658411a0ee1d3d61d23c7`
- automated CI: green

Required after #163 DONE:
- [ ] update/rebase #174 onto new authoritative main;
- [ ] resolve any integration drift;
- [ ] exact-head full CI green;
- [ ] protected Fable/high validation on the new exact head;
- [ ] merge PR #175;
- [ ] post-merge main CI green;
- [ ] close #174.

**Do not start #164 implementation until #174 is DONE.**

---

### 3. #164 — Secret-safe onboarding
Status: **NOT STARTED**

Required:
- [ ] implement secret-bearing path exclusion;
- [ ] pre-model/pre-persistence sanitization;
- [ ] fail-closed uncertain-sensitive handling;
- [ ] Credential Broker reuse;
- [ ] synthetic secret fixture/security tests;
- [ ] relevant onboarding regressions;
- [ ] protected Fable/high validation;
- [ ] docs/handoff;
- [ ] exact-head CI green;
- [ ] merge;
- [ ] post-merge main CI green;
- [ ] close #164, carrying physical criteria to #169.

**Do not start #176 implementation until #164 is DONE.**

---

### 4. #176 — Experience Intelligence / Governed Agent Learning
Status: **PLAN COMPLETE / IMPLEMENTATION NOT STARTED**

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

**#163 protected Fable/high validation is the only allowed implementation/acceptance next step.**
