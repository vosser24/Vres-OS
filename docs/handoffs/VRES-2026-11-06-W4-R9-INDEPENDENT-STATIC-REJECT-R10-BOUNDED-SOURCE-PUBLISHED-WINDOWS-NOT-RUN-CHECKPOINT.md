# Vres-OS — 2026-11-06 W4 R9 independent review; R10 bounded source published; Windows held

**HARD CONTINUITY CHECKPOINT — END THIS CHAT ON PUBLISHED DOCUMENTATION, THEN RESUME IN A FRESH CHAT WITH AN INDEPENDENT R10 READ-ONLY REVIEW FIRST.**

## 1. Product, repository and unchanged scope

Vres-OS is a PRACTICAL PERSONAL daily-operations app for ONE Windows user. It is NOT enterprise IAM, multitenancy, a second Chairman, a duplicate task/memory database, or a collection of unrelated utilities. Preserve ALL V-01..V-42 requirements, M0..M8 integrated roadmap, #163/#164/#165-170/#174/#176, W0 owner integration audit, W1/W2/W3 original evidence, W4 R1-R9 attempts and rejection history, E7/F2/F1/P3/Stage1-6 decisions, and proportional personal P0/P1/P2/P3 approvals.

Repository: https://github.com/vosser24/Vres-OS

Canonical docs branch: `docs/chatgpt-continuity-20261023`
Before THIS documentation publication, LIVE docs HEAD verified: `0a194270cb962f4f43943859b7faa0a472221399`
Prior docs CREATED tree recorded: `75bb87a77e0e223bd895c1de217dda5c3187240e`; its raw header was NOT independently retrieved.
Current new documentation commit/tree are reported AFTER non-force publication/readback, not circularly inferred here.

Product main: `9a8acc5d464b96432a93cb95daa9581412fb07ee` verified unchanged. No main merge.
Accepted W3 R2: `982e77f2f4974b4fbca5da91d3e11aeb56e40271`.
W4 R8: `f7c37a788c513dd21c7f75cbc074e6717c37f809`.
W4 R9: `cdbf6824333bc257854dcc4cdcfbfc3cfaa7222d`.

## 2. R9 read-only review findings (before R10 authoring)

Source R9 branch was live verified, R8→R9 one commit ahead, six exact changed paths, docs/main stable. Independently recomputed Git SHA-1 identity of six source/test files, pyproject and two docs files: 9/9 PASS. Independently fetched and computed SHA-256 with migration normalization for SQL migrations 001 through 041: 41/41 PASS for unchanged R9 GitHub bytes. These hash/readback checks do NOT equal actual integration/test execution or a publisher signature.

Read the COMPLETE R9 owner, no-spawn Git, POSIX output, W4 entrypoint, migration inputs, 28 test functions, pyproject and R8→R9 diff. Verdicts:
1. OPERATIONAL ORIGINAL-SOURCE STAGING: STATIC_REJECT. POSIX mkdir→open initial-directory adoption and parent/root relocation races; Windows handle-bound containment not implemented; external authenticated publisher entrypoint pin absent; Git tree/depth/node work not fully bounded; POSIX arbitrary output parents and crash directory durability incomplete.
2. READ-ONLY INTERRUPTED ADVISORY: NARROW STATIC_ACCEPT only for an expressly selected STABLE small ordinary disposable inventory, NOT concurrent-adversary ownership, not a rollback proof.
3. DESTRUCTIVE ROLLBACK: STATIC_REJECT; its unconditional refusal is intentional and remains REQUIRED.

R9 tests: 28 AUTHORED, NOT_RUN. R9 Windows gate, ZIP, signed interpreter and runtime wheels: NOT_RUN.

## 3. R10 GitHub-only integrated correction, explicitly SOURCE-ONLY

The user said 'proceed' after the above review. We created a **dedicated new** feature branch from exact R9 parent, created five content-addressed blobs, a tree, a single-parent commit, and published with **non-force expected-SHA** update. No Windows files or installed state were accessed.

R10 branch: `feature/personal-w4-r10-bounded-no-launch-source-20261106`
R10 HEAD: `2ee0c09050245ee03c630660ef08e38b4236b136`
CREATED R10 TREE: `2d8603a78fc8419d8f6780bc817964ac2f4d30d0`
SPECIFIED SOLE PARENT: `cdbf6824333bc257854dcc4cdcfbfc3cfaa7222d`
Remote R9→R10: ahead 1, behind 0, EXACTLY FIVE expected paths.
Remote W3 R2→R10: ahead 10, behind 0.
Main remains identical, no main merge.
All five Git SHA-1 blob IDs were independently recomputed from their GitHub content and all 5 post-publication GitHub file SHA readbacks matched:

