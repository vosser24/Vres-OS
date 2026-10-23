# Vres-OS #165 — B2A static REJECT, R2 guarded source correction, Windows review pending

Date: 2026-10-23, Europe/Athens.
Repository: vosser24/Vres-OS.
Canonical docs branch: docs/chatgpt-continuity-20261023.
Source branch: feature/165-chairman-policy-foundation-20261023.
Current judgment: **previous B2A static review REJECT**; new source fix committed and published but **independent R2 Windows test NOT_RUN**.
Roles: ChatGPT implements/GitHub commits, Claude independently reviews without edits, user operates protected Windows worktree.
No runtime authority, model activation, release installation, PostgreSQL or native trust authorization.

## 0. Verified exact source identity and unchanged prior verdicts

- **NEW UNTESTED B2A R2 source HEAD:** 060756b02786c146b87a5262ba2b3b2cc6bf2784.
- **Immediate parent:** c01152e374c4e7e0ae8e0a01eab5148cdf71e84e — original B2A comparator, independent STATIC_REVIEW_REJECT.
- New source Git tree: 6559b30a117453be162405fb1a8e2d045f2cd5cf.
- Source commit read back against feature branch, one commit ahead of original, exactly two MODIFIED files:
  src/vres_os/chairman_history_expectation.py (+16/-10);
  tests/test_chairman_history_expectation.py (+88/-3).
- No edit to Phase A policy, B1 history, F2 size boundary, installed Chairman agent, protected worker/validator pins, migration, installer or global Claude.
- Earlier independently ACCEPTED exact commits remain intact: F2 test-only 36a41b6151b7520329ccc0ada0ff827d836ec579 (3/3 selected PASS, exit 0), F2 implementation b77e0eef07976877e7f198a00484f5d13ce36889 (101/101 PASS), B1 initial f8237bb301dec160f33cab524727e6a0ec79b2c0 (99/99 PASS), Phase A R2 11f2f8689308dfe43e482bca73aa57bb6467c788 (53/53 PASS), P2-A1 security R4 3ba41d5ae6b8f2c2abd93d27f82cce0755878237 (183/183 PASS). Phase A R1 and P2-A1 R1–R3 REJECT remain preserved; those test results do NOT transfer to new B2A.
- No GitHub CI statuses observed at new R2 SHA; no Python/Windows pytest result claimed.

## 1. Full independent static review of original B2A (evidence preserved)

User uploaded Claude's complete independent static inspection report, final marker VRES_165_B2A_STATIC_REVIEW_COMPLETE, verdict **STATIC_REVIEW_REJECT** on original source c01152e374c4e7e0ae8e0a01eab5148cdf71e84e.

Reviewer read both new files fully, plus Phase A policy and B1 proposal-history dependencies. No Git, Bash, Python or pytest invocation occurred in Claude. Operator had independently verified clean detached Windows worktree at C:\Projects\Vres-ChatGPT-Review-165B2A-ReadOnly-20261023. Thus original B2A test status is TESTS_NOT_RUN, not a failed pytest result.

Static acceptance of original implementation: strict exact identity types, count 1..128, SHA-256 checks, canonical-only byte boundary, three-part count/history/head comparison, refusal of mismatched internally valid truncated prefixes or same-length forks relative to an expected checkpoint, absence of provider/DB/vault/install I/O, no false approval object or model-selection operation. The reviewer found NO blocking implementation defect, but **test suite fitness FAIL**.

