# Vres-OS — W4 R14 integrated authenticated immutable release / Windows containment decision

Date: 2026-11-06 (Europe/Athens). Classification: **DESIGN-ONLY, NO IMPLEMENTATION OR APPROVAL**.
Product: practical PERSONAL daily-operations application for ONE Windows user; exactly one existing Chairman and task/memory ownership. Not enterprise IAM, multitenancy, a second agent controller, or a new task store.

## 0. Decision, evidence and scope

**Architecture decision R14-D1: choose independent, pre-execution authentication of one immutable, no-launch SOURCE-ONLY release envelope over attempting to make the existing mutable POSIX writer authoritative.** A release is logically immutable only by binding its exact bytes to an independently trusted publication decision. Being a ZIP, SHA-1 Git object or 0700 directory does NOT make a local pathname physically immutable.

Phase A may verify and describe a signed candidate **without executing W4 Python, extracting, staging, installing, importing, resolving packages or launching Vres**. Phase B may produce deterministic in-memory source packaging after a separately authenticated initial launcher, under an explicit new offline authorization and independent review. Phase C, actual Windows publication/extraction/update, is a **separate held milestone** with independently reviewed Windows NT handle-bound implementation, evidence and specific operator consent. There is no accepted Phase B or C implementation today.

R13 remains an unmodified universal production refusal:
- W4 R13 product branch feature/personal-w4-r13-universal-staging-hold-20261106 HEAD bcf62460d68caebfdbd0e838d44c5997992c5fbc; raw TREE 9bbc5615fef4a8f785e9ddb0056e9430ffe25d63; sole R12 parent 0badcd34d1eafbce5f815512a489d70cb240eecd.
- The unmodified build_no_launch() refuses all operational staging BEFORE chosen source/output root access. The Python direct-file bootstrap CAN execute prior to this refusal; it must never be treated as the initial trust anchor.
- The original release_artifact.stage() and POSIX BoundOutput are independently callable legacy components; an R13-local guard does not make the entire repository nonwriting. Do not invoke them as operational bypasses. Destructive W4 rollback unconditionally refuses without reading a supplied root.
- R13 signed external publisher evidence, Windows NT containment, Windows gate, actual full-source ZIP digest and R13 pytest are NOT_ESTABLISHED / NOT_RUN.

This decision is an implementable contract, not evidence that signer keys, a launcher, a signed release, NT handles, an approval or an actual Windows artifact exist.

## 1. Explicit threat model and trust boundary

Assume an untrusted/mutable Git checkout or extracted ZIP, local same-user processes that may substitute paths, hostile reparse points/junctions/symlinks/hardlinks, case-normalization aliases, altered config and environment, partial writes/crashes, stale manifests, and arbitrary unverified W4 Python bytes. Assume a compromised executable may read the user's profile, credentials, call subprocesses/hooks, or contact PostgreSQL before a later self-check. A hold flag or error message inside that Python is **not** a sandbox.

The initial trust root must be **independent of every byte it authenticates**: outside the W4 repository, Git blob IDs, editable manifest, environment, CLI flags, consent string, self-authored journal and local staged directory. A signed Python interpreter proves Python's publisher only, not the W4 entrypoint's publisher.

One pragmatic PERSONAL design candidate (NOT installed, provisioned or authorized): an independently authenticated minimal native Windows verifier/launcher with a separately owner-approved trust policy that pins the expected publisher public-key fingerprint (or a separately verified Authenticode publisher/channel identity), minimum version/rollback policy, exact permitted release purpose and supported algorithms. The verifier itself must have an independently recorded, verified origin, e.g., a reviewed signed executable plus trusted external checksum/publisher observation. Never execute an unverified downloaded script to verify itself. No requirement for enterprise PKI or multi-user accounts; a personally controlled, independently provisioned publisher identity is acceptable **only after a real key-provisioning/revocation decision and independent review**.

**Blocking unresolved decision:** no independent signer/launcher/public key or credential-handling workflow has been established or authorized. Nobody may infer it from the user's "proceed," an in-repo key, an embedded hash, a GitHub URL or a test double. If no defensible independent key/channel exists, remain in read-only review mode, rather than silently downgrading trust.

