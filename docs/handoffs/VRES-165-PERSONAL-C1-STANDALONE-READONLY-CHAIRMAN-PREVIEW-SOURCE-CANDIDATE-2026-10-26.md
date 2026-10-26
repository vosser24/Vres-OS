# Vres-OS #165 — Personal C1 standalone READ-ONLY Chairman preview CLI source candidate

**Date:** 2026-10-26, Europe/Athens.
**Repo:** vosser24/Vres-OS.
**Canonical documentation branch:** docs/chatgpt-continuity-20261023.
**Source branch:** feature/165-chairman-policy-foundation-20261023.
**STATUS:** **C1_SOURCE_CANDIDATE_COMMITTED / AUTHOR_STATIC_PREFLIGHT_ONLY / INDEPENDENT_CLAUDE_STATIC_NOT_RUN / WINDOWS_PYTEST_NOT_RUN / C1_OFFLINE_ACCEPT_NOT_GRANTED / NOT_INSTALLED**.
**Operating model:** PERSONAL single-user Windows Vres; ChatGPT source author/committer, user Windows operator, Claude Code independent reviewer/evidence evaluator. No published-product IAM, public signing, or external enterprise security ceremony is introduced.

## 0. Read-first and exact source lineage

Read CURRENT docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md first, then THIS new C1 source candidate handoff and:
1. docs/handoffs/VRES-165-PERSONAL-C0-INDEPENDENT-OFFLINE-ACCEPT-PROCEDURAL-ANOMALY-AND-NEXT-PHASE-2026-10-26.md — C0 pure read-only preview independently OFFLINE_ACCEPT at direct source parent.
2. docs/handoffs/VRES-165-PERSONAL-C0-WINDOWS-34-PASS-POWERSHELL-ELSE-ANOMALY-EVALUATION-PENDING-2026-10-26.md — immutable 191-line Windows C0 test transcript, C0-PROC-01 after-test PowerShell else anomaly (nonblocking at accepted C0 SHA).
3. docs/handoffs/VRES-165-B2B1-A1-R2-INDEPENDENT-OFFLINE-ACCEPT-PERSONAL-NEXT-PHASE-2026-10-26.md — prior accepted offline DENY-ONLY A1 R2, separate from C0/C1 CLI.
4. Accepted Phase A ChairmanPolicy and materialize_chairman code, shipped plugin source Chairman template, accepted B1/B2A, historical R3 denial-only design and erratum, and V-01..V-42 development roadmap.

**EXACT NEW C1 GitHub source identity (independently verified by ChatGPT against GitHub commit, feature HEAD and base/new recursive tree comparisons):**

| Item | SHA or exact path |
| --- | --- |
| **NEW C1 source HEAD** | **c545556a4ba9ba48f140e7379da960708a7f3c8d** |
| **NEW source tree** | **65c7b29f0be7b5c8f930d2383a0a4da8d6193268** |
| **Direct parent / accepted C0** | **e6bd8cb8f92a779da1469efe738709918e9da6df** |
| Parent tree | afb9e3c88b17c5342425895ca9fa7798f0ad0752 |
| **ADDED C1 standalone module** | src/vres_os/chairman_selection_cli.py |
| C1 source blob | **6fd0ddcd2b82fca4a48f6a790fee3d0e6ae657d1** (114 Git-added lines) |
| **ADDED C1 selected tests** | tests/test_chairman_selection_cli.py |
| C1 test blob | **599dccb8dc10487796d71337f80a76f089024dbd** (215 Git-added lines) |
| Already independent OFFLINE_ACCEPTED C0 preview, UNCHANGED | src/vres_os/chairman_selection_preview.py blob **1fb133e5d1b79bc4d6f6e305f5c9b03f6c752658** |
| Accepted Phase A policy materializer UNCHANGED | src/vres_os/chairman_policy.py blob **36e62d6a2712ac305fd4070bac658b94d61d155e** |
| Shipped Chairman static template UNCHANGED | plugins/vres-os/agents/chairman.md blob **64cba93d6f69960350a0006b594734288f087ccc** |
| Protected conftest UNCHANGED | tests/conftest.py blob **1c33bb206dbf42691a6af9a709514bf3cc9994af** |
| Python/test config UNCHANGED | pyproject.toml blob **b2d5e30d10d7be0613e90bf3ed1e346be5678969** |

