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


---

# 29. 2026-10-02 #176 E4 closure / E5 continuation seal

This is the newest authoritative handoff boundary. It supersedes section 28 and every older E3/E4 current-action instruction. Historical evidence remains historical and must not be rewritten.

## A. Authoritative repository boundary

Repository:
`vosser24/Vres-OS`

Authoritative product main after E4:
`a0a2769b99f4893733568194c0aa68e78e73aeab`

E4 branch:
`issue-176-e4-temporal-lifecycle-revocation`

E4 PR:
`#182 — #176 E4 temporal lifecycle and revocation`

PR state:
**MERGED**

Exact protected-reviewed E4 branch head:
`553e9d1398073b4cf0a4a4b282b2f3f3ff86ec2b`

Exact reviewed tree:
`6eb856f2c075b2194ccabb59b4a6e906110e4a1d`

Merge commit / new main:
`a0a2769b99f4893733568194c0aa68e78e73aeab`

E4 Vres task:
`TASK-20260930-2c7198e394`

The E4 Vres task is now **completed**. Local read-back after exactly one `task_complete` call confirmed:
- task: `TASK-20260930-2c7198e394`;
- final status: `completed`;
- completed_at: `2026-10-05T08:47:49+03:00`;
- validation status: `passed`;
- `completion_after_latest_passed_validation=true`;
- latest protected request remains `VAL-4dbf9f69b1744e6b` / `passed` / host-observed `claude-fable-5-1`;
- historical `VAL-72e66d088bec405a` remains `rejected`;
- no checkpoint, validation request, code, Git or PR mutation was created by completion;
- the reviewed E4 worktree remained clean at `553e9d1398073b4cf0a4a4b282b2f3f3ff86ec2b`, tree `6eb856f2c075b2194ccabb59b4a6e906110e4a1d`.

No further E4 local lifecycle action is pending.

## B. Exact-head CI and review identity

Final exact-head CI:
- workflow: Vres-OS CI **#470**;
- run id: `37018126950`;
- event: `pull_request`;
- attempt: 1;
- exact head: `553e9d1398073b4cf0a4a4b282b2f3f3ff86ec2b`;
- conclusion: **SUCCESS**;
- full PostgreSQL-backed suite: **2196 passed / 3 skipped**;
- installed-runtime smoke: **PASS**;
- release gate: `PASSED_WITH_EXPLICIT_LIVE_GATES`;
- release-gate static/unit result: **1517 passed / 682 expected DB/live skips**;
- artifact: `11231412578`;
- artifact name: `release-gate-evidence`;
- artifact digest: `sha256:764ac4524c32681f96cc4e550ddffb54c4d48eca16832340105d5391324c1d5c`.

The final E4 review scope was the complete base-to-head diff:
- base: `ddb0719d130fd45b12b6bdc9e1682378ace7ae64`;
- head: `553e9d1398073b4cf0a4a4b282b2f3f3ff86ec2b`;
- **65 files**;
- 41 added;
- 24 modified;
- 0 deleted.

The prior docs-complete product candidate `ce9067ab36716cb1f729466db168d002e1029c93` advanced only through CI-discovered acceptance-harness corrections. Those corrections changed only:
- `tests/test_control_preflight.py`;
- `tests/integration/test_validation_reply_guard_journey.py`.

No E4 product/runtime file changed after `ce9067ab...`.

## C. Protected validation history

Historical first protected lifecycle attempt:
- freeze checkpoint: `CP-20261002-ce4cd17ce2`;
- request: `VAL-72e66d088bec405a`;
- status: **rejected**;
- task remained pending;
- no host model/report was attached before terminal rejection;
- the later validator prose could not rescue the terminal request;
- no E4 candidate defect was established.

The first attempt exposed a protected-validation execution issue: the validator stopped before its own background work completed. The current Vres contract defers one no-report stop, but a subsequent no-report stop is terminal rejection.

Final protected retry:
- current-turn retry freeze: `CP-20261002-836cb0cf41`;
- request: `VAL-4dbf9f69b1744e6b`;
- status: **passed**;
- task validation status: **passed**;
- completed_at: `2026-10-02T18:46:55+03:00`;
- canonical validator: `vres-os:validator`;
- host-observed model: **`claude-fable-5-1`**;
- host agent id: `a757f62be54532130`;
- host session id: `04300332-0486-411f-8bd3-c9886c2edfbf`;
- canonical report: **14/14 checks passed**, no `not_run`, no failed checks;
- all 65 prepared artifact hashes matched;
- state digest reported as `47152e7c…6920`;
- while validation was pending the parent reply gate correctly returned `validation_in_flight`.

The successful retry deliberately:
- used a current-turn Chairman freeze checkpoint;
- launched no validator background/nested agents;
- required a canonical terminal JSON report before validator stop;
- prohibited `outcome=passed` when any check was `not_run` or failed.

## D. Guarded merge and post-main proof

Merge:
- expected-head guard: `553e9d1398073b4cf0a4a4b282b2f3f3ff86ec2b`;
- merge method: merge commit;
- PR #182 merged successfully;
- merge/main SHA: `a0a2769b99f4893733568194c0aa68e78e73aeab`.

Required post-merge main CI:
- workflow: Vres-OS CI **#471**;
- run id: `37029621024`;
- event: **push**;
- attempt: 1;
- exact main head: `a0a2769b99f4893733568194c0aa68e78e73aeab`;
- conclusion: **SUCCESS**;
- full PostgreSQL-backed suite: **2196 passed / 3 skipped**;
- installed-runtime smoke: **PASS**;
- release gate: `PASSED_WITH_EXPLICIT_LIVE_GATES`;
- release-gate static/unit result: **1517 passed / 682 expected DB/live skips**;
- release-gate git commit: `a0a2769b99f4893733568194c0aa68e78e73aeab`;
- dirty: false;
- artifact: `11236608634`;
- artifact name: `release-gate-evidence`;
- artifact digest: `sha256:0da77dfb4357f4b6d1413702192365cc15c11c2d0aa0305fdac433ecc6690758`.

Durable GitHub evidence was posted to issue #176 for:
- exact-head CI;
- rejected protected attempt;
- final protected PASS;
- merge + post-main closure.

## E. Accepted E4 shipped boundary

E4 is repository/protected-acceptance complete and now present on authoritative main.

Accepted scope:
- append-only experience lifecycle ledger;
- temporal retire/reinstate/challenge/supersession/refresh controls;
- provenance-driven source revocation;
- bounded multi-source survival handling;
- JSON + pgvector embedding invalidation/rebuild fencing and stale-worker protection;
- E4 lifecycle-aware E3 retrieval / policy `176.e4.v1`;
- contaminated-session enforcement and serialized session-open/revocation behavior;
- protected context-refresh attestation via migration 040;
- host `claudecode/toolUseId` correlation;
- revoked-only company support suppression across current reader surfaces;
- MCP tools `source_revoke`, `knowledge_lifecycle`, and `context_refresh_ack`.

Residual risks remain explicit and do not reopen E4 absent a real frozen-contract/security/data-integrity violation:
- host `toolUseId` / `updatedInput` behavior dependency;
- 120-second same-user replay window with runtime DB credential;
- writer/runtime credentials in the same OS credential store;
- nominal privilege separation in single-role DB topology;
- owner/superuser trigger authority;
- no `restore_source`;
- bounded/non-transitive company support;
- Stop-hook contamination reporting fails open;
- ACK-path latency was not re-measured after migration 040.

The validator also observed a pre-existing custom-order test-isolation weakness involving runtime-surface stubs and control-preflight tests. It was reproduced as test isolation rather than an E4 runtime defect; canonical CI ordering and isolated execution are green.

## F. E4 local lifecycle closure — DONE

The accepted E4 Vres task was completed exactly once after protected PASS and repository/post-main closure.

