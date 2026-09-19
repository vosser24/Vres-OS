# Vres-OS finalization verification suite

**Purpose:** This is the blocking live suite for deciding whether the current Vres-OS build is ready for wider live evaluation.

The exhaustive `LIVE-VERIFICATION.md` remains the detailed regression catalog. Do not run all historical LV/PA/UE cases after every change. Use this suite to prove each distinct current contract once, then use surface-triggered regressions for future releases.

**Current candidate at creation:** `c896ddbeb37180c609ebe1f49ef09ce162ea2a85`, 34 migrations, post-merge CI #301 green.

## Evidence policy

For every F-case record exact source commit, installed release id, Claude Code version, Python version, PostgreSQL version, start/end time, commands/actions, observed result, PASS/FAIL/BLOCKED/REUSED status, sanitized evidence path, defect id and reviewer.

A prior live PASS may be marked **REUSED** only when all of these are true:

1. its evidence names an exact prior commit and is available for review;
2. no owning implementation/configuration surface changed between that commit and this candidate;
3. no relevant native dependency/provider contract changed materially;
4. F-00 passes on the current candidate;
5. the matrix names the reused evidence id/commit and why it remains applicable.

Do **not** reuse evidence for #60 cancellation/protected lifecycle, #103 project-agent/DAG/acceptance behavior, or UE status-line/compaction/read/output behavior until those surfaces have passed on the current candidate.

Stop the finalization run on a credential leak, wrong-task continuation, cross-project leakage, unauthorized model downgrade, false validation PASS, stale-plan execution, write outside declared scope, fabricated usage telemetry, unexpected deletion or corrupted user-owned Claude settings.

## Execution order

Run in order. Cheap ownership/continuity checks precede protected/multi-agent work.

### F-00 — Exact build, update, migration and telemetry identity

**Maps:** LV-00, LV-03, LV-07, LV-33, UE-01.

**Execute:** With Claude/Codex/workers closed, update from the exact candidate source. Verify Git SHA, installed release id, plugin validation, `vres start` migration application in an existing disposable project, then `vres doctor`, `vres status`, `vres selftest`. Inspect the Claude status line after one trivial prompt.

**PASS requires:**
- exact candidate SHA installed;
- PostgreSQL records exactly the candidate migration count;
- doctor/selftest pass;
- status line renders only host-supplied model/effort/context/5h/7d values;
- missing optional telemetry is omitted, never rendered as a fabricated 0%;
- no polling/error spam or obvious terminal latency;
- current task state is preserved across the binary/schema update.

**Fail fast:** Do not continue if update, migration, selftest or status-line startup fails.

### F-01 — Fresh install and Claude ownership boundaries

**Maps:** LV-01, LV-02, LV-04, PA-01, PA-02.

**Execute:** In a disposable Windows profile/VM with sentinel content in user `~/.claude/CLAUDE.md` and `settings.json`, perform a fresh install and secure first start. Test a path containing spaces/non-ASCII characters. Start one fresh project without `CLAUDE.md` and one with a custom project `CLAUDE.md`.

**PASS requires:**
- user-owned global content survives outside the single Vres managed import block;
- `vres-rules.md` matches the shipped candidate;
- Vres adds a statusLine only when absent or Vres-owned; an unrelated custom statusLine is preserved;
- a missing project `CLAUDE.md` receives only the minimal scaffold;
- an existing project `CLAUDE.md` is untouched;
- credentials are entered only in the secure local setup console;
- supported paths/encoding work.

### F-02 — Installer/update failure, uninstall and recovery ownership

**Maps:** LV-05, LV-06, LV-34, LV-35, LV-36.

**Execute:** In snapshots, exercise one caught update/install failure after user settings/global rules have been touched, one interrupted-install journal case, uninstall without local-data removal, and explicit local cleanup in a separate disposable profile.

**PASS requires:**
- caught failure restores prior active runtime/plugin/bin/global Claude rules/settings bytes;
- interrupted journal blocks blind retry and remains recoverable evidence;
- uninstall removes only Vres-owned runtime/plugin/PATH/global block/Vres-owned statusLine;
- a custom replacement statusLine survives uninstall;
- DB/project/vendor logins are not deleted;
- explicit cleanup never escapes owned paths or acts while workers/journals make removal unsafe.

### F-03 — Stranded cancellation repair

**Maps:** #60 prerequisite / prior cancellation defect.

**Execute:** On the project containing `TASK-20260918-865791f345`, use the explicit current cancellation prompt. Commit the user instruction, cancel the bound task, and inspect final status/session binding.

**PASS requires:**
- task transitions to `cancelled`;
- session unbinds;
- no artifact/expert/repair/orchestration/validation work occurs after the cancel instruction;
- no stale-instruction error;
- no `permission denied for table user_input_observations` error;
- historical task evidence remains intact.

**Do not reuse:** Must run on the current candidate before #60 closure.

### F-04 — Bounded #60 model/assurance protected lifecycle

**Maps:** #60 final fixture, LV-12, LV-13, LV-18.

