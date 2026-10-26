# Vres-OS #165 — Personal C1 R1: old Windows pytest EXIT 1, oversized pytest-ID environment limit, test-only source correction

**Date:** 2026-10-26 (Europe/Athens).
**Repo:** vosser24/Vres-OS.
**Canonical docs branch:** docs/chatgpt-continuity-20261023.
**Feature branch:** feature/165-chairman-policy-foundation-20261023.
**Current verdict:** OLD C1 HEAD **c545556a4ba9ba48f140e7379da960708a7f3c8d** has independent STATIC_PASS but **WINDOWS SELECTED PYTEST EXIT 1**; **NOT independently OFFLINE_ACCEPTED**. NEW C1 R1 HEAD **7ac041018d4ec5a06be07318ecce5e140faccd91** is **ONE-LINE TEST-ONLY SOURCE CANDIDATE**; **STATIC_NOT_RUN / WINDOWS_PYTEST_NOT_RUN / OFFLINE_ACCEPT_NOT_GRANTED** for this new SHA.
**Scope:** pragmatic PERSONAL single-user Windows read-only Chairman preview CLI. No live installed model change, no provider, credentials, global settings, DB contact or main merge.

## 0. Canonical read-first and latest actionable boundary

Read docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md first, then THIS latest C1 R1 failure/correction handoff, followed by:
1. docs/handoffs/VRES-165-PERSONAL-C1-INDEPENDENT-STATIC-PASS-AND-SCOPED-WINDOWS-PYTEST-2026-10-26.md — original independent Claude STATIC_PASS at old C1 SHA c545556a4ba9ba48f140e7379da960708a7f3c8d, ZERO blocking, seven informational I1..I7, previously authorized one selected Windows offline pytest.
2. docs/handoffs/VRES-165-PERSONAL-C1-WINDOWS-REVIEW-READY-AND-INDEPENDENT-STATIC-GATE-2026-10-26.md — old detached C1 checkout already created, guarded SHA/blob/tree/diff status PASS.
3. docs/handoffs/VRES-165-PERSONAL-C1-STANDALONE-READONLY-CHAIRMAN-PREVIEW-SOURCE-CANDIDATE-2026-10-26.md — original C1 source/test at old SHA; source command remains unchanged.
4. docs/handoffs/VRES-165-PERSONAL-C0-INDEPENDENT-OFFLINE-ACCEPT-PROCEDURAL-ANOMALY-AND-NEXT-PHASE-2026-10-26.md — last independently OFFLINE_ACCEPTED pure C0 preview, 34 individual PASS IDs/exit0. Old PowerShell C0-PROC-01 is separately NONBLOCKING; this new C1 failure is NOT the same incident.
5. Historical A1 R2/A1 R1/B2A/B1/Phase A/F2/P2-A1, R3 denial-only design acceptance/erratum, all V-01..V-42 original roadmap.

The operator MUST NOT rerun the already failed C1 old SHA merely to clear the log. Only a separately reviewed NEW C1 R1 source SHA may be tested once after independently STATIC_PASS and a newly guarded isolated worktree.

## 1. EXACT observed C1 failed Windows terminal excerpt — do not embellish

The user pasted only the END of a previous selected Windows C1 PowerShell attempt, not the full pytest trace or all PASSED/FAILED test IDs. The excerpt includes:

    ValueError: the environment variable is longer than 32767 characters
    PYTEST_EXIT_CODE=1
    PYTHONPATH_RESTORED
    === POST-TEST INTEGRITY ===
    PASS: Post-test C1 HEAD
    PASS: Post-test C1 tree
    POST_RUN_WORKTREE_CLEAN
    C1_TEST_EXECUTION_NONZERO_PRESERVE_EVIDENCE
    VRES_165_C1_PERSONAL_PREVIEW_CLI_OFFLINE_TEST_COMPLETE