- task: `TASK-20260930-2c7198e394`;
- completed_at: `2026-10-05T08:47:49+03:00`;
- final validation status: `passed`;
- latest accepted request: `VAL-4dbf9f69b1744e6b`;
- historical rejected request preserved: `VAL-72e66d088bec405a`;
- no completion checkpoint or new validation request was created;
- the final `task_reply_gate` error after completion (“requires ... unfinished task”) is expected and is not a defect.

E4 has no remaining local lifecycle bookkeeping.

## G. E5 — only next #176 implementation tranche

Frozen plan:
`docs/architecture/EXPERIENCE-INTELLIGENCE-PLAN-2026-09-27.md`

Plan commit:
`34f45afa0fb8d5a6a90bef53dec58d9ecef1093d`

E5 frozen-plan scope:
- capability-centric experience retrieval;
- procedure/episode/feedback links;
- validated success/failure history;
- no opaque self-certified expert score;
- no automatic agent prompt rewriting.

Do not infer a larger E5 from convenience. Read issue #176 and the frozen plan first, then freeze a bounded E5 contract before implementation.

Required E5 start sequence:
1. finish the E4 Vres task completion bookkeeping above if still pending;
2. verify authoritative `origin/main == a0a2769b99f4893733568194c0aa68e78e73aeab`;
3. create a fresh E5 worktree/branch from that exact main;
4. create a fresh E5 Vres task;
5. audit existing capability/procedure/episode/feedback truth owners before designing schema;
6. freeze the E5 contract;
7. only then implement E5 in bounded chunks.

Do not begin E6 until E5 is fully accepted, merged and green on post-main CI.

## H. Preserved execution methodology

Continue the accepted cadence:
- bounded defect: targeted red test -> bounded fix -> targeted load-bearing tests -> commit;
- full suite once per coherent final candidate;
- release gate once per coherent final candidate;
- protected validation once per frozen exact-head candidate unless a terminal lifecycle failure is deliberately classified and a fresh request is explicitly authorized;
- no repeated expensive evidence without changed bytes or a concrete evidence gap.

Protected validator lifecycle lesson from E4:
- the freeze checkpoint that anchors `validation_in_flight` must be an explicit Chairman checkpoint in the current user turn before `validation_prepare`;
- validators must not terminal-stop before the canonical report exists;
- `outcome=passed` requires every check status to be `passed`;
- preserve rejected/stale/failed requests as history;
- never use `validation_abandon` on an already terminal request;
- never use `validation_invalidate` unless a current PASS is being explicitly reopened for real post-review changes.

Responsibility split remains:
- ChatGPT primary for architecture, repo/code, PR/CI/merge, durable docs and tranche sequencing;
- local Claude Code for Windows/local PostgreSQL/pgvector/installed runtime/Visual Studio/host-session/live-machine operations;
- single writer per branch, with ownership transferred only at a clean exact committed/pushed SHA.

## I. Remaining frozen program

After E5:
1. E6 — observability + experience utility evidence;
2. E7 — benchmark + security ladder;
3. E8 — Chairman integration + protected acceptance;
4. E9 physical Experience Intelligence criteria carried to #169;
5. #165 Chairman model policy;
6. #166;
7. #167;
8. #168 project adoption + canonical Claude scaffold;
9. #169 integrated Windows / Visual Studio live acceptance;
10. #170 production readiness/go-live;
11. post-#170 Organizational Architecture & Specialist Intelligence / full-team enhancement.

The post-#170 backlog remains mandatory and must not interrupt E5–#170.

## J. Fresh-chat resume prompt

```text
Resume the Vres-OS preproduction program from the newest canonical durable handoff.

Repository:
vosser24/Vres-OS

Canonical documentation branch:
docs-execution-checklist-20260927

Read first:
docs/PREPRODUCTION-EXECUTION-CHECKLIST-2026-09-27.md
docs/handoffs/PREPRODUCTION-RESUME-HANDOFF-2026-09-27.md

Newest authoritative handoff boundary:

# 29. 2026-10-02 #176 E4 closure / E5 continuation seal

Do not resume from older E3/E4 instructions.

AUTHORITATIVE MAIN:
a0a2769b99f4893733568194c0aa68e78e73aeab

E4:
repository/protected acceptance DONE
PR #182 merged
exact reviewed head 553e9d1398073b4cf0a4a4b282b2f3f3ff86ec2b
protected PASS VAL-4dbf9f69b1744e6b on host-observed claude-fable-5-1
post-main CI #471 / run 37029621024 SUCCESS
post-main artifact 11236608634
digest sha256:0da77dfb4357f4b6d1413702192365cc15c11c2d0aa0305fdac433ecc6690758

Before E5, if TASK-20260930-2c7198e394 is still active locally, complete it once with task_complete after re-reading the current PASS evidence. Do not checkpoint or revalidate merely for completion.

E5 is the only next #176 implementation tranche:
- capability-centric experience retrieval;
- procedure/episode/feedback links;
- validated success/failure history;
- no opaque self-certified expert score;
- no automatic agent prompt rewriting.

Start E5 from exact main a0a2769b99f4893733568194c0aa68e78e73aeab.
Read issue #176 and the frozen Experience Intelligence plan first.
Freeze a bounded E5 contract before implementation.
Preserve the targeted-test/full-suite/release-gate/protected-validation cadence.
Do not begin E6 before E5 is accepted, merged and post-main green.

ChatGPT remains primary for architecture/repository/PR/CI/docs.
Local Claude is for Windows/local PostgreSQL/pgvector/installed-runtime/Visual Studio/host/live-machine work.
Never edit the same branch concurrently.
```


---

# 30. 2026-10-05 #176 E5 frozen contract / implementation continuation seal

This is the newest authoritative handoff boundary. It supersedes section 29 for current execution state. Historical E4 evidence remains authoritative history and must not be rewritten.

## A. Product/main boundary

Repository:
`vosser24/Vres-OS`

Authoritative main:
`a0a2769b99f4893733568194c0aa68e78e73aeab`

E4:
**DONE**, including:
- protected PASS;
- guarded PR #182 merge;
- post-main CI #471;
- final Vres task completion on 2026-10-05T08:47:49+03:00.

No E4 action remains.

## B. E5 frozen boundary

E5 branch:
`issue-176-e5-capability-procedure-experience`

Frozen contract commit:
`a06d32801a22a9c17439a0e03c081dae57ba2367`

Tree:
`5cd55b7f4cd6bf9885187af5f179db18018f29c8`

Frozen contract:
`docs/architecture/EXPERIENCE-INTELLIGENCE-E5-CONTRACT-2026-10-05.md`

Parent/base:
`a0a2769b99f4893733568194c0aa68e78e73aeab`

Retrieval schema target:
`176.e5.v1`

E5 implementation has **not** started.

## C. E5 architecture decision

**No migration.**

Verified existing truth owners already contain the required durable evidence:
- `capabilities` / `capability_proofs`;
- `procedures` / `procedure_versions`;
- `procedure_runs` / `procedure_feedback`;
- immutable `experience_episodes`;
- deterministic E1 relations `episode uses capability` and `episode uses procedure`;
- task linkage through `task_id`;
- E4 lifecycle/revocation gates.

The missing E5 capability is read-time integration, not another durable ledger.

## D. Frozen E5 scope

Implement:
- capability-centric experience retrieval;
- procedure/episode/feedback links;
- validated success/failure history.

Never implement in E5:
- opaque expert score;
- success probability;
- authority from run/feedback/proof counts;
- model-specific expertise memory;
- automatic agent/Chairman prompt rewriting;
- automatic procedure promotion/rewrite;
- automatic lifecycle challenge/retire;
- E6 retrieval-observation writes;
- new generic experience tables.

## E. Key retrieval rules

Explicit `capability_keys` become a structured candidate-source signal.