**Execute:** Use the bounded deterministic protected architecture fixture: one obvious existing software-engineering owner, Sonnet worker, explicit protected review trigger, decision-ready final, exactly one canonical validator, direct completion.

**PASS requires:**
- deterministic/single-owner route where applicable;
- no invented specialist/capability;
- governed Sonnet worker model is host-observed;
- no explicit `Agent.model` override;
- latest `ORCHESTRATION_FINAL` is `decision_ready=true` before validation prepare;
- one canonical Fable/high validator attempt;
- validation PASS;
- no second validator, repair loop or post-PASS governance mutation;
- task completes directly.

**Evidence reuse:** Existing A0, routine persistent Sonnet, protected Sonnet and historical deep Fable→Opus→protected-Fable evidence may be referenced; do not repeat the large Opus architecture fixture.

### F-05 — Continuity under checkpoint, compact, clear and restart

**Maps:** LV-08, LV-09, LV-10, UE-02, UE-03.

**Execute:** In one persistent engineering task record objective, decision, changed surface, executed test result, one blocker and exact next action. Exercise native `/compact`, then native `/clear`, then normal exit/restart.

**PASS requires:**
- durable task state survives every transition;
- compacted context retains objective/constraints, durable decisions, changed files/symbols, actual evidence, blocker/current state and next action;
- repeated/stale exploration/raw output is not needlessly retained;
- prior same-host provider session closes as `provider_session_replaced` after `/clear`;
- replacement session binds/rehydrates the correct task;
- unsaved reasoning is not invented after restart.

### F-06 — Concurrent sessions and cross-project isolation

**Maps:** LV-11, LV-22.

**Execute:** Open two Claude sessions in the same project with distinct tasks and one session in a second project. Alternate updates, clear one, complete one, inspect bindings and attempt cross-project access/mutation.

**PASS requires:**
- task/session bindings remain distinct;
- completion/clear does not jump into another task;
- ambiguity is surfaced rather than resolved by recency guessing;
- live concurrent sessions are not closed by mistaken liveness inference;
- project-local state/agents/knowledge do not leak or mutate cross-project.

### F-07 — Simple-task anti-overengineering and context discipline

**Maps:** PA-02, PA-09, UE-04, UE-05.

**Execute:** Give one mechanically simple implementation task with deterministic acceptance, one short known file, one large unfamiliar file/log, and one noisy test/build command.

**PASS requires:**
- smallest direct path: deterministic tool or one governed worker only;
- no manufactured capability/project agent/work graph/reviewer when unnecessary;
- write-capable work freezes deterministic criteria and completes without a judgmental verifier;
- short known file is read directly;
- large/unknown source is narrowed by search/markers and bounded reads;
- noisy command output is filtered/redirected and inspected in bounded excerpts;
- true command exit status remains evidence;
- no custom Read/Bash runtime appears.

### F-08 — Project-agent authority and governor-confirmed gap acquisition

**Maps:** PA-07 plus #107 hardening.

**Execute:** Use a synthetic missing capability. Attempt acquisition before a blocked route, with the wrong gap, with a valid exact blocked gap, duplicate acquisition against that gap, project-agent frontmatter with `model:`/`effort:`, valid registration, then source drift.

**PASS requires:**
- pre-block and wrong-gap acquisition rejected;
- exactly one project capability can be acquired per confirmed blocked gap before rediscovery;
- rediscovery finds/reuses it;
- project agent cannot choose model/effort;
- valid source digest/role/capabilities are preserved;
- changed agent source invalidates reuse until explicit re-registration;
- no company-wide authority is silently created.

### F-09 — Real parallel fan-out, provenance and dependency join

**Maps:** PA-03, PA-04.

**Execute:** Run at least two independent registered project-agent units in one native dispatch, followed by one dependent synthesis/integration unit.

**PASS requires:**
- distinct `agent_key`, role, capability and tier remain separate;
- two native subagent execution intervals overlap in host time;
- host-observed model/work-unit/agent provenance exists for both;
- dependent unit is not ready before all prerequisites pass;
- it becomes ready immediately after the join condition is satisfied;
- final synthesis uses every required report.

### F-10 — Retry isolation, latest-plan invariant and write-scope safety

**Maps:** PA-05, PA-06 plus #105/#109 hardening.

**Execute:** With two independent units, let one succeed and one fail after claim; observe host stop; retry only the failed unit. Separately attempt replanning while a unit is running, old-plan execution after a newer plan, overlapping write scopes, and one direct edit outside the declared scope.

**PASS requires:**
- successful sibling is never relaunched;
- failed attempt retains host provenance and only that unit becomes retryable after prior host stop;
- new worker can bind on retry;
- replanning across running work is rejected;
- older plan becomes historical/non-executable once a newer plan exists;
- overlapping scopes cannot run concurrently;
- direct Write/Edit outside scope is denied;
- disjoint allowed scope succeeds;
- no claim that Bash is an OS sandbox.

### F-11 — SEO-style multi-domain end-to-end synthesis

**Maps:** PA-08.

**Execute:** Use the bounded synthetic SEO/ecommerce app-design scenario. Require genuine SEO, Google/API, data/database, dashboard/UX, ecommerce/digital and system-architecture reasoning, but let discovery reuse shipped capabilities and acquire only real missing project specialists.

