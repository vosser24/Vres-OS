# E7 Boundary 4B — E1 security hardening findings (2026-10-08, reconciled 2026-10-09)

Status as of the evidence cut (2026-10-09): descriptive evidence only. **This document is not the authoritative source of
validation status**; the authoritative acceptance record is the Vres validation ledger for the exact artifact manifest.
Validation history is in section 7. The fresh full live B4B adversarial replay on the corrected product has **not yet been
performed**, so live B4B GREEN is not claimed here.
Supersedes the narrow candidate in `EXPERIENCE-INTELLIGENCE-E7-B4B-REDACTION-HARDENING-ADDENDUM-2026-10-08.md`
(history retained there; the addendum is the earlier, narrower step and is not the current authority).
The original live RED (`c3a7f23`, `no_secret_persistence`) **remains historically valid** and its artifact is untouched.
Canonical contract: the E1 security hardening addendum on the docs branch (`a8346f7`), neither overwritten nor reinterpreted here.

Labels: **[F]** fact observed and read in this work, **[I]** interpretation, **[U]** unresolved / not verified.

## 1. Sequence of events
1. **[F] Original live RED** at `c3a7f23`: adversarial cohort stopped on `no_secret_persistence`. The frozen objective states
   "the service key <<CANARY_1>>" and E1 `capture` persisted the value as `sanitized`.
2. **[F] First candidate (`1693075`, committed)**: one `_PHRASE` rule for `service|secret|signing|encryption|master key`
   in `redaction.py` plus an addendum. Narrow, unit-level only.
3. **[F] Hardening candidate (changes after `1693075`, described here)**: closed whole-word qualifier vocabulary x `key|secret|token|credential`
   in the single owner `redaction.py`; one behaviour for phrase, key/value, residual postcondition and structured keys
   (`is_secret_key` single owner; the duplicate suffix tuple in `experience.py` removed); `begin_task` fail-closed on residual.
4. **[F] Isolated PostgreSQL setup and DryRun**: dedicated native PG 18.6 cluster on 127.0.0.1:55432 via the ignored launcher
   `.vres/local-tools/e7-b4b-hardening-integration.ps1` and helper `e7_b4b_integration_fixture.py`. Cluster identity check
   PASS, migration head `046_experience_retrieval_policy_v5.sql`, disposable database/roles/data dir, cleanup zero.
5. **[F] First integration result: 130 of 131 passed**, one failure in the new security test.
6. **[F] Test raw-INSERT discovery**: the failing test wrote the canary into `orchestration_work_units.last_error` with a
   raw `INSERT`, bypassing the product ingress. The canary was therefore a persisted canary created by test construction,
   not a product defect. The test now produces the failed unit through the public `OrchestrationService.fail_work_unit`
   (the real owner of `last_error`), matching the live artifact path (`via: public_fail_work_unit`). The raw-row case is kept
   only as an explicit legacy defence-in-depth test.
7. **[F] Result after correcting the test: 149/149.**
8. **[F] Residual-only risk found**: `fail_work_unit` used `redact_text`, which covers recognised secrets only. A probe showed
   `sk_test_`, `rk_live_`, `AKIA...`, `xoxb-...`, and `auth=<value>` pass `redact_text` unchanged while `sanitize_text` flags
   them as residual. Such a message would have been persisted in `last_error`.
9. **[F] `fail_work_unit` fix**: use `sanitize_text`; if residual remains, raise a value-free `ValueError` before any
   transaction/write; otherwise persist the sanitized text. Added unit regressions and PG regressions (residual x5 rejected with
   unit status unchanged, no failure event, no `last_error`, zero hits; recognised secret redacted and still capturable).
   Then 595 unit passed, targeted PG 26/26, six-file 155/155, cleanup zero.
10. **[F] Corpus comparison** (sanitizer before/after vs `1693075`): 1703 development+adversarial strings, **0 changes**; the
    independent reviewer re-verified 0/1703. Held-out data not inspected. `redaction.py` has not changed since.
