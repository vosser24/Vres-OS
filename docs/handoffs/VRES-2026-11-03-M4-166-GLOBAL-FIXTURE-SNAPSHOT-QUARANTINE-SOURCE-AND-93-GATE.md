# Vres-OS — 2026-11-03 M4 #166 synthetic global-governance snapshot / quarantine / rollback checkpoint

**Read first status: SOURCE_COMMITTED / GITHUB_REMOTE_VERIFIED; ISOLATED_LINUX_SYNTHETIC_47_PASS_WITH_PREVIEW_STANDIN; FULL_REPOSITORY_WINDOWS_SELECTED_93_NOT_RUN.** One Windows user's practical PERSONAL daily-operations application, NOT enterprise IAM. This new P1 slice is a pure in-memory transaction over synthetic bytes only. It neither reads nor changes actual Claude global settings, PRISM, installed Vres, legacy projects, current-user credentials or PostgreSQL. Do not mistake a positive synthetic quarantine result for real native Claude hook safety or authority to launch Claude.

GitHub: https://github.com/vosser24/Vres-OS
Canonical documentation branch: docs/chatgpt-continuity-20261023
Canonical READ FIRST: docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md
Prior M4 accepted evidence: docs/handoffs/VRES-2026-11-03-M4-GLOBAL-CLAUDE-PREVIEW-WINDOWS-46PASS-ACCEPT-166-NEXT.md
Full original scope: docs/roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md, 42 original items V-01..V-42.
Current board: docs/roadmap/VRES-PERSONAL-LOCAL-WINDOWS-ACCEPTANCE-AND-FULL-DEVELOPMENT-BOARD-2026-10-31.md.

## 1. Exact new source and GitHub provenance

Dedicated new feature branch: feature/personal-m4-global-adoption-fixture-quarantine-20261103
**New feature HEAD: 31b93704a26bb6c53301242f84dfb36bf2c214ba**
**New feature TREE: 13228785f290d533ce7b2dd1ee322e22be8e3d65**
**SOLE parent: dac3a832ba69f8e49877b3a85a39641f40f151b0**
**Parent TREE: 3026e2d21953373858ddeb51b72af535df05cafd**

Exactly two ADD paths against the accepted previous M4 preview HEAD, confirmed by GitHub compare:
- A src/vres_os/global_claude_fixture_transaction.py, blob ced29e0346aa31abf35b986e2d36fde675d22616.
- A tests/test_global_claude_fixture_transaction.py, blob 3419b0526ee06193d1efea313368b8c38418f4a1.

Both newly created GitHub blob IDs match the exact git hash-object identities of the bytes exercised by the isolated local synthetic tests. Feature commit was created with exact sole parent, fresh dedicated branch, nonforce expected-old-SHA lease and remote HEAD/TREE/parent/changed-path readback. No other product source/test files changed, no main merge/PR or installed update.

Verified unchanged product main: HEAD 9a8acc5d464b96432a93cb95daa9581412fb07ee; TREE 659d3fdd6e635dbaecbd5c492ba7279754edaec7. Previous accepted M4 preview source HEAD dac3a832ba69f8e49877b3a85a39641f40f151b0, TREE 3026e2d21953373858ddeb51b72af535df05cafd, is preserved, as is its bounded Windows 46 named PASS with initial preflight excerpt omitted. Earlier M3 Chairman 52 PASS, M3 session 14 PASS, and integrated M2+#167 254 PASS/3 symlink privilege SKIP belong ONLY to their pinned prior commits. Do not pretend they were rerun on the new source.

## 2. Exactly what the new transaction slice implements

The previously accepted M4 preview (src/vres_os/global_claude_adoption_plan.py) is the reusable *synthetic metadata validation contract*. The new global_claude_fixture_transaction.py consumes that plan, a separately supplied synthetic governance-bytes map and opaque native-state handles. It accepts no real filesystem root and uses NO os/pathlib/process/network/DB/credential/Claude APIs. All operations are in-memory Python tuples/bytes; no native hook is evaluated or installed.

Capabilities:
1. A complete CLAIMED synthetic inventory is cross-checked exactly against synthetic governance bytes and opaque vendor handles. Unknown files, manual blockers, symlink/reparse claims, path traversal/UNC/drive names, Windows case-insensitive duplicates, namespace/file-directory collisions, missing/mismatched entries, excessive size and malformed JSON/duplicate keys/nonfinite settings refuse before any transaction.
2. Governance *file bytes* are captured in immutable Python byte tuples with deterministic per-file SHA256 digests and canonical manifest SHA256 seal; caller-provided SHA claims must match synthetic bytes but do NOT become independent source proof.
3. Native Claude credentials, projects and sessions are represented only as opaque handles. Those handles are never dereferenced or echoed, cannot be submitted as raw byte or text values, and object identity is retained across simulated operations. Native auth/session data are not copied, inspected or changed.
4. Quarantine removes all snapshotted legacy governance files from the SYNTHETIC active namespace and retains exact bytes in a synthetic quarantine partition, with a small state journal. A completed quarantine is idempotent; interrupted simulated quarantine refuses blind replay.
5. Recovery/rollback verifies the entire seal, file partition and event journal and restores the exact original synthetic bytes. A post-snapshot simulated edit or corrupt seal refuses rollback without overwriting the changed data.
6. inspect_global_fixture and simulate_global_claude_fixture_roundtrip render only bounded redacted synthetic status and digest counts. They never display untrusted legacy instruction/credential content or grant authority. Physical immutable disk snapshot, actual global quarantine, durable interrupted-process journal, real first Claude launch, activation, KEEP/DROP, F1 reviewer and independent host clearance are ALWAYS FALSE.

