# Vres-OS — Post-#141/#159 Closeout Handoff (2026-09-25)

This file is the authoritative continuation state after completion of issues #141 and #159.

It supersedes `docs/FINALIZATION-HANDOFF-2026-09-25.md` **for continuation purposes only**. That file and all older handoffs remain historical evidence and must not be rewritten to look current.

Repository: `vosser24/Vres-OS`

## 1. Executive state

- #146 is fully complete and remains closed. Do not reopen it to continue model comparison or mutate routing/model policy.
- #159 is fully complete, merged, physically accepted, post-merge verified, and closed.
- #141 is fully complete, merged, physically accepted, post-merge verified, and closed.
- There are currently **no open GitHub issues**.
- The current verified product main commit before this docs-only handoff branch is:
  `acd45f1262979c16b1029ca9241976098cb503e8`
- Post-merge CI #391 is green on that exact commit.
- The primary local clone was normalized to `main` at that exact commit with a clean working tree.
- Historical F-00 through F-15 acceptance remains valid. The changed-surface rerun required by #141 was executed and passed for F-05, F-06, and F-15.
- The corrected native auto-compaction policy is 15% of the native auto-compact window **USED**, leaving roughly 85% of that window free.
- Vres does not persist a custom `CLAUDE_CODE_AUTO_COMPACT_WINDOW`.
- Protected validation remains Fable/high. No routing/model-policy adoption was made.
- JEV remains withdrawn and must not be rerun unless explicitly reintroduced by a future approved design.
- There is no automatic `/clear` subsystem. Native auto-compaction is the preferred continuous context mechanism; `/clear` remains an intentional/manual recovery or task-boundary action.

The repository is at a clean planning boundary. Because there are no open issues, the next development phase should begin by identifying the next concrete requirement, opening a new issue with a frozen acceptance contract, and only then creating a new branch/worktree.

## 2. Exact repository identity

Verified product main before this docs-only handoff:

`acd45f1262979c16b1029ca9241976098cb503e8`

That is the merge commit of PR #158:

`#141 Derive live continuation after protected validation PASS`

The preceding product main was the #159 merge:

`afaf47544e02902af0c30bd1531d88d701c71c36`

Important: this handoff is being created on a later docs-only branch. In the next session, fetch `origin/main` and use the current commit containing this file as the continuation base. Do not reset main back to `acd45f1...`; that SHA is the verified pre-handoff product baseline recorded for provenance.

## 3. Final #159 record — auto-compaction boundary correction

Issue:

`#159 Correct native auto-compaction trigger to 15% used / ~85% free`

PR:

`#160 #159 Correct auto-compaction to 15% used`

Accepted candidate:

`37cb32017ca69fbc83eaf25d11088dbca35cd3a5`

Merge commit:

`afaf47544e02902af0c30bd1531d88d701c71c36`

### Implemented contract

Production Vres-managed Claude setting:

`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=15`

Meaning:

- trigger after roughly 15% of Claude's native auto-compact window is used;
- roughly 85% of that window remains free;
- the status-line `ctx` percentage is full-model **used** context, not remaining context;
- the native auto-compact window can be smaller than the full model context, so the status line need not display exactly 15% when the trigger fires.

Vres does **not** install or persist:

`CLAUDE_CODE_AUTO_COMPACT_WINDOW`

Update semantics:

- Vres-owned legacy `85` migrates to `15`;
- user-owned/custom `85` remains untouched;
- other external threshold modifications are preserved and ownership is relinquished;
- custom window/disable settings remain preserved;
- uninstall removes only a still-owned current managed threshold.

### Physical Windows migration evidence

Installed readback after `update.ps1`:

- managed threshold: `15`
- `autocompact_owned=true`
- persisted custom window: absent
- dedicated `autoCompactWindow`: absent
- `vres doctor`: PASS for required components/configuration
- `vres selftest`: PASS

### Invalid 100k test fixture

