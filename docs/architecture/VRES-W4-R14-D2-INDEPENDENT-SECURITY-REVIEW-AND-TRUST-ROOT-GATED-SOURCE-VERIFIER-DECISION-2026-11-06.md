# Vres-OS — W4 R14-D2 independent static architecture review and trust-root-gated source-verifier decision

Date: 2026-11-06 (Europe/Athens).
Classification: **GITHUB READ-ONLY SOURCE REVIEW AND DESIGN/CORRECTION ONLY. NO SECURITY AUTHORITY, SIGNER, LAUNCHER, SOURCE EXECUTION OR WINDOWS GATE.**
Product: one personal Windows user, one existing Chairman, original task/memory ownership; NOT enterprise IAM, multitenancy, or a new task manager.

## 1. Verdict and exact decision

**ARCHITECTURE VERDICT:** R14-D1's independently authenticated source-only envelope is a defensible *direction*, but the proposed operational authentication path is **BLOCKED / NOT SECURITY-ACCEPTED**. No independent issuer, owner-provisioned publisher key, trustworthy initial executable, protected trust-anchor channel, replay/revocation state, or independently signed immutable candidate exists. The R14 design cannot supply its own missing authority. Do not conflate a signed manifest with an approved signer, or a Git SHA-1 identity with publisher authentication.

**R14-D2 ONE coherent next milestone:** specify and, only after a separately authorized/independently reviewed initial external authority, implement a narrowly scoped **trust-root-gated, read-only authenticated SOURCE-ONLY envelope verifier**. Its only initial positive result is `AUTHENTICATED_SOURCE_CANDIDATE_DATA_ONLY`; it cannot authorize staging, extraction, Python, install, launch, database, native Claude/hooks, F1/Fable, installed P2, or source promotion. Until the external issuer and trusted verifier are established, this milestone is **DESIGN_READY / IMPLEMENTATION_BLOCKED / OPERATIONAL_RELEASE_BLOCKED**. No implementation feature branch is authorized by a generic "proceed" alone.

R13 operational `build_no_launch()` source-path refusal: **NARROW STATIC_ACCEPT as refusal only**; R13 original-source staging: **STATIC_REJECT**; R13 stable explicit interruption advisory: **NARROW STATIC_ACCEPT advisory only**; destructive rollback: **STATIC_REJECT**. All actual R13 pytest, original-owner full ZIP, Windows gate, trusted verifier and runtime wheel closure: **NOT_RUN**. This is independent security reasoning applied to GitHub sources, not a separately instantiated second agent's witnessed signoff.

## 2. Evidence and limits of live GitHub readback

Repository: https://github.com/vosser24/Vres-OS
- Canonical docs branch `docs/chatgpt-continuity-20261023`, observed head `21fd2e2df9321d7cb1a97aedf616ed1dcefdb085`. Its prior checkpoint recorded tree `e7706945cc98e773b3aa2250f85f10de663e8255` and sole parent `a0059d92510a290ef0b6059ea0c67341806f0059`. This review's GitHub connector **did not expose raw commit tree/parent headers**, so prior raw-header claims are HISTORICAL / NOT_INDEPENDENTLY_RAW_REVERIFIED here. Live comparison against the branch confirmed **IDENTICAL 0 ahead / 0 behind**, and the exact R14 architecture, handoff and index blobs were read.
- R13 branch `feature/personal-w4-r13-universal-staging-hold-20261106`, live `bcf62460d68caebfdbd0e838d44c5997992c5fbc`, recorded tree `9bbc5615fef4a8f785e9ddb0056e9430ffe25d63`, recorded sole R12 parent `0badcd34d1eafbce5f815512a489d70cb240eecd`. Live branch compare was IDENTICAL; R12→R13 compare ONE ahead, ZERO behind, exact two modified paths.
- Product main live `9a8acc5d464b96432a93cb95daa9581412fb07ee`, compare IDENTICAL, NO MAIN MERGE.
- Accepted W3 R2: `982e77f2f4974b4fbca5da91d3e11aeb56e40271`; accepted ancestry via W3 R2→R13 live compare, 13 ahead, zero behind.
- R13 source `src/vres_os/personal_w4_no_launch_release.py` Git blob `c206e84a4ab5dee1ebcf5f83b4c768fb7468adc6`; R13 test `tests/test_personal_w4_no_launch_release.py` blob `79b3757cab6ea788f5660f5451126bd15ec81930`. R14 architecture blob `e7612241cb025c1b51c079661720a0f1c6967718`; old index blob `b85d77f0414080311f5de539266cf82206f732d4`.
- Retained owner APIs: `release_artifact.py` `1719f839d75b4dd994125c5f6d1ede2d4b7100b2`; `release_inputs.py` `f6008f391305840645a707407fa8f464b0e27389`; POSIX `personal_w4_bound_output.py` `972c7c8276025c0cc2d68bd1be2d7173a29cb439`; no-spawn `personal_w4_inert_git.py` `af7bcb17f4b09eb262589021b9f6444de2c56fe1`; `pyproject.toml` `b2d5e30d10d7be0613e90bf3ed1e346be5678969`. No dependency-wheel closure.
- R13 source direct-file bootstrap executes Python before the unconditional guard. `_require_trusted_windows_stage()` always raises, and `build_no_launch()` calls it before user-chosen source/output path access. `rollback_interrupted()` always raises without reading a root. The separately callable original `release_artifact.stage()` remains a writing API, with legacy default `shutil.rmtree` on staging failure. POSIX `BoundOutput` is also separately callable, hard-refuses Windows and is not NT-safe staging.
- R13 has **47 authored test functions, 0 new witnessed R13 pytest PASS**. The positive synthetic author harness monkeypatches production stage refusal; it is not an operational release gate.

