# Vres-OS — Post-#146 Technical Handoff (2026-09-25)

This file is the authoritative continuation state for the next development session after completion of issue #146.

It supersedes `docs/FINALIZATION-HANDOFF-2026-09-23.md` and `docs/handoffs/ISSUE-146-20260924.md` **for continuation purposes only**. Those files remain untouched as historical evidence and should not be rewritten to look current.

Repository: `vosser24/Vres-OS`

## 1. Executive state

- F-00 through F-15 final physical acceptance remain PASS.
- Issue #146 is completed, merged, validated, closed, and locally cleaned up.
- The #146 persistent Vres task `TASK-20260924-5814112da6` is completed with the latest protected validation still PASS.
- No routing policy or `model_policies` mutation was made by #146.
- No Sonnet/Opus winner was selected.
- Protected validation remains Fable/high.
- The only open GitHub issue at handoff creation is #141: `Post-validation resume can retain stale validation next_action`.
- #141 is therefore the next concrete repository development item unless the user explicitly reprioritizes.

Do not reopen #146 merely to continue model comparison. The merged #146 slice establishes the live host-evidence plumbing and governance boundary; it does not authorize model-policy adoption.

## 2. Exact repository identity before this handoff commit

Authoritative `main` before the docs-only handoff change:

`5eda28bd477ff819a6d65b412f78501b077703dc`

This is the merge commit of PR #156.

Its Git tree is:

`1ec647db3197e3045feb8302b37962d9c9f6ee09`

That tree is byte-for-byte the candidate tree that received the final protected #146 PASS.

Important: this handoff itself is a later docs-only commit. In the next session, first fetch `origin/main` and use the current commit containing this file as the base. Do not reset main back to `5eda28bd...`; that SHA is the pre-handoff product baseline recorded for provenance.

## 3. #146 lifecycle — final authoritative record

### Activation/base

- Issue: #146 — `Model-generation calibration and governed adoption (Opus 5.5+)`.
- Pre-implementation base: `ed18644ff8a386fce9805c358b766eba46673f3d`.
- Persistent task: `TASK-20260924-5814112da6`.
- Working branch was `issue-146-model-generation-calibration`.
- The branch has now been deleted locally and remotely.

### Candidate commits

- WIP checkpoint commit: `85509ba033389114d9865d1181d6b22156cbed44`.
- Final validated candidate commit: `bb81e9f69c6c39d8d243e2c895e4a0ecde644337`.
- Protected-validated candidate tree: `1ec647db3197e3045feb8302b37962d9c9f6ee09`.
- Candidate canonical manifest SHA-256: `f72ba1b9cbab209a0f46e5567f5294bddf9243d75362a464e2096e880d3d4fcb`.

### Exact #146 changed-file surface

Exactly 14 files differed from base `ed18644...`:

1. `.github/workflows/ci.yml`
2. `docs/LIVE-VERIFICATION.md`
3. `docs/handoffs/ISSUE-146-20260924.md`
4. `scripts/release_gate.py`
5. `src/vres_os/claude_experiment.py`
6. `src/vres_os/cli.py`
7. `src/vres_os/model_experiments.py`
8. `tests/integration/test_model_experiment_journey.py`
9. `tests/test_claude_experiment_producer.py`
10. `tests/test_migration_contract.py`
11. `tests/test_model_experiment_evidence.py`
12. `tests/test_release_boundaries.py`
13. `tests/test_runtime_surfaces.py`
14. `tests/test_windows_node_mcp_git.py`

No database migration was added by #146.

## 4. What #146 implemented

### Live Claude host experiment producer

A local-only CLI was added:

`vres model-experiment run --task-key <TASK> --phase <PHASE> --family sonnet|opus --effort <EFFORT> --prompt-file <FILE> --output-file <NEW_FILE>`

Key boundaries:

