# Vres-OS #165 — C1 personal standalone Chairman preview CLI: Windows REVIEW_READY, next independent STATIC gate

**Date:** 2026-10-26, Europe/Athens.
**Repository:** vosser24/Vres-OS.
**Canonical docs branch:** docs/chatgpt-continuity-20261023.
**Feature branch:** feature/165-chairman-policy-foundation-20261023.
**Current state:** **OPERATOR_C1_DETACHED_SOURCE_REVIEW_READY**, **INDEPENDENT_C1_STATIC_NOT_RUN**, **WINDOWS_C1_PYTEST_NOT_RUN**, **C1_OFFLINE_ACCEPT_NOT_GRANTED**, **NOT_INSTALLED**.
**Scope:** personal single-user Windows Vres. This is a source-checkout, read-only Chairman preview command. No model switch, provider API, credentials, user-global Claude settings, installer, Vres task database or product main contact.

## 0. Read-first and scope of this checkpoint

Read the CURRENT docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md, then THIS latest READY checkpoint, then:
1. docs/handoffs/VRES-165-PERSONAL-C1-STANDALONE-READONLY-CHAIRMAN-PREVIEW-SOURCE-CANDIDATE-2026-10-26.md — original two-ADD C1 source candidate at commit c545556a4ba9ba48f140e7379da960708a7f3c8d with behavioral and test details.
2. docs/handoffs/VRES-165-PERSONAL-C0-INDEPENDENT-OFFLINE-ACCEPT-PROCEDURAL-ANOMALY-AND-NEXT-PHASE-2026-10-26.md — direct C1 source parent C0, independently STATIC_PASS and OFFLINE_ACCEPT strictly for pure read-only preview.
3. docs/handoffs/VRES-165-PERSONAL-C0-WINDOWS-34-PASS-POWERSHELL-ELSE-ANOMALY-EVALUATION-PENDING-2026-10-26.md — historical complete 191-line C0 Windows evidence, including NONBLOCKING post-test C0-PROC-01 standalone PowerShell else error.
4. docs/handoffs/VRES-165-B2B1-A1-R2-INDEPENDENT-OFFLINE-ACCEPT-PERSONAL-NEXT-PHASE-2026-10-26.md — separate accepted A1 R2 deny-only contract, parent of C0.
5. Historical B2A/B1/Phase A source evidence, R3 bounded DENY-ONLY design/erratum, V-01..V-42 personal roadmap and all protected incident holds.

Do NOT confuse an operator READY worktree with independent STATIC_PASS or Windows test PASS. This checkpoint records **ONLY the guarded C1 source checkout**.

## 1. Exact Git source identities and immutable reviewed parent

| Field | Verified exact SHA or path |
| --- | --- |
| **NEW C1 target commit / checked-out HEAD** | **c545556a4ba9ba48f140e7379da960708a7f3c8d** |
| **NEW source tree** | **65c7b29f0be7b5c8f930d2383a0a4da8d6193268** |
| Parent / independently accepted C0 | **e6bd8cb8f92a779da1469efe738709918e9da6df** |
| NEW C1 CLI source | src/vres_os/chairman_selection_cli.py |
| C1 CLI source blob | **6fd0ddcd2b82fca4a48f6a790fee3d0e6ae657d1** |
| NEW C1 selected tests | tests/test_chairman_selection_cli.py |
| C1 selected tests blob | **599dccb8dc10487796d71337f80a76f089024dbd** |
| Previously accepted C0 pure preview, UNCHANGED | src/vres_os/chairman_selection_preview.py blob **1fb133e5d1b79bc4d6f6e305f5c9b03f6c752658** |
| Accepted Phase A policy/materializer UNCHANGED | src/vres_os/chairman_policy.py blob **36e62d6a2712ac305fd4070bac658b94d61d155e** |
| Existing static Chairman plugin template UNCHANGED | plugins/vres-os/agents/chairman.md blob **64cba93d6f69960350a0006b594734288f087ccc** |
| Protected conftest UNCHANGED | tests/conftest.py blob **1c33bb206dbf42691a6af9a709514bf3cc9994af** |
| Pytest config UNCHANGED | pyproject.toml blob **b2d5e30d10d7be0613e90bf3ed1e346be5678969** |
| Original personal P2 anchor | C:\Projects\Vres-P2F-Postinstall-Hardening-20261022 @ **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c** |
| **NEW created detached clean C1 review checkout** | **C:\Projects\Vres-ChatGPT-Review-165C1-CLI-20261026** |

