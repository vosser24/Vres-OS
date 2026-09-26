# Vres Engineering Architecture Constitution

Version: 1.0  
Authority: Vres Engineering Governance  
Engineering maxim: **Local change. Predictable impact. Explicit dependencies. Shared truth. Isolated failures.**

This constitution is the default engineering architecture for software built or adopted under Vres. It applies proportionally: a small utility should remain small, while a serious application must expose stronger module, domain, platform, testing and failure-isolation boundaries. Architecture scales with the application; architectural discipline does not.

## 1. User interaction and authority

The user states intent in normal language. Chairman identifies and runs the required engineering workflow internally.

The only user-facing control phrases are:

- `start vres`;
- native `clear`.

Do not require users to learn Vres CLI, MCP, validation, architecture, credential, data-source or internal workflow commands. Internal tools may exist for deterministic execution, but they are implementation details.

Chairman remains the user-facing coordinator. Independent validators verify; they do not replace Chairman or user authority.

## 2. Default architecture

Prefer a modular monolith unless measured evidence justifies distribution.

For application frontends, the default dependency direction is:

```text
app
 ↓
modules
 ↓
domains
 ↓
shared
```

For service/backend code, the default direction is:

```text
app/server
 ↓
route or feature modules
 ↓
domain services
 ↓
platform/infrastructure
 ↓
database and external systems
```

Dependencies move downward. Circular dependencies are prohibited.

Do not force empty layers into small applications. Introduce a layer only when the responsibility exists.

## 3. Ownership

Every material responsibility has one canonical owner.

A feature/page module owns page-specific UI, route registration, local data composition, page-specific transformations, local tests and its intentional public API.

Reusable business logic belongs in a domain package, not in the first page that happened to need it.

Generic application capability belongs in shared/platform infrastructure only when it is genuinely generic.

Executable scripts and jobs are thin entrypoints. Reusable logic belongs in importable packages/services.

## 4. Feature/module isolation

A module must not import another feature module's private implementation.

If two modules need the same capability, promote the responsibility to the appropriate domain/shared owner.

Cross-boundary use goes through intentional public APIs.

Anything explicitly marked private/internal is not a cross-module contract.

## 5. Public APIs

Every substantive module/domain exposes an intentional public API appropriate to its language and framework.

Consumers use that public API rather than deep-importing implementation files.

Public APIs are kept smaller than internal implementations and changed deliberately.

## 6. Application composition

The application layer owns composition, registration and top-level providers/shells.

It should not accumulate arbitrary feature implementation.

Where the framework supports it, significant routes/pages should be lazy-loaded and independently failure-isolated. A failed page must not unnecessarily take unrelated navigation/pages down.

## 7. Domain and shared layers

Domains own reusable business entities, calculations, validation, contracts, query factories, normalization and business rules.

Domains do not know which current page renders them.

Shared/platform layers contain generic UI, data, API, routing, formatting, errors, configuration, logging, cache and infrastructure primitives.

Shared/platform code does not import feature modules. Shared code should not import business domains unless the selected profile explicitly defines a lower-level domain-independent adapter seam.

## 8. Data and API access

Visual/page components do not contain uncontrolled raw network/database access.

Use intentional query/data-access/domain-service boundaries.

Query/cache identity must include variables that materially affect the response.

Avoid duplicate request fan-out, eager loading of hidden features, giant default payloads and client-side loading of whole datasets merely to show a small view.

Prefer typed REST/domain/BFF APIs by default. Introduce GraphQL or another infrastructure technology only when measured evidence justifies it.

API technology does not replace query/database optimization.

## 9. Database boundary

Centralize connection creation, credentials and low-level data access behind platform/domain repository boundaries.

Do not scatter connection strings, credential access or random SQL connection creation across feature modules.

No database credential belongs in committed source.

## 10. Operational architecture

Separate jobs, pipelines, tools, integrations and database assets by responsibility when those responsibilities exist.

Complex scheduled workflows use an explicit dependency graph. Each material job should identify ownership, dependencies, cadence, timeout, criticality, retry behavior, outputs and freshness expectations.

Do not turn one generic scripts folder into an unowned second application.

## 11. Design systems, charts, tables and exports

Applications with repeated UI behavior use shared design tokens/components.

Equivalent UI semantics should not diverge page by page.

Analytical applications should use common chart/table/export foundations where appropriate. Chart type may vary with the analytical question; equivalent styling and interaction contracts should not drift independently.

Large exports should be server-side when client memory/payload cost becomes material.

## 12. Honest data