An episode may be sourced structurally through:
- direct `episode uses capability`; or
- accepted `capability_proof` task identity.

An accepted procedure may be sourced structurally when an eligible episode:
- directly uses that procedure; and
- structurally matches the requested capability.

Capability structure can improve candidate coverage/relevance only. It never changes scope/authority/lifecycle/preferred version.

Procedure items may expose one bounded `experience_history` extension with:
- validated success episode keys;
- validated failure episode keys;
- other failure episode keys;
- task-backed feedback tied to a current-eligible same-task episode using that procedure;
- latest validated evidence time.

No counts/ratios become authority or scores.

Validated procedure success/failure means the procedure `accepted` flag is captured inside an immutable task-level `validated_runtime` episode whose task passed required validation. It does not claim causality or optimality.

Feedback is evidence-only:
- task-backed;
- same-task eligible episode;
- same procedure;
- redacted/bounded;
- injection-shaped text omitted;
- never approval/instruction authority.

## F. Expected implementation surface

Prefer:
- `src/vres_os/experience_retrieval.py`;
- `tests/test_experience_retrieval.py`;
- focused new PostgreSQL E5 integration tests.

Do not modify migrations, procedure/capability write authority, MCP registration or unrelated systems unless a frozen requirement cannot otherwise be met. Stop for explicit review before such scope expansion.

## G. Immediate next action

Local Claude/Vres must create the fresh E5 task from a correctly rooted E5 worktree before implementation.

Local Claude responsibilities for this handoff step only:
1. create/fetch a clean E5 worktree on exact branch `issue-176-e5-capability-procedure-experience`;
2. verify HEAD `a06d32801a22a9c17439a0e03c081dae57ba2367` and tree `5cd55b7f4cd6bf9885187af5f179db18018f29c8`;
3. start Vres from that E5 root;
4. create one new E5 Vres task for #176 capability/procedure experience integration;
5. checkpoint the frozen base/contract/branch boundary;
6. do not edit code;
7. return the task key + checkpoint to ChatGPT.

After that, ChatGPT resumes primary implementation ownership on the remote E5 branch.

## H. E5 acceptance cadence

Development:
- targeted red test;
- bounded fix;
- targeted load-bearing unit/PostgreSQL/security/E1–E4 regression;
- coherent commits.

Final:
- fresh isolated full PostgreSQL suite once;
- critical lint/diff hygiene;
- installed-runtime smoke;
- release gate;
- exact-head CI;
- current-turn freeze checkpoint;
- protected Fable/high;
- guarded merge;
- post-main CI;
- Vres task completion;
- then E6.

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

Newest authoritative boundary:
# 30. 2026-10-05 #176 E5 frozen contract / implementation continuation seal

AUTHORITATIVE MAIN:
a0a2769b99f4893733568194c0aa68e78e73aeab

E5 BRANCH:
issue-176-e5-capability-procedure-experience

FROZEN E5 CONTRACT:
a06d32801a22a9c17439a0e03c081dae57ba2367

E5 TREE:
5cd55b7f4cd6bf9885187af5f179db18018f29c8

CONTRACT FILE:
docs/architecture/EXPERIENCE-INTELLIGENCE-E5-CONTRACT-2026-10-05.md

E5 architecture:
- no migration;
- capability-centric structured retrieval;
- procedure/episode/feedback evidence integration;
- validated success/failure history;
- no expert score;
- no model-specific memory;
- no automatic prompt rewriting;
- no E6 observation writes.

