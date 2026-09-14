# Known limitations and release boundaries

Applies to the 0.2.0a1 controlled-live-test preview. Read this before installation.
This is not a production release or a claim that the complete Vres vision is implemented.
A green local release gate does not change the boundaries below.

## Explicitly held functionality

| Capability | Actual preview behavior | What is required before enabling the larger promise |
|---|---|---|
| Automatic procedural optimization | Records candidate experiments and applies a conservative mathematical gate, but will not auto-promote from agent-supplied measurements. Explicit, subject-bound user decisions remain possible. | Host-measured, comparable paired replay; accepted-output equivalence; full runtime/token accounting; reliability/security constraints; rollback. |
| Learned automatic model replacement | Recommendations use registered policies. Recorded telemetry is advisory. | Independently measured comparable runs and a policy-promotion authority. |
| Company-wide publication | MCP rejects `company_wide=True`; new content is project-local. | A dedicated authorization event covering the exact content and global scope. |
| Arbitrary transparent session replacement | Hooks checkpoint and restore material state around native sessions/compaction. There is no custom terminal host that replaces every Claude context invisibly. | Actual host lifecycle implementation and end-to-end tests. |
| Infinite nested executive hierarchy | Chairman coordinates ordinary subagents; directors return staffing requests rather than recursively spawning unsupported workers. | Supported nested runtime or a separately tested external coordinator. |
| Chaotic company-disk project reconstruction | Mechanical folder ingestion assigns a nominated project. It does not autonomously infer an entire trustworthy company taxonomy. | Project-discovery evaluation and review of ambiguous assignments. |
| Annual unattended market research | Domain due dates and explicit refresh records exist. No annual background scheduler is installed. | A separately authorized scheduler and actual research/validation execution. |
| Shared capability catalog writes | Public MCP registration is held; installed seed definitions and task-backed proof/read operations remain. | Explicit reviewed catalog authority; no global persona publication merely because an agent names itself an expert. |
| Automatic best-expert hiring | Roles/skills/capability records aid routing; no benchmark establishes that a generated persona is the world's best expert. | Domain-specific competence evaluations and documented evidence retrieval. |
| Automatic company DB reporting | Vres manages its own memory database. It does not automatically discover or authorize arbitrary reporting databases. | Explicit read-only data-source integration and query validation. |
| Generic recipe execution | Accepted contracts and implementation references can be retrieved. A universal safe executable-recipe sandbox is not present. | Registered deterministic executors with verified input/output and permissions contracts. |

## Unexecuted target dependencies

This audit environment did not run Windows/PowerShell, PostgreSQL/psycopg, Windows Credential Manager,
Claude Code, the real MCP SDK transport, Codex, or a downloaded SentenceTransformer. Mock/scripted
boundary tests are not substitutes for those runtimes. See LIVE-VERIFICATION.md for the required tests.

The wheel was built with the recorded local build backend and its package contents checked. Runtime
dependencies remain bounded version ranges, not a tested Windows lockfile. The installer records
`resolved-dependencies.txt` and runs `pip check`, but a resolved environment is not a reproducibility guarantee.
Optional embedding dependencies are large and are deliberately not installed by default.

## Security and authority

The local Windows user is a trusted operator. Claude tools, scripts and the memory runtime operate in
that user's security context. The design is not a multi-tenant server, a cryptographic validator identity
system, or protection against a local agent/operator allowed arbitrary shell access to the same files/database.

The validation hook checks a native subagent event, model-family evidence, registered session, frozen
state, reviewed artifact hashes and a structured report. It does not prove every criterion was actually
exercised or that the same OS user could not forge inputs. High effort is configured rather than attested.

Approval recording points to a real persisted user turn and a specific action/subject. Recognizing natural
acceptance is intentionally conservative. This does not provide a cryptographic binding between arbitrary
chat language and every field of a business contract. Conditional/ambiguous assent must not be broadened.

