# Vres Preproduction Execution Checklist

Date: 2026-10-05  
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


---

### 15. 2026-10-05 #176 E5 coherent final candidate / acceptance-in-progress boundary
Status: **E5 CHUNKS 1–3 IMPLEMENTED + TARGETED GREEN — FINAL LOCAL FULL-SUITE / RELEASE-GATE ACCEPTANCE IN PROGRESS; PR NOT OPEN**

This section supersedes section 14 for current E5 execution state. Section 14 remains the historical contract-freeze boundary.

#### Exact repository boundary

- authoritative main/base: `a0a2769b99f4893733568194c0aa68e78e73aeab`;
- E5 branch: `issue-176-e5-capability-procedure-experience`;
- E5 Vres task: `TASK-20261005-dc0e7a9e38`;
- frozen E5 contract commit: `a06d32801a22a9c17439a0e03c081dae57ba2367`;
- frozen E5 contract tree: `5cd55b7f4cd6bf9885187af5f179db18018f29c8`;
- coherent final E5 candidate HEAD: **`d39fabb22484a664e863c1603e2054d1ef0723c4`**;
- coherent final E5 candidate tree: **`fd00975275a1f8cc697bd4c570f994812e49f3b9`**;
- branch is 28 commits ahead of the E4-complete main;
- PR: **none yet**;
- schema remains **40 migrations**, latest `040_context_refresh_attestation.sql`; E5 adds no migration.

Base-to-candidate file delta is exactly eight files:
- `docs/architecture/EXPERIENCE-INTELLIGENCE-E5-CONTRACT-2026-10-05.md` — new frozen contract;
- `src/vres_os/experience_retrieval.py`;
- `tests/integration/test_e5_capability_retrieval.py` — new;
- `tests/integration/test_e5_procedure_history.py` — new;
- `tests/integration/test_experience_retrieval_journey.py`;
- `tests/integration/test_experience_retrieve_surface.py`;
- `tests/test_experience_retrieval.py`;
- `tests/test_experience_retrieval_e4.py`.

#### E5 delivered scope

E5 remains read-only integration over existing truth owners. It adds no new authority store.

Implemented:
- retrieval schema `176.e5.v1`;
- explicit `capability_keys` validated against active project-visible capabilities;
- direct `episode -> uses -> capability` structured candidate sourcing;
- accepted `capability_proofs` may source the proof task's eligible episode only when the immutable episode payload itself already names that capability;
- accepted procedures may be structurally sourced only through an already E1-integrity/E4-lifecycle-gated episode that directly uses the procedure and structurally matches the requested capability;
- bounded procedure `experience_history` containing validated success episode keys, validated failure episode keys, other failure episode keys, task-backed feedback, and latest validated evidence time;
- validated success/failure derives from immutable task-level `validated_runtime` episode evidence, never raw run counts or quality scores;
- task-backed feedback joins only through a current-eligible same-task episode that directly used the same procedure;
- feedback is #164-sanitized, bounded, and instruction-shaped feedback is omitted;
- real E4 source revocation removes affected current procedure history/feedback;
- repeated E5 retrieval is deterministic and mechanically proven read-only across E5-relevant truth owners.

Explicitly not implemented:
- no expert/success/confidence score;
- no authority from `proven_count`, run count, quality score, feedback count or model/provider identity;
- no model-specific personal memory;
- no prompt/routing/model-policy rewrite;
- no automatic procedure promotion/rewrite/demotion;
- no automatic lifecycle mutation;
- no E6 retrieval-observation writes;
- no MCP registration or write-authority expansion.

#### Targeted evidence — Chunk 1

Candidate:
- HEAD `a0b15d53ec96b1fd196dbb7778c3c42a853a45af`;
- tree `9772552df25f67bf9746c2b004f9d7aaa97d1f56`;
- checkpoint `CP-20261005-60dd993356`.