If the fresh E5 Vres task/checkpoint has not yet been created, do that locally first from the exact E5 worktree without editing code. Then return task/checkpoint to ChatGPT. ChatGPT remains primary for E5 implementation/repository/PR/CI/docs.
```


---

# 31. 2026-10-05 #176 E5 coherent candidate / final-local-acceptance pending seal

This is the newest authoritative handoff boundary. It supersedes section 30 for current E5 execution state. Historical E4 and E5 contract-freeze evidence remains authoritative history and must not be rewritten.

## A. Repository and program identity

Repository:
`vosser24/Vres-OS`

Authoritative product main:
`a0a2769b99f4893733568194c0aa68e78e73aeab`

E5 branch:
`issue-176-e5-capability-procedure-experience`

E5 Vres task:
`TASK-20261005-dc0e7a9e38`

Frozen E5 contract:
`docs/architecture/EXPERIENCE-INTELLIGENCE-E5-CONTRACT-2026-10-05.md`

Frozen contract commit:
`a06d32801a22a9c17439a0e03c081dae57ba2367`

Frozen contract tree:
`5cd55b7f4cd6bf9885187af5f179db18018f29c8`

Coherent final E5 candidate HEAD:
**`d39fabb22484a664e863c1603e2054d1ef0723c4`**

Coherent final E5 candidate tree:
**`fd00975275a1f8cc697bd4c570f994812e49f3b9`**

Remote branch state at this seal:
- branch exists exactly at `d39fabb...`;
- authoritative `main` remains `a0a2769...`;
- branch is 28 commits ahead of main;
- PR for E5: **none yet**;
- product branch bytes are fully committed/pushed; no ChatGPT-side uncommitted product changes exist;
- local E5 worktree was reported clean at the exact candidate after targeted acceptance.

Canonical documentation branch at the start of this seal:
`docs-execution-checklist-20260927`

Section 15 of the execution checklist is the matching E5 current-state override.

## B. E5 frozen architecture — do not redesign

E5 scope is exactly:
- capability-centric experience retrieval;
- procedure/episode/feedback evidence integration;
- validated success/failure history;
- no opaque self-certified expert score;
- no automatic agent/Chairman prompt rewriting.

Architecture decision remains:
**NO migration.**

Existing truth owners remain authoritative:
- `capabilities` / `capability_proofs`;
- `procedures` / `procedure_versions`;
- `procedure_runs` / `procedure_feedback`;
- immutable `experience_episodes`;
- `relations`;
- E4 lifecycle/revocation state;
- task/validation/source evidence.

E5 must never introduce:
- generic capability-experience score table;
- model-specific expertise memory;
- procedure-experience cache/ledger;
- success/confidence probability;
- authority from counts/quality/retrieval frequency;
- automatic prompt rewrite;
- automatic procedure promotion/demotion;
- automatic lifecycle mutation;
- E6 retrieval-observation writes.

## C. Exact implementation delta

Base-to-candidate delta from authoritative main is exactly eight files:
1. `docs/architecture/EXPERIENCE-INTELLIGENCE-E5-CONTRACT-2026-10-05.md` — new frozen contract;
2. `src/vres_os/experience_retrieval.py`;
3. `tests/integration/test_e5_capability_retrieval.py` — new;
4. `tests/integration/test_e5_procedure_history.py` — new;
5. `tests/integration/test_experience_retrieval_journey.py`;
6. `tests/integration/test_experience_retrieve_surface.py`;
7. `tests/test_experience_retrieval.py`;
8. `tests/test_experience_retrieval_e4.py`.

No migration, MCP registration, capability/procedure writer, routing/model policy, prompt surface or E6 observation surface changed.

## D. Implemented E5 behavior

Retrieval schema:
`176.e5.v1`

Capability-centric retrieval:
- explicit `capability_keys` are validated against active project-visible capabilities;
- direct immutable E1 `episode -> uses -> capability` evidence can source an episode even without lexical overlap;
- accepted `capability_proofs` can source the proof task's eligible episode only when the immutable episode payload already names that capability;
- `proven_count` is not used as retrieval authority or expertise evidence;
- foreign/inaccessible capability keys fail closed without cross-project disclosure.

Procedure sourcing:
- an accepted procedure may be structurally sourced only through an already integrity/lifecycle-gated episode that directly uses that procedure and structurally matches the requested capability;
- structural evidence improves candidate coverage/same-tier relevance only;
- it never changes preferred-version authority, scope, lifecycle state or company approval.

Procedure `experience_history`:
- bounded validated success episode keys;
- bounded validated failure episode keys;
- bounded other failed/cancelled episode keys;
- bounded task-backed feedback;
- latest validated evidence timestamp;
- no success rate, quality grade, expert score or probability.

Validated success/failure semantics:
- only task-level immutable episodes;
- episode current-eligible under E4;
- `trust_class='validated_runtime'`;
- immutable payload validation status `passed`;
- immutable payload names the same procedure and its recorded `accepted=true/false` value;
- raw `procedure_runs.quality_score`, run count, model/provider and replay counts do not establish history authority.

Feedback semantics:
- `procedure_feedback.task_id` must map to a current-eligible task episode in the requested project;
- that episode must directly use the same procedure and its immutable payload must identify the procedure;
- feedback text is run through the existing #164 sanitizer;
- sanitized text only; <=300 chars;
- instruction-shaped feedback is omitted;
- null-task, unrelated-task and foreign-task feedback is omitted;
- feedback is evidence-only, never an approval/instruction/promotion channel.

E4 revocation integration:
- if the only supporting source for an episode is revoked through the real E4 source-revocation path, the episode stops contributing current procedure history and feedback;
- accepted procedure authority itself remains governed by the existing procedure owner;
- history/evidence is not physically erased.

Read-only/determinism:
- repeated E5 retrieval of the same request produced identical packs;
- row-count+digest snapshots proved no writes across capability/proof/procedure/run/feedback/episode/lifecycle/relation truth owners.

## E. E5 Vres task/checkpoint history

Task:
`TASK-20261005-dc0e7a9e38`

Initial E5 boundary:
- initial checkpoint `CP-20261005-6b9c6acbb3` was superseded during the setup turn;
- latest intended start-boundary checkpoint became `CP-20261005-d9dd95b696`;
- objective and frozen scope remained unchanged.

Chunk 1:
- explicit checkpoint `CP-20261005-60dd993356`.

Chunk 2:
- explicit Chairman checkpoint `CP-20261005-8e70bf99ac`;
- later `CP-20261005-bb0d29c4e5` has reason `pre_compact` and the same material Chunk-2 state;
- treat `CP-20261005-bb0d29c4e5` as host compaction/lifecycle bookkeeping, not an intentional second Chairman material checkpoint.

Chunk 3 / targeted-development closure:
- explicit Chairman checkpoint `CP-20261005-8fe3a4f070`.

At this seal the task remains unfinished and has **not** entered protected validation.

## F. Targeted evidence — Chunk 1

Candidate:
- head `a0b15d53ec96b1fd196dbb7778c3c42a853a45af`;
- tree `9772552df25f67bf9746c2b004f9d7aaa97d1f56`.

Evidence:
- 165 unit/static tests passed;
- critical Ruff PASS;
- diff-check PASS;
- 3 focused E5 PostgreSQL tests passed;
- 122 E3/E4 retrieval regression tests passed;
- 19 E1 linkage regression tests passed;
- zero local repository mutation.

Fresh PostgreSQL lesson:
- the old database behind `pg_issue163_test_dsn` contained migration drift and was correctly rejected as acceptance evidence;
- a fresh database was created on the same server;
- the machine's production Vres config caused an initial provenance-writer mismatch in the single-role test DB;
- empty isolated `VRES_DATA_DIR` fixed the environment and is now mandatory methodology;
- final Chunk-1 B/C/D all passed;
- fresh DB dropped; original drifted DB untouched.

## G. Targeted evidence — Chunk 2

Candidate:
- head `747997c2dd40ddf551a9bf17726ea573ef805258`;
- tree `187dea9addde9f97f53908148e59309a85a4e3ea`.

Evidence:
- A: 166 passed;
- critical Ruff PASS;
- diff-check PASS;
- B: 5 focused E5 tests passed;
- C: 122 E3/E4 regression tests passed;
- original requested D mixed ordering: 24 passed + 1 setup error because `pg_project` fixture was not discovered;
- reordered D with integration files first: 25 passed / 0 failed;
- no skips/warnings;
- fresh disposable DBs dropped;
- isolated config PASS.

Do not hide the D caveat. Classification:
- affected test is in `tests/integration/test_project_capability_resolve_scope.py`;
- fixture is defined only in `tests/integration/conftest.py`;
- same test passed in C and in integration-first D;
- no product assertion failed;
- treat as pytest file-argument collection topology, not an E5 runtime failure.

## H. Targeted evidence — Chunk 3 / coherent candidate closure

Candidate:
- head `d39fabb22484a664e863c1603e2054d1ef0723c4`;
- tree `fd00975275a1f8cc697bd4c570f994812e49f3b9`.

Evidence:
- A: **235 passed**;
- repository-bounded critical Ruff PASS;
- Chunk-3 diff-check PASS;
- B: **8 passed** focused E5 capability/history/feedback/revocation/read-only tests;
- C: **122 passed** E3/E4 retrieval regression;
- D1: **6 passed** integration episode/project-capability authority;
- D2: **19 passed** experience/procedure/capability unit authority;
- E: **39 passed** source-revocation/retrieval lifecycle regression;
- skips/warnings: **0**;
- no local code/file mutation.

Fresh acceptance DB:
`vres_e5_c3_3635d6ac64bf_test`

It was created fresh, used for B–E, and dropped afterward.

Separate throwaway verification established:
- migration count = 40;
- highest = `040_context_refresh_attestation.sql`;
- `ISOLATED_VRES_CONFIG=PASS`;
- `provenance_writer_user=''`;
- `migration_user=''`.

Note: the migration count was not read directly from the main Chunk-3 acceptance DB; it was separately verified on a fresh throwaway DB. The final full-suite run is explicitly required to read migration count/highest from the SAME acceptance database before running pytest.

## I. Machine/local acceptance methodology — preserve exactly

Python:
`C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`

Do not use the machine's default Python 3.11; it lacks the required pytest/ruff environment.

PostgreSQL:
- `pg_issue163_test_dsn` is only an administrative/server credential source;
- never run tests against its historical drifted database;
- never repair its migration ledger/digest;
- create a fresh unique database ending `_test`;
- use `psycopg.sql.Identifier` for CREATE/DROP DB identifiers;
- `VRES_ALLOW_TEST_DB=1`;
- child receives only the fresh test DSN;
- empty isolated `VRES_DATA_DIR` is mandatory;
- verify empty provenance writer and migration user;
- drop the temp DB in `finally` after evidence capture;
- never expose password/DSN in chat/logs.

Release gate:
- output directory must be fresh and outside checkout;
- isolate `VRES_DATA_DIR`;
- do not inject DB variables;
- `scripts/release_gate.py` already builds the exact candidate wheel, compares packaged `.py`/`.sql` bytes, installs it into a fresh target and runs `wheel-import-smoke`;
- do not overwrite/global-install Vres merely for E5 smoke.

## J. Frozen-contract whitespace waiver

During final local acceptance, repository-wide critical Ruff passed, but baseline→candidate `git diff --check` reported 9 trailing-whitespace lines in the frozen contract.

Verified exact lines:
- 3–7;
- 39;
- 52–54.

Each line ends in exactly two spaces, intentionally used as Markdown hard line breaks.

Those exact bytes were already present in frozen contract commit `a06d32801a22a9c17439a0e03c081dae57ba2367`.

Authoritative decision:
- do NOT edit the frozen contract;
- do NOT create new product bytes for formatting-only normalization;
- baseline→candidate diff-check is waived ONLY for those 9 frozen-contract hard-break lines;
- `git diff --check a06d328... HEAD` must remain clean;
- baseline→candidate excluding the frozen contract must remain clean;
- no other diff-check warning is waived.

Durable issue #176 waiver comment:
`5994173149`

## K. Final local acceptance status — CURRENT LIVE BOUNDARY

First attempt:
- an inspection-only hold blocked the very first Bash command;
- no shell command/test/database/checkpoint ran;
- repository/task state unchanged.

A later real user prompt explicitly replaced/cleared the hold and authorized acceptance-only shell/test/temp-DB/temp-evidence actions while preserving repository immutability.

That next attempt reached:
- Stage 0 identity/frozen-contract/migration checks: PASS;
- repository-wide critical Ruff: PASS;
- worktree clean;
- exact candidate/origin/main identities correct;
- frozen contract unchanged since `a06d328...`;
- migration count from worktree = 40 / latest 040;
- then stopped at baseline→candidate diff-check because of the 9 frozen Markdown hard breaks;
- PostgreSQL full suite, release gate, wheel smoke and final-local checkpoint were not run in that stopped attempt.

ChatGPT then issued the explicit formatting waiver and a continuation prompt that requires before Stage 2:
1. `git diff --check a06d32801a22a9c17439a0e03c081dae57ba2367 HEAD` = clean;
2. baseline→candidate excluding `docs/architecture/EXPERIENCE-INTELLIGENCE-E5-CONTRACT-2026-10-05.md` = clean.

Then the same local run must perform:
- one fresh full PostgreSQL suite on a same-run `_test` DB;
- same-DB migration count/highest proof before pytest;
- isolated config proof;
- exact pass/skip/fail/error counts and skip reasons;
- DB drop proof;
- release gate once;
- wheel-build/install/import-smoke evidence;
- final exact Git identity;
- exactly one explicit final-local-acceptance Chairman checkpoint.

**At the moment of this handoff seal, the user has not yet supplied that resumed local acceptance result. Treat it as PENDING. Do not claim it passed.**

## L. Diff hygiene classification for the pending final acceptance

Already proven:
- repo-wide critical Ruff: PASS;
- frozen contract unchanged from `a06d328...`;
- post-freeze diff-check was reported clean in the stopped run.

Still required in the resumed run:
- repeat/confirm post-freeze diff-check clean;
- baseline→candidate excluding frozen contract clean.

Final report must classify baseline→candidate diff-check as:
`PASS WITH EXPLICIT FROZEN-CONTRACT FORMATTING WAIVER`

only if the two bounded checks above are clean.

## M. What to do with the next local Claude reply

If the user supplies a green final-local-acceptance result:
1. verify HEAD = `d39fabb22484a664e863c1603e2054d1ef0723c4`;
2. verify tree = `fd00975275a1f8cc697bd4c570f994812e49f3b9`;
3. verify worktree clean;
4. verify same acceptance DB had 40 migrations / highest 040 before suite;
5. verify `ISOLATED_VRES_CONFIG=PASS`;
6. verify full suite has zero failures/errors and classify every skip;
7. verify acceptance DB was dropped and original drifted DB untouched;
8. verify release gate = `PASSED_WITH_EXPLICIT_LIVE_GATES`;
9. verify gate commit/tree/dirty match exact candidate;
10. verify wheel filename/SHA256/bytes/source compare count and wheel-import-smoke PASS;
11. verify one final-local-acceptance checkpoint exists;
12. verify no protected validation request exists.

If any of those are missing or failed:
- STOP;
- do not open PR;
- do not call protected validation;
- classify the exact evidence gap/defect.

If all are green:
- ChatGPT rechecks remote E5 head has not moved;
- create PR from `issue-176-e5-capability-procedure-experience` to `main`;
- require exact-head pull_request CI on `d39fabb...`;
- inspect all jobs/steps and release-gate artifact/digest;
- do not protect-validate before exact-head CI is green.

## N. Protected validation protocol after exact-head CI

Only after exact-head PR CI succeeds on unchanged `d39fabb...`:
1. local Claude returns to correctly rooted E5 worktree;
2. read-only reverify task/candidate/CI evidence;
3. create ONE explicit current-user-turn Chairman freeze checkpoint; do not reuse old Chunk checkpoints as the mechanical reply-gate anchor;
4. compute complete E5 base→head review scope;
5. call `validation_prepare` exactly once;
6. delegate exactly `vres-os:validator`, no model override;
7. protected host must select Fable/high;
8. validator must NOT launch background/nested agents;
9. validator's first terminal stop must contain the complete canonical JSON report;
10. `outcome=passed` requires every reported check status = `passed`;
11. while pending, parent may only make non-advancing reply-gate calls and must obtain `mode=validation_in_flight`;
12. after completion, trust host/Vres evidence first, not prose.

Required PASS evidence:
- terminal request status `passed`;
- task validation status `passed`;
- host-observed Fable-family model;
- agent/session identity;
- completed_at;
- exact SHA/tree;
- exact manifest/hashes/state digest;
- no material mutation while pending.

No automatic retry on rejected/stale/failed/wrong-model/wrong-SHA/wrong-scope/non-terminal result.

## O. Merge / closure sequence after protected PASS

On clean host-recorded E5 PASS:
- do not merge locally;
- ChatGPT re-verifies PR exact head;
- guarded expected-head merge;
- capture new authoritative main SHA;
- require separate post-merge `push` CI on that exact main SHA;
- inspect suite/release-gate/artifact evidence;
- durably mark E5 DONE in checklist/handoff/issue;
- complete E5 Vres task exactly once after current protected PASS and post-main closure;
- only then start E6.

## P. Remaining program after E5

1. E6 — observability + experience utility evidence;
2. E7 — benchmark + security ladder;
3. E8 — Chairman integration + protected acceptance;
4. E9 physical Experience Intelligence criteria carried into #169;
5. #165 Chairman model policy;
6. #166;
7. #167;
8. #168 project adoption + canonical Claude scaffold;
9. #169 integrated Windows / Visual Studio live acceptance;
10. #170 production readiness/go-live;
11. post-#170 Organizational Architecture & Specialist Intelligence/full-team enhancement.

Do not let the post-#170 backlog interrupt E5–#170.

## Q. Fresh-chat resume prompt

```text
Resume the Vres-OS preproduction program from the newest canonical durable handoff.

