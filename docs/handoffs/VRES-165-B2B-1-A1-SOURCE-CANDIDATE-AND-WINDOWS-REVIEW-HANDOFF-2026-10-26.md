# Vres-OS #165 — B2B-1 A1 exact-SHA source candidate and independent Windows review handoff

**Date:** 2026-10-26, Europe/Athens.
**Repository:** vosser24/Vres-OS.
**Canonical documentation branch:** docs/chatgpt-continuity-20261023.
**State:** **A1 SOURCE CANDIDATE COMMITTED / INDEPENDENT STATIC REVIEW NOT_RUN / WINDOWS PYTEST NOT_RUN / NOT ACCEPTED.**
**Scope:** ONLY pure offline B2B-1 UNVERIFIED claims and denial-only results. Neither production authorization nor external trust nor install nor #165 completion.

## 0. Read first, exact next action, and project provenance

Read docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md, this handoff, docs/handoffs/VRES-165-B2B-R3-INDEPENDENT-ACCEPT-AND-FULL-RESUME-2026-10-26.md, docs/architecture/VRES-165-B2B-R3-POSTREVIEW-ERRATUM-2026-10-26.md, then the unmodified reviewed R3 architecture. The independent Claude R3 decision was **DESIGN_ACCEPT solely for OFFLINE DENY-ONLY B2B-1**, not for this A1 source. Prior B2B v0/R1/R2 independently **DESIGN_REVISE**; historical outcomes remain intact.

**NEXT:** user creates a fresh guarded, exact-SHA **SOURCE** Windows detached checkout, then Claude Code independently reads and security-reviews both new files, original B1/B2A source interfaces, pyproject.toml and the entire protected tests/conftest.py BEFORE any test. Only an explicit static PASS permits ONE bounded offline Windows CPython 3.12 pytest invocation on tests/test_chairman_b2b_denial_contract.py. Neither ChatGPT's static development inspection nor GitHub's accepted write constitutes independent acceptance.

## 1. GitHub source transaction: exact identity and allowlist

Source branch: feature/165-chairman-policy-foundation-20261023.

| Item | Verified value |
| --- | --- |
| Accepted independent B2A R3 base / A1 single parent | 32847410952e9d4620bf7046cbee4a41a7ddc73b |
| Base source tree | e7e39a50a3528f329d1cd27d1c23a1cbb279e697 |
| NEW A1 feature HEAD/commit | **68adbb121997646677b3b9bd17a391534e5818c8** |
| NEW A1 tree | **0a1a18bac5a68271cdae18e104de1a7ff149c259** |
| ADD source file | src/vres_os/chairman_b2b_denial_contract.py |
| Source Git blob | **706627cc647edb5db655674ee864e16762744a1d** (524 added lines) |
| ADD negative test file | tests/test_chairman_b2b_denial_contract.py |
| Test Git blob | **c159266b477fbc78c1e3ce1578ba9b5a81fec496** (442 added lines) |

ChatGPT created separate unreferenced draft blobs, caught and corrected a slotted-dataclass test assertion BEFORE source commit, created the two-ADD-only Git tree against the exact accepted base tree, fetched BOTH recursively to compute changed-path allowlist (exactly 2 ADD, no modified/deleted paths), created ONE source commit with exactly ONE accepted parent and explicitly advanced ONLY the feature branch with expected-old-SHA/no-force guard. GitHub commit API independently read back tree, parent and two paths; GitHub branch readback returned the exact new HEAD/tree. Commit is unsigned (not signing authority). Main, installer and canonical documentation branch were not touched in the source transaction. No PR, merge, runtime update, provider, signing or protected test run.

Accepted source interface Git blobs, unchanged by A1:
- src/vres_os/chairman_policy.py: 36e62d6a2712ac305fd4070bac658b94d61d155e.
- src/vres_os/chairman_policy_history.py: e19d913714d3625afaeb91d0fccfcfe43d13d195.
- src/vres_os/chairman_history_expectation.py: 304e515e0115716f4da3403017de87eabd888a43.
- tests/conftest.py: 1c33bb206dbf42691a6af9a709514bf3cc9994af.
- pyproject.toml: b2d5e30d10d7be0613e90bf3ed1e346be5678969.

## 2. A1 source behavior, exact non-authority boundary

**Only unverified frozen/slots claim types:** ClaimedDigest with typed purpose; ClaimedScope with bounded opaque unverified user reference and distinct TARGET/RELEASE digest; ClaimedGoverningReference tagged PRE_HISTORY_BASELINE or bounded L_ENTRY(sequence, proposal_sha256); ClaimedPendingState tagged NONE/PENDING/RECOVERY with typed intent/investigation references; ClaimedAnchorHead with independent anchor epoch, latest immutable B1 proposal L count/hash/latest, separate last-governing G and still-blocking Q; ClaimedCanonicalHistory preserving exact raw accepted B1 bytes.

