# Vres-OS #165 — B2B-1 A1 R2 personal-use OFFLINE consistency hardening candidate

**Date:** 2026-10-26 (Europe/Athens).
**Repo:** vosser24/Vres-OS.
**Canonical docs branch:** docs/chatgpt-continuity-20261023.
**Source branch:** feature/165-chairman-policy-foundation-20261023.
**Current status:** **A1 R2 SOURCE_CANDIDATE_COMMITTED / AUTHOR_STATIC_PREFLIGHT_ONLY / INDEPENDENT_WINDOWS_STATIC_REVIEW_NOT_RUN / WINDOWS_PYTEST_NOT_RUN / A1 R2 SOURCE_ACCEPT_NOT_GRANTED**.
**Operational purpose:** the user's Vres is a **PERSONAL Windows installation**, not a publicly sold or multi-tenant commercial product. This tranche is proportionate local reliability and consistency work, NOT an attempt to build an enterprise authentication platform. We keep simple fail-closed offline checks and the pre-existing absolute safety holds while avoiding additional installation, provider, IAM, remote signing or bureaucracy.

## 0. Read-first hierarchy and historical status

Read the current docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md first, then THIS handoff, then:
- docs/handoffs/VRES-165-B2B1-A1-R1-INDEPENDENT-OFFLINE-ACCEPT-AND-A1-R2-HARDENING-HANDOFF-2026-10-26.md — **last independent A1 R1 OFFLINE_ACCEPT**.
- docs/handoffs/VRES-165-B2B1-A1-R1-INDEPENDENT-STATIC-PASS-AND-BOUNDED-PYTEST-GATE-2026-10-26.md — previous Claude F1/F2 P3 and F3 P4 reviewer findings, with original limits.
- docs/handoffs/VRES-165-B2B1-A1-R1-WINDOWS-OFFLINE-PYTEST-EXECUTION-PASS-AND-EVALUATION-PENDING-2026-10-26.md — original operator 94-line Windows test transcript: 71 individual PASSED case IDs, exit0, zero unexpected AppData refusals, integration_opt_in=False, clean post-run, no printed collected footer or command echo.
- docs/architecture/VRES-165-B2B-R3-POSTREVIEW-ERRATUM-2026-10-26.md and original immutable docs/architecture/VRES-165-B2B-TRUSTED-CHAIRMAN-AUTHORITY-CONTRACT-R3-2026-10-26.md — R3 independently DESIGN_ACCEPT only for OFFLINE DENY-ONLY; v0/R1/R2 independently DESIGN_REVISE.

**DO NOT reinterpret A1 R1 acceptance as A1 R2 acceptance.** Its exact code and test blobs remain accepted only at their R1 SHA. No extra A1 R1 test rerun, new physical model evidence, PostgreSQL, installer or existing production release action occurred.

## 1. Exact source commit, parent, blobs, changed paths

| Item | Verified GitHub value |
| --- | --- |
| Last independent A1 R1 OFFLINE_ACCEPT / parent | **1b406c788057f0cb2a8a57578b89110a11b76161** |
| Parent tree | 5f1117df2052212185ee51cfc6dae447bed9895f |
| **New A1 R2 source candidate HEAD** | **9754b190083a0ada757ebee07f2ef5b8f312b58e** |
| **New source tree** | **5372c5ecdc7c6ebbb0cbc9956288250255e7db4e** |
| MODIFIED only source | src/vres_os/chairman_b2b_denial_contract.py |
| New source Git blob | **b7c7e9871f669f6420eed8b20e77fe76e44a489f** (Git diff +42/-10) |
| MODIFIED only tests | tests/test_chairman_b2b_denial_contract.py |
| New test Git blob | **8090e8517aedf510cbd76033442540f7113ed0a3** (Git diff +149/-2) |
| Accepted B2A R3 ancestor remains | 32847410952e9d4620bf7046cbee4a41a7ddc73b |
| Protected tests/conftest.py unchanged | 1c33bb206dbf42691a6af9a709514bf3cc9994af |
| pyproject.toml unchanged | b2d5e30d10d7be0613e90bf3ed1e346be5678969 |
| Original B1 policy module unchanged | 36e62d6a2712ac305fd4070bac658b94d61d155e |
| Original B1 proposal history unchanged | e19d913714d3625afaeb91d0fccfcfe43d13d195 |
| Original B2A comparison unchanged | 304e515e0115716f4da3403017de87eabd888a43 |

ChatGPT fetched both exact A1 R1 accepted Git blobs and inspected accepted B1/B2A interfaces, selected tests and pyproject. It staged new unreferenced Git blobs, then constructed a new tree based EXACTLY on R1 tree. A recursive old/new Git tree comparison verified **exactly two MODIFIED files**, no added/deleted paths, with the expected new source/test blob SHAs. GitHub created one single-parent source commit; GitHub commit readback and source branch readback verified exact SHA/tree/parent and changed paths, and the source ref advanced nonforced with an exact expected-old-SHA guard. GitHub unsigned commit is NOT a native trust authority. No PR, merge, main push, installation or provider calls.