An initial test used a temporary 100,000-token window. At 15%, that creates a trigger near only 15,000 tokens, which is too close to/below the fixed Claude/Vres/plugin session overhead. Claude correctly auto-compacted but then reported repeated auto-compaction thrashing.

That run is **not** acceptance evidence for the intended production boundary.

Do not reuse the 100k fixture as the recommended physical boundary test for a 15%-used policy.

### Valid R2 physical auto-compaction evidence

Temporary process-only acceptance window:

`CLAUDE_CODE_AUTO_COMPACT_WINDOW=800000`

Production percentage remained:

`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=15`

Task:

`TASK-20260925-a15fc9a9bd`

Session:

`08b740a0-c334-466d-a1ce-25e3b1cbc4cc`

Baseline checkpoint:

`CP-20260925-77984435aa`

Automatic PreCompact checkpoint:

`CP-20260925-bb620dae5b`

Native transcript evidence:

- exactly one `compact_boundary`
- trigger: `auto`
- preTokens: `122588`
- postTokens: `18951`
- cumulativeDroppedTokens: `103637`
- durationMs: `44449`
- timestamp: `2026-09-25T10:24:03.829Z`
- no manual `/compact`

Nominal 15% of 800,000 is 120,000 tokens. The observed trigger was +2,588 tokens, about 2.2% above nominal, consistent with the intended boundary.

Vres continuity survived the native rollover without material state mutation.

### #159 automated evidence

Exact-head CI #388:

- SUCCESS
- 1028 passed, 1 skipped
- installed-runtime smoke PASS
- release gate `PASSED_WITH_EXPLICIT_LIVE_GATES`
- artifact `10857441901`
- digest `sha256:d452c3ddcdec89e02489072d56aac9c77f8827901d6878fc2d64c9fa62e647a1`

Post-merge main CI #389:

- SUCCESS
- 1028 passed, 1 skipped
- installed-runtime smoke PASS
- release gate `PASSED_WITH_EXPLICIT_LIVE_GATES`
- release-gate tests 897 passed, 132 skipped
- artifact `10858783203`
- digest `sha256:53d19319c21bf2a84bdc9223590fea999f8b822c91eede281ce3703852757df4`

## 4. Final #141 record — derived post-validation continuation

Issue:

`#141 Post-validation resume can retain stale validation next_action`

PR:

`#158 #141 Derive live continuation after protected validation PASS`

Accepted combined candidate after #159 merged:

`7342206b044a6d7ec277511a574969df4ae058b5`

Merge commit:

`acd45f1262979c16b1029ca9241976098cb503e8`

### Problem fixed

Before #141, a canonical protected validation PASS could be authoritative while persisted descriptive task fields still reflected the last pre-validation checkpoint, for example:

- step still said protected validation needed to run;
- next_action still told Chairman to dispatch validation.

A later material checkpoint is correctly blocked because it would mutate reviewed state or stale the PASS. Native compaction could therefore preserve the stale historical text.

### Implemented contract

`Repository.resume_context()` now exposes a coherent **live projection** when `validation_status=passed`:

- top-level `step`: `protected validation passed`
- top-level `state`: current PASS wording
- top-level `next_action`: continue from validated state without dispatching another validation; explicitly invalidate before real material change
- top-level `pending`: the current derived continuation only
- `continuation_source=derived_validation_pass`

Historical reviewed state is exposed separately:

- `reviewed_state`
- `reviewed_pending`
- `latest_checkpoint`

These historical fields remain evidence. They may contain pre-PASS text and must **not** be treated as the current live instruction when structured validation state says PASS.

The fix does not:

- mutate the reviewed task state merely to refresh prose;
- rewrite historical checkpoints;
- invalidate validation merely to refresh continuation text;
- dispatch a second validation;
- weaken protected checkpoint/material-mutation guards.

A real material change after PASS still requires explicit validation invalidation through the existing governed path.

