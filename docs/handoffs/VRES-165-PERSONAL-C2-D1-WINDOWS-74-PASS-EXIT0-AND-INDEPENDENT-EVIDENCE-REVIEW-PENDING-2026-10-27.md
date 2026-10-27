# Vres-OS #165 — PERSONAL C2-D1 one Windows selected offline pytest: 74 individual PASS, exit 0; independent REPORT-ONLY evaluation PENDING

**Date:** 2026-10-27, Europe/Athens.
**Repository:** vosser24/Vres-OS.
**Scope:** current-user PERSONAL Windows, immutable pure D1 denial/diagnostic source and its new negative tests.
**Current evidence status:** C2_D1_GITHUB_SOURCE_COMMITTED / OPERATOR_WINDOWS_REVIEW_WORKTREE_READY / INDEPENDENT_CLAUDE_STATIC_PASS / OPERATOR_SELECTED_WINDOWS_PYTEST_EXECUTION_PASS / INDEPENDENT_CLAUDE_REPORT_ONLY_EVALUATION_NOT_RUN / **D1 OFFLINE_ACCEPT NOT YET GRANTED** / NO_AUTHORITY_ISSUED / NO_MODEL_ACTIVATION.
**Absolute hold:** LIVE_SCHEMA_048_INCIDENT=OPEN. **NO PostgreSQL contact even SELECT**, direct or via Vres tasks, database backed CLI, bootstrap, doctor, hooks or installation.
**Caution:** The full operator transcript below is USER-SUPPLIED, not independent instrumented host evidence. The accepted in-process conftest fixture is not an OS/network sandbox and cannot attest physical PostgreSQL non-contact.

## 0. Canonical precedence, completed STATIC-only boundary

Read the newest docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md first, THIS newest operator-test checkpoint next, and the prior:
- docs/handoffs/VRES-165-PERSONAL-C2-D1-INDEPENDENT-STATIC-PASS-AND-GUARDED-WINDOWS-TEST-GATE-2026-10-27.md, blob f439249f079bf35f964f917e9160a1283a546706 — independent Claude STATIC_PASS (zero blocking, eight informational I01–I08), strict one-test script/methodology.
- docs/handoffs/VRES-165-C2-D1-CHATGPT-SESSION-CONTINUITY-SEAL-2026-10-27.md, blob f585e3408c80dd3a370ccb2d8d5dfb7f4c195e2b — full historical/roadmap continuity, source/protection boundaries.
- docs/handoffs/VRES-165-PERSONAL-C2-D1-WINDOWS-SOURCE-REVIEW-READY-AND-INDEPENDENT-STATIC-GATE-2026-10-27.md, blob d83cefb2ebfd446c02fdf2f519c1c89a7550e288 — pre-existing detached worktree and guarded Git verification.
- docs/handoffs/VRES-165-PERSONAL-C2-V1-R1-INDEPENDENT-DESIGN-ACCEPT-AND-PURE-D1-NEXT-2026-10-27.md, blob c321ca0e9c45dae239f294ef3cd2b75b7c19280a — separate V1 concept DESIGN_ACCEPT (seven future informational items), NOT a positive release.
- Earlier SHA-specific C0/C1/A1/B2A/B2B/PhaseA/F2/P2-A1/E7 preproduction outcomes, original V-01..V-42 PERSONAL capability roadmap and all historical REJECT, test EXIT1 and procedural findings remain intact; never overwrite a verdict at a failed SHA.

## 1. Immutable GitHub/Windows source boundary

Feature branch: `feature/165-chairman-policy-foundation-20261023`.
**Feature HEAD:** `358b3554075f87f5b8287fbb37d66fa95ad68b7c`.
**Feature tree:** `af1d7349f1e7028145567b6330a5b25bdc0f5920`.
**Single direct parent accepted C1 R1:** `7ac041018d4ec5a06be07318ecce5e140faccd91`.
GitHub comparison again returned exactly one ahead commit and ONLY TWO ADD paths, no other modification/deletion:
- `src/vres_os/chairman_c2_offline_planner.py`, blob `9cde474f7f9a5450c9faf7cbcbe4a608d317c1fd` (240 numbered source lines).
- `tests/test_chairman_c2_offline_planner.py`, blob `975ed8f4a5a38c307be48a99f401c1edcbeba67f` (317 numbered test lines).