## 2. Light-weight personal security changes: no enterprise platform

### 2.1 Reviewer A1-R1-F1 P3 — match claimed canonical prior L, not authentic H

The offline assess_unverified_claims operation now reads/validates a canonical candidate B1 document, requires exactly ONE successor (len(candidate.proposals) == claimed prior count + 1), then for p>=1 constructs a STANDALONE ChairmanPolicyHistory from the first p already accepted B1 proposals and calls its accepted to_document(). It compares the SHA-256 of that prior canonical document and its latest proposal SHA to the *CALLER-SUPPLIED* claimed L identities. It also verifies the new candidate's predecessor digest. A fork with the right count but different earlier history should REFUSE as CLAIM_CONFLICT.

At p=0, count1 and accepted B1 first version1/null predecessor shape are used with typed genesis absence; no zero-entry B1, fake all-zero history SHA, or B2A equality call with p=0. A caller can still forge BOTH a candidate and a matching claimed head; any match remains Indeterminate and is **NOT authentication**. This is strictly practical local consistency, not protected T2-resistant provenance.

### 2.2 Reviewer A1-R1-F2 P3 — G may be older than L, but reference must match

For G.kind=L_ENTRY, check that its sequence refers to an actual proposal within the PRIOR p-entry candidate history and that the SHA at that sequence equals the claimed G.proposal_sha256. G can deliberately refer to an EARLIER entry than latest L (e.g. abandoned or pending proposals). There is NO coercion of last COMPLETED governing installed G to latest proposal L and NO claim of installed/loaded model proof. PRE_HISTORY_BASELINE remains a valid tagged prior state.

### 2.3 Reviewer A1-R1-F3 P4 — simple snapshot hardening, no API redesign

The evaluator now takes exactly one local immutable candidate raw bytes snapshot, validates through B1 and uses the same bytes for the existing domain-separated history-evidence digest. It does not read candidate.raw_b1 twice inside assessment. Refused/Indeterminate and closed reason-code enums/public schema are preserved for backward compatibility. String-mixin reasons and third-party misuse of Indeterminate remain explicitly DOCUMENTED informational risks; no positive boolean, permit, installer/provider path or new authorization API is created. Both result types still raise TypeError on bool(result), matching R1 acceptance.

### 2.4 Negative-test improvements

Nine new distinct test functions, with separate parameterized cases, exercise:
- p>=1 matching canonical prior prefix still always Indeterminate with no positive authority.
- Two real fork variations with equal counts but different first policy or rationale.
- Incorrect old claimed history SHA and latest proposal SHA despite correct linked successor.
- Matching/mismatching G SHA at both earlier and latest prior sequence (two distinct cases).
- Count-zero genesis refusal with a syntactically valid L_ENTRY head reference.
- All-zero *non-genesis* history and latest SHA refusal.
- Invalid types independently substituted into each of the five assessment parameters.
- Low-level mutation of valid candidate B1 bytes AFTER its digest snapshot must REFUSE, never promote trust.
- Denial result reason codes are informational and not a permission signal.
- A previously misleading comment on the matched candidate pair has been clarified.

These tests are **AUTHORED, NOT EXECUTED**. The existing R1 test suite is historical PASS evidence only and cannot be reused to claim R2 PASS. No known privileged imports, positive authority symbols or lines longer than 100 characters were found in the new A1 module in author static text inspection. That inspection is NOT an independent Claude security verdict and NOT a Windows runtime test. The unchanged conftest (1513 lines) remains a process-level isolation fence, not an OS sandbox.

## 3. The user's personal-use security posture and absolute holds

Use practical proportional security for a **single-user personal Vres installation**. Avoid assuming a multi-tenant SaaS threat model, corporate IAM, public signed-release ceremonies or extensive external trust-provider infrastructure are necessary for this OFFLINE tranche. The goal is to catch malformed or accidental inconsistencies and avoid an unverified history silently influencing decisions.

This clarification does NOT waive the ongoing **LIVE_SCHEMA_048_INCIDENT=OPEN** absolute NO PostgreSQL contact (including SELECT), nor permit touching personal real credentials/vaults or global Claude settings, protected Fable, native authorization, model switch/installation, signing, actual release deployment, physical #169 host tests, PR/merge/main or production activation. These are explicit held operations from prior durable handoffs and need separate conscious approval even for personal use. Original F1/#165 remain OPEN/PARTIAL. The later trusted-provider/installer/T2 requirements in the independently reviewed R3 design are a **deferred, optional high-assurance architecture topic**, not a prerequisite to practical OFFLINE personal hardening. If the user later decides to adopt a simpler personal consent/runtime design, it must be separately specified honestly with its limits rather than labeled T2-resistant.

Installed personal Windows release 20261022172833-4d82147b from P2 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c still uses Chairman Sonnet/high. Opus/medium remains candidate-only, UNINSTALLED. Product main last verified 9a8acc5d464b96432a93cb95daa9581412fb07ee. Original V-01..V-42 desired development scope and pending PA-01..08, K0, D2, F2, R0, L-04 remain tracked, not silently discarded. VRES_REPLY_GUARD_WARNING task persistence remains unresolved; this GitHub docs handoff is durable instead of pretending the Vres task state is synchronized.

