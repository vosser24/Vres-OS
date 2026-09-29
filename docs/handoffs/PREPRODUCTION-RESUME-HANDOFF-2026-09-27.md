# Vres-OS — Preproduction Resume Handoff

Date: 2026-09-29  
Repository: `vosser24/Vres-OS`  
Canonical checklist: `docs/PREPRODUCTION-EXECUTION-CHECKLIST-2026-09-27.md`

This is the canonical detailed continuation record after completing #164. A fresh session should be able to resume from this file and the checklist without relying on chat memory.

The operating rule remains strict:

> **Do not start implementation of a later checklist item until the previous item is fully DONE.**

At this handoff boundary:

- **#163 is DONE.**
- **#174 is DONE.**
- **#164 is DONE.**
- **#176 is the first and only allowed next implementation/acceptance item.**
- #165 and everything after #176 remain blocked by sequence.

---

# 1. Exact continuation point

Authoritative `main`:

`fe31e30e593a44b8b5ab565fa0db859bbefec0c6`

This is the merge commit of PR #177 / issue #164, on top of the already-completed #163 Credential Broker and #174 Engineering Architecture Governance foundations.

Final #164 candidate:

- branch: `issue-164-secret-safe-onboarding`
- exact reviewed head: `eddfa35d5418e23d6bac8792df0a6d1877d880a8`
- exact authoritative base: `11591b72b3d396a370e315313925e19b8bcb45ec`
- governed engineering final: `ORCHFINAL-20260929-9bf6f3cc85` — `decision_ready=true`
- local isolated PostgreSQL suite: **1164 passed / 3 skipped / 0 failed / 0 errors**
- exact-head CI: **#441** / `36542621233` — SUCCESS
- protected validation: `VAL-f8d685ab3575430c`
- host-observed protected model: `claude-fable-5-1`
- protected result: **PASS**

Post-merge main CI:

- workflow: Vres-OS CI
- run: **#442**
- run ID: `36544341349`
- event: push
- head: `fe31e30e593a44b8b5ab565fa0db859bbefec0c6`
- status: **completed / success**
- PostgreSQL-backed suite: PASS
- installed-runtime smoke: PASS
- local release gate: PASS
- evidence artifact: `11021203984`
- artifact digest: `sha256:8ab24e44232efa860f2d05e4aec8c2014704dc963920fbe98207326051a7fdc6`

Issue #164:

- state: **closed**
- reason: **completed**
- closed: 2026-09-29
- PR #177: merged

#163, #174 and #164 are DONE.

The first and only implementation item now allowed by the frozen sequence is **#176 — Experience Intelligence / Governed Agent Learning**.

Physical/live acceptance deliberately still owned by #169 includes the real first-run optional embedding model acquisition and sanitized wizzard_9 legacy-project proof.

---

# 2. Canonical sequential execution order

The order remains:

1. **#163 — Credential Broker — DONE**
2. **#174 — Engineering Architecture Governance — DONE**
3. **#164 — Secret-safe onboarding — DONE**
4. **#176 — Experience Intelligence / Governed Agent Learning — ACTIVE NEXT / PLAN COMPLETE / IMPLEMENTATION NOT STARTED**
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

# 17. Active next item — #176 Experience Intelligence

#176 is now the only allowed implementation item.

Issue:

**#176 — Experience Intelligence: governed agent learning, episodic memory and evidence-based experience reuse**

Frozen principles:

> **Models are replaceable workers. Vres owns the experience.**

> **Store evidence richly. Retrieve context sparsely. Promote authority conservatively.**

Prerequisites are now satisfied:

- #163 Credential Broker — DONE;
- #164 secret-safe onboarding / pre-model sanitization — DONE;
- #174 Engineering Architecture Governance — DONE.

The implementation must consume those foundations rather than creating parallel authority/security/architecture systems.

Start sequentially with **E1 — contracts + episode ledger**. Do not begin E2 until E1 has its bounded implementation/tests/evidence. Preserve the broader #176 tranche order E1 through E8, with E9 physical proof deferred to #169.

Critical invariants from issue #176:

- no private agent/model self-training or prompt/policy mutation;
- no second generic memory database;
- execution state remains distinct from long-term experience;
- no raw hidden chain-of-thought persistence;
- every reusable experience item retains source/scope/trust/digest provenance;
- untrusted/external content cannot become privileged instruction or authority;
- project/user scope cannot leak;
- failed trajectories cannot silently become positive procedures;
- retrieval scores are relevance signals, not truth probabilities;
- source revocation must invalidate derived influence;
- bounded retrieval and materiality/recurrence discipline prevent “reflect on everything”;
- consequential governance/security changes retain protected Fable/high acceptance.

After #176 comes #165, then #166, #167, #168, #169 and #170.

Do not start #165 until #176 is fully implemented, tested, protected-validated as required, exact-head-CI green, merged, post-merge-CI green, documented and closed.

---

# 18. Experience Intelligence plan remains frozen

Issue #176 implementation is not yet allowed.

Durable plan:

- branch: `docs-176-experience-intelligence-plan-20260927`
- commit: `34f45afa0fb8d5a6a90bef53dec58d9ecef1093d`
- file: `docs/architecture/EXPERIENCE-INTELLIGENCE-PLAN-2026-09-27.md`

Core principle:

> **Models are replaceable workers. Vres owns the experience.**

and:

> **Store evidence richly. Retrieve context sparsely. Promote authority conservatively.**

Do not implement #176 before #163, #174 and #164 prerequisites are DONE.

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

During the 2026-09-29 closeout:

- checklist was updated to mark #174 DONE and activate #164;
- authoritative main was advanced to `11591b72b3d396a370e315313925e19b8bcb45ec`;
- final #174 exact-head CI/protected validation/merge/post-merge CI evidence was recorded;
- this handoff was rewritten to the #164 continuation boundary.

These docs changes are direct Git commits on the documentation branch; there is no uncommitted remote edit state from these updates.

Do not merge this documentation branch blindly into product main without first considering the chosen #174 integration flow. The next session should treat the branch as durable planning evidence and decide the cleanest docs/main integration as part of #174 bookkeeping without weakening exact-head acceptance.

---

# 22. Exact next-session mission

A fresh session should begin with this internal mission:

> Resume Vres preproduction from the canonical checklist and current handoff. #163, #174 and #164 are DONE and must not be reopened without a new regression. Work only #176 Experience Intelligence. Verify authoritative main `fe31e30e593a44b8b5ab565fa0db859bbefec0c6`, read issue #176 plus `docs/architecture/EXPERIENCE-INTELLIGENCE-PLAN-2026-09-27.md` in full, verify the durable plan commit `34f45afa0fb8d5a6a90bef53dec58d9ecef1093d`, then begin only E1 contracts + episode ledger. Reuse existing Vres truth owners, preserve #163/#164 secret/security boundaries and #174 architecture governance, persist no hidden chain-of-thought, and do not begin #165 or later work until #176 is fully DONE.

This is the exact continuation point.

---

# 23. Handoff integrity

Do not rely on old chat summaries when Git/GitHub disagree.

Authoritative hierarchy:

1. current Git/GitHub state;
2. current canonical checklist;
3. this current handoff;
4. issue/PR-specific handoffs;
5. historical handoffs/chat summaries.

When an issue becomes DONE, update the checklist and handoff again before moving on.

