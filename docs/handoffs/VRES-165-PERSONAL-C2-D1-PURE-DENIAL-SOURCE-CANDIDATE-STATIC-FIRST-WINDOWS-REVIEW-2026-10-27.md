# Vres-OS #165 — PERSONAL C2-D1 PURE OFFLINE DENIAL/DIAGNOSTIC source candidate committed; independent STATIC review NEXT

**Date:** 2026-10-27, Europe/Athens.
**Repository:** vosser24/Vres-OS.
**Feature branch:** feature/165-chairman-policy-foundation-20261023.
**Canonical documentation branch:** docs/chatgpt-continuity-20261023.
**CURRENT PRECISE STATE:** C2_D1_SOURCE_CANDIDATE_COMMITTED / AUTHOR_ONLY_STATIC_PREFLIGHT_COMPLETED / INDEPENDENT_CLAUDE_STATIC_REVIEW_NOT_RUN / WINDOWS_SELECTED_PYTEST_NOT_RUN / INDEPENDENT_OFFLINE_ACCEPT_NOT_RUN / NO_AUTHORITY_ISSUED / NO_MODEL_ACTIVATION.
**NOT a source acceptance, not a completed #165, and not a personal installed runtime change.**
**Product scope:** single-user PERSONAL Windows Vres, no enterprise compliance bureaucracy.

## 0. Read-first precedence and reviewed architecture approval

Start with docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md at the NEWEST verified canonical docs HEAD, then THIS C2-D1 author/source checkpoint. Preserve immutable older handoffs:
1. docs/handoffs/VRES-165-PERSONAL-C2-V1-R1-INDEPENDENT-DESIGN-ACCEPT-AND-PURE-D1-NEXT-2026-10-27.md — independent Claude **DESIGN_ACCEPT strictly to the corrected C2 V1 concept**, ZERO blocking, seven informational constraints I-01..I-07, detailed next D1 scope. Design approval is NOT Python code acceptance.
2. docs/architecture/VRES-165-PERSONAL-C2-REVERSIBLE-CHAIRMAN-MODEL-CHANGE-DESIGN-V1-2026-10-26.md — immutable reviewed corrected V1 blob **407e36528c5cda925517ae0a9db6ba826069aac9**.
3. docs/handoffs/VRES-165-PERSONAL-C2-V1-R1-WINDOWS-DOCS-REVIEW-READY-AND-INDEPENDENT-DESIGN-GATE-2026-10-27.md — operator detached Windows docs review READY, two diff --check PASS, V1 independent design review followed later.
4. docs/handoffs/VRES-165-PERSONAL-C2-D0-V0-INDEPENDENT-DESIGN-REVISE-AND-V1-REPAIR-2026-10-26.md — original v0 DESIGN_REVISE B-01 plus D1..D7, before V1 fixed the design. Original V1 one-byte trailing space STOP also retained at its own SHA.
5. docs/architecture/VRES-165-B2B-TRUSTED-CHAIRMAN-AUTHORITY-CONTRACT-R3-2026-10-26.md and docs/architecture/VRES-165-B2B-R3-POSTREVIEW-ERRATUM-2026-10-26.md — R3 DESIGN_ACCEPT strictly pure DENY-ONLY B2B-1 and outstanding real positive F1 protected consent, anchor, W, loader, publisher and validator STOPs.
6. docs/handoffs/VRES-165-PERSONAL-C2-INSTALLED-CHAIRMAN-MANAGED-RELEASE-BYTES-READONLY-PASS-AND-REVERSIBLE-C2-DESIGN-NEXT-2026-10-26.md — original installed Windows current-user P2 agent observed Sonnet/high; no active model measurement.
7. docs/handoffs/VRES-165-PERSONAL-C1-R1-INDEPENDENT-OFFLINE-ACCEPT-AND-READONLY-MANUAL-PREVIEW-NEXT-2026-10-26.md — accepted C1 R1 source-only read-only preview/trusted test evidence.