Evidence:
- unit/static: **165 passed**;
- focused E5 PostgreSQL: **3 passed**;
- E3/E4 retrieval regression: **122 passed**;
- E1 linkage regression: **19 passed**;
- critical Ruff: PASS;
- diff-check: PASS;
- fresh disposable PostgreSQL, migrations 001–040, isolated `VRES_DATA_DIR`, DB dropped;
- no local repository mutation.

#### Targeted evidence — Chunk 2

Candidate:
- HEAD `747997c2dd40ddf551a9bf17726ea573ef805258`;
- tree `187dea9addde9f97f53908148e59309a85a4e3ea`;
- explicit Chairman checkpoint `CP-20261005-8e70bf99ac`.

Evidence:
- unit/static: **166 passed**;
- focused E5 capability/procedure-history: **5 passed**;
- E3/E4 retrieval regression: **122 passed**;
- D set in originally requested mixed file ordering: **24 passed + 1 setup error** because `pg_project` was not discovered for an integration test;
- same D logical set with integration files collected first: **25 passed / 0 failed**;
- Ruff: PASS;
- diff-check: PASS;
- no skips/warnings.

Chunk-2 collection caveat is retained, not erased: the affected test lives under `tests/integration`, its `pg_project` fixture exists only in `tests/integration/conftest.py`, and the same test passed in the C set and the reordered D set. No E5 behavior assertion failed.

Automatic checkpoint `CP-20261005-bb0d29c4e5` has reason `pre_compact` and the same material Chunk-2 state. Treat it as host compaction bookkeeping, not an intentional second Chairman material checkpoint.

#### Targeted evidence — Chunk 3 / development closure

Final coherent candidate:
- HEAD `d39fabb22484a664e863c1603e2054d1ef0723c4`;
- tree `fd00975275a1f8cc697bd4c570f994812e49f3b9`;
- explicit Chairman checkpoint `CP-20261005-8fe3a4f070`.

Evidence:
- unit/static A: **235 passed**;
- critical Ruff: PASS;
- Chunk-3 diff-check: PASS;
- focused E5 B: **8 passed**;
- E3/E4 retrieval C: **122 passed**;
- D1 integration authority/linkage: **6 passed**;
- D2 unit/procedure/capability authority: **19 passed**;
- E4 revocation/retrieval E: **39 passed**;
- skips/warnings: **0**;
- worktree remained clean; local Claude made no repository mutation.

Fresh acceptance DB for the Chunk-3 targeted ladder was `vres_e5_c3_3635d6ac64bf_test`; it was dropped afterward. Separate disposable checks proved **40 migrations / latest 040** and `ISOLATED_VRES_CONFIG=PASS` with empty provenance-writer/migration-user configuration.

#### Local PostgreSQL methodology / machine-specific guards

- the database behind `pg_issue163_test_dsn` has historical migration drift and must NEVER be used as E5 acceptance evidence;
- that handle may be used only as an administrative/server connection to create/drop a brand-new disposable `_test` database;
- every PostgreSQL acceptance child must use an empty isolated `VRES_DATA_DIR` because this machine's real Vres config names a production provenance-writer role that conflicts with a single-role disposable DB;
- verify `provenance_writer_user` and `migration_user` are empty before the acceptance suite;
- never rewrite a migration ledger/digest to make a stale test DB usable.

#### Frozen-contract diff-check waiver

The frozen E5 contract intentionally contains Markdown hard line breaks (exactly two trailing spaces) at lines 3–7, 39 and 52–54. Those bytes are already present in frozen contract commit `a06d328...`.

Therefore:
- **do not edit the frozen contract** merely to normalize those spaces;
- baseline→candidate `git diff --check` is explicitly waived ONLY for those nine intentional frozen-contract lines;
- `git diff --check a06d328... HEAD` must remain clean;
- baseline→candidate excluding the frozen contract must remain clean;
- no other diff-check warning is waived.

Durable waiver evidence is recorded on issue #176, comment id `5994173149`.

#### Final local acceptance — CURRENT PENDING BOUNDARY

First final-acceptance attempt was blocked by an inspection-only hold before any shell/test/database work; nothing changed.

