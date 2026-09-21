# Vres-OS Finalization — Technical Handoff (2026-09-21, updated after F-12)

## Purpose

Resume Vres-OS final physical acceptance from the exact state reached on 2026-09-21 without re-running already-proven fixtures, losing evidence, rediscovering historical defects, or implementing unrelated features.

Repository:

`vosser24/Vres-OS`

This file is the authoritative continuation state for the next chat/session.

Blocking suite:

`docs/FINAL-VERIFICATION.md`

Historical detailed matrix:

`docs/LIVE-VERIFICATION.md`

At this handoff:

- **F-00 through F-12 are physically PASS.**
- **F-13 is next; audit reuse eligibility before rerunning.**
- F-14 is PENDING/REUSE-ELIGIBLE; F-15 is PENDING.
- Issue **#103** has completed its physical acceptance surfaces through F-12; close it after this handoff merges and post-merge CI succeeds.
- No new feature work should begin before finalization is complete.

---

# 1. Exact repository / installation identity

## GitHub

GitHub `main` immediately before this updated handoff commit:

`50dd4934115f01a8105657f9e286e215f6c353c1`

That commit is the merge of PR #127, the previous finalization handoff.

Last behavior-changing main commit:

`59010df5577e2457c673f74a29e093fbeae9d930`

That is the #125/#126 cross-project onboarding boundary fix.

The handoff update that contains this file will advance `main` again by documentation only. Do not mistake that docs commit for a behavior change.

## Installed runtime used for F-06 through F-10

Active installed release observed during the finalization run:

`20260921132941-8cb5268c`

Managed Python:

`C:\Users\User\AppData\Local\VresOS\releases\20260921132941-8cb5268c\venv\Scripts\python.exe`

Observed:

- psycopg 3.3.6
- PostgreSQL connected
- 34 migrations
- source checkout used for updates: `C:\Vres F01 Δοκιμή\Vres-OS`

Do not hardcode an older release path. Read `%LOCALAPPDATA%\VresOS\active-install.json` when a managed Python path is needed.

---

# 2. Finalization operating policy

Do not add features while F-00..F-15 is incomplete.

For a physical defect:

1. stop the affected F-case;
2. preserve evidence;
3. create a GitHub issue;
4. make the smallest correct fix;
5. review the exact diff;
6. require CI SUCCESS on the exact PR head;
7. merge;
8. require post-merge main CI SUCCESS;
9. physically rerun only the failed subcase unless the change invalidates broader evidence.

Do not rerun passed F-cases without a concrete reason.

Stop immediately on:

- credential leak;
- wrong-task continuation;
- cross-project leakage;
- unauthorized model downgrade;
- false validation PASS;
- stale-plan execution;
- write outside declared scope;
- fabricated telemetry;
- unexpected deletion/corruption of user-owned Claude settings.

Use isolated synthetic fixtures. Never run destructive credential cleanup against the real Windows Credential Manager namespace without true isolation.

User working preferences:

- exact commands;
- minimal repeated explanation;
- evidence-driven verdicts;
- no repeated questions already answered;
- smallest fixes only;
- no speculative rewrites;
- safe isolated testing;
- direct interpretation of pasted output.

---

# 3. Finalization matrix

| Case | Status | Notes |
|---|---|---|
| F-00 | PASS | update/migrations/statusline identity |
| F-01 | PASS | fresh install / Claude ownership boundaries |
| F-02 | PASS | rollback / uninstall / recovery ownership |
| F-03 | PASS | stranded cancellation repair |
| F-04 | PASS | bounded protected model/assurance lifecycle |
| F-05 | PASS | checkpoint / compact / clear / restart continuity |
| F-06 | PASS | concurrent sessions + cross-project isolation |
| F-07 | PASS | anti-overengineering / bounded context / noisy output |
| F-08 | PASS | project-agent authority + governor-confirmed gap acquisition |
| F-09 | PASS | real parallel fan-out + provenance + dependency join |
| F-10 | PASS | retry isolation + latest-plan + write-scope safety |
| F-11 | PASS | SEO/ecommerce multi-domain synthesis (corrected rerun; see section 11) |
| F-12 | PASS | independent judgmental product acceptance: PASS -> FAIL/block -> fresh remediation -> PASS |
| F-13 | **NEXT / REUSE-ELIGIBLE** | procedure + durable knowledge reuse; audit before rerun |
| F-14 | PENDING/REUSE-ELIGIBLE | onboarding + retrieval baseline |
| F-15 | PENDING | realistic-day integrated final verdict |

Do not reopen F-00..F-12 unless a later code change touches an owning surface.

---

# 4. F-00 through F-05 — retained PASS evidence

## F-00 — PASS

Windows status-line executable path defect:

- issue #117
- PR #118
- behavior commit `f35bf19416083369aa87347a891d429081428cf5`
- forward-slash Windows runtime path fixed Claude `statusLine.command`
- physical rerun rendered correctly.

## F-01 — PASS

Isolated current-user fixture:

`C:\Vres F01 Isolated Δοκιμή`

Source checkout:

`C:\Vres F01 Δοκιμή\Vres-OS`

Proved:

- user global sentinel survived;
- only Vres managed global block added;
- custom settings/statusLine preserved;
- shipped `vres-rules.md` hash matched;
- missing project `CLAUDE.md` received minimal scaffold;
- existing project `CLAUDE.md` stayed byte-identical;
- spaces/non-ASCII paths worked.

PowerShell 5.1 display mojibake was decode/display only; persisted UTF-8 was correct.

## F-02 — PASS

Proved:

- interrupted journal blocks blind retry and preserves recovery evidence;
- caught late update failure restores active release/plugin/bin/global Claude rules/settings;
- uninstall removes only Vres-owned surfaces;
- replacement custom statusLine survives;
- explicit cleanup stays inside owned paths.

Real defect:

- issue #119 / PR #120
- PowerShell local `$home` collided with readonly `$HOME`
- renamed to `$ClaudeHome`
- behavior stage `4b68889f1217eabf6fcf5bd52b8547917f08d016`
- PR CI #308 SUCCESS
- post-merge CI #309 SUCCESS.

