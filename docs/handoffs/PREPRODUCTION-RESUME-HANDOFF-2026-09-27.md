# Vres-OS — Preproduction Resume Handoff

Date: 2026-09-27  
Repository: `vosser24/Vres-OS`

This is the canonical detailed handoff for resuming Vres preproduction work in a fresh session without relying on chat memory.

The operating rule is strict:

> **Do not start implementation of a later checklist item until the previous item is fully DONE.**

Planning/research for later work may exist and may be preserved, but implementation does not skip ahead.

---

# 1. Authoritative sources to read first

A fresh session must begin by reading these durable sources before editing anything:

1. `docs/PREPRODUCTION-EXECUTION-CHECKLIST-2026-09-27.md`
2. `docs/PREPRODUCTION-BUILD-HANDOFF-2026-09-25.md`
3. `docs/PREPRODUCTION-ADOPTION-BUILD-PLAN-2026-09-25.md`
4. this file: `docs/handoffs/PREPRODUCTION-RESUME-HANDOFF-2026-09-27.md`
5. issue #163 and PR #173 in full;
6. issue #174 and PR #175 before touching architecture governance;
7. issue #176 and its Git-frozen plan before any learning/experience implementation;
8. the current issue body for whichever checklist item is first not DONE.

Do not infer state from old chat summaries when Git/GitHub can be checked directly.

---

# 2. Current authoritative repository state

Authoritative `main` at handoff creation:

`f0a69c3e471fe25c6547ee1af162019caf290d49`

This is still the planning base for the in-flight #163 and #174 candidates.

## Open implementation PRs

### PR #173 — #163 Credential Broker

- state: open
- merged: false
- mergeable: true
- base: `f0a69c3e471fe25c6547ee1af162019caf290d49`
- head branch: `issue-163-credential-broker`
- head SHA: `4baf4fadbbd402a0dd523837924e6436f74f27d1`

### PR #175 — #174 Engineering Architecture Governance

- state: open
- merged: false
- mergeable: true
- base: `f0a69c3e471fe25c6547ee1af162019caf290d49`
- head branch: `issue-174-engineering-architecture-governance`
- head SHA: `d0b59289e443dab14dd658411a0ee1d3d61d23c7`

## Planning/governance documentation branches

### Sequential execution checklist

- branch: `docs-execution-checklist-20260927`
- checklist commit before this handoff: `a39cbbe05b50f46707ac7262e486185bf2c01091`
- file: `docs/PREPRODUCTION-EXECUTION-CHECKLIST-2026-09-27.md`

### Experience Intelligence plan

- branch: `docs-176-experience-intelligence-plan-20260927`
- commit: `34f45afa0fb8d5a6a90bef53dec58d9ecef1093d`
- file: `docs/architecture/EXPERIENCE-INTELLIGENCE-PLAN-2026-09-27.md`

These documentation branches are intentionally not merged into `main` yet so they do not disturb the exact reviewed base/head of #163.

---

# 3. Permanent product/governance decisions

The following decisions are frozen and must not be casually reinterpreted.

## 3.1 User-facing Vres interaction

The only user-entered control phrases are:

- `start vres`
- native `clear`

All other Vres operations are Chairman-internal implementation details.

The user should never be required to learn commands for:

- architecture checks;
- routing;
- validation;
- checkpoints;
- credentials;
- data sources;
- memory/learning;
- dependency analysis;
- task state;
- procedure reuse;
- adoption.

Chairman identifies intent and invokes the required workflow internally.

## 3.2 Existing-project architecture adoption

Every established codebase adoption must:

1. run a deterministic read-only architecture/codebase audit;
2. identify proportional architecture profile(s);
3. produce an explicit incremental alignment plan;
4. cover each material finding by a reversible tranche or explicit reviewed defer/exception;
5. mechanically validate the plan contract;
6. freeze exact audit/plan identity;
7. require protected `vres-os:validator` Fable/high validation of the exact plan;
8. remain BLOCKED if Fable/high is unavailable;
9. preserve user decision authority;
10. migrate by reversible strangler tranches, not giant repository reorganization.

## 3.3 Architecture maxim

**Local change. Predictable impact. Explicit dependencies. Shared truth. Isolated failures.**