The output does NOT include the traceback frames, test-specific FAIL/ERROR list, any collected/pass count, the live AppData fence line, the selected command echo or preflight PASS lines. Those MUST remain UNKNOWN rather than fabricated. The user's previously supplied PowerShell script had been designed to echo exact worktree/command, check source HEAD/tree/blobs, capture LASTEXITCODE immediately, and run the one selected C1 test command; the excerpt does not independently prove every intermediate output/guard passed. An earlier separate C1 source READY transcript DID pass its guarded checkout preflight.

**Authoritative status at old SHA: selected C1 Windows execution failed with exit 1.** Clean postrun Git HEAD/tree/porcelain means no tracked/untracked code changes were detected; it does NOT convert a failed test into PASS or certify physical host/DB/network isolation. The line PYTHONPATH_RESTORED is a literal unconditional Write-Host emitted by the prior wrapper, NOT independent proof of process environment restoration. The excerpt does not show a database contact; that is different from proving none occurred at OS/network level.

The C1 old independent STATIC_PASS remains the historical source-reading verdict at old SHA, but OFFLINE_ACCEPT is **NOT** granted at old SHA.

## 2. Source-grounded root-cause DIAGNOSIS, strong but not proven by unseen traceback

The exact OLD C1 selected test source test_chairman_selection_cli.py included an oversized negative test fixture without an explicit short pytest param ID:

    b"x" * (512 * 1024 + 1),

This is **524,289 ASCII x bytes**. At the author's analysis environment with installed **pytest 9.0.2**, inspection of pytest implementation found:
- _pytest.python.IdMaker._idval_from_value returns the complete ascii-escaped bytes value for supported byte-string parameters, not a bounded short ID. Computing ascii_escaped on the fixture produces an **ID length 524,289 characters**.
- _pytest.runner._update_current_test_var formats a full test node ID with its setup/call/teardown stage and stores it via os.environ["PYTEST_CURRENT_TEST"].
- On Windows, environment-variable values longer than **32,767 characters** are rejected, matching the observed ValueError.

The excerpt lacks traceback frames identifying the precise failing test and pytest internals, so label this a **strong source- and pytest-mechanism-supported diagnosis**, not an independently reproduced Windows traceback. Do not imply that the new fix has already passed Windows.

This is a pytest **test-ID/metadata** problem at old C1 test source, not evidence that the production standalone Chairman CLI changed installed configuration. Do not claim it disproves other possible errors in the same incomplete transcript.

## 3. EXACT new GitHub test-only correction, identities and unchanged scope

**NEW C1 R1 source HEAD** **7ac041018d4ec5a06be07318ecce5e140faccd91**.
**NEW source tree** **0ef7af10335865231f4350e2dbb7ba561538ee00**.
**Direct parent** **c545556a4ba9ba48f140e7379da960708a7f3c8d** = old STATIC_PASS but WINDOW TEST EXIT1, NOT independent C1 OFFLINE_ACCEPT.

Old vs new GitHub tree recursive comparison: **EXACTLY ONE MODIFIED PATH**, ZERO adds/removals:

    tests/test_chairman_selection_cli.py
    old blob 599dccb8dc10487796d71337f80a76f089024dbd
    new blob e69b09cfca0878819096f8a6d211fbec0d7b3de1

**Only line changed in pytest parametrization:**

    OLD: b"x" * (512 * 1024 + 1),
    NEW: pytest.param(b"x" * (512 * 1024 + 1), id="oversized-template"),

The actual oversized byte TEST VALUE and assertion/execution path are unchanged. The new short metadata ID prevents automatically publishing the 524,289-character bytes value as a pytest test name. No test removed, assertion weakened, CLI source modified or security gate bypassed.