Accepted Phase A/C0/C1/B2B/agent-template/conftest/pyproject Git blobs remain unchanged as earlier verified. The operator ran from already existing clean detached review worktree `C:\Projects\Vres-ChatGPT-Review-165C2-D1-20261027`; the script's source identity check asserts detached HEAD/tree/sole parent, all nine named immutable blobs, exactly two ADDs, diff --check and clean. No new checkout or fetch/rebase/reset/source commit is needed. Original P2 clean anchor `C:\Projects\Vres-P2F-Postinstall-Hardening-20261022` at `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c` remains separate/untouched.

This document is to be added to canonical documentation branch **docs/chatgpt-continuity-20261023** with old docs head `b93467bd5533b10205be7310bfa8bc1007d39398`, tree `7a9d983708fd9715983e658c7f1095f564c03e89`; after new docs commit, read back actual new HEAD/tree, never fabricate it.

## 2. Original operator Windows selected pytest: observed outcome

The user uploaded **ONE 109-line PowerShell transcript**, 21,704 original bytes, original UTF-8 ASCII-compatible text with CRLF separators and a single trailing space after the last PowerShell prompt. **Original file SHA-256 (on uploaded 21,704 bytes): `477cda4fadf63bfe4448d7e34cd539f4fd2a7740ff0e6295565fdb13b40989f6`**. The full console content is preserved in Appendix A below, with ONLY CRLF->LF normalization and one final prompt trailing ASCII space removed for GitHub diff --check hygiene; this makes the human-readable appendix NOT byte-identical to the uploaded file. All meaningful stdout characters and all 74 test IDs are otherwise kept. GitHub blob SHA for this handoff is assigned by the subsequent docs commit; it is NOT the original file SHA256.

**Pre-test log lines 1–18:** source detached HEAD, source HEAD/tree/sole parent, both new module/test Git blobs, unchanged policy/C0/C1/B2B/plugin/conftest/pyproject Git blobs all printed PASS. Exactly TWO added paths, source diff --check, pre-test tracked/untracked clean all printed PASS, marker `C2_D1_PREFLIGHT_PASS`. These are guard PASS labels from the user script, not displayed raw SHA values, and do not alone constitute OS-level attestation.

**Test command and scope lines 19–24:**
- `PYTHONPATH_SCOPE=D1_SOURCE_ONLY`; process-only Python import path was set/restored per the established script, original inherited value was NOT printed (no secret leakage).
- ONE echoed `SELECTED_PYTEST_COMMAND=py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_c2_offline_planner.py`, no other pytest, Python version probe or broad suite shown.
- Dot progress line reached `[100%]`, followed by `PASSES` heading and the in-process fence line:
  `LIVE APP-DATA FENCE: unexpected refusals=0`; `integration_opt_in=False`; protected current-user AppData roots and disposable temp session printed; `removed_env=['GIT_ASKPASS']`. The fence protects observed in-process test paths only, **NOT host/network/driver PostgreSQL contact**.

**Individual results (original lines 25–98):** Exactly **74** distinct individually printed `PASSED tests/test_chairman_c2_offline_planner.py::...` entries across 18 test functions. Pytest did NOT print a closing "74 passed", a collected summary total or a duration. Do NOT invent those. The visible transcript has no FAIL, ERROR, SKIP, XFAIL, XPASS, traceback or command failure. Both the baseline and proposed 4097-space auto-ID cases completed successfully, despite the independently disclosed D1-STATIC-I02 long-ID information-only risk; this single Windows run has not changed source.

