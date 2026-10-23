# Vres-OS — #165 Chairman Phase A R1 REJECT and R2 corrective source checkpoint

Date: 2026-10-23, Europe/Athens.
Evidence status: first independent Phase A review REJECT; source R2 correction COMMITTED and PUBLISHED; R2 independent Windows test NOT_RUN.
Documentation branch: docs/chatgpt-continuity-20261023. Source branch: feature/165-chairman-policy-foundation-20261023.

## 0. Authoritative current boundary (read before running commands)

- Latest #165 source **R2 correction SHA**: 11f2f8689308dfe43e482bca73aa57bb6467c788.
- R2 source parent: 9c919271ba63fb979478c62abaf6c2c3d2679ae7 (R1 reviewed and REJECTED).
- Latest R2 source Git tree: 760d8140127ff40bf2af8ad1a122c3f5d172fc33.
- R2 source changed exactly 2 paths relative to R1: src/vres_os/chairman_policy.py and tests/test_chairman_policy_materialization.py. Source template plugins/vres-os/agents/chairman.md is UNCHANGED by R2.
- Original #165 parent, independently accepted offline P2-A1 R4: 3ba41d5ae6b8f2c2abd93d27f82cce0755878237.
- Original #165 source R1 added module/tests and clarified one Chairman instruction paragraph; no frontmatter or installer integration was made. Both R1 and R2 are pre-release source commits, not installed activation.
- Windows original R1 evaluator directory: C:\Projects\Vres-ChatGPT-Review-165A-20261023, detached at 9c919271ba63fb979478c62abaf6c2c3d2679ae7. Keep this historical worktree intact.
- Windows proposed R2 evaluator directory: C:\Projects\Vres-ChatGPT-Review-165A-R2-20261023. Only create when operator runs a separate fail-stop guarded command.
- Product main last observed 9a8acc5d464b96432a93cb95daa9581412fb07ee; installed Windows personal release still 20261022172833-4d82147b from P2 source 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c; not changed or activated.
- Source #165 Phase A R2 has **no CI checks reported** and **no independent local PASS** as of this handoff. Never carry R1 PASS cases to R2 by assertion.

## 1. Claude R1 evaluator report — complete disposition

The Windows operator returned the full Claude independent report "165 Phase A independent evaluation: Chairman policy materializer at 9c91927" with final **REJECT**, ending VRES_165_PHASE_A_INDEPENDENT_EVALUATION_COMPLETE.

Source verification: exact HEAD 9c919271ba63fb979478c62abaf6c2c3d2679ae7, parent 3ba41d5ae6b8f2c2abd93d27f82cce0755878237, exactly three authorized changed files and clean git diff --check/worktree before and after. Reviewer disclosed one read-only ls-remote GitHub call; no source edits.

Exact authorized test command (one execution):

    py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_policy_materialization.py tests/test_chairman_continuity_contract.py tests/test_plugin_contract.py

Results reported: exit code **1**; **45 cases collected, 39 passed, five failed, two ERROR events** (setup/teardown of the same oversized parametrized case), zero skipped. The counts refer to reported tests vs errors and must not be simply summed into total collected. The reviewer piped the captured output through tail -80 and explicitly did NOT have the full error traceback. Do not assert that the Windows environment-variable limit was physically proven.

Independent acceptance matrix: A policy correctness PASS; B template materialization FAIL; C provenance PASS by source inspection only (the executing test failed); D worker/validator pin separation PASS by static inspection and existing plugin-contract tests; E side effects PASS (no observed connection or live file changes). Final overall REJECT.

F1 HIGH / BLOCKING: Windows Git configured core.autocrlf=true, worktree agent Markdown files have i/lf w/crlf, Chairman template has 112 CR bytes, but R1 materializer refused ALL CR input with "must have LF frontmatter". Five named candidate tests failed; the static source still Sonnet/high. No service contact occurred.

F2 MEDIUM: oversized template test created an implicit ID from more than 512KiB of bytes; test emitted enormous identifiers and setup/teardown errors. Reviewer inferred Windows PYTEST_CURRENT_TEST environment-variable length as likely root cause; actual traceback was truncated and this remains an inference.