- CLI-only; not exposed through MCP.
- Refuses nested Claude Code execution.
- Uses the existing bounded process layer rather than a new subprocess framework.
- `shell=false`.
- Prompt goes through stdin, not a positional prompt.
- Uses a fresh temporary working directory.
- One turn only.
- No tools.
- MCP disallowed.
- No session persistence.
- No `--bare`.
- Prompt/output must stay inside the project.
- Existing output is refused; output is create-only.
- Symlink prompt/output paths are refused.
- Secret-like and oversized prompts are rejected before a paid model call.
- Only Sonnet and Opus experiment families are accepted; protected Fable is not an experiment target.

### Trusted host evidence

New host evidence is stored as `evidence_kind='claude_code_host'` and binds:

- exact physical provider model;
- requested family;
- requested effort;
- host result/session identifiers;
- provider-emitted usage fields;
- Vres adapter monotonic runtime;
- host duration values;
- provider label and cost basis;
- Claude Code version;
- frozen invocation contract;
- input/output SHA-256 digests;
- exact host list-price cost text;
- deterministic six-decimal SQL cost projection.

`host_result_id` is treated as the host identity key and is not mislabelled as a provider API response ID.

### Duplicate protection

Trusted host run recording uses a PostgreSQL advisory transaction lock keyed to the host result identity and rechecks for an existing row under that lock. The real integration race proved one contender waits and only one insert can succeed.

### Governance result

The existing model-experiment attestation/assessment path remains evidence-only:

- one pair may establish an observation for that exact input;
- `policy_mutation_allowed=false` remains explicit;
- no automatic model-policy mutation exists;
- no protected Fable downgrade/replacement was introduced.

## 5. Live #146 model evidence

The accepted live pair used the same prompt bytes and was run from a separate terminal outside Claude Code.

Input digest for both live runs:

`0e387a4d940a063e2ff9e99c779f60a5153f168f55ac75ab70d764a936a599b4`

Both runs returned the same output digest:

`2081d73e67b62147fd8d12e987b3679619dfcddac7c60309ede90371a4418ddb`

### Sonnet live run

- run id: `2`
- physical model: `claude-sonnet-5`
- requested effort: `medium`
- runtime: 3453 ms
- input tokens: 2
- output tokens: 29
- cache read input tokens: 3397
- cache creation input tokens: 1663
- exact host list-price estimate: `0.0076254` USD
- SQL projected estimated cost: `0.007625`
- host result id: `48045f21-07e2-466c-b9c0-e24f055b20b8`

### Opus live run

- run id: `3`
- physical model: `claude-opus-5-5`
- requested effort: `medium`
- runtime: 4281 ms
- input tokens: 2
- output tokens: 29
- exact host list-price estimate: `0.0117902` USD
- SQL projected estimated cost: `0.011790`

Interpretation boundary: these runs prove the live producer and trusted evidence path. They do **not** establish a routing/model winner and do not authorize a policy change.

## 6. `model_policies` invariant

Throughout #146:

- no routing mutation was made;
- no `model_policies` write was made;
- the table remained the documented 9-row baseline;
- all rows were still the pre-#146 rows created on 2026-09-14.

An earlier locally calculated table hash `2fb4ed901e476366922df393d40a9a6a32f21242fe7f7d03416e5a31b90f735f` was not reproducible by the final validator. The final protected review verified the row content/baseline instead. Do not elevate that earlier hash above the verified row content.

## 7. PostgreSQL and repository validation

### Targeted PostgreSQL gate

Final validator-run targeted integration:

`tests/integration/test_model_experiment_journey.py`

Result:

- 3 passed;
- exit 0;
- disposable database had required `_test` suffix;
- included the real two-connection advisory-lock duplicate race;
- `pg_locks` evidence confirmed one connection actually waited;
- exactly one insert succeeded and the duplicate path was rejected as already recorded.

### Full PostgreSQL-enabled suite

Final protected validator independently ran the full suite:

- `1024 passed`;
- `3 skipped`;
- exit 0;
- runtime 476.61 s;
- three skips were documented Windows symlink host-capability skips.

This validator-run `1024` count supersedes the earlier relayed local `1022` count for final evidence.

### Local release gate

Final successful local gate:

- status: `PASSED_WITH_EXPLICIT_LIVE_GATES`;
- 893 passed;
- 134 intentionally skipped because the release gate strips database credentials;
- wheel: `vres_os-0.2.0a1-py3-none-any.whl`;
- wheel SHA-256: `13514bcfe526e581cf0b03b00803e26466c2e271c1fae93f3356d97dd6b1a5c2`.

The local release gate is intentionally not the PostgreSQL proof. PostgreSQL proof comes from the separate DB-enabled suite.

## 8. Windows/release-gate portability corrections discovered during acceptance

Five narrow validated fixes were added after the initial #146 WIP checkpoint:

### `scripts/release_gate.py`

- Migration baseline hashing now uses canonical text/newline semantics (`read_text` + UTF-8 re-encoding), matching runtime migration checksum behavior and avoiding false CRLF failures on Windows.
- Coverage-enabled release-gate pytest now has a finite 900-second budget instead of the previous 180-second budget.

### `tests/test_migration_contract.py`

- Added regression coverage proving LF and CRLF copies produce the same release-gate migration digest.

### `tests/test_release_boundaries.py`

- The symlink-dependent onboarding test skips only Windows WinError 1314 when the host lacks symlink privilege.
- Added an executable contract test proving the release-gate pytest path forwards the finite Windows-capable timeout.

### `tests/test_runtime_surfaces.py`

- Oversized invalid prompt coverage still uses the same huge input, but pytest parameter IDs are short so Windows does not overflow `PYTEST_CURRENT_TEST` environment-variable limits.

### `tests/test_windows_node_mcp_git.py`

- The blocked-stdin Node/libuv child uses raw `os.read` instead of `sys.stdin.buffer.read`, avoiding a CPython buffered-stdin lock fatal error during interpreter shutdown while preserving the blocked-stdin condition.

These fixes were part of the exact protected-validated tree before the final candidate commit.

## 9. Protected validation history

### Historical fail-closed request

`VAL-9f89230b7b934f13`

- Recorded outcome: failed.
- Host-observed validator: `claude-fable-5-1`.
- Failure reason: the validator could not independently execute the PostgreSQL-backed targeted/full-suite checks in that run.
- It found no #146 product defect in the checks it did execute.
- This failed request is intentionally preserved as historical evidence and was never overwritten.

### Final passing request

`VAL-39bb83460d9344f6`

- Recorded outcome: passed.
- Host-observed validator model: `claude-fable-5-1`.
- Validator: exactly one `vres-os:validator` run with no model override.
- Completed: 2026-09-25 11:03:47 +03:00.
- Independently ran both PostgreSQL commands through a child-only local-secret injection path.
- Independently verified the frozen candidate surface, live run rows, producer/evidence contracts, duplicate protection, cost projection, MCP non-exposure, Windows portability corrections, release gate, and governance invariants.
- Candidate tree remained `1ec647db3197e3045feb8302b37962d9c9f6ee09` after validator completion.

## 10. Final #146 GitHub record

### PR #156

Title: `#146 Add governed Claude host model-experiment evidence`

- PR head: `bb81e9f69c6c39d8d243e2c895e4a0ecde644337`.
- Changed files: 14.
- PR CI run: #377 (`36111376194`) — SUCCESS.
- PR release-gate evidence artifact: ID `10852734259`.
- PR artifact digest: `sha256:3d8349755565ade9d625892d17960766f00645ce935b2c03f962e297818436de`.

### Merge

PR #156 merged as:

`5eda28bd477ff819a6d65b412f78501b077703dc`

The merge commit tree is exactly:

`1ec647db3197e3045feb8302b37962d9c9f6ee09`

So GitHub merged the exact protected-validated content tree.