11. **[F] Independent reviewer observations** (section 4) led to one more in-scope fix (section 5).
12. **[F] Rejected validator**: `VAL-62f99eb0e46540e7` (section 7).

## 2. Root cause and owner
`service key <value>` (and sibling families) matched no redaction or residual rule, so E1 `capture` persisted the value, and
`begin_task` stored task text without the residual fail-closed check. Single owner: `src/vres_os/redaction.py`.

## 3. Changes after `1693075`
- `redaction.py`: closed whole-word qualifier vocabulary (service, deployment, deploy, webhook, license, licence, ssh, admin,
  integration, bot, automation, api, private, signing, encryption, master, client, access, secret) x nouns
  key|secret|token|credential; excluded as benign: session, auth, root, ci, cd, pipeline. Whole-word boundary
  (`MY_APP_BOT_KEY` / `myBotKey` secret; `robot_key`, `session_key`, `source_key` not). A `[REDACTED]` placeholder followed by
  structural closers is not re-redacted. `SANITIZER_VERSION` 164.1 -> 164.2 (metadata only).
- `experience.py`, `sensitive_policy.py`: use the single owner; E1 `POLICY_VERSION`/`OBSERVED_POLICY_VERSION` and digests unchanged.
- `repository.py`: `begin_task` sanitizes title and objective via `sanitize_text` and raises before any DB connection on residual.
- `orchestration.py`: `fail_work_unit` fail-closed via `sanitize_text` (step 9); `_acceptance_criteria` fail-closed (section 5).
- Tests: `tests/integration/test_e7_b4b_security_hardening.py` (26), `tests/test_task_begin_sanitization.py` (10), plus updated
  redaction/experience/sensitive-policy/consolidation/retrieval unit and journey tests.
- Converted rejection fixtures: `secret_key = ...` / `JWT_SIGNING_KEY=...` are now redacted completely; rejection fixtures
  moved to `service_key_id` shapes, which stay residual.
- Versioning: no migration; immutable old episodes are not retroactively scrubbed (re-capturing a leaked-evidence episode
  fails closed via the immutable-digest conflict).

## 4. Security scope audit (reviewer observations)
| Observation | Classification | Basis |
|---|---|---|
| `record_work_graph` acceptance criteria text | **IN_SCOPE_SECURITY_BLOCKER — fixed** | [F] criteria JSON is written to `orchestration_work_units` with `json.dumps` and no redaction; only the companion event payload passes `redact()`. A credential in a criterion would persist raw and reach E1 capture inputs. |
| Other `redact_text` sites in `orchestration.py` (plan/routing rationale, recommendation, arbitration, synthesis) | **DOCUMENTED_OUT_OF_SCOPE_OBSERVATION** | [F] they apply canonical recognised-secret redaction. [F] The frozen B4B scenario cannot route a credential into them (authority path: begin_task -> routing -> plan -> work graph -> start -> `fail_work_unit` -> capture). [I] Widening them to `sanitize_text` risks false-positive rejections of long free text and needs a DAG-suite regression; tracked as a separate hardening item, not hidden. Residual-only shapes in those fields are therefore **[U] not proven absent** from storage. |
| Repository event/checkpoint persistence | **DOCUMENTED_OUT_OF_SCOPE_OBSERVATION** | [F] existing generic `redact` path; not on the frozen scenario path. Same residual-only caveat as above. |
| Sanitizer change vs HEAD | Verified | [F] 0/1703 corpus differences (author and reviewer). |
| Episode capture and public responses | Verified in scope | [F] capture sanitizes before write; returned payloads contain no canary (zero-hit tests including legacy raw row). |
| `begin_task` | Verified in scope | [F] fails closed before any DB connection on residual. |

