# Vres-OS #165 — Personal C0 READ-ONLY Chairman selection preview, source candidate

**Date:** 2026-10-26 (Europe/Athens).
**Repo:** vosser24/Vres-OS.
**Feature branch:** feature/165-chairman-policy-foundation-20261023.
**Documentation branch:** docs/chatgpt-continuity-20261023.
**TRANCHE:** #165 PERSONAL C0 / offline read-only Chairman model-selection preview.
**STATE:** **SOURCE_CANDIDATE_COMMITTED, AUTHOR_STATIC_ONLY, CLAUDE_INDEPENDENT_STATIC_NOT_RUN, WINDOWS_PYTEST_NOT_RUN, C0_NOT_ACCEPTED**.
**Scope:** single-user PERSONAL Vres, not a published SaaS, public trust or IAM product. The preview MUST NOT read/update installed settings, authorize a model switch, contact PostgreSQL or access credentials.

## 0. Read-first and exact source identity

Read the CURRENT docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md first, then THIS new C0 source handoff, followed by:
- docs/handoffs/VRES-165-B2B1-A1-R2-INDEPENDENT-OFFLINE-ACCEPT-PERSONAL-NEXT-PHASE-2026-10-26.md — last independent #165 DENY-ONLY **OFFLINE_ACCEPT**.
- docs/handoffs/VRES-165-B2B1-A1-R2-WINDOWS-93-PASS-AND-INDEPENDENT-EVALUATION-PENDING-2026-10-26.md — historical original operator 117-line selected Windows test output at A1 R2 (93 reported PASS, exit0; separate Claude OFFLINE_ACCEPT later).
- Historical R3 denial-only architecture/erratum and Phase A Chairman pure policy/materializer.
- docs/roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md and docs/roadmap/VRES-CHATGPT-LED-FULL-SCOPE-DELIVERY-PLAN-2026-10-22.md — still-active V-01..V-42 personal project roadmap, not declared delivered.

**Exact GitHub feature identity** (verified through source branch, GitHub commit/tree, two-ADD allowlist):

| Identity | SHA / path |
| --- | --- |
| **New C0 candidate HEAD** | **e6bd8cb8f92a779da1469efe738709918e9da6df** |
| **New candidate tree** | **afb9e3c88b17c5342425895ca9fa7798f0ad0752** |
| **Parent = last independently OFFLINE_ACCEPTED A1 R2** | **9754b190083a0ada757ebee07f2ef5b8f312b58e** |
| Accepted A1 R2 parent tree | 5372c5ecdc7c6ebbb0cbc9956288250255e7db4e |
| ADD src/vres_os/chairman_selection_preview.py | **blob 1fb133e5d1b79bc4d6f6e305f5c9b03f6c752658**, 82 Git-added lines |
| ADD tests/test_chairman_selection_preview.py | **blob 79028cf72e33db11efa001687ba77ba7b1bb9ddf**, 177 Git-added lines |
| Existing pure ChairmanPolicy/materializer | src/vres_os/chairman_policy.py, blob **36e62d6a2712ac305fd4070bac658b94d61d155e** |
| Existing static template | plugins/vres-os/agents/chairman.md, blob **64cba93d6f69960350a0006b594734288f087ccc** |
| Protected conftest unchanged | tests/conftest.py, blob **1c33bb206dbf42691a6af9a709514bf3cc9994af** |
| pyproject unchanged | pyproject.toml, blob **b2d5e30d10d7be0613e90bf3ed1e346be5678969** |

The feature branch moved by GitHub expected-head/nonforce from A1 R2 HEAD 9754b190083a0ada757ebee07f2ef5b8f312b58e to C0 e6bd8cb8f92a779da1469efe738709918e9da6df. Recursive tree diff and new GitHub commit readback showed **exactly TWO ADDED paths and ZERO modifications/deletions** in C0. Commit unsigned, NOT a protected endorsement or installed artifact. No existing A1 R2, B1/B2A, plugin template, global Claude settings, install scripts, DB or source history rewritten.

## 1. Minimal PERSONAL preview behavior and honest terminology

