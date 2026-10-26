# Vres-OS #165 — A1 R2 personal Windows offline test EXECUTION PASS; independent evaluator pending

**Date:** 2026-10-26, Europe/Athens.
**Repository:** vosser24/Vres-OS.
**Canonical docs branch:** docs/chatgpt-continuity-20261023.
**Source branch:** feature/165-chairman-policy-foundation-20261023.
**Evidence:** exact full **117-line** text pasted by the user after running the already approved R2 PowerShell preflight and **ONE** selected offline pytest command, reproduced verbatim in §7 below.
**Evidence-scoped status:** **OPERATOR_WINDOWS_OFFLINE_TEST_EXECUTION_PASS / 93 individually observed PASSED lines / PYTEST_EXIT_CODE=0 / INDEPENDENT_CLAUDE_TEST_EVALUATION_NOT_RUN / A1 R2 OFFLINE_ACCEPT_NOT_YET_GRANTED**.
**Scope:** personal single-user Vres-OS offline denial-only reliability, not a published security product. No model activation, native permit, installer, signing, credential access, protected external authority or production-ready statement follows from this test.

## 0. Read-first precedence and exact continuation

Read current docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md first, then THIS newest operator Windows test evidence. Supporting history:
1. docs/handoffs/VRES-165-B2B1-A1-R2-INDEPENDENT-STATIC-PASS-AND-PERSONAL-OFFLINE-TEST-GATE-2026-10-26.md — separate independent Claude STATIC_PASS, zero blocking / five informational.
2. docs/handoffs/VRES-165-B2B1-A1-R2-PERSONAL-WINDOWS-SOURCE-WORKTREE-READY-2026-10-26.md — operator verified a **NEW detached R2** checkout and Git identities; not old R1.
3. docs/handoffs/VRES-165-B2B1-A1-R2-PERSONAL-OFFLINE-CONSISTENCY-SOURCE-CANDIDATE-2026-10-26.md — two-file source candidate.
4. docs/handoffs/VRES-165-B2B1-A1-R1-INDEPENDENT-OFFLINE-ACCEPT-AND-A1-R2-HARDENING-HANDOFF-2026-10-26.md — historically accepted separate R1 SHA/71 observed PASS lines.
5. Historical R3 DENY-ONLY architecture independent DESIGN_ACCEPT, mandatory erratum, old B2A R3 source acceptance and previous rejections.