Safety lesson:

The F-02 isolated filesystem harness did **not** isolate Windows Credential Manager. `uninstall.ps1 -RemoveLocalData` removed the real current-user `postgres.default` credential. It was repaired securely. Never repeat destructive credential cleanup under the same Windows account without credential-store isolation.

## F-03 — PASS

Historical task:

`TASK-20260918-865791f345`

Project:

`C:\Projects\Vres-60-Final-20260918-152340`

Exact same-session prompt `cancel this task` succeeded.

Durable evidence:

- task cancelled;
- session unbound;
- cancellation event 1207;
- `TASK_STATUS_CHANGED` 1208;
- `SESSION_UNBOUND` 1209;
- no artifact/expert/repair/orchestration/validation activity after cancellation.

Issue #60 evidence updated.

## F-04 — PASS

Project:

`C:\Projects\Vres-F04-Protected-20260921`

Task:

`TASK-20260921-e0000dedf2`

Protected pricing fixture:

- deterministic route;
- commercial-director / `cap.pricing`;
- one `vres-os:sonnet-expert`;
- observed model `claude-sonnet-5`;
- `ORCHESTRATION_FINAL` decision_ready=true before validation;
- exactly one validator:
  - `VAL-6ce6d5c89ed04a7a`
  - observed `claude-fable-5-1`
  - PASS;
- direct completion;
- no second validator/repair/reroute/post-PASS orchestration mutation.

A premature completion call was correctly rejected fail-closed and made no durable mutation.

Issue #60 closed.

## F-05 — PASS

Project:

`C:\Projects\Vres-F05-Continuity-20260921`

Task:

`TASK-20260921-00f8c9eb71`

Probe:

`f05_probe.py` -> `F05 TEST PASS`

Proved durable recovery of objective, decision, changed surface, exact executed evidence, blocker/current state, next action through:

- native `/compact`;
- native `/clear`;
- real process exit/restart.

Clear defect:

- issue #121 / PR #122
- durable end reason normalized to `provider_session_replaced`
- behavior commit `19ec313b1d81a2ddd245ac3f12b18269e15c96aa`
- CI #310 / #311 SUCCESS.

Latest checkpoint from that fixture:

`CP-20260921-d6c6a6695e`

Task remains open intentionally.

---

# 5. F-06 — PASS

F-06 is fully complete. Do not restart it.

## Historical same-project concurrency

Project:

`C:\Projects\Vres-F06-Concurrency-A-20260921`

A1:

`TASK-20260921-8e51bf0c7f`

A2:

`TASK-20260921-b58b9c0e79`

Historical wrong-task continuation after `/clear` exposed issue #123.

Fix:

- issue #123 / PR #124
- replacement provider session inherits still-active same-host predecessor task before project-focus fallback
- behavior commit `dc9f29207f786af3518f7ad6b36a3e89e1bf2999`
- CI #312 / #313 SUCCESS.

Physical rerun proved:

- A1 replacement remained A1;
- A2 remained open and untouched;
- predecessor ended `provider_session_replaced`;
- no live-session false closure.

## Historical cross-project onboarding defect

Do not clean these evidence projects:

`C:\Projects\Vres-F06-Concurrency-A-20260921`

`C:\Projects\Vres-F06-Isolation-B-20260921`

Old cross-project path onboarding intentionally remains contaminated evidence.

Issue #125 / PR #126 fixed `onboard_folder` accepting another registered project's path.

Behavior commit:

`59010df5577e2457c673f74a29e093fbeae9d930`

PR CI #316 SUCCESS; post-merge #317 SUCCESS.

## Fresh post-fix projects

Fresh A:

`C:\Projects\Vres-F06-XProject-A-20260921`

project id: **6897**

Primary task:

`TASK-20260921-eff4f8b559`

Fresh B:

`C:\Projects\Vres-F06-XProject-B-20260921`

project id: **6909**

Task:

`TASK-20260921-53f7e71e4c`

Both contained byte-identical:

`f06_scope_fixture\scope.txt`

SHA256:

`bfde2805e9a78ef0b17321d17b4ede7f4eab8b600a9ba77fda2a162303dafc1b`

## #125 physical rerun

From fresh A, onboarding B's registered project path was rejected:

`Onboarding path overlaps another registered Vres project; run onboarding from that project's Claude session`

PASS.

## Own-project onboarding provenance

A job:

`MIG-20260921-92b1485d`

A source:

`SRC-d9af2fa52f97`

Path only under fresh A.

B job:

`MIG-20260921-447da70a`

B source:

`SRC-1d8a4974dbdb`

Path only under fresh B.

Both persisted the identical content hash above while retaining separate project ownership/provenance.

Read-only DB proof ended:

`F06 SOURCE PROVENANCE: PASS`

## A-only knowledge isolation

A-only object:

`KNOW-4104a14935a8`

B exact search returned empty.

B direct read and mutation by key were rejected as outside current project.

Observed error wording mentions “writes” even for read; enforcement is correct. UX wording only.

## Company-wide hold

From B, `company_wide=true` publication was rejected:

`Company-wide publication is held until a dedicated user scope-approval flow is verified`

No write occurred.

## Completion / ambiguity

A ambiguity LEFT:

`TASK-20260921-6cfab49136`

A ambiguity RIGHT:

`TASK-20260921-f3f728458f`

Primary:

`TASK-20260921-eff4f8b559`

A protected validation attempt on PRIMARY:

- checkpoint `CP-20260921-e9259972a2`
- validation `VAL-132158168ef84412`
- observed `claude-fable-5-1`
- correctly FAILED because relayed B-side evidence was not independently verified
- PRIMARY was not completed.

This is good governance evidence, not a product defect.

Separate completion sentinel:

`TASK-20260921-ca559db7dd`