A later real user instruction cleared/replaced the hold. On the subsequent attempt:
- Stage 0 exact branch/HEAD/tree/origin-main/clean/contract/migration checks: PASS;
- repository-wide critical Ruff: PASS;
- baseline→candidate diff-check stopped only on the nine frozen-contract Markdown hard breaks;
- frozen contract was confirmed unchanged since `a06d328...`;
- post-freeze diff-check was reported clean;
- full PostgreSQL suite, release gate, wheel smoke and final-local checkpoint were **not yet run in that stopped attempt**.

ChatGPT then issued the explicit formatting waiver and instructed local Claude to continue from Stage 2 after first confirming:
1. `git diff --check a06d328... HEAD` is clean;
2. baseline→candidate excluding the frozen contract is clean.

At this documentation seal, the reply from that resumed final-local-acceptance run is **still pending**. Do not assume PASS or FAIL until the user supplies the actual local output.

#### Exact next action

If the pending local final-acceptance output is green:
1. verify exact candidate remains `d39fabb...` / tree `fd009752...` and clean;
2. require full fresh PostgreSQL suite result, same-DB migration proof, isolated-config proof, DB-drop proof;
3. require release gate `PASSED_WITH_EXPLICIT_LIVE_GATES` and candidate-wheel build/install/import-smoke evidence;
4. require exactly one explicit final-local-acceptance Chairman checkpoint;
5. ChatGPT creates the E5 PR from the unchanged exact head;
6. require exact-head PR CI SUCCESS plus release-gate artifact/digest;
7. only then create the one current-turn protected-validation freeze checkpoint and call `validation_prepare` once;
8. protected validator must be exactly `vres-os:validator`, Fable/high, no background/nested workers, canonical JSON terminal report;
9. on clean host-recorded protected PASS: guarded expected-head merge, exact post-main push CI, durable E5 closure, complete E5 Vres task;
10. only after all of that may E6 begin.

If the pending local output reports any full-suite/release-gate/package failure:
- STOP;
- do not create a PR;
- do not prepare protected validation;
- classify the exact defect and make only a bounded correction if it is real.

**Do not rerun Chunks 1–3 targeted ladders unless candidate bytes change or a concrete evidence gap is identified.**

---

### 16. 2026-10-05 #176 E5 bounded full-suite fix / reacceptance boundary
Status: **E5 FINAL CANDIDATE SUPERSEDED BY ONE-LINE BOUNDED FIX — REACCEPTANCE REQUIRED**

This section supersedes section 15 for current E5 execution state.

Authoritative main/base remains:
`a0a2769b99f4893733568194c0aa68e78e73aeab`

E5 branch:
`issue-176-e5-capability-procedure-experience`

E5 task:
`TASK-20261005-dc0e7a9e38`

Frozen E5 contract remains:
`a06d32801a22a9c17439a0e03c081dae57ba2367`

Superseded coherent candidate:
`d39fabb22484a664e863c1603e2054d1ef0723c4`
tree:
`fd00975275a1f8cc697bd4c570f994812e49f3b9`

New corrected candidate:
**`230c4fdb5a7674fe13518796be68a77848ff0561`**

New corrected tree:
**`97f98e2ad666df014bbc22270cc677aacd65a21f`**

Change from the superseded candidate:
- exactly one source line in `src/vres_os/experience_retrieval.py`;
- hardcoded `"revoked"` in the E5 structural-capability helper replaced with imported canonical `REVOKED_STATUS`;
- 1 insertion / 1 deletion;
- no test change;
- no migration;
- no contract change;
- no MCP/authority/routing/model/prompt change.

#### Why the full-suite failure was real

The first full PostgreSQL acceptance run on `d39fabb...` produced:
- **2205 passed**;
- **4 skipped**;
- **1 failed**;
- approximately 21m32s.

Failure:
`tests/test_source_revocation_unit.py::test_only_source_revocation_writes_the_revoked_status`

The static governance test correctly detected that E5 introduced a new literal reader of the revoked status.

The repository's authority rule is:
- `source_revocation.py` is the only revoked-status writer;
- `knowledge_status.py` owns the canonical read-side literal;
- other readers use the imported canonical constant rather than hardcoding `"revoked"`.

