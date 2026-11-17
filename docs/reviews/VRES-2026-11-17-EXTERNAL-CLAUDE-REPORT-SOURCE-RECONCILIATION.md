# Vres-OS — externally supplied Claude read-only report: source-grounded reconciliation
**Date:** 2026-11-17 (Europe/Athens)  
**Scope:** P0 GitHub-read-only reconciliation; reporting external analysis only, no source changes, execution or runtime clearance.  
**Received material:** owner-supplied text attributed to Claude (Anthropic), titled "Independent read-only review: Vres-OS issue #185 (W4 first-FULL personal Windows closure)", 219 numbered source-display lines / 18,610 bytes in the uploaded file. Local uploaded-file SHA-256: `c60e13f6bcd9692cc321651ee58aeefbcd6379be97e2342cb475c9ded87a7fd5`. The original full report was supplied in a ChatGPT conversation attachment and is not represented as a GitHub-posted authenticated reviewer submission.

## Independent-review provenance and reported verdicts
The provided report says a separate Claude cloud workspace read public Git source/docs without executing repository Python, tests, Windows commands, PostgreSQL, installed hooks or changing GitHub. Its author expressly says they **did not read issue #185 body/comments**, could not supply a human/cryptographic signoff and grant NO operational authority. No independent reviewer GitHub identity or review artifact is authenticated by this record. Because #185 requires an actual distinct source-grounded review of its full terms, **do not mark that issue complete or claim positive F1/Fable authority**.

Reported three-part determinations (NOT self-issued operational clearance):
- **THREAT_MODEL: REVISE.** Revisit user-only filesystem ACL assumptions, OS/Python authenticity, out-of-band SHA-256 provenance and explicitly unmitigated hostile same-user/admin/repository scenarios.
- **RELEASE_DESIGN: DESIGN_REVISE.** Design a new, separate source-only package for the existing Personal Day, not a P1 edit, R13 cherry-pick or original `stage()` bypass; add reviewed allowlisting, pre-import verification and accident guards; an optional offline first-path package is NOT an accepted first-FULL feature release.
- **OPERATIONS:** P0 read-only GitHub allowed; new source-only engineering and later isolated tests are **conditional on separate explicit owner approval and respective gates**; installed Windows/P2, current PostgreSQL (even SELECT), real credentials, native Claude/hooks, protected merges and real UAT remain **BLOCKED**.

## This session's fresh independent GitHub readback (not from the attached report)
`docs/chatgpt-continuity-20261023`: HEAD `8d3c65a15ad0563b247333e6f9b44d2cd27c64a8`, TREE `bf78edb70419e02cddaabe80412c2126a6536968`, parent `de235807583843ee80104c3f5d628d5e98b48a79`.

`feature/personal-day-human-plan-integrated-20261117`: HEAD `179dbfc81a076f2aa1600e3392f538885c8178b3`, TREE `219fb4a7147a029a36a7db89f98497dd39dd59af`, parent `9e2b538b06f34926f611db7e20120be572577101`.

Protected `main`: HEAD `9a8acc5d464b96432a93cb95daa9581412fb07ee`, TREE `659d3fdd6e635dbaecbd5c492ba7279754edaec7`, two parents `6af7bddf246e0f628c3e52add9528742e85189ca` and `8ae041721bf0418f6472ab541b6838fd73fec46a`.

Protected R13 `feature/personal-w4-r13-universal-staging-hold-20261106`: HEAD `bcf62460d68caebfdbd0e838d44c5997992c5fbc`, TREE `9bbc5615fef4a8f785e9ddb0056e9430ffe25d63`, parent `0badcd34d1eafbce5f815512a489d70cb240eecd`.

Issue #185 LIVE: OPEN, no assignee; `help wanted`. The report does not change these facts.

## Verified static source observations
1. `src/vres_os/personal_portable_delivery.py` remains historical P1, Git blob `79180e365179f53c74bc2f397c6b88f96805730c`. Its `_MAX_BYTES = 128 * 1024` and ten older blob pins cannot represent this Personal Day candidate. The PowerShell launcher accepts `Get-AuthenticodeSignature(...).Status -eq 'Valid'` without confirming the exact Python publisher AND owner-selected executable digest; this is a real static trust gap, not proof of an exploitable current Windows install.
2. `pyproject.toml` Git blob `b2d5e30d10d7be0613e90bf3ed1e346be5678969` declares only `vres` and `vres-mcp`; current `personal_day_desktop.py` Git blob `316e2507f2cb615fe5926a6d76cd02de92f84cd4` declares an opt-in Tk `main()` / `__main__`, **not** an accepted Windows launcher.
3. `install.ps1` Git blob `8b5dd6dcc3cc8315f7a4c27d0173b4963b52d933`, lines ~219 onward, invokes original `release_artifact.py stage`, then venv/pip and later `claude plugin validate` / plugin publication. Under the existing incidents, this path MUST NOT BE USED. The current `release_artifact.py` Git blob `497fa3d96742a868f8b00b5dcb26e8afe03fd159` still defines callable `stage()`.
4. Protected R13 `personal_w4_no_launch_release.py` contains direct-file Python bootstrap reading/checking siblings and `exec(compile(...))` before its protected refusal; **not** an independent pre-execution trust root.
5. Current `project.py` imports the processes module at top level and inside `discover_project` reaches `sources`; `sources.py` imports `approvals` at top level and defines a lazy `db` contact helper. Thus potential optional DB/child-process dependencies exist. Static imports alone do not establish safe execution or contact.