Redaction covers common credential patterns, not all possible secrets. Never place real credentials in
chat, source documents, transcripts, test fixtures or Git. PostgreSQL administrators and local users with
filesystem/vault privileges remain able to access data. Vres does not encrypt all database contents itself.
Use infrastructure encryption, access controls and backups appropriate to the deployment.

Project filtering is an application boundary, not PostgreSQL row-level multi-tenant isolation. Knowing a
DB password or having arbitrary local shell access can bypass it. Do not expose this MCP server to strangers.

## Installation, upgrade and recovery

The installer stages versioned virtual environments at their permanent location, verifies imports/plugin
structure, and switches a runtime pointer only after its staging checks. Caught failures attempt to restore
old plugin/runtime/launcher state. None of that has yet run under PowerShell here.

A power loss at the publication boundary leaves a journal for manual recovery. Do not delete the journal
blindly. This preview is not a guaranteed unattended, crash-repairing installer for a novice.
Binary rollback is not database rollback. Back up PostgreSQL and artifact/source files before upgrades.
Older executables must not be forced against an unknown newer schema.

Automatic database provisioning refuses existing role/database names. If interrupted after creating a new
role, an orphan may remain; use new unused names or have an administrator inspect it. Vres must not reset
or delete someone else's role to make a retry convenient. Administrator credentials are discarded rather
than stored; only the dedicated runtime credential goes into the Windows vault.

The primary tested setup target must be a disposable VM and a dedicated database. Do not point the preview
at the user's existing Nexus/Praktiker/ERP production database. Native platform sandboxing and prompt
permissions are separately configured vendor capabilities, not guarantees supplied by Vres.

## Memory, artifacts and concurrency

Only persisted material state survives. Unsaved reasoning, a user instruction lost before a successful
write, or files never included in a review cannot be reconstructed reliably. Session-end hooks are best
effort; do not rely on their short native timeout to save a whole conversation.

SQL locks, checksums, uniqueness and leases have scripted boundary tests, but real lock contention,
serialization behavior and interrupted transactions still require PostgreSQL tests. No database-wide
backup/restore operation is automated by this preview.

Source paths often reference the original files; ingestion is not an archival backup. Moved/deleted raw
sources can make evidence unavailable. Back up source/artifact storage with the DB. Hashes detect changes;
they do not preserve deleted bytes.

## Ingestion and retrieval

Office/PDF extraction is bounded and isolated in a child process. POSIX resource limits do not constitute
a Windows RAM sandbox; timeout/output/ZIP preflight alone cannot eliminate all parser exhaustion risks.
Use a disposable VM for hostile files. OCR is not automatic. Encrypted/scanned/no-text PDFs go to review.
Legacy `.xls`, unsupported encodings and specialized formats can require conversion.

XLSX formulas use stored cached values; Vres does not recalculate Excel, follow external links, run macros
or interpret drawings. PDF layout, slide diagrams and images may carry meaning not present in extracted text.
Truncation is bounded and must remain visible; a partial extraction is not a whole-document proof.

Cross-run hashing deduplicates source records, but unchanged files can still be reparsed on a new onboarding
run. This is not a fully cached incremental document-processing engine. Files can change during acquisition;
they are flagged rather than silently certified as stable.

Optional vector search requires real model/download/runtime verification. JSON-vector fallback scans a
bounded candidate set, so recall is limited and must not be described as exhaustive. Greek/Greeklish quality
has no real company benchmark yet. Similarity, numeric confidence and repeated model agreement are not
probabilities of truth. Knowledge freshness requires real re-verification, not just resetting a date.

## Licensing and supply chain

Vres source is MIT. Third-party packages/models have their own licenses; the PDF dependency is now pypdf,
not PyMuPDF. This is not a legal clearance of the entire transitive dependency graph. No complete vulnerability
scan, signed installer, Windows code-signing certificate or tested offline dependency mirror is included.
Local SHA-256 manifests prove file consistency relative to the supplied manifest, not publisher authenticity.