ChatGPT verified GitHub source HEAD/tree/parent and exact two ADDED path/blob identities against GitHub before authoring this handoff. The operator's guarded Windows checkout independently reports successful checks of all seven listed blob identities. Claude has NOT examined C1 source yet. GitHub source branch has no new commit after c545556a4ba9ba48f140e7379da960708a7f3c8d at checkpoint creation.

## 2. User-provided PowerShell checkout — actual observed evidence

The user pasted a full interactive PowerShell transcript. It establishes the following specific positive output labels, not a Python or test run:

    === C1 PERSONAL CLI WORKTREE PREFLIGHT ===
    PASS: Original P2 HEAD
    PASS: Original P2 clean
    From https://github.com/vosser24/Vres-OS
       e6bd8cb..c545556  feature/165-chairman-policy-foundation-20261023 -> origin/feature/165-chairman-policy-foundation-20261023
    PASS: Remote C1 HEAD
    Preparing worktree (detached HEAD c545556)
    HEAD is now at c545556 feat(chairman): add #165 C1 standalone personal read-only preview CLI
    PASS: C1 review HEAD
    PASS: C1 review tree
    PASS: Accepted C0 parent
    PASS: C1 CLI source
    PASS: C1 CLI tests
    PASS: Accepted C0
    PASS: Original policy
    PASS: Chairman template
    PASS: Test isolation
    PASS: Pytest config
    PASS: Exactly two added C1 files
    PASS: Detached C1 worktree clean
    SOURCE_SHA=c545556a4ba9ba48f140e7379da960708a7f3c8d
    SOURCE_TREE=65c7b29f0be7b5c8f930d2383a0a4da8d6193268
    VRES_165_C1_PERSONAL_PREVIEW_CLI_SOURCE_REVIEW_READY

The full operator-provided script also:
- Checked the existing P2 path and prevented creation over an already-existing C1 review path.
- Checked the origin against the official vosser24/Vres-OS HTTPS URL; no positive label was printed for this conditional but no STOP occurred.
- Required original P2 exact HEAD 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c and clean tracked/untracked porcelain; got PASS for both.
- Ran only git fetch --no-tags on the feature ref and checked the expected remote C1 SHA before creating a worktree.
- Created the C1 detached worktree at the new exact head; did not change the original P2 checkout.
- Guarded HEAD, tree, direct accepted C0 parent, both new blob identities, C0/Phase A/plugin template/protected conftest/pyproject blobs.
- Checked the new worktree was detached. This was guarded by a throw-on-failure conditional rather than a separate PASS marker.
- Compared the accepted C0 parent to C1 with git diff --name-status --no-renames and required EXACTLY TWO lines beginning A (new C1 module and new C1 tests); PASS reported for this allowlist.
- Ran git diff --check from parent to C1, with no printed integrity errors and no STOP. It checked clean tracked/untracked worktree status and reported PASS.
- Printed BOTH complete C1 HEAD and tree SHA with the READY marker; no STOP or error appeared.

**Evidence provenance:** this is operator-supplied Windows stdout, corroborated against GitHub source objects by ChatGPT. This is NOT an independent Claude audit, not a physical installed-release measurement, and not a Python test. The observed shell script contains no C1 pytest, provider action, Vres task operation, PostgreSQL, install or model-change invocation. The original transcript remains in the user's conversation; this handoff preserves its exact success values and guarded methodology, but is not falsely called a complete byte-for-byte copy of all PowerShell prompts.

## 3. New C1 source functionality requiring separate independent review

Source path src/vres_os/chairman_selection_cli.py is a thin Python module entrypoint exposing a usable checkout-bound preview, NOT a Vres-installed CLI. Command shape after future acceptance:

    py -3.12 -B -m vres_os.chairman_selection_cli --source-root <explicit-source-checkout> --reported-model sonnet --reported-effort high --proposed-model opus --proposed-effort medium

The command:
- Uses argparse with explicitly supplied repo checkout source root, both baseline/proposed model and effort, optional source policy versions (default1).
- Reads ONLY a fixed repo-relative source file plugins/vres-os/agents/chairman.md in binary, limited to 512KiB plus a refusal read byte. Its path is drawn from the explicit caller-controlled source checkout; it MUST NOT be mislabeled a live installed Chairman check.
- Delegates all policy validation, source/template matching, immutable candidate rendering and actual hashes to the ALREADY ACCEPTED C0 preview and Phase A policy materializer.
- Displays an ASCII-safe read-only version of C0 text for legacy Windows terminals, with explicit baseline (NOT live-verified), proposal (NOT installed), no approval/setting modification language and source/rendered hashes.
- Has no apply/installer/model-selection mutation, no db/bootstrap/CLI imports, provider or credentials dependency.
- Returns 0 for a preview and nonzero for missing/mismatched/malformed source/invalid inputs, with neutral template error text and no secret path echo.