C2-D1 is an independent NEW source boundary. Do NOT inherit the earlier C1 R1 OFFLINE_ACCEPT test verdict. C2 V1 DESIGN_ACCEPT permits considering this narrow pure source implementation, not installed authority.

## 1. Exact committed SOURCE SHA, tree, parent and file allowlist

| Bound | Exact SHA/path |
| --- | --- |
| **CURRENT FEATURE C2-D1 candidate HEAD** | **358b3554075f87f5b8287fbb37d66fa95ad68b7c** |
| Feature Git tree | **af1d7349f1e7028145567b6330a5b25bdc0f5920** |
| Single direct parent, accepted C1 R1 | **7ac041018d4ec5a06be07318ecce5e140faccd91** |
| Parent C1 R1 tree | **0ef7af10335865231f4350e2dbb7ba561538ee00** |
| **ONLY ADD: new D1 planner module** | src/vres_os/chairman_c2_offline_planner.py blob **9cde474f7f9a5450c9faf7cbcbe4a608d317c1fd** (~240 numbered lines plus terminal empty line) |
| **ONLY ADD: new focused D1 negative tests** | tests/test_chairman_c2_offline_planner.py blob **975ed8f4a5a38c307be48a99f401c1edcbeba67f** (~317 numbered lines plus terminal empty line) |
| **Untouched Phase A policy/materializer** | src/vres_os/chairman_policy.py blob **36e62d6a2712ac305fd4070bac658b94d61d155e** |
| **Untouched accepted C0 pure preview** | src/vres_os/chairman_selection_preview.py blob **1fb133e5d1b79bc4d6f6e305f5c9b03f6c752658** |
| **Untouched accepted C1 standalone CLI** | src/vres_os/chairman_selection_cli.py blob **6fd0ddcd2b82fca4a48f6a790fee3d0e6ae657d1** |
| **Untouched accepted B2B-1 pure deny-only** | src/vres_os/chairman_b2b_denial_contract.py blob **b7c7e9871f669f6420eed8b20e77fe76e44a489f** |
| **Untouched source agent body** | plugins/vres-os/agents/chairman.md blob **64cba93d6f69960350a0006b594734288f087ccc** |
| **Untouched protected conftest** | tests/conftest.py blob **1c33bb206dbf42691a6af9a709514bf3cc9994af** |
| **Untouched pytest config** | pyproject.toml blob **b2d5e30d10d7be0613e90bf3ed1e346be5678969** |

The GitHub feature commit has EXACTLY two ADDED files above, no modifies/deletes; feature ref advanced non-force with expected-old HEAD. ChatGPT independently fetched new commit SHA/parent/tree, both file blobs, recursive parent/new source tree allowlist, and exact unchanged support file blobs. No PR, main merge, installer, package, model or global Claude change.

## 2. Implemented CURRENT pure D1 boundary — conceptual source audit, no execution

**Public module exports at exact candidate SHA:** ClaimedDigestPurpose, ClaimedReviewLabel, DenialOnlyResult, DiagnosticOnlyDigests, Indeterminate, PlannerCode, Refused, UnverifiedDigest, UnverifiedReviewClaims, plan_chairman_c2_diagnostic.

Inputs:
- EXACT bytes template, bounded to >0 and <=512KiB, caller supplied.
- EXACT bounded canonical ChairmanPolicy.to_document() bytes for caller-reported baseline and caller-proposed policy, maximum 4096 bytes each; strict canonical round trip via accepted Phase A ChairmanPolicy.from_document and to_document.
- Explicit frozen/slotted UNVERIFIED review labels for body, source tests, publisher. Allowed claimed labels NOT_ASSERTED or CLAIMED_REVIEWED. These labels NEVER attest real review or provider provenance.
- Optional typed caller-supplied digest with explicit purpose SUPPLIED_TEMPLATE, RENDERED_CANDIDATE or RELEASE; wrong purpose rejected, correct-looking digest remains untrusted.