## 5. #141 automated evidence

Initial corrected #141 candidate CI #387:

- SUCCESS
- 1027 passed, 1 skipped
- installed-runtime smoke PASS
- release gate `PASSED_WITH_EXPLICIT_LIVE_GATES`
- artifact `10855674675`
- digest `sha256:54b98716fc1841b621b7694a2ec52739b0a3bfeb5810f3a3703a0744a1405c21`

After #159 merged, #141 was refreshed onto corrected main using a merge commit that preserved both histories.

Final exact PR head:

`7342206b044a6d7ec277511a574969df4ae058b5`

Exact-head CI #390:

- SUCCESS
- 1029 passed, 1 skipped
- installed-runtime smoke PASS
- release gate `PASSED_WITH_EXPLICIT_LIVE_GATES`
- release-gate tests 897 passed, 133 skipped
- wheel SHA-256 `ed008686df1c0eb2dd276997cdf09f8cd2bacb399fab26683659029ae123738a`
- artifact `10859078437`
- digest `sha256:52b278de1728bc7b3efd1d7b56aeeac86216d46e0dc974939e278af4ae4f1873`

Post-merge main CI #391 on `acd45f1...`:

- SUCCESS
- 1029 passed, 1 skipped
- installed-runtime smoke PASS
- release gate `PASSED_WITH_EXPLICIT_LIVE_GATES`
- release-gate tests 897 passed, 133 skipped
- wheel SHA-256 `e91c638caf7a145d48180af14f2faa133b4ccb7b93911651aa5ab5ebd9668681`
- artifact `10861347779`
- digest `sha256:35c1b1a8e7eb20b7fa45b36d4293c145b3521f278f09914694d30125a87ffa86`

## 6. #141 physical F-05 — protected PASS continuity

Disposable project:

`C:\Projects\Vres-141-Live-Acceptance-R2-20260925`

Task:

`TASK-20260925-c1c92d78c5`

Fixture:

`f05-validation-fixture.txt`

Fixture exact content:

`VRES-141-F05-PROTECTED-PASS`

Fixture bytes:

`27`

Fixture SHA-256:

`ce8f058f7cf22cae63b4dabc1681fb7273af92fd8a6ce23be5ad08408244e728`

Pre-validation checkpoint:

`CP-20260925-3aa401ff43`

Validation request:

`VAL-19ec9ca629e34bb2`

Observed validator:

`claude-fable-5-1`

Authoritative result:

`passed`

Physical sequence passed:

1. canonical protected PASS;
2. live resume immediately exposed `derived_validation_pass`;
3. historical checkpoint remained pre-PASS;
4. native `/compact` created historical PreCompact checkpoint `CP-20260925-3acd605dc7` without re-promoting stale text;
5. native `/clear` replacement session automatically recovered the same task;
6. normal `/exit` plus fresh Claude restart automatically recovered the same task;
7. fresh task_resume, validation evidence, fixture hash and size all remained correct;
8. exactly one validation request existed;
9. no validation_invalidate and no duplicate validation occurred.

F-05: **PASS**.

## 7. #141 physical F-06 — concurrency and project isolation

Project A:

`C:\Projects\Vres-F06-Concurrency-A-20260925`

ALPHA:

`TASK-20260925-d02bc1b0ef`

ALPHA checkpoint:

`CP-20260925-588dd3caac`

BETA:

`TASK-20260925-cc972db0b8`

BETA initial checkpoint:

`CP-20260925-6ea67477c6`

BETA final-review checkpoint:

`CP-20260925-d42e00506c`

BETA protected validation:

`VAL-480198e2dd744be6`

BETA observed validator:

`claude-fable-5-1`

BETA completion:

- authoritative validation passed;
- exactly one validation request;
- task_complete succeeded;
- BETA disappeared from unfinished tasks.

Temporary ambiguity setup task GAMMA:

`TASK-20260925-d01784a11a`

GAMMA was explicitly cancelled by current user instruction to clear project focus.

Observed F-06 behaviors:

- A1 and A2 held distinct concurrent live session bindings to ALPHA and BETA.
- Neither live process was incorrectly closed as stale.
- Native `/clear` in A1 created a replacement session that inherited ALPHA before project-focus fallback.
- A2 remained live and bound to BETA across A1 clear.
- After GAMMA cancellation cleared focus, no-key resume surfaced `ambiguous: true` with ALPHA and BETA rather than selecting the more recent task.
- BETA protected completion did not move A1 away from ALPHA.
- After BETA completion, A1 no-key resume and reply gate still resolved ALPHA.

Project B:

`C:\Projects\Vres-F06-Isolation-B-20260925`

Project-B DELTA task:

`TASK-20260925-b1483e6c46`

DELTA checkpoint:

`CP-20260925-092ae1fc04`

Cross-project attempts from Project B against ALPHA were rejected before mutation:

`Object is outside the current project; cross-project/global writes require separate authorization.`

This applied to both explicit cross-project resume/bind and checkpoint attempts.

Project-B local retrieval also returned no ALPHA-specific knowledge or project agents.

F-06: **PASS**.

## 8. #141 physical F-15 realistic-day smoke

Disposable project:

`C:\Projects\Vres-F15-141-Smoke-20260925`

Task:

`TASK-20260925-9d52780376`

Final checkpoint:

`CP-20260925-ee7031e03e`

Protected validation:

`VAL-c54a44c4256348f6`

Observed validator:

`claude-fable-5-1`

Specialist:

- one bounded CTO-role worker;
- host-observed model `claude-sonnet-5`;
- report `ORCHREP-20260925-f64072e6aa`;
- orchestration final `ORCHFINAL-20260925-7f734312a6`;
- no unnecessary panel.

Reusable procedure/knowledge lookup returned none and the workflow continued normally rather than manufacturing reuse.

The synthetic release-readiness artifact passed all eight deterministic acceptance criteria.

Before clear:

- authoritative validation passed;
- request count 1;
- task remained active;
- live continuation was already `derived_validation_pass`;
- stale historical pre-PASS text existed only in reviewed/history fields.

After native `/clear`:

- SessionStart automatically recovered the exact task;
- no-key task_resume returned the same task;
- existing protected PASS remained authoritative;
- no validation invalidation;
- no duplicate validation;
- task_complete succeeded using the existing PASS;
- task disappeared from unfinished task_open_list.

Context observation:

Before smoke work:

- 36.7k / 1m full-model tokens used (~4%);
- 930.3k free;
- native auto-compact window 1m;
- buffer 33k.

After `/clear`:

- 37.8k / 1m used (~4%);
- 929.2k free;
- native auto-compact window 1m;
- buffer 33k.

These observations are descriptive only. They do not establish measured token savings and must not auto-change routing/model policy.

F-15: **PASS**.

## 9. Current local workstation state

Primary clone:

`C:\Users\User\Vres-OS`

Normalized state after #141 merge:

- branch: `main`
- HEAD: `acd45f1262979c16b1029ca9241976098cb503e8`
- `origin/main`: same SHA
- working tree: clean
- old stale `C:\Projects\Vres-Main-Update-20260922` main worktree removed
- #141 development worktree `C:\Projects\Vres-Post-Validation-Continuity-20260925` removed
- remote #141 branch deleted

Evidence/historical worktrees still present. Do not delete them blindly.

Notable current evidence worktree:

`C:\Projects\Vres-Autocompact-15-20260925`

It is detached at the accepted #159 candidate `37cb320...`.

The merged remote branch `issue-159-autocompact-15-used` still exists at handoff creation. It may be removed later as cleanup, but do not confuse branch cleanup with product correctness.

Other older acceptance/historical worktrees remain intentionally present from prior phases.