### Post-merge CI

Main CI run #378 (`36111690909`) — SUCCESS.

Every substantive step succeeded:

- setup/container;
- checkout;
- Python setup;
- exact build-backend provisioning;
- dependency install;
- repository-wide critical lint;
- strict model-evidence lint;
- full PostgreSQL integration suite;
- installed runtime import smoke;
- local release gate;
- release-gate evidence upload;
- cleanup.

Post-merge release-gate artifact:

- ID `10852947746`;
- digest `sha256:7633861c33a98a27446cafb57f75b6898b666a3da639466c6376b989a63bfc7f`.

### Issue/task closure

- GitHub issue #146 is closed with state reason `completed`.
- Final evidence was posted to the issue before closure.
- Vres task `TASK-20260924-5814112da6` was completed at 2026-09-25 11:32:57 +03:00.
- Read-back showed `task_status='completed'`, `validation_status='passed'`, and completion after the latest passing validation.

## 11. #146 cleanup state

The completed #146 feature branch was deleted locally and remotely.

Local checkout at cleanup:

`C:\Projects\Vres-Model-Calibration-20260924`

Final observed state before this handoff work:

- branch: `main`;
- HEAD: `5eda28bd477ff819a6d65b412f78501b077703dc`;
- `origin/main`: same;
- clean worktree (`STATUS_COUNT=0`);
- only one worktree;
- no remaining `vres-146-*` items under `%TEMP%`.

The temporary #146 local secret handle was deleted.

The local Vres secret store still contained:

`pg_issue139_test_dsn`

Do not delete that handle automatically. It belongs to prior issue #139 test infrastructure. Never expose its value in chat, logs, docs, or Git.

GitHub release-gate artifacts for CI #377/#378 remain the durable #146 CI evidence even though local temp evidence was intentionally removed.

## 12. Non-blocking observations intentionally carried forward

These were observed during protected #146 review and were not acceptance blockers. Preserve them rather than silently rewriting history:

1. `docs/handoffs/ISSUE-146-20260924.md` is a dated checkpoint and is stale relative to final execution. That is intentional; this new handoff supersedes it for continuation.
2. `src/vres_os/claude_experiment.py` commentary references the originally characterized Claude Code 2.1.281 result envelope, while accepted live rows were later produced by Claude Code 2.1.282.
3. A create-only output-file write failure occurring after a successful paid model call exits with a generic error; the special 'preserved / model_run not recorded' notice is specifically tested for DB-recording failure, not this output-write edge path.
4. `test_provisioning_never_alters_existing_account_or_database` showed test-order fragility when run as a small subset. The validator reproduced the same behavior on the pre-#146 base and the test passes in full-suite order, so it is not classified as a #146 regression.
5. `docs/RELEASE-VALIDATION.md` still contains historical wording from the synthetic model-experiment era stating that a real live-provider adapter remained to be supplied. #146 has now supplied and live-tested the Claude host producer. Treat that paragraph as documentation debt if/when release docs are refreshed; it is not authority to undo #146.

Do not turn any of these observations into a model-policy change.

## 13. What must remain unchanged going forward

- F-00 through F-15 stay accepted; do not rerun the historical matrix without a changed owning surface.
- Protected validator remains `fable/high`.
- Routine governed worker tiers remain Sonnet/Opus families.
- Host-observed physical model identity remains authoritative for trusted model experiments.
- Caller/self-reported telemetry remains advisory.
- One model pair remains evidence only, never automatic policy authority.
- `model_policy_change` remains protected.
- No JEV runtime testing: JEV was explicitly withdrawn before proof and removed from the active path.
- Do not claim production readiness merely from green CI/finalization.
- Do not claim measured token savings from the existing acceptance work.

## 14. Next development phase — GitHub issue #141

#141 is currently the **only open GitHub issue** and is the next default development target.

Title:

`Post-validation resume can retain stale validation next_action`

### Problem

