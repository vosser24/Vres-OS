# Vres-OS — 2026-11-03 M3 PERSONAL session-resume wrong-task prevention — source published, Windows next

**Status:** M3 P1 SOURCE_COMMITTED / GITHUB_REMOTE_VERIFIED; new WINDOWS OFFLINE TEST NOT_RUN. This is a practical one-Windows-user Chairman/session-continuity improvement, NOT enterprise IAM, an installed upgrade, physical host verification, PostgreSQL or independent F1/Fable clearance.

## 1. Source, GitHub identities, exact changed files

Repo: https://github.com/vosser24/Vres-OS
New feature branch: feature/personal-m3-session-resume-ambiguity-guard-20261103
New HEAD: 1469765d7403f1985aa9ba65978299fdaa32f941
New TREE: e05f4d632b5226d4f1946c1fa0da8c116c8c108f
Exact single parent: 7a1d2da36f9ef1475e7909ca8850b9b641380b1d
Parent TREE: 98658c0270b65032f38ab38c0671c48b2a291bc1
Feature commit: https://github.com/vosser24/Vres-OS/commit/1469765d7403f1985aa9ba65978299fdaa32f941

Exactly three changed paths, verified via GitHub compare: modified src/vres_os/session_lifecycle.py, new blob 090122c81caddd0cc19490c31f3fb22011bf740d; modified src/vres_os/hooks.py, new blob 481b7fe49dfb024d8029278f354299666dc1888e; added tests/test_personal_session_resume_ambiguity.py, blob 64288c3d23bea59e2307f22937d9f56d4cc42c00. No installer, release manifest, hook definition JSON, database guard, credential, model-policy, real user profile, real legacy project, PR or main merge changes.

Product main last verified HEAD 9a8acc5d464b96432a93cb95daa9581412fb07ee, TREE 659d3fdd6e635dbaecbd5c492ba7279754edaec7. Accepted combined M2+#167 source branch and parent remain unchanged. Its earlier integrated selected Windows source acceptance was 254 distinct PASS, three Windows symlink-privilege SKIPPED, pytest exit0, release-inputs 001–041 exit0, clean protected Git pre/post and restored environment. Full record: docs/handoffs/VRES-2026-11-03-HARD-CHECKPOINT-INTEGRATED-M2-167-254PASS-3SKIP-POSTFLIGHT-ACCEPTED.md. Do NOT rerun the 254 tests for this focused M3 change.

## 2. Practical defect and exact correction

The existing replaced-session task inheritance selected ORDER BY recent end time LIMIT 1 among eligible same-host/same-project unfinished predecessors. When several provider sessions had been replaced recently, that could resume the wrong task. Project-focus fallback was then invoked without distinguishing the ambiguous predecessor case.

The new session-lifecycle query retains project, host-PID, replaced-reason, unfinished-task and ended-state constraints; additionally bounds predecessor end time around the current session start (plus/minus two minutes), fetches at most TWO rows, and raises an explicit ambiguity error for any two valid candidates. No bind/update/event occurs in that refusal. A unique predecessor and a valid existing binding preserve earlier semantics.

The two Chairman lifecycle entry points, SessionStart and UserPromptSubmit, now skip ALL implicit project-focus fallback when this specific ambiguity occurs. They surface a VRES_CONTINUITY_AMBIGUOUS message asking the user to choose the exact task key, without claiming there are no unfinished tasks when no context projection is selected. Other unexpected errors are not silently reclassified as safe.

This reuses the EXISTING Vres sessions/tasks/project-focus truth owners. It neither creates a parallel memory database nor modifies running Vres hooks. Effectiveness under real native Claude is NOT_RUN and held.

## 3. Evidence — original results must remain distinct

The new test module has TWELVE test functions / FOURTEEN expected parametrized pytest cases. It covers unique predecessor, multiple different-task and same-task predecessors, no mutation on ambiguity, missing predecessor, pre-bound session, missing provider/host identification, no fallback on ambiguity, nonambiguous fallback, correct SessionStart and UserPromptSubmit messages, no false empty-task report, and unexpected storage-error propagation.

Tests use synthetic data and monkeypatch connection functions, not real PostgreSQL. The existing tests/conftest.py has a live user-profile AppData fence. New module selected Windows pytest has **NOT_RUN** in this ChatGPT session; GitHub source publication, reading source and creating a script do NOT count as unit PASS. GitHub CI triggers push to main or pull requests; no PR/main change or CI test is claimed.