F3 LOW: externally constructible ChairmanMaterialization stored caller-provided digests without verifying relationship to content; a future Phase B consumer could trust inconsistent hashes.

F4 LOW / NOT EXECUTED: deep JSON nesting under 4KiB might raise RecursionError instead of the intended ChairmanPolicyError.

F5 INFORMATIONAL: accepted noncanonical JSON source forms are canonicalized on serialization; unused exception binding; simple static I/O assertion not independently sufficient. No release/installer/real model testing was done.

The evaluator found no evidence of Vres startup, PostgreSQL connection, credential access or file mutations. It noted no dedicated keyring fixture for these selected tests, but its source inspection confirmed no selected credential path executed. This R1 verdict is preserved and never recast as PASS.

## 2. ChatGPT-authored R2 patch (NOT YET INDEPENDENTLY REVIEWED)

The correction was committed by ChatGPT to the SAME #165 feature branch with exact parent R1 and without touching the accepted P2-A1 security source or historical reports.

1. F1: In-memory _render_chairman accepts only UNIFORM LF or UNIFORM CRLF UTF-8 input (ordinary Git LF blobs or Windows core.autocrlf CRLF checkout), preserves original exact newline convention and Chairman body bytes when modifying only model/effort fields, and still rejects mixed CRLF/LF, bare CR, NUL, BOM/invalid UTF-8, malformed/foreign frontmatter and oversized inputs. Tests have newline-aware frontmatter/body comparison.
2. F2: oversized pytest case is explicitly named "oversized-template"; test runner no longer needs to populate a 512KiB default parameter ID. F2's original OS cause remains inferred until new reviewer evidence.
3. F3: immutable ChairmanMaterialization now retains real template bytes and candidate bytes, derives hashes on demand and checks candidate equality with a fresh deterministic render in __post_init__. Caller-supplied SHA fields no longer exist; no arbitrary hash values can be passed as metadata.
4. F4: from_document now catches RecursionError during JSON parsing as ChairmanPolicyError; an explicit deeply nested JSON refusal case is added.
5. Regression tests added for both newline styles, unchanged bytes, forged candidate rejection, impossible policy object, invalid mixed styles, and previous worker/validator invariants.
6. Only src/vres_os/chairman_policy.py and tests/test_chairman_policy_materialization.py changed; R2 GitHub commit and tree readback verified. No installed plugin, DB, migration, global Claude, provider, worker pin, release manifest or signing code changed.

R2's status is **PUBLISHED / TEST NOT_RUN / ACCEPTANCE PENDING**. The GitHub branch reference was checked against exact source SHA and the parent/diff shows exactly one commit and those two paths. This document must not say R2 tests have passed before the Windows reviewer runs them.

## 3. EXACT next operator/evaluator actions

Operator should create a new detached review worktree under C:\Projects\Vres-ChatGPT-Review-165A-R2-20261023, anchored at the unmodified original personal source git worktree C:\Projects\Vres-P2F-Postinstall-Hardening-20261022. Use ONE complete PowerShell scriptblock with a strict ^[0-9a-f]{40}$ check, remote GitHub ref check, expected SHA/parent validation, no existing review path, fetch with immediate exit-code check, clean target review status, verify allowed two changed files and diff --check before printing READY. The previous SHA transcription bug was corrected and must not recur.

Correct R2 HEAD: 11f2f8689308dfe43e482bca73aa57bb6467c788.
Correct R2 PARENT: 9c919271ba63fb979478c62abaf6c2c3d2679ae7.
Allowlist: src/vres_os/chairman_policy.py and tests/test_chairman_policy_materialization.py.
Existing R1 review worktree stays intact at its rejected SHA.

After a verified R2 worktree is ready, Claude is independent reviewer ONLY. Launch safe-mode/no custom hooks or MCP and verify source identity, parent, source/test diff, no forbidden I/O, preserved Opus/medium requested policy vs UNCHANGED installed Sonnet/high template, exact manifest/content hashes from real bytes, consistent LF/CRLF, and no unexpected changes to protected Fable/high and Sonnet/Opus worker agents.

