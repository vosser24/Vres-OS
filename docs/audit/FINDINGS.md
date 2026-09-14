# Audit findings and disposition

These are concrete code/boundary findings from the recovered tree and this audit, not a claim that all future
corner cases are eliminated. Exact execution counts/coverage belong to the generated release evidence.
Tests named below may use scripted DB/service doubles; PostgreSQL, Windows and live-model proof are separate.

| Area | Finding / correction | Local evidence | Remaining target proof |
|---|---|---|---|
| Recovery | Historical claimed tree was not in the exported bundle. Recovered bundle plus ZIP, committed baseline, preserved originals. | Git history, migration baseline JSON, release byte comparison | Remote GitHub availability |
| DB setup | Existing role password/ownership could be changed; now refuse existing auto-provision targets. | `test_audit_regressions.py`, `test_release_boundaries.py` | Real roles, permissions, interrupted provisioning |
| Selftest | Obsolete acceptance argument made first setup fragile; use actual approval/procedure API and isolated cleanup. | Source call contracts and local entry-point tests | Real PostgreSQL selftest |
| Readiness | Config ready could precede completed migration/selftest; now publish last and restore prior config on failure. | Setup failure/recovery regression doubles | Vault + real migration failure |
| DB errors | Runtime SQL bugs could look like outages or malformed inputs; narrow exception boundaries. | Error-boundary tests | Real psycopg exception hierarchy |
| Migrations | Missing integrity checks and upgrades could edit old SQL; preserve recovered 001–006, additive 007–009, checksums/locks. | Hash/sequence/package gate | Execute and migrate PostgreSQL |
| Session binding | Latest-task/MCP startup ID could select wrong work after clear; explicit current hook ID and scoped binding. | Repository/hook/MCP tests | Native clear, compaction, concurrent windows |
| Recovery bounds | Transcript input could be huge/secret-bearing; bounded tail, exclude tool/thinking content and redact. | Real file/stream tests | Native transcript compatibility |
| Task authority | Ordinary state edits could self-declare passed; reject them and require observed review. | Public/service authority tests | Actual protected subagent events |
| Review freshness | A pass could certify changed state/files; bind request to state and artifact hashes and reject stale completion. | File/state digest and stale-review tests | Native model/hook lifecycle |
| Approval | Caller strings could impersonate acceptance; record real user turn and action/subject, prevent reuse across subjects. | Approval and public decision tests | Natural-language ambiguity/call ordering |
| Procedure replay | Retry could create fake versions; fingerprint accepted contract and experiment under locks. | Idempotency and changed-contract regressions | Concurrent transactions |
| Side-effect order | Invalid partial benchmark could consume approval before error; validate before approval persistence. | `test_incomplete_procedure_metrics_do_not_consume_approval` | Real transport retries |
| Evidence metrics | Missing/NaN/negative/fractional values could mislead optimization; validate and retain missing as unknown. | Metric/Pareto tests | Real paired measurement instrumentation |
| Auto-promotion | Agent booleans/scores were not independent proof; automatic procedure/model promotion held. | Public API and policy tests | Host-measured replay implementation |
| Validator policy | Alias/unknown phase could drift into weak fallback; protect review/audit aliases and reject unknown phase. | Model-phase tests | Actual entitlement/resolved model |
| Knowledge | Invented type, direct canonical, mutable statement could bypass governance; allowlist/gates/immutable supersession. | Knowledge lifecycle boundary tests | Source validity and domain judgment |
| Scope | Identical files across projects could share authority; scope-aware identity and immutable source location ownership. | Source/registry/public scoped access tests | Actual multi-project DB retrieval |
| Registry graph | Untyped keys and unknown nodes could appear equivalent/no-impact; typed nodes, explicit unknown, bounded traversal. | Graph identity/bounds tests | Large graph performance/completeness policy |
| Provenance | Repeated relation writes overwrote supporting evidence; additive evidence table. | Relation SQL boundary tests | Concurrent evidence writes |
| Preferences | Negation could be stripped while claiming user preference; require full quoted actual instruction. | Preference/event regressions | Actual conversation semantics |
| Refresh | A validation string could certify another/unreviewed delta; exact artifact/request/task matching. | Refresh artifact/freshness tests | Actual research and strongest validator |
| Shared expertise | A project agent could publish arbitrary global capability definitions; public registration held. | Shared-catalog authority test | Explicit future catalog-approval path |
| Documents | Unbounded extraction/ZIP bombs/content mutation were possible; preflight/bounds/isolated workers/stability checks. | Actual malformed/OOXML/PDF/CSV/text tests | Windows memory limits, adversarial corpus |
| Credentials | Search/event errors could persist common secrets; broader URI/token redaction and scoped metadata. | Redaction/persistence boundary tests | Real vault, uncommon secrets |
| Workers | PID assumptions, stale claim or failed load could strand/rewrite jobs; kernel lock + DB lease/attempt checks. | Lock/subprocess/embedding doubles | Real DB concurrency and model inference |
| Python launch | Project CWD could shadow runtime modules; isolated Python plus approved worker launcher. | Subprocess/project-shadowing tests | Native Windows launch behavior |
| Codex | Late path/prompt validation and unbounded execution; validate before lookup, stdin prompt, read-only flags, timeout/output caps. | Real generic subprocess + adapter argument tests | Real Codex sandbox/login |
| Windows update | In-place venv overwrite or relocation risks; permanent staged runtime, pointer/plugin/bin publication and recovery journal. | Static install contracts only | PowerShell install/update/failure/rollback |
| Windows identity | Loose release path, wrong UTF-8 reads and unsupported default Python could break safety/installation. | Static path/encoding/discovery contracts | Greek user paths and side-by-side Python |
| Packaging | Wheel/package data had not been independently checked; actual offline build, byte comparisons, separate import smoke. | release_gate logs | Runtime dependency resolution on Windows |
| Test data | Integration tests could leave unscoped records; dedicated `_test`/ack gate, unique project, cleanup only own rows. | Fixture inspection; tests remain skipped locally | Execute integration suite |
| Distribution | Old ZIP and latest claims diverged; export exact clean commit and verify restored bundle/ZIP/wheel. | Separate export manifest and recovery test logs | Download integrity on target |

## Deliberate non-claims

No separate live validator model executed in this audit. No test suite here proves every business acceptance
criterion or every dependency. Coverage records missed lines/branches. Full unattended company routing, safe
universal deterministic executors, cryptographic approval/reviewer attestation, complete company migration,
unattended annual research and paired-measurement auto-optimization remain outside this preview's proof.
