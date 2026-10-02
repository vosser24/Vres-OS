# Vres-OS — Preproduction Resume Handoff

Date: 2026-09-29  
Repository: `vosser24/Vres-OS`  
Canonical checklist: `docs/PREPRODUCTION-EXECUTION-CHECKLIST-2026-09-27.md`

This is the canonical detailed continuation record after completing #176 E2 and entering #176 E3. E3 contract/discovery and Chunk 1 are committed locally; the current live step is bounded Chunk 1 hardening before Chunk 2. A fresh session should be able to resume from this file and the checklist without relying on chat memory.

The operating rule remains strict:

> **Do not start implementation of a later checklist item until the previous item is fully DONE.**

At this handoff boundary:

- **#163 is DONE.**
- **#174 is DONE.**
- **#164 is DONE.**
- **#176 remains active; E1 and E2 are DONE; E3 is ACTIVE; Chunk 1 hardening is the only allowed next implementation work.**
- #165 and everything after #176 remain blocked by sequence.

---

# 1. Exact continuation point

Authoritative `main`:

`74c6445228a922db2622806f27e3c49a6c3454a7`

This is the merge commit of PR #180, completing #176 E2 on top of the already accepted E1 foundation.

#176 tranche status:

- E1 — contracts + immutable episode ledger: **DONE**;
- E2 — transition verifier + safe consolidation: **DONE**;
- E3 — unified experience retrieval: **NEXT / NOT STARTED**;
- E4–E8: **NOT STARTED**;
- E9 remains physical acceptance in #169.

Final E2 acceptance identity:

- issue: #176, tranche E2 only;
- branch: `issue-176-e2-consolidation`;
- PR: #180;
- E2 task: `TASK-20260929-9fdfbe76eb`;
- historical failed protected request: `VAL-84afc8fa56a245bf` — FAILED and preserved;
- final protected request: `VAL-58bb131a10b54abd` — PASS;
- host-observed protected validator/model: `vres-os:validator` / `claude-fable-5-1`;
- exact protected-reviewed head: `c1dccfa800381b1f5b01fd054cb3819720600e2a`;
- E2 base: `407c4a323f4f65c8f28c422789508bb7ce128682`;
- exact-head CI: #461 / `36585887143` — SUCCESS;
- exact-head artifact: `11042340684`;
- exact-head artifact digest: `sha256:afb432d024f1647586b0d0d2e239c34fda2845344f1549ab973ce8996d82eaa8`;
- merge/main: `74c6445228a922db2622806f27e3c49a6c3454a7`;
- post-merge main CI: #462 / `36589408835` — SUCCESS;
- post-merge PostgreSQL integration: PASS;
- post-merge installed-runtime smoke: PASS;
- post-merge release gate: PASS;
- post-merge artifact: `11042962873`;
- post-merge artifact digest: `sha256:082fdc00743b212dd7f3fb30c9de451b943274e755d8f6b81bc4624a3e0a1ab6`.

The failed first protected review was productive and remains part of the evidence trail. It led to bounded corrections for:
- participation/trust per-check labeling;
- removal of the undisclosed recurrence-acceptance escape hatch;
- exact frozen-plan Git identity in the E2 contract;
- the specific F541 SQL-string nit;
- cleaner evidence handling for isolated CI versus contaminated local provenance configuration.

E2 shipped no E3 retrieval behavior and no #165+ scope.

#163, #174 and #164 remain DONE. #176 remains the only active implementation issue.

The first and only implementation tranche now allowed is **#176 E3 — unified experience retrieval**.

---
# 2. Canonical sequential execution order

The order remains:

1. **#163 — Credential Broker — DONE**
2. **#174 — Engineering Architecture Governance — DONE**
3. **#164 — Secret-safe onboarding — DONE**
4. **#176 — Experience Intelligence / Governed Agent Learning — ACTIVE / E1 DONE / E2 DONE / E3 NEXT**
5. **#165 — Chairman model policy — NOT STARTED**
6. **#166 — Global Claude adoption — NOT STARTED**
7. **#167 — Current-user Data Source Registry — NOT STARTED**
8. **#168 — Project adoption / canonical scaffold — NOT STARTED**
9. **#169 — Integrated Windows / Visual Studio live acceptance — NOT STARTED**
10. **#170 — Production Readiness / Go-Live — NOT STARTED**

Do not begin #165 until #176 is fully DONE.

---

# 3. Final #163 implementation identity

Issue:

**#163 — Credential Broker: current-user reusable secrets and prompt ingress protection**

PR:

**#173**

Accepted implementation head:

`4baf4fadbbd402a0dd523837924e6436f74f27d1`

Original base:

`f0a69c3e471fe25c6547ee1af162019caf290d49`

Merge commit:

`7f9961b5980f1a229cece4902f9e1d709e397e22`

The merge used an expected-head guard against the accepted head, so GitHub would have rejected the merge if PR #173 had moved.

#163 product scope is now on authoritative main.

---

# 4. Final #163 architecture and security contract

Credential Broker implements current-Windows-user reusable credential resources.

Durable credential values:

- remain in Windows Credential Locker on the supported Windows target;
- are not stored as plaintext in PostgreSQL, project files, CLAUDE.md, skills, agents, procedures, checkpoints, knowledge, logs or validation artifacts.

Vres persists only non-secret:

- resource identity/metadata;
- current-user namespace;
- field names;
- pending-capture metadata;
- explicit per-project bindings.

Credential identity is normalized by:

- service type;
- origin/service;
- account.

The resource is not owned by the project that first discovered it.

Cross-project reuse requires an explicit project binding.

Knowing a resource id is not sufficient authorization.

Another Windows user must not inherit the first user's reusable credential namespace.

Legacy project-scoped `vres secret` remains supported.

Native Claude/Codex vendor authentication remains outside Vres credential ownership.

Environment variables and materialized files are ephemeral delivery adapters, not durable credential stores.

---

# 5. Final #163 prompt-ingress contract

The high-confidence credential guard runs before normal Vres prompt/session persistence.

Important accepted behavior:

- deterministic credential detection;
- `decision=block`;
- non-secret reason;
- `suppressOriginalPrompt=true`;
- bounded unambiguous values may enter a secure pending-capture flow;
- ambiguous/conflicting input is blocked without silently becoming a reusable credential;
- capture failure remains blocking;
- failure logs use a fixed non-secret diagnostic rather than provider exception text.

The guard runs before normal task/user-instruction persistence so blocked credential material is not staged into Vres PostgreSQL.

Exact live Claude transcript/debug behavior remains a #169 physical criterion.

---

# 6. #163 automated/exact-head evidence

Exact-head CI:

- run: **#407**
- run ID: `36158185554`
- exact head: `4baf4fadbbd402a0dd523837924e6436f74f27d1`
- conclusion: **success**
- full suite: **1056 passed, 1 skipped**
- installed-runtime smoke: PASS
- local release gate: PASS

The one skip is the inherited Windows-specific Node/libuv inherited-stdin Git hang case.

A PostgreSQL credential-ingress journey was also exercised directly before final protected validation:

`tests/integration/test_credential_ingress_journey.py`

Result:

- **1 passed**
- not skipped
- run through the secure local-secret handle
- no credential value exposed into chat/model context.

The local test DSN is stored by handle:

`pg_issue163_test_dsn`

Do not print or export its value. Preserve the handle unless a later deliberate cleanup establishes it is no longer needed.

---

# 7. #163 protected Fable/high validation

First protected request:

`VAL-253f18abb7ca4165`

This correctly failed closed because the required PostgreSQL integration journey had not yet been run with a valid disposable `_test` DSN.

That historical failure is preserved and was not rewritten.

After secure test-DB preparation and successful PostgreSQL journey, the fresh authoritative validation was:

`VAL-52be75fc46484345`

Host-observed validator/model:

`claude-fable-5-1`

Contract:

- pinned protected validator;
- Fable/high;
- no substitute model;
- no model override.

Outcome:

**PASSED**

The validator independently reran the required PostgreSQL journey through secure local-secret injection and re-derived the #163 acceptance contract.

Do not rerun #163 protected validation unless a future regression changes this owned surface.

---