Architecture scales with application complexity; architectural discipline does not.

## 3.4 Learning / institutional experience

The frozen principle for future #176 implementation is:

> **Models are replaceable workers. Vres owns the experience.**

and:

> **Store evidence richly. Retrieve context sparsely. Promote authority conservatively.**

Agents do not privately self-train or silently rewrite their own prompts/policies.

Experience belongs primarily to durable Vres scopes such as:

- project;
- domain;
- capability;
- procedure;
- task family;
- technology/environment.

The full design is frozen in issue #176 and Git commit `34f45afa0fb8d5a6a90bef53dec58d9ecef1093d`.

## 3.5 Strict sequential execution

Later implementation does not start until the previous checklist item is DONE.

DONE means, where applicable:

- implementation complete;
- required unit/integration/security tests complete;
- protected Fable/high complete;
- required host/Chairman smoke complete;
- docs/handoff current;
- exact-head PR CI green;
- PR merged;
- post-merge authoritative main CI green;
- issue closed;
- deferred physical criteria explicitly carried to #169;
- no unresolved critical blocker remains.

---

# 4. Current required execution order

The canonical current order is:

1. **#163 — Credential Broker**
2. **#174 — Engineering Architecture Governance**
3. **#164 — Secret-safe onboarding**
4. **#176 — Experience Intelligence / Governed Agent Learning**
5. **#165 — Chairman model policy**
6. **#166 — Global Claude adoption**
7. **#167 — Current-user Data Source Registry**
8. **#168 — Project adoption / canonical scaffold**
9. **#169 — Integrated Windows / Visual Studio live acceptance**
10. **#170 — Production Readiness / Go-Live**

No later implementation begins early.

---

# 5. Current active item — #163 Credential Broker

Issue:

**#163 — Credential Broker: current-user reusable secrets and prompt ingress protection**

PR:

**#173**

Current candidate:

`4baf4fadbbd402a0dd523837924e6436f74f27d1`

Base:

`f0a69c3e471fe25c6547ee1af162019caf290d49`

## 5.1 Frozen architecture

Credentials are reusable for the **current Windows user only**.

Durable value storage:

- Windows Credential Locker only.

Vres stores only non-secret metadata/handles and explicit project bindings.

Credential identity belongs to normalized:

- service type;
- origin/service;
- account.

Credential identity does **not** belong to the project that first created it.

Cross-project reuse:

- same current Windows user;
- explicit project binding required.

Another Windows user must not inherit the first user's credential catalog/vault.

`.env` is not durable Vres credential storage.

Environment variables/materialized files are temporary delivery adapters only.

Models consume handles/adapters rather than plaintext whenever possible.

Native Claude/Codex OAuth/vendor authentication remains outside Vres credential ownership.

## 5.2 Implemented #163 surfaces

New credential broker provides:

- normalized website/database/generic service identity;
- stable resource IDs;
- current-user namespace;
- metadata-only list/lookup/discovery;
- explicit per-project bind/unlink;
- child-process environment delivery by handle;
- exact-value output redaction;
- guarded temporary materialization under Vres local-secret area;
- tracked/symlink cleanup refusal;
- pending credential capture;
- explicit confirm/discard;
- deterministic prompt-ingress credential guard;
- no plaintext `credential get`;
- legacy project-scoped `vres secret` compatibility.

## 5.3 Prompt-ingress security contract

High-confidence credentials are intercepted before:

- ConfigStore;
- Repository/session lifecycle;
- task binding;
- PostgreSQL user instruction persistence.

Blocked prompt response uses:

- `decision = block`
- non-secret reason
- `suppressOriginalPrompt = true`

This matters because current Claude Code UserPromptSubmit behavior can otherwise redisplay the blocked original prompt in host feedback.

Ambiguous/conflicting detection:

- block where needed;
- do not silently create reusable credential.

Capture failure:

- still block;
- log only fixed non-secret diagnostic;
- never log provider exception text containing secret material.

## 5.4 Windows-only durable backend

The new Credential Broker refuses its default durable backend off Windows.

Injected fake stores remain usable for deterministic tests.

This protects the frozen architecture that reusable broker values live only in Windows Credential Locker.

## 5.5 #163 automated evidence