Repository:
vosser24/Vres-OS

Canonical documentation branch:
docs-execution-checklist-20260927

Read first:
docs/PREPRODUCTION-EXECUTION-CHECKLIST-2026-09-27.md
docs/handoffs/PREPRODUCTION-RESUME-HANDOFF-2026-09-27.md

Newest authoritative boundary:
# 31. 2026-10-05 #176 E5 coherent candidate / final-local-acceptance pending seal

Do not resume from section #30 or older E5-start instructions.

AUTHORITATIVE MAIN:
a0a2769b99f4893733568194c0aa68e78e73aeab

E5 BRANCH:
issue-176-e5-capability-procedure-experience

E5 TASK:
TASK-20261005-dc0e7a9e38

FROZEN E5 CONTRACT:
a06d32801a22a9c17439a0e03c081dae57ba2367

COHERENT FINAL E5 CANDIDATE:
d39fabb22484a664e863c1603e2054d1ef0723c4

E5 TREE:
fd00975275a1f8cc697bd4c570f994812e49f3b9

PR:
none yet

E5 Chunks 1–3 are implemented and targeted-green.
Do not rerun their targeted ladders unless bytes change or a concrete evidence gap is found.

Important targeted evidence:
- Chunk 1 checkpoint CP-20261005-60dd993356
- Chunk 2 checkpoint CP-20261005-8e70bf99ac
- host pre-compact bookkeeping CP-20261005-bb0d29c4e5
- Chunk 3 checkpoint CP-20261005-8fe3a4f070
- Chunk 3: 235 unit/static + 8 focused E5 + 122 E3/E4 + 6 D1 + 19 D2 + 39 E4 revocation, zero skips/warnings

Frozen-contract formatting waiver:
- lines 3–7, 39, 52–54 contain intentional two-space Markdown hard breaks already present at a06d328
- do not edit the frozen contract
- baseline diff-check is waived only for those nine lines
- post-freeze diff-check and baseline-excluding-contract diff-check must be clean
- durable issue comment id 5994173149