New src code is restricted to PERSONAL source-level read-only functionality. No real runtime/provider model activation or current-host/native installed-model attestation occurs; the C1 command has NOT been invoked or independently evaluated.

## 4. C1 authored test selection and possible review risks

New selected test file tests/test_chairman_selection_cli.py contains fourteen test functions and parametrized cases. It writes a fake plugin Chairman template only into pytest's disposable tmp_path **during a future approved test**, not the operator's installed or git worktree file. It is currently SOURCE ONLY and tests are NOT_RUN.

Independent STATIC reviewer should specifically inspect:
- File read selection and source-root correctness: a user-supplied root can point to a wrong checkout; exactly one expected fixed relative template file is read; symlink check only directly protects the final template path, not all parent junction/reparse points; decide proportional safety for a PERSONAL explicitly-chosen source, not enterprise multiuser privilege claims.
- Argparse parsing for model/effort, exact bounded canonical version, required arguments, no silent fallback or CLI/bootstrap import side effects.
- Correct model-only/effort-only/no-op/version rendering, LF/CRLF, body preservation, real digest generation delegated to accepted C0. Check legacy Windows ASCII substitution and any error-path encoding problem without inventing an observed failure.
- Report text must never claim live installed Sonnet/high or approval; source checkout still may not be installed state.
- Read-only actual preview vs disposable tmp_path fixture WRITE during tests: do not incorrectly call entire test collection strictly no-filesystem-writes.
- Honest negative test assertions, single Path.open read behavior and risks of monkeypatching Path.open while pytest capture is active; whether tests truly exercise desired refusals.
- No DB, vault, keyring, protected model/validator, provider, subprocess, installer/apply, arbitrary dynamic import or user-global Claude/config write. Test fixture is a permitted temp-only file writer, not a production code feature.
- Existing protected tests/conftest.py in FULL before proposing a selected pytest run, pyproject pytest config and accepted C0 pure preview/Phase A pure policy source. Document partial vs full reads honestly.

**If a concrete correctness error is found, STATIC_REJECT; do not run pytest or "fix" anything in the review worktree.** Cosmetic/minor personal-use theoretical issues are INFORMATIONAL. Source repairs require new ChatGPT-authored exact SHA and separate review, never rewriting accepted C0.

## 5. NEXT C1 independent Claude STATIC-only review

The user should NOW open a **fresh** Claude Code session in the ALREADY-CREATED C1 checkout. Do NOT create another C1 worktree, fetch/reset/stash, rerun C0/A1 tests or resume stale R1/R2/C0 sessions.

    Set-Location -LiteralPath "C:\Projects\Vres-ChatGPT-Review-165C1-CLI-20261026"
    claude

**Independent static-only reviewer tools:** Read/Grep/Glob only. NO Bash, Shell, PowerShell, Git, Python, pytest, MCP, Vres task/DB/provider, Codex, subagent, file edit or commit. Read BOTH new C1 source/test files IN FULL, accepted C0 preview and Phase A policy IN FULL; also full protected tests/conftest.py (last independent static review counted 1513 lines), relevant C0 and Phase A tests, only necessary static plugin Chairman header/body and pyproject pytest config. Keep exact file/line coverage and disclose partial reads.

Report:
- A. Exact operator-provided source SHA/tree/parent and exact reviewed file content; do NOT falsely claim Git verified by Claude.
- B. Lines read fully vs partially, tests integrity, no Io/PG/provider/globals aside from bounded explicit read.
- C. BLOCKING and INFORMATIONAL issues referenced by file/line; focus on real personal usability/safety.
- D. An honest conftest process-only isolation and new test fixture temp-write assessment. This is not OS/network attestation.
- E. Exactly one verdict **STATIC_PASS / STATIC_REJECT / STATIC_BLOCKED**, status **PYTEST_NOT_RUN / NO_SOURCE_MODIFICATION / NO_AUTHORITY_ISSUED / NO_MODEL_ACTIVATION**, terminal marker **VRES_165_C1_PERSONAL_PREVIEW_CLI_STATIC_REVIEW_COMPLETE**.
- Even if STATIC_PASS, STOP, and DO NOT run pytest in Claude static step.

**Future only after independently STATIC_PASS, subject to new operator instruction:** ONE bounded Windows selected offline pytest, not yet run:

    py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_selection_cli.py