- checkpoint `CP-20260921-b775d9dcbe`
- validation `VAL-ac3f9034cfc44f7c`
- observed `claude-fable-5-1`
- all four criteria passed
- task completed;
- session unbound;
- no-key `task_resume` returned ambiguous with exactly PRIMARY + LEFT + RIGHT.

No silent recency selection.

## Final native /clear lineage

LEFT was explicitly resumed before native `/clear`.

Replacement provider session:

`ac4b0a97-a298-45e8-a8d1-de44018db821`

Predecessor:

`d57eaf71-e5c3-42a3-bf5d-373b338551df`

Predecessor:

- same task LEFT;
- same host PID 19556;
- ended `provider_session_replaced`.

Current `SESSION_BOUND` event 1456 source:

`provider_session_replaced`

No-key resume returned LEFT exactly.

Read-only proof ended:

`F06 CLEAR LINEAGE: PASS`

Therefore F-06 = PASS.

---

# 6. F-07 — PASS

Project:

`C:\Projects\Vres-F07-Simple-20260921`

Project id:

**7044**

Fixture:

- short known `app.py`;
- 5000-line `large_reference.txt`;
- marker at line 4321:
  `F07_REQUIRED_VALUE=F07 SIMPLE PASS`;
- noisy `noisy_check.py` emits 1200 noise lines.

Claude behavior:

- direct one-line edit only:
  `F07 OLD` -> `F07 SIMPLE PASS`;
- large file narrowed by marker/search;
- noisy command redirected to temp;
- output bounded;
- true exit captured:
  `EXIT=0`;
- decisive line:
  `F07 ACCEPTANCE PASS`;
- no worker;
- no validator;
- no persistent task;
- no routing;
- no work graph.

Untracked `CLAUDE.md` was created by `start vres` before the implementation prompt and was not part of the task change surface.

Durable DB proof:

- TASKS: []
- ROUTING REQUESTS: 0
- WORKER RUNS: 0
- WORK UNITS: 0
- VALIDATION REQUESTS: 0

Ended:

`F07 GOVERNANCE MINIMALITY: PASS`

Therefore F-07 = PASS.

---

# 7. F-08 — PASS

Project:

`C:\Projects\Vres-F08-Agents-20260921`

Project id:

**7055**

Task id:

**96**

Task:

`TASK-20260921-22d3decd4c`

## Phase 1 — governor-confirmed acquisition

Synthetic need:

`xenolithic kiln resonance calibration`

Pre-block acquisition correctly rejected:

`Project capability acquisition requires the task's latest route to be governor-blocked`

Initial schema omission of `task_key` was harness noise only; the correctly formed call hit the intended boundary.

First discovery:

`ORCHDISC-20260921-721a7ea445`

Missing exactly the synthetic need.

Blocked route:

`ROUTE-4ae2e49aab8f4db5`

Observed arbiter:

`claude-fable-5-1`

Persisted outcome:

- blocked;
- no experts;
- required gap exactly `xenolithic kiln resonance calibration`.

Wrong gap correctly rejected:

`gap_need is not authorized by the latest blocked routing decision`

Valid acquired project capability:

`cap.project.f08.xenolithic-kiln`

Owner:

`specialist-f08-xenolithic-kiln`

Domain:

`synthetic-f08`

Acquisition event:

**1466**

Duplicate same-gap acquisition before rediscovery rejected:

`This governed gap already acquired project expertise; rediscover before adding another specialist`

Rediscovery:

`ORCHDISC-20260921-712322da29`

Missing became empty and the project capability was reused.

No company-wide capability was created.

## Phase 2 — project-agent authority / source drift

Forbidden agent with `model: opus` and `effort: high` rejected:

`Project agent definitions must not set model or effort; Vres routing owns execution tier`

First valid project-agent commit in the disposable fixture repo:

`3a04a95dc29b0708dc924caec4eeee5b4de3426d`

Registered agent:

`agent.project.f08.xenolithic-kiln`

Role:

`specialist-f08-xenolithic-kiln`

Capability:

`cap.project.f08.xenolithic-kiln`

Write policy:

`report_only`

Original source digest:

`066dba6dc966f43d6975ab9545e0377f661b1758adfe74ec111cb65b8842a30b`

Discovery with agent:

`ORCHDISC-20260921-b1d0869bbd`

After source modification, direct get rejected:

`Project agent source changed; re-register the agent before execution`

Search while drifted returned empty.

Explicit re-registration succeeded.

New digest:

`2c1a7caac8ce90be77c55e6214913f25b42974ab6e1c93bb3ed4d3bd58f9b61e`

Second fixture commit:

`f5a8816eb346a0de7ff4fe06f027d2ba98f06274`

Final search returned the agent again.

Durable DB proof confirmed:

- capability project_id 7055;
- agent project_id 7055;
- capability `proven_count=0` (acquisition did not silently mark proof);
- exactly one acquisition event;
- no `model` or `effort` metadata;
- zero company-wide rows for capability or agent.

Ended:

`F08 DURABLE AUTHORITY: PASS`

Therefore F-08 = PASS.

Keep the agent/capability state; do not clean the project.

---

# 8. F-09 — PASS

Same project id **7055**.

Task id:

**97**

Task:

`TASK-20260921-806307a54e`

Fixture agent commit:

`bb4afca6b64741d6996b791a25fac04f9cef3f16`

Additional project agents:

- `agent.project.f09.data` -> data-director -> `cap.postgresql`
- `agent.project.f09.cto` -> cto -> `cap.software-engineering`

Kiln agent reused from F-08.

Discovery:

`ORCHDISC-20260921-701f203ef6`

No gaps.

## Preserved stale-route evidence

First F-09 route:

`ROUTE-24ba269271ac414e`

was rejected:

`task_changed_during_routing`

Cause: a task checkpoint occurred while the routing governor was in flight.

The rejection was correct fail-closed behavior. Preserve it; do not delete/rewrite it.

Fresh route:

`ROUTE-308686808d634543`

Observed governor:

`claude-fable-5-1`

Persisted:

- routed;
- lead cto;
- assurance routine;
- no gaps;
- three exact experts;
- all Sonnet;
- no extra expert.

Plan:

`ORCHPLAN-20260921-ba6e77eeb7`

Work units:

A kiln:

`ORCHWORK-20260921-52037b0787`

B data:

`ORCHWORK-20260921-9ea685ded0`

C dependent CTO:

`ORCHWORK-20260921-0c4b9bb0cf`

Reports:

- A `ORCHREP-20260921-5e94954f43`
- B `ORCHREP-20260921-0db38688df`
- C `ORCHREP-20260921-50f002806c`

Host agents:

- A `a1327f2641d9dc970`
- B `a15becfee7169766e`
- C `aef2b19f394cc3481`

All observed:

`claude-sonnet-5`

A/B actual DB intervals:

- A: 14:57:47.087683 -> 14:58:04.366706
- B: 14:57:53.789390 -> 14:58:13.668739

Overlap:

**True**

C started:

14:58:40.200134

Latest prerequisite completion:

14:58:13.668739

Therefore dependency join was respected.

Final:

`ORCHFINAL-20260921-869f78c259`

- accepted all three reports;
- decision_ready=true;
- synthesis contained:
  - `F09_KILN_LIMIT=73`
  - `F09_KILN_MODE=phase-locked`
  - `F09_DB_ENGINE=PostgreSQL`
  - `F09_DB_ISOLATION=serializable`.

Read-only proof ended:

`F09 PARALLEL DAG: PASS`

## F-09 observation to preserve

Worker B read its read-only fixture before calling `orchestration_work_unit_start`.

It caused:

- no write;
- no scope escape;
- no relaunch;
- no provenance loss.

The worker report itself preserved the note.

Treat this as an observation, not a blocker, unless later acceptance requires strict pre-read claim ordering.

Therefore F-09 = PASS.

---

# 9. F-10 — PASS

Project:

`C:\Projects\Vres-F10-Safety-20260921`

Project id:

**7236**

Task id:

**98**

Task:

`TASK-20260921-2594d63453`

Fixture project-agent commit:

`3d622a41f1518c42d491fade7fc56046eb96a9bf`

Agents:

- `agent.project.f10.cto`
- `agent.project.f10.data`

Discovery:

`ORCHDISC-20260921-8e8b6653d0`

Route:

`ROUTE-d09ed25e6fdd4905`

Observed arbiter:

`claude-fable-5-1`

Persisted route:

- routed;
- cto + data-director;
- both Sonnet;
- no gaps;
- `hard_protected=false`;
- assurance **protected**.

This is valid. The governor chose protected because the task proves governance invariants. Do not reroute/downgrade.

## PLAN 1 — retry isolation / running-work replan rejection

Plan:

`ORCHPLAN-20260921-664a4bac38`

A / cto:

`ORCHWORK-20260921-61acf25141`

B / data:

`ORCHWORK-20260921-e28bd5ed99`

A and B launched together.

While running, a replan attempt was rejected:

`Cannot record a new orchestration plan while prior work units are running`

A:

- host `a25ee557f0e710d01`
- report `ORCHREP-20260921-73836528be`
- observed `claude-sonnet-5`
- passed
- attempt_count 1
- never relaunched.

B attempt 1:

- host `a66447abc6999029d`
- observed `claude-sonnet-5`
- intentional failure:
  `F10 synthetic transient failure`
- worker run status rejected after stop;
- host-stop rejection event 1539:
  `Governed worker stopped without a valid orchestration expert report`.

After host stop, only B was retryable.

B retry:

- new host `a34bc9ceef0c17d70`
- report `ORCHREP-20260921-9c5269f254`
- observed `claude-sonnet-5`
- passed.

Final PLAN 1:

- A passed attempt 1;
- B passed attempt 2;
- failed and retry host IDs differ;
- successful sibling was not rerun.

## PLAN 2 — latest plan + overlap + direct scope enforcement

Plan:

`ORCHPLAN-20260921-c0505c4606`

After PLAN 2 was recorded, attempting old PLAN 1 readiness/execution was rejected:

`Only the task's latest orchestration plan may execute or finalize work`

PLAN 2 A:

`ORCHWORK-20260921-dd7bcfed44`

Scope:

`f10/shared`

Host:

`a4608de0bfc4070d3`

Report:

`ORCHREP-20260921-f00b7db99f`

Observed:

`claude-sonnet-5`

Passed attempt 1.

PLAN 2 B:

`ORCHWORK-20260921-4854d794ab`

Scope:

`f10/shared/sub`

While A was running, parent attempted B start.

Rejected:

`Write scope overlaps running work unit ORCHWORK-20260921-dd7bcfed44`

B remained:

- pending;
- attempt_count 0;
- no host worker;
- no report.

A's native out-of-scope `Write` to:

`f10/outside/blocked.txt`

was rejected:

`Work unit ORCHWORK-20260921-dd7bcfed44 may write only within its declared scope: f10/shared`

File remained absent.

A's native in-scope write succeeded:

`f10/shared/allowed-a.txt`

Exact bytes:

`F10_PLAN2_A=PASS`

No trailing newline.

Bash was used only for sleeps/read-only inspection, never as the tested write mechanism and never described as an OS sandbox.

## PLAN 3 — disjoint concurrent write scopes

Plan:

`ORCHPLAN-20260921-74a72ca094`

A3:

`ORCHWORK-20260921-c96c970774`

Scope:

`f10/a`

Host:

`a2973e23626fce769`

Report:

`ORCHREP-20260921-e823c74e0b`

B3:

`ORCHWORK-20260921-531e7e8d2a`

Scope:

`f10/b`

Host:

`a3b2b192e0e069a28`

Report:

`ORCHREP-20260921-a2ef0fbc5c`

Both:

- canonical `vres-os:sonnet-expert`;
- observed `claude-sonnet-5`;
- passed;
- attempt_count 1;
- no relaunch.

DB intervals:

A3:

15:21:56.113269 -> 15:22:32.618594