Never convert missing, unknown, unmeasured or unattributable data into zero unless zero is genuinely the measured value.

Do not manufacture a visualization because a design expects it when no trustworthy data exists. Render an explicit unavailable/instrumentation state.

## 13. Development/runtime consistency

Local development should execute the same application implementation used in production as closely as practical.

Do not maintain unrelated dev/prod backends merely for convenience.

## 14. Security

Never commit passwords, API keys, database passwords, auth cookies, private tokens or production credentials.

Use approved secret storage/delivery.

If an embedded credential is discovered, treat it as exposed: rotate it, remove it from current source, and assess history cleanup. Moving the value to another committed file is not remediation.

## 15. Tests

Every substantive module is independently testable.

Tests should cover the module/domain contract, critical transformations, empty/null states, relevant user-visible filters/rules and failure behavior.

Applications also maintain integration evidence appropriate to risk: route smoke, API contracts, architecture boundaries, database integration and browser smoke for critical flows.

## 16. Performance

Architecture must not create hidden performance regressions.

Measure the surfaces that matter: route/bundle size, initial request count, API p50/p95, payload size, DB query duration/count and connection usage.

Do not import every feature into the root bundle or repeatedly scan large facts without evidence.

## 17. Complexity signals

Large files are warning signals, not automatic violations.

Around 500–800 lines of ordinary application code, or several unrelated responsibilities in one file, should trigger responsibility review.

Split by ownership/responsibility, not mechanically by line count.

## 18. Reuse rule

Before implementing:

1. inspect the owning module;
2. inspect relevant domains;
3. inspect shared/platform capabilities;
4. reuse an existing implementation when the responsibility matches;
5. otherwise create the new behavior in the correct ownership layer.

Do not copy reusable calculations/components between feature folders.

Before creating shared code ask: **Would this abstraction still make sense if its current consumers disappeared?** If not, keep it local.

## 19. Existing-project adoption

Existing applications are never reorganized through one giant move.

Adoption is read-first and strangler-based:

```text
deterministic codebase inventory
→ architecture/dependency audit
→ profile selection
→ findings against this constitution
→ Chairman alignment plan
→ deterministic plan check + exact audit/plan digests
→ protected Fable/high validation of that exact plan identity
→ user decision/authority
→ incremental reversible tranches
→ architecture/test evidence after each tranche
```

Every material audit finding must be addressed by a bounded migration tranche or an explicit reviewed defer/exception.

No architecture-changing adoption work or activation may start from an unvalidated plan.

If protected Fable/high is unavailable, the plan is BLOCKED. Do not substitute another model, Codex review or caller assertion.

Fable validates the plan. Chairman presents/synthesizes it. The user decides what to authorize.

## 20. New applications

New applications establish the smallest appropriate architecture from the beginning.

Do not create empty enterprise-style directories for a tiny utility.

As responsibilities become substantive, establish explicit app/module/domain/shared or equivalent boundaries before coupling becomes entrenched.

Substantive modules receive short local `CLAUDE.md` ownership/API/dependency/test contracts. Do not duplicate this global constitution into every module.

## 21. Machine enforcement

Architecture is not prose only.

Where technically possible, CI checks:

- circular dependencies;
- forbidden dependency directions;
- sibling feature-module coupling;
- explicit private/internal cross-boundary imports;
- unresolved ownership/public-boundary gaps;
- secret scanning;
- route/job/database ownership appropriate to the selected profile.

Generated dependency maps are evidence; manually maintained diagrams are not source of truth when code can regenerate them.

## 22. Exceptions

An exception must be explicit, owned, justified and have a revisit/removal trigger.

Claude/Chairman may not invent an exception to make a plan pass.

## 23. Change discipline

Before a material software change determine internally:

1. what owns the change;
2. whether the behavior already exists;
3. whether it is module-local, domain or shared/platform;
4. the allowed dependency direction;
5. whether a public API changes;
6. whether the dependency map changes;
7. whether failure remains isolated.

Then implement the smallest coherent change.

When an existing structure conflicts with this constitution, fix only the boundary required for safe implementation and separately surface unrelated debt.

## 24. Definition of architectural success

Architecture is healthy when:

- one feature can be understood without reading the entire application;
- modifying one page rarely requires unrelated edits;
- reusable logic has one canonical owner;
- dependencies flow predictably;
- architecture rules are machine-enforced where possible;
- failures are isolated proportionately;
- data contracts are explicit;
- operational dependencies are visible;
- the deployment remains as simple as practical until evidence justifies distribution.
