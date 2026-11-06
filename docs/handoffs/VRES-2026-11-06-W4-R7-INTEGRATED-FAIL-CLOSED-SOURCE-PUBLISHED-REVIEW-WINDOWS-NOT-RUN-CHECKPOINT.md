# Vres-OS — 2026-11-06 W4 R7 integrated fail-closed source correction; independent review and Windows gate NOT_RUN

**HARD GITHUB CONTINUITY CHECKPOINT — END CURRENT CHAT; START A NEW INDEPENDENT REVIEW CHAT.**

## 1. Product scope and absolute safety holds

- Vres-OS is a practical PERSONAL daily-operations application for ONE Windows user; NOT enterprise IAM, multitenancy, a second Chairman or a duplicate task/memory database. Preserve V-01..V-42, M0..M8, #163/#164/#165–170/#174/#176, W0 integration audit, historical E7/F2/F1/P3/Stage1–6 and proportional P0/P1/P2/P3 operator approvals.
- Repository https://github.com/vosser24/Vres-OS ; canonical docs branch docs/chatgpt-continuity-20261023 ; product main 9a8acc5d464b96432a93cb95daa9581412fb07ee UNCHANGED, no main merge.
- LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL EVEN SELECT, direct or indirect. HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: NO ordinary native Claude Code, installed hooks or potentially hook-routed commands.
- Independently trusted F1/Fable positive authority NOT_GRANTED. Original P3 incident disposition OPEN. No installation, runtime launch, migration, Windows Sandbox R2, real credentials, profile, PRISM, legacy project or protected original Windows worktree access/changes.
- Protected installed P2 source 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c. Physical installed identity NOT_REVERIFIED. Previously reported Chairman Sonnet/high; Opus/medium NOT_INSTALLED.
- Completed real TASK-DAY-01: preserve C:\Projects\Vres-Personal-Notes\TASK-DAY-01.md and C:\Projects\Vres-Desk-Personal; DO NOT reopen, change, recreate or delete.
- No Windows source/test/output root creation or Windows gate execution without NEW explicit authorization. No interrupted W4 stage deletion; no P2/main overwrite.

## 2. Live GitHub state and author-side source publication

- First read live docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md and the prior 2026-11-06 R5 independent-reject/R6 corrective handoff. GitHub connector returned R6 remote ref HEAD 11e57b2d325303df326281408af09a247247bb56; docs remote ref before this checkpoint HEAD ba24a5a83bb59571b5fedad5a4b0b927d533b416; main HEAD 9a8acc5d464b96432a93cb95daa9581412fb07ee.
- Existing R6 created tree fc25d2f259c9bf3dac17b5aaa3d3873f254a58a6. R6 source blob d356e420d0d15acd57f8f5135a28ca6f238d4eda, tests blob 04fceb01b3a1e0d889ef55194ed1abb4242e7ca3. R5 parent 903ed3c3ccd7bd0d4471cd04ecbc46f0c0742ef6. R6 independent operational STATIC_REJECT (current chat), advisory narrow STATIC_ACCEPT read-only only, destructive rollback STATIC_REJECT as a capability.
- NEW R7 feature branch: feature/personal-w4-r7-integrated-stage-safety-20261106.
- R7 exact published HEAD: c9ed861ea47a043ed65b42c7ce0aca6c338e9b31.
- R7 Git TREE created by GitHub create_tree: d819ae594a6eee0344a594825a16661799a1c6e8.
- R7 commit created with exactly ONE specified parent: R6 11e57b2d325303df326281408af09a247247bb56.
- R7 source: src/vres_os/personal_w4_no_launch_release.py; new blob ac5b1684de3c44bb531fbf0f4af17f4e1d98cf35.
- R7 tests: tests/test_personal_w4_no_launch_release.py; new blob 95119d76f6a75c1bdd528a1747f73f81a6843788.
- Non-force update_ref with expected R6 SHA PASS; remote R7 branch HEAD and both exact file blobs readback PASS. R6→R7 compare ahead 1 / behind 0, precisely TWO modified paths: source +116/-22; tests +52/-2. No other code paths changed.
- GitHub connector fetch_commit exposes ref SHA and per-file patches but NOT raw commit tree/parent headers. Exact R7 created tree/sole parent are supported by create_tree/create_commit inputs and ahead/behind readback; separate direct raw-object HEAD/TREE/parent header verification remains NOT_VERIFIED.
- Original release owner src/vres_os/release_artifact.py blob 1d26d02dab7967f0e966bf26a757084669424b0b; release_inputs.py a0cdf3195f0cf0f2a61ce32521a74f78260832f7; pyproject.toml b2d5e30d10d7be0613e90bf3ed1e346be5678969. UNCHANGED in R7. W3 R2 accepted narrow base 982e77f2f4974b4fbca5da91d3e11aeb56e40271 remains ancestor. Preserve R1 acd444..., R2 b6294..., R3 f9742..., R4 1d4a738..., R5 903ed3..., R6 11e57... rejected/not-run provenance.