The only next *proposed* pytest command, pending local preflight of tests/conftest.py and isolated protected roots, is the same three targeted test modules:

    py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_policy_materialization.py tests/test_chairman_continuity_contract.py tests/test_plugin_contract.py

Do not rerun R1 worktree, install dependencies, start Vres, touch PostgreSQL, access credential vault, run full tests or falsely assert CI. Claude should report exact command, exit code, counts, findings and final ACCEPT / REJECT / BLOCKED for **R2 Phase A OFFLINE ONLY**. On a confirmed defect ChatGPT fixes with a new narrow commit and docs checkpoint.

## 4. Release and program holds unchanged

The full V-01..V-42 original backlog remains active DEVELOPMENT; #165 is PARTIAL/OPEN. R2 does NOT implement Phase B history/policy authority, installed managed materialization or physical host-model observation. Opus/medium is an unactivated requested candidate, not a live model change.

P2-A1 R4: accepted offline source 3ba41d5ae6b8f2c2abd93d27f82cce0755878237, independent 183/183 selected offline tests PASS. Prior R1-R3 security REVIEWS REJECT with 42/117/153 passed selected tests; all results preserved. Five R4 residual findings remain open pending deployment scope.

LIVE_SCHEMA_048_INCIDENT=OPEN; D2=OPEN; F2=QUARANTINED; R0_DB_READ=NOT_RUN; NATIVE_TRUST_APPROVAL=NOT_GRANTED; K0_T1=BLOCKED; L-04=OPEN; POSITIVE_PRODUCTION_TRUST_ISSUANCE=DISABLED. PostgreSQL service STOPPED at last reported observation; no contact, SELECT, migrations or service start. Installed personal release 20261022172833-4d82147b unchanged; PA-01..PA-08 current-live acceptance NOT_COMPLETE. No deployment, global Claude modification, secret access, PR/merge, source branch rewrite or physical model experiment authorized.

## 5. NEW SESSION RESUME PROMPT (current latest)

RESUME Vres-OS ChatGPT-led development from GitHub docs/chatgpt-continuity-20261023 CURRENT HEAD. Read docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md FIRST, then docs/handoffs/VRES-165-PHASE-A-R1-REJECT-R2-WINDOWS-CRLF-CORRECTION-2026-10-23.md, the prior Windows-worktree-ready handoff and #165 Phase A contract, followed by P2-A1 R4 acceptance and the 42-row functionality register. ChatGPT owns code and GitHub commits; Claude is independent evaluator and user operates Windows. The #165 Phase A initial source 9c919271ba63fb979478c62abaf6c2c3d2679ae7 was independently REJECTED on Windows, despite 39 passed tests, because shipped template CRLF made materialization fail (five failures) and an oversized test caused two ERROR events. The newest ChatGPT-authored correction SHA is 11f2f8689308dfe43e482bca73aa57bb6467c788 on feature/165-chairman-policy-foundation-20261023, parent 9c919271ba63fb979478c62abaf6c2c3d2679ae7, two changed paths; it is NOT yet independently tested. Next: one new detached Windows review worktree plus the same narrowly scoped Claude offline evaluation. Preserve all previous reviews and schema-048 no-contact restrictions. After EACH substantive answer, commit detailed new docs handoff and update continuity index with exact readback. Do not change main, installed Vres, global Claude, vault, signing or database without separate authority.

## 6. 2026-10-23 superseding R2 operator worktree success

The Windows operator has now run the guarded R2 review worktree creation successfully: clean detached C:\Projects\Vres-ChatGPT-Review-165A-R2-20261023, exact 40-character SHA **11f2f8689308dfe43e482bca73aa57bb6467c788**, expected parent, only chairman_policy.py and test_chairman_policy_materialization.py changed, no STOP/fatal and marker VRES_165_PHASE_A_R2_REVIEW_READY. That supersedes this file's earlier instruction to create the R2 worktree. The independent R2 pytest/reviewer result is still NOT_RUN. For current next action and complete output, read [the R2 Windows worktree verified handoff](VRES-165-PHASE-A-R2-WINDOWS-WORKTREE-VERIFIED-2026-10-23.md). Keep R1 REJECT and its worktree unmodified.