B3:

15:22:01.465412 -> 15:22:51.165898

Overlap:

**True**

Exact output bytes:

`f10/a/cto.txt` -> `F10_CTO_WRITE=PASS`

`f10/b/data.txt` -> `F10_DATA_WRITE=PASS`

Durable assertion ended:

`F10 RETRY / PLAN / WRITE SCOPE: PASS`

Therefore F-10 = PASS.

---

# 10. Observations intentionally preserved, not defects

Do not “clean” or rewrite these away:

1. F-06 A2 reply-gate warning `state_changed_after_reply_gate`, immediately resolved with a non-material gate and no state corruption.
2. F-06 PRIMARY protected validator correctly refused to treat relayed cross-project evidence as independently verified.
3. F-08 first acquisition call omitted `task_key`; schema error was harness noise, followed by the real governed rejection.
4. F-08 one company-wide hold call supplied literal `"null"` for `path_or_uri`; the scope guard executes first and no write occurred.
5. F-09 stale route `ROUTE-24ba269271ac414e` was correctly rejected after a mid-route checkpoint.
6. F-09 Worker B read a read-only fixture before claiming its work unit.
7. F-10 governor chose protected assurance despite `hard_protected=false`; this is valid governor consequence reasoning, not a failure.
8. F-10 early `orchestration_plan_record` attempts had schema/exclusion-field mistakes before the successful plan; no incorrect plan persisted.
9. PowerShell LF/CRLF Git warnings in disposable agent fixture repos are non-blocking; registered source digests were verified after commits.

---

# 11. F-11 — PASS

Status: PASS, accepted by the user after the final evidence seal (`F11 FINAL EVIDENCE SEAL: PASS`).

## Historical failed attempt — preserved, not rewritten

`TASK-20260921-dd8b1517a7` (completed 2026-09-21T13:03:15Z).

It is not a clean acceptance run: its formal arbitration was recorded after the CTO synthesis, and the task was completed although the fixture required it to stay active. Its evidence, including its protected validation `VAL-a8fa7149a6ec4541`, is preserved as history and is not part of the acceptance.

## Corrected acceptance rerun

- Task: `TASK-20260921-1e0eea9c54` — remains ACTIVE, `completed_at` NULL.
- Project id: `7429`; project path `C:\Projects\Vres-F11-SEO-20260921` — do not clean.
- Route: `ROUTE-aee2c09255e34ca5` (routed, protected; lead `cto`). SEO Sonnet with `agent.project.f11.seo`; data-director Sonnet; digital-director Sonnet; CTO Opus.
- Plan: `ORCHPLAN-20260921-6f37e91013`
- SEO report: `ORCHREP-20260921-79210106f8`
- Digital/CRO report: `ORCHREP-20260921-46ed990f23`
- Data report: `ORCHREP-20260921-d3b98caafe`
- Arbitration: `ORCHARB-20260921-9ecbbd2ce0` (topic `F11 faceted-navigation indexation policy`)
- CTO report: `ORCHREP-20260921-c05632b528`
- Final: `ORCHFINAL-20260921-9662c9b003`, `decision_ready=true`
- No extra protected validator was run on the corrected acceptance rerun, and the task was deliberately not completed.

## Physical ordering proof

1. SEO, Digital/CRO and Data units ran independently with real pairwise execution overlap.
2. Arbitration was recorded after the relevant SEO and Digital/CRO reports and BEFORE CTO execution (event 1672 at 13:16:36Z; CTO start event 1674 at 13:17:25Z).
3. The CTO began only after all prerequisite units completed (last prerequisite completed 13:16:42Z).
4. The CTO report referenced all three prerequisite reports plus the arbitration.
5. The final accepted every selected report plus the arbitration.

## Arbitration substance

- Arbitrary or generated facet combinations are not indexable.
- Only explicitly controlled, high-intent, evidence-gated facet landing pages may become indexable.
- The corrected run chose category plus exactly one facet only.
- Everything outside the controlled allowlist stays outside the indexable set.

## Fixture identity variance (documented naming variance, not a governance failure)

- The original governor-authorized project capability remains `cap.technical-seo`, owner `specialist-technical-seo`. It remains project-scoped and was reused, not duplicated. The contract names below (`cap.project.f11.technical-seo` / `specialist-f11-seo`) were not created: no governed tool renames a capability, and a second SEO capability was not permitted.
- The corrected executable F-11 project agent is `agent.project.f11.seo`, source `.claude/agents/f11-seo.md`, `write_policy=report_only`, no model or effort authority.
- The old project agent `specialist-technical-seo` remains historical and was not selected.
- Google/API: the rerun discovery used five needs, and the governor folded Google Search Console API ingestion into software engineering. No `cap.project.f11.google-api` or `agent.project.f11.google-api` was created.
- The route was prepared with risk trigger `material_durable_disagreement`, not the contract's `cross_domain`.

## Final evidence seal

- The final PostgreSQL proof ran with `SHOW transaction_read_only -> on`. An earlier proof had reported `off`; the sealed proof supersedes it.
- The task remained active with `completed_at` NULL.
- No unauthorized company-wide capability or agent authority exists.
- The direct-read tail created no new task, discovery, route, plan, graph, work unit or worker.
- `f11_simple.txt` logical value: `F11_SIMPLE_DIRECT_READ=PASS`. The working-tree CRLF versus committed LF is attributable to `core.autocrlf=true`; Git reports no logical diff. One extra byte-identity clause in the sealing script reported FAIL for this reason; the assertion as specified holds.

## Assumptions caveat

The synthetic architecture retains uncalibrated assumptions and thresholds and unverified Search Console API details. They are documented as assumptions, not claimed as physically validated facts. `decision_ready=true` was obtained by carrying the CTO's 12 recorded unknowns as documented assumptions in the final synthesis (Chairman decision `DEC-20260921-56cf2fd08f`), not by resolving them.

## F-11 contract (retained for reference)

Official contract:

SEO-style multi-domain end-to-end synthesis.