## 3. P0 publisher bootstrap: external to everything authenticated

A positive trust path requires a separately approved provenance of one *initial* trusted verifier executable and every native dependency it loads; one owner-approved publisher identity and independently protected, versioned trust policy; and an actual private-key custody/rotation/revocation procedure. The signing key must not be generated, stored, downloaded, or trusted as a side effect of the candidate manifest, Git repo, W4 Python, user-controlled environment, a command-line bypass, an in-repo public key or a journal.

For one user, a personally owned publisher key and a narrow independently reviewed native Windows verifier may be proportional. No enterprise IAM, CA service, HSM, second Chairman or second memory store is implied. Windows Authenticode can contribute to the initial verifier's independently verified origin, but generic signature validity is not a Vres-OS publisher authorization: the *specific allowed* binary/publisher and policy must be independently pinned. A valid PSF Python signature proves Python origin, not W4 source origin.

**Boundary limitation:** a same-user malicious process able to replace BOTH the verifier executable and its policy may defeat local self-verification. Define an independently protected or out-of-band bootstrap and review its scope. A hash on disk beside its own untrusted binary is not a root of trust. Do not assert protection against a fully compromised administrator/kernel.

**Actual current state:** initial verifier binary NOT_CREATED, independently verified hash NOT_ESTABLISHED, approved public-key fingerprint NOT_GRANTED, private-key provision NOT_RUN, trusted policy NOT_CREATED, signed envelope NOT_CREATED, user approval for key/Windows/protected-profile changes NOT_GRANTED.

## 4. Seal the exact bytes; resolve signed-envelope production order

Require the publisher to first create and finish the complete source-only ZIP as inert data, independently read its exact bytes and produce an immutable exact-byte manifest. **Only then** sign the exact final manifest. Phase A receives that fully formed ZIP + manifest + detached signature as data. The manifest is EXTERNAL to the ZIP; the signed manifest must not be a ZIP member whose own digest it is supposed to sign, because that creates a self-hash circular dependency.

Phase B is optional and held. After an independent authenticated bootstrap AND distinct owner consent, trusted orchestration can invoke reviewed original-owner in-memory verification/regeneration on exactly pinned source bytes and compare the regenerated ZIP SHA-256 to the signed ZIP hash. The initial publisher/source-building procedure, including what code may run before signing, is separate and **PENDING**; the R13 all-platform refusal may not be monkeypatched to create an operational artifact. Without a legitimate independently authenticated producer, there is no authentic candidate to verify.

Proposed strict envelope contract (SPECIFICATION ONLY, no key/signature):
- Fixed and documented schema and purpose `VRES-OS/W4/SOURCE-ONLY/1`; exact product/one-user intended release channel; strict limits on manifest, ZIP, file count, total content and per-file sizes.
- A single owner-approved, externally pinned cryptographic algorithm and verifier implementation, with no manifest-controlled algorithm switch or fallback. Select and independently review the actual algorithm/implementation **before coding**; no fake Ed25519/ECDSA keys or self-reported Authenticode authority.
- Signature input is a domain-separated *byte sequence*, e.g. ASCII domain `VRES-OS/W4/SOURCE-ONLY/1\0` concatenated with fixed-endian unsigned 64-bit manifest byte length and **exact manifest bytes**. Pin the domain, framing, signature representation and library behavior in a future independent contract; never sign parse-and-reserialized JSON.
- Strict UTF-8 without BOM, no trailing content, duplicate-key rejection, exact field allowlist, canonical serialization specification, no floats or implicit type conversion, ASCII-safe path grammar, normalized ZIP member names and collision checks. Reject unknown schemas, unexpected keys/fields, duplicate ZIP members, ADS/devices/UNC and path aliases. Never use manifest-specified URLs or fetch signer keys from the release.
- Exact ZIP byte length + SHA-256; exact source commit/tree and signed SHA-256 per-file inventory; independently pinned accepted W3 base/owner blobs/allowlist; exact internal `SOURCE-MANIFEST.json` SHA-256 and content mapping; 001–041 inert SQL digest set, no 042+; no activation. Git SHA-1 identities are supplemental content/ancestry references, NOT publisher authentication. A signed detached digest must bind what the next consumer actually reads, not a stale pathname.
- Dependency evidence states `runtime_dependency_closure_accepted=false` and wheel-lock `NOT_RUN`. A `launch_authorized=false` field is a policy declaration only and does not sandbox untrusted code.

## 5. Replay, expiry, trusted time and key recovery