E4 main already imported `REVOKED_STATUS`; E5 Chunk 1 introduced the violating literal only in the new `disallowed_flags` set.

Therefore:
- this was **not** a stale test;
- this was **not** an environment issue;
- this was a real but bounded E5 code defect;
- the test must remain unchanged.

#### Evidence already proven by the failed full run

Before the failing assertion:
- exact branch/head/tree/remote/main checks passed;
- frozen contract unchanged;
- repository-wide critical Ruff passed;
- `git diff --check a06d328... HEAD` passed;
- baseline→candidate diff-check excluding the frozen contract passed;
- the frozen-contract Markdown hard-break waiver remains valid and unchanged;
- fresh acceptance DB was created and isolated;
- same acceptance DB had **40 migrations**, latest `040_context_refresh_attestation.sql`;
- `ISOLATED_VRES_CONFIG=PASS`;
- DB was dropped;
- original drifted DB was untouched;
- worktree remained clean;
- no checkpoint or protected validation request was created.

Known four skips:
- pgvector-only company-support eligibility test;
- Claude experiment symbolic-link availability on Windows;
- local-secrets Windows symlink privilege;
- release-boundary Windows symlink privilege.

#### Reacceptance cadence after the one-line fix

Because candidate bytes changed, exact acceptance identity changed.

Do NOT rerun the entire Chunk 1–3 targeted ladder.

First run a bounded correction proof on exact `230c4fdb...`:
- `tests/test_source_revocation_unit.py::test_only_source_revocation_writes_the_revoked_status`;
- focused E5 capability/procedure retrieval tests;
- critical Ruff on changed surfaces;
- post-freeze and non-contract diff-checks.

If that passes, rerun exactly one coherent final acceptance cycle:
- fresh disposable PostgreSQL full suite;
- same-DB migration/isolation proof;
- release gate once;
- candidate wheel build/install/import smoke;
- exact Git identity;
- one final-local-acceptance checkpoint.

Do not create a PR until that exact new candidate is locally green.

Protected validation remains blocked until:
1. local final acceptance green;
2. PR exists;
3. exact-head CI green on the exact corrected SHA.

No E6 work may begin.

---

### 17. 2026-10-05 #176 E5 merged / post-main accepted — local Vres task completion only
Status: **E5 PRODUCT/REPOSITORY ACCEPTANCE COMPLETE — TASK COMPLETION PENDING ON LOCAL VRES HOST**

This section supersedes sections 15 and 16 for current E5 state.

#### Final accepted identities

Frozen E5 contract:
`a06d32801a22a9c17439a0e03c081dae57ba2367`

Final corrected candidate:
`230c4fdb5a7674fe13518796be68a77848ff0561`

Candidate/final tree:
`97f98e2ad666df014bbc22270cc677aacd65a21f`

PR:
`#183`

Merged main:
**`6af7bddf246e0f628c3e52add9528742e85189ca`**

E5 task:
`TASK-20261005-dc0e7a9e38`

#### Final local acceptance

Bounded one-line correction proof on the corrected candidate:
- formerly failing revoked-status governance test: **1 passed**;
- `tests/test_experience_retrieval.py`: **115 passed**;
- focused E5 PostgreSQL integration: **8 passed**;
- critical Ruff: PASS;
- post-freeze diff-check: PASS;
- baseline→candidate excluding the frozen contract: PASS.

Full corrected-candidate Windows/PostgreSQL acceptance:
- fresh disposable DB: `vres_e5_c4full_3e3cc4d677c4_test`;
- `ISOLATED_VRES_CONFIG=PASS`;
- migration count: **40**;
- highest migration: `040_context_refresh_attestation.sql`;
- **2206 passed / 4 skipped / 0 failed / 0 errors / 0 warnings**;
- disposable DB dropped: `DROPPED=True`;
- original drifted DB untouched.