## 4. NEXT GATE — one fresh simple guarded Windows review, Claude STATIC FIRST

The A1 R1 detached worktree is already independently reviewed and accepted. Do NOT modify, reset, fetch into or rerun it. For this new source SHA the user should create a **new** distinct guarded detached Windows checkout after verifying original clean P2 anchor and official origin; suggest:

    C:\Projects\Vres-ChatGPT-Review-165B2B1-A1-R2-20261026

- From clean original P2 anchor C:\Projects\Vres-P2F-Postinstall-Hardening-20261022 verify HEAD 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c and origin https://github.com/vosser24/Vres-OS.git; STOP on wrong/dirty anchor or existing review destination.
- Fetch the exact intended feature ref and require remote SHA 9754b190083a0ada757ebee07f2ef5b8f312b58e.
- Create NEW detached worktree at that SHA; check tree 5372c5ecdc7c6ebbb0cbc9956288250255e7db4e, immediate accepted R1 parent 1b406c788057f0cb2a8a57578b89110a11b76161, source blob b7c7e9871f669f6420eed8b20e77fe76e44a489f, test blob 8090e8517aedf510cbd76033442540f7113ed0a3. Changed-path diff versus R1 must be exactly two MODIFIED A1 files; git diff --check clean; porcelain including untracked clean. Leave old R1 checkout untouched.
- Next Claude Code is INDEPENDENT static-only reviewer (Read/Glob/Grep, no editing/testing before review) of 2 modified modules, accepted B1/B2A, protected tests/conftest.py isolation and pyproject. Be proportionate to personal scope. Look especially at new slice-based canonical prefix, G earlier semantics, hostile inputs, no privileged import, counterexamples and test assertions. Require STATIC_PASS/REJECT/BLOCKED. No Claude source fix.
- Only after STATIC_PASS and separate user-run approval, ONE bounded CPython 3.12 Windows offline pytest invocation, existing selected command \`py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_b2b_denial_contract.py\`. Preserve actual complete output, exit, fence, pre/post clean; no added Python version probe (historic R3-PROC-01), retries or DB. A newly run result does not retrospectively alter accepted R1.
- If REJECT, the user preserves evidence and ChatGPT repairs in a NEW source SHA; no reruns of identical rejected tree just to make output green.
- Separate docs-only handoff after independent source review/test each substantive step; do not invent a verdict.

## 5. Immutable history and next-session resume

Historical B2B v0/R1/R2 designs independently DESIGN_REVISE, immutable R3 design independent DESIGN_ACCEPT only OFFLINE DENY-ONLY + normative R3 erratum; original A1 first commit 68adbb121997646677b3b9bd17a391534e5818c8 untested; A1 R1 1b406c788057f0cb2a8a57578b89110a11b76161 independent STATIC_PASS and OFFLINE_ACCEPT (71 individually reported PASSED lines, exit0, zero unexpected refusals, incomplete footer/command echo, operator identity limitations) and reviewer F1/F2 P3, F3 P4. This new R2 candidate is NOT independently accepted and has NO observed Windows test output.

Prior B2A R3 32847410952e9d4620bf7046cbee4a41a7ddc73b independently 95 PASSED lines/exit0 and R3-PROC-01 extra interpreter-version probe; B2A R2 source 060756b02786c146b87a5262ba2b3b2cc6bf2784 91/92 REJECT; original B2A static REJECT; Phase A R2 53/53, B1 99/99, F2 101/101 plus 3/3, P2-A1 guard R4 183/183 offline PASS only at exact original SHAs, all older REJECTs remain historical.

**NEXT-SESSION RESUME:** Read canonical docs index and THIS A1 R2 personal offline source candidate handoff. Feature branch source SHA **9754b190083a0ada757ebee07f2ef5b8f312b58e**, tree **5372c5ecdc7c6ebbb0cbc9956288250255e7db4e**, parent last independently OFFLINE_ACCEPT A1 R1 **1b406c788057f0cb2a8a57578b89110a11b76161**; ONLY 2 modified A1 files, source blob b7c7e9871f669f6420eed8b20e77fe76e44a489f and tests blob 8090e8517aedf510cbd76033442540f7113ed0a3. Fixed unverified canonical prior prefix and old G entry consistency, single candidate bytes snapshot, targeted tests; still DENY-ONLY and no trusted authority. ChatGPT AUTHOR static preflight only; Windows source/tests and independent Claude NOT_RUN. NEXT guarded distinct Windows checkout then Claude static-first source review and single explicit bounded offline pytest if safe. Personal-use proportional security, NOT enterprise published-product ceremony. Original program F1/#165 OPEN, installed Sonnet/high and Opus/medium candidate only; LIVE_SCHEMA_048_INCIDENT no PostgreSQL contact even SELECT and all other held operations remain untouched. Preserve V-01..V-42 and old exact-SHA verdicts, task-persistence warning, docs-only continuity commits.