One FULL native Windows PowerShell 5.1 script was prepared: docs/handoffs/VRES-PERSONAL-M3-SESSION-RESUME-WINDOWS-GATE-2026-11-03.ps1, Git blob c7d1a47beb95edb98d4136893258adad70356c56. It uses official origin and original protected P2 checkout preflight, exact source HEAD/tree/parent/three-path allowlist and three PRE blobs; creates NEW detached C:\Projects\Vres-Review-M3-Session-Resume-20261103 only if absent; scrubs process PG/DB/VRES/Git env within a try/finally and uses disposable TEMP/AppData; invokes only py -3.12 -B -m pytest on new synthetic module with plugins disabled; checks exit0 + fourteen named PASSED rows and zero named SKIPPED/FAILED; restores process environment; checks POST source HEAD/tree/three blobs and both checkouts clean. Success marker: VRES_PERSONAL_M3_OFFLINE_SESSION_RESUME_COMPLETE_PENDING_EVALUATION. This script is STATIC-AUTHORED, not yet Windows-parsed or executed. The first internal JavaScript template draft was syntax-invalid BEFORE creating any Git object or executing any Windows command; the corrected unexecuted script is the only published candidate, not a Python or Windows test failure.

## 4. Hard holds and protected history remain unchanged

LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL contact even SELECT, direct or indirect via CLI, MCP, hooks, doctor, bootstrap, migration, F2, recovery or database introspection. HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: seven historical native Claude posttool Read/Grep DB-routing attempts refused; NO ordinary native Claude Code, running installed hooks or plugin validation. Independently trusted F1/Fable positive authority NOT GRANTED. Source matchers and Stage3–6 static/dry-run results are not real host safety proof. No actual installed Vres, Claude global settings/PRISM, real credentials, model changes, real legacy project or main merge without separate P3 dispositions and exact owner P2 approval.

Original installed P2 historically observed SOURCE HEAD 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c, TREE 205c081277ece483c634e1c801c39595abd4549c, installed source hooks blob 5833973d9be6ccf4263dda2d461cc5994d30416c, NOT freshly inspected this chat. Keep protected original Git checkout C:\Projects\Vres-P2F-Postinstall-Hardening-20261022 and every previous Windows review worktree untouched (rejected #167, accepted #167 R1, M2 rollback, #167 store, accepted combined M2+#167 and all historical P2 worktrees).

Retain rejected A12 original 18 PASS/1 FAIL commit 345a568b551ac23183c54f10611335adee903b96, A13 original 28 PASS/1 FAIL cdaa39aaa774cef88a4831bf6b157e380fbb69d9; A16 environment-copy uncertainty, A19 blocked/uncommitted, original #167 Windows 43 PASS/1 FAIL corrected R1 44 PASS, first integrated PowerShell parser-rejected attempt before any commands, corrected wrapper's missing aggregate-summary after successful pytest, and separately completed later read-only postflight. Keep PT1/PT2A–D, Hook-R1, Stage1–6, E7/E8, C2B/R0/F2, original complete V-01..V-42 and issues #165–170/#174/#176.

## 5. EXACT NEXT action / roadmap

NEXT ONE atomic P1 Windows operator step: copy the FULL committed guarded native PowerShell script into ordinary Windows PowerShell 5.1 OUTSIDE Claude, upload the COMPLETE stdout/stderr or transcript for evaluation. Do not rerun 254 earlier cases; do not execute real installer, Claude or PostgreSQL. On full 14 PASS/zero SKIP/exit0 plus clean Git and restored env, record only selected M3 WINDOWS OFFLINE ACCEPTANCE, then continue one useful integrated Chairman/experience or synthetic adoption slice. If failed, preserve rejected actual output, correct on isolated exact-parent branch, never bypass the guard.

M0–M8 PERSONAL roadmap remains: M2 installation HELD; M3 Chairman/task/experience; M4 existing Claude/PRISM new and legacy adoption; M5 same-Windows-user credential and source reuse; M6 Visual Studio #169; M7 limited pilot #170; M8 optional later. All original 42 requirements binding, no removal.

Automatic checkpoint at or before 20 completed assistant replies or conservative over-half context: verify docs/main/source HEAD/tree/parents, publish authorized complete work and dated handoff/index using expected-old-SHA nonforce, provide FULL inline fenced fresh-session resume prompt and finish the chat. Do not invent real Windows, trusted reviewer, installed or PostgreSQL evidence.