## 2. One release-envelope contract, authenticated before Python

The publisher emits (a) one source-only immutable candidate byte stream, (b) one exact-byte manifest and (c) a detached authenticated signature over a domain-separated manifest byte stream. The trusted launcher/verifier, not W4 Python, must verify:

1. Its own independently approved binary/publisher identity, policy version and trust-anchor source. Refuse a trust anchor acquired from candidate data, user-controlled environment variables, current working directory, manifest-specified key download or command-line bypass.
2. A strong modern signature using a vetted implementation, explicit allowed algorithm(s), pinned signer key ID/fingerprint, signature context/domain separation, key expiration and revocation policy where applicable. SHA-256 alone proves digest equality; Git SHA-1 alone proves neither signature nor publisher. Verify exact MANIFEST BYTES, not a permissive parse-and-re-serialize interpretation.
3. Strict manifest schema version, byte-length ceiling, duplicate-key rejection, UTF-8/no-BOM/normalization rules, denied unknown fields, immutable product name and purpose, non-privileged no-launch capability assertions, replay/rollback/version/expiration rules, and an operator-approved source selection. "launch_authorized=false" in manifest is a declaration, NOT an OS sandbox.
4. Exact selected repository source commit/tree and accepted sole-parent ancestry to W3 R2, exact OWNER_BLOBS including the original release_artifact.py, release_inputs.py, no-spawn adapter, W3 source owners and pyproject, and a bounded, canonical per-path SHA-256 inventory of every release-scope file. A candidate cannot bring its own accepted root list.
5. Explicit 001–041 inert SQL migration pin SHA-256 matches; 042+ and experimental C2B/R0/F2 inputs excluded; no SQL is executed, parsed as code or used to connect to any database.
6. Actual candidate ZIP SHA-256, exact compressed/uncompressed sizes and file count, filename normalization and duplicate-name denial, recursion/compression-bomb limits, forbidden reparse/symlink/mode/ADS/device/case-alias members, no external URLs, no executable activation, and exact internal bytes/manifest readback. ZIP and source hashes must cover what subsequent consumers really read.
7. Dependency declaration evidence must accurately say UNRESOLVED: the existing pyproject.toml has version ranges, not a fully SHA-256-locked wheel closure. Do not imply an installable reproducible runtime until a separately accepted dependency closure and license check.
8. Revocation/expiry/unavailable-time policy must fail closed or produce an explicit independent review hold. Never silently accept a self-declared timestamp as proof of trusted time. Key rotation and signer compromise recovery require a separately recorded owner decision.

Illustrative MANIFEST FIELDS ONLY, not a real signed artifact: schema, purpose, repository, source_commit, source_tree, accepted_base, source_owner_git_blobs, release_file_inventory_sha256, release_files[{path,size,sha256,git_blob}], migrations_001_041_digest_set, source_zip_sha256, source_zip_size, dependency_status, publisher_key_id, signed_at, not_after, release_sequence, capability_holds. These fields and any canonicalization specification require independent implementation review; do not paste a fake signature or test key as authority.

## 3. Exact pre-execution sequence; fail closed at every edge

T0: operator separately authorizes only a named, non-sensitive, already available candidate and a narrowly scoped verification action after independent authority review. No default HOME/profile/real legacy/P2 enumeration. No external fetch, shell hook, Git subprocess, Vres CLI, installer or migration.
T1: independently authenticated, signed/trusted verifier opens bounded candidate and manifest as **data**. It checks signer/policy and integrity before calling or importing ANY W4/Python source. A verified PSF Python 3.13.17 -I -B process is required only if a later specifically approved source-only phase actually needs Python.
T2: verify exact-byte detached signature, manifest semantics, pinned source/ZIP and no-launch scope, then read the candidate using pinned handles; do not trust a later path re-open. Refuse missing/mutable/redirected roots or ambiguous file identity. Record provenance without secrets.
T3: OPTIONAL, only after a distinct clearance and permission, use a trusted already authenticated orchestrator to perform original-owner source-only memory verification (not legacy stage()), no Git subprocess, 001–041 inert digests and TWO deterministic ZIP calculations. Do not bypass R13 by monkeypatching production guards. Report real ZIP hashes only if actual bytes were generated and independently re-read.
T4: **STOP. No extracted executable, runtime wheel install, database, host hook, native Claude, application launch, P2 change, release promotion or deletion.** Those require later separate authorizations, a Windows NT publisher backend and the relevant P3 incident dispositions.
T5: any later consumption must independently re-check signed manifest, exact candidate bytes, signer validity/policy and opened-object identity at time of consumption. A past PASS against a now-closed mutable pathname does not bind future bytes.

