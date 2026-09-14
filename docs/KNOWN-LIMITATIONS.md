# Known limitations and release boundaries

Applies to the 0.2.0a1 controlled-live-test preview. Read this before installation.
This is not a production release or a claim that the complete Vres vision is implemented.
A green local release gate does not change the boundaries below.

## Explicitly held functionality

| Capability | Actual preview behavior | What is required before enabling the larger promise |
|---|---|---|
| General automatic procedural optimization | Caller-reported telemetry remains non-promoting. Project-scoped procedures using the code-owned `vres:builtin:json-recipe:v1` executor can create a protected-contract-identical candidate, generate runtime-owned paired measurements on the same input, bind them to protected replay validation, and auto-promote only after output-equivalence/no-regression attestation and Pareto superiority. Company-wide procedures using that same executor can enter the same measured replay path only through explicit authority: exact candidate creation requires one `company_procedure_optimize` approval, and final attested promotion requires a fresh exact approval bound to the replay evidence. | Target-Windows executor acceptance; fault/concurrency/rollback testing; an explicit policy if unattended company-wide replacement is ever desired; and separate registration/evidence for any additional executor family. |
| Learned automatic model replacement | Recommendations still use registered policies. Ordinary `model_record_run` telemetry is explicitly `reported`, while migration 012 reserves `host` model-run provenance and migration 014 adds paired host-run experiment attestations. The internal evidence service requires provider/model identity, provider response ID and provider-emitted token usage plus adapter-requested effort, adapter-monotonic runtime, completion status and exact input/output digests. A frozen protected-Fable review can attest one pair and identify a quality-preserving runtime/token improvement, but the result explicitly has `policy_mutation_allowed=false`. CI uses synthetic provider envelopes to exercise this state machine and no host evidence sink is exposed through MCP. | A production live-provider adapter that constructs the required envelope from actual vendor-emitted structured metadata on comparable prompts; repeated experiment aggregation across representative inputs; explicit policy-promotion authority; target-host/live-provider validation; and fault/concurrency analysis before policy mutation. Protected validation must remain non-downshiftable and excluded from experimentation. |
| Arbitrary transparent session replacement | Hooks checkpoint and restore material state around native sessions/compaction. There is no custom terminal host that replaces every Claude context invisibly. | Actual host lifecycle implementation and end-to-end tests. |
| Infinite nested executive hierarchy | Chairman coordinates ordinary subagents; directors return staffing requests rather than recursively spawning unsupported workers. | Supported nested runtime or a separately tested external coordinator. |
| Chaotic company-disk project reconstruction | Mechanical folder ingestion assigns a nominated project. It does not autonomously infer an entire trustworthy company taxonomy. | Project-discovery evaluation and review of ambiguous assignments. |
| Annual unattended market research | Domain due dates and explicit refresh records exist. No annual background scheduler is installed. | A separately authorized scheduler and actual research/validation execution. |
| Automatic best-expert hiring | Roles/skills/capability records aid routing; shared catalog definitions require exact company approval. No benchmark establishes that a generated persona is the world's best expert. | Domain-specific competence evaluations and documented evidence retrieval. |
| Automatic company DB reporting | Vres manages its own memory database. It does not automatically discover or authorize arbitrary reporting databases. | Explicit read-only data-source integration and query validation. |
| Generic recipe execution | Vres has one registered deterministic JSON recipe family with bounded `copy`, `rename`, `set`, `delete`, `pick`, `sort`, `sum` and `count` operations. It executes in an isolated no-shell worker with time/input/output budgets and contract validation. Arbitrary Python, shell, imports, filesystem/network operations, external programs and unregistered implementation references are not executable through this path. | Every additional executor family needs explicit code registration, bounded permissions, verified input/output contracts, runtime-owned measurement provenance and its own target-platform validation. A universal arbitrary-code runner remains out of scope. |

## Executed and unexecuted target dependencies

Repository CI starts PostgreSQL 16, applies the packaged migrations through the guarded integration fixture,
and runs the full test suite including company-authority, optimization-replay, bounded-executor, company-
optimization and model-experiment evidence journeys. The authority journey covers exact-approved global sources,
durable knowledge, registry objects, capability definitions and accepted procedure baselines, including scope
provenance and changed-content rejection. The replay journey covers a reported candidate that cannot
self-promote, runtime-classified baseline/candidate runs on the same input, frozen replay context, an observed
Fable validator completion, replay attestation, Pareto assessment and promotion with retained evidence
provenance.

The bounded-executor journey goes further: it creates a project-scoped accepted procedure using the registered
JSON recipe implementation, registers a protected-contract-identical candidate, executes the baseline and
candidate through the actual isolated `vres_os.procedure_worker` on the same 10,000-value input, records the
worker-produced timing and canonical input/output digests as runtime evidence, verifies identical output,
records the protected replay validation, and promotes the measured Pareto-superior candidate. The executor does
not persist a fabricated quality score; when both deterministic runs lack a numeric quality score, the exact
protected-contract replay plus host-observed output equivalence supplies only the no-quality-regression basis for
the Pareto gate. The bounded-executor tranche passed 254 tests on its recorded Linux/PostgreSQL head.

Migration `012_model_run_provenance.sql` executes against PostgreSQL 16 in CI. It preserves existing model
telemetry as `reported` and reserves `host` provenance plus input/output digests and execution evidence for
comparable model experiments. Ordinary model telemetry explicitly writes `reported`, and the advisory aggregate
query explicitly filters to reported rows so host experiment evidence cannot be mixed into legacy telemetry.
The provenance-only validation head passed 256 tests against PostgreSQL 16.