**Important limitation:** The snapshot is an *in-memory fixture prototype*, NOT a durable immutable on-disk backup; the in-memory journal does not recover a real interrupted Windows process. Source is NOT wired to the real installer or user profile, deliberately. A later separate P1 disposable-directory filesystem implementation with explicit local test sandbox gating can build on this behavior. Actual current-user global Claude/PRISM adoption remains P2/P3 held.

## 3. Actual test provenance and original rejected attempt — no invented Windows PASS

Isolated ChatGPT-owned Linux container, NOT user's Windows:
- An initial standalone synthetic pytest run: 38 PASSED / 4 FAILED. All four failed only because the test helper attempted hashlib.sha256 on deliberately invalid None/list/dict/str inputs *before* invoking the validation under test. Original negative retained as REJECTED_TEST_HELPER, not source behavior acceptance.
- Corrected the helper to hash only exact bytes and pass None digest claim for invalid data. R1 standalone isolated run 42 PASSED, exit0.
- Expanded integrated synthetic fixture coverage for directory-type fraud, claimed hashes on vendor-native handles, unverified directories, and one combined snapshot/quarantine/rollback status contract. Final standalone isolated run **47 PASSED / zero failed**, exit0, approximately 0.12 seconds. The source/test bytes of this last run have exact Git blob IDs as in section 1.
- For these container tests, the parent M4 preview validator API was represented by a LOCAL RECONSTRUCTED compatible copy of the preview path/category/manifest validation (its public GitHub source was inspected), NOT an entire checked-out, real GitHub repository dependency/test environment. Therefore this result is **ISOLATED_LINUX_SYNTHETIC_WITH_RECONSTRUCTED_PARENT_API**, not actual full-repo integration, not native Windows and NOT installed hook/PostgreSQL safety.
- New test file has 29 test functions expanded to **47 named parametrized cases** (confirmed actual final pytest output in isolated container): end-to-end exact roundtrip; repeated activation refusal/idempotence; interruption at 0,1,2 and full four files; active/quarantine edits refuse rollback; seal/journal/native-handle mutation; prompt injection and credential filename non-disclosure; malformed JSON/UTF-8; traversal/UNC/drive/control paths; manual blockers; incomplete/partial inventory; forged hashes/reparse; Windows casefold collisions; oversized/invalid bytes; pure stdlib I/O surface, directory/declaration mismatch and source integration status flags.
- **Selected native Windows pytest on the new GitHub source: NOT_RUN.** No installed Windows user-state or native Claude/PRISM runtime action was attempted.

## 4. EXACT next one-atomic Windows P1 offline acceptance gate

Full pinned PowerShell 5.1 script: docs/handoffs/VRES-2026-11-03-M4-GLOBAL-FIXTURE-QUARANTINE-WINDOWS-93-OFFLINE-GATE.ps1
Git blob: cc813db03aa7bfbfbfc4edc68ab005bcfedc409d.

Run in ordinary Windows PowerShell 5.1 **outside Claude Code**. Operator does not use PostgreSQL, installer, real credentials, real global configuration, real PRISM or any legacy project. Before any test, the gate checks official GitHub origin, protected original P2 source HEAD/TREE/clean, new feature HEAD 31b937... TREE 132287..., sole accepted M4 parent dac3a... parent TREE 3026e..., exactly two A-status changed paths and two PRE Git blobs; then creates only a NEW detached checkout C:\Projects\Vres-Review-M4-Global-Fixture-20261103 if absent (never reset protected older reviews). It saves/clears/restores inherited process VRES/PG/DATABASE_URL/GIT/CLAUDE_CONFIG_DIR/Python/pytest variables and fences TEMP LocalAppData.

It selects exactly three test modules:
- tests/test_global_claude_fixture_transaction.py — **47 expected cases, NOT_RUN on native Windows**.
- tests/test_global_claude_adoption_plan.py — **43 expected cases at this descendant source, NOT_RUN**.
- tests/test_claude_contract.py — **3 expected cases at this descendant source, NOT_RUN**.
Total **93 expected DISTINCT NAMED PASSED, zero named FAILED/ERROR/SKIPPED, PYTEST_EXIT_CODE=0**; count individual "-q -rA" passed node IDs rather than a nonexistent aggregate summary. On success the script verifies process environment restoration, POST candidate HEAD/TREE, both source/test blobs, both Git checkouts clean and original protected P2 HEAD/TREE.

