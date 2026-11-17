# W4: owner's Git-fetch + original PowerShell update route — SOURCE ONLY / HELD

Date: 2026-11-17 (Europe/Athens). Owner selected **Git fetch followed by the original PS1 installer in UPDATE mode**, using the existing Windows installation; no second product, second installer, new Chairman, data store or backend.

## Implementation and boundaries

- Modify **root update.ps1** only for a new fail-closed *source-checkout preflight* and optional -PreflightOnly. It still delegates all actual installed-runtime changes to **original install.ps1 -Update** and its original versioned staging, snapshot and recovery implementation. The historical update owner was already present; this source change does not install or run it.
- Preflight requires an independently selected exact 40-hex source commit, one of four explicit GitHub origin URL spellings, repository-root invocation, matching checked-out HEAD and completely clean working tree, plus original installer and release-input paths. Git is used **locally** for metadata checks only. No automatic Git fetch, checkout, file writing, native Claude, PostgreSQL or installation on -PreflightOnly.
- This script is itself from the Git worktree and **is not a separately trusted launcher or external source verifier**. Origin text, matching HEAD, SHA-1 commit and clean status do not prove trusted publisher, interpreter, wheel identity, NTFS object identity or host integrity. Reading Git metadata cannot clear #185 or authorize any execution.
- The existing install.ps1 calls original release_inputs.py and release_artifact.py before the staged object identity and dependency closure have a trusted independent boundary; it can run pip and native Claude, and may touch installed P2 and the Claude user profile. **Do not run update.ps1 (including -PreflightOnly) while the source/interpreter execution and host/operational holds have not been cleared.**
- The original 248-file carrier is inert and omits rules, launcher and installer inputs. **Use a complete pinned Git checkout**, not the inert source ZIP. This source milestone does NOT build an installable first-FULL release or enable the HELD vres-day command.
- Dedicated original-user Windows installation remains **UNTOUCHED / UNKNOWN** from GitHub. No host Git command or PowerShell command ran, no real PostgreSQL even SELECT, no native Claude/hooks, no tests, no package resolution, no migrations and no installer activation.
- Preserve V-01..V-42; M0..M8; W0..W3; W4 R1..R13; C2B/K0 and the October 22/30/31 and November 5 integrated roadmaps. One original Chairman, task/session/result/history, data/credential/project/experience owners.

## Proposed operator procedure AFTER separate operational clearance (NOT RUN NOW)

The approved source commit must be supplied independently from a trusted release authorization, **never invented from a branch's latest HEAD**. In an existing **separate, clean Windows Git checkout** of the original GitHub repository with origin configured:

~~~powershell
# DO NOT EXECUTE WHILE CURRENT HOLDS ARE OPEN.
$ApprovedCommit = "<independently reviewed, exact 40-hex release commit>"
git fetch --no-tags origin <reviewed-release-branch>
git switch --detach $ApprovedCommit
.\update.ps1 -SourceCommit $ApprovedCommit -PreflightOnly
# Only after full separate release/Windows/host approval:
.\update.ps1 -SourceCommit $ApprovedCommit
~~~

If there is NO prior installed managed release, update mode must refuse; do not silently fall back to a fresh install or overwrite protected P2. Using git fetch/switch in a non-protected separate checkout must never discard local unpushed work. Actual independent pre-execution source/interpreter trust, OS-enforced no-network/no-child isolation for any source test, Windows/NTFS trust boundary, full dependencies and runtime acceptance remain prerequisite work. For now, all commands above are **PENDING / NOT_RUN**.

## Exact open blockers

- LIVE_SCHEMA_048_INCIDENT=OPEN: **no PostgreSQL including SELECT**, direct or indirect.
- HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: **no ordinary native Claude Code/hooks**.
- #185 OPEN: genuine distinct three-verdict independent review NOT_OBTAINED. Original P3, F1/Fable, WPR and R13 stage/release holds persist.
- No main/R13 merge, installed P2 overwrite, credential/user-profile touch, real legacy project/PRISM, global KEEP/DROP, original TASK-DAY-01 mutation, installer activation, migration, release stage() or destructive rollback.
- Authored static regression checks in tests/test_personal_w4_git_fetch_update_contract.py are **NOT_RUN**. New PowerShell preflight has **NOT_RUN** on Windows or other hosts. Earlier older-tree 732/732 cannot be transferred here.

Next: request independent #185 review of exact update wrapper and integrated existing-owner Windows source; resolve real defects, independently establish pre-execution trust and isolation, then receive explicit exact-scoped owner approval before physical Windows rollout, with the owner's git fetch / PS1 update preference retained.