| Observed test function | Individual PASSED IDs |
| --- | ---: |
| `test_unverified_good_looking_input_is_indeterminate_not_a_permission` | 1 |
| `test_all_caller_claimed_reviews_are_untrusted_even_when_everything_matches` | 1 |
| `test_neither_baseline_nor_opus_policy_can_result_in_positive_authority` | 4 |
| `test_pure_renderer_preserves_caller_template_line_endings` | 2 |
| `test_malformed_or_oversized_caller_template_is_refused_without_digest` | 11 |
| `test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally` | 28 |
| `test_untyped_claims_cannot_become_a_review_approval` | 5 |
| `test_corrupted_frozen_claims_are_revalidated_at_call_boundary` | 1 |
| `test_same_sha_under_wrong_digest_purpose_is_refused_not_converted` | 2 |
| `test_mismatching_caller_template_sha_is_refused_even_with_claimed_review` | 1 |
| `test_untyped_or_bad_claimed_digest_is_neutral_refusal` | 5 |
| `test_constructing_invalid_typed_digest_refuses` | 4 |
| `test_reported_baseline_disagreement_refuses_without_source_discovery` | 1 |
| `test_known_sonnet_default_doctrine_refuses_even_if_claimed_reviewed` | 4 |
| `test_known_doctrine_case_variants_conservatively_refuse` | 1 |
| `test_old_doctrine_does_not_claim_a_runtime_model_from_sonnet_noop` | 1 |
| `test_result_types_are_frozen_closed_and_never_truthy` | 1 |
| `test_module_has_only_closed_negative_api_and_no_side_effect_surface` | 1 |
| **TOTAL individual PASSED entries** | **74** |

**Post-test original lines 99–109:** printed `PYTEST_EXIT_CODE=0`, `PASS: PYTHONPATH_RESTORED`, exact source HEAD/tree and both D1 blobs PASS, `PASS: Post-test worktree clean`, marker `C2_D1_WINDOWS_TEST_EXECUTION_PASS_PENDING_INDEPENDENT_EVALUATION`, then `VRES_165_C2_D1_WINDOWS_SELECTED_TEST_EXECUTION_COMPLETE`. Final normal shell prompt `PS C:\Users\User>` is expected when the script's Push-Location/Pop-Location restores the user's original directory; it is not evidence of a D1 mismatch. No PowerShell orphan ELSE error or extra interpreter invocation is shown. The script did not explicitly echo its CWD before pytest; target review CWD comes from the supplied one-shot script/Push-Location and preflight path. Preserve this as an evidence limitation, not independent host certification.

**ChatGPT provisional operator-execution determination:** **OPERATOR_TEST_EXECUTION_PASS** (74 individually observed PASSED entries, immediate reported test EXIT0, in-process fence markers, process PYTHONPATH restoration, post-source/worktree intact) at exact immutable source SHA. **This is NOT independent D1 OFFLINE_ACCEPT.**

## 3. Preserve STATIC review findings and evidence limitations

The previous independent Claude STATIC_PASS remains exactly eight informational items, ZERO blockers, as documented at `f439249f079bf35f964f917e9160a1283a546706`: I01 Indeterminate check-elimination inference; I02 long 4097-space policy pytest parameter ID (observed PASS this time); I03 brittle exact-substring negative Sonnet doctrine matcher; I04 deliberately discarded claimed review; I05 cross-purpose claimed digest always refused; I06 duplicated 4096/512KiB size caps; I07 preview-only Ruff UP042; I08 deep JSON parse/refusal. No static item has been erased, given approval status, or silently fixed.

