# Vres-OS #165 — B2A R3 independent Windows OFFLINE ACCEPT

**Evidence date:** 2026-10-23, Europe/Athens.
**Repo:** vosser24/Vres-OS.
**Canonical documentation branch:** docs/chatgpt-continuity-20261023.
**Source branch:** feature/165-chairman-policy-foundation-20261023.
**Disposition:** **ACCEPT for exact B2A R3 offline comparator and tests ONLY.**
This is not an authenticated user-event approval, an installed Chairman policy, a host physical-model result, production readiness or approval to access held systems.

## 0. Exact identity and distinct historical outcomes

| Boundary | Full source SHA | Independent evidence |
| --- | --- | --- |
| **B2A R3 currently accepted** | **32847410952e9d4620bf7046cbee4a41a7ddc73b** | Windows Claude ACCEPT; 95 PASS lines; pytest exit 0 |
| Immediate parent R2 | 060756b02786c146b87a5262ba2b3b2cc6bf2784 | **REJECT**; 92 collected, 91 PASS, 1 FAIL, exit 1 |
| Initial B2A | c01152e374c4e7e0ae8e0a01eab5148cdf71e84e | **STATIC_REVIEW_REJECT**, pytest NOT_RUN |
| F2 test-only boundary | 36a41b6151b7520329ccc0ada0ff827d836ec579 | ACCEPT; 3 selected/3 PASS |
| F2 Unicode writer/reader code | b77e0eef07976877e7f198a00484f5d13ce36889 | ACCEPT; 101/101 selected PASS |
| Initial B1 candidate proposal history | f8237bb301dec160f33cab524727e6a0ec79b2c0 | ACCEPT; 99/99 selected PASS |
| Phase A R2 | 11f2f8689308dfe43e482bca73aa57bb6467c788 | ACCEPT; 53/53 Windows CRLF PASS |
| P2-A1 R4 guarded DB target | 3ba41d5ae6b8f2c2abd93d27f82cce0755878237 | ACCEPT offline; 183/183 selected PASS |

Earlier Phase A R1 and P2-A1 guard R1–R3 independent rejections remain valid, not superseded as historical observations.

**Current source commit:** 32847410952e9d4620bf7046cbee4a41a7ddc73b, immediate parent 060756b02786c146b87a5262ba2b3b2cc6bf2784, tree e7e39a50a3528f329d1cd27d1c23a1cbb279e697. Difference from R2 is exactly ONE modified test path: tests/test_chairman_history_expectation.py. Current production comparator blob src/vres_os/chairman_history_expectation.py remains **304e515e0115716f4da3403017de87eabd888a43**; unchanged from R2. GitHub feature ref at this same exact full SHA was independently read back on this turn. No R3 source write is performed by sealing acceptance.

## 1. Independent reviewer report as provided by operator

Complete Claude report ended with marker **VRES_165_B2A_R3_INDEPENDENT_EVALUATION_COMPLETE** and final verdict **ACCEPT**, explicitly restricted to R3 offline source and tests.

Operator's guarded Windows review worktree: C:\Projects\Vres-ChatGPT-Review-165B2A-R3-20261023, detached at exact R3 HEAD, immediate parent matched, git diff --check exited 0, clean tracked/untracked status before and after test run, production comparator blob identical before/after. The Git identity was independently checked by evaluator. Remote: vosser24/Vres-OS.

**ONE authorized pytest invocation** (reviewer says run once):

    py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_history_expectation.py tests/test_chairman_policy_history.py

Run from exact detached R3 worktree on Windows CPython 3.12.10 64-bit; **exit 0**. Claude counted **95 PASSED lines**, 0 failed, 0 error, 0 skipped, 0 XFAIL or XPASS. The usual total printed by pytest was suppressed due to project addopts "-q" combined with command "-q" (double quiet); **"95 collected" is INFERRED from the lines, not observed as a collection footer**, and deselected count was not printed. No -k/-m selection was used. DO NOT fabricate an observed collection/deselection count. No broad repository/DB/host suite was run.

