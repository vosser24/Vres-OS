# Release validation: what the evidence means

## Reproduce the local gate

From the repository root, using Python 3.12 or 3.13:

```powershell
python -m pip install ".[full,dev]"
python scripts\release_gate.py --output C:\VresEvidence\static
```

The gate writes actual logs, JUnit, coverage JSON, a file ledger and wheel-content checks to the nominated
output directory. Use a directory outside the checkout. A nonzero exit is a failed gate, not a warning to
ignore. Dependency installation needs network access unless an independently prepared package mirror exists.
The offline wheel stage additionally requires the declared build backend to be present in the prepared
environment; CI provisions the exact `setuptools==82.0.1` backend before invoking this gate.

This gate executes local tests and Python compilation; parses JSON/frontmatter; checks package and migration
manifests; builds an actual wheel without dependency resolution or build isolation; compares packaged
Python/SQL bytes to source; smoke-imports selected installed modules in a separate directory; checks local
documentation links; and runs `git diff --check` when a Git checkout is available. The installed-wheel smoke
requires the company MCP entry point, replay service, bounded executor, deterministic recipe module, procedure
worker, model-policy module, model-experiment evidence service and all packaged migrations currently present
through `014_model_experiment_attestation.sql`. The structure gate also requires the controlled project executor
workflow plus the exact-approved company candidate/promotion tools while separately testing that raw runtime,
host-model-evidence and raw promotion/policy-mutation sinks are not exposed as MCP tools.

The local gate deliberately removes ambient Vres database credentials, so PostgreSQL integration tests are
reported as skipped there. It does NOT execute PowerShell, PostgreSQL or a live model. Structural migration
checks are not a SQL parser or a guarantee that PostgreSQL accepts the schema. Any integration skips are
reported, never counted as passes. Tests using scripted DB connections prove submitted SQL/parameters and
application branching, not DB semantics.

## PostgreSQL CI gate

The repository workflow adds a separate runtime gate before the local release gate. It starts a disposable
PostgreSQL 16 service named with the required `_test` suffix, sets the explicit integration opt-in flag,
installs the full test runtime, and executes the complete test suite. The integration fixture applies the
packaged migrations and cleans only records belonging to its own generated project. This exercises real
PostgreSQL SQL/application semantics for the tested journeys without changing the local gate's credential-safe
contract.

For the company-authority tranche, the green CI boundary includes migration `010_company_authority.sql`,
exact-subject approval provenance, company-wide source/knowledge/registry publication, shared capability
catalog registration, exact-approved company-wide procedure baselines, and the installed
`vres_os.company_mcp` entry-point smoke.

For the optimization-evidence tranche, the green CI boundary additionally includes
`011_optimization_attestation.sql`, runtime-vs-reported measurement provenance, exact input/output digests,
frozen validation contexts, replay attestations, PostgreSQL `numeric`/Python `Decimal` metric handling, and a
replay journey that proves a candidate cannot attest before protected validation and can be promoted only after
a current Fable-observed PASS, unchanged evidence, exact contract fingerprints and the Pareto gate. The trusted
runtime-run and raw promotion sinks remain intentionally absent from both MCP surfaces.

For the bounded-executor tranche, CI executes the registered `vres:builtin:json-recipe:v1` worker rather than
inserting runtime measurements directly. The integration journey accepts a project-scoped baseline recipe,
registers a candidate with the protected input/invariant/validation/output contracts copied unchanged, runs
baseline and candidate through the isolated no-shell worker on the same 10,000-value input, verifies identical
canonical input/output digests and result, records the worker-produced timing evidence, freezes that pair into
protected replay validation, records the bound Fable validator report, and promotes the measured Pareto-superior
candidate. The executor stores no fabricated quality score; exact protected-contract replay plus host-observed
output equivalence supplies only the no-quality-regression comparison basis when both deterministic runs have
no numeric quality score.

For the model-provenance tranche, migration `012_model_run_provenance.sql` adds a fail-visible distinction
between ordinary `reported` model telemetry and a reserved `host` measurement class, together with exact
input/output digests and execution evidence. Existing rows remain `reported`, and `ModelPolicyService.record_run`
explicitly writes `reported` so the ordinary MCP telemetry path cannot become host evidence through a database
default.