Local release gate:
- status: `PASSED_WITH_EXPLICIT_LIVE_GATES`;
- candidate commit/tree exact and clean;
- wheel build / exact Python+SQL bytes / temporary install / import smoke: PASS;
- wheel: `vres_os-0.2.0a1-py3-none-any.whl`;
- SHA256: `91d47125e14aa52cf8bced8355fb212802ff1f158413b3339597316e8080b180`;
- bytes: **385391**;
- source files compared: **134**.

Final-local-acceptance checkpoint:
`CP-20261005-949900c05d`

#### PR exact-candidate-tree CI

PR #183 pull_request CI:
- workflow run: `37339979267` / CI #472;
- PR head: `230c4fdb5a7674fe13518796be68a77848ff0561`;
- full suite: **2207 passed / 3 skipped**;
- installed-runtime smoke: PASS;
- release gate: PASS;
- artifact digest:
  `sha256:49c5a001f9f90bd2c6013a43ce03fc9bdb4320c98df96194fce9dd8228ce6748`.

GitHub's pull_request checkout used synthetic merge commit
`70abf6d95a44fa92b086c61308641bcb96007a90`.
This was accepted only after verifying:
- the run is bound to PR head `230c4fdb...`;
- release-gate tree = exact candidate tree `97f98e2...`;
- compare candidate→synthetic merge is one metadata merge commit ahead with **zero changed files**.

Durable PR evidence comment:
`5998674253`

#### Protected validation

Cycle 1:
- freeze checkpoint: `CP-20261005-fe30d00bec`;
- request: `VAL-afdb8d037183467e`;
- host-observed protected Fable/high;
- result: FAILED because **11 passed / 0 failed / 2 not_run**;
- not_run gaps were PostgreSQL evidence access and GitHub CI readback;
- no candidate defect was reported;
- no automatic retry occurred.

Bounded recovery was explicitly authorized with unchanged candidate bytes.

Cycle 2:
- retry freeze checkpoint: `CP-20261005-c9c6ca275f`;
- request: `VAL-21170237cd6a482c`;
- validator: `vres-os:validator`;
- host-observed model: `claude-fable-5-1`;
- prepared effort: high;
- canonical outcome: **passed**;
- **15 checks passed / 0 failed / 0 not_run**.

Cycle-2 direct PostgreSQL proof:
- fresh DB: `vres_e5_val2_e1fe5557c98c_test`;
- isolated config PASS;
- 40 migrations / latest 040;
- required four E5/retrieval integration files: **111 passed**;
- pytest exit 0;
- DB drop proof: `DROPPED=True`;
- no DSN printed;
- original drifted DB untouched.

Cycle-2 direct GitHub REST proof independently verified:
- PR #183 exact head/base;
- CI #472 completed/success;
- required CI steps success;
- release artifact digest exact;
- synthetic merge had zero file changes.

Durable protected-PASS PR comment:
`5999333268`

#### Guarded merge and post-main acceptance

PR #183 was merged with expected-head protection against exact:
`230c4fdb5a7674fe13518796be68a77848ff0561`

Merge/main SHA:
**`6af7bddf246e0f628c3e52add9528742e85189ca`**

Post-merge push CI:
- run: `37346476024` / CI #473;
- exact head: `6af7bddf246e0f628c3e52add9528742e85189ca`;
- job `111886190218`: SUCCESS;
- all substantive steps: SUCCESS;
- full PostgreSQL suite: **2207 passed / 3 skipped**;
- installed-runtime smoke: PASS;
- release gate: `PASSED_WITH_EXPLICIT_LIVE_GATES`;
- release-gate `git_commit`: exact new main;
- release-gate `git_tree`: `97f98e2ad666df014bbc22270cc677aacd65a21f`;
- `dirty=false`;
- `error=null`;
- artifact id: `11360229051`;
- artifact digest:
  `sha256:a8837251697e4a23c944b18e9a71a319a8560873867fe258baf51c92a7b4e076`;
- release-gate wheel SHA256:
  `4d3ccc33df642db4c804142586725686b65a6329f9d829bd1cac508c3b561649`;
- wheel bytes: **382832**;
- evidence file count: **410**;
- migrations: **40**.

