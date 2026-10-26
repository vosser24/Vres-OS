# Vres-OS #165 — Personal C0 Chairman read-only preview: Windows SOURCE_REVIEW_READY and next independent Claude static gate

**Date:** 2026-10-26, Europe/Athens.
**Repository:** vosser24/Vres-OS.
**Source branch:** feature/165-chairman-policy-foundation-20261023.
**Docs branch:** docs/chatgpt-continuity-20261023.
**Status:** **OPERATOR_WINDOWS_C0_SOURCE_REVIEW_READY / CLAUDE_C0_STATIC_NOT_RUN / C0_PYTEST_NOT_RUN / C0_NOT_INDEPENDENTLY_ACCEPTED**.
**Roles:** ChatGPT creates reviewed source/docs commits, user operates Windows, Claude Code independently reads/reviews bounded source before any separately gated offline tests.
**Scope:** single-user PERSONAL Vres, narrowly scoped read-only model-choice *developer API*, not a published/commercial product or existing installed UI/model activation.

## 0. Canonical read-first, prior acceptance, and scope

Read the CURRENT docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md, then THIS new operator READY handoff, then:
1. docs/handoffs/VRES-165-PERSONAL-C0-READONLY-CHAIRMAN-SELECTION-PREVIEW-SOURCE-CANDIDATE-2026-10-26.md — original full C0 source/negative-test authorship handoff, exact source SHA/blobs.
2. docs/handoffs/VRES-165-B2B1-A1-R2-INDEPENDENT-OFFLINE-ACCEPT-PERSONAL-NEXT-PHASE-2026-10-26.md — independently accepted A1 R2 **PARENT**, 93 individual Windows PASS test lines/exit0 and Claude STATIC_PASS/OFFLINE_ACCEPT at its own immutable source SHA.
3. Historical R3 B2B independently DESIGN_ACCEPT strictly for OFFLINE DENY-ONLY and its erratum; B2B v0/R1/R2 independently DESIGN_REVISE.
4. docs/roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md and delivery plan for full V-01..V-42 roadmap; one C0 source candidate does not close it.

**Current next gate:** open ONE NEW Claude Code session from ALREADY-EXISTING C0 worktree and perform independent **STATIC-ONLY** review. DO NOT recreate/fetch/reset/stash worktree or run pytest in this step. On static REJECT/BLOCKED do not test; any correction must be a new ChatGPT-authored source SHA.

## 1. Exact source and unchanged parent identities

| Field | SHA / value |
| --- | --- |
| **C0 preview source HEAD / review target** | **e6bd8cb8f92a779da1469efe738709918e9da6df** |
| Source tree | **afb9e3c88b17c5342425895ca9fa7798f0ad0752** |
| Accepted A1 R2 direct parent | **9754b190083a0ada757ebee07f2ef5b8f312b58e** |
| ADD source | src/vres_os/chairman_selection_preview.py |
| Source blob | **1fb133e5d1b79bc4d6f6e305f5c9b03f6c752658** |
| ADD tests | tests/test_chairman_selection_preview.py |
| Test blob | **79028cf72e33db11efa001687ba77ba7b1bb9ddf** |
| Existing Phase A policy/materializer (unchanged) | src/vres_os/chairman_policy.py blob **36e62d6a2712ac305fd4070bac658b94d61d155e** |
| Existing static template (unchanged) | plugins/vres-os/agents/chairman.md blob **64cba93d6f69960350a0006b594734288f087ccc** |
| Protected test isolation (unchanged) | tests/conftest.py blob **1c33bb206dbf42691a6af9a709514bf3cc9994af** |
| Pytest configuration (unchanged) | pyproject.toml blob **b2d5e30d10d7be0613e90bf3ed1e346be5678969** |
| Clean original personal P2 anchor | C:\Projects\Vres-P2F-Postinstall-Hardening-20261022 @ 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c |
| **ALREADY CREATED** detached Windows review checkout | **C:\Projects\Vres-ChatGPT-Review-165C0-Preview-20261026** |

GitHub source branch and commit were read back separately by ChatGPT: commit e6bd8cb8f92a779da1469efe738709918e9da6df, tree afb9e3c88b17c5342425895ca9fa7798f0ad0752, accepted parent 9754b190083a0ada757ebee07f2ef5b8f312b58e, exactly **TWO ADDED** preview source/test paths with exact blob SHAs; the rest of the source tree is unchanged. No source SHA or installed personal release should be modified by this documentation checkpoint.

## 2. Operator-provided guarded PowerShell proof

The user pasted the following successful bounded Windows checkout output. It is an **operator-reported local command execution**, separately corroborated for repository identity by GitHub objects; not an independent Claude Git/host inspection:

\`\`\`text
=== C0 PERSONAL PREVIEW WORKTREE PREFLIGHT ===
PASS: Original P2 HEAD
PASS: Original P2 worktree clean
remote: Enumerating objects: 11, done.
remote: Counting objects: 100% (11/11), done.
remote: Compressing objects: 100% (6/6), done.
remote: Total 7 (delta 3), reused 0 (delta 0), pack-reused 0 (from 0)
Unpacking objects: 100% (7/7), 4.37 KiB | 154.00 KiB/s, done.
From https://github.com/vosser24/Vres-OS
   9754b19..e6bd8cb  feature/165-chairman-policy-foundation-20261023 -> origin/feature/165-chairman-policy-foundation-20261023
PASS: Remote preview HEAD
Preparing worktree (detached HEAD e6bd8cb)
HEAD is now at e6bd8cb feat(chairman): add #165 personal read-only selection preview
PASS: Preview HEAD
PASS: Preview tree
PASS: Accepted A1 R2 parent
PASS: Preview source
PASS: Preview tests
PASS: Original policy
PASS: Chairman template
PASS: Test isolation
PASS: Pytest config
PASS: Exactly two added preview files
PASS: Detached review worktree clean
SOURCE_SHA=e6bd8cb8f92a779da1469efe738709918e9da6df
SOURCE_TREE=afb9e3c88b17c5342425895ca9fa7798f0ad0752
VRES_165_C0_PERSONAL_PREVIEW_SOURCE_REVIEW_READY
PS C:\Users\User>
\`\`\`

The original guarded script, previously provided to the user, checks the official HTTPS origin, clean original P2 checkout, new distinct destination, fetch of exact remote feature SHA, creation of detached worktree, exact SHA/tree/parent/six blobs, net TWO ADD allowlist versus accepted A1 R2 parent, git diff --check and clean tracked/untracked porcelain. The compressed operator transcript prints PASS labels rather than every raw compared value; do not overstate the local evidence. There are no STOP/error lines in the pasted output.

**NO PYTHON / PYTEST / CLAUDE STATIC REVIEW / POSTGRESQL / PROVIDER / VAULT / INSTALLER / MODEL CHANGE** are reported in this operator checkout transcript. A1 R2 historical independently accepted source remains unchanged.

## 3. Exact C0 candidate scope requiring independent review

The pure module \`src/vres_os/chairman_selection_preview.py\` exports just:
- \`ChairmanSelectionPreviewError\`;
- \`preview_chairman_selection(template: bytes, *, reported_baseline: ChairmanPolicy, proposed: ChairmanPolicy) -> str\`.

This in-memory developer API:
- Revalidates exact caller-supplied typed baseline and proposal.
- Requires \`materialize_chairman(template, reported_baseline).content == template\`, checking only **internal source-template/baseline byte agreement**; does NOT measure installed configuration or authenticate the user's active model.
- Uses the accepted pure \`materialize_chairman\` materializer to compute a proposal while retaining body and LF/CRLF newline conventions.
- Returns deterministic display text for reported baseline, proposed candidate, changed family/effort/version or no-op, computed template and rendered-candidate SHA hashes, and explicit no-install/no-authorization caveats.
- Exposes no installer/apply/approval capability, reads no path and never calls credentials, database, provider, subprocess, live host or a protected runtime.

Last independently observed installed PERSONAL Chairman = Sonnet/high, but the function DOES NOT VERIFY installed state; proposed Opus/medium is UNINSTALLED. No UI, CLI entrypoint or physical model attestation is yet part of this candidate.

The new \`tests/test_chairman_selection_preview.py\` uses in-memory fixtures and pytest. Its authored tests (NOT_RUN) address:
- Sonnet/high -> Opus/medium display and no claim of live observation;
- computed hashes, preservation of body bytes, LF/CRLF;
- noop and version-only preview;
- mismatch between supplied template and claimed baseline;
- wrong policy types, malformed/invalid source template, frozen policy low-level mutation/deleted slot handling;
- no privileged API exports/imports.

Existing Phase A policy/materialization source, protected conftest and static plugin template are unchanged. This is a source preview candidate, not an authorized installation or live model switch.

## 4. EXACT NEXT STEP: new Claude Code C0 STATIC-ONLY review

User starts from PowerShell:

    Set-Location -LiteralPath "C:\Projects\Vres-ChatGPT-Review-165C0-Preview-20261026"
    claude

Use a **NEW Claude session** opened from the C0 worktree, not \`claude --resume\` from an old C0/R1/R2/R3 session. Existing older finished Vres Claude sessions may be closed with /exit but need not all be closed; do not delete old worktrees or clear global Claude configuration.

Give Claude an independent **READ/GREP-only static** scope:
1. Read both C0 new files IN FULL, accepted \`src/vres_os/chairman_policy.py\`, actual \`plugins/vres-os/agents/chairman.md\`, relevant existing \`tests/test_chairman_policy_materialization.py\`, full \`tests/conftest.py\` (1513 lines) and \`pyproject.toml\` pytest settings.
2. Confirm exact non-installed/caller-supplied terminology and verify that mismatched template/baseline data refuses rather than being interpreted as a live check.
3. Review display/version/noop/hashes for consistency; check whether string formatting or canonical template corner cases could falsely suggest a configuration was installed. Validate LF/CRLF and body-preserving tests against accepted materializer.
4. Challenge false-positive test assertions and out-of-scope I/O; ensure the module imports only accepted pure policy code and stdlib, no filesystem/credential/PG/provider/child process and no generated positive permission API.
5. Report any actual bugs BLOCKING; cosmetic observations INFORMATIONAL, proportionate to personal use. Return exactly \`STATIC_PASS\`, \`STATIC_REJECT\`, or \`STATIC_BLOCKED\`, exact source SHA, file/line coverage, proof-limit disclosure and test isolation suitability.
6. \`PYTEST_NOT_RUN\`, \`NO_SOURCE_MODIFICATION\`, \`NO_AUTHORITY_ISSUED\`, \`NO_MODEL_ACTIVATION\`; finish marker **VRES_165_C0_PERSONAL_PREVIEW_STATIC_REVIEW_COMPLETE**.
7. Even on STATIC_PASS do **not** run pytest yet; next user-reviewed separate selected test gate.

**Only future approved test selection, never in the static gate:**

    py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_selection_preview.py

No broad tests, extra version probes, retries, database startup or contacts, or runtime model switch. A future clean single selected Windows test and independent evidence-only review are required before declaring C0 independently accepted.

## 5. Standing safety and personal-user proportionality

Vres is the user's PERSONAL single-user environment, NOT a published commercial product. Do not introduce enterprise IAM, public certificate-chain ceremonies, multi-tenant rules or signed commercial release burdens for an inert preview. Preserve only necessary concrete local safety: truthful baseline/proposal display, no silent installed switch, no credential exposure, bounded offline tests.

**LIVE_SCHEMA_048_INCIDENT=OPEN** means ABSOLUTELY NO PostgreSQL contact, even SELECT, nor Vres startup/health/bootstrap that could point at the incident database. Original program F1 independently authenticated consent/history/validator and issue #165 OPEN/PARTIAL. User-global Claude settings/hooks/plugins, real vault/credentials/keyring, protected provider/Fable, native signing, model install, physical host #169 observation, PR/main merge and release are separately held until explicit approval. Installed PERSONAL release remains 20261022172833-4d82147b from original P2 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c, Chairman Sonnet/high; Opus/medium UNINSTALLED candidate. The last independently accepted A1 R2 SHA is 9754b190083a0ada757ebee07f2ef5b8f312b58e, 93 actual reported individual PASSED lines / exit0, Claude report-only OFFLINE_ACCEPT. Old A1 R1 71/exit0, B2A R3 95/exit0 and all earlier per-SHA accept/reject records retained. VRES_REPLY_GUARD_WARNING indicates Vres protected task persistence is not verified; do not query database to "heal" it.

Full V-01..V-42 roadmap, D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 blocked, L-04 OPEN, PA-01..08 incomplete are still open/held where applicable. New preview source is not yet installed; no impact on product main.

## 6. Next-session short resume

**CURRENT C0 feature source SHA:** e6bd8cb8f92a779da1469efe738709918e9da6df, tree afb9e3c88b17c5342425895ca9fa7798f0ad0752, direct accepted A1 R2 parent 9754b190083a0ada757ebee07f2ef5b8f312b58e, EXACT 2 ADD files source blob 1fb133e5d1b79bc4d6f6e305f5c9b03f6c752658 and tests blob 79028cf72e33db11efa001687ba77ba7b1bb9ddf, pure read-only personal caller-supplied preview; no installed model reads or writes. **OPERATOR WINDOWS C0 REVIEW WORKTREE READY** in C:\Projects\Vres-ChatGPT-Review-165C0-Preview-20261026, clean and detached with expected full marker. **CLAUDE C0 STATIC REVIEW NOT_RUN, WINDOWS PYTEST NOT_RUN, C0 SOURCE ACCEPT NOT_GRANTED**. Next new Claude Code from C0 folder with independent static Read/Glob/Grep-only review; no tests until separate gate. Preserve personal-use scope and original F1/#165, PostgreSQL no-contact, credential/model/install/main holds.