## 10. Disposable persistent tasks intentionally left as evidence

Some disposable physical-acceptance projects still contain unfinished persistent tasks. This is not a product defect; they were deliberately left active to preserve evidence or because the test contract required leaving them active.

Important examples:

- #159 auto-compaction task `TASK-20260925-a15fc9a9bd`: active in the #159 disposable project.
- #141 F-05 task `TASK-20260925-c1c92d78c5`: active in the F-05 disposable project with current protected PASS.
- F-06 ALPHA `TASK-20260925-d02bc1b0ef`: active in Project A.
- F-06 DELTA `TASK-20260925-b1483e6c46`: active in Project B.
- F-06 BETA is completed.
- F-06 GAMMA is cancelled.
- F-15 smoke task `TASK-20260925-9d52780376` is completed.

Do not let these test tasks influence work in other projects. Project scoping prevents cross-project selection. If a future cleanup phase wants to cancel/remove disposable tasks or delete their folders, do it explicitly and preserve the relevant GitHub/CI evidence first.

## 11. Governance and model-routing invariants that remain unchanged

- Protected validation remains Fable/high.
- #146 calibration evidence remains evidence only.
- No Sonnet/Opus winner has been adopted as policy authority from #146.
- No #141 or #159 work changed routing/model policies.
- Caller/self-reported model identity remains advisory; host-observed evidence is authoritative where required.
- Do not automatically promote a model based on one comparison, self-reported latency, or token usage.
- JEV runtime testing remains withdrawn.
- Codex is optional/held unless explicitly enabled for a future test.
- Headless Claude `-p`, `--max-turns`, and native headless plan mode remain outside the current runtime finalization contract unless a future issue explicitly brings them in.
- Do not claim production/customer readiness merely from green CI/finalization.
- Do not claim measured token savings from the current acceptance evidence.

## 12. Auto-compaction operational rules going forward

Treat the managed percentage correctly:

`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=15`

means approximately **15% USED**, not 15% remaining.

Do not invert it back to 85.

Do not persist `CLAUDE_CODE_AUTO_COMPACT_WINDOW` as part of Vres installation.

A temporary process/session window may be used only for bounded physical testing and must not be mistaken for production configuration.

The 100k/15% test fixture is too small for a normal Vres/Claude session and can cause immediate compaction thrash. Use a sufficiently large bounded test window if future physical boundary testing is needed.

The status-line `ctx` value is full-model **used** context.

Native auto-compaction is preferred for ordinary long-session continuity. `/clear` remains manual/intentional.

## 13. Historical checkpoints and validation semantics

After a protected PASS:

- top-level resume fields are the live continuation;
- `reviewed_state`, `reviewed_pending`, and `latest_checkpoint` are historical/reviewed evidence;
- historical text may legitimately say validation had not run yet;
- historical text must never be re-promoted over the authoritative current PASS;
- do not write a fake post-review material checkpoint merely to make historical prose look current;
- do not invalidate or revalidate merely to refresh descriptive continuation;
- if the user actually wants a material change after PASS, explicitly invalidate validation through the governed lifecycle first.

## 14. Evidence and secrets to preserve

Do not expose secret values in chat, logs, docs, or Git.

The prior issue #139 test secret handle:

`pg_issue139_test_dsn`

was intentionally preserved in the earlier handoff. Do not delete it automatically. Any cleanup must first establish ownership and whether later tests still rely on it.

GitHub CI/release-gate artifacts are durable evidence and should be preferred over recreating temporary local fixtures.

## 15. Non-blocking observations carried forward

These are not current blockers and should not be silently rewritten into defects without fresh evidence:

1. Older handoff files are intentionally stale snapshots; this file supersedes them only for continuation.
2. `src/vres_os/claude_experiment.py` commentary historically references the originally characterized Claude Code 2.1.281 result envelope, while accepted later live rows used Claude Code 2.1.282.
3. A create-only output-file write failure occurring after a successful paid model call still exits with a generic error; the special preserved-call notice is specifically covered for DB-recording failure, not every output-write edge path.
4. `test_provisioning_never_alters_existing_account_or_database` previously showed test-order fragility in a small subset but reproduced on the pre-change base and passes in full-suite order.
5. `docs/RELEASE-VALIDATION.md` contains some historical wording from the earlier synthetic model-experiment era. Treat that as documentation debt if release docs are refreshed; it is not authority to undo #146.
6. GitHub CLI `gh` was not on PATH in the PowerShell session used during #141 merge cleanup. Git itself and the connected GitHub integration were sufficient. This is an environment/tooling note, not a Vres defect.

## 16. Surface-triggered regression rule remains authoritative

Do not rerun the entire historical matrix after every future change.

Use `docs/FINAL-VERIFICATION.md`:

- always establish exact candidate identity/F-00 as required;
- rerun the cases owned by the changed surface;
- run F-15 smoke;
- reuse prior physical evidence only when the documented reuse rules are satisfied.

For session lifecycle/hooks/compaction/reply-guard changes, the minimum live family remains:

- F-05
- F-06
- F-15

#141 has now passed all three on the accepted candidate.

## 17. Next development phase

There are no open GitHub issues at handoff creation.

Therefore the next session must **not invent a continuation issue from stale handoff text**.

Recommended order:

1. Fetch `origin/main --prune`.
2. Verify the current main contains this handoff.
3. Confirm the primary clone is clean and on main.
4. Check current open issues/PRs.
5. If there is still no open issue, decide the next concrete product requirement with the user.
6. Open a dedicated issue with:
   - exact problem statement;
   - scope boundary;
   - frozen acceptance contract;
   - owning surfaces;
   - minimum surface-triggered regression family.
7. Create a dedicated branch/worktree from current main.
8. Implement the smallest correct change.
9. Run focused tests, exact-head CI/release gate, required physical acceptance, merge, post-merge main CI, then close the issue.
10. Create another handoff only when crossing a real development boundary.

Do not reopen #141, #146, or #159 merely because they are named in historical evidence. Reopen only if a real regression is newly demonstrated and the issue lifecycle intentionally requires reopening rather than a new issue.

## 18. Optional cleanup after this handoff is merged

Cleanup is non-blocking.

Possible later cleanup:

- delete the merged remote `issue-159-autocompact-15-used` branch;
- remove `C:\Projects\Vres-Autocompact-15-20260925` after deciding its physical evidence is no longer needed locally;
- archive/delete disposable F-05/F-06/F-15 project folders after durable evidence is confirmed sufficient;
- prune older historical worktrees one-by-one only after verifying each is clean and no unique commit/evidence would be lost.

Never bulk-delete historical worktrees based only on age.

## 19. New-session starter prompt

Use this as the first instruction in a new chat/session:

> Resume Vres-OS from `docs/FINALIZATION-HANDOFF-2026-09-25-POST-141-159.md`. Fetch and verify current `origin/main` first. #146, #159, and #141 are fully complete and must not be reopened or used to mutate routing/model policies without new evidence. Auto-compaction is now 15% USED / roughly 85% free with no persisted custom window. The #141 live continuation fix is merged and F-05/F-06/F-15 plus post-merge CI are green. There are no open issues at handoff creation, so first inspect current GitHub state and identify the next real product requirement before creating a new issue/branch. Preserve historical checkpoints/evidence and follow the surface-triggered regression policy.

## 20. Closeout verdict

The #141/#159 development phase is complete.

The verified product baseline is:

`acd45f1262979c16b1029ca9241976098cb503e8`

on `main`, with post-merge CI #391 green.

There is no known blocking defect from this phase, no open GitHub issue at handoff creation, and no pending required rerun from #141/#159.

The correct next action is a new planning/development phase from current main, not continuation of either closed issue.
