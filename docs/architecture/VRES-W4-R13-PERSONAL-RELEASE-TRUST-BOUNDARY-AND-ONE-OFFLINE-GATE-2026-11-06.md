# Vres-OS — W4 R13: coherent trust-boundary and single Windows release-gate design

Date: 2026-11-06 (Europe/Athens). Status: DESIGN CONTRACT ONLY. No security approval, real Windows gate, production release, installation or filesystem execution.

## 1. Binding product and decision

Vres-OS remains a practical PERSONAL daily-operations application for ONE Windows user. It is neither enterprise IAM/multitenancy nor a second Chairman/task database. Preserve the complete V-01..V-42 requirement trace, M0..M8 delivery roadmap, W0–W3 narrow acceptances, W4 R1–R12 source review/rejection records, and issues #163/#164/#165–170/#174/#176.

R12 operational original-source staging: STATIC_REJECT.
R12 stable, deliberately selected read-only interrupted-stage inventory: NARROW STATIC_ACCEPT (advisory only).
R12 destructive rollback: STATIC_REJECT (unconditional no-read refusal required).
R13 prevents operational staging even on POSIX, not only Windows, until ALL remaining independent authority and publication conditions have evidence. This change is a negative capability, not an accepted release.

## 2. The trust root MUST live outside the code being authenticated

1. A distinct trusted publisher/channel must authenticate an exact release-source commit and the initial Python entrypoint byte identity BEFORE executing any untrusted W4 Python file. A SHA-1 Git object ID establishes content identity, not publisher authority. Self-embedded expected hashes and matching sibling blobs are insufficient.
2. Establish exactly who signs/trusts the initial evidence, how that trust anchor is provisioned independently, how signer/certificate/key revocation and expiry are checked, and how authorization is passed to a narrowly scoped launcher. No bypass by a user-supplied boolean, platform name, environmental toggle, approval phrase, or journal claim.
3. The independently verified, signed PSF Python 3.13.17 interpreter and isolated -I -B command are separate requirements; an authentic Python interpreter is not evidence that W4 source is published by an independently trusted Vres signer.
4. The launcher must independently verify exact W4 source/test/dependency blobs, expected ancestry, source-input pins, authorizations and negative holds BEFORE loading or executing W4 code. Static GitHub remote readback alone cannot establish trusted Windows installation identity or physical source state.
5. Until the above is independently evidenced and reviewed, the R13 operational staging guard is universal and mandatory. No production override, no ordinary native Claude, no PostgreSQL, no installed hooks.

## 3. NT handle-anchored filesystem and safe candidate-publish requirements

No Windows implementation exists or is authorized by this document. A future independently reviewed implementation must at least:

- Start with an operator-approved, new disposable root under the exact authorized Windows parent; verify every ancestor, volume and directory identity against link, junction, mount-point, device, alternate stream, and reparse redirection according to Windows NT semantics. Do not treat POSIX dir_fd checks as equivalent.
- Retain trusted directory handles for all source read, exclusive destination creation, file write, enumeration and rename operations. Each child must be opened relative to the verified parent identity with non-follow/reparse controls, and any reparse or hardlink ambiguity must fail closed.
- Deny reserved DOS filenames, case/normalization aliases, traversal, path-length ambiguity, name collisions, unwanted alternate data streams, unexpected files and unsafe ACL inheritance. Bound every read, decompression, tree walk, archive field and output write before untrusted materialization.
- Create a newly exclusive private candidate without adopting an existing pathname or deleting an unknown interrupted root. Assert that resulting handles refer to the created objects, not merely to an inode/file ID observed later from a substituted pathname.
- Provide a reviewed same-volume, handle-relative, crash-consistent publication protocol with verified temporary and final identity, explicit flush/durability semantics and recovery behavior. Never claim POSIX fsync is a Windows crash-consistency proof.
- Revalidate a publisher-authenticated manifest, ZIP SHA-256 and released files at EVERY later consumption of the candidate. A same-UID actor with rights to the directory may still move or replace a path after handles close; no mutable path alone proves continuing ownership or immutability.
- Preserve interrupted stages for inspection. Destructive rollback remains disabled even if a journal or human supplies the old approval string. Recovery design requires its own separately reviewed authority and explicit human consent.

Do not reduce the required model to a simulated writer that only tests the happy path. Do not bypass R13 fail-closed guards to make a purported Windows production test pass.

## 4. One meaningful future source-only offline integration gate, not endless microtests

First require independently defensible source/static clearance, publisher authentication and NT containment design, with operator consent for the exact disposable source/test/output root creation and invocation. Only then:

1. Read and reverify the LIVE canonical continuity docs/index, exact R13 product branch HEAD/TREE/sole parent and unchanged W3 owner modules. Pin all bytes and branch/source provenance.
2. Independently validate signed PSF Python 3.13.17, launcher trust material and -I -B direct isolation before any W4 source execution. Never run ordinary native Claude, host hooks, Vres main CLI, installer or database commands.
3. Use exact original release-owner source and no-spawn Git reader. Verify 001–041 inert migration bytes and source-only policy in memory; prohibit 042+, experimental files, real credentials/profile, P2, PRISM, legacy user projects and protected worktrees.
4. Verify an ACTUAL deterministic original-source manifest and ZIP byte SHA-256 twice on full pinned source with explicit independent readback, not a synthetic owner substitute. Ensure no Git subprocess, no runtime wheel installation and no activation.
5. Exercise selected root refusal, stale/missing/redirected input, symlink/junction/reparse, hardlink, case aliases, oversized trees/blobs, interrupted journal, unexpected neighbor, post-close root replacement and negative rollback outcomes, under nonmutation checks.
6. Record provenance for every assertion: PASS, FAIL or NOT_RUN; require explicit operator authorization for any Windows creation/execution. Never transfer prior W1–W3 narrow Windows passes or R9 41/41 digest evidence into a new R13 execution claim.

The currently unapproved gate remains NOT_RUN. A new independent reviewer must first determine whether a trusted external-launcher plan and Windows NT backend can actually meet the above threat model, or whether the correct product design is an immutable signed artifact with verification-on-consumption and reduced filesystem privilege assumptions. No release promotion without explicit decision.

## 5. Remain held

LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL even SELECT or any indirect access.
HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: NO ordinary native Claude, installed hooks or hook-routed commands.
Original P3 incident OPEN; independent F1/Fable positive authority NOT_GRANTED.
NO installed P2 modification, real credentials, real user profile, real legacy project, protected worktree, runtime installer, migration execution, Windows Sandbox R2 launch, main merge, #169 real Visual Studio UAT or #170 real daily-use pilot.

W4 R13 source GitHub publication and tests authored do not change these holds.

## 6. Next decision

Obtain an INDEPENDENT READ-ONLY review of exact R13 universal refusal and original R12 trust failures; then develop and validate ONE coherent publisher-authenticated + NT-bound source-only release design, not disconnected negative microtests. If the essential external publisher trust cannot be established, stop at safe source review and do not claim a released Windows artifact.