All FOUR independent R3 parametrized canonical negative cases had separate reported PASSED IDs:
- key-order: canonical top-level starts proposals, altered starts schema; altered bytes differ, comparator refuses "not canonical".
- literal-unicode: the Greek rationale has literal non-ASCII UTF-8 in alternate document rather than ASCII JSON escapes; comparator refuses "not canonical".
- trailing-newline: parses as JSON with whitespace but is noncanonical; comparator refuses "not canonical".
- bom: parser refuses UTF-8 BOM and comparator exposes "Invalid candidate", before canonical byte comparison.

The parent R2 independent REJECT was caused by a fake key-order variant that reproduced canonical bytes and masked three cases in one loop. R3 corrects only tests, splits them and pins expected refusal strings. This is a **new distinct ACCEPT**, never a retroactive reinterpretation of R2.

## 2. Windows isolation and one procedural exception

The evaluator inspected tests/conftest.py all 1513 lines before testing, both selected test modules, accepted history APIs and pyproject.toml. It reported disposable per-session and per-test VRES_DATA_DIR, protected real LocalAppData/AppData VresOS paths, platformdirs/audit-hook fences, scrubbing of DB and PG env values, psycopg/Vres-driver connection tripwires, private DB-target registry, no unreviewed subprocess allowance for selected test sites, and pythonpath=["src"]. Fence summary: unexpected refusals=0, integration_opt_in=False. No refusal, connection-tripwire failure, worktree change or evidence of Vres initialization. Imported source path was **inferred from pyproject.toml**, not directly runtime-probed. This is not a live credential, PostgreSQL, installed-model or host-evidence verification.