Expected terminal marker, NOT YET OBSERVED: VRES_PERSONAL_M4_GLOBAL_FIXTURE_OFFLINE_POSTFLIGHT_COMPLETE_PENDING_EVALUATION.
If any gate refuses, preserve first actual error and do NOT bypass, reset/delete a worktree or overwrite installed P2. Retain source test run status as NOT_RUN until full user Windows result. No reason to rerun older broad 254-case suite.

## 5. Binding OPEN incidents, installed provenance and user consent

**LIVE_SCHEMA_048_INCIDENT=OPEN:** absolutely NO PostgreSQL contact even SELECT, direct or indirect via Vres MCP/CLI/doctor/bootstrap/native hooks/migration/recovery/F2/schema inspection. The new pure functions never connect.
**HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN:** original seven refused native Claude Read/Grep posttool DB-route attempts. NO ordinary native Claude Code launch or installed managed hooks/plugin validation; static source/matcher counts (Stage3–6, in-memory 9-to-0 exclusion) do NOT clear this.
Independent trusted F1/Fable positive authority NOT GRANTED. No real current-user Claude/PRISM settings, actual legacy project, credentials, model/permissions, installed Vres P2 release, external transaction, product main merge or live pilot without independently verified P3 disposition and separately explicit P2 owner approval.

Last HISTORICALLY observed installed P2 release source HEAD 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c, TREE 205c081277ece483c634e1c801c39595abd4549c, historical installed source hooks Git blob 5833973d9be6ccf4263dda2d461cc5994d30416c. Not freshly inspected on the user's Windows PC. Preserve C:\Projects\Vres-P2F-Postinstall-Hardening-20261022 original anchor; prior M4 preview C:\Projects\Vres-Review-M4-Global-Claude-Preview-20261103; M3 briefing C:\Projects\Vres-Review-M3-Chairman-Briefing-20261103; M3 session C:\Projects\Vres-Review-M3-Session-Resume-20261103; M2+#167 integrated; rejected #167; accepted #167 R1; M2 rollback; #167 store; PT1/PT2A–D, E7/E8/C2B/R0/F2, Stage1–6 and all historical protected review worktrees. No deletion/reset.

Preserve original rejections rather than converting them to passes: #168 A12 18P/1F source 345a568b551ac23183c54f10611335adee903b96; A13 28P/1F cdaa39aaa774cef88a4831bf6b157e380fbb69d9; A16 environment-copy uncertainty; A19 blocked source; #167 original 43P/1F corrected R1 44P; first integrated M2+#167 PS5.1 parser refusal pretest, second aggregate-summary wrapper refusal after actual 254P and separate postflight accepted; first M3 status path separator preflight refusal then 14P accepted with initial PRE excerpt absent; M3 Chairman original authored None-default fixture issue discovered static before tests, corrective commit then 52P accepted with PRE excerpt absent; M4 preview 46P accepted with PRE excerpt absent; new fixture 38P/4F original helper then corrected 42P and 47P isolated. Never invent trusted Fable acceptance or real host incident clearance.

## 6. Next roadmap and checkpoint conditions

Keep all original V-01..V-42 requirements, M0–M8 personal roadmap, issues #165–170/#174/#176 and #166 OPEN. Current M2 installed release is P3 HELD. M3 selected Chairman/session continuity offline accepted but native host still held. M4 pure preview selected Windows 46 PASS and new in-memory transaction source committed; complete #166 physical current-user adoption, immutable disk snapshots, truly inactive installed legacy hooks, explicit KEEP/DROP and durable multi-file recovery all PENDING. M5 personal same-Windows-user credential/data-source reuse, M6 #169 Visual Studio/PRISM real legacy onboarding P2/P3 gated, M7 #170 limited daily pilot P2/P3 gated, optional M8 later.

**EXACT NEXT operation:** one guarded Windows PowerShell selected 93-case offline run and evidence evaluation. If success, update docs acceptance with exact source and provenance, then develop the next useful issue #166 disposable-fixture ON-DISK journal/snapshot/quarantine mechanics on another exact-parent P1 source branch without accessing the real profile. If failed, preserve original and correct source/test only after reviewing evidence. Do not start native Claude, touch PostgreSQL or install PRISM.

**Project HARD AUTO-CHECKPOINT:** at or before 20 completed assistant replies since last verified GitHub checkpoint, or conservatively estimated context exceeds 50% (if uncertain, checkpoint early). Stop beginning new phases; verify GitHub docs/main/feature HEAD/TREE/PARENTS, historical installed identity only as actually available, publish all authorized completed source/docs commits with exact parents, nonforce expected-old-SHA updates and remote readbacks, date comprehensive docs/handoffs continuity and prepend newest READ FIRST index, preserve rejected tests and P3 holds, supply ONE complete inline fenced fresh-chat resume prompt and exact verified docs SHA/tree/links and next milestone, then end this session recommending a new ChatGPT chat. Never imply async work, exact unseen context percentage or local Windows access.