New **pure** \`preview_chairman_selection(template: bytes, *, reported_baseline: ChairmanPolicy, proposed: ChairmanPolicy) -> str\`:
1. Accept ONLY explicit typed caller-supplied existing/baseline and proposed policy objects (reuse accepted Phase A ChairmanPolicy; no new policy engine or privilege abstraction).
2. Recreate/revalidate both frozen/slotted policy values to catch malformed or low-level corrupted objects; refuse unknown model/effort/version types rather than silently downgrade/fallback.
3. Use the accepted \`materialize_chairman\` pure renderer on the caller-supplied static template for the baseline; require that the rendered baseline reproduces exactly the supplied bytes, proving only **internal SOURCE TEMPLATE CONSISTENCY**, NOT live installed status.
4. Materialize proposed candidate purely in memory against the same template (Phase A preserves original body and LF/CRLF convention).
5. Return only human-readable **preview text** with labels "Reported baseline (NOT live-verified)" and "Proposed candidate (NOT installed)", changed model, changed effort and changed policy version (or explicit no-op), plus hashes computed from supplied original template/candidate content.
6. State clearly: **caller-supplied historical baseline, not a live host measurement; no approval, settings change, model activation or installation**. Even exact matching inputs create no operator event, trusted history, apply API, installer or permit.
7. No function reads any file/installed config, database, keyring, provider, system model, global Claude settings or network service. No output claims physical runtime model identity or authenticated consent.

**Concrete historical context:** last operator-observed personal release \`20261022172833-4d82147b\` from original P2 \`82c82430b38f93bd6b9d5c3af3b5de9c1368af9c\` was **Chairman Sonnet/high**. The source template also has \`model: sonnet\`, \`effort: high\`; user previously requested a proposal to switch to **Opus/medium**, which remains an **UNINSTALLED candidate**. The new function does not query the actual currently installed model. This is a **developer API building block**, not a wired UI/CLI action or installed feature. Native application preview/confirmation/rollback, if useful, are distinct future phases with explicit user approval and no surprise writes.

## 2. New test selection — AUTHORED BUT NOT_RUN

The separate new file \`tests/test_chairman_selection_preview.py\` tests:
- Deterministic informative Sonnet/high -> Opus/medium text; explicit historical baseline vs proposed/uninstalled caveats.
- Computed source-template and actually materialized candidate SHA-256; preserving unchanged body and accepted native newline behavior.
- Both LF and CRLF input styles.
- Identical/no-op preview, version-only display without authorization.
- Refusal of claimed baseline that disagrees with supplied template.
- Exact typed policies; rejects None, bools, dictionaries, other non-policy objects.
- Malformed, non-Chairman, duplicate-key, empty/invalid UTF-8 source template.
- Low-level mutation/deletion of policy fields fail-closed.
- Smoke check the module exports no permission, provider, keyring, IO or installer symbols.

**Existing accepted** \`chairman_policy.py\`, materialization test file, template and \`tests/conftest.py\` are NOT modified. The new tests use entirely in-memory fixture bytes and pure original Phase A ChairmanPolicy/materialize_chairman. No database fixtures, file access, child processes or direct Vres task state is used by new test code. As always, conftest process-level guards are not a physical OS sandbox.

**Current evidence:** ChatGPT author checked exact imports and line lengths in source/test text, source parent/tree/blob identity and allowed Git changed paths. **NO independent Claude security review, Windows CPython execution, pytest collection, runtime TEST PASS or C0 OFFLINE_ACCEPT yet.** Do not extend A1 R2's prior 93-PASS acceptance to a distinct new HEAD.

## 3. Future C0 review and minimal test ladder

The user asked ChatGPT to lead step by step and asked whether to close all open Claude sessions. Correct guidance:
- **NO**, not every Claude session. Old finished **Vres-specific** A1 R1 / A1 R2 / B2B R3 review sessions may be closed with \`/exit\` once no run is active. Keep unrelated sessions and any actively running work. Exiting Claude Code does not delete its history or Git worktrees.
- Do NOT delete/reset any old accepted review worktrees, force-kill ongoing jobs, clear Claude global settings, destroy local Vres task state or run \`claude --resume\` into stale R1/R2 sessions.
- After user executes the NEW guarded C0 source checkout and posts \`VRES_165_C0_PERSONAL_PREVIEW_SOURCE_REVIEW_READY\`, open **ONE FRESH Claude Code session** in the new C0 worktree. Do not use previously completed R2 session for the new source.
- Proposed new Windows checkout path: \`C:\Projects\Vres-ChatGPT-Review-165C0-Preview-20261026\` (distinct from A1 R1/R2 and R3). Git worktree add creates it; no separate mkdir required.
- Guard original P2 anchor \`C:\Projects\Vres-P2F-Postinstall-Hardening-20261022\`, HEAD \`82c82430b38f93bd6b9d5c3af3b5de9c1368af9c\`, clean porcelain and official HTTPS origin. Require destination absent, fetch exact feature remote HEAD \`e6bd8cb8f92a779da1469efe738709918e9da6df\`, worktree add \`--detach\` that SHA, check head/tree/accepted parent/exact two new blobs, **exact TWO ADDED file paths** against parent, \`git diff --check\` and clean checkout. Stop on unexpected SHA or dirty original; no old checkout modification.
- Claude STATIC-FIRST use Read/Glob/Grep only (no Bash/Git/Python/pytest/source edits/DB/global Claude actions), read entire 2 new files, accepted Phase A pure policy/materializer, selected source template, full protected conftest before any new test, pyproject and relevant tests. Report independent STATIC_PASS / STATIC_REJECT / STATIC_BLOCKED with exactly which files/lines inspected; focus on baseline honesty, exact byte matching, no-op, malformed, LF/CRLF, hashes and true absence of I/O. Even STATIC_PASS must NOT execute pytest in same step.
- If STATIC_PASS, ONE user-controlled Windows offline bounded pytest command at new C0 exact SHA, under the existing safe conftest:

      py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_selection_preview.py

  Capture **echoed exact command**, actual individual PASSED/FAILED case IDs, exit code, live-app-data fence unexpected refusals and integration_opt_in, post-run unchanged HEAD/tree/clean status. No extra Python version probes, broad suite, hidden retries, DB even SELECT or installed tests.
- Independent Claude evidence-only verdict OFFLINE_ACCEPT/REJECT/BLOCKED is a separate step. After each substantive review, checkpoint documentation independently, preserve any REJECT and create a NEW source SHA for fixes. Do not claim C0 accepted before observed Windows test and independent evaluation.

## 4. Permanent PERSONAL operational holds and roadmap

**LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL contact, EVEN SELECT**, no startup/bootstrap/health check that might touch incident server. F1 actual operator consent/protected H/Fable trust and issue #165 remain OPEN/PARTIAL; this OFFLINE preview does NOT solve them. Real credentials/keyring/vault, signing, native source trust, provider or protected Fable calls, live model dispatch/switch, installer, user-global Claude/plugin/settings mutation, PR/main merge, physical host model observation and release remain separately held until explicit approval. Installed Chairman Sonnet/high is unchanged; Opus/medium is a proposal.

Preserve K0-T1 blocked, PA-01..PA-08 incomplete, D2 open, F2 quarantined, R0 NOT_RUN, L-04 OPEN, V-01..V-42 roadmap; old B2B v0/R1/R2 DESIGN_REVISE and R3 DESIGN_ACCEPT only offline deny-only; previous B2A R3 independent 95 reported PASS/exit0 and R3-PROC-01 extra version probe; A1 R1 independent 71 reported PASS/exit0; last A1 R2 independent 93 reported PASS/exit0 with command echoed and informational I-1..I-5, all scoped to their original SHA. The previous VRES_REPLY_GUARD_WARNING means Vres task persistence cannot be presumed healthy; GitHub docs are the durable record. No task-state/DB probe attempted.

**Next-session short resume:** source C0 new GitHub HEAD **e6bd8cb8f92a779da1469efe738709918e9da6df**, tree **afb9e3c88b17c5342425895ca9fa7798f0ad0752**, parent independently OFFLINE_ACCEPT A1 R2 **9754b190083a0ada757ebee07f2ef5b8f312b58e**, strictly 2 ADD paths \`src/vres_os/chairman_selection_preview.py\` blob **1fb133e5d1b79bc4d6f6e305f5c9b03f6c752658** and \`tests/test_chairman_selection_preview.py\` blob **79028cf72e33db11efa001687ba77ba7b1bb9ddf**; C0 new source/tests independent STATIC_NOT_RUN/WINDOWS_PYTEST_NOT_RUN. User can close finished Vres Claude sessions but need not close all. Next guarded NEW C0 Windows worktree, Claude STATIC FIRST, then selected test only if approved; this is a READ-ONLY dev preview, not installed UI or model switch. Keep PERSONAL scope and all schema-048/credential/provider/installer/global settings/main restrictions.