Evidence caveats:
- This is user-supplied Windows output, not independently witnessed subprocess/shell/Git identity by Claude. The exact current source SHA values are demonstrated by pre/post PASS labels grounded in previously supplied guarded script; the console does not echo the raw matching hex values.
- One selected pytest command is echoed once; no hidden retries or other commands appear in this excerpt, but not native OS instrumentation.
- 74 counted IDs derive from actual displayed `PASSED` lines, NOT collected/footer count.
- `tests/conftest.py` enforces process-level AppData and DB isolation policies; it is not physical network/OS PostgreSQL no-contact proof, and the persistent LIVE_SCHEMA_048 total prohibition remains.
- Source HEAD/tree and new blobs were rechecked after, but every unchanged protected blob was checked only before the test. Unchanged full tree indirectly protects those files.
- The current effective Claude Chairman model has NOT been measured. Original P2 installed Sonnet/high file identity remains old recorded observation, not retested here.
- `VRES_PERSISTENCE_WARNING` and `VRES_REPLY_GUARD_WARNING` unresolved; no Vres DB/task/persistence probe authorized.
- The exact real source of the 109-line output is an uploaded operator attachment; its original content digest is recorded above. This Markdown contains a safely line-normalized complete console copy, not a binary-original capture.

## 4. NEXT one INDEPENDENT Claude REPORT-ONLY evidence decision

Use a **SEPARATE Claude Code review session** or explicitly clean independent reviewer context. Supply (a) the complete original 109-line Windows console transcript (not merely our summary), (b) the prior C2-D1 complete STATIC_PASS report ending `VRES_165_C2_D1_INDEPENDENT_STATIC_REVIEW_COMPLETE`, and (c) exact pre-approved PowerShell script/context as needed. Claude must perform **REPORT-ONLY, ZERO TOOLS**: NO Read/Grep/Glob, Bash/Git/PowerShell, Python/pytest, MCP/Vres task, PostgreSQL even SELECT, provider, installed model/credentials/global Claude configuration, subagents, writes or test reruns. It must not infer SHA from pasted labels or certify physical no-contact.

