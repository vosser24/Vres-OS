# Vres-OS Finalization — Technical Handoff (2026-09-21)

## Purpose

Resume Vres-OS final physical acceptance from the exact verified state reached on 2026-09-21 without re-running already-proven fixtures, rediscovering historical defects, or implementing unrelated features.

Repository: `vosser24/Vres-OS`

Authoritative code baseline before this documentation-only handoff commit:

`59010df5577e2457c673f74a29e093fbeae9d930`

Baseline main CI:

- run #317 — SUCCESS
- full PostgreSQL integration suite — SUCCESS
- installed-runtime import smoke — SUCCESS
- local release gate — SUCCESS

At this handoff, the only open product issue is:

- #103 — Add first-class project agents and governed parallel execution DAG

The documentation commit containing this file may move `main` beyond the code baseline above. The code baseline remains the last behavior-changing commit at the time of this handoff.

---

## Finalization operating policy

Do not add new features while final physical verification `F-00..F-15` is incomplete.

Only fix defects physically uncovered by the finalization suite.

Current blocking suite:

`docs/FINAL-VERIFICATION.md`

Historical detailed verification mapping:

`docs/LIVE-VERIFICATION.md`

For a physical defect:

1. stop that F-case;
2. preserve evidence;
3. create a GitHub issue;
4. make the smallest correct fix;
5. review the exact diff;
6. require CI SUCCESS on the exact PR head;
7. merge;
8. require post-merge main CI SUCCESS;
9. physically rerun only the failed subcase unless the change invalidates broader evidence.

Do not rerun passed F-cases without a concrete reason.

Stop the finalization run immediately on:

- credential leak;
- wrong-task continuation;
- cross-project leakage;
- unauthorized model downgrade;
- false validation PASS;
- stale-plan execution;
- write outside declared scope;
- fabricated telemetry;
- unexpected deletion or corruption of user-owned Claude settings.

Use safe isolated tests. Do not run destructive credential cleanup against the real Windows Credential Manager namespace.

---

## User working preferences

The user wants:

- exact commands;
- minimal repeated explanation;
- evidence-driven verdicts;
- no repeated questions whose answers are already known;
- smallest fixes only;
- no speculative rewrites;
- safe isolated testing;
- direct interpretation of pasted output.

Do not ask the user to rerun an already-passed F-case.

---

# Current installation/update state

The repository code baseline is:

`59010df5577e2457c673f74a29e093fbeae9d930`

The local installed runtime had not yet been physically confirmed updated to that #126 merge at the moment this handoff was written.

Before continuing F-06 in a new session, update the local installation.

~~~powershell
Set-ExecutionPolicy -Scope Process Bypass

Set-Location "C:\Vres F01 Δοκιμή\Vres-OS"

git checkout main
git pull --ff-only

$head = git rev-parse HEAD
$head

# If main has only advanced by this handoff/documentation commit,
# that is expected. The latest behavior-changing baseline is:
# 59010df5577e2457c673f74a29e093fbeae9d930

.\update.ps1 -UseRemotePostgres
~~~

Answer `y` if prompted.

Then:

~~~powershell
vres doctor
~~~

Expected:

- PostgreSQL connected;
- 34 migrations recorded;
- no new migration from #121/#123/#125 fixes.

Do not ask the user to rerun F-00.

---

# F-00 — PASS

Scope:

Migration/update smoke, doctor/selftest, statusline Windows compatibility.

Initial physical run found a real Windows status-line defect: backslash paths in Claude's `statusLine.command`.

Workflow:

- Issue #117
- PR #118
- fix normalized runtime executable path to forward slashes
- merged behavior commit: `f35bf19416083369aa87347a891d429081428cf5`
- CI #306 SUCCESS

Physical rerun:

- statusLine command auto became a forward-slash Windows path;
- status line rendered correctly.

F-00 = PASS.

---

# F-01 — PASS

Scope:

Fresh install/global/project Claude ownership/path/encoding/secure first start.

Used isolated current-user fixture instead of a second Windows user:

- test root: `C:\Vres F01 Isolated Δοκιμή`
- isolated Claude config: `$testRoot\.claude`
- isolated LOCALAPPDATA: `$testRoot\LocalAppData`
- source checkout: `C:\Vres F01 Δοκιμή\Vres-OS`

Physical evidence:

- global user sentinel survived;
- Vres global block added;
- custom settings/statusline preserved;
- shipped `vres-rules.md` hash matched;
- missing project `CLAUDE.md` generated minimal scaffold;
- existing project `CLAUDE.md` remained byte-identical;
- Greek and space-containing paths worked.

PowerShell 5.1 initially displayed mojibake only because of its default decode. `Get-Content -Encoding UTF8` showed the persisted text was correct UTF-8.

F-01 = PASS.

## Real Claude profile after accidental early fixture modification

The real profile was restored.

Real `CLAUDE.md`:

~~~text
<!-- vres-os:begin -->
@~/.claude/vres-rules.md
<!-- vres-os:end -->
~~~

Real settings were restored using the active runtime pointer dynamically.

Do not hardcode old release directories.

---

# F-02 — PASS

Scope:

- caught update/install rollback;
- interrupted journal protection;
- uninstall ownership;
- custom settings preservation;
- explicit cleanup containment.

## Interrupted journal

Physical result:

- update refused;
- uninstall refused;
- journal preserved.

PASS.

## Late update rollback

Injected a failure after status-line update.

Physical rollback proved:

- release restored;
- plugin restored;
- bin restored;
- `CLAUDE.md` restored;
- rules restored;
- settings restored;
- journal cleared.

PASS.

## Real defect #119

Physical uninstall initially failed with:

`Cannot overwrite variable HOME because it is read-only or constant.`

Root cause:

PowerShell variables are case-insensitive; local `$home` collided with built-in readonly `$HOME`.

Workflow:

- Issue #119
- PR #120
- renamed local variable to `$ClaudeHome`
- strengthened tests
- exact-head CI #308 SUCCESS
- merged
- post-merge CI #309 SUCCESS

Behavior main at that stage:

`4b68889f1217eabf6fcf5bd52b8547917f08d016`

Physical default uninstall rerun proved:

- runtime removed;
- plugin removed;
- Vres rules removed;
- user CLAUDE sentinel preserved;
- theme/custom sentinel preserved;
- replacement custom statusline preserved;
- project file unchanged.

Explicit cleanup rerun proved:

- owned config/log/runtime removed;
- outside sentinel preserved;
- project preserved.

F-02 = PASS.

## Important F-02 harness safety lesson

The isolated environment did not isolate Windows Credential Manager.

`uninstall.ps1 -RemoveLocalData` removed the real current-user `postgres.default` secret.

This was a test-design mistake, not a product defect.

The credential was securely repaired:

- new random runtime password;
- ALTER ROLE;
- `postgres.default` restored only in SecretStore.

Verification afterward:

- `vres doctor` connected;
- 34 migrations;
- `vres selftest` passed:
  - task_resume true
  - knowledge_retrieval true
  - procedure_reuse true
  - pareto_gate true

Do not rerun destructive credential cleanup under the same Windows account without true credential-store isolation.

---

# F-03 — PASS

Scope:

Stranded cancellation repair for historical task:

`TASK-20260918-865791f345`

Project:

`C:\Projects\Vres-60-Final-20260918-152340`

Historical defect lineage:

- #100
- PR #101
- permission issue after first fix
- corrective PR #102
- migration 032
- SECURITY DEFINER `latest_observed_user_instruction`

First physical cancellation prompt was too verbose and was rejected by the deliberately narrow cancellation parser.

No permission error occurred and no unrelated task work occurred.

Exact same-session prompt:

~~~text
cancel this task
~~~

succeeded.

Durable evidence:

- task status `cancelled`;
- project focus cleared;
- session unbound;
- cancellation event 1207;
- `TASK_STATUS_CHANGED` event 1208;
- `SESSION_UNBOUND` event 1209;
- no artifact/expert/repair/orchestration/validation activity after cancellation.

Evidence was recorded on #60.

F-03 = PASS.

UX observation only:

A long pasted cancellation instruction is rejected while exact `cancel this task` succeeds.

Do not treat that as a finalization defect unless a later acceptance criterion requires broader language.

---

# F-04 — PASS

Scope:

Bounded #60 model/assurance protected lifecycle.

Physical project:

`C:\Projects\Vres-F04-Protected-20260921`

Task:

`TASK-20260921-e0000dedf2`

Fixture:

bounded synthetic pricing recommendation with explicit protected independent review.

Correct arithmetic:

- A = 8.40
- B = 7.85
- C = 7.50

Important correction:

An earlier pre-fixture note mistakenly said C=7.05. 7.50 is correct.

Durable evidence:

- task `completed`;
- validation status `passed`;
- exactly one route;
- routing source `deterministic`;
- hard protected = true;
- assurance = `protected`;
- owner = `commercial-director`;
- capability = `cap.pricing`;
- exactly one worker:
  - agent `vres-os:sonnet-expert`
  - tier `sonnet`
  - observed model `claude-sonnet-5`;
- orchestration final event 1220:
  - `decision_ready=true`;
- orchestration final existed before validation request;
- exactly one validator request:
  - `VAL-6ce6d5c89ed04a7a`
  - observed `claude-fable-5-1`
  - status/outcome passed
  - 8 checks;
- validation completed before task completion;
- post-PASS events only:
  - `VALIDATION_INGESTION`
  - `SESSION_UNBOUND`
  - `TASK_COMPLETED`;
- no second validator;
- no repair loop;
- no reroute;
- no post-PASS orchestration mutation.

One premature completion call occurred before validator ingestion finished.

It was correctly rejected fail-closed and made no durable mutation.

Issue #60 was then closed.

F-04 = PASS.

---

# F-05 — PASS

Scope:

Persistent continuity through:

- native `/compact`;
- native `/clear`;
- real process exit/restart.

Project:

`C:\Projects\Vres-F05-Continuity-20260921`

Task:

`TASK-20260921-00f8c9eb71`

Probe:

`f05_probe.py`

Contents:

~~~python
print("F05 TEST PASS")
~~~

Original execution:

~~~text
python f05_probe.py
F05 TEST PASS
~~~

Durably persisted facts included:

- objective;
- one-file/no-delegation decision;
- changed surface;
- exact executed command/output;
- blocker/current condition;
- exact next action.

## Compact

Native `/compact`:

- PreCompact succeeded;
- PostCompact succeeded;
- same task rehydrated;
- all six durable facts recovered.

PASS.

## Clear defect #121

Initial physical evidence found old session persisted:

`end_reason='clear'`

instead of:

`provider_session_replaced`

Workflow:

- Issue #121
- PR #122

Fix:

canonicalize Claude native SessionEnd `clear` to Vres durable reason `provider_session_replaced`.

Merged behavior main:

`19ec313b1d81a2ddd245ac3f12b18269e15c96aa`

CI:

- PR #310 SUCCESS
- post-merge #311 SUCCESS

Physical rerun:

predecessor session showed:

`end_reason='provider_session_replaced'`

and its SESSION_END event had the same reason.

PASS.

## Process restart

A new Claude process recovered:

- same task;
- objective;
- decision;
- changed surface;
- previous test evidence;
- blocker;
- next action.

It reran:

`python f05_probe.py`

exactly once and got:

`F05 TEST PASS`

Latest checkpoint:

`CP-20260921-d6c6a6695e`

Task remained open intentionally.

F-05 = PASS.

---

# F-06 — IN PROGRESS

Do not restart F-06 from scratch.

The same-project concurrency portion is already physically PASS.

The remaining work is only the fresh cross-project isolation tail after the latest #125 fix.

Official F-06 contract in `docs/FINAL-VERIFICATION.md` requires:

- distinct task/session bindings;
- completion/clear must not jump into another task;
- ambiguity surfaced instead of recency guessing;
- live concurrent sessions not falsely closed;
- project-local state/agents/knowledge do not leak cross-project.

Maps LV-11 and LV-22.

---

# F-06 same-project concurrency — PASS

Physical project:

`C:\Projects\Vres-F06-Concurrency-A-20260921`

Tasks:

A1:

`TASK-20260921-8e51bf0c7f`

task id 88

A2:

`TASK-20260921-b58b9c0e79`

task id 89

project id:

`6701`

## First run exposed wrong-task continuation

After `/clear` in A1, both A1 and A2 reported the A2 task:

`TASK-20260921-b58b9c0e79`

Real defect.

Root cause:

replacement provider session opened unbound and project-wide focus pointed at A2, so replacement A1 inherited project focus instead of A1's predecessor task.

Workflow:

- Issue #123
- PR #124

Fix:

before project-focus fallback, a replacement session now inherits the still-active task of the most recent same-host predecessor session durably ended as `provider_session_replaced`.

Fix constraints:

- same project;
- same host PID;
- recent predecessor;
- never overwrite already-bound current session;
- never touch another live session;
- do not rewrite project focus;
- project focus remains fallback only when no replacement lineage exists.

Merged behavior main:

`dc9f29207f786af3518f7ad6b36a3e89e1bf2999`

CI:

- PR #312 SUCCESS
- post-merge #313 SUCCESS

## Physical rerun after #124

A1 current session:

`4cf2af6f-4c75-463a-b90d-8734dc34a6ad`

- task id 88
- task `TASK-20260921-8e51bf0c7f`
- open
- host PID 8768

A1 predecessor:

`4a486f48-ec5d-4491-8dde-31afebc97127`

- task A1
- same host PID 8768
- ended as `provider_session_replaced`

A2 current session:

`04b222a3-46bb-4de5-842c-f803c238ac79`

- task id 89
- task `TASK-20260921-b58b9c0e79`
- open
- host PID 20372

Binding event 1348:

- `source='provider_session_replaced'`
- previous A1 session -> new A1 session
- previous/new task both A1.

A2 remained open and untouched.

Therefore:

F-06 same-project concurrent session isolation = PASS.

Do not rerun it unless later session-lifecycle code changes.

---

# F-06 reply-guard observation

In A2, `start vres` produced one reply-guard warning:

`state_changed_after_reply_gate`

Claude immediately reran the gate as non-material and it passed.

Task checkpoint/activity sequence appeared unchanged.

No task state mutation occurred.

This is currently an observation, not an F-06 defect.

Do not open a defect unless it repeats in a way that causes state corruption, blocks valid behavior, or violates an acceptance criterion.

---

# F-06 original Project B evidence — VALID

Second physical project:

`C:\Projects\Vres-F06-Isolation-B-20260921`

B task:

`TASK-20260921-3cde3d3dc9`

Valid evidence already obtained:

## Cross-project task resume rejection

From B, attempted to resume:

`TASK-20260921-8e51bf0c7f`

Vres rejected:

~~~text
Error executing tool task_resume:
Object is outside the current project;
cross-project/global writes require separate authorization
~~~

No workaround used.

PASS evidence.

## B open-task listing

B listed only:

`TASK-20260921-3cde3d3dc9`

Neither A task appeared.

PASS evidence.

## Byte-identical fixtures

A and B `scope.txt` both had SHA256:

`F43FB550ECB8A940AFF67E52034927F853627AC2E61847C34AB5B50A923B9B29`

This byte-identity evidence is valid.

---

# F-06 contaminated onboarding evidence — preserve, do not reuse

The old A/B onboarding run exposed another real defect.

Proper A onboarding registered:

- source: `SRC-841191cfb396`
- location: `C:\Projects\Vres-F06-Concurrency-A-20260921\f06_scope_fixture\scope.txt`
- reported disk SHA256: `f43fb550ecb8a940aff67e52034927f853627ac2e61847c34ab5b50a923b9b29`
- job: `MIG-20260921-d64d5820`

Proper B onboarding registered:

- source: `SRC-fb2f2eb3768e`
- location: `C:\Projects\Vres-F06-Isolation-B-20260921\f06_scope_fixture\scope.txt`
- same disk SHA256
- job: `MIG-20260921-7d436a32`

Then, by mistake, an A-project Claude session was told to onboard:

`C:\Projects\Vres-F06-Isolation-B-20260921\f06_scope_fixture`

Vres accepted it under project A / project id 6701.

Job:

`MIG-20260921-f1fc291f`

This was real cross-project provenance contamination.

Do not delete it.

Do not clean the old A/B test projects.

Keep them as physical defect evidence.

Do not reuse them to prove the fixed cross-project onboarding behavior.

---

# Defect #125 / PR #126 — cross-project onboarding boundary

Issue:

#125 — F-06: onboard_folder can ingest another registered project's path

Root cause:

`onboard_folder(path)` used the current project id but allowed an arbitrary caller-supplied directory.

Therefore project A could mechanically ingest files physically owned by registered project B.

Because source registration deduplicates by:

- project id;
- content hash;
- source type;
- authority;
- version;

and then records additional supplied paths in `source_locations`, this could attach B's filesystem location as provenance to an A-owned source.

Fix:

PR #126 added a pre-ingestion scope guard.

Behavior now:

- current-project folder: allowed;
- external unregistered legacy folder: allowed;
- folder inside another registered Vres project: rejected;
- parent folder that would recursively sweep another registered project: rejected;
- rejection occurs before onboarding writes.