Operations:
- Reconstruct immutable untrusted claim snapshots, validate types and canonical policy docs without exposing user text or hidden defaults.
- Reuse accepted Phase A materialize_chairman and verify supplied template exactly matches caller baseline's rendered bytes; if not, closed neutral refusal.
- Derive candidate only in memory using accepted byte-exact Phase A renderer; preserve original supplied body and uniform LF/CRLF newline bytes; SHA-256 of actual supplied template and actual rendered candidate as diagnostic-only content IDs.
- Refuse known Sonnet-default/Opus-never-default-shell BODY contradiction when proposed requested family is Opus. This is conservative recognition of known unsafe wording, NEVER a certification that other doctrine/body/test surfaces are safe. Synthetic fixtures only; the tests do not touch actual installed P2.
- Exact closed neutral Refused codes: MALFORMED_INPUT, CLAIM_CONFLICT, DIGEST_DOMAIN_CONFLICT, DOCTRINE_CONFLICT. Indeterminate has ONE intentionally neutral INDEPENDENT_AUTHORITY_UNAVAILABLE code: DO NOT treat it as asserting all other checks passed or publisher as the only missing requirement. Both result variants are frozen/slotted and bool() raises TypeError.
- DiagnosticOnlyDigests exposes literal labels DIAGNOSTIC_ONLY, NOT_INSTALLED, NOT_AUTHORIZED, and bool() likewise raises TypeError.
- Even when all caller claims read CLAIMED_REVIEWED and the claimed digest equals actual supplied bytes, return Indeterminate when otherwise well formed. A publisher-reviewed claim is NOT independent publisher proof. No permit token, approve, installed, can_install, positive status, callback, state persistence, release manifest or install writer API.

Static allowlist: source imports Python stdlib hashlib/re/dataclasses/enum plus previously accepted .chairman_policy exclusively. No os, sys, pathlib, subprocess, socket, ctypes, psycopg, keyring, I/O, open/connect/install/activate functions, current-user installed path, database, credential, provider/Fable, file or process or clock access. ChatGPT checked exact source text for prohibited import/function patterns and both files for >=101 character lines and trailing whitespace before commit. **This author static preflight IS NOT an independent reviewer STATIC_PASS and does NOT prove runtime safety.**

## 3. New focused negative tests — EXPECTATIONS, NOT observed results

The new test module covers:
- Correct-looking neutral fixture still Indeterminate and explicit NOT_INSTALLED/NOT_AUTHORIZED labels; computed SHA agrees with accepted Phase A.
- Entirely untrusted CLAIMED_REVIEWED descriptors in body/tests/publisher, including matching caller-supplied SHA, yield the same Indeterminate.
- Sonnet policy no-op and Opus candidate both never positive, bool() fails, result cannot equal True, no can_install/checks_passed.
- Uniform LF and CRLF template preservation, no source body manipulation and exact candidate diagnostics.
- Malformed/empty/mixed-newline/non-UTF8/wrong-role/oversize template refusal; >512KiB fixture deliberately has short pytest ID **oversized-template** to avoid previous C1 Windows 32767-character environment-variable bug.
- Malformed/noncanonical/duplicate-key/unsupported family, giant/deep JSON and corrupt policy bytes refuse.
- Invalid/corrupted low-level frozen review labels and claimed digest types refuse rather than authorizing.
- Wrong digest purpose (candidate or release given as source template) yields DIGEST_DOMAIN_CONFLICT even with matching SHA.
- Incorrect typed caller template digest neutral refusal.
- Synthetic known P2 Sonnet control-plane body and Opus never-default-shell cases yield DOCTRINE_CONFLICT, including uppercase variants; claims of reviewed cannot override.
- Unchanged Sonnet policy remains indeterminate even if original body says Sonnet; does NOT measure actual running Claude.
- Frozen result data, closed enum, no permit/import/side-effect/export symbols.

