# Vres-OS PERSONAL PT-2A — Offline transition planner source committed; Windows validation next

**Date:** 2026-10-29 (Europe/Athens). **Repository:** `vosser24/Vres-OS`.

**Current PT-2A status:** `AUTHOR_SOURCE_AND_TESTS_COMMITTED` / `AUTHOR_GITHUB_TREE_AND_DIFF_VERIFIED` / `WINDOWS_PYTEST_NOT_RUN` / `INDEPENDENT_PT2A_REVIEW_NOT_RUN` / `NO_INSTALLED_CHANGE` / `NO_MODEL_ACTIVATION` / `NO_F1_AUTHORITY`.

## Read-first safety and source-of-truth boundaries

- **Database:** `LIVE_SCHEMA_048_INCIDENT=OPEN`; absolutely **NO PostgreSQL contact, even SELECT**, including Vres task, doctor, bootstrap, CLI, health, hooks, recovery or indirect troubleshooting. `VRES_REPLY_GUARD_WARNING` and `VRES_PERSISTENCE_WARNING` remain unresolved and are not reasons to query DB/task state.
- **Automatic host hook:** `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`. Original PT-1 Claude reviewer transcript showed FOUR `PostToolUse:Read` and THREE `PostToolUse:Grep` automatic `reply_activity_observe` attempts, each refused by Vres database guard; it does **not** show successful PostgreSQL contact. The reviewer clarified the hook errors were not visible in their own direct tool results and that their `NO_POSTGRESQL_CONTACT_BY_REVIEWER` means no deliberate DB call, not absence of hook attempts. A later separate zero-tool Claude note contained another `VRES_REPLY_GUARD_WARNING` stop message, not evidence of a successful DB call. **Do not run further hook-bearing native Claude tools until a separately authorized NO-DB-ATTEMPT review mode is established; do not disable installed/global Claude hooks or approve a database target.**
- **Accepted PERSONAL risk model:** P0 ephemeral / P1 reversible project work / P2 protected user-confirmed changes / P3 incident HOLD. Offline source and tests are authorized; **actual Sonnet/high → Opus/medium installation requires new specific informed user consent**. Strict F1 cryptographically independent positive provider remains BLOCKED; this PERSONAL transition never claims to implement F1.

## Accepted PT-1 R1 and provenance

- `feature/personal-governed-chairman-preview-20261027` accepted immutable R1 HEAD **`7b6b7457236cf601fa056152b78713060fe0573e`**, tree **`bcdd89b01dabbd663e1b7d874ad4750718a1c1b0`**, direct failed original R0 parent `8e2628bbf94ffb204796fb51d3056d9eb4e7025f`.
- Pure PT1 preview `src/vres_os/personal_chairman_preview.py` Git blob **`045969e7a0b6f2b4320f9edba5e1629a4b50ec6e`**, corrected PT1 test Git blob **`fcdbc695107d6cc1d9f9c66e5fa6469bc6be64a3`**, unchanged governed Chairman SOURCE blob **`bc160273c1a1f8cfb8a844041da206c90a00769b`**, unchanged `tests/conftest.py` **`1c33bb206dbf42691a6af9a709514bf3cc9994af`**.
- Guarded Windows six selected module run: **189 individually reported PASSED, zero FAILED, `PYTEST_EXIT_CODE=0`**, AppData fence unexpected refusals=0, `integration_opt_in=False`, environment restored, post-test worktrees reported clean. User-uploaded R1 log included test and postcheck sections, but **not original R1 preflight/checkout creation**, and the final marker was printed separately; accept scoped test evidence, NOT full atomic preflight proof.
- Independent Claude review: **`STATIC_ACCEPT`, zero blocking, five informational I1–I5** (parser source-hash gate first; LF/CRLF identity distinction; frozen Python objects not protected issuers; coarse static import test; no installed-model proof). Full Claude report text Git blob **`efb87f1cebb39b8eb2936e5fc3cbe6bc84a65fd2`**, original user raw SHA256 **`60202b1ebd11117c9afc40e1c94aa13faa4cc2ba8803ea24d5da50084c713dc0`**. Original Windows R1 log Git blob **`acbbd341e11ff7246408faddaa214afb4957b4d9`**. Both original R0 failures (188 pass/1 AST-fail/exit1 each) remain immutable and are NOT converted to PASS.
- Previously independent accepted D1B `feature/165-chairman-policy-foundation-20261023` HEAD **`e26cc43acfed9664e497067189962ac847ad266f`**, tree **`65a468ab8b3846219bb37edf1606eb6e1ef67cba`**, unchanged.

## Newly committed PT-2A source (2026-10-29)

**New separate feature branch:** `feature/personal-governed-chairman-pt2a-offline-plan-20261029`.

| Git item | Exact SHA / status |
| --- | --- |
| PT-2A feature HEAD | `22122047cc985ffc8fb3e5d0d30e3d68d8d57df9` |
| PT-2A tree | `a64cdc6cd188e6f9f4186cf5d3887ce82125cf0e` |
| Single direct parent | PT-1 accepted R1 `7b6b7457236cf601fa056152b78713060fe0573e` |
| ADD `src/vres_os/personal_chairman_transition_plan.py` | Git blob `0aa49e386432c7e080da18831a9b6c6afb200ad8` (208 lines) |
| ADD `tests/test_personal_chairman_transition_plan.py` | Git blob `463f6c291a4f52f4056056ab6659237c386ed498` (288 lines) |
| Diff scope | ONE new commit; exactly TWO ADDED source/test paths; no modifications to any previous source/test/policy files |
| GitHub read-back | Branch HEAD, tree, sole parent, two new blobs, old accepted PT1 source/test, Chairman/renderer/conftest blobs all PASS |