For the company-optimization-authority tranche, migration `013_company_optimization_authority.sql` preserves
separate candidate and promotion approval provenance. The PostgreSQL journey begins with an exact-approved
company-wide bounded baseline, requires a fresh exact `company_procedure_optimize` approval to create the
protected-contract-identical candidate, executes baseline/candidate through the registered bounded worker,
freezes and validates the paired replay, and then requires another fresh exact approval before the attested
candidate can become globally preferred. The promotion subject binds the expected preferred/candidate versions,
replay attestation, run IDs, validation request, input/output digests and contract fingerprints. The candidate
approval cannot authorize promotion, and a baseline approval cannot authorize either optimization phase.

For the model-experiment-evidence tranche, migration `014_model_experiment_attestation.sql` adds an immutable
paired experiment attestation that references two host-classified model runs plus one frozen protected validation
request. The internal host-run sink requires a provider-shaped execution envelope whose provider/model identity,
provider response ID, provider-emitted token usage, requested effort, adapter-monotonic runtime and completion
status agree exactly with the persisted run. Baseline and candidate must be successful runs on the same task,
phase, task family and exact input digest, with distinct model/effort identities. The protected validator receives
a typed `model_experiment` context and must return the exact experiment key plus boolean quality-no-worse and
protected-regression findings before an attestation can be recorded. A favorable pair may be reported as an
observed Pareto improvement for that exact input, but the service explicitly returns
`policy_mutation_allowed=false`; no model-policy write path is introduced by this tranche. The protected
Fable/high validation phase itself is excluded from experimentation.

The model-experiment PostgreSQL integration deliberately uses **synthetic provider envelopes** and a synthetic
observed Fable transcript fixture to prove the database/provenance/state-machine checks. It does not invoke a
live Claude/Codex provider and is not evidence that provider identity, token usage or runtime have been captured
from a real vendor response. The production boundary is therefore: Vres can validate and persist a provider-
shaped host-evidence contract, but a real live-provider adapter still has to construct that envelope from actual
vendor-emitted metadata before a live model experiment can be claimed.

The retry-hardened company-optimization code head reported **268 passed** in the full PostgreSQL 16 workflow.
Its credential-stripped local release gate reported **262 passed and 6 intentionally skipped PostgreSQL
integration modules**. Both lint layers, installed-wheel smoke through migration 013, the offline release gate
and evidence upload passed. The approved MCP promotion path was additionally hardened so a safe idempotent retry
routes directly to the service transaction instead of failing first on a now-stale preview; repeated candidate
previews also reuse the already allocated exact candidate version for the same experiment.

The model-experiment package-proof head `16e7d690c610fc089cb53aef770c3c6a1a35f7ed` reported **277 passed** in the
full PostgreSQL 16 workflow. Its credential-stripped local release gate reported **270 passed and 7 intentionally
skipped PostgreSQL integration modules**. Both lint layers, installed-wheel smoke through migration 014,
`ModelExperimentService` import from the installed wheel, the offline release gate and evidence upload passed.
The uploaded release-gate evidence artifact for that run was ID `10343711282`; the uploaded ZIP SHA-256 was
`3b9b4d04f23088638970a70942abb07b642ceed819f266fd112e2730717db395`.

The bounded executor and company optimization evidence remain deliberately narrow. They prove the registered
JSON recipe implementation and exact-approved global authority workflow on the recorded Linux/Python runner,
not arbitrary Python or shell execution, not a universal procedure compiler, not unattended company-wide
replacement, and not the target Windows installation. Its recipe language has no shell, filesystem, network,
import or arbitrary-code operation. Technical Pareto superiority alone never grants company promotion authority.

The model evidence is similarly bounded. PostgreSQL accepts both the reported-vs-host provenance schema and the
paired model-experiment attestation state machine. It is **not** evidence that live Claude/Codex model identity,
runtime, quality, cost or token usage has been measured comparably. A live host experiment must still capture
provider-emitted structured metadata on exact comparable inputs through a verified adapter, and any later model-
policy promotion must have its own repeated-evidence rule and explicit policy authority. The protected Fable/high
validation policy remains non-downshiftable.

