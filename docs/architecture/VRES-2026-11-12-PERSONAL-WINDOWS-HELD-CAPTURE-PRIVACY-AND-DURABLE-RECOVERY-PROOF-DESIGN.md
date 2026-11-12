# Vres-OS — Personal Windows held-capture privacy and durable recovery proof design

**Date:** 2026-11-12 (Europe/Athens)
**Scope:** ORIGINAL #168 project-adoption owner, protected original #174 engineering governance and original #165 read-only Chairman view.
**Status:** DESIGN ONLY / NOT_IMPLEMENTED / NOT_TESTED / NO_RUNTIME_AUTHORIZATION.

## Decision and product fit

Vres-OS is ONE production-quality PERSONAL daily-operations application for ONE Windows user. The original #168 project_adoption.py remains the only project-adoption/capture/recovery state owner; the original #165 Chairman is the user-facing reviewer, never a second journal, independent credential vault, task store, or remediation executor. The original #163/#164 Credential Broker owns credentials; the original #167 Data Source Registry owns data-source metadata; #176 owns Experience Intelligence; #174 owns protected architecture evidence. Do not create enterprise IAM, multitenancy, additional Chairman instances, or disconnected recovery programs.

Current source deliberately returns FALSE for _held_capture_private_storage_available on Windows. POSIX owner-only mode and SHA-256 manifest readback do not prove secure Windows access control, encryption, authenticated state, atomic filesystem mutation or durability. The feature cannot be enabled by changing that Boolean, trusting a local JSON assertion, copying a successful Linux test, or treating this document as security evidence. Actual project writes remain HELD.

## Threat boundary and expected assumptions

Assume the trusted Windows kernel and official cryptographic APIs are functioning, but treat project folders, migrated Claude/PRISM configuration, hooks, external sources, saved journals, path strings, legacy consent claims, and any process-controlled attestation as untrusted. Any process running with the same Windows user token may be able to decrypt that user's DPAPI data: owner-private encryption protects at-rest disclosure and access from other principals but is NOT a defense against arbitrary same-user malware, an administrator, kernel compromise or all filesystem TOCTOU races. Those limits must be explicit in the acceptance report. Do not claim an independent Fable/high verdict from the process or files whose integrity it is evaluating.

The allowed current-user state must be distinct from the selected project tree, installed P2, native Claude profile, actual credential store and any database path. The state root must be explicitly bound to an approved current-user application-data location and the exact project key/identity. Do not follow caller-selected junctions or reparse points and do not infer the actual Windows installation from GitHub.

## Candidate implementation contract — NOT active

1. **Owner and root verification:** derive the current-user identity from a trusted Windows access token, never a caller-supplied user string. Before creating state, open and inspect each existing filesystem ancestor with Windows handle-based no-reparse constraints, stable file IDs and volume identity where supported. Confirm the final root is outside the selected project and not an alias of it. Revalidate every ancestor before/after each sensitive operation, but do not describe these checks as fully race-free without a proven handle-relative implementation.
2. **Access control:** create current-user application-data containers with protected DACL inheritance, narrowly scoped SYSTEM and exact user access, and explicit review of inherited Allow/deny ACEs, owner SID, integrity level, reparse/linked directories, ACL changes and unexpected principals. Verify access with actual security descriptor reads and negative access probes from a distinct disposable principal in an independently approved test environment. POSIX chmod is not Windows ACL evidence. A declarative DACL string in a journal is NOT proof.
3. **Encryption:** use Windows current-user DPAPI or a comparably independently reviewed OS-managed current-user encryption mechanism for bounded, nonsensitive but potentially private preimage payloads. Encrypt before persistent storage; no plaintext temp/preimage/journal copy may touch disk. Include an authenticated, versioned envelope binding project identity, capture ID, numbered target, content kind, preimage SHA-256 and selected plan digest; verify integrity and decrypt back to bounded bytes during closing inspection. A bare SHA-256 checksum is not authentication, and DPAPI is not a separate trusted Fable signature.
4. **Secret boundary:** retain current secret-looking path/content and binary refusals before encryption. Do not treat encrypted backup capability as permission to retain API keys, passwords, tokens, database contents or real legacy secrets. Credential Broker remains the single existing credential owner; no second secret store is introduced.
5. **Durable journal:** create an exclusive authenticated current-user PREPARING capture journal before any payload. Save only allowlisted identity/provenance metadata; typed human CAPTURE consent is distinct from later project-WRITE consent. Use explicit finite transition states (PREPARING, COPIES_SEALED_HELD, RECOVERY_REQUIRED) with versioned expected predecessor, exact plan digest, unique capture ID, bounded record size and idempotency rules. No transition may silently delete orphaned copies, retry a partially sealed capture or imply a prepared project write.
6. **Filesystem durability:** write ciphertext to exclusive create-new files on the same approved volume; flush file buffers; use properly reviewed Windows atomic rename/replacement primitives for the prepared envelope and seal; verify directory metadata/durability guarantees with actual Windows evidence. If required primitives or safety properties cannot be guaranteed, hold the state as RECOVERY_REQUIRED. Cross-volume rename, shadow-path, reparse, hardlink, interrupted create and partial write attacks must fail closed.
7. **Closing readback:** the ORIGINAL #168 inspector must independently reopen no-follow state, verify current Windows security descriptors, decrypt every required ciphertext, compare expected digest and length, re-observe original source/current target and ancestor/file-ID evidence, reparse journal+manifest+seal under strict bounded JSON semantics, and repeat a final coherent readback. Absence-only targets are parent-bound absence evidence, never claimed reread captured bytes.
8. **Manual recovery:** map unprepared, orphaned, invalid, incomplete, drifted and sealed-held states into redacted recovery classes consumed by the ORIGINAL #165 selected-plan session view. The CURRENT source closing-readback check is a cooperative diagnostic only; it has no Windows atomicity or authenticated-file-state proof. Every interrupted/uncertain condition routes to manual review, no auto cleanup/resume/replay, and no project write.
9. **Separate authority:** capture-specific human evidence is not remediation consent. An actual project write must have a fresh, independently attributable human operation approval for the exact project, target set, source/preimage/postimage and effect digest, plus independent protected F1/Fable/high where required. No in-process model string, user-chosen JSON assertion, screenshot or Github status can manufacture these gates.
10. **Inverse/postimage:** do not claim rollback rehearsed merely because an inverse blueprint is structurally valid. Validate exact postimage bytes, bounded no-follow current state, durable inverse preimage or bound absence, and verified filesystem rollback in a separately approved disposable environment before proposing any real operation. Actual project remediation remains prohibited.