Must prove:

- staffing is evidence-driven, not a fixed panel;
- shipped capabilities are reused;
- only genuine gaps become project specialists;
- independent specialist work overlaps where appropriate;
- directors/project specialists/capabilities remain distinguishable;
- system-architecture synthesis waits for prerequisites and uses all required reports;
- material disagreement is arbitrated rather than averaged;
- no worker/project agent chooses model/effort;
- simple subproblems still use the minimal path;
- final assurance follows consequence/risk rather than team size.

## F-11 fresh project setup

Use a fresh project:

`C:\Projects\Vres-F11-SEO-20260921`

PowerShell:

~~~powershell
$f11 = "C:\Projects\Vres-F11-SEO-20260921"

New-Item -ItemType Directory -Force $f11 | Out-Null
Set-Location $f11

git init
git config user.name "Vres F11 Fixture"
git config user.email "vres-f11@example.invalid"

@'
# F11 Synthetic SEO / Ecommerce Architecture Scenario

Build the architecture recommendation for a bounded ecommerce search-performance dashboard.

Business context:
- The catalog contains 50,000 synthetic products.
- PostgreSQL is the required application datastore.
- Search-performance data is ingested from a synthetic Google Search Console style API.
- The dashboard is used by ecommerce/content operators.
- The dashboard must expose organic-search performance alongside ecommerce search/conversion signals.
- The architecture must distinguish ingestion, storage, application/API, dashboard, and operational boundaries.

SEO requirement:
- Product and category pages must remain crawlable/indexable.
- Arbitrary faceted URL combinations must not create unbounded crawl/index expansion.

Google/API requirement:
- API ingestion must be incremental, retryable and idempotent.
- API failures must not corrupt the last known successful dataset.

Data requirement:
- PostgreSQL stores normalized daily search metrics with query/page/date dimensions.
- Reprocessing the same source batch must not duplicate logical rows.

Dashboard / ecommerce requirement:
- Operators need query, landing-page and date filtering.
- Ecommerce-search/CRO reasoning must connect discoverability evidence to actionable product/search improvements.

Intentional material tradeoff:
- SEO position: arbitrary faceted URLs should not be indexed because uncontrolled combinations create crawl/index expansion.
- Digital/CRO position: selected high-intent facets can be valuable organic landing experiences.
- The final architecture must resolve this disagreement explicitly rather than averaging the two positions.

System architecture requirement:
- The final design must use every required specialist report.
- It must state a concrete boundary for which facet pages may be indexable.
'@ | Set-Content -Encoding UTF8 ".\f11_scenario.md"

@'
F11_SIMPLE_DIRECT_READ=PASS
'@ | Set-Content -Encoding UTF8 ".\f11_simple.txt"

git add f11_scenario.md f11_simple.txt
git commit -m "Add F11 SEO ecommerce fixture"

claude
~~~

Inside Claude:

`start vres`

## F-11 discovery contract

Create one persistent task:

Title:

`F11 SEO Ecommerce Architecture`

Objective:

Use evidence-driven discovery, only genuinely required project capability acquisition, real parallel specialist execution, explicit disagreement arbitration, and dependent system-architecture synthesis for `f11_scenario.md`.

Keep active. Do not complete.

Initial `orchestration_discover` needs exactly:

1. `technical seo`
2. `google search console api integration`
3. `postgresql`
4. `ecommerce search`
5. `conversion optimization`
6. `software engineering`

Expected shipped reuse, subject to authoritative discovery:

- PostgreSQL -> `cap.postgresql` / data-director
- ecommerce search -> `cap.ecommerce-search` / digital-director
- conversion optimization -> `cap.cro` / digital-director
- software engineering -> `cap.software-engineering` / cto

Expected genuine gaps, again only if discovery confirms them:

- `technical seo`
- `google search console api integration`

Do **not** pre-create all six experts.

## F-11 governor-confirmed gap acquisition

If discovery has gaps, prepare route with:

`["cross_domain", "new_capability_gap"]`

Launch one canonical routing arbiter if Fable is required.

While route is in flight:

- no checkpoint;
- no task-state mutation;
- non-material reply gate only if needed.

Acquire only exact persisted `required_gap_needs`.

If authorized, use:

Technical SEO capability:

- key `cap.project.f11.technical-seo`
- name `F11 Technical SEO`
- domain `synthetic-f11-seo`
- owner `specialist-f11-seo`

Google/API capability:

- key `cap.project.f11.google-api`
- name `F11 Google Search Console API Integration`
- domain `synthetic-f11-google-api`
- owner `specialist-f11-google-api`

No company-wide authority.

## F-11 project agents

Only for genuinely acquired project capabilities.

SEO:

- source `.claude/agents/f11-seo.md`
- agent key `agent.project.f11.seo`
- role `specialist-f11-seo`
- capability `cap.project.f11.technical-seo`
- write_policy `report_only`

Google/API:

- source `.claude/agents/f11-google-api.md`
- agent key `agent.project.f11.google-api`
- role `specialist-f11-google-api`
- capability `cap.project.f11.google-api`
- write_policy `report_only`

No `model:` or `effort:` in project-agent frontmatter.

Commit only those F11 agent files.

Rediscover the exact six needs. Required before continuing:

- no missing capabilities;
- company capabilities remain company-scoped;
- F11 acquisitions remain project-scoped;
- project agents appear only for compatible specialist capabilities.

## F-11 final routing / plan

Prepare final route from rediscovery with:

`["cross_domain"]`

Do not request a tier or assurance.

Persist whatever valid governor result is produced.

Expected smallest reasonable consolidation, but do not force it:

- SEO specialist;
- Google/API specialist;
- data-director;
- digital-director covering ecommerce search + CRO;
- cto for software/system architecture.

No need may be silently dropped.

Create one work unit per selected expert.

All non-CTO units:

- independent;
- report-only;
- no dependencies.

CTO:

- depends on every selected non-CTO domain unit;
- report-only;
- final architecture synthesis.