**NO test run performed**. Do not invent passed/collected counts, test duration, protected fence outputs or OS/network attestation. Actual new Windows selected pytest is a FUTURE conditional gate after independent STATIC_PASS only.

## 4. Next exact operator Windows source-checkout and independent static-first review

**NEXT action:** one guarded Windows Git detached source-review worktree from the ORIGINAL clean P2 anchor:

    C:\Projects\Vres-P2F-Postinstall-Hardening-20261022

Expected P2 HEAD **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c**, official HTTPS origin, clean. Suggested NEW destination (MUST NOT preexist):

    C:\Projects\Vres-ChatGPT-Review-165C2-D1-20261027

Fetch only feature/165-chairman-policy-foundation-20261023, verify remote expected HEAD **358b3554075f87f5b8287fbb37d66fa95ad68b7c**; create new detached worktree there; guard head/tree/parent/clean exactly. Verify diff from parent ONLY the two ADD files; git diff --check and exact both new and old immutable accepted Phase A/C0/C1/B2B/plugin/conftest/pyproject Git file blob SHAs. No source edits, no tests, no installed file reads, no Vres CLI, no PostgreSQL even SELECT. Final READY marker, only if ALL guards pass:

    VRES_165_C2_D1_WINDOWS_SOURCE_REVIEW_READY

Once user pastes complete READY output, launch one NEW Claude Code session in that exact fresh worktree, **STATIC REVIEW FIRST** using Read/Glob/Grep only, no Bash/Python/pytest/MCP/provider/DB, reviewing both new files IN FULL plus accepted Phase A source, B2B denial API, selected config/test fixture and immutability. Return STATIC_PASS / STATIC_REJECT / EVIDENCE_BLOCKED with precise lines/limits and marker:

    VRES_165_C2_D1_INDEPENDENT_STATIC_REVIEW_COMPLETE

**Only if STATIC_PASS**, later separately issue ONE specifically selected Windows CPython 3.12 offline pytest command with process PYTHONPATH pinned to new D1 source/src; recommended future command, NOT TO EXECUTE AT CURRENT GATE:

    py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_c2_offline_planner.py

Require complete user PowerShell stdout/exit code, individually printed PASSED IDs (not a guessed footer), process fixture AppData unexpected refusals0/integration_opt_in false when observed, restored PYTHONPATH equality, post-run exact HEAD/tree and clean Git. Review and independently accept/reject at exact SHA after actual test output. Do not run additional Python version checks (historical R3-PROC-01) or old broad test suite. Never infer OS-level/physical PostgreSQL no-contact from in-process conftest.

If static reviewer finds blocking or operator test fails, STOP at that SHA, preserve failure, author bounded NEW SOURCE SHA correction with exact allowlist and fresh review; no amended or forced ref, no retroactive acceptance.

## 5. User-visible product and trust controls