## 5. Additional in-scope fix: work-graph acceptance criteria
`_acceptance_criteria` now passes each criterion key and statement through `sanitize_text`; a residual, or a key that changes
under sanitization, raises a value-free `ValueError` before any write; recognised secrets are redacted in the stored statement.
Regressions: 5 unit tests in `tests/test_task_begin_sanitization.py` (recognised secret redacted; 2 residual rejections;
credential-bearing key rejected; benign text unchanged). The work-graph PG file `test_project_agent_parallel_dag.py` passed 15/15.

## 6. Evidence on the exact current source (executed by the author in this session)
- Unit: 611 passed (Python 3.12).
- `test_project_agent_parallel_dag.py` on the isolated cluster: 15 passed.
- Six-file integration (isolated launcher, no symlink waiver): **155 passed** (26 + 5 + 30 + 14 + 77 + 3 collected), results
  `PASSED=155 FAILED=0 ERROR=0 SKIPPED=0 NOT_COLLECTED=0`, migration 046, identity PASS,
  `cleanup_database/roles/data_dir_remaining=0`, `recovery_state=ABSENT`, exit 0.
- Corpus gate: sanitizer unchanged since the 0/1703 comparison; not re-run.
- `git diff --check`: CRLF warnings only. Ruff on changed src files: added findings are line-length only (pre-existing noise).
- **Attribution.** Author-run: the 611 unit tests, the 15 work-graph PostgreSQL tests, the 155 six-file integration tests,
  and the corpus comparison. Reviewer-reproduced (validator `VAL-ae2b99375f534d9e`): 335 unit tests
  (`test_task_begin_sanitization`, `test_redaction`, `test_sensitive_policy`, `test_experience`) and the 26 focused PostgreSQL
  security tests on the isolated cluster, cleanup zero, recovery ABSENT. The reviewer did **not** reproduce the full
  611-test or 155-test runs, the 15 work-graph tests, or the corpus comparison.
- Documentation edits after that review change no source or test file; the earlier test evidence is attributed to the runs
  above and was not re-executed for documentation-only changes.

## 7. Validation history
- **[F] `VAL-ae2b99375f534d9e`**: recorded `passed` by Vres for its exact frozen artifact set, with host-observed Fable-family
  model, a real agent id, session binding and a persisted canonical report (10 passed checks). It covered an earlier version
  of this document.
- **[I]** Correcting this document afterwards is a new reviewable change and requires its own fresh protected validation.
  Which request validates the final artifact set is recorded only in the Vres ledger, not in this file.
- **[F] `VAL-62f99eb0e46540e7`** (below) was rejected earlier.

### 7.1 Rejected validation `VAL-62f99eb0e46540e7`
- **[F] Status: rejected** at Vres ingestion. Reason recorded: *"A skipped or failed check cannot establish PASS"*.
- **[F] Cause**: the validator returned outcome `passed` while one check was `not_run` (PostgreSQL evidence it had been told not
  to reproduce). The ingestion rule is correct and is not weakened.
- **[F]** It was also frozen on a state that has since changed (`orchestration.py` and test files), so it is stale regardless.
- **[I]** No model attestation or acceptance was ever recorded for it; it is not evidence of review, positive or negative.
- It was followed by a fresh request under a new key, where every check was individually verified by the validator and
  unverifiable items went into non-check limitations.

## 8. Remaining risks and limitations
- Pattern-based redaction is not a proof that every secret is detected.
- Broader key matching (digit-stripped flat suffix) may redact more structured keys than before.
- Residual-only credentials in the out-of-scope fields of section 4 are not proven absent.
- Immutable pre-fix episodes are not retroactively scrubbed.
- As of the evidence cut, the full live B4B adversarial replay has not been run on the corrected product; GREEN of the live
  cohort is **not claimed**. This hardening evidence does not substitute for it.
- The original live RED (`c3a7f23`) remains historically valid; its artifact is preserved unchanged.
- Residual-only risks at the out-of-scope persistence boundaries of section 4 are **not claimed resolved**.
- Acceptance of this implementation is recorded only in the Vres validation ledger; live B4B acceptance is a separate,
  later boundary.