In this model a signed source archive may become an authenticated *release candidate*. It is **not** a safe executable Windows release nor a completed UAT.

## 4. Windows NT filesystem containment for a later C phase

Portable Python Path.lstat(), os.open(), dir_fd and POSIX fsync are insufficient for a Windows NT security claim. A distinct reviewed Windows-native component must specify and demonstrate:

- Starting from an explicitly authorized Windows parent, use native handle-relative NT directory opens (e.g. NtCreateFile RootDirectory semantics under reviewed rules), not a string-prefix-only C:/Projects policy. Verify complete ancestor/volume identity, creation disposition, ACL/security descriptors, share modes, file IDs, unexpected hardlink counts, reparse tags, ADS and NT/DOS device/normalization aliases with actual NT behavior.
- Refuse UNC/device/ADS/drive-relative/path-prefix escapes and mountpoints, junctions, symlinks, reparse entries and colliding casefold/normalization names according to the actual filesystem and Win32/NT namespace. Do not assume CreateFileW with a concatenated path is handle-relative containment.
- Hold verified source/candidate directory handles until read/write/verify steps finish. Exclusive new-file/new-root creation must never adopt a preexisting pathname. Do not infer that mkdir→stat→open proves the newly created object under same-user concurrent replacement.
- A publication, if subsequently authorized, requires a reviewed same-volume handle-bound rename/exclusive-final-name protocol, identity/ACL/owner verification, no overwrite of unexpected neighbors, bounded file creation and readback, explicit failure preservation and documented FlushFileBuffers/NTFS durability expectations. Do not claim a generic flush proves power-failure recovery.
- Post-close/root replacement remains possible whenever another process retains necessary directory rights. Model this explicitly: hold controlled handles through use; verify-on-consumption; deny trust of old pathnames, journals or receipt files as ownership.
- Record interrupted roots but **do not delete them**. A separate future recovery owner/proof and explicit human consent would be required to permit any destructive rollback; R13's unconditional no-read rollback hold remains in force.

The preferred R14 approach minimizes or avoids filesystem publication in Phase A/B. A future C implementation must be independently security-reviewed, then tested on actual Windows NTFS with junction, hardlink, ACL, rename, case/ADS, unexpected neighbor, and interruption attacks. The available environment does not support claiming that this has happened.

## 5. Single integrated ORIGINAL-owner offline Windows gate — specification, not execution

This is one coherent gate for a *future* exact candidate, not a set of serial microtests and not an instruction to run anything now. Preconditions: externally authenticated verifier/launcher and signer decision, independently defensible NT root design, new explicit operator authorization with exact disposable roots/commands and signed PSF Python 3.13.17 evidence. Until all conditions hold, GATE=NOT_RUN.