**PASS requires:**
- staffing is evidence-driven, not a fixed panel;
- independent specialist work overlaps where appropriate;
- directors/project specialists/capabilities remain distinguishable;
- system-architecture synthesis waits for prerequisites and uses all required reports;
- material disagreement is arbitrated rather than averaged;
- no worker/project agent chooses its own model;
- simple subproblems within the same installation still use the minimal path;
- final assurance follows consequence/risk rather than team size.

### F-12 — Independent judgmental product acceptance, pass and fail

**Maps:** PA-10, PA-11.

**Execute:** Build one bounded write-capable product slice with deterministic implementation criteria and one genuinely judgmental UX/product/domain criterion. Run a report-only dependent verifier once with PASS, then in a fresh/current plan with FAIL.

**PASS requires:**
- criteria are frozen before implementation;
- implementation worker reports deterministic evidence only and cannot self-approve judgmental criteria;
- verifier is not ready before implementation passes;
- verifier receives only authorized target criteria and remains report-only;
- passed judgment permits finalization;
- failed judgmental acceptance leaves verifier evidence durable but blocks finalization;
- remediation uses new/current work rather than rewriting the failed result;
- protected validation, when required, remains a separate assurance layer.

### F-13 — Procedure and durable knowledge reuse with provenance/scope

**Maps:** LV-14 through LV-22, LV-31, LV-32.

**Execute:** Use one small synthetic transformation/analysis contract. Correct it once, explicitly accept it, `/clear`/restart, apply the same procedure to new data, record one limited observation/preference with source provenance, then inspect project/cross-project retrieval.

**PASS requires:**
- exact accepted contract is reused rather than yesterday's output;
- changed approved content requires new approval;
- negation/source provenance is preserved;
- observation remains scoped/limited, not promoted to causation/policy;
- old/superseded knowledge remains history without becoming current truth;
- project scope is enforced;
- no automatic procedure/model promotion from self-reported speed/token claims.

**Evidence reuse:** May be REUSED when prior physical evidence exists and procedure/knowledge/provenance surfaces are unchanged from that evidence commit.

### F-14 — Onboarding and retrieval baseline

**Maps:** LV-23 through LV-27.

**Execute:** Onboard a small synthetic mixed-format folder including duplicates and an unusual/error case. Retrieve via lexical search with embeddings disabled. If embeddings are enabled for the release, run the optional embedding runtime case too.

**PASS requires:**
- raw source files remain untouched;
- extraction/dedupe/provenance bounds are visible;
- malformed/unsupported cases fail visibly rather than hanging or fabricating content;
- lexical retrieval works without embeddings;
- embeddings are NOT RUN, not PASS, when disabled.

**Evidence reuse:** May be REUSED when onboarding/parser/retrieval/dependency surfaces are unchanged from prior reviewed physical evidence.

### F-15 — One realistic day and final verdict

**Maps:** LV-29, LV-37, UE-06.

**Execute:** Without engineer coaching, perform one realistic synthetic day using the normal Chairman conversation: resume durable state, one simple deterministic task, one specialist/multi-agent task, one reusable procedure/knowledge lookup, one compact/clear transition, one product acceptance check and one protected action where required. Record status-line/context/usage observations.

**PASS requires:**
- all current non-reused blocking F-cases have PASS evidence;
- any REUSED evidence meets the reuse rules above;
- no unresolved critical defect;
- optional disabled features are recorded NOT RUN, not passed;
- user can operate through normal conversation without knowing internal MCP tools;
- no false claims of production readiness or measured token savings;
- UE usage observations are recorded descriptively across comparable scenarios and do not auto-change routing/model policy.

## Surface-triggered regression policy after finalization

After the suite passes once, future changes run **F-00 + the cases owned by the changed surface + F-15 smoke**, not the whole historical matrix.

| Changed surface | Minimum rerun |
|---|---|
| installer/update/uninstall/global Claude/statusLine | F-00, F-01, F-02, F-15 |
| session lifecycle/hooks/compaction/reply guard | F-05, F-06, F-15 |
| assurance/model routing/validator/completion | F-04, F-15 |
| project agents/capability discovery/acquisition | F-08, F-11, F-15 |
| work graph/retry/provenance/write scopes/latest plan | F-09, F-10, F-15 |
| acceptance criteria/product verifier | F-07, F-12, F-15 |
| procedure/approval/preferences/knowledge | F-13, F-15 |
| onboarding/parsers/retrieval/embeddings | F-14, F-15 |
| engineering skill/read/Bash efficiency rules | F-07, F-15 |
| docs-only with no executable/instruction contract change | F-00 smoke; no automatic full rerun |

## Optional and held features

- Codex adapter: run the historical optional Codex case only when Codex is enabled for the candidate.
- Embeddings: run only when installed/enabled; otherwise mark NOT RUN.
- Headless Claude `-p`, `--max-turns`, native headless plan mode: not part of the current runtime and therefore not finalization blockers.
- Production/customer data: outside this controlled synthetic finalization suite.