Exact-head GitHub Actions:

- run: **#407**
- run ID: `36158185554`
- head: `4baf4fadbbd402a0dd523837924e6436f74f27d1`

Results:

- PostgreSQL-backed full suite: **1056 passed, 1 skipped**
- repository lint: PASS
- strict relevant lint: PASS
- installed-runtime smoke: PASS
- local release gate: PASS

The one skip is the existing Windows-specific Node/libuv inherited-stdin Git hang test.

## 5.6 Important #163 audit fixes already made

During final audit the tranche was hardened with:

1. `suppressOriginalPrompt=true` for credential-blocked UserPromptSubmit;
2. full, non-truncated credential resource handles in CLI output;
3. full, non-truncated pending-capture IDs;
4. explicit Windows-only default durable broker backend;
5. tests for each of those contracts.

Do not revert these as cosmetic changes.

## 5.7 #163 tests already cover

Among other things:

- resource metadata without values;
- two projects linked to one resource;
- unlinked project denied;
- exact-value child output redaction;
- rollback between vault and metadata;
- tracked-path refusal;
- malformed registry fail-closed;
- origin normalization;
- duplicate identity;
- prompt password/token block;
- prompt/value absent from Vres DB/log persistence;
- false positive not silently captured;
- second-user namespace simulation;
- prompt suppression;
- full-length handles;
- Windows-only production backend.

## 5.8 #163 remaining acceptance gates

#163 is **not DONE** yet.

Remaining:

- [ ] canonical protected `vres-os:validator` Fable/high PASS on the exact candidate;
- [ ] required F-15 / Chairman realistic-host smoke for the lifecycle/hook surface;
- [ ] update final handoff/docs if acceptance changes the branch head;
- [ ] rerun exact-head CI after any final head change;
- [ ] merge PR #173;
- [ ] verify new authoritative `main`;
- [ ] verify post-merge main CI green;
- [ ] close #163;
- [ ] explicitly state in closure that physical Windows criteria remain #169 acceptance work.

## 5.9 Protected-validator rule

`plugins/vres-os/agents/validator.md` pins:

- model: Fable
- effort: high

If protected Fable is unavailable or overridden:

- do not substitute Sonnet;
- do not substitute Opus;
- do not substitute Codex;
- do not self-certify;
- status remains BLOCKED.

## 5.10 F-15 requirement

Current finalization policy says changes to session lifecycle/hooks/compaction/reply guard trigger relevant F-05/F-06/F-15 regression surfaces.

#163 changed the UserPromptSubmit lifecycle implementation, therefore a normal Chairman-host realistic smoke remains required before accepting the tranche.

Do not confuse this with #169 final physical Windows acceptance.

## 5.11 Physical #163 criteria intentionally deferred to #169

Do **not** claim these passed during #163 implementation:

1. real Windows Credential Locker under User A;
2. Project A/B reuse without re-entry;
3. unbound Project C denied;
4. real child-only environment / parent remains clean;
5. actual Claude transcript/debug behavior for a blocked synthetic credential;
6. second real Windows account cannot reuse User A resource;
7. uninstall/reinstall Vres does not remove native Claude/Codex authentication.

#169 owns these physical proofs.

## 5.12 Exact next action in a fresh session

The next session must do **only #163 acceptance work**.

First:

1. verify `origin/main` is still `f0a69c3e471fe25c6547ee1af162019caf290d49` unless it legitimately advanced;
2. verify PR #173 exact head is still `4baf4fadbbd402a0dd523837924e6436f74f27d1`;
3. verify branch/worktree cleanliness;
4. run the protected Fable/high validation through the actual Claude/Vres host;
5. read the host-observed validator evidence;
6. if PASS, perform the required F-15 Chairman smoke;
7. if both pass and no source correction is needed, complete docs/handoff/merge sequence;
8. stop immediately on any validator finding and fix #163 only.

Do not touch #174 merge/rebase or #164 implementation before #163 is DONE.

---

# 6. Held item — #174 Engineering Architecture Governance

Issue:

**#174 — Engineering Architecture Constitution and Fable-validated adoption planning foundation**

PR:

**#175**

Current candidate:

`d0b59289e443dab14dd658411a0ee1d3d61d23c7`