**UNCHANGED production/runtime and accepted source paths:**
- C1 standalone CLI src/vres_os/chairman_selection_cli.py blob **6fd0ddcd2b82fca4a48f6a790fee3d0e6ae657d1**.
- Previously independently accepted C0 src/vres_os/chairman_selection_preview.py blob **1fb133e5d1b79bc4d6f6e305f5c9b03f6c752658**.
- Accepted Phase A src/vres_os/chairman_policy.py blob **36e62d6a2712ac305fd4070bac658b94d61d155e**.
- Static Chairman source plugin plugins/vres-os/agents/chairman.md blob **64cba93d6f69960350a0006b594734288f087ccc**.
- Protected tests/conftest.py blob **1c33bb206dbf42691a6af9a709514bf3cc9994af**.
- Pytest config pyproject.toml blob **b2d5e30d10d7be0613e90bf3ed1e346be5678969**, containing pytest pythonpath=["src"].
- Original P2 anchor C:\Projects\Vres-P2F-Postinstall-Hardening-20261022 at HEAD **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c** (clean at prior operator checkout proof).

GitHub new source commit is single parent, unsigned, and feature ref advanced with nonforce expected-old-SHA. GitHub source SHA/tree/blob evidence is independent of the incomplete Windows failure excerpt. **NEW C1 R1 has not run tests and is NOT independently accepted.**

## 4. NEXT user/operator action — NEW guarded detached C1 R1 review workspace, not a pytest rerun

The OLD failed C1 worktree C:\Projects\Vres-ChatGPT-Review-165C1-CLI-20261026 stays **untouched** at the old SHA. Do not reset, stash, pull, edit, rerun pytest, remove, or use it as the new reviewer worktree.

Proposed NEW distinct review directory:

    C:\Projects\Vres-ChatGPT-Review-165C1-R1-20261026

In plain Windows PowerShell, guarded steps:
1. Ensure original clean P2 anchor and official vosser24/Vres-OS HTTPS origin; ensure NEW C1 R1 review destination does NOT already exist.
2. Fetch feature branch ref with --no-tags into existing P2 repo, require EXACT remote **7ac041018d4ec5a06be07318ecce5e140faccd91**; create detached new worktree at that exact SHA, not old C1 directory.
3. Verify HEAD **7ac041018d4ec5a06be07318ecce5e140faccd91**, tree **0ef7af10335865231f4350e2dbb7ba561538ee00**, direct parent FAILED previous C1 **c545556a4ba9ba48f140e7379da960708a7f3c8d**, test blob **e69b09cfca0878819096f8a6d211fbec0d7b3de1**, CLI source blob **6fd0ddcd2b82fca4a48f6a790fee3d0e6ae657d1**, accepted C0/Phase A/template/conftest/pyproject unchanged.
4. Diff net old C1 -> new C1 R1 must be EXACT one "M" path tests/test_chairman_selection_cli.py; git diff --check; detached clean porcelain.
5. Print marker **VRES_165_C1_R1_PYTEST_ID_FIX_REVIEW_READY** and paste full output to ChatGPT. Do NOT run Python, pytest or preview CLI in this first worktree step.
6. ChatGPT will prepare a short independent Claude STATIC-ONLY review of the one-line test-ID fix against previous C1 STATIC_PASS, source SHA/tree/parent, and Windows error mechanism. No Git/Python/pytest/DB calls by Claude. If STATIC_PASS, issue separately bounded one selected offline Windows C1 R1 pytest, preserving all test IDs/exit/fence/postclean, and independent evidence-only verdict afterward. No automatic rerun/retry from old SHA.

**This is a NEW source SHA with a distinct test revision, not repetition of an accepted test.** Do not grant C1 OFFLINE_ACCEPT until real Windows PASS plus independent evaluation at the new SHA.

## 5. Permanent PERSONAL and incident holds

LIVE_SCHEMA_048_INCIDENT=OPEN: **ABSOLUTELY NO PostgreSQL contact, including SELECT.** Previous C1 static reviewer noted protected conftest imports DB modules but stubs psycopg and monitors unexpected contacts. This is only an in-process fence, not native OS isolation. No Vres task state/database bootstrap or health probe despite **VRES_PERSISTENCE_WARNING** and **VRES_REPLY_GUARD_WARNING** task-persistence uncertainty.