Launch up to four independent ready workers in one native parallel dispatch using each work-ready canonical worker type/tier.

No explicit model override.

Every worker must claim its work unit before substantive work and record its own expert report.

## F-11 disagreement arbitration

The scenario deliberately conflicts:

SEO:

arbitrary faceted URL combinations should not be indexable.

Digital/CRO:

selected high-intent facets can be valuable organic landing pages.

After the relevant reports exist, call `orchestration_arbitrate`.

Topic:

`F11 faceted-navigation indexation policy`

Required concrete resolution in substance:

- arbitrary/generated facet combinations are not indexable;
- only explicitly curated high-intent facet landing pages meeting controlled criteria may be indexable;
- all other combinations remain outside the indexable set.

Do not average the disagreement into vague prose.

Give CTO all prerequisite report keys plus the arbitration key/resolution.

CTO report must distinguish:

1. SEO/indexation boundary;
2. Google/API ingestion/retry/idempotency;
3. PostgreSQL storage/idempotency;
4. dashboard/ecommerce/CRO;
5. application/system architecture;
6. resolved facet disagreement.

Finalize with every selected expert report key + arbitration key.

Required:

`decision_ready=true`

Do not complete the task.

Do not run protected validation unless later explicitly required by the F-case.

## F-11 minimal-path tail

After finalization, directly Read the short known file:

`f11_simple.txt`

Required exact value:

`F11_SIMPLE_DIRECT_READ=PASS`

Do not:

- create another task;
- discover;
- route;
- launch worker;
- create work graph.

This proves minimal path remains intact after complex orchestration.

## F-11 durable proof after behavioral run

Before declaring F-11 PASS, run one read-only PostgreSQL proof covering:

- exact acquired scopes;
- zero unauthorized company-wide rows;
- persisted final route roster/tier/assurance;
- distinct project-agent/director identities;
- actual independent worker time overlap;
- CTO start after every prerequisite completion;
- arbitration event references both conflicting reports;
- CTO report references every prerequisite report + arbitration;
- final accepts every selected report and is decision_ready;
- simple direct read did not create a new task/route/worker.

Do not mark F-11 PASS from Claude prose alone.

---

# 12. F-12 through F-15 pending

## F-12 — independent judgmental product acceptance

F-12 is the next blocking case.

Need one bounded write-capable slice with:

- deterministic implementation criteria frozen before work;
- one genuine judgmental UX/product/domain criterion;
- implementation worker may report deterministic criteria only;
- dependent report-only verifier;
- one PASS plan;
- fresh/current FAIL plan;
- failed judgment remains durable and blocks finalization;
- remediation uses new/current work;
- protected validation remains a separate layer.

This is still part of #103 physical closure.

## F-13 — procedure + durable knowledge reuse

May reuse prior evidence only if all FINAL-VERIFICATION reuse rules are met and owning surfaces have not changed.

Need prove:

- exact accepted contract reused;
- changed approved content requires new approval;
- negation/source provenance preserved;
- observation remains limited/scoped;
- superseded knowledge remains history;
- project scope enforced;
- no auto-promotion from self-reported speed/token claims.

## F-14 — onboarding/retrieval

May reuse prior evidence only when owning parser/retrieval/onboarding surfaces are unchanged.

Important:

#125 changed cross-project onboarding path ownership, so no pre-#126 evidence may be used to claim that specific safety property.

Need mixed-format synthetic folder, duplicate, malformed/unsupported case, lexical retrieval with embeddings disabled; embeddings NOT RUN if disabled.

## F-15 — realistic day / final verdict

Only after all blocking cases pass/reuse validly.

Must exercise normal Chairman conversation:

- resume durable state;
- simple deterministic task;
- specialist/multi-agent task;
- procedure/knowledge lookup;
- compact/clear;
- product acceptance;
- protected action if required;
- descriptive status/context/usage observations.

No claim of production readiness or measured token savings without evidence.

---

## F-12 accepted physical evidence (2026-09-21)

Project: `C:\\Projects\\Vres-F12-Acceptance-20260921`

Task: `TASK-20260921-3f4d89508a` — ACTIVE, not completed.

Frozen test SHA256: `56ECEAB561EC4D65707F9DD85EA99CCABE1A796FA2868C3A0C8F16F30DFB65DA`.

Plan A PASS: `ORCHPLAN-20260921-11ae92c8aa`; implementation `ORCHREP-20260921-439767260c`; verifier `ORCHREP-20260921-411db6ba56`; final `ORCHFINAL-20260921-d1fbff091d`, decision_ready=true. Accepted artifact commit: `0b9866dbbe2d3fb751d995d6261be8986f9a551c`.

Plan B required FAIL: `ORCHPLAN-20260921-522482004e`; deterministic implementation report `ORCHREP-20260921-3f3ea1c9c0` PASS; independent verifier `ORCHREP-20260921-9f0e5b7f18` FAIL; no successful final. Finalization was rejected because J1 had not passed independent verification. Failed artifact commit: `bee552142149c07f9871ec9bd1953c436734adf0`.

Plan C remediation PASS: `ORCHPLAN-20260921-9ac3120cd9`; implementation `ORCHREP-20260921-fac8b9ef12`; verifier `ORCHREP-20260921-adc783baea`; final `ORCHFINAL-20260921-7a2c3de0f6`, decision_ready=true.

Durable proof: every work graph preceded its implementation start; implementers reported deterministic criteria only; verifiers were dependent/report-only and ran only after implementation PASS; J1 sequence was PASS / FAIL / PASS; Plan-B failure remained durable after Plan C; all routes used routine assurance; no protected validator was required; read-only PostgreSQL proof used transaction_read_only=on. Final accepted conclusion: `F12 INDEPENDENT PRODUCT ACCEPTANCE: PASS`.

F-12 evidence project must not be cleaned. Current preserved state at handoff: HEAD `bee552142149c07f9871ec9bd1953c436734adf0`; only `refund_notice.py` contains the uncommitted Plan-C remediation. Do not reset or commit it merely for tidiness.

