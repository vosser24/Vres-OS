# Security boundary and threat model

## Trusted

The local Windows user, the administrator who provisions PostgreSQL, the native Claude/Codex authentication
stores and explicitly installed Vres code are trusted. This preview is not a multi-tenant network service.
A model allowed arbitrary shell access as that user can potentially reach the same credential/database/files.
No prompt or MCP role name removes that OS-level power.

## Controls implemented

Dedicated DB role creation refuses pre-existing names; admin secret is not persisted. Runtime password writes
require Windows Credential Manager. Config remains non-secret. Searchable/event metadata receives best-effort
redaction. SDK credentials remain vendor-owned. Remote PostgreSQL TLS mode is explicit, not silently disabled.

MCP uses scoped object checks; evidence and subject-specific approvals are required for elevated mutations.
Protected review uses host-observed SubagentStop, actual model evidence, session binding, frozen state and
artifact hashes. Ordinary task edits cannot declare themselves passed. This is not cryptographic attestation.

Subprocess inputs avoid shell concatenation; parser/Codex output and duration are bounded. Installed Python
runs in isolated mode to avoid a project directory shadowing the Vres package. Project CWD restriction is not
an OS sandbox. Untrusted engineering should use an independently configured restrictive runtime/VM.

Document acquisition rejects common path/ZIP expansion hazards, ignores symlink/reparse paths and never executes
macro content. The Windows parser process does not yet have a hard job-object memory limit. Hostile documents
still belong in a disposable environment, not on a workstation containing sensitive company data.

## Release boundaries

Install/update/uninstall use expected owned paths/markers and staged runtimes. Same-user filesystem races,
reparse-point attacks, sudden power loss and Windows process semantics still require live adversarial tests.
A catch block is not proof of transactional Windows installation. Journals need operator review after an
abrupt interruption; database rollback requires separate backup/restore planning.

No source/DB/vault credential is included in release artifacts. A SHA-256 list is integrity evidence, not a
trusted signature. Dependency ranges and local package inventories are not a full SBOM/vulnerability audit.
See KNOWN-LIMITATIONS.md for the exact held functions and unverified dependencies.