Integration test proves rejection adds no current-project:

- onboarding job;
- source;
- source location;
- review queue record.

No migration.

Final PR head:

`503096776f437c204cbac04122a07aea156f372e`

PR CI:

#316 SUCCESS

Merged behavior main:

`59010df5577e2457c673f74a29e093fbeae9d930`

Post-merge CI:

#317 SUCCESS

Issue #125 closed.

---

# Exact resume point

F-06 is not yet complete.

Do not rerun:

- F-00;
- F-01;
- F-02;
- F-03;
- F-04;
- F-05;
- F-06 same-project A1/A2 concurrency.

Resume only the cross-project portion using fresh project directories because the old A/B source provenance is intentionally contaminated evidence.

---

# Fresh F-06 cross-project rerun — first action

After updating the local Vres installation to current main, create fresh projects:

~~~powershell
$a = "C:\Projects\Vres-F06-XProject-A-20260921"
$b = "C:\Projects\Vres-F06-XProject-B-20260921"

New-Item -ItemType Directory -Force "$a\f06_scope_fixture" | Out-Null
New-Item -ItemType Directory -Force "$b\f06_scope_fixture" | Out-Null

$content = "F06_FRESH_SCOPE_20260921`nSynthetic project-isolation evidence.`n"
$utf8 = New-Object Text.UTF8Encoding($false)

[IO.File]::WriteAllText("$a\f06_scope_fixture\scope.txt", $content, $utf8)
[IO.File]::WriteAllText("$b\f06_scope_fixture\scope.txt", $content, $utf8)

git -C $a init
git -C $b init

Get-FileHash "$a\f06_scope_fixture\scope.txt" -Algorithm SHA256
Get-FileHash "$b\f06_scope_fixture\scope.txt" -Algorithm SHA256
~~~

Hashes must match.

---

# Fresh Project A

~~~powershell
Set-Location "C:\Projects\Vres-F06-XProject-A-20260921"
claude
~~~

Inside Claude:

~~~text
start vres
~~~

Then:

~~~text
Create a persistent Vres task named F06 Fresh Project A.

Objective: verify cross-project isolation after the F-06 onboarding boundary fix.

Keep it active. Do not delegate, validate, or complete it.

Report only the task key.
~~~

Record the new task key.

---

# Fresh Project B

Separate PowerShell:

~~~powershell
Set-Location "C:\Projects\Vres-F06-XProject-B-20260921"
claude
~~~

Inside Claude:

~~~text
start vres
~~~

Then:

~~~text
Create a persistent Vres task named F06 Fresh Project B.

Objective: verify cross-project isolation after the F-06 onboarding boundary fix.

Keep it active. Do not delegate, validate, or complete it.

Report only the task key.
~~~

Record B's new task key.

---

# First post-fix physical assertion: reproduce #125

From fresh A:

~~~text
Attempt to mechanically onboard only this folder:

C:\Projects\Vres-F06-XProject-B-20260921\f06_scope_fixture

Do not work around any Vres rejection.

Report the exact result only.
~~~

Required result is a rejection equivalent to:

~~~text
Onboarding path overlaps another registered Vres project;
run onboarding from that project's Claude session
~~~

If accepted, F-06 fails again and work must stop.

If rejected, #125 physical rerun PASS.

Do not repeat the old contaminated case.

---

# After #125 physical rejection succeeds

Continue only with the following F-06 tail.

## Proper A -> A onboarding

From fresh A:

~~~text
Mechanically onboard only:

C:\Projects\Vres-F06-XProject-A-20260921\f06_scope_fixture

Do not use embeddings.
Do not change my task binding.
Report the onboarding job result.
~~~

## Proper B -> B onboarding

From fresh B:

~~~text
Mechanically onboard only:

C:\Projects\Vres-F06-XProject-B-20260921\f06_scope_fixture

Do not use embeddings.
Do not change my task binding.
Report the onboarding job result.
~~~

Public Vres tools do not expose all stored source fields cleanly enough for proof.

Use one read-only PostgreSQL Python evidence script afterward.

Verify:

- A and B project ids differ;
- both source records have the same stored `content_hash`;
- A source is owned by A;
- B source is owned by B;
- A `source_locations` contains only A path;
- B `source_locations` contains only B path;
- no B path exists in A's fresh source locations;
- no A path exists in B's fresh source locations.

