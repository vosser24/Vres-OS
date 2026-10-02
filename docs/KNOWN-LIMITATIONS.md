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
| Infinite nested executive hierarchy | Vres now supports a flat governed project-agent work graph with native Claude fan-out/fan-in, dependencies, retries and bounded parallelism. It still does not provide recursive self-spawning executive hierarchies; project agents execute through trusted Vres worker envelopes. | Keep the hierarchy flat unless the host later supplies a separately testable nested-runtime contract. |
| Project-agent parallel execution | Migrations 033–034 and CI exercise project-local agent identity, dependency readiness, retry isolation, host-evidence binding, non-overlapping declared write scopes and durable work-unit acceptance criteria. Direct Write/Edit tools are scope-checked after host binding. Deterministic criteria can complete without a review agent; judgmental write-unit criteria require a declared dependent report-only verifier and block finalization until accepted. CI does not prove real Claude workers overlap in time on the target Windows host, and Bash is not presented as a filesystem sandbox. | Target-Windows physical acceptance must show 2+ registered agents genuinely overlap, a dependent unit starts only after prerequisites pass, a failed sibling alone retries, scope collisions are denied, observed model/agent/work-unit provenance is retained, deterministic work stays minimally staffed, and judgmental product acceptance is independently exercised. |
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
model experiment host envelope is likewise non-secret. The #163 Credential Broker adds deterministic high-confidence
`UserPromptSubmit` interception, current-user resource metadata, explicit project bindings, Locker-backed pending
capture and exact-value child-output redaction. Repository tests can prove that blocked synthetic credentials do
not enter Vres's PostgreSQL user-input ledger; they cannot prove what the installed Claude Code host has already
written to its own transcript/debug state before or around hook execution. Windows User-A/User-B isolation and
real host transcript/debug behavior remain mandatory #169 physical acceptance criteria.

Never intentionally place real credentials in chat, source documents, transcripts, test fixtures or Git.
PostgreSQL administrators and local users with filesystem/vault privileges remain able to access data. Vres does
not encrypt all database contents itself. Use infrastructure encryption, access controls and backups appropriate
to the deployment.

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

