# Vres-OS — Preproduction Resume Handoff

Date: 2026-09-28  
Repository: `vosser24/Vres-OS`  
Canonical checklist: `docs/PREPRODUCTION-EXECUTION-CHECKLIST-2026-09-27.md`

This is the canonical detailed continuation record after completing #163. A fresh session should be able to resume from this file and the checklist without relying on chat memory.

The operating rule remains strict:

> **Do not start implementation of a later checklist item until the previous item is fully DONE.**

At this handoff boundary:

- **#163 is DONE.**
- **#174 is the first and only allowed next implementation/acceptance item.**
- #164 and everything after it remain blocked by sequence.

---

# 1. Exact continuation point

Authoritative `main`:

`7f9961b5980f1a229cece4902f9e1d709e397e22`

This is the merge commit of PR #173 / issue #163.

Post-merge main CI:

- workflow: Vres-OS CI
- run: **#438**
- run ID: `36420420225`
- head: `7f9961b5980f1a229cece4902f9e1d709e397e22`
- status: **completed / success**
- PostgreSQL-backed suite: **1056 passed, 1 skipped**
- repository critical lint: PASS
- strict protected-surface lint: PASS
- installed-runtime import smoke: PASS
- local release gate: `PASSED_WITH_EXPLICIT_LIVE_GATES`

Issue #163:

- state: **closed**
- reason: **completed**
- closed: 2026-09-28
- PR #173: merged

Physical Windows/customer-environment acceptance was explicitly **not** claimed by #163 and remains owned by #169.

---

# 2. Canonical sequential execution order

The order remains:

1. **#163 — Credential Broker — DONE**
2. **#174 — Engineering Architecture Governance — ACTIVE NEXT**
3. **#164 — Secret-safe onboarding — NOT STARTED**
4. **#176 — Experience Intelligence / Governed Agent Learning — PLAN COMPLETE, IMPLEMENTATION NOT STARTED**
5. **#165 — Chairman model policy — NOT STARTED**
6. **#166 — Global Claude adoption — NOT STARTED**
7. **#167 — Current-user Data Source Registry — NOT STARTED**
8. **#168 — Project adoption / canonical scaffold — NOT STARTED**
9. **#169 — Integrated Windows / Visual Studio live acceptance — NOT STARTED**
10. **#170 — Production Readiness / Go-Live — NOT STARTED**

Do not begin #164 until #174 is fully DONE.

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

# 13. Active next item — #174 Engineering Architecture Governance

Issue:

**#174 — Engineering Architecture Constitution and Fable-validated adoption planning foundation**

PR:

**#175**

Branch:

`issue-174-engineering-architecture-governance`

Current live PR head as of this handoff:

`9756b44d4ae953db327b10072e70003e51df9404`

Important correction versus older handoff text:

- older recorded held head: `d0b59289e443dab14dd658411a0ee1d3d61d23c7`
- current head: `9756b44d4ae953db327b10072e70003e51df9404`
- current head is **2 commits ahead** of `d0b59289...`
- those two commits harden the constitution/handoff:
  - `c42b2fb4269ae85a9e7770fd376d2ad8faa07768` — enforcement-before-assurance constitution rule
  - `9756b44d4ae953db327b10072e70003e51df9404` — record enforcement-governance hardening

Current #174 exact-head CI:

- run: **#437**
- run ID: `36349196127`
- conclusion: **success**

However #174 is **not merge-ready now** because #163 advanced authoritative main.

Current relationship to main:

- authoritative main: `7f9961b5980f1a229cece4902f9e1d709e397e22`
- #174 head: `9756b44d4ae953db327b10072e70003e51df9404`
- merge base: `f0a69c3e471fe25c6547ee1af162019caf290d49`
- #174 head is **68 commits ahead** of current main from the merge base;
- #174 head is **30 commits behind** current main.

This means the next session must integrate current main before accepting #174.

Do not treat old CI #437 as sufficient after that integration.

---

# 14. What #174 already builds