## Required external proof gates before Windows capture activation

| Gate | Positive evidence required | Current result |
|---|---|---|
| WPR-01 | Exact signed/pinned Windows implementation identity and isolated reviewed source | NOT_PROVEN |
| WPR-02 | Trusted token-derived current-user boundary, ACL descriptor readbacks and negative distinct-principal access checks | NOT_PROVEN |
| WPR-03 | Actual DPAPI encrypt/decrypt/tamper/other-user refusal with no plaintext disk spill | NOT_PROVEN |
| WPR-04 | No-follow handle-based path confinement, file-ID and reparse/junction/hardlink race behavior | NOT_PROVEN |
| WPR-05 | Exclusive journal + encrypted copy + manifest/seal durable crash/restart matrix on Windows | NOT_PROVEN |
| WPR-06 | Read-only inspector authenticates exact saved bytes and absence-only semantics | NOT_PROVEN |
| WPR-07 | Separate trusted human project-write authorization and independent protected Fable/high | NOT_GRANTED |
| WPR-08 | Exact-pinned isolated complete-source transfer, transitive no-DB/no-host/no-native-Claude test-import safety, then actual synthetic test results | NOT_RUN |
| WPR-09 | Independently verified LIVE_SCHEMA_048 and HOST_HOOK_DB_ROUTE incident clearance, plus original P3/release holds as relevant | OPEN |
| WPR-10 | Owner's NEW explicit consent before any final Windows Claude Code disposable dummy UAT | NOT_GRANTED |

**Fail-closed acceptance:** no single application-controlled boolean, private directory permission, encrypted blob, test authoring count, local SHA, GitHub commit, docs approval or model narrative can satisfy the independent proof gate. All checks must cite exact artifacts and conditions, with PASS/FAIL/NOT_RUN provenance. Maintain current Windows capture denial until the full implementation and independent evidence exist.

## Integration milestones after this design

- Integrate proof-backed Windows storage in the existing original #168 state owner only, without importing native Claude/hook or contacting PostgreSQL.
- Complete a real durable interrupted-recovery state machine, authenticated forward/postimage and inverse filesystem verification in source, with explicit private/current-user boundaries and independently attributable consent.
- Preserve original #165 Chairman, #166 current-user global adoption, #167 Credential Broker-linked Data Source Registry, #176 experience/memory, #169/#170 verification and release, and complete V-01..V-42, M0..M8, W0..W3, W4 R1..R13.
- Do not run the final user-selected Windows Claude dummy UAT until substantive integrated development, independent incident/Fable clearances and NEW host permission. Never perform it after each small source milestone.

No Windows files, user profile, real project, installed P2, credentials, PostgreSQL, native Claude, hooks, installer, release or production main are accessed or authorized by this design.