CURRENT LIVE STATE:
A resumed local final-acceptance run was instructed after the waiver, but its result has NOT yet been supplied in this handoff.
Do not assume PASS.

When the user supplies the local Claude result:
- audit full fresh PostgreSQL suite evidence
- audit same-DB migration count/highest
- audit isolated VRES_DATA_DIR proof
- audit release gate and candidate-wheel build/install/import smoke
- audit exact SHA/tree/clean worktree
- audit one explicit final-local-acceptance checkpoint
- require no protected validation request yet

If all final-local evidence is green:
1. verify remote head remains d39fabb22484a664e863c1603e2054d1ef0723c4
2. create the E5 PR
3. require exact-head pull_request CI and artifact evidence
4. only then run one current-turn protected validation freeze/prepare/vres-os:validator Fable-high sequence
5. on host-recorded PASS, guarded merge
6. require post-main push CI on exact merge SHA
7. close E5 and complete the Vres task
8. only then start E6

If final-local acceptance failed:
STOP and classify the exact defect. Do not create PR or protected validation.

Methodology:
- ChatGPT primary for architecture/repo/PR/CI/docs
- local Claude for Windows/local PostgreSQL/installed runtime/host/live-machine proof
- single writer per branch
- no duplicate expensive full-suite/release-gate/protected-validation evidence without changed bytes or a concrete gap
```

---

# 32. 2026-10-05 #176 E5 one-line canonical-status fix / reacceptance seal

This is the newest authoritative handoff boundary. It supersedes section 31 for current E5 execution state.

## A. Exact repository boundary

Repository:
`vosser24/Vres-OS`

Authoritative main:
`a0a2769b99f4893733568194c0aa68e78e73aeab`

E5 branch:
`issue-176-e5-capability-procedure-experience`

E5 task:
`TASK-20261005-dc0e7a9e38`

Frozen E5 contract:
`a06d32801a22a9c17439a0e03c081dae57ba2367`

Superseded coherent candidate:
`d39fabb22484a664e863c1603e2054d1ef0723c4`

Superseded tree:
`fd00975275a1f8cc697bd4c570f994812e49f3b9`

Current corrected candidate:
**`230c4fdb5a7674fe13518796be68a77848ff0561`**

Current corrected tree:
**`97f98e2ad666df014bbc22270cc677aacd65a21f`**

PR:
**none yet**

E5 remains 40 migrations through:
`040_context_refresh_attestation.sql`

## B. Why d39fabb is superseded

The first full PostgreSQL acceptance cycle was finally allowed to run after the inspection-only hold was explicitly replaced and the frozen-contract Markdown hard-break waiver was issued.

Waiver checks:
- `git diff --check a06d328... HEAD`: PASS;
- baseline→candidate excluding the frozen E5 contract: PASS.

Fresh acceptance database:
`vres_e5_final_62085d1c361f_test`

Environment:
- `ISOLATED_VRES_CONFIG=PASS`;
- same acceptance DB migration count: **40**;
- same acceptance DB highest migration: `040_context_refresh_attestation.sql`;
- database dropped after the run;
- original drifted database behind `pg_issue163_test_dsn` untouched.

Full suite result on `d39fabb...`:
- **2205 passed**;
- **4 skipped**;
- **1 failed**;
- exit code 1;
- approximately 21m32s.

Because the full suite failed:
- release gate was NOT run;
- no final-local-acceptance checkpoint was created;
- no PR was created;
- no protected validation request was created.

## C. Exact failure

Failing test:
`tests/test_source_revocation_unit.py::test_only_source_revocation_writes_the_revoked_status`

Assertion expected the only non-session code-level revoked literal reader to be:
`knowledge_status.py`

Actual static readers additionally contained:
`experience_retrieval.py`

The test is a repository governance guard, not a runtime behavior test. It scans Python string constants for the exact word `revoked` to enforce status-literal ownership.

## D. Root cause

E4 main already imported and used the canonical:
`REVOKED_STATUS`

E5 Chunk 1 introduced one new hardcoded read-side literal in the structural-capability helper:

```python
disallowed_flags = {"historical", "not_current", "revoked", "retired", "expired"}
```

This violated the existing canonical-status-owner rule even though runtime semantics were equivalent.

The static governance test correctly detected it.

Classification:
- **real E5 code defect**;
- bounded;
- read-side canonical-constant violation only;
- not an environment problem;
- not a stale test;
- not a test-harness defect.

Do NOT relax the test allow-list.

## E. Bounded fix

ChatGPT changed exactly one line:

from:
```python
{"historical", "not_current", "revoked", "retired", "expired"}
```

to:
```python
{"historical", "not_current", REVOKED_STATUS, "retired", "expired"}
```

Commit:
**`230c4fdb5a7674fe13518796be68a77848ff0561`**

Tree:
**`97f98e2ad666df014bbc22270cc677aacd65a21f`**

Diff from `d39fabb...`:
- one file;
- one insertion;
- one deletion;
- file: `src/vres_os/experience_retrieval.py`.

Unchanged:
- all tests;
- frozen E5 contract;
- migration set;
- MCP surfaces;
- capability/procedure write authority;
- routing/model policy;
- prompts;
- E6 surfaces.

Durable issue #176 fix classification comment:
`5997730568`

## F. Frozen-contract whitespace waiver remains in force

The E5 contract's intentional Markdown hard line breaks remain unchanged.

Waived baseline diff-check lines:
- 3–7;
- 39;
- 52–54.

All were already present at frozen contract commit `a06d328...`.

Do not edit them.

For the corrected candidate require:
1. `git diff --check a06d328... HEAD` = clean;
2. baseline→candidate excluding the frozen contract = clean.

No other whitespace warning is waived.

## G. Targeted E5 development evidence remains useful but exact candidate identity changed

Chunks 1–3 targeted evidence remains architectural/regression support, but exact acceptance must be rerun because source bytes changed by one line.

Do NOT rerun every historical Chunk 1/2/3 ladder.

Required bounded correction proof:
- exact failing governance test;
- focused E5 retrieval integration affected by the one-line set membership change;
- critical Ruff;
- bounded diff checks.

If bounded correction proof passes, rerun one complete final acceptance cycle on the corrected candidate.

## H. Required bounded correction proof

From a clean local E5 worktree fast-forwarded to exact:
`230c4fdb5a7674fe13518796be68a77848ff0561`

require:
- tree `97f98e2ad666df014bbc22270cc677aacd65a21f`;
- origin branch same exact SHA;
- origin/main still `a0a2769...`;
- worktree clean.

Run:
1. `tests/test_source_revocation_unit.py::test_only_source_revocation_writes_the_revoked_status`;
2. `tests/test_experience_retrieval.py`;
3. `tests/integration/test_e5_capability_retrieval.py`;
4. `tests/integration/test_e5_procedure_history.py`;
5. critical Ruff on `experience_retrieval.py` plus these tests;
6. post-freeze diff-check;
7. baseline→head excluding frozen contract diff-check.

Use a fresh isolated disposable PostgreSQL DB for the integration tests and the established empty `VRES_DATA_DIR` methodology.

No checkpoint is needed merely for the bounded correction if the final full acceptance follows immediately.

## I. Corrected-candidate final acceptance

If the bounded correction proof is green, run exactly one coherent final acceptance cycle:

### Fresh full PostgreSQL suite
- new unique `_test` DB;
- use `pg_issue163_test_dsn` only as admin/server credential source;
- never run against or repair its drifted DB;
- empty isolated `VRES_DATA_DIR`;
- verify empty provenance writer / migration user;
- same acceptance DB migration count = 40;
- same acceptance DB highest migration = 040;
- run complete `pytest -q -ra`;
- zero failures/errors required;
- record every skip and reason;
- drop DB after evidence capture.

### Release gate
Only after full suite passes:
- one fresh outside-checkout evidence directory;
- isolated `VRES_DATA_DIR`;
- no DB vars;
- require `PASSED_WITH_EXPLICIT_LIVE_GATES`;
- exact git commit/tree/dirty evidence;
- wheel build;
- exact Python/SQL byte comparison;
- temporary wheel installation;
- wheel-import-smoke PASS;
- capture wheel filename/SHA256/bytes/source-files-compared.

### Final local checkpoint
Only after full suite + release gate + final Git identity are green:
- create exactly one intentional final-local-acceptance Chairman checkpoint;
- this is NOT the protected-validation freeze;
- next action must hand control to ChatGPT for PR creation/exact-head CI;
- do not call `validation_prepare`.

## J. PR / CI / protected-validation sequence after local acceptance

If exact corrected candidate is locally green:

1. ChatGPT verifies remote branch exact head: `230c4fdb5a7674fe13518796be68a77848ff0561`;
2. verify main unchanged: `a0a2769b99f4893733568194c0aa68e78e73aeab`;
3. create E5 PR;
4. require exact-head pull_request CI on `230c4fdb...`;
5. inspect jobs/steps/full PG suite/installed-runtime/release-gate artifact + digest;
6. only then return to local E5 session for ONE current-turn freeze checkpoint;
7. recompute complete E5 artifact scope;
8. `validation_prepare` exactly once;
9. delegate exactly `vres-os:validator`;
10. no model override; host Fable/high;
11. no validator background/nested workers;
12. first terminal stop must contain complete canonical JSON;
13. PASS requires every check status `passed`;
14. while pending, no material mutation and require `validation_in_flight` for any interim reply;
15. trust host/Vres evidence first.

No automatic retry on a failed protected request.

## K. Merge / closure after protected PASS

On host-recorded protected PASS:
- guarded expected-head merge by ChatGPT;
- require post-merge `push` CI on exact new main SHA;
- verify full suite/release gate/artifact;
- durably close E5 in issue/checklist/handoff;
- complete E5 Vres task exactly once after current protected PASS and post-main closure;
- only then begin E6.

## L. Current E5 task state

Task:
`TASK-20261005-dc0e7a9e38`

Latest intentional targeted-development checkpoint:
`CP-20261005-8fe3a4f070`

Host compaction checkpoint:
`CP-20261005-bb0d29c4e5` with reason `pre_compact`

No final-local-acceptance checkpoint was created after the failed `d39fabb...` full suite.

No protected validation request exists for E5.

The task remains unfinished.

## M. Fresh-chat resume prompt

```text
Resume the Vres-OS preproduction program from the newest canonical durable handoff.

