# Vres-OS #165 — B2B-1 A1 R1 test-expectation correction and exact Windows review boundary

**Date:** 2026-10-26, Europe/Athens.
**Source branch:** feature/165-chairman-policy-foundation-20261023.
**Documentation branch:** docs/chatgpt-continuity-20261023.
**Status:** **A1 R1 SOURCE CORRECTION COMMITTED / INDEPENDENT WINDOWS STATIC REVIEW NOT_RUN / PYTEST NOT_RUN / A1 NOT ACCEPTED**.
**Roles:** ChatGPT authors/commits; user operates guarded Windows PowerShell; Claude Code independently reviews/tests only the statically approved bounded selection, never implements.

## 0. Read-first and precedence

Read this NEW correction handoff, then [original complete A1 source and review handoff](VRES-165-B2B-1-A1-SOURCE-CANDIDATE-AND-WINDOWS-REVIEW-HANDOFF-2026-10-26.md), [independent R3 deny-only design acceptance](VRES-165-B2B-R3-INDEPENDENT-ACCEPT-AND-FULL-RESUME-2026-10-26.md), [mandatory R3 erratum](../architecture/VRES-165-B2B-R3-POSTREVIEW-ERRATUM-2026-10-26.md), and [immutable reviewed R3 architecture](../architecture/VRES-165-B2B-TRUSTED-CHAIRMAN-AUTHORITY-CONTRACT-R3-2026-10-26.md).

This handoff **supersedes ONLY the source checkout SHA/blobs for the next A1 Windows independent reviewer**. It does not rewrite the initial Git source commit or the previous published documentation: both are historical and **TESTS_NOT_RUN**, not ACCEPT/REJECT. R3 independent DESIGN_ACCEPT applies only to inert OFFLINE DENY-ONLY design. v0/R1/R2 B2B designs independently DESIGN_REVISE. Reviewer corrections R3-N03/N04/N05/N08/N09 and deferred security holds R3-N01/N02/N06/N07, NF-05..NF-10 remain unchanged.

## 1. Exact source commit and blob ledger

| Boundary | SHA | Status |
| --- | --- | --- |
| Accepted B2A R3 base | 32847410952e9d4620bf7046cbee4a41a7ddc73b, tree e7e39a50a3528f329d1cd27d1c23a1cbb279e697 | independent Windows 95 PASSED lines, exit 0; R3-PROC-01 extra version probe |
| First ChatGPT A1 candidate | 68adbb121997646677b3b9bd17a391534e5818c8, tree 0a1a18bac5a68271cdae18e104de1a7ff149c259 | 2 files ADD, author static only, Windows NOT_RUN |
| **CURRENT A1 R1 review target** | **1b406c788057f0cb2a8a57578b89110a11b76161**, tree **5f1117df2052212185ee51cfc6dae447bed9895f** | ONE test MODIFIED vs immediate parent; independent Windows NOT_RUN |

R1 is directly parented to original A1 68adbb121997646677b3b9bd17a391534e5818c8. Source blob src/vres_os/chairman_b2b_denial_contract.py **706627cc647edb5db655674ee864e16762744a1d**, 524 lines, **unchanged** by correction. Corrected tests/test_chairman_b2b_denial_contract.py blob **f5667e18f53517719a741534127209eabf07ccdc**, 442 lines. Its original first-A1 blob was c159266b477fbc78c1e3ce1578ba9b5a81fec496. Exactly ONE assertion changed: expected Python exception for vars(head) on a frozen slotted dataclass became TypeError rather than AttributeError, because vars() requires a __dict__. This is an **author static catch, NOT an observed test or independent Claude finding**.

GitHub recursive-tree diff confirmed A1 R1 vs first A1 exactly ONE modified test file and no other paths; original module blob unchanged. GitHub commit readback confirmed parent/tree. GitHub compare from accepted base to R1 confirmed two commits ahead and NET exactly TWO ADDED paths (524 source lines +442 tests lines), no B1/B2A edit. Feature ref advanced with exact expected-head no-force operation and verified again. Git commits unsigned; SHA shape/identity does not confer protected signing authority. No source PR/merge, model activation, installed release, signing or provider.

## 2. Developer static review summary — NOT independent

A1 module contains frozen/slots explicitly UNVERIFIED L/G/Q/user/target/release descriptors, PRE_HISTORY_BASELINE/L_ENTRY governing G, NONE/PENDING/RECOVERY pending Q, typed genesis proposal_count=0 with absent B1 digests, exact raw canonical B1 history parsing (B1 1..128 entries), B2B separately purpose/version-domain SHA digests distinct from legacy B1 SHA, closed neutral Refused/Indeterminate outcomes, and TypeError when treated as authorization booleans. The function only performs bounded offline refusals or returns Indeterminate, NEVER authenticated trust, approved positive status or install permit.

New tests cover canonical exact bytes and malformed/duplicate/extra/unknown fields, BOM/literal Unicode/key order/trailing newline, wrong digest domains, false empty genesis, SHA type/zero, missing G/Q, cross-user/release/target mismatch, pending/recovery blocking, claimed count+1, mutation, lack of approval exports and truthiness. ChatGPT author scanned new module text for privileged imports and positive symbols; none identified, all lines <=100 chars. This is NOT a static AST/provenance proof, and **NO WINDOWS PYTEST OR CLAUDE SOURCE REVIEW HAS RUN**. Independent evaluator must assess this exact SHA from scratch.