Exactly TWO ADDED C1 source/test paths, ZERO MODIFIED or DELETED old files versus accepted C0 parent. GitHub new tree was based exactly on parent tree, recursive old/new blob-path map verified strict two-ADD allowlist, and the new single-parent GitHub source commit and feature branch HEAD were independently read back. Commit is unsigned and NOT protected trust/approval.

## 1. Personal functionality actually authored (not yet independently accepted)

Standalone Python module:

    src/vres_os/chairman_selection_cli.py

invoked after isolated checkout, Python src path resolution and separate acceptance via:

    py -3.12 -B -m vres_os.chairman_selection_cli --source-root "<review-source-checkout>" --reported-model sonnet --reported-effort high --proposed-model opus --proposed-effort medium

The command requires explicit source root and BOTH explicit reported/proposed model and effort options. It supports supported Sonnet/Opus family aliases and low/medium/high efforts; optional reported/proposed version default is visibly documented as version 1 for source policy comparison, not runtime authority. No model provider is invoked.

**Allowed source read:** it reads ONLY the fixed source-checkout-relative file **plugins/vres-os/agents/chairman.md** under the explicitly user-selected source root. No glob, filesystem discovery, installed Claude config lookup or vault scan; missing/symlink/not-file/oversized template refuses with neutral CLI status. Bound at 512 KiB + 1 byte and never outputs raw template contents or caller-provided filesystem path in fixed error messages. Its sole intended file I/O is the bounded source-template READ; stdout/stderr are used only for human-readable display/error. This C1 read path is a separate reviewed extension of PURE C0, not a secret/installed-config reader. The new module does NOT import vres_os.cli, bootstrap, db, keyring, psycopg, provider APIs or model dispatch.

**Source/model semantics:** reuses accepted C0 preview_chairman_selection and accepted Phase A materialize_chairman. The source template MUST byte-match caller-supplied reported baseline through C0; this only checks internal supplied source consistency and does NOT prove an installed setting. Display explicitly says **Reported baseline (NOT live-verified)** and **Proposed candidate (NOT installed)**. It shows changed model, effort, optional version or no-op, genuine source/candidate hashes and "No approval, settings change, model activation or installation was performed."

**Windows console usability:** C0's UTF-8 em dash title is displayed with an ASCII hyphen by the thin C1 stdout boundary. C0's accepted source/API is not modified; this avoids a known informational legacy Windows codepage rendering issue without introducing an encoder or config write. One successful preview exits status 0; malformed/absent source template or inconsistency is a neutral PREVIEW_REFUSED, exit 2. Argparse rejects absent/unsupported choices/version before reading the source file.

**NO APPLY ROUTE:** there is no option for writing/configuration, approval, switching, global hooks/plugins, signing or installer. This is a **developer user-invokable source-checkout command**, not yet a shipped native installed Vres CLI or registered installed command. It must not be described as reading the active installed Chairman. A future user-approved model switch/rollback is a different tranche.

## 2. C1 new tests AUTHORED — NOT RUN

Separate NEW C1 tests, scoped to src/vres_os/chairman_selection_cli.py, use disposable pytest tmp_path fixture to create only **plugins/vres-os/agents/chairman.md INSIDE TEST TEMP**. This is the sole authorized fixture write and does not touch the real repo plugin file or user-global config.

Fourteen distinct test functions plus parametrized cases cover:
- Human-readable ASCII console output and explicit historical/not-installed/preview-only language.
- Template unchanged after actual CLI main() call, with source/candidate content SHA display.
- Exactly ONE opened file at the fixed checked-out template subpath in READ-BINARY mode (Path.open monkeypatched to deny any other read/write path).
- Native LF and CRLF source/template data; preview does not rewrite.
- No-op model/effort case.
- **Model-only and effort-only** display independently (additional useful I1 C0 reviewer coverage without changing accepted C0).
- Explicit version number display without authority.
- Invalid explicit versions (zero, negative, too large, invalid strings) are argparse refusals before template read.
- Invalid model/effort choices rejected by parser rather than silently substituted.
- Missing explicit --source-root, missing fixed source template and refusal of unsafe/disallowed or malformed source contents including over 512 KiB.
- Reported template/baseline mismatch returns neutral error, with no user path/file content echo.
- No positive privilege/DB/provider/installer names on the CLI import surface.