Requested independent verdict exactly one: **OFFLINE_ACCEPT**, **OFFLINE_REJECT**, **EVIDENCE_BLOCKED**, for the pure D1 source/test offline boundary **358b3554075f87f5b8287fbb37d66fa95ad68b7c** ONLY. Reviewer must independently count actual printed PASSED IDs (74 expected from ChatGPT's separate audit, not to be assumed), check one echoed exact command, process `PYTHONPATH` scope restoration, expected pre/post identity labels, in-process fence unexpected refusals0/integration false, missing pytest printed aggregate/footer, potential 4097-space auto-ID anomaly, absence of shell errors and whether the remaining evidence limitations block acceptance. Reviewer must preserve all eight earlier informational issues and C2 V1 I-01..I-07; never promote denial-only static bytes, claimed publisher/reviews/hashes or operator label into positive installation authority.

If decision **OFFLINE_ACCEPT**, ChatGPT will evaluate exact report + marker, then commit a distinct docs-only acceptance handoff and advance index. If **OFFLINE_REJECT** or **EVIDENCE_BLOCKED**, preserve failed/pending SHA and exact limitations, do not rerun the same test without a new justified gate or edit source silently. Expected marker:

`VRES_165_C2_D1_INDEPENDENT_OFFLINE_EVALUATION_COMPLETE`

Even OFFLINE_ACCEPT would mean ONLY pure PERSONAL OFFLINE DENY-ONLY planner source/tests on this SHA; **NO real E/V/CAS/W, trusted publisher, installed policy-aware Chairman body, installation, model/provider activation or #165/F1 trusted release approval.**

## 5. Permanent holds, history and user-facing roadmap

- Original current-user installed release `20261022172833-4d82147b` last inspected READ-ONLY: Chairman Sonnet/high, LF, 24208 UTF-8 bytes, SHA256 `a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73`. Effective model in a running Claude session UNVERIFIED. Opus/medium UNINSTALLED; original frontmatter-only P2 Opus digest `b73e7497454a464f6b6bc1df00f42422696da786a07eb2936ae73ad73abedf54` is DIAGNOSTIC_ONLY_INVALID_FOR_INSTALLATION.
- Original #165/F1 protected trusted H0/Hn, last history L/governing G/pending Q, user event E, validator protected Fable/high V, nonce-consuming CAS, separate install warrant W, independent publisher/loader, physical model #169 OPEN. Prior B2B R3 only DENY-ONLY, C2 V1 R1 only DESIGN_ACCEPT; no positive trust issued here.
- LIVE_SCHEMA_048_INCIDENT=OPEN: absolutely NO PostgreSQL even SELECT. D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 blocked, L-04 OPEN, PA-01..08 incomplete. No Vres task state/bootstrap/doctor/health/hooks/database CLI or warning recovery probes.
- No credentials, vault/keyring, protected Fable, provider, native model switch, installer, signing, current-user/global Claude plugin/skills/config changes, PR/merge/release/main. USER_DECISION_ON_NON_F1_PERSONAL_EXPERIMENT=NOT_MADE.
- Accepted older C1 R1 7ac041... 29 observed Windows PASSED/exit0, C0 e6bd8... 34, A1 R2 9754b... 93/A1 R1 1b406... 71, B2A R3 328474... 95 with R3-PROC-01; old C1 c545556... pytest EXIT1 remains failed. C0-PROC-01 historical postrun ELSE error nonblocking and earlier B2B/B2A design/test rejections preserved.
- The complete V-01..V-42 PERSONAL delivery roadmap, Visual Studio legacy-project onboarding, project continuity, secure reusable current-user credential handles and production-readiness tasks remain open development, not installed or completed by this D1 offline test.

## Appendix A — Complete 109-line operator PowerShell transcript (line endings normalized for Git diff)

```text
=== VRES C2-D1 GUARDED OFFLINE TEST ===
PASS: Detached HEAD
PASS: Source HEAD
PASS: Source tree
PASS: Sole accepted parent
PASS: Blob src/vres_os/chairman_c2_offline_planner.py
PASS: Blob tests/test_chairman_c2_offline_planner.py
PASS: Blob src/vres_os/chairman_policy.py
PASS: Blob src/vres_os/chairman_selection_preview.py
PASS: Blob src/vres_os/chairman_selection_cli.py
PASS: Blob src/vres_os/chairman_b2b_denial_contract.py
PASS: Blob plugins/vres-os/agents/chairman.md
PASS: Blob tests/conftest.py
PASS: Blob pyproject.toml
PASS: Exactly two added D1 files
PASS: Source diff --check
PASS: Pre-test worktree clean
C2_D1_PREFLIGHT_PASS
PYTHONPATH_SCOPE=D1_SOURCE_ONLY
SELECTED_PYTEST_COMMAND=py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_c2_offline_planner.py
..........................................................................                                                             [100%]
================================================================== PASSES ===================================================================
LIVE APP-DATA FENCE: unexpected refusals=0 protected=['c:\\users\\user\\appdata\\local\\vresos', 'c:\\users\\user\\appdata\\roaming\\vresos'] trusted_temp_base=C:\Users\User\AppData\Local\Temp session_root=C:\Users\User\AppData\Local\Temp\vres-pytest-app-data-fq_tcyp0\VresOS init_order=['validate-temp-base', 'create-session-directory', 'validate-session-directory', 'create-app-data-root', 'enable-isolation'] removed_env=['GIT_ASKPASS'] integration_opt_in=False
========================================================== short test summary info ==========================================================
PASSED tests/test_chairman_c2_offline_planner.py::test_unverified_good_looking_input_is_indeterminate_not_a_permission
PASSED tests/test_chairman_c2_offline_planner.py::test_all_caller_claimed_reviews_are_untrusted_even_when_everything_matches
PASSED tests/test_chairman_c2_offline_planner.py::test_neither_baseline_nor_opus_policy_can_result_in_positive_authority[sonnet-claims0]
PASSED tests/test_chairman_c2_offline_planner.py::test_neither_baseline_nor_opus_policy_can_result_in_positive_authority[sonnet-claims1]
PASSED tests/test_chairman_c2_offline_planner.py::test_neither_baseline_nor_opus_policy_can_result_in_positive_authority[opus-claims0]
PASSED tests/test_chairman_c2_offline_planner.py::test_neither_baseline_nor_opus_policy_can_result_in_positive_authority[opus-claims1]
PASSED tests/test_chairman_c2_offline_planner.py::test_pure_renderer_preserves_caller_template_line_endings[lf]
PASSED tests/test_chairman_c2_offline_planner.py::test_pure_renderer_preserves_caller_template_line_endings[crlf]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_or_oversized_caller_template_is_refused_without_digest[]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_or_oversized_caller_template_is_refused_without_digest[not-a-template]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_or_oversized_caller_template_is_refused_without_digest[---\nname: chairman\n]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_or_oversized_caller_template_is_refused_without_digest[---\nname: validator\ndescription: x\nmodel: sonnet\neffort: high\n---\nbody\n]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_or_oversized_caller_template_is_refused_without_digest[---\nname: chairman\ndescription: x\nmodel: sonnet\neffort: high\n---\n]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_or_oversized_caller_template_is_refused_without_digest[---\nname: chairman\ndescription: x\nmodel: sonnet\nmodel: opus\neffort: high\n---\nbody\n]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_or_oversized_caller_template_is_refused_without_digest[---\nname: chairman\ndescription: x\nmodel: sonnet\neffort: high\n---\nbody\r\n]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_or_oversized_caller_template_is_refused_without_digest[\xff]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_or_oversized_caller_template_is_refused_without_digest[oversized-template]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_or_oversized_caller_template_is_refused_without_digest[not bytes]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_or_oversized_caller_template_is_refused_without_digest[template10]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[baseline-]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[baseline-not json]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[baseline-{}]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[baseline-[]]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[baseline-{"schema":"wrong","version":1,"family":"sonnet","effort":"high"}]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[baseline-{"effort":"high","family":"sonnet","schema":"vres-chairman-control/1"}]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[baseline-{"effort":"high","family":"auto","schema":"vres-chairman-control/1","version":1}]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[baseline-{"effort":"high","family":"sonnet","schema":"vres-chairman-control/1","version":true}]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[baseline-{"effort":"high","family":"sonnet","schema":"vres-chairman-control/1","family":"opus","version":1}]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[baseline-\xef\xbb\xbf{"effort":"high","family":"sonnet","schema":"vres-chairman-control/1","version":1}]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[baseline-                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 ]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[baseline-deep-json-nesting]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[baseline-{"effort":"high","family":"sonnet","schema":"vres-chairman-control/1","version":1}\n]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[baseline-{"schema":"vres-chairman-control/1","version":1,"family":"sonnet","effort":"high"}]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[proposed-]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[proposed-not json]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[proposed-{}]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[proposed-[]]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[proposed-{"schema":"wrong","version":1,"family":"sonnet","effort":"high"}]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[proposed-{"effort":"high","family":"sonnet","schema":"vres-chairman-control/1"}]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[proposed-{"effort":"high","family":"auto","schema":"vres-chairman-control/1","version":1}]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[proposed-{"effort":"high","family":"sonnet","schema":"vres-chairman-control/1","version":true}]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[proposed-{"effort":"high","family":"sonnet","schema":"vres-chairman-control/1","family":"opus","version":1}]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[proposed-\xef\xbb\xbf{"effort":"high","family":"sonnet","schema":"vres-chairman-control/1","version":1}]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[proposed-                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 ]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[proposed-deep-json-nesting]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[proposed-{"effort":"high","family":"sonnet","schema":"vres-chairman-control/1","version":1}\n]
PASSED tests/test_chairman_c2_offline_planner.py::test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally[proposed-{"schema":"vres-chairman-control/1","version":1,"family":"sonnet","effort":"high"}]
PASSED tests/test_chairman_c2_offline_planner.py::test_untyped_claims_cannot_become_a_review_approval[None]
PASSED tests/test_chairman_c2_offline_planner.py::test_untyped_claims_cannot_become_a_review_approval[False]
PASSED tests/test_chairman_c2_offline_planner.py::test_untyped_claims_cannot_become_a_review_approval[value2]
PASSED tests/test_chairman_c2_offline_planner.py::test_untyped_claims_cannot_become_a_review_approval[claim]
PASSED tests/test_chairman_c2_offline_planner.py::test_untyped_claims_cannot_become_a_review_approval[value4]
PASSED tests/test_chairman_c2_offline_planner.py::test_corrupted_frozen_claims_are_revalidated_at_call_boundary
PASSED tests/test_chairman_c2_offline_planner.py::test_same_sha_under_wrong_digest_purpose_is_refused_not_converted[RENDERED_CANDIDATE]
PASSED tests/test_chairman_c2_offline_planner.py::test_same_sha_under_wrong_digest_purpose_is_refused_not_converted[RELEASE]
PASSED tests/test_chairman_c2_offline_planner.py::test_mismatching_caller_template_sha_is_refused_even_with_claimed_review
PASSED tests/test_chairman_c2_offline_planner.py::test_untyped_or_bad_claimed_digest_is_neutral_refusal[hash]
PASSED tests/test_chairman_c2_offline_planner.py::test_untyped_or_bad_claimed_digest_is_neutral_refusal[False]
PASSED tests/test_chairman_c2_offline_planner.py::test_untyped_or_bad_claimed_digest_is_neutral_refusal[None]
PASSED tests/test_chairman_c2_offline_planner.py::test_untyped_or_bad_claimed_digest_is_neutral_refusal[bad3]
PASSED tests/test_chairman_c2_offline_planner.py::test_untyped_or_bad_claimed_digest_is_neutral_refusal[bad4]
PASSED tests/test_chairman_c2_offline_planner.py::test_constructing_invalid_typed_digest_refuses[SUPPLIED_TEMPLATE-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa]
PASSED tests/test_chairman_c2_offline_planner.py::test_constructing_invalid_typed_digest_refuses[SUPPLIED_TEMPLATE-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA]
PASSED tests/test_chairman_c2_offline_planner.py::test_constructing_invalid_typed_digest_refuses[SUPPLIED_TEMPLATE-000000000000000000000000000000000000000000000000000000000000000]
PASSED tests/test_chairman_c2_offline_planner.py::test_constructing_invalid_typed_digest_refuses[SUPPLIED_TEMPLATE-True]
PASSED tests/test_chairman_c2_offline_planner.py::test_reported_baseline_disagreement_refuses_without_source_discovery
PASSED tests/test_chairman_c2_offline_planner.py::test_known_sonnet_default_doctrine_refuses_even_if_claimed_reviewed[claims0-p2-sonnet]
PASSED tests/test_chairman_c2_offline_planner.py::test_known_sonnet_default_doctrine_refuses_even_if_claimed_reviewed[claims0-opus-not-shell]
PASSED tests/test_chairman_c2_offline_planner.py::test_known_sonnet_default_doctrine_refuses_even_if_claimed_reviewed[claims1-p2-sonnet]
PASSED tests/test_chairman_c2_offline_planner.py::test_known_sonnet_default_doctrine_refuses_even_if_claimed_reviewed[claims1-opus-not-shell]
PASSED tests/test_chairman_c2_offline_planner.py::test_known_doctrine_case_variants_conservatively_refuse
PASSED tests/test_chairman_c2_offline_planner.py::test_old_doctrine_does_not_claim_a_runtime_model_from_sonnet_noop
PASSED tests/test_chairman_c2_offline_planner.py::test_result_types_are_frozen_closed_and_never_truthy
PASSED tests/test_chairman_c2_offline_planner.py::test_module_has_only_closed_negative_api_and_no_side_effect_surface
PYTEST_EXIT_CODE=0
PASS: PYTHONPATH_RESTORED
=== C2-D1 POST-TEST INTEGRITY ===
PASS: Post-test HEAD
PASS: Post-test tree
PASS: Post-test blob src/vres_os/chairman_c2_offline_planner.py
PASS: Post-test blob tests/test_chairman_c2_offline_planner.py
PASS: Post-test worktree clean
C2_D1_WINDOWS_TEST_EXECUTION_PASS_PENDING_INDEPENDENT_EVALUATION
VRES_165_C2_D1_WINDOWS_SELECTED_TEST_EXECUTION_COMPLETE
PS C:\Users\User>
```