**R3-N03:** G baseline is a separate variant with NO B1 entry; L_ENTRY must name an existing bounded sequence, never assume latest L == G. **R3-N05:** NONE serializes to literal JSON null; PENDING(intent), RECOVERY(intent, investigation_ref) have disjoint exact key sets. RECOVERY never clears Q or authorizes continuation.

**R3-N04:** B1 from_document plus byte-for-byte equality to to_document; malformed/BOM/key-order/literal Unicode/trailing newline/duplicate/extra/missing JSON is refused. B1 1..128 nonempty format and legacy canonical B1 SHA remain UNCHANGED. A proposal_count=0 H0 has typed null SHA values and may not fake empty B1 history. An A1 inert claimed successor requires count exactly old claimed proposal_count+1; this is only an **UNVERIFIED syntactic count check**, not a protected prior-prefix comparison. A1 **DOES NOT** compare claimed P against an authenticated H_n, does not call B2A with a false origin, and does not assert this count check proves append authenticity. That separate protected gate remains OPEN.

A1 canonical claimed-anchor JSON contains embedded purpose/domain/version, exact closed field sets, bounded integers/ASCII opaque ID, SHA-256 lowercase/nonzero shape and bounded raw bytes. A1 B1-history evidence bytes have their own binary version/domain prefix plus explicit 4-byte length and canonical B1 document. Claimed evidence digests use SHA-256 of these version/purpose-separated bytes; they NEVER replace legacy B1 sha256 and are NOT signatures or trusted attestations. Cross-purpose SHA substitution refuses.

**Only decision return classes:** frozen Refused(code) and Indeterminate(code), closed RefusalCode enum. Both explicitly reject bool() with TypeError, and neither has permit, success, trusted, authority, approved, checks_passed or ready-for-install outputs. Indeterminate merely says independent authority is not established even if self-consistent claims were supplied; it is NOT a positive elimination oracle. The current limited assess_unverified_claims operation refuses malformed/conflicting scope/digest/pending/count assertions and never owns a privileged action. Reviewer MUST independently challenge any anti-oracle leakage or positive interpretation of a particular reason code.

**NO** filesystem/process/network/registry/DB/keyring/ctypes import or operation, vault, credential, provider, protected Fable/validator, trusted E/V/W, CAS/store, native signature, startup/bootstrap, CLI/model activation, installer, real runtime or host observation. Source author scanned new source/test text for privileged imports/positive symbols and lines exceeding 100 characters; no matches. This was **developer static inspection only**, not AST execution, Windows security assessment, or pytest.

## 3. Negative tests authored but unexecuted

The only new test file covers: canonical JSON round-trip/domain/schema, typed genesis null and no zero-entry B1, independent epoch vs count and G, legacy-vs-B2B SHA separation, genuine key-order/escaped ASCII/trailing newline/BOM/duplicate/non-UTF8/deep/oversized cases, 16 malicious JSON field/tag/scope changes, wrong integer/bool/count/version/digest types, zero-filled/upper-case digest, exact canonical B1 bytes and Unicode, PENDING/RECOVERY still blocking, cross-user/target/release mismatches, cross-domain or substituted evidence digest, claimed count+1 shape, attacker-controlled claims remaining Indeterminate, refusal/indeterminate truthiness TypeError and no positive API, FrozenInstanceError/slots and deliberate low-level corruption readback refusal.

**Results:** NOT_RUN. There are NO reported PASSED lines, no pytest exit code, no collection count, no isolation/tripwire outcome and no independent Claude SOURCE_ACCEPT. Do not call these tests passing merely because GitHub accepted the code.

## 4. Windows safety preflight and isolated evaluator (UNEXECUTED)

The developer read the accepted B1/B2A source and relevant original tests plus pyproject. The accepted tests/conftest.py (1513 lines) includes a pre-import protected live-app-data fence, TEMP/TMP local NTFS/ReFS checks, VRES_DATA_DIR disposable separation, platformdirs/audit-hook interception, disallowed external children, database/libpq env scrub, autouse psycopg/Vres driver connection tripwires and session summary. That is a process-level fence, not an OS sandbox; independent Claude MUST inspect ALL of conftest.py again in its own fresh Windows source worktree, including code not reproduced in this handoff.

User Windows anchor: C:\Projects\Vres-P2F-Postinstall-Hardening-20261022, expected original P2 source HEAD 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c, clean. Do not reuse old B2A or design checkout. Require official origin, a fresh previously non-existing detached A1 review worktree, fetched exact new source SHA, single parent match, exact tree match, Git blob verification and changed-path allowlist, git diff --check, clean porcelain before review. All guards must STOP before any unsafe write on mismatch. No reset/stash/cleanup of other worktrees.