Do not trust Claude prose claiming a stored hash when it only computed the disk hash.

---

# Remaining LV-22 checks

## Cross-project A-only object access from B

Create one unambiguous project-local object in fresh A using a normal project-local public MCP surface.

Prefer a synthetic knowledge or registry object with a unique key/string.

From B:

- search for it;
- direct-read it by key;
- attempt mutation by key.

Required:

- B search does not leak the A-only object;
- direct read is rejected as outside current project;
- mutation is rejected.

Use the existing `_require_node` project guard as the expected enforcement mechanism.

Do not fabricate global authorization.

---

# company_wide=True test

From fresh B, use a public MCP surface such as `source_register(... company_wide=True)`.

No approval should be fabricated.

Required fail-closed result:

~~~text
Company-wide publication is held until a dedicated user scope-approval flow is verified
~~~

This is an intentional HELD preview boundary, not a missing feature to implement during finalization.

---

# F-06 complete-one / ambiguity tail

Official LV-11/F-06 also requires:

- complete one task;
- clear the other;
- ambiguity must be surfaced instead of guessed by recency.

Do this only after cross-project isolation checks are clean.

Do not weaken protected completion to make the fixture easy.

If completing the synthetic F-06 task would require unrelated protected orchestration/validation, design the smallest fixture consistent with current lifecycle semantics.

Required evidence:

- one session finishing its task does not jump into another session's active task;
- an unbound context with multiple unfinished tasks does not silently select the most recent one;
- `task_open_list` exposes ambiguity.

Inspect current behavior before improvising broad state changes.

---

# Expected final F-06 verdict

F-06 can be marked PASS only after:

1. same-project A1/A2 session/task separation — already PASS;
2. A1 clear/replacement task lineage — already PASS;
3. other live session not falsely closed — already PASS;
4. Project B cannot resume/list A tasks — already PASS historically;
5. post-#125 fresh A cannot onboard registered B's path — pending physical rerun;
6. fresh A/B own onboarding produces same content hash but separate source ownership/provenance — pending;
7. A-only object does not leak/read/mutate from B — pending;
8. `company_wide=True` is explicitly held — pending;
9. complete-one/clear-other does not jump tasks and ambiguous unbound state is surfaced — pending.

Only then mark F-06 PASS.

---

# F-07 onward

## F-07

Simple-task anti-overengineering and context discipline.

Goal:

prove trivial/small work does not spawn unnecessary persistent tasks, routing, agents, validators, or oversized context.

## F-08

Project-agent authority / gap acquisition.

Maps into remaining open issue #103.

Must physically prove project-agent ownership/authority and safe gap behavior.

## F-09

Real parallel fan-out / provenance / dependency join.

Also maps to #103.

Must use real governed parallel work, not sequential simulation.

## F-10

Retry / latest-plan / write-scope behavior.

Need prove retries obey current plan and declared writes, with no stale-plan execution.

## F-11

SEO multi-domain synthesis.

Exercises real multi-domain routing/synthesis.

## F-12

Product acceptance pass/fail.

Physical acceptance lifecycle.

## F-13

Procedure / knowledge reuse.

Evidence reuse is allowed under finalization rules if the required current surfaces are already proven and unaffected.

Do not repeat expensive historical fixtures automatically.

## F-14

Onboarding / retrieval.

Evidence reuse is allowed when still valid.

Note: #125 changed onboarding path-scope behavior, so reuse must not claim cross-project path safety from evidence generated before #126.

## F-15

Integrated realistic day / final verdict.

Must combine important current runtime surfaces and produce the final shippability verdict.

---

# Open issue #103

Current only open product issue:

#103 — Add first-class project agents and governed parallel execution DAG

Do not close it merely because unit/CI tests exist.

It remains tied to physical F-08/F-09/F-10/F-11/F-12 acceptance.

Close only when its physical finalization criteria are satisfied.

---

# Closed defect chronology

## #117 / PR #118

Windows status-line executable backslash normalization.

Merged behavior commit:

`f35bf19416083369aa87347a891d429081428cf5`

## #119 / PR #120

PowerShell `$HOME` collision in uninstall.

Merged behavior stage:

`4b68889f1217eabf6fcf5bd52b8547917f08d016`

## #121 / PR #122

Native `/clear` persisted literal `clear` instead of durable `provider_session_replaced`.

Merged behavior commit:

`19ec313b1d81a2ddd245ac3f12b18269e15c96aa`

## #123 / PR #124

Replacement session after `/clear` could bind to another concurrent task through project focus.

Merged behavior commit:

`dc9f29207f786af3518f7ad6b36a3e89e1bf2999`

## #125 / PR #126

`onboard_folder` could ingest a path owned by another registered Vres project.

Merged/current behavior baseline:

`59010df5577e2457c673f74a29e093fbeae9d930`

---

# CI chronology

Relevant successful main runs:

- #317 SUCCESS — current behavior baseline / #125 fix
- #313 SUCCESS — #123/#124 session-lineage fix
- #311 SUCCESS — #121/#122 clear-reason fix
- #309 SUCCESS — #119/#120 uninstall fix
- #306 SUCCESS — #117/#118 statusline fix

---

# Historical fixture IDs to preserve

F-03 cancelled task:

`TASK-20260918-865791f345`

F-04 protected pricing task:

`TASK-20260921-e0000dedf2`

F-05 continuity task:

`TASK-20260921-00f8c9eb71`

F-06 original same-project A1:

`TASK-20260921-8e51bf0c7f`

F-06 original same-project A2:

`TASK-20260921-b58b9c0e79`

F-06 original Project B:

`TASK-20260921-3cde3d3dc9`

These are historical evidence. Do not reuse them for fresh #125 cross-project proof.

---

# Historical projects to preserve

Do not clean:

`C:\Projects\Vres-F06-Concurrency-A-20260921`

`C:\Projects\Vres-F06-Isolation-B-20260921`

They contain useful physical defect/fix history.

The accidental cross-project onboarding in the old A/B fixture is evidence of #125.

Do not delete or manually rewrite its DB provenance just to make the database aesthetically clean.

Use new fresh project directories for post-fix evidence.

---

# Post-finalization roadmap — retained, DO NOT IMPLEMENT YET

## 1. Claude -> Codex execution handoff

Desired direction:

`vres handoff codex`

Principles:

- Vres owns the task;
- hand off task state, not transcript/protocol translation;
- no generic gateway/polling framework initially;
- Codex is a governed executor;
- continuation packet should include:
  - task/objective;
  - constraints;
  - decisions;
  - current step;
  - dependencies;
  - write scope;
  - acceptance;
  - files;
  - evidence;
  - tests;
  - blockers;
- prefer `codex exec --json`;
- trust postconditions, not exit code alone;
- writes should use temporary worktree + changed-path verification after physical workspace-write preflight;
- current Windows Codex workspace-write may be unreliable;
- never fall back to danger-full-access.

## 2. External Capability Discovery & Audit

Inventory installed MCP/plugins/skills/agents.

Classify:

- USE
- USE WITH GUARDS
- DEVELOPMENT REQUIRED
- DECLINE

Installation != adoption.

Vres retains model/effort authority.

## 3. JEV Browser Control

First browser-control fixture.

Likely USE WITH GUARDS.

Normal browser MCP/profile/auth.

Do not let a model-pinned `jev-browser` agent become a governed Vres agent.

## 4. E-11 UX/UI Browser Audit Capstone

Audit account creation flow.

Produce durable:

- screenshots;
- journey evidence;
- findings;
- remediation;
- redesign;
- diagram;
- presentation-ready evidence.

The later presentation should not require rerunning the browser audit.

## 5. Superpowers plugin

Optional external development methodology only.

Never a Vres runtime dependency.

---

# New-session resume instructions

When this handoff is opened in a new chat/session:

1. Treat this file as the authoritative continuation state.
2. Verify current GitHub main only if needed.
3. Do not reopen F-00..F-05.
4. Do not redo F-06 same-project concurrency.
5. Confirm/update the user's installed Vres runtime to current main.
6. Resume at fresh F-06 cross-project post-#125 rerun.
7. First physical assertion: fresh A must reject onboarding fresh registered B's folder.
8. Then finish remaining F-06 source-scope/global-scope/complete-one/ambiguity checks.
9. If F-06 passes, move directly to F-07.
10. Continue the finalization ladder through F-15.
11. Keep #103 open until its physical project-agent/DAG acceptance surfaces pass.
12. No new feature work before finalization completes.

The immediate user-visible action after loading this handoff should be the concise update/install command block followed by the fresh F-06 A/B setup.

Do not spend a turn re-explaining historical context unless asked.