The complete gate shall:
1. Reverify live docs/product R13 or approved successor/main refs, exact raw TREE/parents/diff and all W3 original owner blobs. Freeze exact bytes in an independent manifest before any Python entrypoint.
2. Use only authenticated original release owner and no-spawn Git adapter. Confirm strict source scope, no Git subprocess, anchored source identity, bounded inflate, original owner API compatibility and an exact 001–041 inert SQL digest check without database contact.
3. Produce the ACTUAL full original-owner source-only manifest and deterministic ZIP in authenticated memory, calculate ZIP SHA-256 twice, re-read every member by hash, and compare exact original-owner/source scope counts. No fake owner, fake signatures, synthetic ZIP or mocked production refusal counts as this positive gate.
4. Fail closed for altered/missing/stale publisher, wrong Git pin, unknown dependency/manifest field, out-of-scope code, 042+, poisoned/stale source, source/ZIP swap, redirect/junction/reparse/hardlink, NT name/ADS alias, case collision, oversized input, concurrent root movement, unexpected neighbor, interrupted journal and post-close candidate replacement.
5. Verify operational staging remains refused on ALL platforms in unchanged R13 until a separately reviewed new design supersedes it. Do not monkeypatch _require_trusted_windows_stage for an operational Windows assertion.
6. Explicitly prove non-contact/nonmutation boundaries and report actual PASS/FAIL/NOT_RUN with evidence provenance; no protected P2, real Windows user profile, credentials, legacy project, PostgreSQL, native Claude/hook route, Sandbox R2 or installed-state mutation.
7. Mark artifact trust only to the scope actually proven. A no-launch source-only gate does NOT grant runtime dependency closure, install, F1/Fable, G1 incident clearance, #169 Visual Studio UAT or #170 pilot acceptance.

The reviewer must prefer real integrated failure modes over another isolated mocked happy-path test collection. All positive claims require witnessed executed evidence, not authored test names.

## 6. Concrete implementation contract and non-goals

A future single R14-derived product feature branch may implement exactly ONE cohesive boundary composed of: (a) externally trusted verifier/launcher and out-of-band publisher policy; (b) sealed source-only envelope verifier with explicit strict manifest/schema and byte-budget; (c) binding to the unchanged original release-owner in-memory validation without executing unverified code; (d) one offline integration acceptance plan. It must NOT start with a bypass flag or replacement POSIX writer. If (a) cannot be implemented independently, stop; (b) alone is not a trusted release.

Do not invent an enterprise CA, HSM, second identity system or credential store for one Windows user. Do not silently create keys, install certificates, provision Windows binaries, set ACLs, create source/output roots, call third-party signing services or modify user settings without new specific authorization. The signer identity, trust anchor, revocation rule and launcher implementation remain PENDING decisions, not granted permissions.

Do not introduce a duplicate task database, a second Chairman, disconnected personal applications or alter inherited W3 owners merely to fit the packaging approach.

## 7. Nonnegotiable holds and original scope

- LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL even SELECT, direct or indirect.
- HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: NO ordinary native Claude Code, installed hooks or hook-routed operations.
- Original P3 incident OPEN, F1/Fable independent positive authority NOT_GRANTED.
- No real credentials/profile/PRISM/legacy projects/protected worktrees/installed P2/model switches; no installer, Vres runtime, migration, Windows Sandbox R2 launch, product-main merge, destructive root removal.
- No Windows source/test/output creation or execution without NEW explicit operator consent and independent preceding security clearance.
- Preserve old installed P2 historical source 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c (physical current state NOT_REVERIFIED), all three previously accepted side-by-side P1 copies and completed TASK-DAY-01 original note; do not reopen/delete/recomplete it.
- Preserve ALL original V-01..V-42 requirements, M0..M8, issues #163/#164/#165–170/#174/#176, W0 release audit, P1/W1/W2/W3 evidence, W4 R1–R13 and original rejected attempts, E7/F2/C2B/R0/K0, Stage1–6, P0/P1/P2/P3 proportional approvals and #169/#170 later real UAT.

## 8. Exit decision and one next milestone

**R14 design decision is READY FOR INDEPENDENT READ-ONLY SECURITY REVIEW, not STATIC_ACCEPT, code acceptance or gate approval.** Obtain independent review of this exact architecture against R13/R12 and the Windows NT attacker model; require an explicit viable external trust-anchor decision. Then, if defensible, implement ONE cohesive externally authenticated sealed-source verifier with its integrated negative scenarios on a dedicated exact-parent feature branch, without changing the R13 production staging refusal. No actual Windows gate until independent prior clearance and new owner authorization. If issuer or trusted initial launcher is unavailable, record BLOCKED instead of producing a fake positive gate.

No source/test branch changes or Windows execution occurred as part of this docs-only R14 design decision.