Current installed original P2 current-user Vres release **20261022172833-4d82147b** remains last read-only observed Sonnet/high, UTF-8 LF/24208 bytes and SHA-256 a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73. Not independently measured from running Claude. Proposed Opus/medium is UNINSTALLED. Original P2 fixed-doctrine frontmatter-only proposed Opus candidate digest **b73e7497454a464f6b6bc1df00f42422696da786a07eb2936ae73ad73abedf54** remains **DIAGNOSTIC_ONLY_INVALID_FOR_INSTALLATION**. Future coordinated policy-aware agent BODY and test-pin review (D1B), new genuine pinned policy-bound immutable plugin release (D3) and independent F1 trust/consent/protected validator/loader and physical host (#169) are SEPARATE and NOT performed or approved in D1.

**LIVE_SCHEMA_048_INCIDENT=OPEN: ABSOLUTE NO PostgreSQL contact, even SELECT.** No Vres task/doctor/bootstrap/setup/probes despite VRES_PERSISTENCE_WARNING or VRES_REPLY_GUARD_WARNING. D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 blocked, L-04 OPEN, PA-01..PA-08 incomplete. #165 F1 external trusted publisher/genesis H0/Hn/E/V/CAS/W/loader and #169 physical model verification OPEN. No credentials/vault/keyring, protected Fable/provider, signing, native installer, global Claude/skill/config modifications, PR/main merge, installed active model change or automatic promotion/demotion.

Older accepted per-SHA: C1 R1 **7ac041...** independent STATIC_PASS/OFFLINE_ACCEPT after 29 individually printed Windows pytest PASS/exit0 and manual read-only source preview; prior old C1 **c545556...** Windows pytest EXIT1 NOT accepted. C0 **e6bd8cb...** accepted 34 PASS/exit0 with late PowerShell C0-PROC-01 nonblocking. A1 R2 **9754b190...** 93 PASS, A1 R1 **1b406c78...** 71 PASS, B2A R3 **32847410...** 95 PASS and R3-PROC-01; previous B2A R2 REJECT and B2B v0/R1/R2 DESIGN_REVISE, B2B R3 accepted strictly DENY-ONLY, Phase A/B1/F2/P2-A1 per-SHA verdicts preserved. Original personal V-01..V-42 roadmap remains full and not claimed production complete.

## 6. Docs-only seal and new-chat resume

This NEW source candidate has already advanced FEATURE branch; subsequent docs transaction must **ADD this checkpoint Markdown** and **MODIFY docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md only** on canonical docs branch, atop prior verified docs HEAD **1b7eedaa201f9b912d6075724720806c86c73320**, tree **b2d86527b75a0bc6e6831c3777d5fe9d5f61f3af**. Compare recursive docs old/new tree: exactly two docs paths and no deletes, one-parent commit, expected-old-head NONFORCED advance, exact blob/commit/tree/branch readback and feature HEAD unchanged **358b3554075f87f5b8287fbb37d66fa95ad68b7c**. No other source or installed changes, no test execution.

**NEW CHATGPT SESSION RESUME:** from newest canonical docs index. Feature HEAD **358b3554075f87f5b8287fbb37d66fa95ad68b7c**, Git tree **af1d7349f1e7028145567b6330a5b25bdc0f5920**, parent accepted C1 R1 **7ac041018d4ec5a06be07318ecce5e140faccd91**; EXACTLY 2 ADD paths new C2-D1 pure module blob **9cde474f7f9a5450c9faf7cbcbe4a608d317c1fd**, new focused tests blob **975ed8f4a5a38c307be48a99f401c1edcbeba67f**, old C1 PhaseA/C0/B2B/plugin/conftest/pyproject untouched. Author GitHub SHA/tree/blob/allowlist static check only; independent STATIC NOT_RUN, Windows selected pytest NOT_RUN, independent OFFLINE_ACCEPT NOT_RUN, no C2-D1 installation/positive authority. Current user requested "PROCEED" for these two narrow source files and source commit was created. This proceeds from independently accepted C2 V1 design blob 407e36528c5cda925517ae0a9db6ba826069aac9, Claude DESIGN_ACCEPT with 7 informational I-01..I-07, not source acceptance. Code inputs only caller bytes + UNVERIFIED labels and typed optional digest, reuses immutable PhaseA materializer and ensures content SHA diagnostics only, recognized P2 doctrine refusal, returns only closed Refused/Indeterminate and raises on bool; no imports/op for FS/DB/provider/install. **NEXT operator guarded detached D1 source-review folder C:\Projects\Vres-ChatGPT-Review-165C2-D1-20261027** anchored at original clean P2 source worktree, exact feature HEAD/tree/parent, two ADD and protected original blobs, diff --check, new detached clean; only afterward independent Claude STATIC review, then ONE offline selected pytest if STATIC_PASS. Preserve original F1/#165, LIVE_SCHEMA_048 zero PostgreSQL even SELECT, current installed Sonnet/high, proposed Opus UNINSTALLED, all review/process failures, history and V-01..V-42.
