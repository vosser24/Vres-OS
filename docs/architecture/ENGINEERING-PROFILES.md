# Vres Engineering Architecture Profiles

These profiles specialize the universal Engineering Architecture Constitution without weakening it.

A project may activate more than one profile. Profiles are proportional guidance, not permission to manufacture empty structure.

## minimal

Use for a small application/utility with few responsibilities.

Minimum expectations:

- clear owner/responsibility;
- tests appropriate to risk;
- secret safety;
- intentional dependencies;
- no circular dependency;
- no speculative app/modules/domains/shared scaffolding.

Promote responsibilities into explicit layers only when real reuse or complexity appears.

## frontend-web

Use for browser applications.

As the application grows, prefer:

```text
app
 ↓
modules
 ↓
domains
 ↓
shared
```

Expect where relevant:

- route ownership;
- module public APIs;
- route-level lazy loading;
- route-level failure isolation;
- shared design system/chart/table primitives;
- intentional query/cache layer;
- bounded request fan-out;
- route/module tests.

## full-stack-web

Use for applications with meaningful frontend and backend responsibilities.

Frontend follows the frontend-web profile.

Backend defaults to:

```text
app/server
 ↓
route/feature modules
 ↓
domain services
 ↓
platform/infrastructure
 ↓
database/external systems
```

Prefer one manageable deployment/modular monolith until real evidence justifies service distribution.

## python-service

Use for Python APIs/services.

Expect where relevant:

- thin application factory;
- route/feature modules;
- domain services;
- central platform/config/db/logging boundaries;
- no sibling feature-module implementation imports;
- explicit package APIs;
- Import Linter/equivalent dependency enforcement when the project is large enough.

## data-analytics

Use for analytical/reporting/data applications.

Expect:

- explicit data contracts/source-of-truth;
- honest missing/unknown semantics;
- reusable metrics/calculations in domain owners;
- common chart/table/export foundations where UI exists;
- bounded data fetching/query behavior;
- no client loading of giant raw datasets just to render small views;
- database/query performance evidence appropriate to scale.

## pipeline-jobs

Use for scheduled jobs, ETL/ELT, orchestration and operational pipelines.

Expect each material job to declare:

- key/owner;
- dependencies;
- cadence;
- timeout;
- retry behavior;
- criticality;
- outputs;
- freshness expectations.

Entry scripts remain thin. Reusable logic belongs in pipeline/domain/integration packages.

## cli-library

Use for CLI tools and reusable libraries.

Expect:

- thin executable entrypoints;
- reusable logic in importable packages;
- deliberate public API;
- dependency discipline;
- tests independent of the executable wrapper.

## Profile selection

Profile selection is evidence-driven from the actual codebase and user intent.

For existing-project adoption:

1. deterministic audit proposes profile signals;
2. Chairman confirms/refines the applicable profile based on code and purpose;
3. the alignment plan states the target profile(s);
4. protected Fable/high validates the plan before architecture-changing adoption work.

No profile changes the rule that users interact with Vres conversationally rather than through internal commands.