Claude is **independent static/security reviewer and test evaluator, never implementation agent**. First Read/Glob/Grep the exact two files, B1/B2A interfaces and full conftest, examine mutable-object bypasses, malformed JSON, domain separation, zero-count, race/authority escalation, exception behavior, anti-oracle issues, import reachability and tests. Do NOT run Git/Python/pytest/Bash or extra diagnostics before static PASS; do not edit any source or fixtures. If static fails: REJECT, pytest NOT_RUN, ChatGPT repair requires a NEW distinct SHA and new review.

If and only if static PASS is explicitly recorded, run **ONE** exactly selected Windows offline command from detached source worktree:

    py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_b2b_denial_contract.py

No additional Python version probe or other Python scripts (avoid historical R3-PROC-01), no broad suite or integration opt-in, no PostgreSQL even SELECT. Preserve complete terminal output, exact $LASTEXITCODE, PASSED/FAILED test IDs, isolation/tripwire terminal footer, before/after porcelain cleanliness, and any process deviation. If rejected, never massage results; return issue-specific REJECT with original evidence. If accepted, acceptance is solely offline A1 at THIS exact source SHA; no positive trust or installation.

## 5. Mandatory historical holds and reviewer concerns

Historical B2A R3 exact accepted parent 32847410952e9d4620bf7046cbee4a41a7ddc73b: Windows exit 0 and 95 separate PASSED lines; test collection number inferred, not printed. One extra sys.version Python probe **R3-PROC-01** remains recorded. Parent B2A R2 REJECT 91/92 and initial B2A static REJECT remain separate. Earlier B1 99/99, F2 code 101/101, F2 tests 3/3, Phase A R2 53/53 and P2-A1 R4 183/183 accepted only at their own SHAs; all earlier REJECT outcomes preserved. R3 design acceptance alone did not accept this new A1 Python.

**Unresolved design gates:** R3-N01 partial-install ABANDON/recovery, N02 exact W-backed COMPLETE, N06 real trusted consent display for G/L, N07 true E/V/CAS for each forward transition; NF-05 linearizable CAS/revoke, NF-06 effective runtime overrides, NF-07 independent trusted release publisher, NF-08 genesis lineage, NF-09 release status at W, NF-10 actual validator provenance. NO native trusted provider/positive issuance, F1 OPEN and #165 OPEN/PARTIAL.

**LIVE_SCHEMA_048_INCIDENT=OPEN; absolutely NO PostgreSQL contact even SELECT.** D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 blocked, L-04 OPEN, PA-01..PA-08 incomplete. No real credentials/vault, changes to global Claude hooks/settings/plugins, signing, provider calls, protected Fable, personal installer, source PR/merge to main, OS-level physical model test or release without separate explicit permission.

Personal installed release unchanged: 20261022172833-4d82147b (original P2 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c), Chairman Sonnet/high. Opus/medium remains an UNINSTALLED candidate. Product main last verified 9a8acc5d464b96432a93cb95daa9581412fb07ee, NOT promoted by A1. All V-01..V-42 development backlog stays active, not a live deployment claim.

## 6. Next exact checkpoint and continuation

1. Publish this handoff and update the index as ONE **separate documentation-only** GitHub commit on docs/chatgpt-continuity-20261023, parent 9b441b613c112fcdcfd0c0becaf0efb8b8e18bbb. Read back commit/tree/parents/two docs paths and unchanged feature SHA; if a tool blocks, do not claim sealed.
2. User guarded Windows checkout at **68adbb121997646677b3b9bd17a391534e5818c8**; Claude independent static review first; exact bounded selected pytest only if static passes. Do not repeat prior accepted reviews. No further source edits to A1 except via a NEW commit after an independent REJECT.
3. Preserve complete operator/Claude report and any test failure/procedural deviation. Next docs-only handoff/index update after that substantive result; only an independently accepted A1 can open an A2 denial-only design/development step, never a real trust provider by default.

**New-session resume:** read CURRENT continuity index, this A1 handoff, R3 acceptance, post-review erratum and immutable reviewed R3 design; source feature HEAD 68adbb121997646677b3b9bd17a391534e5818c8 with parent 32847410952e9d4620bf7046cbee4a41a7ddc73b, tree 0a1a18bac5a68271cdae18e104de1a7ff149c259 and exact 2 ADD paths/blobs above. A1 implementation committed but INDEPENDENT STATIC REVIEW AND WINDOWS TESTS NOT_RUN. Next guarded detached SOURCE checkout and Claude evaluation. All operational/security/roadmap holds persist.