The installed Chairman remains last operator-observed Sonnet/high; proposed Opus/medium is UNINSTALLED. Original F1/#165 protected authenticated user consent/history/validator remains OPEN/PARTIAL. No real credentials/vault/keyring, global Claude settings/hooks/plugins changes, model/provider/Fable calls, signing, installer, physical host #169, PR/main merge or product release.

Preserve prior accepted C0 independent OFFLINE_ACCEPT at **e6bd8cb8f92a779da1469efe738709918e9da6df**, 34 Windows individual PASS lines/exit0 with separate NONBLOCKING C0-PROC-01 after-test PowerShell ELSE error; accepted A1 R2 **9754b190083a0ada757ebee07f2ef5b8f312b58e** 93 PASS/exit0; accepted A1 R1 **1b406c788057f0cb2a8a57578b89110a11b76161** 71 PASS/exit0; B2A R3 **32847410952e9d4620bf7046cbee4a41a7ddc73b** 95 PASS/exit0 and historical R3-PROC-01 extra version probe; prior B2A R2 91/92 REJECT/static REJECT; B2B v0/R1/R2 DESIGN_REVISE, R3 DESIGN_ACCEPT only DENY-ONLY with erratum; previous Phase A/B1/F2/P2-A1 exact-SHA outcomes and full original V-01..V-42 roadmap remain unchanged. PERSONAL single-user proportionality remains the product principle, not commercial enterprise IAM bureaucracy.

## 6. Documentation transaction and exact next-session resume

This NEW documentation handoff and a MODIFY to docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md must be the ONLY two changed paths in canonical docs branch over last verified docs HEAD **2b139321d4a5578d876f70c6eac54045cb115812**, tree **7e9fe9a8cc99952a7b45d59c5cacfe5b6ebc880e**. Compare old/new recursive Git trees EXACT two files, no deletions; commit one parent and nonforced expected-SHA update, read back both docs and latest feature refs and changed blob identities. Neither this docs commit nor the one-line test-source commit invokes pytest on user's host, installed Vres, PostgreSQL or provider.

**NEW-SESSION RESUME:** SOURCE HEAD **7ac041018d4ec5a06be07318ecce5e140faccd91**, tree **0ef7af10335865231f4350e2dbb7ba561538ee00**, parent **c545556a4ba9ba48f140e7379da960708a7f3c8d** (= original C1 independent STATIC_PASS but Windows selected pytest EXIT1 with ValueError env variable >32767). New EXACT one modified file tests/test_chairman_selection_cli.py blob **e69b09cfca0878819096f8a6d211fbec0d7b3de1**, just adds pytest.param explicit id "oversized-template" to existing 512KiB+1 bytes negative fixture; C1 production CLI and all prior accepted sources unchanged. Pytest 9 uses bytes as unbounded ID and PYTEST_CURRENT_TEST environment variable, so this is strongly supported root hypothesis but the supplied log lacks full traceback. C1 R1 independent STATIC_NOT_RUN, Windows PYTEST_NOT_RUN, C1 R1 OFFLINE_ACCEPT_NOT_GRANTED. User old C1 worktree unchanged and clean post-test, new proposed C1 R1 directory not yet created. NEXT one guarded NEW detached C1 R1 checkout at C:\Projects\Vres-ChatGPT-Review-165C1-R1-20261026, then focused Claude STATIC-ONLY review, then one separately approved selected pytest and report-only acceptance. Original F1/#165 still OPEN, installed Sonnet/high unchanged, Opus/medium uninstalled, LIVE_SCHEMA_048 no PostgreSQL even SELECT, held K0/PA/D2/F2/R0/L-04 plus credentials/provider/global/installer/main and Vres task persistence caveats unchanged.