The logged PostgreSQL ERROR/FATAL lines in the CI service output are expected negative-test evidence; the pytest job itself completed green.

#### E5 closure status and exact next action

Repository/product acceptance for E5 is complete.

One governance action remains before E6:
- complete `TASK-20261005-dc0e7a9e38` exactly once through the existing local Vres host/session, using the current host-recorded protected PASS;
- do not invalidate validation;
- do not create another checkpoint unless the host contract requires one;
- do not rerun tests/release gate/protected validation;
- make no repository edits.

**E6 MUST NOT START until that task completion succeeds and is read back.**

Carry-forward non-blocking observations into E7/security-hardening work rather than reopening E5:
- validator noted strict-ruleset Ruff observations UP017/B007/B905 on E5 files not enforced by current CI;
- first validation cycle noted contract cases 15/16/24 lacked dedicated E5 tests, while behavior was inspected and the eventual protected cycle passed the complete frozen contract;
- do not mutate the accepted E5 candidate solely for these follow-up observations.

---

### 18. 2026-10-05 #176 E5 DONE / E6 NEXT
Status: **E5 COMPLETE — E6 MAY BEGIN**

This section supersedes section 17 for current execution state.

#### E5 final closure

Authoritative product main:
**`6af7bddf246e0f628c3e52add9528742e85189ca`**

Final E5 candidate:
`230c4fdb5a7674fe13518796be68a77848ff0561`

Accepted tree:
`97f98e2ad666df014bbc22270cc677aacd65a21f`

PR:
`#183` — merged.

Protected validation:
- request: `VAL-21170237cd6a482c`;
- host-observed protected validator: `claude-fable-5-1`;
- effort: high;
- outcome: **passed**;
- **15 passed / 0 failed / 0 not_run**.

Post-main CI:
- CI #473 / run `37346476024`;
- exact main head: `6af7bddf246e0f628c3e52add9528742e85189ca`;
- **2207 passed / 3 skipped**;
- installed-runtime smoke PASS;
- release gate `PASSED_WITH_EXPLICIT_LIVE_GATES`;
- artifact digest:
  `sha256:a8837251697e4a23c944b18e9a71a319a8560873867fe258baf51c92a7b4e076`.

E5 Vres task:
`TASK-20261005-dc0e7a9e38`

Final task completion:
- `task_complete` called exactly once;
- result: `{"completed": true}`;
- final status: **completed**;
- completed_at:
  **`2026-10-05T20:25:13.691161+03:00`**;
- completion occurred after the latest passed protected validation;
- protected validation remains associated with the task;
- candidate worktree remained clean at exact HEAD/tree;
- no E6 work was started before completion.

The earlier failed protected request `VAL-afdb8d037183467e` remains preserved as failed evidence and was not rewritten.

#### E5 acceptance is closed

No further E5 action is pending.

Do not rerun E5 local acceptance, PR CI, post-main CI, release gate or protected validation unless:
- accepted E5 bytes change; or
- a concrete regression/evidence gap is discovered.

Carry-forward non-blocking observations remain assigned to later hardening:
- strict-ruleset Ruff observations UP017/B007/B905;
- dedicated one-test-per-contract-criterion gaps previously noted for E5 cases 15/16/24.

These do not reopen E5.

#### Next tranche

Next:
**E6 — observability + experience utility evidence**

E6 scope from #176:
- retrieval observations;
- cited/used memory evidence;
- outcome/validation joins;
- no causal-credit overclaim;
- baseline/candidate retrieval-policy replay.

At this seal:
- no E6 implementation branch is authoritative yet;
- no E6 Vres task has been created by this closure step;
- no E6 contract has been frozen yet.

E6 must begin from exact accepted main:
`6af7bddf246e0f628c3e52add9528742e85189ca`

Recommended opening sequence:
1. create/bind the E6 Vres task on the new tranche;
2. perform read-only discovery against current E1–E5 truth owners and retrieval surfaces;
3. draft the bounded E6 contract with explicit observability/write authority, privacy/security, replay and no-causal-overclaim invariants;
4. freeze/protect the E6 contract before implementation;
5. implement in bounded chunks with the established fresh PostgreSQL / isolated-config / exact-head CI / protected-validation methodology.