### F-13 resume rule

F-13 is REUSE-ELIGIBLE, not automatically REUSED. First compare exact prior F-13 evidence/commit(s) against current main for changes to procedure, approval, preferences, knowledge, provenance, project-scope, or relevant native/provider contracts. If every reuse rule in `docs/FINAL-VERIFICATION.md` holds, record exact reused evidence and rationale. Otherwise rerun only the invalidated smallest synthetic fixture. Do not start F-14 until F-13 is PASS/REUSED.

### Remaining ladder

F-14: reuse audit first; pre-#126 evidence cannot prove the #125 cross-project onboarding-path boundary. If rerun is needed, use mixed-format synthetic input, duplicate, malformed/unsupported case, lexical retrieval; embeddings are NOT RUN when disabled.

F-15: final realistic-day integration only after F-13/F-14 PASS or valid REUSED. No false production-readiness or measured-token-savings claims.

# 13. Open issue #103

Issue:

**#103 — Add first-class project agents and governed parallel execution DAG**

Do not close solely because unit/integration tests exist.

Physical surfaces already proven:

- F-08 project-agent authority / gap acquisition — PASS
- F-09 parallel fan-out / provenance / dependency join — PASS
- F-10 retry / latest-plan / write-scope safety — PASS
- F-11 multi-domain synthesis — PASS

Still needed before closure:

- F-12 independent product acceptance — pending; this is the final physical #103 acceptance surface

Do not close #103 yet. Keep it open until F-12 passes and no critical defect remains.

---

# 14. Closed defect chronology

- #117 / PR #118 — Windows statusLine executable backslash normalization
  - `f35bf19416083369aa87347a891d429081428cf5`
- #119 / PR #120 — PowerShell `$HOME` collision in uninstall
  - stage `4b68889f1217eabf6fcf5bd52b8547917f08d016`
- #121 / PR #122 — native `/clear` durable end reason
  - `19ec313b1d81a2ddd245ac3f12b18269e15c96aa`
- #123 / PR #124 — concurrent replacement session could bind wrong task
  - `dc9f29207f786af3518f7ad6b36a3e89e1bf2999`
- #125 / PR #126 — `onboard_folder` accepted another registered project's path
  - `59010df5577e2457c673f74a29e093fbeae9d930`

---

# 15. Projects/evidence that must not be cleaned

Historical defect evidence:

- `C:\Projects\Vres-F06-Concurrency-A-20260921`
- `C:\Projects\Vres-F06-Isolation-B-20260921`

Fresh F-06 final evidence:

- `C:\Projects\Vres-F06-XProject-A-20260921`
- `C:\Projects\Vres-F06-XProject-B-20260921`

F-07:

- `C:\Projects\Vres-F07-Simple-20260921`

F-08/F-09:

- `C:\Projects\Vres-F08-Agents-20260921`

F-10:

- `C:\Projects\Vres-F10-Safety-20260921`

F-11 (failed attempt `TASK-20260921-dd8b1517a7` and corrected rerun `TASK-20260921-1e0eea9c54`, both in one project):

- `C:\Projects\Vres-F11-SEO-20260921`

These disposable repos contain physical evidence and should remain untouched until finalization is signed off.

---

# 16. Post-finalization roadmap — retain, DO NOT IMPLEMENT YET

## Claude -> Codex execution handoff

Desired direction:

`vres handoff codex`

Principles:

- Vres owns task;
- hand off task state, not transcript/protocol translation;
- governed executor;
- prefer `codex exec --json`;
- trust postconditions, not exit code alone;
- temporary worktree + changed-path verification after real workspace-write preflight;
- never danger-full-access fallback.

## External Capability Discovery & Audit

Inventory installed MCP/plugins/skills/agents and classify:

- USE
- USE WITH GUARDS
- DEVELOPMENT REQUIRED
- DECLINE

Installation != adoption. Vres retains model/effort authority.

## JEV Browser Control

First browser-control fixture, likely USE WITH GUARDS.

Do not let a model-pinned external agent become a governed Vres agent.

## E-11 UX/UI Browser Audit Capstone

Audit account-creation flow with durable screenshots/journey findings/remediation/redesign/diagram/presentation-ready evidence.

## Superpowers plugin

Optional external development methodology only. Never a Vres runtime dependency.

---

# 17. New-session resume instructions

Update after F-11 acceptance: items 3 and 6-14 below, and the F-11 sentence after the list, are superseded because F-11 is PASS (section 11). Do not rerun F-00 through F-11. Resume directly at **F-12** (section 12).

When opening a fresh ChatGPT session:

1. Treat this handoff as authoritative.
2. Verify GitHub `main` only if needed; do not spend a turn re-explaining old history.
3. **Do not rerun F-00 through F-10.**
4. Do not clean or rewrite prior disposable evidence projects.
5. Confirm the installed runtime only if the new session has evidence it changed.
6. Resume directly at **F-11** using `C:\Projects\Vres-F11-SEO-20260921`.
7. Run the six-need discovery before acquiring or registering specialists.
8. Reuse shipped capabilities; acquire only exact governor-confirmed gaps.
9. Preserve model/effort authority in Vres routing; project agents never choose them.
10. Require real parallel worker overlap where work is independent.
11. Record explicit arbitration for the SEO-vs-digital facet-indexation disagreement.
12. Require CTO to wait for all prerequisites and use every required report plus arbitration.
13. Run the simple direct-read tail without creating another governance stack.
14. Verify F-11 with read-only PostgreSQL evidence before marking PASS.
15. Then continue F-12 -> F-15.
16. Keep #103 open through F-12 physical acceptance.
17. No new feature work before finalization completes.

Immediate next user-visible action in the new session should be the concise F-11 project setup and execution instruction, not a history recap.

---

# 18. One-line resume state

**Current blocker:** none.

**Last completed case:** F-12 PASS.

**Next action:** F-13 reuse-eligibility audit; rerun only if the reuse rules fail.

**Do not redo:** F-00..F-12.