After a canonical protected validation PASS, authoritative `validation_status` is correct, but persisted descriptive fields can remain from the pre-validation checkpoint:

- `current_step` may still say validation needs to be dispatched;
- `next_action` may still say to call `validation_prepare`.

A later material checkpoint is correctly blocked because it would mutate reviewed state or invalidate the fresh PASS. Native `/compact` can therefore snapshot those stale descriptive fields unchanged. `/clear`/rehydration behaved safely in F-15 because the system consulted authoritative validation evidence and did not actually dispatch a duplicate validator, but the continuation text is still wrong/stale.

### Existing physical #141 reproduction evidence

Project:

`C:\Projects\Vres-F15-Realistic-Day-20260922`

Task:

`TASK-20260922-e67a4e17f0`

Fresh protected PASS:

`VAL-2a1bff9f46574ad4`

Pre-validation checkpoint:

`CP-20260922-37b05eb364`

Post-native-compact automatic checkpoint:

`CP-20260923-2225c42519`

The PASS remained authoritative and no duplicate validation executed, but stale validation-dispatch text remained in the descriptive state.

### #141 acceptance contract

1. Reproduce checkpoint-before-validation -> canonical protected PASS.
2. `validation_status=passed` remains current.
3. Resume context no longer presents the pre-PASS validation-dispatch instruction as the current next action.
4. Historical checkpoint contents remain unchanged.
5. PreCompact/PostCompact continuity does not re-promote stale validation instructions.
6. No validation invalidation or second validation is required merely to refresh descriptive continuation.
7. Existing protected checkpoint/material-mutation guards remain fail-closed.
8. Add regression coverage for native compact/clear continuity after protected PASS.

## 15. #141 likely owning surfaces — investigation starting points, not a decided design

Current code explains the observed shape:

### `src/vres_os/repository.py`

`Repository.resume_context()` currently returns persisted task-state fields directly:

- `step = task.current_step`;
- `next_action = task.next_action`;
- `validation_status = task.validation_status`;
- plus latest checkpoint/snapshot metadata.

This means a fresh validation PASS can be authoritative while the descriptive fields still reflect the last pre-PASS material checkpoint.

`Repository.checkpoint()` updates `state_summary/current_step/next_action` and marks validation pending if those material fields change. That fail-closed behavior must not be weakened merely to make continuation text prettier.

### `src/vres_os/hooks.py`

`compact()` creates the automatic checkpoint from:

- `task.state_summary`;
- `task.current_step`;
- `task.next_action`.

So if those fields are stale after PASS, PreCompact can persist the same stale text again.

The post-compaction/user-prompt continuity path calls `resume_context()` and renders the returned state, so a safe fix may belong in a derived resume/continuation view rather than a material checkpoint write.

### `src/vres_os/validation_lifecycle.py` / validation services

`validation_invalidate` is intentionally the path for a real post-review material change. #141 must not abuse invalidation merely to update descriptive continuation.

### Likely regression test areas

- `tests/test_chairman_continuity_contract.py`
- `tests/test_compaction_hooks.py`
- `tests/test_hooks.py`
- `tests/test_validation_checkpoint_guard_contract.py`
- `tests/integration/test_validation_checkpoint_guard.py`
- `tests/integration/test_session_lifecycle_recovery_journey.py`

Do not assume all of these need edits. Start by tracing the smallest ownership boundary.

## 16. Design constraints for #141

A correct #141 solution should prefer a derived/non-material continuation concept over weakening protected mutation guards.

Preserve all of the following:

- validation PASS freshness is authoritative;
- historical checkpoints are immutable evidence;
- no fake post-review material mutation;
- no automatic validation invalidation just to refresh prose;
- no second protected validation solely to repair `next_action` text;
- compact/clear remain fail-safe;
- task/session ambiguity handling remains explicit;
- persisted material state and derived resume guidance remain distinguishable;
- a completed task must not become resumable merely because historical state text exists.