Secret-safe onboarding (#164) is a deterministic pattern policy, not proof that no secret exists. Unquoted
values containing spaces are redacted only up to the first whitespace; keys with a prefix over 64 characters
may miss the primary rule (the residual check may still stop the file); a secret with no credential-looking
key and no known token shape is not detected. Name rules are deliberately broad: `auth.*` also excludes
`auth.py`, and `.pem`/`.key` files are excluded even if public, so useful content can be skipped. The word
"Bearer" followed by a token-like word in prose counts as sanitized. Onboarding never stores or captures
secrets; confirming a candidate credential needs the user-local Credential Broker (#163).
The residual policy prefers false-positive fail-closed: a benign key that contains a credential word with a long value (for example `password_policy: required-by-security`) sends the file to review and retains no content. #164 is not universal secret detection.

Embeddings during onboarding (#164) are optional for basic ingestion and cataloguing, and are the intended path to
semantic retrieval of onboarded project knowledge. Onboarding is not offline-only. When `embeddings_enabled` is true,
only sanitized chunks are queued; the worker loads the model named by Vres configuration
(`ConfigStore().load().embedding_model`, never project content) local-files-only first, and only on a genuine local
cache miss acquires that same model from its repository (`trust_remote_code=False` on both paths). Downloading a model
sends no project text, and encoding always runs locally; there is no remote embedding provider. Project content can
never choose a model or trigger network access: URLs, model names and links in documents are inert data. If
acquisition fails, sanitized chunks stay, jobs are not lost (see below) and no
embedding is reported complete. The exception type used to detect a cache miss (`OSError` from the local-only load)
and the `local_files_only` argument were not verified against an installed `sentence-transformers` in this
environment (the package is optional and not installed here); a real download/first-run check remains a live gate.
Jobs stay pending while attempts remain and become `failed` after 3 attempts; a `failed` job is not automatically revived, so a machine that was offline for all attempts needs its failed embedding jobs reset before acquisition is retried. The model download reveals the model id and the client IP to the model repository, never project content. `semantic_search` loads the same configured model and can therefore also trigger the same acquisition. Cache-miss detection treats any `OSError` from the local-only load as a miss (this also covers an unreadable cache) and is unverified against the real library.

Optional vector search requires real model/download/runtime verification. JSON-vector fallback scans a
bounded candidate set, so recall is limited and must not be described as exhaustive. Greek/Greeklish quality
has no real company benchmark yet. Similarity, numeric confidence and repeated model agreement are not
probabilities of truth. Knowledge freshness requires real re-verification, not just resetting a date.

### Unified experience retrieval (#176 E3)

E3 exposes one explicit, read-only MCP tool, `experience_retrieve`, bound to the current session project. It
returns a bounded experience pack read from the existing Vres truth owners (knowledge, procedures, task
decisions, E1 episodes, relations); it is not a second generic memory authority and stores nothing.

- Authority and scope are applied before relevance. Relevance, semantic similarity and recency are ordering
  signals only and are not truth; stored `confidence` is passed through as author-asserted, not verified.
- Conflicts, stale items, challenged items and premise mismatches are surfaced with their members and reasons.
  E3 does not silently resolve, average or promote them. Premise checks compare only caller-asserted premises
  against premises the item states; unstated premises are flagged unverified, not matched.
- Raw fallback is a bounded lexical search over already-stored, sanitized chunks, returned as low-trust evidence
  references only. E3 introduces no filesystem or network re-read of raw sources.
- The optional semantic signal depends on the embedding limitations above (optional model, bounded JSON-vector
  fallback, truncation reported); when unavailable, retrieval degrades to lexical and says so.
- Automatic Chairman/hook injection is not enabled in E3; it remains E8. Retrieval observation and utility
  recording are not enabled in E3; they remain E6. Retrieval is therefore an explicit call, not autonomous
  infinite memory or context injection.
- Live proof of the packaged tool on the target host is a separate gate; see the E3 handoff for what was and was
  not exercised.

### Temporal lifecycle and revocation (#176 E4)

- Forgetting controls use, not history: retire, supersede and revoke never delete sources, evidence, episodes or ledger
  rows. Revoked memory is a metadata-only tombstone in historical retrieval; a tombstone still discloses that a
  revoked item (by key) matched the query. Physical erasure of source bytes is not provided.
- Contamination is an attestation, not proof. Vres records no consumption of context, so every open session of the
  project is marked "may have loaded" on revocation; `context_refresh_ack` is the Chairman's attestation that context
  was re-derived. Checkpoint prose and transcript text are not scanned, and artifacts already written are not cleansed.
- While contaminated, the PreToolUse hook denies every Vres tool except the safe list and `context_refresh_ack`, and
  admits that call only for the latest contamination event of the host session (exact tool name, exact
  `{"request": {"contaminated_event_key": ...}}` input, parent only). The admitted hook writes a single-use, 120-second
  attestation on that host session; the MCP tool consumes it and fails closed (`refresh_not_attested`) without one, so
  the tool cannot acknowledge another session by key. The trust root is the host hook's `session_id`; the runtime
  database role could forge the attestation, as it could already append ledger rows. Denials and notices name up to
  five revoked identifiers, or a count for larger cascades; the full cascade stays in the lifecycle ledger.
- `source_revoke` results above 8 KiB return counts and sha256 digests instead of key lists. A cascade over 500
  nodes fails closed with no change. There is no `restore_source`; recovery is a new source plus approved reinstatement.
- Lifecycle approvals are bound to the exact action and target and are project scope only. Company-scope lifecycle is
  deferred. Legacy `KnowledgeService.update/supersede` service methods remain callable internally without the project
  lifecycle lock; the public `knowledge_promote(status='challenged')` and `knowledge_supersede` tools now route through
  the ledgered lifecycle service and need an approval and a reason.
- Retrieval carry-over: episode lifecycle state in historical queries is the current ledger state, not the state at
  `as_of` (fail-closed); episode support considers direct `derived_from` sources only; `experience_consolidation`
  keeps a status deny-list that covers every status the schema allows. The raw-chunk fallback defect is fixed in the closure stage (`_raw` applies the same dead-support gate; pinned by
  `test_raw_chunk_of_a_company_item_whose_only_support_is_revoked_is_never_returned`). Not covered by E4: the
  `knowledge_search`/embedding readers still return a company item whose only support is revoked (outside the E3
  retrieval-integration clause; future cleanup).

## Licensing and supply chain

Vres source is MIT. Third-party packages/models have their own licenses; the PDF dependency is now pypdf,
not PyMuPDF. This is not a legal clearance of the entire transitive dependency graph. No complete vulnerability
scan, signed installer, Windows code-signing certificate or tested offline dependency mirror is included.
Local SHA-256 manifests prove file consistency relative to the supplied manifest, not publisher authenticity.