**Procedural exception (must never be omitted):** the evaluator also invoked \`py -3.12 -c "import sys;print(sys.version)"\` before the authorized pytest within the same shell command to identify Python 3.12.10. It imported only Python sys and reportedly accessed no network/files/provider. Nonetheless this was ONE EXTRA Python invocation beyond the strict one-test-command instruction. The independent evaluator disclosed it, and the offline source verdict is ACCEPT; record the process deviation separately as **R3-PROC-01**, rather than silently ignoring it or inventing a second pytest. Future Claude prompts must explicitly forbid even benign extra interpreter/diagnostic calls unless independently authorized. No repeated test is justified solely by this benign version-print step.

Reviewer informational observations: pytest.raises match strings use re.search substrings rather than anchored full-message equality, sufficient to distinguish noncanonical checks versus parser BOM. Literal-unicode case relies on the known non-ASCII rationale and assertion altered!=canonical. Neither was blocking.

## 3. What was accepted, and what remains entirely OPEN

Accepted only the **pure, non-authenticating** B2A expected-history comparator and its offline regression tests. It compares canonical candidate-history bytes to caller-SUPPLIED expected proposal count/history SHA-256/latest proposal SHA-256, refusing mismatch or malformed history. It returns None on equality; no approval flag, token, actor identity or installed policy is produced. An adversary that controls both a forged history and the matching expected triple can still obtain equality.

**F1 trusted external authority remains OPEN:** an independently authenticated operator-event record must supply the expected identity and protected validation must bind the exact history/policy, purpose, installation target and authorization decision. Do not infer consent from hash-only equality, free-text rationale, untrusted manifest or local assertion. A future approval/installer adapter MUST distinguish trusted provenance, immutable external head, replay/fork/rollback resistance and no-silent-downgrade behavior; this is NEW future work, not claimed accomplished by B2A R3.

#165 remains OPEN/PARTIAL. Requested Opus/medium is an in-memory candidate only; installed Chairman remains Sonnet/high. No launch of Claude as the new Chairman, no host-observed model generation, no telemetry trust or protected worker/validator pin change. No PR/merge/main push, installer, signing or release update.

## 4. Preserved program and database STOP boundaries

**LIVE_SCHEMA_048_INCIDENT=OPEN**; PostgreSQL service last reported STOPPED. No PostgreSQL contact, not even SELECT or a health probe; no migration/startup/Vres selftest/bootstrap/setup. D2 OPEN; F2 quarantined; R0_NOT_RUN; K0-T1 BLOCKED; native trust not approved; L-04 OPEN; positive production trust issuance disabled; PA-01..PA-08 incomplete. No real credentials/Windows Credential Locker, global Claude config/hooks/plugin mutation, live provider calls, installer activation, PR/merge, native signing or positive trust issuance without distinct user authority.

Installed Windows personal Vres release: 20261022172833-4d82147b from original P2 source 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c; no new installation and model still Sonnet/high. Product main last independently verified 9a8acc5d464b96432a93cb95daa9581412fb07ee. Full V-01..V-42 product-development backlog remains active and NOT runtime activated. Retain P2-A1 R4 risks and Phase A informational findings.

## 5. B2B next architecture gate (design-first, no live or fake authority)

The next bounded work should specify an **independently trusted provenance contract** for Chairman history/approval that never treats a caller-provided expected SHA as trustworthy on its own. Before code that asserts authority exists, define:
- Source of operator identity and authenticated, consent-bearing user event, versus text merely appearing in a chat or rationale.
- Independent immutable/pinned head, count, canonical history SHA and latest proposal SHA; replay, race, fork, truncation and rollback refusal semantics.
- Protected Fable validation evidence tied to the exact source/policy/history and a validation outcome, distinct from user approval.
- Explicit separation of proposed, evaluated, authorized, installed and host-observed physical-model states; no telemetry-driven auto-promotion/demotion.
- Signature/key/vault/provider boundaries: no unapproved live Windows secret access, no key creation, no signing or production trust issuance; design can be offline/abstract only.
- Failure handling: absence/staleness/conflicting anchors or missing protected evidence MUST fail closed, no silent model fallback.
- A future versioned installer manifest/rollback contract, with exact release/template/policy hashes and source provenance, also deferred.
- Limited, isolated offline tests under conftest fences; separately approved physical #169 host observations after all safety gates.

Do not mark F1 CLOSED until the trusted external anchor and protected authority adapter are designed, independently validated and explicitly authorized; B2A only supplies a reusable equality primitive.

## 6. New session resume prompt

RESUME Vres-OS from current GitHub HEAD of docs/chatgpt-continuity-20261023. Read docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md, then THIS B2A R3 OFFLINE ACCEPT handoff, then R3 worktree readiness / R2 REJECT and original B2A STATIC_REVIEW_REJECT. Current source branch feature/165-chairman-policy-foundation-20261023 at exact 32847410952e9d4620bf7046cbee4a41a7ddc73b, parent independently R2 REJECT 060756b02786c146b87a5262ba2b3b2cc6bf2784, one modified test file only and production comparator unchanged. Claude independent ACCEPT R3, Windows Python 3.12.10, 95 PASSED lines, exit 0, 4 separate canonical tests PASS, no observed DB contact/worktree mutation. Actual collection total NOT printed; reviewer inferred 95. One extra \`py -3.12 -c\` sys.version invocation (R3-PROC-01) occurred before pytest; preserve as process deviation. R2 historical REJECT 92 collected/91 PASS/1 FAIL, original B2A static REJECT; earlier F2 3/3 +101/101, B1 99/99, Phase A R2 53/53 and P2-A1 guard R4 183/183 ACCEPT intact. Next: design the true B2B trusted external provenance/operator-event/protected-validation contract OFFLINE without claiming activation, before any coding/installation of authority. F1 still OPEN, #165 OPEN/PARTIAL, installed Chairman Sonnet/high, schema-048 PostgreSQL NO CONTACT, vault/K0/PA/signing/credential/global-Claude restrictions and 42-item backlog retained. ChatGPT owns development/Git docs, Claude independent reviewer, user operates bounded Windows tests. After each substantive response, publish detailed docs-only handoff/index with verified SHA.