Possible design families already named in issue #141, but not yet chosen:

- derived/superseded continuation view;
- explicit non-material validation-completion metadata;
- another mechanism that overlays current continuation without rewriting reviewed material state.

Do not pick one before reading the current code/tests and reproducing the exact stale-state sequence.

## 17. Recommended next-session execution order

1. `git fetch origin --prune`.
2. Verify current `origin/main` contains this handoff and start from that exact commit.
3. Read this file first.
4. Read issue #141 in full.
5. Read `docs/FINAL-VERIFICATION.md` surface-triggered regression policy.
6. Inspect `Repository.resume_context`, `Repository.checkpoint`, compaction hooks, validation lifecycle, and the existing continuation/checkpoint tests.
7. Reproduce #141 with a disposable/synthetic task rather than mutating old F-15 evidence.
8. Create a dedicated branch/worktree for #141; do not develop directly on main.
9. Freeze the smallest acceptance contract before editing.
10. Implement the smallest correct change; do not weaken the protected validation/checkpoint guard.
11. Run focused unit/contract tests first.
12. Run the PostgreSQL integration slice if the change touches persisted lifecycle semantics.
13. Apply the surface-triggered regression policy. For session lifecycle/hooks/compaction changes, the minimum historical live rerun family is F-05, F-06, F-15; scope it to the changed behavior rather than blindly rerunning unrelated fixtures.
14. Require CI success on the exact PR head.
15. Require post-merge main CI success.
16. Only then close #141 and complete its persistent Vres task.

## 18. Recommended new worktree/branch naming

Suggested new worktree:

`C:\Projects\Vres-Post-Validation-Continuity-20260925`

Suggested branch:

`issue-141-post-validation-resume`

These names are recommendations, not existing resources at handoff creation.

## 19. Things not to do in the next session

- Do not continue development in the deleted #146 feature branch.
- Do not recreate #146 temporary evidence or rerun paid Sonnet/Opus calls unless a future explicitly authorized calibration plan requires new evidence.
- Do not mutate routing/model policies as a side effect of #141.
- Do not edit historical F-15 checkpoints to make #141 disappear.
- Do not invalidate a valid protected PASS just to rewrite `next_action` prose.
- Do not rerun JEV.
- Do not delete `pg_issue139_test_dsn` without a separate reason and safe ownership check.
- Do not treat stale documentation phrases as executable policy.

## 20. Evidence hierarchy for continuation

For #146 final state, prefer in this order:

1. merged Git objects on `main`;
2. GitHub CI #377/#378 and their release-gate artifacts;
3. host-recorded protected validation `VAL-39bb83460d9344f6`;
4. the completed Vres task record;
5. PR #156 / issue #146 final comments;
6. this handoff summary;
7. older #146 checkpoint handoff for historical detail only.

For #141, the GitHub issue body is the authoritative acceptance contract until a new task freezes a more detailed implementation contract.

## 21. New-session starter prompt

Use this as the first instruction in a new chat/session:

> Resume Vres-OS from `docs/FINALIZATION-HANDOFF-2026-09-25.md`. Fetch current `origin/main` first and verify this handoff is present. #146 is fully complete and must not be reopened or used to mutate routing/model_policies. The only open issue is #141 (`Post-validation resume can retain stale validation next_action`). Read #141 and the handoff, create a clean dedicated #141 worktree/branch from current main, reproduce the stale post-validation continuation safely, freeze the acceptance contract, and implement the smallest fix without weakening protected validation/checkpoint guards. Preserve historical checkpoints and use the surface-triggered regression policy.

## 22. Final handoff verdict

The repository is at a clean post-#146 development boundary.

#146 is not pending. Its implementation, live evidence, PostgreSQL validation, protected Fable/high review, PR, pre-merge CI, merge, post-merge CI, issue closure, task completion, branch cleanup, secret cleanup, and temporary evidence cleanup are complete.

The next default engineering phase is #141.