Original source findings with severity, before R2 correction:
- **C-1 BLOCKING:** tests/test_chairman_history_expectation.py:147 passed b" " * (256*1024+1) as unnamed pytest parameter, risking a gigantic Windows PYTEST_CURRENT_TEST environment value (past R1 occurrence had setup/teardown errors). This was reasoned statically, not executed.
- **C-2 LOW:** wrong-schema case was a str, so it failed type validation before actually reaching history schema checking.
- **C-3 LOW:** vars(module) name-based absence-of-I/O assertion is a weak test, not proof of no I/O; independent source inspection is the stronger evidence.
- **C-4 LOW:** noncanonical JSON test only covered whitespace, not changed key order/raw UTF-8/trailing newline/BOM variants.
- **C-5 LOW:** missing expected wrong-type/subclass, 128 count boundary and digest slot mutation tests.
- **D-2 LOW:** deleting an expected object's slotted field could raise raw AttributeError instead of the documented ChairmanHistoryExpectationError (still failed closed).
- **D-3 LOW:** revalidated identity snapshot was discarded, so subsequent comparisons reread mutable low-level bypass data.
- **D-4 LOW:** locally repeated proposal-count constant might drift from accepted history model.
- **D-5 MEDIUM FUTURE INTEGRATION RISK:** a malicious caller could self-derive expected hashes from its own forged history; a successful comparison would be tautological. Not an implementation defect in this inert pre-authority component, but **F1 trusted external provenance remains OPEN**.
- Other findings: constant-time equality not required for public content hashes; C-1 was static inference, not an observed pytest error.

The first attempts to fix the named pytest ID through a narrow test-only Git write and publish earlier B2A docs were blocked by tool safety controls and produced NO commits. These historical blocks remain true. They do not indicate that the later independently scoped R2 fix was already reviewed.

## 2. Exact R2 correction authored and COMMITTED by ChatGPT

After independent static REJECT, ChatGPT published a separate same-feature correction, parent exactly c01152e3, without force push/rebase. GitHub readback verified the full new commit and changed-path allowlist.