- `src/vres_os/release_artifact.py`: `ba4fde661d1b6d748d9d7346249e171bf76fafb6`
- `src/vres_os/personal_w4_inert_git.py`: `db298b868b55a16f7973807d0f1e5c4dd82897a5`
- `src/vres_os/personal_w4_bound_output.py`: `1831b824a3be43b3c3bb503a3e759ae829865dc0`
- `src/vres_os/personal_w4_no_launch_release.py`: `0e488cc980670139c320ebf5027f8c11fda9ee02`
- `tests/test_personal_w4_no_launch_release.py`: `4a3f2e4d64bed6ddebdb7241e8ffdae53b602f65`

UNCHANGED R10 `src/vres_os/release_inputs.py`: `f6008f391305840645a707407fa8f464b0e27389`.
UNCHANGED R10 `pyproject.toml`: `b2d5e30d10d7be0613e90bf3ed1e346be5678969`.
Other original W3 owner hashes remain subject to their inherited pinned R9 OWNER_BLOBS; no modifications to those owners.

Integrated modifications:
- Original release_artifact `_tree_entries` adds optional per-tree entry budget and `_commit_files` adds a bounded W4 profile: 2048 visited trees, 8192 aggregate entries, 4 MiB total tree bytes, 32 levels, in addition to the existing 350 file / 15 MiB file bytes limits. Legacy owner mode with omitted bounds is unchanged and NOT W4-authorized.
- Loose-object reader's scope inventory now has 4096 scan-node and 32-depth ceilings and source/.git identity recheck, while W4 .git preliminary inventory has 8192 metadata node budget.
- POSIX-only BoundOutput requires a private same-effective-UID output parent without group/other write access, reopens the selected absolute parent through no-follow handles for identity checks, adds file-count/aggregate-byte/node/depth budgets, lazy fd-relative `scandir`, independent directory descriptions (never shared dup readdir offsets) and directory fsyncs. Failed roots and journals remain retained; same-UID hostile replacement, post-completion movement and Windows filesystem containment remain UNPROVEN.
- W4 source and output must share an explicit parent in the synthetic POSIX path. Advisory interruption marker has 64 KiB read cap, identity/size checks, canonical safe relative components, lazy bounded read-only scanner (4096 nodes/32 depth). No deletion.
- W4 bootstrap and OWNER_BLOBS changed to exact R10 sibling hashes, with explicit negative independent-entrypoint/window-containment flags and refusal in receipt.
- 28 prior test functions retained; one updated to account for scandir; 6 new R10 synthetic negative tests (shared parent, marker budget, inventory budget, POSIX writable parent, parent relocation, deep/large Git tree). TOTAL 34 AUTHOR-WRITTEN tests.

**Critical negative capability:** `_require_trusted_windows_stage()` remains an unconditional refusal on Windows before source access/output creation. The old `release_owner.stage()` is NOT invoked from W4; original legacy installer `stage()` remains unapproved. No Git subprocess in the W4 injected Git release path. Destructive rollback still always refuses. No signed external publisher authentication and no trusted F1/Fable positive authority.

## 4. Evidence and unfinished tests; do NOT upgrade to PASS

R10 source branch publication, exact five paths and commit ancestry through GitHub compare: PASS.
R10 FIVE independently re-computed Git blob SHA-1 values and FIVE remote post-publication readbacks: PASS.
R9 SQL migrations 001–041 independently SHA-256 validated: 41/41 PASS AT R9 on bytes left unchanged by R10, not an R10 integration execution.
R10 34 AUTHOR-WRITTEN tests: NOT_RUN.
R10 Python syntax/AST/compile: NOT_RUN (could not obtain a local raw code copy without disallowed/unavailable access).
R10 pytest: NOT_RUN.
R10 independent separate-agent static review: NOT_RUN / STATIC_ACCEPT NOT_GRANTED.
R10 actual original-owner full source Git checkout: NOT_RUN.
R10 real source ZIP, SHA256 and reproducibility: NOT_RUN.
R10 signed PSF Python 3.13.17 `-I -B` offline Windows gate: NOT_RUN.
R10 Windows source/test/output root creation: NOT_AUTHORIZED, NOT_RUN.
R10 safe Windows filesystem writer: NOT_IMPLEMENTED, Windows staging HARD REFUSED.
R10 3rd-party wheel closure/recovery: NOT_RUN.
R10 installed physical P2 identity: NOT_REVERIFIED.
R10 entrypoint independent external pin: NOT_ESTABLISHED.
R10 raw commit TREE/parent *header* independently fetched: NOT_VERIFIED; created tree/specified sole parent and remote ancestry/file readback are recorded separately.

Known residual risks to review: same-user POSIX mkdir/open adoption, parent relocation before/after checks, ancestry rewalk TOCTOU, source read-only path races, non-streaming os.walk per-directory enumeration under oversized hostile inputs, cross-platform fsync behavior, crash consistency, entrypoint authenticity, and whether 34 authored tests actually run against original code. Do not claim the R10 corrections eliminate these risks.