## 3. Integrated R7 implementation — AUTHOR WORK ONLY, not a security acceptance

1. `_GitReaderScope` retains strong references to ancestry, source verification and staging Git transports through every operation/failure path; failed closes remain in `_PENDING_GIT_READERS` for bounded synchronous retry and an atexit retry. No further stage may start while unresolved reader references remain. This improves top-level retriability but does NOT prove OS child or descendant termination.
2. Both Git spawning paths now specify `cwd=exe.parent` instead of inheriting the caller working directory. This mitigates a particular search-path risk but is NOT DLL/auxiliary-loader authentication.
3. `_require_trusted_windows_stage` explicitly HARD REFUSES actual Windows Git/staging operations pending a separately proven signed Git/DLL/loader chain, bounded spawn/descendant containment and filesystem staging-safety implementation. Therefore R7 CANNOT and MUST NOT be called an operational Windows staging release candidate. This refusal is deliberate.
4. `_root_identity` and `_assert_root_identity` perform same-file-system device/inode identity checks around major staging/ZIP milestones. These detect some substitutions but cannot close Windows reparse/hardlink/TOCTOU races; Windows remains hard refused.
5. Successful build retains `W4-INCOMPLETE.json` as a diagnostic journal rather than unlinking it by path. The `W4-RECEIPT.json` supersedes that journal and makes `inspect_interrupted` refuse completed roots. Original owner `stage` code still owns path-based temporary manifest rename/unlink and remains unmodified. Do not mistake marker preservation for comprehensive no-deletion safety.
6. Prior R6 .git/commondir reject guard is retained unchanged.

## 4. Tests and precise evidence

- R7 has 20 AUTHORED Python test functions (R6 had 17). New authored tests target Windows fail-closed, failed top-level cleanup reference/retry and root identity-shift refusal; an existing Git batch test now asserts explicit cwd; existing ZIP test expects retained journal, and binary-hash test isolates its check from the hard Windows hold.
- R7 independent second-agent review: NOT_RUN. R7 PYTHON SYNTAX: NOT_RUN. R7 PYTEST: NOT_RUN. R7 original-owner Windows integration: NOT_RUN. R7 real ZIP/source manifest and ZIP reproducibility: NOT_RUN. Git and DLL signed closure: NOT_RUN. Wheel dependency closure: NOT_RUN. Physical P2 identity: NOT_REVERIFIED. No source or Windows test output was created in this chat.
- Source patch was inspected by author and published/read back via GitHub. Do not call this a test PASS or independent STATIC_ACCEPT.
- Historical: W4 R1 six author-simulated PASS at R1 SHA only, operational STATIC_REJECT; R2 ten authored NOT_RUN/STATIC_REJECT; R3 twelve authored NOT_RUN/STATIC_REJECT; R4 fourteen authored NOT_RUN/STATIC_REJECT; R5 sixteen authored NOT_RUN/independent STATIC_REJECT; R6 seventeen authored NOT_RUN/independent operational STATIC_REJECT; R7 twenty authored NOT_RUN/independent review NOT_RUN.
- W1 R2 operator-reported offline Windows 18 PASS in narrow original-source scope; W2 R2 operator-reported original-source Windows adapter PASS, genuine pytest/root symlink NOT_RUN; W3 R2 operator-reported 13-blob original-source synthetic Windows adapter PASS, genuine pytest/real integrations NOT_RUN. Never transfer PASS between commits.