Automated validation:

- GitHub Actions run **#436**
- run ID `36249928550`
- **1058 passed, 1 skipped**
- repository critical lint: PASS
- strict architecture-governance lint: PASS
- strict protected-surface lint: PASS
- installed-runtime smoke: PASS
- local release gate: `PASSED_WITH_EXPLICIT_LIVE_GATES`

## 6.1 What #174 built

- versioned Engineering Architecture Constitution;
- proportional architecture profiles;
- Chairman-only architecture UX;
- deterministic read-only architecture audit;
- stable rule/finding IDs;
- existing-project alignment-plan contract;
- exact `audit_digest`;
- exact `plan_digest`;
- required protected Fable/high validation of exact audit/plan state;
- no giant rewrite rule;
- nested local CLAUDE ownership contracts for substantive modules;
- architecture MCP tools registered internally;
- architecture CI/contracts;
- documentation/handoff.

## 6.2 Hardened audit behavior

The audit handles:

- fresh vs established;
- proportional profile detection;
- standard app/modules/domains/shared/platform layouts;
- conventional packaged Python layouts such as `src/<package>/...`;
- Python relative/local imports without executing project code;
- JS/TS imports including side-effect imports;
- dependency cycles;
- shared -> domain;
- shared -> module;
- domain -> module;
- platform -> domain/module;
- sibling feature module coupling;
- explicit private/internal cross-boundary imports;
- module local CLAUDE/public API signals;
- oversized responsibility warnings;
- symlink refusal;
- unsupported parser limitations;
- bounded inventory/parse limitations.

Known analysis limits are reported instead of hidden.

## 6.3 #174 plan authority contract

A mechanically valid alignment plan does **not** authorize activation.

It must bind:

- active constitution version;
- current `audit_digest`;
- canonical `plan_digest`;
- every detected target profile;
- every material finding.

Any later plan/audit mutation invalidates the protected review and requires a fresh Fable/high PASS.

## 6.4 #174 remaining work after #163 DONE

Once #163 is fully DONE:

- [ ] update/rebase #174 onto new authoritative main;
- [ ] resolve any integration drift;
- [ ] rerun exact-head full CI;
- [ ] run protected Fable/high on the rebased exact head;
- [ ] update handoff if required;
- [ ] merge PR #175;
- [ ] post-merge main CI green;
- [ ] close #174.

Do not start #164 until #174 is DONE.

---

# 7. Next implementation item after #174 — #164

Issue:

**#164 — Secret-safe onboarding: path exclusion, pre-model sanitization and fail-closed ingestion**

Status:

**NOT STARTED**

This must be built before Experience Intelligence because persistent memory turns ingested material into future privileged context.

Required #164 direction includes:

- deterministic sensitive-path classification before content extraction;
- exclude `.env`, `.env.*`, secrets files, credentials/auth/private-key material, Vres local-secret material;
- persist only bounded non-secret metadata for excluded files;
- sanitize useful mixed documents before model/persistence;
- expand sensitive key families such as `*_PASSWORD`, `*_TOKEN`, `*_SECRET`, `*_API_KEY`, etc.;
- reuse the Credential Broker rather than invent another secret store;
- fail closed when suspicious material cannot be sanitized confidently;
- never execute project/browser/API/OTP/deployment actions during onboarding;
- comprehensive synthetic security fixtures;
- protected Fable/high;
- exact-head CI;
- merge/post-main/close.

Physical sanitized legacy-project acceptance belongs to #169.

---

# 8. Planned future foundation — #176 Experience Intelligence

Issue:

**#176 — Experience Intelligence: governed agent learning, episodic memory and evidence-based experience reuse**

Status:

**PLAN COMPLETE / IMPLEMENTATION NOT STARTED**

Durable Git plan:

- branch: `docs-176-experience-intelligence-plan-20260927`
- commit: `34f45afa0fb8d5a6a90bef53dec58d9ecef1093d`
- file: `docs/architecture/EXPERIENCE-INTELLIGENCE-PLAN-2026-09-27.md`

Research/design review status:

**PASS for planning only.**

It is not host-protected validation and not implementation acceptance.

## 8.1 #176 prerequisites

Do not implement #176 until:

- #163 DONE;
- #174 DONE;
- #164 DONE.

## 8.2 #176 core architecture

Reuse current Vres truth owners:

- task/checkpoint state = live execution;
- task decisions = durable choices;
- knowledge = semantic facts/lessons/gotchas;
- procedures = procedural memory;
- feedback/runs/replay = procedure evolution;
- capabilities/proofs = demonstrated expertise;
- relations/evidence = provenance;
- sources/artifacts/events/validation = raw evidence archive.

Add only missing experience-specific primitives:

- immutable bounded experience episodes;
- memory transition audit;
- retrieval/use observations.

No hidden chain-of-thought persistence.

No private model self-training.

No silent agent prompt mutation.

## 8.3 #176 planned tranches

- E1 — contracts + episode ledger
- E2 — transition verifier + safe consolidation
- E3 — unified experience retrieval
- E4 — temporal lifecycle + revocation
- E5 — capability/procedure experience integration
- E6 — observability + utility evidence
- E7 — benchmark + security ladder
- E8 — Chairman integration + protected acceptance
- E9 — physical integrated acceptance inside #169

## 8.4 #176 critical security rules

Persistent memory is privileged context.

Protect against:

- memory poisoning;
- delayed injection;
- memory flooding/amplification;
- secret persistence;
- cross-project leakage;
- stale source influence;
- external observations becoming policy;
- poisoned procedure candidates;
- negative transfer;
- false-premise reuse;
- failed trajectories being copied as successful recipes.

External/untrusted data cannot establish:

- approval;
- company rule;
- agent/system instruction;
- validation downgrade;
- permissions;
- preferred procedure;
- credentials.

## 8.5 #176 evaluation rules

Compare:

- memory disabled;
- raw archive/refinding;
- structured memory;
- hybrid memory.

Measure:

- task success;
- validation outcome;
- retries/rework;
- tool calls;
- runtime/tokens;
- retrieval precision/recall;
- stale/conflict handling;
- premise awareness;
- negative transfer;
- poisoning success;
- scope leaks.

Use held-out and adversarial corpora.

Do not claim learning improvement from “agent seemed better.”

---

# 9. Remaining original preproduction ledger

## #165 — Chairman model policy

Status: NOT STARTED.

Target:

- explicit Chairman/control-plane model policy;
- intended initial policy Opus/medium;
- generation-tolerant aliases;
- host-observed evidence remains authoritative;
- no telemetry auto-mutation;
- no silent downgrade;
- protected validation;
- #169 physical host proof.

Do not start until #176 DONE under the current canonical checklist.

## #166 — Global Claude adoption

Status: NOT STARTED.

Title:

**Global Claude adoption: snapshot, quarantine, Chairman KEEP/DROP migration and rollback**

Owns current-user global Claude adoption over an established environment.

#169 live acceptance uses PRISM `vosser24/prism_5` as deliberate dirty pre-existing Claude state.

Do not implement before prior checklist items are DONE.

## #167 — Current-user Data Source Registry

Status: NOT STARTED.

Title:

**Current-user Data Source Registry and read-only semantic database catalog**

Owns the current-user reusable data-source identity/catalog and read-only semantic DB discovery behavior.

Must build on the Credential Broker rather than duplicate credentials.

Do not implement before #166 DONE.

## #168 — Project adoption and canonical Claude scaffold

Status: NOT STARTED.

Must consume:

- #163 Credential Broker;
- #164 secret-safe onboarding;
- #174 architecture governance;
- #176 Experience Intelligence;
- #166 global adoption foundations where relevant;
- #167 data-source catalog.

Owns:

- fresh / legacy / adoption_pending / awaiting_user / validation_pending / activating / active / rollback state;
- KEEP/DROP migration;
- canonical project Claude scaffold;
- credential/data-source linking;
- architecture audit + plan + Fable gate;
- Experience Intelligence integration;
- interruption/recovery.

No second architecture or memory mechanism may be invented here.

## #169 — Integrated Windows / Visual Studio live acceptance

Status: NOT STARTED.

This is the physical integrated acceptance after **all build tranches are merged and main is green**.

It must use:

- Windows;
- Visual Studio / integrated workflow;
- exact packaged release candidate;
- dirty pre-existing Claude setup;
- `vosser24/prism_5`;
- real/sanitized legacy project;
- synthetic credentials;
- real host-observed model evidence.

Must prove integrated:

- installer/global ownership;
- global adoption;
- project adoption;
- Credential Broker;
- secret-safe onboarding;
- architecture governance;
- Experience Intelligence;
- data-source catalog;
- Chairman/validator model authority;
- cross-user/project isolation;
- interruption/recovery;
- realistic-day smoke.

Defects discovered in #169 create bounded implementation issues; fix/merge them, then rerun only impacted acceptance surfaces.

## #170 — Production Readiness / Go-Live

Status: NOT STARTED.

Only after #169 DONE.

Owns:

- exact release artifact/manifests/hashes;
- Windows production install;
- PostgreSQL auth/least privilege/provenance boundary;
- credential/security/storage/logging review;
- backup/restore;
- update/rollback/interrupted update;
- adoption recovery;
- monitoring/health/escalation;
- capability inventory;
- staged real-world pilot;
- final production go-live evidence.

Do not call Vres production-ready before #170 passes.

---

# 10. Historical completed items that must stay closed

Do not reopen these without a fresh regression:

- #141
- #146
- #159

Historical validation evidence remains reusable unless a later change modifies the owned surface and current finalization policy requires rerun.

---

# 11. Physical-live-testing policy

The user explicitly wants final integrated physical testing **after all new development is merged**.

Do not prematurely run or claim the final Windows acceptance while individual implementation tranches are still open.

Final integrated testing is #169.

It will be performed from the user's Visual Studio / integrated development workflow, not the previous PowerShell-only style.

---

# 12. Git/validation discipline

For every implementation issue:

1. verify authoritative `origin/main`;
2. read full issue and relevant handoff before branch/worktree changes;
3. inspect existing code/tests before editing;
4. make the smallest robust change;
5. add targeted tests;
6. run relevant unit/integration/security tests;
7. run PostgreSQL-backed suite where applicable;
8. run protected Fable/high when required;
9. update docs/handoff;
10. require exact-head PR CI green;
11. merge only after all gates;
12. verify post-merge main CI green;
13. close issue with any physical criteria explicitly carried forward;
14. update canonical checklist;
15. only then begin the next checklist item.

Never combine multiple implementation issues into one tranche merely for convenience.

---

# 13. Current known blockers

## #163

Only blockers are acceptance/host gates:

- protected Fable/high cannot be substituted;
- F-15 requires real Claude/Vres Chairman host behavior.

Automated repository evidence is green.

## #174

Held by sequence, not by implementation defect.

Automated repository evidence is green.

It must be rebased/revalidated after #163 changes authoritative main.

## #176

Held intentionally until secret-safe ingestion and architecture governance are authoritative.

Do not interpret the complete research plan as permission to implement early.

---

# 14. Current exact next-session mission

A fresh session should state internally:

> Resume Vres preproduction from the canonical execution checklist. Work only #163. Verify authoritative main and PR #173 exact head first. Do not start #174 rebase or #164/#176 implementation. Complete the protected Fable/high validation and required Chairman/F-15 host smoke. If either fails, fix only #163, rerun required evidence, and repeat. If both pass, finish #163 merge/post-merge/closure, update the checklist, and stop before beginning #174 unless the user explicitly continues.

This is the single allowed continuation point.

---

# 15. User interaction preference

Keep the product interaction conversational.

Do not require the user to issue internal Vres commands.

The user should be able to:

- say `start vres`;
- describe the desired work in natural language;
- use native `clear`.

Chairman handles the machinery.

For development/acceptance sessions, explain only the minimum operator steps that cannot be executed from the current environment.

---

# 16. Handoff integrity rule

Whenever an issue becomes DONE:

1. update `docs/PREPRODUCTION-EXECUTION-CHECKLIST-2026-09-27.md`;
2. update or supersede this handoff with:
   - new authoritative main SHA;
   - merged PR;
   - exact validation evidence;
   - post-merge CI;
   - issue closure;
   - next allowed item;
3. commit the update to Git;
4. link the commit in the relevant GitHub issue;
5. never rely only on chat memory for continuation.