Original accepted blobs unchanged:
- src/vres_os/chairman_policy.py 36e62d6a2712ac305fd4070bac658b94d61d155e.
- src/vres_os/chairman_policy_history.py e19d913714d3625afaeb91d0fccfcfe43d13d195.
- src/vres_os/chairman_history_expectation.py 304e515e0115716f4da3403017de87eabd888a43.
- tests/conftest.py 1c33bb206dbf42691a6af9a709514bf3cc9994af (1513 lines).
- pyproject.toml b2d5e30d10d7be0613e90bf3ed1e346be5678969.

## 3. Exact next Windows user and Claude independent gate

User starts from original P2 worktree C:\Projects\Vres-P2F-Postinstall-Hardening-20261022, verifying clean status, exact P2 HEAD 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c, official origin https://github.com/vosser24/Vres-OS.git, and the selected NEW review path does not already exist; STOP on any mismatch. Fetch only feature remote ref and verify exact SHA 1b406c788057f0cb2a8a57578b89110a11b76161. Create a NEW detached checkout at this SHA; never reuse original B2A or R3 docs worktrees. Verify HEAD, tree 5f1117df2052212185ee51cfc6dae447bed9895f, immediate parent 68adbb121997646677b3b9bd17a391534e5818c8, grandparent accepted B2A 32847410952e9d4620bf7046cbee4a41a7ddc73b, blobs 706627cc647edb5db655674ee864e16762744a1d and f5667e18f53517719a741534127209eabf07ccdc, net exactly 2 ADD vs accepted base, git diff --check exit 0 and clean tracked/untracked status. Do not reset/stash/overwrite existing directories.

Claude Code **independent reviewer only**: READ/Glob/Grep exact two files, accepted B1/B2A source, pyproject and the complete **1513-line** tests/conftest.py before any execution. Independently challenge slotted mutation, malformed JSON, canonical reserialization, no false genesis, hash-domain mismatches, G vs L/Q, Refused/Indeterminate anti-oracle, caller-asserted provenance and no privileged imports/call paths. Static REJECT means STOP and PYTEST NOT_RUN, followed only by new ChatGPT source SHA and new audit. Do not change source, hooks or test harness. No extra Git/Bash/Python diagnostics by Claude during static review.

If and ONLY if independent STATIC_PASS, run ONE bounded offline Windows CPython 3.12 test invocation from clean detached source checkout:

    py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_b2b_denial_contract.py

Preserve COMPLETE real pytest stdout/stderr, exact exit code, per-case actual PASS/FAIL lines, printed collection/deselection only if present, protection fence and connection-tripwire results, clean Git before/after. Do NOT run a standalone py -3.12 -c version probe (historic R3-PROC-01), broad suite, integration DB or extra scripts. Either an independent REJECT remains REJECT or exact-SHA ACCEPT applies only OFFLINE A1, never to real authorization or model installation.

## 4. All historical and operational safety holds — unchanged

**LIVE_SCHEMA_048_INCIDENT=OPEN; PostgreSQL NO CONTACT even SELECT.** D2 OPEN, F2 quarantined, R0_NOT_RUN, K0-T1 BLOCKED, PA-01..08 incomplete, L-04 OPEN. **F1/#165 OPEN**. Trusted user-event E, independent anchored H/G/L/Q, protected validator V, CAS, install warrant W, independently reviewed release publisher, source/enrollment, loader/runtime enforcement, T2 resistance and physical host #169 validation are NOT implemented or approved; R3-N01/02/06/07 and NF-05..10 are mandatory future STOP gates. No real credentials/keyring/vault, global Claude settings/hooks/plugin changes, signing, real provider/Fable, protected host test, PR/main merge or installation.

Installed personal Windows release 20261022172833-4d82147b from P2 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c remains Chairman **Sonnet/high**; Opus/medium remains UNINSTALLED candidate. Product main last verified 9a8acc5d464b96432a93cb95daa9581412fb07ee. Preserve all original V-01..V-42 functionality scope. Historical B2A R2 REJECT (91 PASS/1 FAIL exit1), original B2A static REJECT, Phase A R2 53/53, B1 99/99, F2 101/101 and 3/3, P2-A1 R4 183/183 all retain their source-scoped identities. B2A R3 95 actual PASSED lines and exit0; do not claim a printed count. Its R3-PROC-01 extra interpreter-version probe remains recorded.

## 5. Resume boundary

**Review target:** feature/165-chairman-policy-foundation-20261023 at 1b406c788057f0cb2a8a57578b89110a11b76161, tree 5f1117df2052212185ee51cfc6dae447bed9895f, with initial A1 parent 68adbb121997646677b3b9bd17a391534e5818c8 and accepted B2A grandparent 32847410952e9d4620bf7046cbee4a41a7ddc73b. New A1 R1 source and tests **NOT independently reviewed or tested**. This corrected source is not authorized for production and cannot issue native trust.

This NEW handoff plus canonical continuity index are to be committed separately as docs-only on top of the prior docs commit a2c380ecef69e9df4bec7f249feaf8adf0a72677; verify actual docs SHA/tree/parent/2-file allowlist before describing docs as sealed. Upon independent Windows verdict, append a fresh new handoff/index and commit docs separately, preserving REJECT, NOT_RUN, process deviations and previous source identities.