**Current status AUTHOR_STATIC_ONLY.** Source/tests were examined by ChatGPT for bounded imports, exact fixed source path, limited binary read and safe output; NO independent Claude static review, live Windows CPython execution, selected pytest, OS/network attestation or C1 OFFLINE_ACCEPT. Do NOT reuse accepted C0 34-PASS test result to claim C1 PASS or invoke any unreviewed CLI on personal installed environment.

Potential reviewer considerations, to evaluate rather than hide:
- A source-root directory may be user-supplied, including an incorrect checkout. The module checks template consistency but intentionally does not authenticate the user's live installed model.
- Symlink denial is for the final fixed candidate file, not a full Windows reparse/junction lineage security proof. This is personal explicitly-chosen source checkout, not a privileged provider.
- Tests create disposable temporary fixture files, so they are not strictly in-memory-only, though the reviewed runtime operation is read-only.
- CLI is source-worktree-invokable through a temporary PYTHONPATH pointing at that checkout's src directory; it is not a globally installed console script.
- Cli parser argparse invalid-option messages may include the invalid user-supplied argument, but never secret template content.
- This is not a pytest/test-result claim; independent reviewer to decide if any correctness concern is blocking.

## 3. Next single step — guarded fresh Windows C1 source worktree only

User explicitly requested ChatGPT to proceed with pragmatic step-by-step personal development. Do NOT initiate full enterprise security reviews, raw database tests or unnecessarily rerun accepted parent tests. The first Windows step is bounded new isolated read-only source checkout verification; Python/pytest and Claude static are separate future gates.

**Operator original P2 anchor:** C:\Projects\Vres-P2F-Postinstall-Hardening-20261022 @ exact HEAD 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c and clean status.
**Proposed NEW detached C1 review directory:** C:\Projects\Vres-ChatGPT-Review-165C1-CLI-20261026.

PowerShell gate methodology from prior C0:
1. STOP if original P2 directory is missing/dirty or original HEAD differs. Verify official origin https://github.com/vosser24/Vres-OS.git (or same HTTPS without .git). STOP if C1 destination exists; do not reset/overwrite old folders.
2. Fetch only feature branch ref into original P2 repo with --no-tags. Require fetched SHA EXACT c545556a4ba9ba48f140e7379da960708a7f3c8d; no changed checkout of P2.
3. Create NEW detached C1 worktree at exact SHA; verify HEAD c545556a4ba9ba48f140e7379da960708a7f3c8d, tree 65c7b29f0be7b5c8f930d2383a0a4da8d6193268, direct parent independently accepted C0 e6bd8cb8f92a779da1469efe738709918e9da6df.
4. Verify exact two new C1 file blobs, unchanged accepted C0 and Phase A policy/blob, static template and protected conftest/pyproject; exactly TWO source/test **ADDED** paths compared to C0 parent, git diff --check exit0, clean detached worktree status.
5. Final marker must be **VRES_165_C1_PERSONAL_PREVIEW_CLI_SOURCE_REVIEW_READY**. User pastes full PowerShell output to ChatGPT. No Claude/Python/pytest in THIS step.

After READY, ChatGPT will prepare precise **fresh Claude Code STATIC-ONLY** prompt using new C1 directory. Only after STATIC_PASS and operator approval, run EXACTLY ONE selected offline Windows pytest on **tests/test_chairman_selection_cli.py**, preserving real output, original source sha/head, new temp-root fixture fence, exit and worktree status, with no hidden retry or extra py version probe. Independent report-only evidence evaluator then decides C1 OFFLINE_ACCEPT/REJECT/BLOCKED at exact source SHA; no installed Vres model changes.

**Eventual manual preview use AFTER separate source acceptance only:** set PYTHONPATH transiently to the accepted C1 review checkout's src (no pip installation) and call the standalone module with --source-root the SAME reviewed checkout. Restore or clear the old PYTHONPATH after execution. This reads only source plugin template and displays only; it does NOT touch active installed Sonnet/high. Do NOT execute this during source worktree preflight.