# 8. #163 required live regression family

Because #163 changed UserPromptSubmit/lifecycle behavior, the applicable finalization policy required:

- **F-05**
- **F-06**
- **F-15**

All three are accepted as PASS for the #163 candidate.

## 8.1 F-05 — continuity across compact/clear/restart

Disposable project:

`C:\Projects\Vres-F05-163-20260928`

Project key:

`project:934d63add27d17a0eea213fa`

Task:

`TASK-20260928-a1684a676f`

Decision:

`DEC-20260928-239d22bf2c`

Marker:

`F05-MARKER-TASK-20260928-a1684a676f`

Authoritative compact checkpoints:

- PreCompact: `CP-20260928-fa4b3207f2`
- PostCompact verified: `CP-20260928-c3a79c7e95`

Provider sessions:

- before native clear: `bf008759-fe40-404e-be27-172db0e6e645`
- after native clear: `1a85dc8d-d310-4ea5-8edb-3835d15a0279`
- after normal exit/restart: `5b1582ae-eae9-4c7d-a7b5-45ec903e5ada`

Authoritative evidence established:

- durable objective/constraints/decision/changed surface/marker survived native compact;
- marker re-test exit 0;
- old provider session ended with `end_reason=provider_session_replaced`;
- replacement session inherited the correct task;
- normal restart rehydrated the same task;
- no invented unsaved reasoning.

An initial F-05 FAIL was an evidence-access failure because MCP did not expose historical checkpoint/session-end fields. The gap was closed using SELECT-only authoritative storage readback. No continuity defect was found.

F-05: **PASS**.

## 8.2 F-15 — realistic bounded Chairman smoke

Task:

`TASK-20260928-82bf5b484b`

Reply-gate turn:

`TURN-c1835666fed4`

Checkpoint:

`CP-20260928-5aad28afe5`

F-15 exercised:

- durable task/resume behavior;
- native auto-compaction continuity;
- deterministic task work;
- validator specialist;
- procedure/knowledge lookup;
- product acceptance;
- protected action;
- protected-PASS checkpoint guard.

No unresolved critical defect was found.

F-15: **PASS**.

## 8.3 F-06 — concurrent sessions and cross-project isolation

### Project A

Path:

`C:\Projects\Vres-F06-163-A-20260928`

Project key:

`project:0c82204055fa1a4b2e153d00`

ALPHA:

- task: `TASK-20260928-9712fbcc0d`
- original A1 provider session: `8930d0f7-310f-49f6-873a-5a938c88915a`
- replacement A1 provider session after native clear: `e42c2582-4dad-4e22-ad4b-ca0de58cc0b4`
- marker: `F06-ALPHA-163-20260928`

BETA:

- task: `TASK-20260928-1ff9f5f007`
- A2 provider session: `2b7b96b2-f600-4b49-a218-b3e0eeeacf60`
- marker: `F06-BETA-163-20260928`
- initial checkpoint: `CP-20260928-68fca5bc42`
- final-review checkpoint: `CP-20260928-e0a0179f57`
- protected completion validation: `VAL-f16767c705674dd1`
- host-observed validator: `claude-fable-5-1`
- validation outcome: PASS
- task completion: PASS

### A1 native clear replacement evidence

The native clear replacement proof established:

- replacement A1 session differed from old A1;
- replacement inherited ALPHA before project-focus/recency fallback;
- old A1 was durably ended as `provider_session_replaced`;
- A2/BETA remained open and separate;
- ALPHA marker exit 0;
- BETA marker unchanged.

### Genuine ambiguity/no-recency proof

Earlier ambiguity attempts were noisy because the session was not actually unbound or because later audit logic incorrectly expected read-only calls to leave task events.

The final clean setup used temporary:

GAMMA-RAW:

`TASK-20260928-9793297100`

Helper provider session:

`334f2d33-bc49-491a-8b34-2797c72d3ccf`

GAMMA-RAW was explicitly cancelled by a separate current user instruction:

`cancel this task`

After cancellation:

- helper session was unbound;
- project focus was null;
- ALPHA active;
- BETA active.

Then, in the same helper turn, the real governed call:

`task_resume(session_id="334f2d33-bc49-491a-8b34-2797c72d3ccf")`

with **no task_key** returned:

`ambiguous=true`

with unfinished candidates containing both:

- `TASK-20260928-1ff9f5f007` BETA
- `TASK-20260928-9712fbcc0d` ALPHA

Neither task was selected by recency.

Immediately afterward:

- `vres_status.active_task=null`;
- ALPHA/BETA remained active;
- their observed timestamps/state were unchanged by the ambiguity call.

### Important F-06 evidence semantics

Do not reopen the ambiguity proof merely because a later ALPHA checkpoint says the ambiguity claim was “unevidenced.”

Repository implementation matters:

- MCP `task_resume` delegates to `Repository.resume_context()`;
- for a no-key unbound session with multiple unfinished tasks, `resume_context()` returns `{"ambiguous": true, ...}`;
- that read-only path does **not** write a `task_events` record.

Therefore absence of a `task_events` row is not evidence that the no-key call did not occur.

Likewise, later explicit keyed `task_resume(..., BETA)` calls can update project focus, so a later `project_focus=BETA` observation does not invalidate the earlier moment when project focus was null.

The final ambiguity acceptance is the same-turn live tool return plus immediate no-mutation/focus checks, matching the documented F-06 behavioral contract.

### Post-ambiguity governed session binding

A1 later proved through governed tools:

- current session remained `e42c2582-4dad-4e22-ad4b-ca0de58cc0b4`;
- explicit governed ALPHA resume succeeded;
- BETA was separately active before completion.

A2 independently proved:

- current session remained `2b7b96b2-f600-4b49-a218-b3e0eeeacf60`;
- governed BETA resume succeeded;
- ALPHA remained separately active.

### BETA protected completion and A1 non-jump

BETA final-review validation:

`VAL-f16767c705674dd1`

Host-observed validator:

`claude-fable-5-1`

Outcome:

**PASS**

Then:

`task_complete(TASK-20260928-1ff9f5f007)`

returned:

`{"completed": true}`

Post-completion unfinished inventory contained ALPHA only.

Final A1 non-jump proof:

- A1 provider session: `e42c2582-4dad-4e22-ad4b-ca0de58cc0b4`
- no-key `task_resume` resolved to ALPHA
- BETA was absent from unfinished tasks
- ALPHA remained active
- non-material reply gate allowed
- no checkpoint/status/task mutation occurred.

This satisfies the documented F-06 requirement that completion of one concurrent task does not move the other session to another task.

### Project B isolation

Path:

`C:\Projects\Vres-F06-163-B-20260928`

Project key:

`project:94de0216d177f194d13de76b`

DELTA:

- task: `TASK-20260928-82441fc165`
- B1 provider session: `1ba464b6-2439-4e29-9810-fceeebfe5126`
- checkpoints: `CP-20260928-094a7ed49d` -> `CP-20260928-ead67184b8`
- decision: `DEC-20260928-e095178b5e`
- marker: `F06-DELTA-163-20260928`
- marker grep exit: 0

Project-B attempts against Project-A ALPHA were rejected before mutation:

`Object is outside the current project; cross-project/global writes require separate authorization`

This applied to:

- explicit resume/bind;
- checkpoint/write attempt.

Project-B local knowledge lookup for the ALPHA marker returned none.

Project-B project-agent lookup returned none.

ALPHA/BETA were not mutated by those rejected attempts.

### Formal F-06 outcome

The documented F-06 contract requires:

- distinct task/session bindings;
- clear/completion must not jump tasks;
- ambiguity surfaced rather than recency guessing;
- live concurrent sessions not falsely closed;
- project-local state/agents/knowledge do not leak cross-project.

The combined accepted live evidence satisfies all five.

F-06: **PASS**.

---

# 9. Auto Mode / evidence observations from F-06

During ALPHA reconciliation, several `task_checkpoint` / reply-gate attempts were temporarily denied by the Claude host Auto Mode classifier with a “no verdict” style permission failure.

A later checkpoint attempt succeeded:

`CP-20260928-9f3fc71621`

This is an environment/host observability note, not a #163 product failure:

- the failed attempts did not mutate state;
- a later normal attempt persisted;
- the issue did not block the required F-06 behavioral proof.

Do not open a #163 source correction solely because of this transient denial unless it becomes reproducible under ordinary governed operations.

There is also a possible future observability improvement: read-only ambiguity decisions do not leave a durable task-event audit row. If stronger historical auditability is desired, create a separate bounded issue later; do not retroactively add it to #163 acceptance.

---

# 10. #163 merge and closure

PR #173 was verified immediately before merge:

- state: open
- mergeable: true
- base: `f0a69c3e471fe25c6547ee1af162019caf290d49`
- exact accepted head: `4baf4fadbbd402a0dd523837924e6436f74f27d1`
- exact-head CI #407: success

Merged with expected-head protection.

Merge commit:

`7f9961b5980f1a229cece4902f9e1d709e397e22`

Post-merge main CI #438 then passed completely.

Issue #163 was closed only after that post-merge success.

Closure comment explicitly preserved #169 physical criteria.

#163 is DONE and must remain closed unless a genuinely new regression is found.

---

# 11. #169 criteria explicitly deferred from #163

Do not claim these as already physically proven:

1. real Windows Credential Locker under User A;
2. Project A/B reuse without credential re-entry;
3. unbound Project C denial;
4. real child-only environment delivery while parent stays clean;
5. actual Claude transcript/debug behavior for a blocked synthetic credential;
6. a second real Windows user cannot see/reuse User A's credential;
7. uninstall/reinstall preserves native Claude/Codex login state.

These belong to #169 integrated Windows / Visual Studio live acceptance after all build tranches are merged.

---

# 12. Disposable acceptance-project state

The F-05/F-06 directories are disposable acceptance projects, not the Vres product repository.

They intentionally contain synthetic marker changes and may contain generated `CLAUDE.md` files.

Do **not** merge those fixture changes into Vres-OS.

Do not delete the evidence projects blindly until the relevant acceptance record is safely durable and no later troubleshooting needs them.

The #163 product candidate itself was kept untouched during the live acceptance ladder and merged from the accepted exact head.

---

# 13. Final #174 Engineering Architecture Governance evidence

Issue:

**#174 — Engineering Architecture Constitution and Fable-validated adoption planning foundation**

PR:

**#175**

Accepted integration identity:

- original held head: `9756b44d4ae953db327b10072e70003e51df9404`
- integrated exact candidate: `7ded3c16e5e85f5715fb052f403907eec3750628`
- integrated base/main: `7f9961b5980f1a229cece4902f9e1d709e397e22`
- merge commit / current main: `11591b72b3d396a370e315313925e19b8bcb45ec`

Integration was history-preserving and retained the exact #174 21-path scope. #163 runtime/security files remained behaviorally unchanged.

Important bounded integration corrections completed before acceptance:

- the architecture audit excludes Vres-owned `.vres` state entirely, including `.vres/local-secrets`;
- regression coverage proves source-looking files under `.vres/local-secrets` are not read and cannot affect inventory/dependency/findings/audit digest;
- the C7 security carve-out is explicit: normal Vres/architecture UX remains Chairman-led/conversational, while credential capture/confirm/bind/discard/save actions requiring hidden local input or explicit authority remain user-run local-terminal safety-boundary operations; Chairman must not auto-authorize them or automatically pass `--yes`;
- inherited Markdown trailing whitespace was cleaned rather than weakening `git diff --check`.

Local Phase 3 final evidence:

- targeted architecture/#163 integration family: **67 passed / 0 skipped / 0 failed**;
- lint gates: PASS;
- CI-equivalent isolated full PostgreSQL suite: **1087 passed / 3 skipped / 0 failed / 0 errors**;
- installed-runtime smoke: PASS;
- release gate: `PASSED_WITH_EXPLICIT_LIVE_GATES`.

The reusable local test DSN remains stored by handle:

`pg_issue163_test_dsn`

Do not print or export its value.

Exact-head CI:

- run #439 / `36455460478`;
- exact head `7ded3c16e5e85f5715fb052f403907eec3750628`;
- conclusion: **success**.

Final canonical protected acceptance:

- request: `VAL-aa05bb6018e941cc`;
- validator: `vres-os:validator`;
- pinned assurance: Fable/high;
- host-observed model: `claude-fable-5-1`;
- exact reviewed head: `7ded3c16e5e85f5715fb052f403907eec3750628`;
- result: **PASS**.

Phase 5 forensics also reconfirmed the previously accepted #42 protected-validation protocol. Earlier stale/superseded validation attempts were caused by post-`validation_prepare` Chairman task mutations. The authoritative Phase 5B run followed the correct sequence: final checkpoint before preparation, no task-state mutation while validation was in flight, interim reply only through `task_reply_gate(advances_state=false)` with `mode=validation_in_flight`, then read-only host-attestation verification. No #174 code defect was found in that lifecycle surface.

PR #175 was merged with expected-head protection.

Post-merge main CI:

- run #440 / `36530581547`;
- head `11591b72b3d396a370e315313925e19b8bcb45ec`;
- conclusion: **success**;
- PostgreSQL suite, installed-runtime smoke, release gate and evidence upload all PASS;
- artifact `11016787086`;
- digest `sha256:59e506706a168648057860d8e683816940973a512440c09c253228296d5abedf`.

Issue #174 is DONE and must not be reopened without a genuinely new regression.

---

# 14. Final #174 shipped architecture foundation

Authoritative main now contains:

- versioned Engineering Architecture Constitution;
- proportional architecture profiles;
- Chairman-only architecture UX;
- deterministic read-only architecture audit;
- stable architecture finding IDs;
- existing-project alignment-plan contract;
- exact `audit_digest`;
- exact `plan_digest`;
- mandatory protected Fable/high validation before architecture-changing adoption activation;
- no-giant-rewrite / reversible strangler principle;
- architecture-aware project CLAUDE scaffold;
- architecture MCP/internal tools;
- architecture governance tests and CI contracts.

It does **not** own:

- #168 full fresh/legacy adoption state machine;
- KEEP/DROP activation;
- canonical scaffold migration engine;
- #169 final physical Windows acceptance.

Preserve those boundaries.

---

# 15. Final #164 secret-safe onboarding evidence

#164 closed the legacy-project secret-ingestion gap without reducing required onboarding functionality.

Final product/security contract:

- known sensitive paths are classified before ordinary hash/extraction;
- excluded files retain only bounded non-secret provenance;
- useful mixed documents are sanitized before classification, persistence, chunking, embeddings or model-facing review;
- suspicious residual credential forms fail closed to `sensitive_review_required`;
- raw secret spans/values are not persisted;
- sanitized records do not persist the raw-file SHA-256;
- existing Credential Broker remains the only durable secret architecture;
- semantic embeddings remain available when enabled;
- configured embedding model identity comes only from trusted Vres configuration;
- local cache is preferred and the same configured model may be acquired when absent;
- `trust_remote_code=False`;
- legacy/project content cannot select a model or authorize arbitrary network activity;
- only sanitized persisted chunks reach local embedding inference;
- source files remain untouched.

Final validation identity:

- task: `TASK-20260929-03eade4905`;
- candidate: `eddfa35d5418e23d6bac8792df0a6d1877d880a8`;
- governed final: `ORCHFINAL-20260929-9bf6f3cc85` / `decision_ready=true`;
- exact-head CI: #441 / `36542621233` SUCCESS;
- protected validation: `VAL-f8d685ab3575430c` PASS;
- observed validator: `claude-fable-5-1`;
- merge/main: `fe31e30e593a44b8b5ab565fa0db859bbefec0c6`;
- post-merge CI: #442 / `36544341349` SUCCESS.

Deferred live criteria:

- real first-run SentenceTransformer acquisition with actual optional dependencies;
- sanitized wizzard_9 project live onboarding;
- target Windows/Visual Studio integrated proof.

Those are not implementation blockers for #176 and remain owned by #169 / the corresponding live runtime case.

---

# 16. #174 closure evidence is final

Do not reuse pre-integration #174 evidence as if it were the final acceptance record.

Superseded baseline only:

- held head `9756b44d4ae953db327b10072e70003e51df9404`;
- old CI #437 / `36349196127`.

Final accepted evidence:

- integrated head `7ded3c16e5e85f5715fb052f403907eec3750628`;
- exact-head CI #439 / `36455460478` SUCCESS;
- protected validation `VAL-aa05bb6018e941cc` PASS;
- host-observed `claude-fable-5-1`;
- merge/main `11591b72b3d396a370e315313925e19b8bcb45ec`;
- post-merge CI #440 / `36530581547` SUCCESS.

This is the authoritative #174 closure identity.

---

# 17. Active next item — #176 E3 unified experience retrieval

#176 remains the only allowed implementation issue.

Completed foundations:

- #163 Credential Broker — DONE;
- #164 secret-safe onboarding / pre-model sanitization — DONE;
- #174 Engineering Architecture Governance — DONE;
- #176 E1 contracts + episode ledger — DONE;
- #176 E2 transition verifier + safe consolidation — DONE.

The next and only allowed tranche is **E3 — unified experience retrieval**.

E3 must consume the existing truth owners rather than introduce another memory authority:

- task decisions / current rules;
- existing `knowledge_items`, including only lifecycle-eligible E2 proposed lessons according to the retrieval contract;
- accepted procedures;
- E1 episodes where specific precedent adds value;
- relations/evidence links;
- source/artifact/raw archive only through bounded fallback.

Frozen E3 design requirements from issue #176:

1. determine current project/task/capability/domain/scope and temporal intent;
2. apply hard scope/authority/security filters **before** semantic retrieval;
3. retrieve current decisions/rules;
4. retrieve matching accepted procedures;
5. retrieve relevant semantic lessons/gotchas/premise warnings;
6. retrieve only a small number of relevant episodes when concrete precedent helps;
7. detect conflicts, stale assumptions and premise mismatch;
8. use bounded raw-evidence/archive search only when structured memory is insufficient;
9. compose one compact experience pack.

Hybrid retrieval may use:
- exact/structured filters;
- lexical search;
- optional embedding similarity;
- relations/graph links;
- temporal validity/recency;
- applicability/task-family/capability match;
- evidence/authority status;
- diversity / duplicate suppression.

A retrieval score is never a probability of truth or authority.

Retrieval must not silently rewrite, promote, supersede or otherwise mutate the memory it consumes. Retrieval-triggered challenge/reverification/consolidation proposals belong to later governed lifecycle behavior, not hidden E3 side effects.

Do not begin E4 until E3 is bounded, implemented, tested, evidenced, protected-reviewed where required, merged and post-merge green.

Do not begin #165 until all of #176 is DONE.

---

# 18. Experience Intelligence plan is frozen and now active

Issue #176 implementation is now allowed because all prerequisites are DONE.

Durable plan:

- branch: `docs-176-experience-intelligence-plan-20260927`;
- commit / branch head: `34f45afa0fb8d5a6a90bef53dec58d9ecef1093d`;
- file: `docs/architecture/EXPERIENCE-INTELLIGENCE-PLAN-2026-09-27.md`.

Core principles:

> **Models are replaceable workers. Vres owns the experience.**

> **Store evidence richly. Retrieve context sparsely. Promote authority conservatively.**

E1 and E2 are now complete. Implementation continues only with **E3 — unified experience retrieval**. The broader E3→E8 order remains frozen; E9 physical acceptance stays in #169.

---

# 19. User interaction / operator methodology

For live Windows development/acceptance steps, the user prefers:

- **one PowerShell block per stage**
- **one Claude prompt block per stage**

Do not scatter a stage across many command snippets unless absolutely necessary.

Keep Vres product interaction conversational.

Normal user-facing controls remain:

- `start vres`
- native `clear`

Chairman should handle internal Vres machinery.

Final #169 testing will be performed through the user's Visual Studio / integrated workflow, not treated as a PowerShell-only product experience.

---

# 20. Git and validation discipline

For each issue:

1. verify authoritative main;
2. read issue + handoff + checklist;
3. verify exact branch/head;
4. inspect existing implementation before editing;
5. make only the current issue's smallest robust changes;
6. run targeted tests;
7. run full integration suite where required;
8. run protected Fable/high when required;
9. update docs/handoff;
10. require exact-head CI;
11. merge only after all gates;
12. verify post-merge main CI;
13. close issue;
14. update checklist/handoff;
15. only then move to the next item.

Do not combine multiple issue tranches for convenience.

---

# 21. Current documentation branch

Canonical checklist/handoff branch:

`docs-execution-checklist-20260927`

During the 2026-09-29 #164 closeout:

- #164 candidate `eddfa35d5418e23d6bac8792df0a6d1877d880a8` passed exact-head CI #441;
- protected validation `VAL-f8d685ab3575430c` passed with host-observed `claude-fable-5-1`;
- PR #177 merged as `fe31e30e593a44b8b5ab565fa0db859bbefec0c6`;
- post-merge main CI #442 passed;
- issue #164 was closed completed;
- checklist was updated to mark #164 DONE and activate #176;
- this handoff was rewritten to the #176 continuation boundary.

These documentation changes are direct Git commits on the documentation branch. Product main is authoritative for runtime code; this branch is the durable execution ledger/handoff and must not be merged blindly merely to copy planning text.

---

# 22. Exact next-session mission

A fresh ChatGPT continuation session must begin from the latest seal in section 27, not from the older E1/E2 start text preserved for history.

Current mission:

> Resume Vres preproduction at #176 E3. E1 and E2 are DONE. Product main remains `74c6445228a922db2622806f27e3c49a6c3454a7`. The E3 Windows worktree is `C:\Projects\Vres-Issue-176-E3-20260929`, branch `issue-176-e3-unified-experience-retrieval`, task `TASK-20260929-9c9d52b7e5`. The frozen E3 contract is local commit `c03b2c269c4118d47b39c4c3236fc106412b4d3b`; Chunk 1 is local commit `ff025a8a738062c3453d34cb045c5abf005db7f3`. Neither commit has been pushed and GitHub currently has no remote E3 branch. The already-dispatched next step is **Chunk 1 hardening**, not Chunk 2. Review the current Claude result when it returns. Close the broad read-time `_INJECTION` misuse, confirm procedure-query ownership, account for all Chunk 1 tests 1–20, rerun the accepted isolated PostgreSQL/no-write methodology, and require a separate hardening commit. Only after that passes may E3 Chunk 2 begin. Do not start E4. Do not start #165+ until #176 is fully DONE. New unrelated requests go after #170 unless they are current-tranche blockers.

This is the exact continuation point.

# 23. Handoff integrity

Do not rely on old chat summaries when Git/GitHub disagree.

Authoritative hierarchy:

1. current Git/GitHub state;
2. current canonical checklist;
3. this current handoff;
4. issue/PR-specific handoffs;
5. historical handoffs/chat summaries.

When an issue becomes DONE, update the checklist and handoff again before moving on.


---

# 24. 2026-09-29 session seal

This section is the final chat/session boundary after #164 closeout.

## Authoritative repository state

- repository: `vosser24/Vres-OS`;
- authoritative `origin/main`: `fe31e30e593a44b8b5ab565fa0db859bbefec0c6`;
- PR #177: merged;
- issue #164: closed / completed;
- post-merge CI #442 / `36544341349`: SUCCESS;
- next open implementation issue: #176;
- #176 frozen plan branch/head: `docs-176-experience-intelligence-plan-20260927` @ `34f45afa0fb8d5a6a90bef53dec58d9ecef1093d`.

## #164 local task housekeeping

The #164 implementation task is:

`TASK-20260929-03eade4905`

The chat contains authoritative protected PASS and repository closure evidence, but it does **not** contain a confirmed final read-back showing that `task_complete` was actually executed after the external merge/post-merge closeout.

Therefore a future operator should **not guess**:

1. in the old #164 worktree/session, read the task status first;
2. if it is already completed, do nothing;
3. if it is still active and the original exact candidate worktree remains at the reviewed head with the accepted validation current, complete only that historical task without reopening #164 product work;
4. do not checkpoint or mutate the old task merely to narrate closure;
5. do not use that historical task as the #176 task.