Preserve past evidence: W4 R1 six author-simulated PASS ONLY at R1; W4 R2 ten tests NOT_RUN, R3 twelve, R4 fourteen, R5 sixteen, R6 seventeen, R7 twenty, R8 twenty-one, R9 twenty-eight all NOT_RUN. W1 R2 operator-reported narrow Windows 18 PASS; W2 R2 operator-reported offline adapter PASS, genuine pytest/root symlink NOT_RUN; W3 R2 operator-reported original 13-blob offline Windows synthetic adapter PASS, real integration NOT_RUN. No evidence transferred to R10.

## 5. ABSOLUTE HOLDS and protected identity

- `LIVE_SCHEMA_048_INCIDENT=OPEN`: NO PostgreSQL even SELECT, direct or indirect.
- `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`: NO native Claude Code, installed hooks or hook-routed commands.
- Original P3 incident OPEN; independently trusted F1/Fable positive authority NOT_GRANTED.
- NO installed P2 changes, installer, Vres runtime, migration, Windows Sandbox R2, credentials, user-profile, PRISM, real legacy project, protected worktrees or product-main merge.
- NO Windows source/test/output root creation or Windows gate without NEW, separately explicit user authorization.
- NO cross-session automatic deletion of interrupted W4 stage.
- Protected installed P2 source identity `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c`; actual physical installed identity NOT_REVERIFIED.
- Chairman previously reported Sonnet/high; Opus/medium NOT_INSTALLED.
- Completed real task TASK-DAY-01, original note `C:\Projects\Vres-Personal-Notes\TASK-DAY-01.md` and desk `C:\Projects\Vres-Desk-Personal`; DO NOT reopen/modify/recreate/delete.
- No native Vres/Claude/DB/host hook test or Windows source/output directory was launched/created during R10 authoring.

## 6. NEXT SINGLE MILESTONE AND STOP CONDITIONS

**NEXT fresh-chat action: act as an independently distinct READ-ONLY senior Python, Git supply-chain, Windows/NT filesystem, release-recovery security reviewer of exact CURRENT R10.** FIRST fetch live canonical docs continuity index and THIS latest handoff, verify live docs/R10/main refs, exact ancestry, blobs, R9→R10 five-path diff, and raw trees/sole parents if a safe read-only connector genuinely supplies them (otherwise mark NOT_INDEPENDENTLY_VERIFIED). Read COMPLETELY the five changed R10 files, unchanged release_inputs/pyproject, all 34 authored tests, original owner and R9 history. Assess bounded tree and Git checkout traversal, proper no-subprocess callback, stable source/manifest/in-memory ZIP, POSIX writer initial root adoption, parent ancestry rechecks and races, POSIX fsync/crash semantics, Windows hard refusal, source entrypoint publisher-authentication trust, bounded advisory, and always-refused destructive rollback. Return THREE distinct verdicts: (1) operational staging, (2) stable read-only advisory, (3) destructive rollback. Report precise code line findings, severity, counterexamples and one integrated correction if required. Never auto-accept R10 because it is published.

Only AFTER defensible independent static clearance AND trustworthy handle-bound Windows filesystem containment is evidenced may the user separately approve ONE pinned original-owner source-only offline Windows gate. The eventual Windows gate must verify externally signed PSF Python 3.13.17 `-I -B`, exact source/ancestry, genuine owner 001–041 and manifest, actual ZIP SHA256/reproducibility, NO Git subprocess, negative interruptions, and protected state nonmutation. Do not bypass Windows hard refusal for a test. Later held: wheels/recovery, independent P3 disposition, F1/Fable authority, installed P2 consent, #169 Visual Studio real Windows UAT, #170 bounded personal daily-use pilot. Do not silently drop V-01..V-42/M0..M8.

Continuity procedure: at/before 20 assistant replies or conservatively approaching >50% context, stop feature development, checkpoint all authorized complete GitHub work, publish dated `docs/handoffs/` handoff and update `VRES-CHATGPT-CONTINUITY-INDEX.md` newest READ FIRST with non-force expected-SHA lease, verify remote blobs, give complete inline fresh-chat resume prompt with GitHub links and docs HEAD/tree, then END session. No exact context percentage available; no background handoff or unverified Windows claims.

The full integrated roadmap remains at `docs/roadmap/VRES-PERSONAL-COMPLETE-PENDING-DEVELOPMENT-RELEASE-AND-REAL-WINDOWS-UAT-PLAN-2026-11-05.md`; W0 integration audit at `docs/handoffs/VRES-2026-11-05-W0-EXACT-GITHUB-RELEASE-INTEGRATION-AUDIT.md`.