## 4. Unchanged personal safety and incident holds

**LIVE_SCHEMA_048_INCIDENT=OPEN: ABSOLUTELY NO PostgreSQL contact, EVEN SELECT**; do not start Vres, reconnect, bootstrap, query, migrate or inspect held DB. D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 blocked, L-04 OPEN, PA-01..PA-08 pending. Original issue #165/F1 real authenticated operator-event/protected head/Fable positive authority still OPEN/PARTIAL and is NOT satisfied by source-local model-preview printing.

Last user-observed installed Windows personal Chairman remains **Sonnet/high** at release 20261022172833-4d82147b from P2 source 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c. Opus/medium is a proposed **UNINSTALLED** candidate, not a measured active system state or approval. No real credentials/vault/keyring, global Claude hooks/settings/plugins mutation, protected Fable/provider, signing, native install warrant, installer, live model change, real #169 physical host observation, PR/main merge or release without explicit separate authorization. No hidden task state fix.

Previous Claude evaluator reported distinct **VRES_PERSISTENCE_WARNING** (instruction not safely staged) and **VRES_REPLY_GUARD_WARNING** (pre-reply task gate unverified). Treat both as unresolved Vres task persistence limitations; canonical GitHub docs and exact source SHA are durable continuity. Never start/connect the incident DB even to investigate warnings.

All original 42 Vres functionalities, personal adoption/legacy-project workflow, procedural memory, knowledge, credential handle reuse and safe database registry remain desired, not declared implemented because C1 was committed.

## 5. Historic per-SHA verdicts and compact resume

- Current new C1 source candidate c545556a4ba9ba48f140e7379da960708a7f3c8d is **NOT YET reviewed/tested/accepted**; its parent C0 at e6bd8cb8f92a779da1469efe738709918e9da6df is independently OFFLINE_ACCEPT at 34 individually observed PASS lines, wrapper exit0; C0-PROC-01 (standalone PowerShell else after PASS) nonblocking and five informational findings remain historical.
- A1 R2 pure denial-only OFFLINE_ACCEPT 9754b190083a0ada757ebee07f2ef5b8f312b58e (93 individual PASS/exit0), A1 R1 OFFLINE_ACCEPT 1b406c788057f0cb2a8a57578b89110a11b76161 (71 individual PASS/exit0), B2A R3 OFFLINE_ACCEPT 32847410952e9d4620bf7046cbee4a41a7ddc73b (95 individual PASS/exit0 with R3-PROC-01 extra interpreter probe), earlier B2A R2 91/92 REJECT, original B2A static REJECT, B2B design v0/R1/R2 DESIGN_REVISE / immutable R3 design-only DESIGN_ACCEPT, Phase A R2 53/53, B1 99/99, F2 101/101 plus 3/3, P2-A1 guard R4 183/183 previous per-SHA accepted or rejected as individually recorded. None silently superseded by C1.
- Full V-01..V-42 original roadmap and all K0/PA/D2/F2/R0/L-04 incident/legacy holds remain active.

**NEXT-SESSION RESUME:** Read latest canonical docs index and THIS C1 source handoff. Feature HEAD **c545556a4ba9ba48f140e7379da960708a7f3c8d**, tree **65c7b29f0be7b5c8f930d2383a0a4da8d6193268**, direct accepted C0 parent **e6bd8cb8f92a779da1469efe738709918e9da6df**, strict TWO ADD files src/vres_os/chairman_selection_cli.py blob **6fd0ddcd2b82fca4a48f6a790fee3d0e6ae657d1**, tests/test_chairman_selection_cli.py blob **599dccb8dc10487796d71337f80a76f089024dbd**. Cli is an explicit user-root selected checked-out source-template-only READ, stdout pure previous C0 preview, no install/apply/DB/provider; C1 author static only, new Windows checkout NOT_CREATED, Claude independent static NOT_RUN, Windows pytest NOT_RUN. Next user guarded new detached C1 Windows source checkout, STOP on mismatch, then Claude static, separately selected one offline test and report-only acceptance. Installed Sonnet/high unchanged; Opus/medium uninstalled. Personal-use proportionate methodology, no Postgres even SELECT, all protected credentials/global Claude/runtime/model/main holds, two independent Vres persistence warnings unresolved.