## 5. Open blockers and next exact safe action

- Trusted Windows Git executable plus all DLL/auxiliary loader dependencies have NOT been independently verified; process creation before a subprocess timeout and descendants not bounded by R7.
- Global retained references and atexit retry do NOT guarantee cleanup of unkillable processes. Inspect reader ownership, exception masking and process lifecycle carefully.
- Original owner `release_artifact.py` stage uses path-based temporary manifest write/rename/unlink and final stage rename; Windows junction/reparse/alias/hardlink/TOCTOU and hostile parent substitution remain unproven. Source and ZIP outputs NOT tested with actual original-owner Windows evidence.
- R7 now hard-refuses Windows; DO NOT bypass/monkeypatch that hold in a real gate. Synthetic test bypasses are NOT operational authority.
- Runtime dependency versions/wheels and their secure closure unresolved. P3/F1/Fable/installed P2/#169/#170 HELD.
- NEXT EXACT ACTION in a FRESH independently distinct READ-ONLY senior Python, Git supply-chain, Windows filesystem and release-recovery reviewer chat: verify live GitHub docs/R7/main HEADs, raw trees/sole parents if accessible, R6→R7 exact patches, full R7 source, all 20 tests, original owner/inputs/pyproject. Assess whether retention logic can mask exceptions, whether Windows hard hold is genuinely enforced before any child/output-root creation, retained-journal/receipt consistency, Git loader and path protection, and whether any regression/counterexample exists. Return THREE verdicts separately: source archive operational staging, read-only advisory interruption inspection, destructive rollback. Do not accept R7 automatically.
- If independent review finds a truly bounded defect, correct it only with a dedicated exact-parent branch and verified expected-SHA non-force readback. Do not start endless microtests. The coherent follow-on milestone is a trusted no-Git-spawn or independently attested, contained Git executable chain plus handle-bound file staging model; only then one original-owner, SOURCE-ONLY, OFFLINE, NO-LAUNCH Windows gate with NEW explicit approval BEFORE any Windows source/test/output root or execution. Later runtime wheel closure, P3/F1/Fable and real UAT require separate evidence/consents.
- Preserve W0 original integration audit at docs/handoffs/VRES-2026-11-05-W0-EXACT-GITHUB-RELEASE-INTEGRATION-AUDIT.md and full pending roadmap docs/roadmap/VRES-PERSONAL-COMPLETE-PENDING-DEVELOPMENT-RELEASE-AND-REAL-WINDOWS-UAT-PLAN-2026-11-05.md. Preserve all old handoffs, protected worktrees, rejected commands/tests and exact original incidents.

## 6. Hard continuity and checkpoint integrity

- At/before 20 completed assistant replies after last verified checkpoint OR conservatively near >50% context, publish authorized completed source/docs on correct branches with exact parent, non-force expected-SHA lease, remote HEAD/tree/parent/blob readback to the extent observable; do not claim raw tree/parent if unavailable.
- End this session at the verified documentation checkpoint and provide FULL fresh-chat resume prompt inline (not just a link). No background job, no Windows or installed state claims. Reset counting only after checkpoint verified.
- Checkpoint prepared following GitHub R7 author-side patch publication; final canonical docs commit SHA/tree/parent and both docs blobs are to be recorded from actual publication results, NOT guessed in this precommit handoff.