Migration `013_company_optimization_authority.sql` and the company optimization journey execute against the same
disposable PostgreSQL 16 gate. The journey proves three distinct authority events: baseline publication,
candidate creation and final attested promotion. Candidate and promotion approvals are stored separately, the
promotion subject binds the replay attestation, run IDs, validation request, exact digests and contract
fingerprints, and the candidate approval cannot be reused as the promotion approval. The retry-hardened code head
passed 268 tests in the full PostgreSQL suite; the local credential-stripped gate passed 262 with six database
integration modules intentionally skipped.

Migration `014_model_experiment_attestation.sql` also executes against PostgreSQL 16. Its integration journey uses
two deliberately synthetic provider-shaped envelopes on the same exact input digest, freezes the pair into a
`model_experiment` validation context, records an observed Fable/high validator report with explicit
`candidate_quality_not_worse` and `protected_regression` findings, stores an immutable attestation, and can report
a one-pair runtime/token observation while explicitly refusing policy mutation. The host evidence contract
revalidates provider/model identity, provider response ID, provider-emitted usage, adapter-requested effort,
adapter-monotonic runtime and completion status whenever a host row is consumed. The packaged evidence head
passed **277 tests** in the full PostgreSQL suite; the credential-stripped local gate passed **270 tests with 7
intentionally skipped PostgreSQL integration modules** and installed-wheel smoke required migration 014 plus
`ModelExperimentService`.

That is real Linux/Python/PostgreSQL execution of Vres's model-experiment evidence **state machine**, not a live
Claude/Codex model experiment. The CI producer is synthetic and exists to prove application provenance,
validation and persistence semantics. There is no production adapter in this tranche that invokes live provider
candidates and obtains these fields from actual vendor responses, no repeated experiment corpus, and no policy
promotion authority or mutation path.

This audit environment still has not executed the Windows/PowerShell installer, Windows Credential Manager,
live Claude Code plugin/hooks/models, a live paired model experiment, the real MCP SDK transport, live Codex,
the bounded recipe worker on the target Windows installation, or a downloaded SentenceTransformer.
Installed-module smoke tests and Linux/subprocess integration are not substitutes for those target runtimes.
See LIVE-VERIFICATION.md for the required target tests.

The wheel is built with the declared build backend prepared in the CI environment and its package contents
checked. Runtime dependencies remain bounded version ranges, not a tested Windows lockfile. The installer
records `resolved-dependencies.txt` and runs `pip check`, but a resolved environment is not a reproducibility
guarantee. Optional embedding dependencies are large and are deliberately not installed by default.

## Security and authority

The local Windows user is a trusted operator. Claude tools, scripts and the memory runtime operate in
that user's security context. The design is not a multi-tenant server, a cryptographic validator identity
system, or protection against a local agent/operator allowed arbitrary shell access to the same files/database.

The validation hook checks a native subagent event, model-family evidence, registered session, frozen state,
reviewed artifact hashes and a structured report. Procedure replay freezes the exact procedure replay context;
model experimentation freezes exact host run IDs, identities, digests and execution-evidence fingerprints. This
does not prove every criterion was actually exercised, that a local user with equal privileges could not forge
inputs, or that synthetic provider envelopes are equivalent to a live provider transport. The bounded JSON
worker narrows its own executable language, but it is still application-level isolation under the same local OS
account. High effort is configured rather than cryptographically attested.

Project-local approvals point to a real persisted user turn and a specific action/subject. Company-authority
writes add an exact redacted subject fingerprint and dedicated `company_<action>` approval type. Changing the
approved company content changes that fingerprint and fails closed. Accepted company-wide procedure approval
binds the reusable procedure contract, implementation reference and any initial baseline metrics to the same
scope provenance stored on the procedure. That baseline approval does not authorize optimization. A bounded
company candidate requires a separate exact optimization approval, and making an attested candidate globally
preferred requires another exact approval tied to the frozen replay evidence. Candidate and promotion provenance
are stored separately and retries must use the same exact approval. This is still application-level provenance,
not a cryptographic signature or independent identity system. Conditional/ambiguous assent must not be
broadened.

Model policies are shared operational routing state. A `host` row and even a favorable
`model_experiment_attestation` are evidence, not authority to alter shared policy. The evidence service explicitly
returns `policy_mutation_allowed=false`, the public MCP surfaces cannot write host model evidence or promote
policy, and protected Fable/high validation is not an experiment target. Any future promotion path must
independently establish repeated representative evidence plus the exact authority for changing policy.

Replay evidence uses `RESTRICT` references from attestations/optimization decisions to the runs and validation
request that justified promotion. Company optimization additionally retains exact candidate and promotion
approval references. Model experiment attestations likewise use `RESTRICT` references to both exact model runs
and the protected validation request. This is intended to preserve evidence chains. Administrators with direct
DB privileges can still modify or delete data by operating outside the cooperative application workflow; Vres
is not a tamper-proof ledger.

Redaction covers common credential patterns, not all possible secrets. The registered JSON executor refuses
payloads or recipe constants whose persisted redacted representation differs from the supplied value, and the
model experiment host envelope is likewise non-secret. Never place real credentials in chat, source documents,
transcripts, test fixtures or Git. PostgreSQL administrators and local users with filesystem/vault privileges
remain able to access data. Vres does not encrypt all database contents itself. Use infrastructure encryption,
access controls and backups appropriate to the deployment.

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

Migration/application semantics and the normal integration journeys execute against PostgreSQL 16 in CI.
Real concurrent lock contention, serialization behavior under load, duplicate concurrent promotion attempts and
interrupted transactions still require separate stress/fault testing. Model experiments additionally need
repeated-run/concurrency semantics before they can support a future policy decision. No database-wide
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