- **C-1:** unsafe unnamed parameter replaced with pytest.param(..., id="oversized-history"). No 256KiB value is used as a node identifier.
- **C-2:** wrong-schema parameter is now bytes; a dedicated test explicitly confirms that a valid-shaped history reaches and triggers the history schema rejection before comparison rewraps the result.
- **C-4:** tests added for altered JSON key order, literal UTF-8 instead of canonical escapes, trailing newline and BOM.
- **C-5:** tests added for incorrect expected-object types, subclass rejection, 128 proposal-count boundary, deleted slotted expected fields and low-level modified digest fields.
- **D-2:** attribute deletion during expected snapshot reconstruction is normalized to ChairmanHistoryExpectationError, preserving fail-closed API behavior.
- **D-3:** a revalidated immutable local snapshot \`checked\` is used for all subsequent comparisons rather than rereading the original expected object.
- **D-4:** compare-module imports the proposal-count bound from the accepted history module instead of duplicating a magic 128.
- **C-3 remains a nonblocking test-quality limitation:** vars(module) is not a proof of absence of I/O. The independent reviewer must inspect source/import graph; no new IO introduced or claimed.

The revised implementation is still a **pure non-authenticating comparison primitive**. It re-parses candidate history and returns None on equality; does NOT authenticate expected values, approve a model, sign, install or change a runtime. No user-event provenance or protected Fable validation exists. **F1 remains OPEN.**

## 3. NEXT OPERATOR ACTION: fresh exact-R2 Windows review and bounded tests

One NEW detached worktree, preserve the original STATIC_REVIEW_REJECT folder untouched:

    C:\Projects\Vres-ChatGPT-Review-165B2A-R2-20261023

Source feature branch: feature/165-chairman-policy-foundation-20261023.
Expected HEAD: 060756b02786c146b87a5262ba2b3b2cc6bf2784.
Expected immediate parent: c01152e374c4e7e0ae8e0a01eab5148cdf71e84e.
Compare exactly two modified paths as in section 0.
Use original read-only personal P2 anchor C:\Projects\Vres-P2F-Postinstall-Hardening-20261022 at 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c; verify clean worktree/official origin/current remote/40-character SHA/ref/parent; fetch and git worktree add --detach to NEW absent folder, diff --check, changed allowlist and clean review; print READY ONLY after every check. No checkout/reset/clean/overwrite of existing review folders.

After real READY, launch Claude safe-mode with only built-in Read/Glob/Grep/Bash and disallow external MCP, stop if unexpected Vres hooks/db plugin starts. Claude reviews exact R2 vs original STATIC_REVIEW_REJECT and test modifications. First inspect tests/conftest.py for disposable user-data root and private appdata, PostgreSQL connection tripwires, blocked child processes, DB/PG/GIT env cleanup and any credential/keyring path. If isolation cannot be demonstrated, report BLOCKED without executing tests.

**Proposed ONE offline pytest command, NOT YET EXECUTED:**

    py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_history_expectation.py tests/test_chairman_policy_history.py

This tests the corrected B2A comparator and its accepted B1 history dependency. No full repository suite, PostgreSQL, installed version, external model call or additional Python probes. Return actual command/exit counts, preflight, exact worktree SHA/parent/diff before-after, observed side effects and independent ACCEPT/REJECT/BLOCKED limited to B2A R2 offline source. Distinguish executed tests from code inspection. Do not claim a PASS until operator returns Claude results.

## 4. Release/incident holds (unchanged)

LIVE_SCHEMA_048_INCIDENT=OPEN; PostgreSQL service last observed STOPPED; NEVER contact DB even for SELECT. D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 blocked, L-04 open, PA-01..08 incomplete, native trust approval NOT_GRANTED, positive production trust issuance DISABLED. No real credential vault, Windows secret access, user/global Claude modification, installation/activation, PR/main merge/force push or physical model test without separate authority.

#165 remains OPEN/PARTIAL; installed Windows personal release 20261022172833-4d82147b from original P2 source 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c unchanged; shipped Chairman still sonnet/high and default requested policy opus/medium remains candidate ONLY. Product main last read 9a8acc5d464b96432a93cb95daa9581412fb07ee. Preserve all original V-01..V-42 product-development backlog and accepted/rejected evidence.

## 5. Copy-ready new-session RESUME

Resume vosser24/Vres-OS ChatGPT-led project from CURRENT HEAD docs/chatgpt-continuity-20261023. Read docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md, then THIS B2A STATIC REJECT / R2 REPAIR handoff first, followed by the original B2A static-worktree handoff and F2 test-only ACCEPT. Latest source feature branch commit **060756b02786c146b87a5262ba2b3b2cc6bf2784**, parent **c01152e374c4e7e0ae8e0a01eab5148cdf71e84e**; two modified comparator source/test files. Original B2A c01152e was independent STATIC_REVIEW_REJECT (TESTS_NOT_RUN), because test parametrization could overflow Windows. New R2 corrects that plus lower-severity static findings, but independent R2 tests NOT_RUN. NEXT action: guard/create one NEW detached Windows review folder C:\Projects\Vres-ChatGPT-Review-165B2A-R2-20261023 then launch Claude offline independent review with exact two-module pytest; do not reuse earlier results. F1 authenticated external history anchor, trusted operator event and protected validator still OPEN; no installed Opus/medium. Preserve accepted F2 3/3, 101/101, B1 99/99, Phase A 53/53, P2-A1 R4 183/183, all R1-R3/R1 rejection evidence. Schema-048 DB no-contact, global Claude, vault, native trust, live PA/K0 blocks remain. After each substantive response commit detailed docs-only handoff+read-first index and report verified SHA.

## 6. 2026-10-23 SUPERSEDING successful B2A R2 Windows checkout

The Windows operator successfully executed the guarded B2A R2 worktree script and supplied the terminal output ending VRES_165_B2A_R2_REVIEW_READY. A new clean detached review folder exists at C:\Projects\Vres-ChatGPT-Review-165B2A-R2-20261023 at source 060756b02786c146b87a5262ba2b3b2cc6bf2784 (parent original static REJECT c01152e374c4e7e0ae8e0a01eab5148cdf71e84e). Only chairman_history_expectation.py and test_chairman_history_expectation.py differ from parent. No STOP/fatal. Therefore the earlier "create a new worktree" action in this handoff is now HISTORICAL. The latest [B2A R2 worktree-verified handoff](VRES-165-B2A-R2-WINDOWS-WORKTREE-VERIFIED-2026-10-23.md) governs the next Claude safe-mode offline evaluation. R2 independent tests remain NOT_RUN. F1 trusted external history authentication and all schema-048, installer and Opus activation holds remain OPEN.