Repository:
vosser24/Vres-OS

Canonical documentation branch:
docs-execution-checklist-20260927

Read first:
docs/PREPRODUCTION-EXECUTION-CHECKLIST-2026-09-27.md
docs/handoffs/PREPRODUCTION-RESUME-HANDOFF-2026-09-27.md

Newest authoritative boundary:
# 32. 2026-10-05 #176 E5 one-line canonical-status fix / reacceptance seal

Do not resume from section #31 or the superseded d39fabb candidate.

AUTHORITATIVE MAIN:
a0a2769b99f4893733568194c0aa68e78e73aeab

E5 BRANCH:
issue-176-e5-capability-procedure-experience

E5 TASK:
TASK-20261005-dc0e7a9e38

FROZEN CONTRACT:
a06d32801a22a9c17439a0e03c081dae57ba2367

SUPERSEDED CANDIDATE:
d39fabb22484a664e863c1603e2054d1ef0723c4

CURRENT CORRECTED CANDIDATE:
230c4fdb5a7674fe13518796be68a77848ff0561

CURRENT TREE:
97f98e2ad666df014bbc22270cc677aacd65a21f

The first full suite on d39fabb produced 2205 passed / 4 skipped / 1 failed.
The failure was test_source_revocation_unit.py::test_only_source_revocation_writes_the_revoked_status.

Root cause:
E5 hardcoded one read-side "revoked" literal in experience_retrieval.py.
This violated the canonical status-literal owner rule.
The bounded fix replaces only that literal with imported REVOKED_STATUS.
The governance test remains unchanged.

Next:
1. fast-forward local E5 worktree to exact 230c4fdb...
2. run bounded correction proof: failing governance test + focused E5 retrieval + Ruff + bounded diff checks
3. if green, rerun one full fresh PostgreSQL suite on the corrected exact candidate
4. if full suite green, run release gate once and capture wheel smoke evidence
5. create one final-local-acceptance checkpoint
6. return evidence to ChatGPT
7. only then create PR / exact-head CI
8. only after exact-head CI green perform one current-turn protected Fable/high validation
9. guarded merge + post-main CI + E5 task completion
10. only then E6

Do not rerun all historical Chunk 1–3 ladders.
Do not edit the frozen contract.
Preserve the frozen-contract Markdown hard-break waiver exactly as section #32 describes.
```

---

# 33. 2026-10-05 #176 E5 protected PASS / guarded merge / post-main acceptance seal

This is the newest authoritative handoff boundary. It supersedes section #32 for current execution state.

## A. Exact accepted repository boundary

Repository:
`vosser24/Vres-OS`

E5 frozen contract:
`a06d32801a22a9c17439a0e03c081dae57ba2367`

Final E5 candidate:
`230c4fdb5a7674fe13518796be68a77848ff0561`

Accepted E5 tree:
`97f98e2ad666df014bbc22270cc677aacd65a21f`

PR:
`#183`

Authoritative product main after guarded merge:
**`6af7bddf246e0f628c3e52add9528742e85189ca`**

E5 Vres task:
`TASK-20261005-dc0e7a9e38`

Task status at this seal:
**active; repository/acceptance closure complete; local task_complete still required exactly once.**

## B. Final local acceptance evidence

Final-local checkpoint:
`CP-20261005-949900c05d`

Corrected candidate full Windows/PostgreSQL suite:
- **2206 passed**;
- **4 skipped**;
- **0 failed**;
- **0 errors**;
- **0 warnings**;
- fresh isolated DB;
- migrations 40 / latest 040;
- `ISOLATED_VRES_CONFIG=PASS`;
- `DROPPED=True`;
- historical drifted DB untouched.

Local release gate:
- `PASSED_WITH_EXPLICIT_LIVE_GATES`;
- candidate identity clean;
- candidate wheel build/install/import and exact Python/SQL byte comparison PASS;
- wheel SHA256 `91d47125e14aa52cf8bced8355fb212802ff1f158413b3339597316e8080b180`.

Do not rerun this evidence unless bytes change or a concrete gap is discovered.

## C. PR CI evidence

PR #183 exact accepted head:
`230c4fdb5a7674fe13518796be68a77848ff0561`

CI #472 / run:
`37339979267`

Result:
- SUCCESS;
- full suite: **2207 passed / 3 skipped**;
- installed runtime smoke PASS;
- release gate PASS;
- artifact digest:
  `sha256:49c5a001f9f90bd2c6013a43ce03fc9bdb4320c98df96194fce9dd8228ce6748`.

GitHub's pull_request checkout synthetic merge:
`70abf6d95a44fa92b086c61308641bcb96007a90`

This synthetic object introduced zero file changes relative to the accepted candidate and shared exact tree:
`97f98e2ad666df014bbc22270cc677aacd65a21f`.

Treat this as PR checkout metadata, not candidate mutation.

## D. Protected validation history

Cycle 1:
- checkpoint: `CP-20261005-fe30d00bec`;
- request: `VAL-afdb8d037183467e`;
- protected Fable/high;
- outcome failed because **2 checks were not_run**;
- **0 checks failed**;
- evidence gaps only: PostgreSQL runtime proof and independent CI readback.