This housekeeping does not block #176 repository work because #164 product acceptance, merge, post-merge CI and issue closure are already complete.

## Fresh #176 session start

Preferred clean worktree:

`C:\Projects\Vres-Issue-176-Experience-Intelligence-20260929`

Start from exact authoritative main:

`fe31e30e593a44b8b5ab565fa0db859bbefec0c6`

Before source edits:

1. fetch/prune origin and verify `origin/main` exact SHA;
2. read the canonical checklist and this handoff;
3. read issue #176 in full;
4. read the frozen plan at commit `34f45afa0fb8d5a6a90bef53dec58d9ecef1093d`;
5. inspect current Vres truth owners before adding schema/services;
6. create a dedicated #176 branch/worktree from authoritative main;
7. begin only **E1 — contracts + episode ledger**;
8. freeze E1's smallest bounded contract before editing;
9. do not begin E2 until E1 implementation/tests/evidence are complete;
10. do not start #165 or any later issue.

## E1 non-negotiable boundaries

E1 must:

- add only missing experience-specific primitives;
- reuse task/checkpoint state, decisions, knowledge, procedures, capabilities, relations, sources, artifacts, work reports and validation as existing truth owners;
- keep execution state separate from long-term experience;
- persist no raw hidden chain-of-thought;
- derive episodes only from mechanically known/sanitized evidence;
- retain project/scope/trust/source/digest provenance;
- capture meaningful failures as failures, never silently as positive procedures;
- preserve #163 Credential Broker and #164 secret-safe ingestion boundaries;
- preserve #174 architecture/governance rules;
- add PostgreSQL migration only when required by the E1 data contract;
- include malformed/corrupt payload fail-closed tests, scope isolation, provenance/digest checks, secret/injection negative proofs and rollback/idempotency appropriate to durable writes.

## Deferred live evidence still owned by #169

Do not lose these carried criteria:

- real Windows Credential Locker/current-user isolation;
- real first-run SentenceTransformer configured-model acquisition;
- sanitized wizzard_9 legacy-project onboarding;
- target Windows/Visual Studio integrated project adoption;
- Experience Intelligence E9 live proof after E1–E8 are merged;
- final production/go-live evidence remains #170.

## Fresh-session resume prompt

Use the exact mission in section 22, with this session-seal section as the most recent operational clarification.



---

# 25. 2026-09-29 #176 E1 closure / E2 continuation seal

This section supersedes older E1-start instructions elsewhere in this historical handoff.

## Authoritative repository state

- authoritative main: `407c4a323f4f65c8f28c422789508bb7ce128682`;
- PR #179: merged;
- E1 protected-reviewed head: `bc03707c9cef77967cc1abd2ffe0733d4393b42c`;
- E1 task: `TASK-20260929-7e344a1e68`;
- freeze checkpoint: `CP-20260929-7c91c106e4`;
- protected validation: `VAL-b7d08edab1c74e98` — PASS;
- validator/model: `vres-os:validator` / host-observed `claude-fable-5-1`;
- exact-head CI #454 / `36557839748`: SUCCESS;
- merge commit: `407c4a323f4f65c8f28c422789508bb7ce128682`;
- post-merge main CI #455 / `36560731741`: SUCCESS;
- post-merge suite: **1186 passed / 1 skipped**;
- installed-runtime smoke: PASS;
- release gate: `PASSED_WITH_EXPLICIT_LIVE_GATES`;
- post-merge artifact: `11028544812`;
- post-merge artifact digest: `sha256:047cbd0fa0ed34c38ab14e98f44fa07f0a7ca22d4039ff265a07340405f841a0`.

## E1 status

E1 contracts + immutable episode ledger: **DONE**.

Accepted E1 additionally proves:
- versioned experience policy is database-immutable;
- complete accepted source evidence is sanitized/digested before compact projection;
- work-unit episodes do not inherit task-wide validation authority;
- work-unit episodes retain only directly attributable evidence plus stable task identity/objective and direct capabilities;
- project/scope isolation, provenance, failure integrity, concurrency/idempotency and relation evidence remain bounded;
- no E2+ behavior was smuggled into E1.

Issue #176 remains open because E2–E8 remain.

## Exact next implementation tranche

**E2 — transition verifier + safe consolidation.**

Before E2 source edits:
1. verify `origin/main` exactly equals `407c4a323f4f65c8f28c422789508bb7ce128682`;
2. read the canonical checklist, this section, issue #176, the frozen plan and merged E1 contract;
3. inspect E1 tables/service plus knowledge/procedure/capability/decision/relation truth owners;
4. create a dedicated E2 branch/worktree from authoritative main;
5. freeze E2's bounded contract before implementation;
6. implement only transition verification + safe consolidation;
7. no E3 retrieval implementation yet;
8. keep untrusted/external observations non-authoritative;
9. preserve source/scope/trust/digest/failure provenance and revocation compatibility;
10. use protected Fable/high when the E2 governance/security boundary requires it;
11. require exact-head CI, guarded merge and post-merge main CI before E3.

#165 and later issues remain blocked until all of #176 is DONE.


---

# 26. 2026-09-29 #176 E2 closure / E3 continuation seal

This is the newest authoritative session boundary and supersedes older E1/E2 start instructions elsewhere in this historical handoff.

## Authoritative repository state

- repository: `vosser24/Vres-OS`;
- authoritative main: `74c6445228a922db2622806f27e3c49a6c3454a7`;
- PR #180: merged;
- issue #176: open;
- E1: DONE;
- E2: DONE;
- E3: NEXT / NOT STARTED;
- #165+ remain blocked until #176 is fully DONE.

## Final E2 validation and merge evidence

Final protected candidate:
`c1dccfa800381b1f5b01fd054cb3819720600e2a`

Historical protected failure:
`VAL-84afc8fa56a245bf` — FAILED, preserved.

Final protected acceptance:
- request: `VAL-58bb131a10b54abd`;
- validator: `vres-os:validator`;
- host-observed model: `claude-fable-5-1`;
- result: PASS.

Exact-head CI:
- #461 / `36585887143`;
- candidate: `c1dccfa800381b1f5b01fd054cb3819720600e2a`;
- status: SUCCESS;
- artifact: `11042340684`;
- digest: `sha256:afb432d024f1647586b0d0d2e239c34fda2845344f1549ab973ce8996d82eaa8`.

Merge:
- expected-head guarded merge of PR #180;
- main merge commit: `74c6445228a922db2622806f27e3c49a6c3454a7`.

Post-merge:
- CI #462 / `36589408835`;
- event: push to main;
- exact main SHA: `74c6445228a922db2622806f27e3c49a6c3454a7`;
- status: SUCCESS;
- PostgreSQL integration: PASS;
- installed-runtime smoke: PASS;
- release gate: PASS;
- artifact: `11042962873`;
- digest: `sha256:082fdc00743b212dd7f3fb30c9de451b943274e755d8f6b81bc4624a3e0a1ab6`.

## E2 accepted product boundary

E2 owns:
- deterministic transition verification from E1 evidence;
- exact source/payload digest checks;
- RFC 6901 pointer + literal quote support checks;
- failure-integrity rules;
- participation/trust quarantine;
- recurrence quarantine until later replay calibration;
- proposed/project-local lesson creation only;
- dedupe and conflict preservation;
- immutable append-only transition audit;
- atomicity/idempotency/concurrency/rollback.

E2 does not own:
- retrieval or ranking;
- experience packs;
- revocation/supersession lifecycle;
- capability/procedure integration;
- retrieval observations;
- benchmark program;
- Chairman automatic memory injection.

Those remain E3–E8.

## E2 task housekeeping

E2 Vres task:
`TASK-20260929-9fdfbe76eb`

The repository tranche is closed. If the local Vres task is still active, complete only that historical E2 task using its current accepted protected validation; do not reuse it as the E3 task. Do not add a new checkpoint merely to narrate GitHub closure unless Vres lifecycle itself requires one.

## Exact E3 start

Create a new E3 task/branch/worktree from authoritative main `74c6445228a922db2622806f27e3c49a6c3454a7`.

Recommended worktree:
`C:\Projects\Vres-Issue-176-E3-20260929`