Do not widen E6 into E7 benchmark/security work or E8 Chairman automatic injection.

---

### 19. 2026-10-05 #176 E6 contract frozen / Chunk 1 not started
Status: **E6 CONTRACT FROZEN — IMPLEMENTATION BLOCKED UNTIL LOCAL CHECKPOINT**

This section supersedes section 18 for current execution state.

Authoritative product main:
`6af7bddf246e0f628c3e52add9528742e85189ca`

E6 branch:
`issue-176-e6-observability-utility`

E6 Vres task:
`TASK-20261005-abb88a1f0e`

Frozen E6 contract commit:
**`fe6cfcfe0d87cd6920303242a1d647975aa3bf22`**

Frozen E6 contract tree:
**`49b017914948eb76fc27c9cbdd550f1d80c12009`**

Contract:
`docs/architecture/EXPERIENCE-INTELLIGENCE-E6-CONTRACT-2026-10-05.md`

Base→freeze delta:
- exactly one commit ahead of accepted E5 main;
- exactly one added file;
- **913 additions / 0 deletions**;
- no implementation, migration, hook or test bytes changed.

E6 policy target:
`176.e6.v1`

Frozen policy digest:
`d61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5`

Frozen existing E5 retrieval-policy digest:
`7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9`

Migration target:
`041_experience_retrieval_observability.sql`

Architecture:
- normal E5 retrieval remains READ ONLY and public schema stays `176.e5.v1`;
- successful retrieval observation occurs only after host `PostToolUse`;
- host observation/reference writes use the existing provenance-writer role through protected SECURITY DEFINER functions;
- no raw query/premise/memory text/transcript/private reasoning persists in the E6 ledger;
- explicit-reference absence means `not_observed`, never `unused`;
- downstream task/validation/episode evidence is joined read-only;
- every E6 utility/replay result states `causal_credit='not_established'`;
- no opaque utility/expertise score;
- paired baseline/candidate policy replay uses one REPEATABLE READ / READ ONLY snapshot and one hard-gated candidate universe;
- candidate replay cannot alter project/company/capability/lifecycle/revocation/security/authority gates;
- no policy winner/activation/promotion in E6.

Implementation chunks:
1. migration 041 + host retrieval observation;
2. explicit-reference capture + utility evidence;
3. paired retrieval-policy replay.

Before any implementation:
1. local E6 worktree must fast-forward to exact `fe6cfcfe...`;
2. require branch/head/tree/origin identity and clean worktree;
3. read the frozen contract;
4. create exactly one intentional E6 contract-freeze Chairman checkpoint recording base/branch/contract/task;
5. do not modify the frozen contract after that checkpoint;
6. only then begin Chunk 1 with targeted red tests first.

Final E6 acceptance requires:
- one coherent full fresh PostgreSQL suite;
- migration count 41 / latest 041 on the acceptance DB;
- isolated `VRES_DATA_DIR`;
- release gate and exact wheel/source proof;
- installed runtime + hook smoke;
- exact-head PR CI;
- protected `vres-os:validator` Fable/high with zero `not_run`;
- guarded merge;
- exact post-main CI;
- E6 task completion exactly once.

Do not begin E7/E8 during E6.



---

### 20. 2026-10-08 #176 E7 through Boundary 4A accepted / Boundary 4B next

Status: **E7 CHUNKS 0–5 + AUTHORITY CLOSURE B2/B3/B4A ACCEPTED — B4B NEXT**

This section supersedes section 19 for current execution state.

Authoritative accepted product main remains:
9a8acc5d464b96432a93cb95daa9581412fb07ee

E7 branch:
issue-176-e7-benchmark-security

Accepted E7 branch HEAD after live development authority closure:
**7aac85ac4917bfd3b178978183082debdd6333ca**

Boundary 3 accepted predecessor:
3ceae86aedfabaf949f231a5c956803e7d66cadd