The held branch contains:

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

# 15. Exact #174 resume methodology

A fresh session must work only #174.

Start with read-only verification:

1. read this handoff and the canonical checklist;
2. fetch `origin/main`;
3. verify main is still `7f9961b5980f1a229cece4902f9e1d709e397e22` or record any legitimate advancement;
4. fetch PR #175;
5. verify current #174 head before making any change;
6. inspect branch/worktree cleanliness;
7. compare #174 against authoritative main;
8. inspect integration overlap before merging histories.

Because #174 already has a long reviewed history, prefer a history-preserving update of the branch with current main rather than casually rewriting dozens of commits. A normal merge of current main into the #174 branch is acceptable as the “update/rebase” step if it produces the smallest auditable integration and avoids a force push.

Do not blindly resolve conflicts.

Pay special attention to any overlap involving:

- Claude contract/scaffold behavior;
- MCP entrypoint/registration;
- Chairman rules;
- onboarding/start-vres skills;
- CI workflow;
- any lifecycle/security surface introduced by #163.

After integration:

1. inspect exact diff against new main;
2. resolve only real integration drift;
3. run targeted architecture-governance tests;
4. run the full PostgreSQL-backed suite as applicable;
5. push the exact new head;
6. require exact-head GitHub CI green;
7. run protected `vres-os:validator` with pinned Fable/high on that exact head;
8. do not substitute another model if Fable/high is unavailable;
9. update #174 handoff/docs if the head/evidence changed;
10. merge PR #175 only after all gates;
11. verify post-merge main CI green;
12. close #174;
13. update this checklist/handoff;
14. only then start #164.

Do not reuse old #174 Fable/CI evidence as acceptance for the integrated head.

---

# 16. #174 prior evidence is baseline only

Prior held-head CI is useful regression context:

- head: `9756b44d4ae953db327b10072e70003e51df9404`
- CI #437 / `36349196127`: SUCCESS

Older handoff evidence may mention CI #436 and head `d0b59289...`; those are superseded by the current held head and #437.

After main integration, a fresh exact-head CI run is mandatory.

Protected Fable/high must also be rerun on the fresh exact head because base/integration state changes.

---

# 17. After #174

Next is #164 — Secret-safe onboarding.

Do not start #164 until #174 is fully:

- integrated with authoritative main;
- tested;
- protected-validated;
- exact-head CI green;
- merged;
- post-merge CI green;
- closed;
- documented.

#164 must then build deterministic sensitive-path exclusion, pre-model/pre-persistence sanitization, fail-closed uncertain-sensitive handling and Credential Broker reuse.

After #164 comes #176 Experience Intelligence, then #165, #166, #167, #168, #169, #170.

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

During the 2026-09-28 closeout:

- checklist was updated to mark #163 DONE and activate #174;
- a stale #174 held-head reference was corrected to `9756b44d4ae953db327b10072e70003e51df9404`;
- this handoff was rewritten to the current continuation boundary.

These docs changes are direct Git commits on the documentation branch; there is no uncommitted remote edit state from these updates.

Do not merge this documentation branch blindly into product main without first considering the chosen #174 integration flow. The next session should treat the branch as durable planning evidence and decide the cleanest docs/main integration as part of #174 bookkeeping without weakening exact-head acceptance.

---

# 22. Exact next-session mission

A fresh session should begin with this internal mission:

> Resume Vres preproduction from the canonical checklist and 2026-09-28 handoff. #163 is DONE and must not be reopened without a new regression. Work only #174. Verify authoritative main `7f9961b5980f1a229cece4902f9e1d709e397e22`, then verify live PR #175 head (currently `9756b44d4ae953db327b10072e70003e51df9404`). Integrate current main into #174 with an auditable history-preserving update, resolve only real drift, run targeted/full tests, require exact-head CI, run protected Fable/high on the exact integrated head, merge, verify post-merge main CI, close #174 and update docs. Do not start #164 until #174 is DONE.

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