Before implementation:
1. read issue #176 and frozen plan completely;
2. read merged E1 and E2 contracts/services/tests;
3. inspect current `KnowledgeService`, procedure matching, task decisions, relations, existing `KnowledgeService.hybrid_search` / embedding behavior and raw-source search;
4. freeze the E3 retrieval contract before code;
5. define authority/scope/temporal/premise/conflict filters before ranking;
6. define a bounded experience-pack budget and evidence-key output;
7. specify abstention / no-useful-precedent behavior;
8. specify deterministic ordering/tie-breaks where deterministic;
9. specify no-write/no-reconsolidation side effect during E3 retrieval;
10. define targeted and PostgreSQL retrieval tests before E4.

Do not start E4 until E3 is fully closed.
Do not start #165 until #176 is fully closed.


---

# 27. 2026-09-29 #176 E3 contract + Chunk 1 / hardening continuation seal

This is the newest authoritative session boundary. It supersedes older E3-start instructions elsewhere in this historical handoff.

## A. Authoritative product/repository state

- repository: `vosser24/Vres-OS`;
- authoritative product `main`: `74c6445228a922db2622806f27e3c49a6c3454a7`;
- issue #176: open;
- E1: DONE;
- E2: DONE;
- E3: ACTIVE;
- E4–E8: NOT STARTED;
- #165+ remain blocked until #176 is fully DONE;
- canonical docs branch: `docs-execution-checklist-20260927`.

## B. Current E3 local worktree identity

Windows worktree:

`C:\Projects\Vres-Issue-176-E3-20260929`

Branch:

`issue-176-e3-unified-experience-retrieval`

E3 task:

`TASK-20260929-9c9d52b7e5`

Authoritative base:

`74c6445228a922db2622806f27e3c49a6c3454a7`

Frozen plan source:
- branch: `docs-176-experience-intelligence-plan-20260927`;
- commit: `34f45afa0fb8d5a6a90bef53dec58d9ecef1093d`;
- file: `docs/architecture/EXPERIENCE-INTELLIGENCE-PLAN-2026-09-27.md`.

The local Claude environment did not have `gh.exe`; it used the frozen Git plan. The connected GitHub review outside that local session independently checked live issue #176 and found no material E3 requirement missing from the frozen plan. Do not treat lack of local `gh.exe` as permission to guess current issue state.

## C. E3 contract/discovery completed

Frozen E3 contract:

`docs/architecture/EXPERIENCE-INTELLIGENCE-E3-CONTRACT-2026-09-29.md`

Local contract commit:

`c03b2c269c4118d47b39c4c3236fc106412b4d3b`

Status:
- discovery/contract: PASS;
- no missing schema primitive found;
- no migration planned;
- no second memory/vector store;
- commit is **local only**;
- no remote E3 branch exists yet;
- no PR exists yet.

The contract owns staged, scope-first, trust-aware unified retrieval over existing decisions, knowledge, procedures and E1 episodes; bounded experience packs; explicit conflict/staleness/premise handling; optional semantic/graph/time signals; bounded raw-evidence fallback; no truth-probability interpretation of relevance; no retrieval-time memory mutation.

## D. E3 Chunk 1 implementation checkpoint

Chunk 1 local commit:

`ff025a8a738062c3453d34cb045c5abf005db7f3`

New files:
- `src/vres_os/experience_retrieval.py`;
- `tests/test_experience_retrieval.py`;
- `tests/integration/test_experience_retrieval_journey.py`.

Routing/orchestration:
- governed route recorded;
- one worker only;
- routed specialist role: `cto`;
- execution tier: Sonnet;
- visible executor shell: `vres-os:sonnet-expert`;
- assurance: routine;
- no work graph;
- no `work_unit_key` was therefore supplied; the worker report's empty criteria list is not by itself a Chunk 1 defect;
- Chairman independently reran the worker's tests before committing.

Chunk 1 evidence already obtained:
- targeted unit + regression suite: **97 passed** = 39 new + 58 existing regression tests;
- fresh disposable PostgreSQL 18 E3 journey: **14 passed**;
- existing E1/E2 integration journeys on the fresh DB: **19 passed**;
- repository-critical lint for changed surface: PASS;
- `git diff --check`: PASS;
- migration added: NO;
- no-write proof: row counts + md5 digests for 11 relevant tables unchanged before/after retrieval;
- retrieval transaction is read-only and attempted INSERT/UPDATE fail with `ReadOnlySqlTransaction`;
- retrieval-observation rows are not written in E3 Chunk 1.

## E. Current Chunk 1 open findings

The next step is **not Chunk 2 yet**.

Current bounded defect requiring hardening:

1. E3 reused E2's broad write-time `experience_consolidation._INJECTION` regex during retrieval. That regex deliberately catches broad authority/instruction words such as `policy` and `approved`; using it as a read-time suppression rule can hide legitimate benign historical/business memory. E3 must preserve trust/instruction boundaries without treating ordinary vocabulary as sufficient reason to drop otherwise eligible evidence.

Additional hardening review items:

2. Procedures currently use one E3 scoped read query instead of `ProcedureService.find_matches`; the reason reported is that `find_matches` opens its own connection and lacks the E3 scope gate. Preserve the procedure lifecycle owner and avoid semantic fork/duplication.
3. Map every original Chunk 1 requirement 1–20 to exact unit/integration tests. Do not add redundant integration tests purely for numbering, but no requirement may remain genuinely untested.
4. Features intentionally deferred beyond Chunk 1 are not defects: challenged/conflict output, premise evaluation, semantic/embedding signal, raw-chunk fallback, MCP tool, and Chairman integration.

A bounded Chunk 1 hardening prompt has already been dispatched in the live Claude session. Await and review that result. The hardening prompt requires a separate commit after `ff025a8...` and explicitly forbids starting Chunk 2 automatically.

## F. Accepted testing methodology — preserve exactly

These rules are now part of the continuation contract because earlier sessions exposed avoidable tooling/syntax mistakes.

### Windows PowerShell execution

- Assume **Windows PowerShell 5.1** unless the user explicitly says otherwise.
- Prefer **one PowerShell block per stage** and **one Claude/Chairman prompt per stage**.
- Wrap multi-step pasted blocks in `& { ... }` so a `throw` terminates the whole pasted block. Do not print a later false `PASS` after an earlier STOP.
- After any STOP, inspect the actual partial state and continue from it. Do not blindly rerun an idempotency-sensitive patch.
- Avoid fragile inline `python -c` quoting from PowerShell for nontrivial probes. Use a temporary UTF-8 `.py` file and, when importing unmerged source, set `PYTHONPATH` explicitly to the worktree `src` directory; restore the environment afterward.
- Do not infer a sandbox/local path that was not actually established.

### Git hygiene

- Verify branch, local HEAD, remote HEAD/main and clean/expected change surface before mutation.
- Use race guards before push/merge.
- Never force-push this workflow.
- Run `git diff --check` before candidate freeze/commit. Trailing whitespace and blank-line-at-EOF findings are real candidate hygiene defects and must be fixed before protected validation.
- If a command providing evidence fails, STOP. Do not continue to print a success banner.
- A new commit, including documentation-only cleanup, changes candidate identity; exact-head CI/validation evidence on the previous SHA becomes historical.

### Lint discipline

- Do not suddenly enforce unrelated repo-wide style debt while fixing one lint finding.
- Current CI-critical Ruff contract is `E9,F63,F7,F82` plus any specifically relevant bounded rule such as `F541` or `I001` when that rule is the defect under review.
- Do not turn existing E501/formatting debt into unrelated source churn unless the current tranche explicitly owns that cleanup.

### PostgreSQL integration

- Use a **fresh disposable PostgreSQL database** and an empty/isolated `VRES_DATA_DIR` for acceptance journeys.
- Do not use the historically contaminated shared test DB as an acceptance baseline when its migration checksum/policy/provenance state differs from the candidate.
- Where relevant, clear/avoid inherited `VRES_DATABASE_URL`, `VRES_PROVENANCE_WRITER_DATABASE_URL` and `VRES_MIGRATION_DATABASE_URL` before an isolated validator-side broad-suite rerun.
- Preserve real DB/test exit codes; do not pipe away the exit code of commands used as evidence.
- For read-only retrieval, prove no-write structurally and with before/after durable-state evidence, not only by code inspection.