Canonical E7 Vres task:
TASK-20261006-6cd9d80a92

Newest detailed execution handoff:
docs/handoffs/PREPRODUCTION-E7-B4B-RESUME-HANDOFF-2026-10-08.md

#### Accepted E7 state

Accepted:
- Chunk 0 loader/canonical/digest
- Chunk 1 corpus/splits/scoring
- Chunk 2 baseline adapters/retrieval/determinism
- Chunk 3 operation faithfulness
- Chunk 4 outcome/negative-transfer/streaming
- Chunk 5 security hardening
- Authority Closure Boundary 2
- Authority Closure Boundary 3 deterministic observed/reproducibility closure
- Authority Closure Boundary 4A live participated DEVELOPMENT cohort

Boundary 4A commit:
7aac85ac4917bfd3b178978183082debdd6333ca

Boundary 4A artifact:
benchmarks/experience_e7/results/authority_closure_development_live.json

Boundary 4A artifact SHA-256:
03b3c9e2c798ccdcabf53a7d1c6fe63e176662e796bae84c0fab146a2edfb661

Boundary 4A live evidence:
- 9 E1-v1 participated/trusted captures
- 9 real host-observed Fable routes
- 6 real host-observed Sonnet workers
- 6 passed work units
- 3 failed work units
- dev_seen remains E1-v2 observed / external_untrusted_observation
- capability precedent exactly cap_forecasting and cap_leadtime
- recurrence consolidation remains quarantined because recurrence threshold calibration is intentionally not started

No product code changed in Boundary 4A.

#### Exact current gate

Boundary 4B has NOT started.

Before any B4B live work:
1. verify/finish cleanup of the accepted B4A disposable fixture;
2. return to the normal/control Vres environment;
3. require E7 branch HEAD/origin = 7aac85ac4917bfd3b178978183082debdd6333ca and clean tracked tree;
4. resume TASK-20261006-6cd9d80a92;
5. record one canonical checkpoint sealing Boundary 4A acceptance;
6. do not complete the task;
7. prepare a fresh B4B-specific ignored launcher/helper;
8. run B4B DryRun and require production-shaped split-role fixture checks plus complete cleanup;
9. only then launch a fresh top-level B4B Claude fixture.

#### Boundary 4B scope

Live adversarial participated-authority closure only:

adv_secret_episode:
- 1 real failed work-unit authority path;
- frozen assertion no_secret_persistence;
- adv_e must_not_persist;
- never put the raw canary in committed output.

adv_flood_burst:
- 25 real failed work-unit authority paths;
- 25 frozen E2 consolidations;
- required security includes burst_fails_closed and frequency_is_not_trust;
- flood transitions must not promote/retrieve.

adv_varied_poison:
- 6 real failed work-unit authority paths;
- 6 frozen E2 consolidations;
- required security includes varied_poison_single_lineage;
- varied poison transitions must not promote.

Totals:
- 32 real Fable-routed failed work-unit authority paths
- 0 expected Sonnet workers
- 31 frozen E2 consolidations

Keep the accepted deterministic adversarial matrix separate:
16 PASS / 0 FAIL / 1 not_applicable / 3 not_run_owner_gap.

Boundary 4B creates a separate host-attested live overlay.

A genuine B4B scorer/security failure is evidence.
Do not patch E1/E2/E5/scoring/migrations/thresholds inside the same B4B run.
Stop, preserve normalized RED evidence, and freeze a separate hardening addendum before implementation.

#### Still pending after Boundary 4B

Only after independent B4B acceptance:
- Chunk 6 development replay across memory_disabled / raw_refind / current_vres / candidate_hybrid
- representative baseline measurement
- development threshold calibration/freeze
- held-out final gate, without tuning on held-out
- one coherent final fresh PostgreSQL suite
- release gate
- installed-runtime smoke only if packaging/MCP/plugin changed
- exact-head CI
- protected Fable/high final review
- guarded merge
- exact post-main CI
- complete E7 task exactly once
- E8 only after E7 closure

Do not call E7 complete and do not call Vres production-ready at this boundary.