The future selected test must echo exact C1 working directory, command and source SHA, count actual printed PASSED/FAILED case IDs, capture process exit immediately, app-data protected fence (unexpected refusals/integration opt in), and post-test unchanged HEAD/tree/porcelain. Do not repeat C0 34-test suite just to reprove accepted C0. After actual selected test evidence, a separate Claude evidence-only OFFLINE_ACCEPT/REJECT/BLOCKED is necessary before claiming C1 independently accepted or invoking user preview against a source checkout.

## 6. Standing personal incident and full continuity

**LIVE_SCHEMA_048_INCIDENT=OPEN means NO PostgreSQL contact, EVEN SELECT.** D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 blocked, L-04 OPEN, PA-01..PA-08 pending. Original #165 F1 genuine trusted operator consent/protected history/Fable authority remains OPEN and C1 read-only source template is NOT that authority.

Installed PERSONAL Chairman Sonnet/high is not changed. Opus/medium remains UNINSTALLED proposed candidate. Installed release 20261022172833-4d82147b (last operator-verified source P2 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c), historical product main and unrelated feature branches are not updated by C1 checkout. No credentials/vault/keyring, signing, global Claude hooks/settings/plugins, native provider/Fable, installer, active model switch, physical #169 test, PR/main merge or live release without separate user approval.

Earlier independent C0 OFFLINE_ACCEPT at e6bd8cb8f92a779da1469efe738709918e9da6df: 34 individually PASSED Windows selected test cases, wrapper exit0, nonblocking late C0-PROC-01 PowerShell ELSE syntax error and five informational findings. A1 R2 accepted at 9754b190083a0ada757ebee07f2ef5b8f312b58e with 93 individual PASS; A1 R1 accepted at 1b406c788057f0cb2a8a57578b89110a11b76161 with 71 PASS; B2A R3 accepted at 32847410952e9d4620bf7046cbee4a41a7ddc73b with 95 individual PASS/exit0 but distinct historical R3-PROC-01 extra Python version probe. B2A R2 prior 91/92 REJECT and initial static REJECT, B2B design v0/R1/R2 DESIGN_REVISE, R3 DESIGN_ACCEPT strictly OFFLINE DENY-ONLY with erratum; earlier Phase A/B1/F2/P2-A1 accepted/rejected exact-SHA evidence all preserved. V-01..V-42 full personal capability roadmap is NOT fully implemented by C1.

Keep prior **VRES_PERSISTENCE_WARNING** (Claude user instruction not safely staged) distinct from **VRES_REPLY_GUARD_WARNING** (Vres reply task pre-gate not verified). No Vres task/DB probe, bootstrap or healing; canonical GitHub docs/handoffs are durable.

## 7. GitHub docs-only transaction and next-session resume

This handoff is a NEW documentation file and one MODIFY to docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md on canonical docs branch atop verified prior docs HEAD **1a551336122128da3dc77f6160e96c192d8978ea**, tree **be0ad6f71a3bc5114fe684556aafa7e53fcd1921**. Require strict recursive old/new tree difference of exactly these 2 documentation files, no source change; single-parent GitHub commit, nonforced expected-head ref update and post-commit readback of both docs and feature source refs.

**NEW-SESSION RESUME:** feature C1 exact commit c545556a4ba9ba48f140e7379da960708a7f3c8d, tree 65c7b29f0be7b5c8f930d2383a0a4da8d6193268, parent independently accepted C0 e6bd8cb8f92a779da1469efe738709918e9da6df, two new C1 ADD files source blob 6fd0ddcd2b82fca4a48f6a790fee3d0e6ae657d1 and tests blob 599dccb8dc10487796d71337f80a76f089024dbd; accepted C0, Phase A, plugin template and protected conftest UNCHANGED. User executed guarded Windows checkout, original P2 clean, fetched exact GitHub feature, created NEW clean detached C1 review worktree C:\Projects\Vres-ChatGPT-Review-165C1-CLI-20261026, verified SHA/tree/parent/all seven blobs/two ADD/diff integrity and printed VRES_165_C1_PERSONAL_PREVIEW_CLI_SOURCE_REVIEW_READY. Independent Claude C1 STATIC_NOT_RUN, Windows selected C1 PYTEST_NOT_RUN, C1 OFFLINE_ACCEPT NOT GRANTED. NEXT fresh Claude Code static-only in existing C1 worktree; no source edits or tests yet. Personal single-user source-checkout read-only interface, not installed Chairman or Opus activation; preserve all original F1/#165, LIVE_SCHEMA_048 NO PostgreSQL, V-01..V-42 and credential/provider/global Claude/model/installer/main holds.