## Important qualifications to the Claude report
- The report claims a **52-module full import closure** and describes it as the same as a **54-entry inventory**; those counts are not identical. Its AST methodology and dynamic/importlib/plugin/conditional paths have not been independently reproduced by this session. **Do not upgrade the inventory to STATIC_COMPLETE or dependency-complete**, or infer that only stdlib/Tk/wheel-free bytes suffice for full V-01..V-42.
- A package that deliberately excludes `db`, `sources`, `secrets`, keyring, migrations and wheels is a **narrow offline Personal Day slice**, NOT the complete eventual owner-requested Windows/Chairman/PostgreSQL/learning/credential application. Preserve original V-01..V-42 and #165–170/#176 instead of silently reducing scope.
- The local PC's `C:\Projects`, `%LOCALAPPDATA%` and other NTFS ACL/reparse/link/sync characteristics are UNKNOWN. Default ACLs cannot be represented as a physical-machine observation. Explicit verification is mandatory before any actual write.
- A Python `sys.addaudithook` or `sys.meta_path` denylist can help accidental route control but is **not** a strong sandbox or trustworthy initial source verifier; separately validate import/startup order and Windows `pythonw -I -S -B` zip behavior. Do not claim these proposals PASS.
- Optional retry after `PermissionError` in the original lifecycle needs precise fresh state/identity checks to preserve interrupted-state manual recovery and must never silently change the original owner under an untested proposal.
- Python file bytes and ZIP digests require independently selected SHA-256 out of band, not merely a same-repository self-certified hash. Git SHA-1 identifies objects; it is not Vres publisher trust.
- Claude's report is a valuable **external AI assessment**, not a signed complete independent #185 acceptance. Its author explicitly did not read #185; request issue-body reconciliation by the distinct reviewer without executing source.

## PASS / FAIL / NOT_RUN separation
- **OBSERVED PASS (this session, static):** authenticated GitHub branch commit/tree/parent + issue readback; selected file/line/source checks above; local uploaded report SHA-256 captured.
- **REPORTED PASS (Claude only, not re-run here):** source/tree inventory and 58 Git blob matches, source AST analysis.
- **CONFIRMED DESIGN GAPS (static):** historical P1 launcher/pins/cap, unexposed Desktop entry, original installer stage/pip/plugin path, R13 current-source divergence.
- **NOT_RUN:** independent signed/authenticated reviewer review of full issue #185, independent import closure proof, exact current source full compile/integrated tests, Python/Tk/wheel Windows runtime closure, physical NTFS checks, source ZIP build, executable Windows launch, Windows dummy/real UAT, PostgreSQL, native Claude/hooks, issue #169/#170 acceptance. Prior 732/732 belongs only to parent `9e2b538b`; current `179dbfc8` historical 11/11 stub-owner narrow test report does NOT imply full acceptance.

## Gate and next concrete milestone
Before writing a new **source** branch, obtain informed specific owner approval for exactly one `feature/personal-w4-first-full-source-closure-...` branch from freshly verified `179dbfc8` for the source-only integrated Personal Day launch/package design (R1–R5 and R7 refinements), **no execution, no packaging to Windows, no staging, no actual installs, no original P1 edits, no main/R13 merge, no DB/host/credentials/PRISM/legacy operations**. Scope must describe the offline initial package as a stepping stone, not first-FULL readiness. A separate distinct reviewer must reconcile #185 full issue and any changes before any runtime authorization. Upon explicit owner consent, implement the coherent integrated source+test changes on a dedicated engineering branch with expected-SHA nonforce Git update/readback. Do NOT stage or execute code merely because an earlier user said "go" to review. 

All incidents stay OPEN: `LIVE_SCHEMA_048_INCIDENT` (NO PostgreSQL even SELECT); `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED` (NO native Claude Code/hooks); historical P3; F1/Fable positive authority NOT_GRANTED; WPR/R13 release holds; installed P2/Windows local worktrees UNKNOWN; no real TASK-DAY-01, credentials, profile, PRISM, global KEEP/DROP, installer or rollback.