No automatic retry occurred.

Cycle 2 was explicitly authorized on unchanged candidate bytes.

Cycle 2:
- checkpoint: `CP-20261005-c9c6ca275f`;
- request: `VAL-21170237cd6a482c`;
- validator: `vres-os:validator`;
- host-observed model: `claude-fable-5-1`;
- effort: high;
- host-recorded outcome: **passed**;
- **15/15 checks passed**;
- **0 failed**;
- **0 not_run**.

Direct validator PostgreSQL proof:
- DB `vres_e5_val2_e1fe5557c98c_test`;
- 40 migrations / latest 040;
- isolated config PASS;
- four required integration files: **111 passed**;
- exit 0;
- `DROPPED=True`;
- drifted DB untouched.

Direct validator GitHub REST proof:
- PR head/base exact;
- CI #472 exact accepted head and success;
- all seven required CI steps success;
- artifact digest exact;
- synthetic merge zero changed files.

No repository mutation occurred during either protected cycle.

## E. Guarded merge

ChatGPT reverified immediately before merge:
- main = `a0a2769b99f4893733568194c0aa68e78e73aeab`;
- E5 branch = exact final candidate;
- PR #183 open/mergeable;
- PR head exact.

Merge used expected-head protection against:
`230c4fdb5a7674fe13518796be68a77848ff0561`

GitHub merge result:
- merged = true;
- new main:
  **`6af7bddf246e0f628c3e52add9528742e85189ca`**.

## F. Post-main push CI

Mandatory post-merge push CI:
- CI #473;
- run id `37346476024`;
- event: push;
- branch: main;
- exact head:
  `6af7bddf246e0f628c3e52add9528742e85189ca`;
- job `111886190218`;
- conclusion: SUCCESS.

All substantive steps passed:
- install runtime;
- repository-wide critical lint;
- strict architecture-governance lint;
- strict authority/model-evidence lint;
- full PostgreSQL suite;
- installed-runtime import smoke;
- local release gate;
- evidence upload.

Full suite:
**2207 passed / 3 skipped**

Release gate:
- `PASSED_WITH_EXPLICIT_LIVE_GATES`;
- `git_commit=6af7bddf246e0f628c3e52add9528742e85189ca`;
- `git_tree=97f98e2ad666df014bbc22270cc677aacd65a21f`;
- `dirty=false`;
- `error=null`;
- release-gate unit/static tests: **1520 passed / 690 skipped**;
- coverage: **55.34% lines / 46.93% branches**;
- migrations: **40**;
- evidence file count: **410**.

Post-main artifact:
- id `11360229051`;
- name `release-gate-evidence`;
- digest:
  `sha256:a8837251697e4a23c944b18e9a71a319a8560873867fe258baf51c92a7b4e076`;
- expired=false;
- bound to exact new main.

Post-main release-gate wheel:
- `vres_os-0.2.0a1-py3-none-any.whl`;
- SHA256:
  `4d3ccc33df642db4c804142586725686b65a6329f9d829bd1cac508c3b561649`;
- bytes: **382832**;
- exact Python/SQL source-byte proof PASS;
- installed import smoke PASS.

The PostgreSQL service log contains expected ERROR/FATAL entries generated by negative/fail-closed tests; the actual test and gate conclusions are green.

## G. Issue / audit references

Relevant durable records:
- frozen-contract Markdown hard-break waiver: issue comment `5994173149`;
- one-line canonical-status fix classification: issue comment `5997730568`;
- PR CI synthetic-merge exact-tree classification: PR comment `5998674253`;
- protected-validation cycle-1 bounded recovery authorization: PR comment `5999110178`;
- protected validation PASS record summary: PR comment `5999333268`.

## H. E5 result

E5's implementation and acceptance objectives are complete:
- capability-centric experience retrieval;
- procedure/episode/feedback links;
- validated success/failure history;
- E4 revocation integration;
- read-only deterministic retrieval;
- no opaque expertise score;
- no automatic prompt rewrite;
- no E6 observation writes.

No migration was added by E5.

Accepted truth owners remain the existing capabilities/proofs, procedures/versions/runs/feedback, immutable experience episodes, relations, task identity and validation/source/artifact evidence.

## I. Carry-forward observations — not E5 blockers

Carry into E7 benchmark/security hardening rather than reopening the accepted E5 candidate:
- strict-ruleset Ruff observations UP017/B007/B905 reported by the validator but not enforced by current CI;
- first protected attempt noted E5 contract cases 15, 16 and 24 do not have dedicated one-test-per-criterion coverage, although the complete protected cycle later passed with direct runtime/source evidence.

Do not mutate E5 solely for those observations.

## J. Exact next action — LOCAL VRES TASK COMPLETION ONLY

Before E6 begins, return to the same local E5 Vres host/session and complete:

`TASK-20261005-dc0e7a9e38`

exactly once.

Preconditions are already satisfied:
- protected validation current PASS:
  `VAL-21170237cd6a482c`;
- candidate files unchanged since protected PASS;
- guarded PR merge complete;
- post-main push CI #473 green;
- canonical issue/checklist/handoff closure recorded.

Local completion instructions:
1. do not edit repository files;
2. do not invalidate protected validation;
3. do not rerun tests/release gate/validator;
4. read back current task and validation evidence;
5. call `task_complete` exactly once;
6. read task back and require status=completed / completion timestamp present;
7. return task-completion evidence to ChatGPT.

If `task_complete` refuses because validation is stale or task state changed:
STOP and return exact evidence.
Do not repair or revalidate automatically.

**E6 MUST NOT START BEFORE SUCCESSFUL E5 TASK COMPLETION.**

## K. Remaining program after E5 task completion

Next tranche:
**E6 — observability + experience utility evidence**

Then:
- E7 — benchmark + security ladder;
- E8 — Chairman integration + protected acceptance;
- E9 criteria carried into #169;
- #165;
- #166;
- #167;
- #168;
- #169 integrated Windows / Visual Studio acceptance;
- #170 production readiness / go-live;
- post-#170 Organizational Architecture & Specialist Intelligence / full-team enhancement.

## L. Fresh-chat resume prompt

```text
Resume the Vres-OS preproduction program from the newest canonical durable handoff.

Repository:
vosser24/Vres-OS

Canonical documentation branch:
docs-execution-checklist-20260927

Read first:
docs/PREPRODUCTION-EXECUTION-CHECKLIST-2026-09-27.md
docs/handoffs/PREPRODUCTION-RESUME-HANDOFF-2026-09-27.md

Newest authoritative handoff boundary:
# 33. 2026-10-05 #176 E5 protected PASS / guarded merge / post-main acceptance seal

Newest authoritative checklist boundary:
### 17. 2026-10-05 #176 E5 merged / post-main accepted — local Vres task completion only

AUTHORITATIVE PRODUCT MAIN:
6af7bddf246e0f628c3e52add9528742e85189ca

E5 FINAL CANDIDATE:
230c4fdb5a7674fe13518796be68a77848ff0561

E5 ACCEPTED TREE:
97f98e2ad666df014bbc22270cc677aacd65a21f

E5 PR:
#183 MERGED

PROTECTED PASS:
VAL-21170237cd6a482c
15/15 passed, 0 failed, 0 not_run
Fable/high

POST-MAIN CI:
#473 / run 37346476024
SUCCESS
2207 passed / 3 skipped
release gate PASSED_WITH_EXPLICIT_LIVE_GATES
artifact digest sha256:a8837251697e4a23c944b18e9a71a319a8560873867fe258baf51c92a7b4e076

E5 VRES TASK:
TASK-20261005-dc0e7a9e38

CURRENT ACTION:
Complete that E5 Vres task exactly once on the existing local host/session.
Do not edit code, rerun tests, rerun validation, or start E6 first.

After successful task_complete readback, return evidence to ChatGPT.
Only then start E6.
```