**Implementation:** `plan_personal_chairman_transition(accepted_source, claimed_managed_before=None, claimed_distribution_before=None)` uses the previously accepted pure PT-1 byte-pinned renderer. Two **fixed logical target roles** are `managed` and `distribution`: the function accepts NO OS paths and performs NO filesystem, process, database, credential, network, vendor/model or installer I/O. Optional “before” bytes are deliberately named **caller-supplied claims**; one-sided, malformed, oversized or non-Sonnet/high inputs are rejected. Missing pairs produce `BEFORE_COPIES_NOT_SUPPLIED`; divergent pairs produce `MANAGED_DISTRIBUTION_DIVERGENCE`; any bytes not exactly matching accepted SOURCE produce `SOURCE_RELEASE_RECONCILIATION_REQUIRED`. The manifest never includes the raw claimed old bytes, only digests and lengths.

The manifest distinguishes `source_git_blob_lf_normalized` from `source_sha256_as_supplied`, so a CRLF checkout is not misidentified as the LF Git blob. It also labels `PREPARED_OFFLINE_ONLY`, `NO_F1_AUTHORITY`, `NOT_INSTALLED`, `REQUIRED_SEPARATELY`, `effective_model=UNKNOWN`, `installed_state_verified=False`, `claimed_before_provenance=CALLER_SUPPLIED_UNTRUSTED`, `release_pointer=NOT_READ`, `trusted_paths_resolved=False`, `rollback_snapshot=NOT_CREATED`, and **`safe_to_install=False` unconditionally**; truthiness raises TypeError. Even two caller copies matching accepted SOURCE are not real installed-state proof or permission.

**No original P2 bytes read:** Last-observed installed P2 Chairman Sonnet/high, historical 24,208 LF bytes/SHA256 `a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73`, Opus/medium NOT INSTALLED, active physical model unknown. PT2A does not assume original P2 installed body equals the newer independently accepted D1B SOURCE body. An actual installer will require separate documented reconciliation, targeted backup, journal, reparse-point/host checks, truthful release-distribution coherence and full rollback evidence.

**Author-side status:** GitHub objects/changed-path allowlist verified; NO native Windows pytest, independent PT2 source review, provider/model call, installer or installed-host state observation. Do not invent a test count or claim acceptance at PT2A SHA before the operator's evidence.

## Next bounded operator gate (ONE atomic PowerShell script)

The next user action is **NOT a Claude review** (host hooks remain unsafe). Use **normal Windows PowerShell 5.1** and the full text artifact:

`VRES_PERSONAL_PT2A_GUARDED_WINDOWS_VALIDATION_2026-10-29.txt`

Local script SHA256 **`1a707d407dd60cd5115e2a26c43b036e435f45e175170c08876771d80977de21`**, **8,798 UTF-8 bytes**, **174 lines**, no CRLF conversion. Copy the **entire** script from its opening `& {` to final `}` and paste **once**, not line by line. It verifies original clean P2 anchor, accepted D1B and PT1 R1 checkouts, official remote/new PT2A branch HEAD/tree/parent, exact two added files and old blobs, clean diff, **new detached** `C:\Projects\Vres-ChatGPT-Review-Personal-PT2A-20261029`, then seven selected OFFLINE Python3.12 pytest modules with plugin autoload disabled, PG/DB/integration variables cleared process-only and restored, app-data fence/tripwire. Captures individually printed `PASSED tests/`, exit code and posttest Git cleanliness.

**Fail-fast:** ALL operations are inside ONE PowerShell script block; any STOP aborts, reports `VRES_PERSONAL_PT2A_ABORTED`, and does NOT print `VRES_PERSONAL_PT2A_WINDOWS_SELECTED_TEST_COMPLETE`. No rerun blindly. Return complete operator output starting from PT2A preflight; if code/test fails, preserve it for minimal correction and revalidation. Never contact PostgreSQL even SELECT, touch installed/global Claude/profile/credentials, call Vres tools or attempt model activation.

After Windows selected tests PASS and source static is independently assessed through a **separately established no-hook/no-DB-attempt tool environment** (or an appropriately scoped GitHub-only source review), PT2A may be sealed. Then develop PT2B *offline reversible journal/backup/reconciliation testing* with a separately approved boundary. The actual installed PT4 model change remains blocked pending new informed user consent and physical loaded-model verification limits.

## Documentation continuity limitation

Canonical documentation branch `docs/chatgpt-continuity-20261023` remains at HEAD **`9528d4ee8597a3924350b12a58c3a90685a2ec6c`**, tree `af347794bd145f3f055efeb1939f7c42684e4197`. The full original independent PT-1 reviewer report was created as **unattached** GitHub blob `efb87f1cebb39b8eb2936e5fc3cbe6bc84a65fd2`; acceptance handoff unattached blob `cd10928cf0aa8224e79cdcfeadb39e03d6e3b5f7`; a prepared canonical-index blob `707c32738e952ae018cbe79182c98620598719d2` also remains **unattached**. The earlier `create_tree` documentation-branch publication was blocked by tool safety, and no attempts were made here to bypass that restriction. **Do not claim a sealed canonical PT-1 acceptance or PT2 docs HEAD that does not exist.** This local handoff captures the pending review outcome and new source commit, while GitHub source branch is durably published.

Preserve full PERSONAL V-01..V-42 roadmap: Visual Studio fresh/legacy project onboarding, governed orchestration, secure reusable per-current-user credential handles, cross-project continuity; past accepted/rejected per-SHA evidence, original strict F1 design/feasibility holds, E7/PA/F2 and schema-048 incident restrictions.