No acceptance based only on candidate-provided `signed_at`, `not_after` or `release_sequence`. Offline verification must either (A) compare the candidate with one exact release digest/sequence already approved through an independent, protected channel, or (B) use a separately accepted monotonic policy/time source and recorded revocation state. If neither exists, refuse and report `TRUST_POLICY_NOT_ESTABLISHED`. Signature validity alone cannot exclude a previously legitimate but revoked or rolled-back release. An unavailable trustworthy clock/revocation source is a review hold, not silent acceptance.

A replacement publisher key, signer compromise, expired key, lost verifier, lost minimum-sequence state or policy rollback requires independently documented human recovery authorization. A candidate may never update its own trust anchors or erase revocation history. Do not invent offline freshness assurance from JSON fields.

## 6. Pre-execution and Windows-consumption boundaries

T0: independently identify a previously authorized, non-sensitive verification candidate and one independent verifier/policy. No automatic HOME/user profile/legacy/P2 scanning, network fetch, Git subprocess, shell, native Claude, hooks, PostgreSQL or Vres CLI.
T1: a separately authenticated trusted launcher opens bounded candidate/manifest/signature as data. Before ANY W4 Python import/exec, verify the allowed publisher and exact-byte signature/semantics. Abort without extraction or output if uncertain.
T2: hold opened object identities during validation, reject symlink/reparse/hardlink/ADS/name aliases and unexpected file/volume identities under actual Windows NT behavior; compute SHA-256 from the consumed bytes. Reopen through a mutable path is NOT the same verified candidate.
T3: Phase A STOP, returning only an authenticated inert-source data verdict with exact signer/policy/digest evidence. Retain immutable evidence WITHOUT claiming immutable future pathname. No file publication.
T4: any later phase must independently reauthenticate signer/policy and candidate bytes at actual consumption time. Post-close replacement cannot be negated by a past PASS.

**Phase C is NOT in R14-D2.** A later Windows NT-native, handle-bound publication design must separately prove identity, ACL/ownership, reparse/junction/hardlink/rename/ADS/case/UNC controls, exclusive final name, failure evidence, actual NTFS crash/recovery semantics and post-close verification. Neither POSIX `BoundOutput` nor `release_artifact.stage()` may serve as a Windows bypass. No destructive rollback is allowed.

## 7. ONE integrated future original-owner offline acceptance gate

This is an acceptance *plan*, not permission or evidence of execution. Preconditions: independently trusted verifier/issuer/algorithm/revocation policy, independent preflight security clearance, and NEW exact operator authorization covering disposable Windows roots and commands. Prior to that: GATE=NOT_RUN.

The same integrated gate must witness: trusted-verifier origin; signed exact bytes; correct source/manifest/ZIP SHA-256 and genuine original owner/regeneration; original W3 source owner identities; inert 001–041 digest checks; no 042+; bounded file parsing, negative modified signer/policy and key cases, stale/rollback candidates, malformed canonical JSON/ZIP, case/ADS/reparse/hardlink/rename swaps, memory/time budget failures, interruptions and post-close substitution; unchanged R13 operational refusal on every platform and unchanged installed P2. Report explicit PASS/FAIL/NOT_RUN per observed experiment. Fake owners, fake signatures, monkeypatched refusal or authored unexecuted tests count as **NOT_RUN** for operational acceptance.

Do not bootstrap the trusted verifier by executing the untrusted candidate; do not install Python packages from the candidate; do not launch Vres, contact PostgreSQL or exercise native Claude/hook routes. Future POSIX staging is also not authorized.

## 8. Absolute holds, continuity and precise next decision

LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL even SELECT, directly or indirectly. HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: NO ordinary native Claude Code or installed hooks. Original P3 OPEN; F1/Fable independent positive authority NOT_GRANTED. Do not touch real credentials, user profile, PRISM, protected worktrees, legacy project, installed P2, completed TASK-DAY-01, Windows Sandbox R2, native installer, migrations or product main. No Windows source/test/output root creation or execution without NEW operator consent and prior independent security clearance. Installed P2 historical source `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c`; physical present identity NOT_REVERIFIED; Sonnet/high historical, Opus/medium NOT_INSTALLED.

Preserve all V-01..V-42, M0..M8, #163/#164/#165–170/#174/#176, original P1/W1/W2/W3 narrow Windows evidence, W0 original-owner release audit, all R1–R13 rejects, original rejected A12/A13/A16/A19 attempts, E7/F2/F1/C2B/R0/K0/Stage1–6, approvals P0/P1/P2/P3 and later #169 Visual Studio real Windows UAT and #170 bounded daily-use pilot. All detailed history is linked in the canonical continuity index and the prior R13-review/R14-design handoff.

**NEXT EXACT OPERATION:** Independent owner/publisher provisioning decision for a *specific externally verifiable* verifier origin and signer/trust-policy lifecycle, as a separate consent and independent security review. Until available, implement NO operational verifier or positive-trust artifact; do not make a dedicated implementation feature branch or weakened R13 guard. If this is not possible, remain BLOCKED. No work has been performed on the Windows host in this review.