A green Linux/PostgreSQL CI run is still not Windows acceptance, a production database authorization,
concurrency/load/fault proof, a live Claude/Codex transport test, or proof against a hostile local administrator.
The bounded worker and any future live-provider model experiment runner must still be exercised through the exact
installed artifact on the target Windows live-test host before those target capabilities can claim acceptance.

## Release artifact protocol

1. Finish source changes and run the gate successfully.
2. Commit the source, tests and docs. Never label uncommitted files a release commit.
3. Require the PostgreSQL CI workflow to pass on the exact PR/release head.
4. Re-run the local gate on that clean commit and capture its full SHA/tree ID.
5. Export source with `git archive`, and full history with `git bundle create ... --all`.
6. Restore the bundle into a separate checkout, run `git fsck`, and run the tests there.
7. Compare every source ZIP member byte-for-byte with the committed Git blob.
8. Inspect the wheel, including every migration through 014 and the registered executor/worker/model-policy/
   model-experiment modules. A wheel alone is not the Windows distribution: it excludes the top-level
   installer/plugin/docs by design.
9. Produce a manifest with artifact SHA-256 hashes, commit/tree IDs, environment inventory and exact results.
10. Include gate logs and a per-file evidence ledger. Preserve unavailable dependencies as NOT RUN.

Do not place a wheel inside the source commit and then imply the commit produced itself. Generated release
artifacts belong beside the source export; record their hashes in a separate release manifest.

## Labels

- **Local gate passed:** the exact local commands in the evidence log passed in the recorded environment.
- **PostgreSQL CI passed:** the exact repository head passed the full suite against the workflow's disposable
  PostgreSQL service; this is scoped runtime evidence, not target-Windows acceptance.
- **Replay evidence path passed:** the exact head proved the tested runtime-run → frozen protected validation →
  replay attestation → Pareto assessment → promotion state machine. This label alone does not imply an executor.
- **Bounded registered executor passed:** the exact head additionally produced the tested paired runtime evidence
  through the code-owned deterministic JSON worker and completed the protected project-scoped promotion journey.
  This label does not authorize arbitrary code.
- **Exact-approved company optimization passed:** the exact head additionally proved candidate authorization,
  bounded runtime replay, protected attestation, Pareto eligibility and a separately authorized company-wide
  promotion with retained candidate/promotion provenance. This label does not mean company optimization is
  unattended or automatically authorized.
- **Model telemetry provenance passed:** the exact head proved migration 012 and the explicit reported-vs-host
  storage boundary. It does not by itself mean a paired model experiment passed.
- **Host model experiment evidence path passed:** the exact head proved migration 014 and the tested synthetic
  host-envelope → frozen protected validation → model-experiment attestation → one-pair observation state machine.
  This label does **not** mean a live Claude/Codex provider was invoked, does not mean repeated statistical model
  evidence exists, and does not authorize or mutate model policy.
- **Controlled-live-test preview:** a packaged checkpoint with known held capabilities, ready to be evaluated
  on a disposable or otherwise controlled target; it is not yet proved usable by a novice.
- **Windows acceptance passed:** the exact live matrix was executed and reviewed against the exact artifact.
- **Production ready:** requires a separate operational/security/recovery acceptance; this audit does not claim it.

## Historical recovery

The recoverable ZIP reproduced 41 tests with two PostgreSQL test modules skipped. Larger historical chat
counts and claims of ten migrations were not present in that source. This audit preserves the recovered
001–006 migration bytes and added later migrations as new reviewed history. Only the current generated
evidence manifest and repository tree determine the current count; do not copy an old number into a README
as if it were a fresh test result.

## Validator independence

The repository CI and deterministic gates are execution evidence, not a substitute for an independent live
model review. The replay/executor/company-optimization/model-experiment integrations exercise the protected-
validator ingestion path using observed Fable transcript fixtures and exact frozen contexts; that proves the
application checks, not that an independent live model externally reviewed this build. The model-experiment
integration additionally uses synthetic provider envelopes rather than a real vendor response. Product-side
validator hooks are code under test, not a cryptographic identity proof. The strongest protected validation role
must still be observed in LIVE-VERIFICATION.md before trusting its application-level completion decisions on the
target host, and the model experiment path must observe real provider-emitted metadata before claiming live model
comparison evidence.