### Test/evidence interpretation

- A targeted suite PASS proves only its named surface. Do not call the whole tranche complete from targeted tests.
- Map requested acceptance criteria to concrete tests before closing a chunk.
- Separate unit evidence, PostgreSQL journey evidence, full-suite evidence, installed-runtime smoke, release gate, protected validation and physical/live acceptance.
- Do not repeat already-green expensive suites without a changed candidate or a specific evidence gap.

### Exact-head CI and merge

- Before final protected acceptance, require fresh CI on the exact candidate SHA.
- Capture run number/id, exact head, event, conclusion, required step status, artifact id and digest.
- If the protected validator cannot reach GitHub, create a bounded local evidence file by directly querying GitHub's public REST API **before the final freeze**, verify exact run/head/steps/artifact/digest, and give that read-only evidence file to the validator. Do not rely only on relayed prose.
- Merge with an expected-head SHA guard only after exact-head CI and required protected validation PASS.
- After merge, require a new `push` CI run on the exact merge/main SHA before marking the tranche DONE.

### Protected validation #42 lifecycle

- Make exactly one final material checkpoint **before** `validation_prepare`.
- Freeze exact artifact list + exact reviewed Git SHA.
- After `validation_prepare`, do not mutate task/checkpoint/decision/orchestration state while validation is in flight.
- Interim status reply only through `task_reply_gate(... advances_state=false)` and only if it returns `mode=validation_in_flight`.
- Delegate exactly `vres-os:validator`; do not manually override the protected model.
- Read host evidence first after validator completion: fresh VAL id, terminal status/report/completed_at, host-observed Fable-family model, exact reviewed head/hashes, task validation status.
- Validator prose alone is insufficient.
- If stale/rejected/wrong model/wrong SHA/non-terminal/failed, STOP and report durable evidence. Do **not** retry automatically.

## G. Role/executor identity clarification discovered during E3

Do not confuse organizational role with executor shell/model tier.

Current Chunk 1 identity:
- routed role = `cto`;
- execution tier = Sonnet;
- canonical executor shell = `vres-os:sonnet-expert`.

Vres already persists role separately from execution tier/model. The generic Sonnet/Opus shell name leaking into visible status is a later UX/organizational-observability concern, not an E3 blocker.

## H. New-request sequencing rule / queued post-#170 work

User rule:

> New requests discovered during the active frozen pipeline are appended to the end unless they are a genuine blocker/defect in the current tranche.

Therefore do not insert the following into #176 or #165–#170:

**Post-#170 Organizational Architecture & Specialist Intelligence audit.**

That future audit must recover the **original Agent Board from the earliest project conversation/design artifacts**, not infer the target organization from the current repo's reduced executive roster. The user specifically recalls that every key Director had a fuller departmental structure and Technology/IT was a full software organization with product-owner/product-design and specialist engineering roles. The future audit must reconstruct the original department -> Director -> role -> specialist hierarchy, compare it with current implementation, identify lost vs intentionally consolidated roles, improve specialist display identity, and add role/capability/department performance attribution without fabricating quality scores.

This queued item is after #170 and must not interrupt the current pipeline.

## I. Fresh-chat first action

When the current Chunk 1 hardening result arrives, paste that exact Claude output into the new ChatGPT session.

The new session must:
1. read this section 27 first;
2. verify authoritative Git/GitHub state before claiming anything remote;
3. remember that `c03b2c...` and `ff025a8...` are local-only unless the user subsequently pushed them;
4. review the hardening report against the bounded defect/test matrix;
5. if hardening PASS is real, record the hardening commit and then design/authorize E3 Chunk 2;
6. if hardening finds a defect, stay in Chunk 1 and fix only that defect;
7. do not recreate the E3 task, contract or Chunk 1;
8. do not start E4 or any later issue.


---

# 28. 2026-10-02 #176 E4 migration-040 pre-validation / ChatGPT-primary continuation seal

This is the newest authoritative handoff boundary. It supersedes section 27 and all older E3/E4 start instructions for current execution state. Historical evidence remains historical and must not be rewritten.

## A. Exact current repository / Vres boundary

Repository:
`vosser24/Vres-OS`

Authoritative remote product main:
`ddb0719d130fd45b12b6bdc9e1682378ace7ae64`

That main is the accepted E3 merge commit. E4 is not merged yet.

E4 Windows worktree:
`C:\Projects\Vres-Issue-176-E4-20260930`

E4 branch:
`issue-176-e4-temporal-lifecycle-revocation`

E4 Vres task:
`TASK-20260930-2c7198e394`

Latest local Vres checkpoint:
`CP-20261002-b2e09a2047`

Final migration-040 docs-complete E4 candidate:
`ce9067ab36716cb1f729466db168d002e1029c93`

Final tree:
`5cf813f19feb36e23f59dc6ddf632c38ac09e869`

Remote branch verification performed by ChatGPT on 2026-10-02:
- branch exists remotely;
- remote branch HEAD == `ce9067ab36716cb1f729466db168d002e1029c93`;
- no E4 PR existed at that verification point;
- remote `main` remained `ddb0719d130fd45b12b6bdc9e1682378ace7ae64`.

Do not infer later PR/CI state from this handoff; verify live GitHub state at fresh-chat start.

## B. E4 implementation status

E4 A–G implementation is complete and the migration-040 pre-validation integrity closure is complete.

Accepted/frozen architecture now includes:
- append-only experience lifecycle ledger;
- retirement/challenge/supersession/reinstate/refresh lifecycle primitives;
- provenance-driven source revocation and multi-source support handling;
- JSON + pgvector embedding invalidation/rebuild protections and stale-worker fencing;
- E4 lifecycle-aware E3 retrieval / pack `176.e4.v1`;
- contaminated-session enforcement, Stop reporting and serialized session-open/revocation ordering;
- MCP tools `source_revoke`, `knowledge_lifecycle`, `context_refresh_ack`;
- protected context-refresh attestation via migration 040;
- revoked-only company support exclusion across all current read paths.

Frozen base E4 contract:
- commit: `a69b836fa3fbf6a97c00f830b05495c48c5af563`;
- file: `docs/architecture/EXPERIENCE-INTELLIGENCE-E4-CONTRACT-2026-09-30.md`;
- current candidate keeps that frozen file unchanged.

Migration-040 contract amendment:
- dated E4 contract addendum records the approved schema correction;
- schema count is now **40**, latest **040**;
- MCP tool count is **51**.

## C. Final local acceptance evidence on candidate ce9067ab

Evidence already complete:
- full JSON PostgreSQL-backed suite: real `PYTEST_EXIT=0`;
- skips: three known Windows symlink privilege skips + one pgvector-only skip;
- real-pgvector company-support eligibility and affected vector paths: PASS;
- the legacy `test_semantic_jsonb_path_and_hybrid_exclude_non_use` is intentionally JSON-only and reproduces its mismatch when forced onto pgvector mode at the prior base; do not treat that mode mismatch as a new E4 defect;
- targeted ACK/public-adapter/split-role security tests: **72 passed**;
- critical Ruff: PASS;
- `git diff --check`: PASS;
- local release gate: exit 0 / `PASSED_WITH_EXPLICIT_LIVE_GATES`;
- release-gate DB skips are by design and are not PostgreSQL acceptance evidence.

Migration-040 security closure:
- ordinary runtime cannot mint the protected ACK attestation;
- host `claudecode/toolUseId` correlation must match the hook-issued nonce;
- missing host correlation fails closed;
- company knowledge with only revoked applicable support is excluded from knowledge get/search, chunk/hybrid, JSON semantic, pgvector semantic, and E3 structured/raw retrieval.

## D. Residual risks / accepted review items

Do not automatically open another implementation mini-loop for these. Carry them into protected validator / later live-production review unless they demonstrably violate a frozen E4 MUST/NEVER:

- `toolUseId` correlation was observed on Claude Code 2.1.286; if the host drops it, ACK fails closed;
- same-user process with transcript access plus runtime DB credential could replay the latest nonce once inside the short TTL;
- provenance-writer credential and runtime credential live in the same OS credential store;
- single-role disposable acceptance databases make role separation nominal; production least-privilege proof belongs later;
- transitive company-support analysis remains limited;
- ACK-path latency was not re-measured after the final closure.

## E. Exact next E4 sequence — no more routine development

The next action is NOT another code-hardening chunk.

1. Verify live remote branch HEAD is still exactly `ce9067ab36716cb1f729466db168d002e1029c93`.
2. Create/verify the E4 PR to `main`.
3. Obtain fresh exact-head CI on the exact candidate.
4. Capture CI run number/id, event, exact head, required step results, artifact id/name/digest.
5. Make exactly one final material Vres checkpoint AFTER exact-head CI and BEFORE `validation_prepare`.
6. Freeze exact candidate SHA/tree/artifact manifest.
7. Call `validation_prepare` once.
8. Delegate exactly `vres-os:validator`; do not override protected model.
9. While validation is in flight, do not mutate checkpoint/decision/orchestration/task state.
10. Read host evidence first: fresh VAL id, terminal status/report, completed_at, host-observed Fable-family model, exact reviewed SHA/hashes, task validation status.
11. Do not retry automatically on reject/fail/stale/wrong-model/wrong-SHA.
12. Only after PASS: guarded expected-head merge.
13. Require post-merge push CI on exact new main SHA.
14. Durably close E4 before E5.

## F. Faster working methodology from this handoff

The prior E4 process became too expensive because release-level evidence was repeated after small corrections. Preserve the following cadence going forward.

### Development / test cadence

For a bounded code correction:
1. write/run the targeted failing test;
2. implement the bounded fix;
3. rerun load-bearing targeted unit/PostgreSQL/security tests;
4. inspect diff/state;
5. commit/checkpoint the bounded correction.

Do NOT automatically run the whole suite after each small fix.

Run:
- full suite once per coherent final tranche candidate;
- release gate once per coherent final tranche candidate;
- protected validation once per frozen exact-head candidate.

Repeat an expensive suite only when candidate bytes changed after that evidence or when a concrete evidence gap requires it.

### Responsibility split requested by the user

**ChatGPT becomes the primary coding/repository coordinator again.**

ChatGPT owns, when the branch is in remote GitHub state:
- architecture and bounded implementation decisions;
- code/repository edits through the connected repository tools when practical;
- PR creation/inspection;
- exact-head CI evidence;
- guarded merge;
- documentation/checklist/handoff updates;
- tranche-status accounting;
- review of local/live evidence;
- deciding whether a result is a blocker, safe debt, or later-tranche item.

**Local Claude Code is reserved for machine-specific/local proof and correction.**

Use local Claude for:
- Windows PowerShell/Visual Studio execution;
- fresh local PostgreSQL and real pgvector acceptance;
- installed-runtime/package smoke;
- Windows Credential Locker/current-user behavior;
- local host-hook/session behavior that cannot be reproduced remotely;
- real legacy-project/adoption/live tests;
- bounded corrections whose defect exists only in the local/live environment.

When Claude makes a local code correction:
1. targeted tests first;
2. commit locally;
3. push exact branch SHA;
4. stop;
5. return exact transcript/SHA to ChatGPT;
6. ChatGPT verifies remote identity and resumes repository/CI orchestration.

### Single-writer branch rule

Never have ChatGPT and Claude modify the same branch concurrently.

Before handing ownership:
- current writer must commit;
- worktree/repo must be clean;
- push exact SHA;
- receiving side must fetch/verify that exact SHA before editing.

This rule is mandatory to prevent divergent local/remote histories.

### Classification rule

Only a genuine frozen-contract/security/data-integrity violation is an immediate blocker.

A conservative safe limitation or performance opportunity is documented and carried forward; it must not automatically create another mini-development stage.

Items explicitly owned by later E5/E6/E7/E8/#165–#170 stay later.

## G. Full remaining product program

After E4 is accepted and merged:

1. #176 E5 — capability/procedure experience integration.
2. #176 E6 — observability + experience utility evidence.
3. #176 E7 — benchmark + security ladder.
4. #176 E8 — Chairman integration + protected acceptance.
5. E9 physical Experience Intelligence criteria carried into #169.
6. #165 — Chairman model policy.
7. #166 — read full canonical issue before implementation.
8. #167 — read full canonical issue before implementation.
9. #168 — project adoption + canonical Claude scaffold.
10. #169 — integrated Windows / Visual Studio live acceptance.
11. #170 — production readiness / go-live.
12. Post-#170 — Organizational Architecture & Specialist Intelligence / full-team enhancement.

The post-#170 full-team enhancement remains mandatory queued work:
- recover the original Agent Board and full department -> Director -> role -> specialist structure from earliest project artifacts;
- restore/audit the full Technology/IT software organization including product/design/architecture/database/backend/frontend/security/DevOps/QA/reliability and other originally defined specialists;
- distinguish intentional consolidation from accidentally lost roles;
- keep role identity distinct from execution model/tier;
- improve human-facing specialist identity;
- add mechanically supported role/department/capability performance attribution without fabricated quality scores.

## H. Fresh-chat first action

In the new ChatGPT session:

1. Read this section 28 first.
2. Verify GitHub live state:
   - `main`;
   - E4 remote branch head;
   - whether a PR now exists;
   - whether exact-head CI already ran.
3. Treat `ce9067ab36716cb1f729466db168d002e1029c93` as the candidate only if remote branch still equals it.
4. Do NOT rerun local full suites/release gate merely for ceremony.
5. If no PR exists, create it.
6. Obtain exact-head CI/artifact evidence.
7. Then instruct local Claude only for the final Vres freeze/checkpoint + protected validator lifecycle if those Vres/local host tools are required.
8. On protected PASS, ChatGPT performs/coordinates guarded merge + post-main CI and updates durable docs.
9. If protected validation finds a real defect, fix only that defect using the single-writer/targeted-test workflow above.
10. Do not begin E5 before E4 merge/post-main closure.

## I. Fresh-chat resume prompt

```text
Resume the Vres-OS preproduction program from the newest canonical durable handoff.

Repository:
vosser24/Vres-OS

Canonical documentation branch:
docs-execution-checklist-20260927

Read first:
docs/PREPRODUCTION-EXECUTION-CHECKLIST-2026-09-27.md
docs/handoffs/PREPRODUCTION-RESUME-HANDOFF-2026-09-27.md

The newest authoritative handoff boundary is:

# 28. 2026-10-02 #176 E4 migration-040 pre-validation / ChatGPT-primary continuation seal

Do not resume from older E3/E4 instructions in the historical handoff.

Authoritative remote main at handoff:
ddb0719d130fd45b12b6bdc9e1682378ace7ae64

E4 branch:
issue-176-e4-temporal-lifecycle-revocation

Frozen E4 candidate:
ce9067ab36716cb1f729466db168d002e1029c93

Candidate tree:
5cf813f19feb36e23f59dc6ddf632c38ac09e869

E4 Vres task:
TASK-20260930-2c7198e394

Latest local Vres checkpoint:
CP-20261002-b2e09a2047

First verify live GitHub state. At the handoff check the remote E4 branch existed at the exact candidate SHA and no PR existed yet.

Do not reopen routine E4 development. Next is PR + exact-head CI + one final pre-validation Vres freeze checkpoint + exactly one protected vres-os:validator run. Then guarded merge and post-main CI.

Working method:
- ChatGPT is primary for architecture, coding/repository edits, PR/CI/merge, docs and status.
- Local Claude is for Windows/local PostgreSQL/pgvector/installed-runtime/Visual Studio/live tests and machine-specific corrections.
- Never edit the same branch concurrently; transfer ownership only at an exact clean/pushed SHA.
- Use targeted tests for bounded fixes; full suite/release gate once per final candidate; protected validation once per frozen exact-head candidate.
- Do not auto-retry protected validation.
- Distinguish real blockers from safe debt/later-tranche work.

After E4: E5, E6, E7, E8, #165, #166, #167, #168, #169 live acceptance, #170 go-live, then the queued full-team Organizational Architecture & Specialist Intelligence enhancement.
```