**NEXT GATE:** start a **FRESH Claude Code session in the ALREADY EXISTING R2 folder** C:\Projects\Vres-ChatGPT-Review-165B2B1-A1-R2-20261026 and submit a **REPORT-ONLY EVIDENCE EVALUATION** of this operator text (§7). Do not reuse an A1 R1 or B2B R3 Claude Code session or run another test. Require independent \`OFFLINE_ACCEPT\` / \`OFFLINE_REJECT\` / \`EVIDENCE_BLOCKED\` expressly limited to this R2 pure offline DENY-ONLY source/test SHA. Claude must distinguish evaluation of the text from verification of actual Windows host/network actions.

Operator convenience, using PowerShell:

    Set-Location -LiteralPath "C:\Projects\Vres-ChatGPT-Review-165B2B1-A1-R2-20261026"
    claude

The folder **already exists**, is a clean detached Git worktree and must NOT be recreated with mkdir, git worktree add, git fetch or reset. For VS Code: File > Open Folder, select that same R2 path; open terminal there and run claude. Avoid \`claude --resume\` for the old R1 reviewer because it could read stale context.

## 1. Exact source identity / accepted parent / protected isolated test configuration

| Identity | Verified GitHub / operator-supplied value |
| --- | --- |
| NEW A1 R2 candidate | **9754b190083a0ada757ebee07f2ef5b8f312b58e** |
| Source tree | **5372c5ecdc7c6ebbb0cbc9956288250255e7db4e** |
| Independently OFFLINE_ACCEPTED R1 parent | **1b406c788057f0cb2a8a57578b89110a11b76161** |
| Changed module | src/vres_os/chairman_b2b_denial_contract.py |
| Module blob | **b7c7e9871f669f6420eed8b20e77fe76e44a489f** |
| Changed selected tests | tests/test_chairman_b2b_denial_contract.py |
| Tests blob | **8090e8517aedf510cbd76033442540f7113ed0a3** |
| Protected tests/conftest.py blob | **1c33bb206dbf42691a6af9a709514bf3cc9994af** |
| pyproject.toml blob | **b2d5e30d10d7be0613e90bf3ed1e346be5678969** |
| Windows R2 worktree | C:\Projects\Vres-ChatGPT-Review-165B2B1-A1-R2-20261026 |

The feature SHA is one commit above independently accepted R1. The net source delta is exactly TWO modified files: the claimed-evidence evaluator plus the negative test module; accepted B1/B2A, protected conftest, dependency metadata, CLI/bootstrap/installed Vres are unchanged. GitHub HEAD/tree/blobs and parent were independently verified by ChatGPT prior to the Windows test. Local PowerShell checks are operator-supplied evidence, not independently observed Git operations by Claude.

A1 R2 is intended to reject internal inconsistencies in **UNVERIFIED** user-supplied old B1 prefix claims, distinguish earlier completed governing G from latest L and snapshot candidate bytes once. None of these are authorized trusted operator events, privileged model changes or installer decisions. A1 R1's separate OFFLINE_ACCEPT is preserved at its prior SHA, NOT automatically transferred to R2.

## 2. ONE selected R2 Windows pytest: exact observed evidence

The operator supplied a transcript with **117 file lines** and no reported STOP:
- Seven explicit preflight PASS lines for R2 HEAD, R2 tree, accepted R1 parent, R2 production source blob, corrected test blob, protected conftest blob and pyproject blob, followed by \`PREFLIGHT_PASS\` and the full source SHA.
- The approved command is **now echoed verbatim in the Windows output**, unlike the earlier R1 transcript:

      PYTEST_COMMAND=py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_b2b_denial_contract.py

- Progress dots end with \`[100%]\`. The \`-rA\` output contains exactly **93 lines individually prefixed** \`PASSED tests/test_chairman_b2b_denial_contract.py::\`. The original 71 reported R1 cases remain covered in this file along with new R2 tests, but only the exact output proves this run's selected test IDs.
- No FAILED, ERROR, SKIP, XFAIL, XPASS, unhandled exception, pytest warning or connection-tripwire failure line is visible in the provided transcript.
- \`LIVE APP-DATA FENCE: unexpected refusals=0\`, protected Local/Roaming VresOS paths, trusted Local Temp base, session-only disposable directory, expected isolation init order, \`removed_env=['GIT_ASKPASS']\`, and **\`integration_opt_in=False\`**. This is an in-process audit/fixture fence, NOT OS-level sandbox/network-attestation proof.
- \`PYTEST_EXIT_CODE=0\` is recorded immediately after the explicitly echoed single invocation, as captured by the operator's PowerShell wrapper; do not mislabel it as a line emitted by pytest.
- Post-test marker section includes \`PASS: Post-test R2 HEAD\`, \`PASS: Post-test R2 tree\`, \`POST_RUN_WORKTREE_CLEAN\`, and final \`VRES_165_B2B1_A1_R2_OFFLINE_TEST_EXECUTION_COMPLETE\`.
- There is **NO separate pytest total/collected footer** such as \`93 passed in Ns\` or \`93 collected\`. The number 93 is the counted individual PASSED lines, **not a printed summary count**. No test duration or number deselected is established.
- Exactly ONE pytest invocation section is shown and there is no extra interpreter version probe (previous historical B2A R3-PROC-01 was distinct), retry, broad integration suite, actual credentials/vault, PostgreSQL, provider or installed model call visible. The operator transcript cannot prove that no other external OS event happened outside its capture.
- No source worktree changes, git commit/push, PR, release, installer or runtime activation are evidenced.
- **This is an OPERATOR test execution PASS, NOT yet the independent Claude test-evaluator acceptance**. Do not label A1 R2 as final OFFLINE_ACCEPT until the next independent evidence-only reviewer issues it.

## 3. Previously independent A1 R2 STATIC_PASS, informational findings and correct isolation scope

The prior Claude STATIC_PASS reviewed full R2 implementation and test files, full 1513-line tests/conftest.py, accepted B1 policy/history, Grep-only B2A expectation definitions/imports and pyproject pytest config. Its session CWD happened to be the **old R1** worktree, but Claude used explicit complete **R2 paths** and did not modify either checkout.

The independent reviewer found **zero BLOCKING** and five INFORMATIONAL observations, none a reason to invent a runtime security breach:
- I-1: defensive unreachable exception handler around B1 prefix reconstruction.
- I-2: redundant new successor's supersedes digest comparison after B1's whole-chain validation.
- I-3: no additional p>=2 middle-history fork case although canonical prefix equality covers it.
- I-4: mutation test checks digest mismatch rather than instrumenting exact attribute-read count, which was statically one.
- I-5: minor blank lines/formatting near 100 chars; Ruff not executed.

Reviewer concluded no apparent I/O or privilege access from source/test, process-level protected-data fence and Vres/psycopg tripwires appropriate for the selected test. This is based on **static reading**, not physically verified zero network traffic. Claimed prior prefix and G comparisons remain caller-supplied and may at best reject internal contradictions; matching still yields only Indeterminate, NEVER permission. Maintain easy-to-understand personal-use safety, not multi-tenant enterprise trust claims.

## 4. NEXT independent Claude evidence-only assessment, without re-running anything

The user should open a fresh Claude Code session in the **existing R2** worktree, using the simple PowerShell command in §0. Give Claude this exact source target and the **whole transcript §7**; no need for any Git or pytest execution, network browsing or Vres task action.

Require a single closed evidence verdict \`OFFLINE_ACCEPT\`, \`OFFLINE_REJECT\`, or \`EVIDENCE_BLOCKED\`, with:
1. Quote the full SHA and disclose that local Git identity is operator-provided, previously verified independently against remote GitHub by ChatGPT, NOT verified by Claude through Git.
2. Count each \`PASSED ...\` line; preserve actual 93 and distinguish from absent printed collected/closing summary. Check command echo, progress, no FAIL/ERROR/SKIP, wrapper exit=0, app-data fence (unexpected=0 / integration_opt_in=False) and post-run unchanged HEAD/tree/porcelain.
3. Consider the prior independent STATIC_PASS and I-1..I-5 strictly INFORMATIONAL. Assess whether the single selected personal offline test evidence suffices for **A1 R2 offline denial-only acceptance only**, subject to disclosed logging/in-process limits.
4. Note no OS-level network attestation, no physical PostgreSQL proof, no native trusted event/installer/model approval. Original F1/#165, original Vres reply-guard task persistence warning remain OPEN.
5. Report \`NO_TEST_RERUN\`, \`NO_SOURCE_MODIFICATION\`, \`NO_AUTHORITY_ISSUED\`, \`NO_MODEL_ACTIVATION\`, \`NO_POSTGRESQL_CONTACT_BY_REVIEWER\`.
6. Finish with marker \`VRES_165_B2B1_A1_R2_INDEPENDENT_OFFLINE_EVALUATION_COMPLETE\`.

On OFFLINE_REJECT or EVIDENCE_BLOCKED, preserve failures/limits without resetting or running tests. On OFFLINE_ACCEPT, preserve as A1 R2 personal offline source/test accepted at the exact SHA, then create a distinct docs-only verdict handoff. There is no authority to automatically enable real model switching, protected Fable, installer or global Claude configuration.

## 5. Hold boundaries, legacy continuity and reporting honesty

- **LIVE_SCHEMA_048_INCIDENT=OPEN**: no PostgreSQL contact, **not even SELECT**, no self-healing Vres database/driver probe. D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 blocked, L-04 OPEN, PA-01..08 pending.
- Original #165 **F1 external authenticated operator/anchored policy and protected validator** remain OPEN; these personal offline checks do not claim that authority. No real vault/credentials/keyring/global Claude hooks/settings modifications, privileged provider calls, native signing, installer, active Chairman switch, physical host #169 observation, PR/main merge or production release without separate explicit authorization.
- Installed personal Vres release \`20261022172833-4d82147b\` from original P2 \`82c82430b38f93bd6b9d5c3af3b5de9c1368af9c\` stays Chairman **Sonnet/high**; Opus/medium remains **UNINSTALLED candidate**.
- Prior independent A1 R1 OFFLINE_ACCEPT: source SHA \`1b406c788057f0cb2a8a57578b89110a11b76161\`, 71 individually printed PASS lines, exit 0, missing command echo/printed count in that historical output. Historic B2A R3 accepted 95 individual PASS lines, exit0, R3-PROC-01 extra interpreter-version probe; B2A R2 and initial static REJECTs, B2B designs v0/R1/R2 DESIGN_REVISE, R3 DESIGN_ACCEPT only OFFLINE DENY-ONLY; Phase A R2/B1/F2/P2-A1 per-SHA accepted/rejected history, full original V-01..V-42 roadmap remain unchanged.
- \`VRES_REPLY_GUARD_WARNING\` previously shown by Claude STOP hook means authoritative Vres task persistence is unverified; this Windows test transcript does not heal that warning. GitHub docs/commit SHAs remain the durable continuity.

## 6. Documents-only commit and exact next-session handoff

Commit this NEW file plus a MODIFICATION to docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md on canonical docs branch **docs/chatgpt-continuity-20261023** atop last verified docs SHA \`48d5bab5e1096f42d24b6f765d0bf077e89b5643\`. There must be ONLY these two docs changes; parent HEAD/tree, both blobs, unchanged source branch SHA must be verified and docs ref advanced nonforced with expected-old-SHA. Do not create a new product source commit or run any tool/pytest on the user host to write these docs.

**New-session resume:** source A1 R2 SHA **9754b190083a0ada757ebee07f2ef5b8f312b58e**, tree **5372c5ecdc7c6ebbb0cbc9956288250255e7db4e**, last independently accepted R1 parent \`1b406c788057f0cb2a8a57578b89110a11b76161\`; two modified files with source blob \`b7c7e9871f669f6420eed8b20e77fe76e44a489f\` and test blob \`8090e8517aedf510cbd76033442540f7113ed0a3\`. NEW R2 Windows detached worktree already READY/clean, Claude independently STATIC_PASS five informational I-1..I-5, user executed ONE selected R2 pytest, **93 observed PASSED test IDs, EXIT 0, command echoed, unexpected refusals 0, integration opt-in false, post-run clean**, printed collection/footer absent. **NEXT independent Claude evidence-only report** at exact R2 SHA, with no rerun; source R2 OFFLINE_ACCEPT pending. User needs only open existing R2 folder (\`Set-Location -LiteralPath "C:\Projects\Vres-ChatGPT-Review-165B2B1-A1-R2-20261026"; claude), NOT create a new R2 Git folder or reuse R1 session. Personal use scope avoids unnecessary product-grade security ceremony, but LIVE_SCHEMA_048 no PostgreSQL, credentials, real provider, model installer and main holds remain. Preserve Vres reply-warning task uncertainty.

## 7. COMPLETE unmodified operator-supplied 117-line Windows PowerShell transcript

The following is the **full raw file content from this user message**. Keep exact lines and do not infer any additional output omitted from it. It does not independently authenticate OS traffic or installed-model state.

\`\`\`text
=== A1 R2 WINDOWS OFFLINE TEST PREFLIGHT ===
PASS: R2 HEAD
PASS: R2 tree
PASS: Accepted R1 parent
PASS: R2 source blob
PASS: R2 test blob
PASS: Offline isolation blob
PASS: Pytest configuration blob
PREFLIGHT_PASS
R2_SOURCE_SHA=9754b190083a0ada757ebee07f2ef5b8f312b58e
=== EXACTLY ONE SELECTED OFFLINE PYTEST RUN ===
PYTEST_COMMAND=py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_b2b_denial_contract.py
.............................................................................................                                          [100%]
================================================================== PASSES ===================================================================
LIVE APP-DATA FENCE: unexpected refusals=0 protected=['c:\\users\\user\\appdata\\local\\vresos', 'c:\\users\\user\\appdata\\roaming\\vresos'] trusted_temp_base=C:\Users\User\AppData\Local\Temp session_root=C:\Users\User\AppData\Local\Temp\vres-pytest-app-data-qrg7iz3j\VresOS init_order=['validate-temp-base', 'create-session-directory', 'validate-session-directory', 'create-app-data-root', 'enable-isolation'] removed_env=['GIT_ASKPASS'] integration_opt_in=False
========================================================== short test summary info ==========================================================
PASSED tests/test_chairman_b2b_denial_contract.py::test_genesis_is_typed_and_never_a_fake_empty_b1_history
PASSED tests/test_chairman_b2b_denial_contract.py::test_g_is_not_inferred_from_latest_history_and_epoch_is_distinct_from_count
PASSED tests/test_chairman_b2b_denial_contract.py::test_evidence_digests_are_domain_separated_from_legacy_b1_and_each_other
PASSED tests/test_chairman_b2b_denial_contract.py::test_round_trip_anchor_is_strict_canonical_ascii_and_no_text_is_echoed
PASSED tests/test_chairman_b2b_denial_contract.py::test_alternate_or_malformed_anchor_bytes_always_refuse[key-order]
PASSED tests/test_chairman_b2b_denial_contract.py::test_alternate_or_malformed_anchor_bytes_always_refuse[escaped-ascii]
PASSED tests/test_chairman_b2b_denial_contract.py::test_alternate_or_malformed_anchor_bytes_always_refuse[trailing-newline]
PASSED tests/test_chairman_b2b_denial_contract.py::test_alternate_or_malformed_anchor_bytes_always_refuse[bom]
PASSED tests/test_chairman_b2b_denial_contract.py::test_alternate_or_malformed_anchor_bytes_always_refuse[leading-space]
PASSED tests/test_chairman_b2b_denial_contract.py::test_alternate_or_malformed_anchor_bytes_always_refuse[duplicate]
PASSED tests/test_chairman_b2b_denial_contract.py::test_alternate_or_malformed_anchor_bytes_always_refuse[deep-json]
PASSED tests/test_chairman_b2b_denial_contract.py::test_alternate_or_malformed_anchor_bytes_always_refuse[oversized]
PASSED tests/test_chairman_b2b_denial_contract.py::test_alternate_or_malformed_anchor_bytes_always_refuse[non-utf8]
PASSED tests/test_chairman_b2b_denial_contract.py::test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse[<lambda>0]
PASSED tests/test_chairman_b2b_denial_contract.py::test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse[<lambda>1]
PASSED tests/test_chairman_b2b_denial_contract.py::test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse[<lambda>2]
PASSED tests/test_chairman_b2b_denial_contract.py::test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse[<lambda>3]
PASSED tests/test_chairman_b2b_denial_contract.py::test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse[<lambda>4]
PASSED tests/test_chairman_b2b_denial_contract.py::test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse[<lambda>5]
PASSED tests/test_chairman_b2b_denial_contract.py::test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse[<lambda>6]
PASSED tests/test_chairman_b2b_denial_contract.py::test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse[<lambda>7]
PASSED tests/test_chairman_b2b_denial_contract.py::test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse[<lambda>8]
PASSED tests/test_chairman_b2b_denial_contract.py::test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse[<lambda>9]
PASSED tests/test_chairman_b2b_denial_contract.py::test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse[<lambda>10]
PASSED tests/test_chairman_b2b_denial_contract.py::test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse[<lambda>11]
PASSED tests/test_chairman_b2b_denial_contract.py::test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse[<lambda>12]
PASSED tests/test_chairman_b2b_denial_contract.py::test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse[<lambda>13]
PASSED tests/test_chairman_b2b_denial_contract.py::test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse[<lambda>14]
PASSED tests/test_chairman_b2b_denial_contract.py::test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse[<lambda>15]
PASSED tests/test_chairman_b2b_denial_contract.py::test_anchor_epoch_is_exact_bounded_integer[True]
PASSED tests/test_chairman_b2b_denial_contract.py::test_anchor_epoch_is_exact_bounded_integer[-1]
PASSED tests/test_chairman_b2b_denial_contract.py::test_anchor_epoch_is_exact_bounded_integer[9223372036854775808]
PASSED tests/test_chairman_b2b_denial_contract.py::test_anchor_epoch_is_exact_bounded_integer[0]
PASSED tests/test_chairman_b2b_denial_contract.py::test_anchor_epoch_is_exact_bounded_integer[1.5]
PASSED tests/test_chairman_b2b_denial_contract.py::test_proposal_count_cannot_be_bool_or_out_of_range[True]
PASSED tests/test_chairman_b2b_denial_contract.py::test_proposal_count_cannot_be_bool_or_out_of_range[-1]
PASSED tests/test_chairman_b2b_denial_contract.py::test_proposal_count_cannot_be_bool_or_out_of_range[129]
PASSED tests/test_chairman_b2b_denial_contract.py::test_proposal_count_cannot_be_bool_or_out_of_range[1]
PASSED tests/test_chairman_b2b_denial_contract.py::test_proposal_count_cannot_be_bool_or_out_of_range[1.1]
PASSED tests/test_chairman_b2b_denial_contract.py::test_typed_digests_refuse_all_zero_uppercase_bad_length_and_wrong_types[0000000000000000000000000000000000000000000000000000000000000000]
PASSED tests/test_chairman_b2b_denial_contract.py::test_typed_digests_refuse_all_zero_uppercase_bad_length_and_wrong_types[FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
PASSED tests/test_chairman_b2b_denial_contract.py::test_typed_digests_refuse_all_zero_uppercase_bad_length_and_wrong_types[aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa]
PASSED tests/test_chairman_b2b_denial_contract.py::test_typed_digests_refuse_all_zero_uppercase_bad_length_and_wrong_types[123]
PASSED tests/test_chairman_b2b_denial_contract.py::test_typed_digests_refuse_all_zero_uppercase_bad_length_and_wrong_types[None]
PASSED tests/test_chairman_b2b_denial_contract.py::test_non_genesis_needs_two_real_shape_digests_and_g_cannot_point_forward
PASSED tests/test_chairman_b2b_denial_contract.py::test_candidate_raw_b1_must_equal_accepted_history_to_document[key-order]
PASSED tests/test_chairman_b2b_denial_contract.py::test_candidate_raw_b1_must_equal_accepted_history_to_document[literal-unicode]
PASSED tests/test_chairman_b2b_denial_contract.py::test_candidate_raw_b1_must_equal_accepted_history_to_document[trailing-newline]
PASSED tests/test_chairman_b2b_denial_contract.py::test_candidate_raw_b1_must_equal_accepted_history_to_document[bom]
PASSED tests/test_chairman_b2b_denial_contract.py::test_candidate_raw_b1_must_equal_accepted_history_to_document[duplicate]
PASSED tests/test_chairman_b2b_denial_contract.py::test_candidate_raw_b1_must_equal_accepted_history_to_document[empty]
PASSED tests/test_chairman_b2b_denial_contract.py::test_candidate_raw_b1_must_equal_accepted_history_to_document[genesis-zero-entry]
PASSED tests/test_chairman_b2b_denial_contract.py::test_candidate_raw_b1_must_equal_accepted_history_to_document[oversized]
PASSED tests/test_chairman_b2b_denial_contract.py::test_pending_and_recovery_both_block_without_clearing_or_authorizing[PENDING]
PASSED tests/test_chairman_b2b_denial_contract.py::test_pending_and_recovery_both_block_without_clearing_or_authorizing[RECOVERY]
PASSED tests/test_chairman_b2b_denial_contract.py::test_claimed_successor_count_is_exact_but_not_a_trust_head_check
PASSED tests/test_chairman_b2b_denial_contract.py::test_canonical_prefix_match_still_is_not_external_authority
PASSED tests/test_chairman_b2b_denial_contract.py::test_valid_fork_with_identical_count_is_refused_against_claimed_prior[different-root-policy]
PASSED tests/test_chairman_b2b_denial_contract.py::test_valid_fork_with_identical_count_is_refused_against_claimed_prior[modified-first-reason]
PASSED tests/test_chairman_b2b_denial_contract.py::test_wrong_claimed_prior_identity_refuses_even_for_correct_linked_history[history_sha256]
PASSED tests/test_chairman_b2b_denial_contract.py::test_wrong_claimed_prior_identity_refuses_even_for_correct_linked_history[latest_proposal_sha256]
PASSED tests/test_chairman_b2b_denial_contract.py::test_governing_older_or_latest_must_match_prior_proposal_sha[1]
PASSED tests/test_chairman_b2b_denial_contract.py::test_governing_older_or_latest_must_match_prior_proposal_sha[2]
PASSED tests/test_chairman_b2b_denial_contract.py::test_genesis_rejects_a_well_shaped_but_nonexistent_governing_b1_entry
PASSED tests/test_chairman_b2b_denial_contract.py::test_non_genesis_explicitly_refuses_zero_filled_sha[history_sha256]
PASSED tests/test_chairman_b2b_denial_contract.py::test_non_genesis_explicitly_refuses_zero_filled_sha[latest_proposal_sha256]
PASSED tests/test_chairman_b2b_denial_contract.py::test_every_assessment_argument_requires_an_exact_typed_claim[0-None]
PASSED tests/test_chairman_b2b_denial_contract.py::test_every_assessment_argument_requires_an_exact_typed_claim[1-None]
PASSED tests/test_chairman_b2b_denial_contract.py::test_every_assessment_argument_requires_an_exact_typed_claim[2-None]
PASSED tests/test_chairman_b2b_denial_contract.py::test_every_assessment_argument_requires_an_exact_typed_claim[3-None]
PASSED tests/test_chairman_b2b_denial_contract.py::test_every_assessment_argument_requires_an_exact_typed_claim[4-None]
PASSED tests/test_chairman_b2b_denial_contract.py::test_every_assessment_argument_requires_an_exact_typed_claim[0-False]
PASSED tests/test_chairman_b2b_denial_contract.py::test_every_assessment_argument_requires_an_exact_typed_claim[1-False]
PASSED tests/test_chairman_b2b_denial_contract.py::test_every_assessment_argument_requires_an_exact_typed_claim[2-invalid7]
PASSED tests/test_chairman_b2b_denial_contract.py::test_every_assessment_argument_requires_an_exact_typed_claim[3-False]
PASSED tests/test_chairman_b2b_denial_contract.py::test_every_assessment_argument_requires_an_exact_typed_claim[4-invalid9]
PASSED tests/test_chairman_b2b_denial_contract.py::test_candidate_bytes_changed_after_digest_snapshot_refuse_without_authority
PASSED tests/test_chairman_b2b_denial_contract.py::test_reason_codes_are_information_not_a_consumer_permission
PASSED tests/test_chairman_b2b_denial_contract.py::test_pending_variants_are_closed_and_wrong_digest_domains_refuse
PASSED tests/test_chairman_b2b_denial_contract.py::test_cross_user_target_or_release_claims_refuse_instead_of_approving[user]
PASSED tests/test_chairman_b2b_denial_contract.py::test_cross_user_target_or_release_claims_refuse_instead_of_approving[target]
PASSED tests/test_chairman_b2b_denial_contract.py::test_cross_user_target_or_release_claims_refuse_instead_of_approving[release]
PASSED tests/test_chairman_b2b_denial_contract.py::test_cross_purpose_hash_and_digest_changes_refuse_even_with_same_sha_shape
PASSED tests/test_chairman_b2b_denial_contract.py::test_matching_attacker_controlled_claims_still_yield_only_indeterminate
PASSED tests/test_chairman_b2b_denial_contract.py::test_refusal_is_also_non_truthy_non_authorizing_and_codes_are_closed
PASSED tests/test_chairman_b2b_denial_contract.py::test_frozen_slots_and_corruption_revalidation_fail_closed
PASSED tests/test_chairman_b2b_denial_contract.py::test_low_level_candidate_mutation_and_missing_slots_never_authorize
PASSED tests/test_chairman_b2b_denial_contract.py::test_incorrect_api_input_shapes_are_refused_without_raising_untrusted_text[None]
PASSED tests/test_chairman_b2b_denial_contract.py::test_incorrect_api_input_shapes_are_refused_without_raising_untrusted_text[False]
PASSED tests/test_chairman_b2b_denial_contract.py::test_incorrect_api_input_shapes_are_refused_without_raising_untrusted_text[bad2]
PASSED tests/test_chairman_b2b_denial_contract.py::test_incorrect_api_input_shapes_are_refused_without_raising_untrusted_text[unverified]
PASSED tests/test_chairman_b2b_denial_contract.py::test_incorrect_api_input_shapes_are_refused_without_raising_untrusted_text[0]
PASSED tests/test_chairman_b2b_denial_contract.py::test_module_has_no_positive_provider_installer_or_privileged_import_surface
PYTEST_EXIT_CODE=0
=== POST-TEST INTEGRITY ===
PASS: Post-test R2 HEAD
PASS: Post-test R2 tree
POST_RUN_WORKTREE_CLEAN
TEST_EXIT_ZERO_PENDING_INDEPENDENT_EVALUATION
VRES_165_B2B1_A1_R2_OFFLINE_TEST_EXECUTION_COMPLETE
PS C:\Users\User> 
\`\`\`
