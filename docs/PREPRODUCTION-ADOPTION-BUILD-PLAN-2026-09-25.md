# Vres-OS — Pre-Production Adoption Build Program

Date: 2026-09-25  
Repository: `vosser24/Vres-OS`  
Planning base: `4370e6794a3595696179f3781cfc661edf015e8d`  
Verified product implementation baseline before docs-only continuation commits: `acd45f1262979c16b1029ca9241976098cb503e8`

## 1. Purpose

This document freezes the implementation program that follows the 2026-09-25 real-world coverage audit.

The prior finalization program (#141, #146, #159) remains complete. Its accepted evidence is historical and reusable under the existing surface-triggered regression policy. This program does not reopen those issues.

The audit established genuine pre-production gaps around:

- current-user credential continuity and secure reuse across projects;
- secret-safe legacy ingestion;
- configurable Chairman model policy;
- clean adoption of an already-established current-user Claude environment;
- reusable current-user external database registration and semantic indexing;
- legacy-project adoption and canonical Claude/Vres scaffolding;
- integrated Windows acceptance against a realistic dirty-global Claude setup and an actual legacy project;
- final Production Readiness / Go-Live.

The implementation program is intentionally decomposed into bounded issues. Each issue must be built, validated, committed, merged and post-merge verified before the next dependent tranche starts.

## 2. Non-negotiable architecture

### 2.1 Current-Windows-user scope

The following reusable resources are local to the current Windows user only:

- credential resources and their metadata;
- Windows Credential Locker secret values;
- external data-source registrations;
- semantic database catalogs and schema/dependency fingerprints;
- explicit project-to-credential bindings;
- explicit project-to-data-source bindings;
- global Claude adoption snapshots/manifests for that user's Claude configuration.

They are not:

- machine-wide;
- company-wide Vres publication;
- automatically visible to another Windows account;
- ambient authority for every project.

A project must be explicitly linked to a reusable credential or data source before that project can consume it.

### 2.2 Secrets

Durable secret values belong only in the operating-system credential vault.

Vres PostgreSQL may store non-secret handles and metadata, but never durable secret values.

`.env` is not Vres's durable secret store.

Environment variables and local materialized files are temporary delivery mechanisms only.

No secret value may be promoted into:

- CLAUDE.md;
- Claude rules;
- skills;
- agents;
- project memory;
- Vres durable knowledge;
- procedures;
- review queues;
- embeddings;
- checkpoints;
- validation artifacts;
- normal logs.

Whenever a Vres-owned local adapter can consume a secret handle directly, the model must not receive the plaintext value.

### 2.3 Adoption authority

Legacy Claude/project content is untrusted historical input during adoption.

It is never policy authority merely because it was previously active.

The authority sequence is:

```text
deterministic scanner
    ↓
governed semantic worker where needed
    ↓
Chairman recommendation
    ↓
user KEEP / DROP decision
    ↓
protected Fable validation
    ↓
deterministic activation
```

Chairman recommends. The user decides. Protected validation verifies the exact approved manifest. Deterministic Vres code activates it.

### 2.4 Average-user interaction

Adoption findings are grouped for readability but individually decidable.

Every material item receives:

| Field | Requirement |
|---|---|
| # | Stable item number within the frozen adoption proposal |
| Item | Plain-language name |
| What it does | One concise explanation |
| Chairman recommendation | KEEP / DROP / KEEP→MOVE TO PROJECT / KEEP DISABLED / REVIEW CAREFULLY |
| Why | Short recommendation rationale |
| Destination if KEEP | Global preference, project rule, capability candidate, procedure candidate, knowledge, etc. |

The user's action remains simple:

```text
KEEP 2,3,7
DROP 1,4,5,6
```

Grouping never implies bulk approval. Missing item numbers remain unresolved. Vres must not guess.

DROP means not active/not promoted. The immutable adoption backup is retained according to retention policy.

### 2.5 Model authority

Initial target control-plane policy:

```text
Chairman               Opus / medium
Routine governed work  Sonnet
Deep governed work     Opus when routed
Routing arbiter        Fable / high when required
Protected validator    Fable / high
```

Model family policy is generation-tolerant. Do not hard-code `claude-opus-5-5`.

Host-observed physical identity remains evidence. Telemetry does not automatically change model policy.

### 2.6 Database authority

External database onboarding starts read-only.

Structural metadata acquisition must be deterministic first.

Semantic interpretation is evidence-bearing analysis, not automatic truth.

No raw business-row sampling is required for the initial catalog and must not happen merely because the database can be queried.

## 3. Execution order

The authoritative dependency order is:

```text
#163 Credential Broker
      ↓
#164 Secret-safe onboarding
      ↓
#165 Chairman Opus/medium policy
      ↓
#166 Global Claude adoption
      ↓
#167 Data Source Registry + semantic DB catalog
      ↓
#168 Project adoption + canonical scaffold
      ↓
#169 Integrated Windows live acceptance
      ↓
#170 Production Readiness / Go-Live
```

#167 may share implementation planning with #164 after #163, but it must be merged before #168 because project onboarding must know whether to link/reuse/audit a data source rather than inventing duplicate database behavior.

## 4. Per-issue engineering protocol

Every development issue #163–#168 follows the same lifecycle.

### 4.1 Start from exact current main

At the beginning of each tranche:

1. fetch/prune;
2. verify `origin/main`;
3. verify the prior dependency issue is merged and its post-merge CI is green;
4. verify working tree is clean;
5. read this build plan, the current authoritative handoff and the issue itself;
6. create a dedicated branch/worktree only then.

Never build two dependent tranches concurrently.

### 4.2 Freeze the acceptance contract before source edits

Before editing implementation:

- identify owned source surfaces;
- identify database migrations required;
- identify installer/plugin/hook surfaces;
- identify unit/integration/live regressions;
- record explicit non-goals;
- run/inspect current baseline tests where they materially de-risk the change.

### 4.3 AIGO engineering discipline

For each issue:

1. impact before change;
2. design before code;
3. smallest viable implementation;
4. deterministic mechanisms before model reasoning;
5. preserve explicit ownership/scope boundaries;
6. maintain backward compatibility unless the issue intentionally changes a contract;
7. fail closed on security/provenance ambiguity;
8. never weaken protected validation to simplify implementation.

### 4.4 Validation layers

Each tranche must distinguish:

1. implementation review;
2. automated unit/contract tests;
3. PostgreSQL integration tests where relevant;
4. installed/runtime smoke;
5. protected Fable validation;
6. exact-head CI;
7. post-merge main CI.

For #163–#168, physical Windows/live criteria are frozen in each issue but are executed together in #169 from the Visual Studio workflow. Do not start the final physical acceptance early and do not mark deferred live criteria PASS during implementation.

### 4.5 Commit discipline

Each tranche should normally end with:

- implementation commit(s);
- tests in the same PR;
- issue-specific docs;
- handoff update containing exact candidate SHA/evidence;
- protected validation;
- PR;
- exact-head CI;
- merge;
- post-merge CI;
- explicit carry-forward of its deferred physical criteria into #169;
- issue close only after the implementation evidence chain is durable.

The issue close means the build tranche is complete; it does not claim the later #169 physical acceptance has already passed.

Do not mix the next issue into the current PR.

## 5. Issue #163 — Credential Broker

Title: **Credential Broker: current-user reusable secrets and prompt ingress protection**

### 5.1 Goal

Evolve the existing project-scoped local secret primitive into a current-user credential-resource system that can be explicitly linked to more than one project without re-entering the value.

### 5.2 Existing reusable implementation

Reuse rather than replace:

- `SecretStore` Windows Credential Locker enforcement;
- `LocalSecretManager` rollback behavior;
- bounded child-process environment injection;
- exact-value output redaction;
- Git-excluded local materialization;
- tracked-file refusal;
- local cleanup;
- current secret CLI patterns.

### 5.3 New design

Introduce a non-secret current-user credential catalog.

Suggested conceptual entities:

```text
credential_resources
credential_fields
project_credential_bindings
credential_capture_attempts
```

A resource identity is based on normalized service identity + account label, for example:

```text
website | https://www.example.gr | main
postgres | db.example.gr:5432/sales | readonly
github | github.com | work
```

Values remain outside PostgreSQL.

### 5.4 Prompt ingress

A deterministic `UserPromptSubmit` guard detects high-confidence credential material before normal model processing when the host contract supports blocking.

It must:

- never echo the secret;
- never persist the raw prompt in Vres;
- produce a local pending capture;
- tell the user a credential was blocked;
- require explicit confirm/discard;
- allow uncertain text to proceed or request safer clarification according to the final false-positive policy.

This path must be physically tested against actual Claude Code transcript/debug behavior before making claims stronger than the host proves.

### 5.5 Cross-project reuse

A saved credential can be offered in another project only after matching a non-secret service identity.

The project receives a binding, not a copy.

Project unlink and resource delete are separate operations.

### 5.6 Validation

The full acceptance contract is in issue #163. Its Windows-user isolation and prompt/transcript host checks are mandatory live criteria in #169 before production.

## 6. Issue #164 — Secret-safe onboarding

Title: **Secret-safe onboarding: path exclusion, pre-model sanitization and fail-closed ingestion**

### 6.1 Goal

Guarantee that historical project/global material cannot cause raw credentials to enter durable Vres state or model context during onboarding.

### 6.2 Path-level policy

Add deterministic exclusion before extraction for credential-bearing paths, including:

- `.env`, `.env.*`;
- `secrets.toml`;
- credential/auth/private-key files;
- Vres local-secret material.

Maintain generated/dependency exclusions.

### 6.3 Content-level policy

Useful mixed documents are sanitized before:

- chunks;
- embeddings;
- review;
- model analysis;
- durable knowledge.

Expand environment-style key detection.

If Vres cannot safely sanitize a suspicious source, the source becomes `sensitive_review_required`; its raw content does not proceed.

### 6.4 Credential candidate extraction

If onboarding discovers a reusable credential, any secure capture must delegate to #163's Credential Broker. There is one secret-storage architecture.

### 6.5 Golden fixture

Use a sanitized copy of `wizzard_9`.

Required negative proof:

- `.streamlit/secrets.toml` never becomes knowledge;
- embedded synthetic credentials in handover text do not survive in persisted/model-visible forms;
- application code is not executed during inventory.

## 7. Issue #165 — Chairman Opus/medium policy

Title: **Chairman model policy: configurable Opus/medium default with host-observed monitoring**

### 7.1 Goal

Make Chairman model/effort a governed control-plane policy with an initial `opus/medium` value.

### 7.2 Separation from worker routing

Do not collapse Chairman into normal build/analyze model policies.

Chairman is the control plane. Worker routing remains separate.

### 7.3 Materialization

The installed agent definition must be deterministically derived from:

- immutable release template;
- active Chairman policy.

Record enough metadata/hash information to prove what was installed.

### 7.4 Monitoring

Collect only evidence the host/runtime actually supports.

Do not fabricate a universal quality score.

No automatic model-policy mutation.

### 7.5 #146 reuse

Reuse #146's exact physical generation evidence machinery. Do not reopen #146 or reinterpret one pair as model-policy authority.

## 8. Issue #166 — Global Claude adoption

Title: **Global Claude adoption: snapshot, quarantine, Chairman KEEP/DROP migration and rollback**

### 8.1 Goal

Turn an established current-user Claude environment into a clean Vres-governed environment without wiping vendor state and without silently inheriting legacy authority.

### 8.2 Installer boundary

The installer remains deterministic.

It performs:

```text
inventory
→ snapshot
→ hash manifest
→ quarantine/neutralize active legacy governance
→ install Vres baseline
→ mark GLOBAL_ADOPTION_PENDING
```

It does not perform semantic migration.

### 8.3 Snapshot scope

Use a strict allowlist of governance/config surfaces. Do not bulk-copy/delete all unknown Claude runtime state and then call it ownership.

Never destroy native vendor authentication/session data.

### 8.4 Legacy execution quarantine

Legacy hooks/control-plane config must not remain capable of governing the first adoption session.

This requirement is critical when testing against PRISM, because PRISM intentionally installs many hooks and orchestration surfaces.

### 8.5 First-start migration

Chairman owns the user interaction.

Semantic worker output returns to Chairman; the user never needs to know a migration subagent name.

Legacy content remains untrusted data until explicitly promoted.

### 8.6 PRISM fixture

Planned live fixture:

- repository: `vosser24/prism_5`;
- current known main at plan creation: `44329fdbfbb5a61d409ad202c57237805d56fe9d`;
- PRISM docs describe global `~/.claude/hooks`, `skills`, `agents`, `tools`, `commands`, merged settings and preserved state.

At live-test time, re-fetch the actual chosen PRISM commit. Do not assume the planning-time SHA is still current.

PRISM is a fixture, not a Vres dependency.

## 9. Issue #167 — Data Source Registry + semantic DB catalog

Title: **Current-user Data Source Registry and read-only semantic database catalog**

### 9.1 Goal

Register a database once per current Windows user, securely bind its credential handle, build a read-only structural/semantic catalog, and reuse that catalog from explicitly authorized projects.

### 9.2 Data-source identity

Suggested identity fields:

- engine;
- host;
- port;
- database/service;
- credential resource;
- access contract.

Credentials remain in the vault.

### 9.3 Structural scan

PostgreSQL is the first engine unless separately expanded.

Acquire structure deterministically from safe catalog views.

Initial catalog should cover:

- schemas;
- tables;
- columns;
- types;
- defaults;
- PK/FK/unique/check;
- indexes;
- views/materialized views;
- sequences/types;
- functions/procedures/triggers where readable;
- comments;
- dependency edges;
- safe ownership/size/estimate metadata.

### 9.4 Semantic pass

A governed data/PostgreSQL worker interprets the bounded graph.

Persist evidence class with each semantic claim.

Do not promote inference to canonical truth merely because the model is confident.

### 9.5 Code ↔ DB map

Where statically discoverable, map project read/write/query/migration surfaces to database objects.

### 9.6 Reuse and drift

Normal project starts use a cheap fingerprint.

Unchanged database → reuse current catalog.

Changed database → bounded incremental refresh.

Large/unknown drift → reviewed/full audit.

## 10. Issue #168 — Project adoption + canonical scaffold

Title: **Project adoption and canonical Claude scaffold with credential/data-source linking**

### 10.1 Goal

Make `start vres` a real project-adoption entry point.

### 10.2 Project state

Classify:

- fresh;
- legacy;
- adoption pending;
- active;
- interrupted/rollback required.

### 10.3 Claude-native scaffold

Core project directories may include:

```text
.claude/
  rules/
  skills/
  agents/
  agent-memory/
```

Project `CLAUDE.md` remains concise always-on guidance.

Other Claude-native files are created only when actually required.

Do not invent a `.claude/lessons` convention.

### 10.4 Semantic placement

Map learned material by meaning:

```text
always-on convention → CLAUDE.md / rules
workflow             → skill + Vres procedure
specialist           → agent after governed capability need
agent-specific memory→ agent-memory
facts/decisions      → Vres knowledge/decision
user preference      → Vres preference
```

### 10.5 Legacy adoption

Existing material is snapshotted/read safely, classified and shown as grouped numbered KEEP/DROP items.

Nothing is silently overwritten simply because Vres has a preferred layout.

### 10.6 Credential/data-source integration

Project adoption must be able to:

- recognize a previously saved current-user credential;
- request explicit binding;
- recognize a previously cataloged data source;
- request explicit binding;
- offer a new read-only database audit when no catalog exists;
- refresh only when drift is detected.

### 10.7 Golden project fixture

Use the user's actual legacy project in #169 after the synthetic/sanitized development fixture has already proven the contract.

## 11. Issue #169 — Integrated Windows live acceptance

Title: **Integrated Windows live acceptance from Visual Studio: PRISM global adoption + real legacy project**

This is the first whole-system proof after all build tranches are merged.

### 11.1 Operator workflow

The user requested that the acceptance be run from Visual Studio / its integrated terminal/development workflow rather than the previous PowerShell-only guided style.

PowerShell may still be invoked by scripts/terminals where the product itself requires it; the acceptance is not a claim that PowerShell ceases to exist. The important change is that the real user workflow starts and operates from Visual Studio rather than a synthetic sequence of isolated PowerShell test consoles.

### 11.2 Dirty-global setup

Before Vres:

1. use a disposable/snapshotted Windows user;
2. install and verify PRISM from its supported Windows path;
3. create realistic PRISM global state;
4. optionally bootstrap a small PRISM project to establish realistic project/global history;
5. record exact PRISM/Claude/environment identity.

### 11.3 Fresh Vres install

Fresh Vres must adopt the established Claude environment rather than requiring PRISM uninstall.

Acceptance includes:

- snapshot;
- quarantine;
- native auth preservation;
- Chairman Opus/medium;
- grouped numbered KEEP/DROP;
- preserved useful capabilities only under Vres governance;
- project-specific relocation;
- protected validation;
- restart;
- rollback;
- idempotence.

### 11.4 Actual legacy project

Use the actual user-selected legacy project.

If real credentials exist, rotate/use disposable test credentials where needed for repeatable evidence; never commit them.

If a database exists, exercise real linking/catalog behavior with a bounded read-only account.

### 11.5 Fault acceptance

Exercise interrupted global adoption, project adoption and catalog refresh.

Mixed half-active states are failures.

## 12. Issue #170 — Production Readiness / Go-Live

Production readiness remains separate from repository finalization and from #169 live acceptance.

Required areas:

- release artifact and manifest;
- target Windows installation;
- PostgreSQL least privilege;
- current-user credential/security review;
- backup/restore;
- update/rollback/interrupted recovery;
- adoption recovery;
- monitoring/health/escalation;
- enabled/held inventory;
- staged low-risk pilot;
- final launch decision.

## 13. Regression strategy

Do not rerun the complete historical matrix after every issue.

Use the current surface-triggered policy.

Expected families:

| Issue | Minimum likely impacted acceptance |
|---|---|
| #163 | secret/local-secret + UserPromptSubmit; F-01/F-02 if global hook/settings changes; F-15 |
| #164 | LV-23/24/25; onboarding scope; redaction; F-15 |
| #165 | F-04; model routing/experiment; F-15 |
| #166 | F-00/F-01/F-02/F-05/F-15 + new GA suite |
| #167 | database/security/retrieval + F-06/F-15 |
| #168 | PA-02; LV-22/23/24/25; F-06/F-15 + new project-adoption suite |
| #169 | integrated whole-system surface selection |
| #170 | production-specific operational gate |

F-05/F-06/F-15 evidence from #141 remains reusable until a changed surface invalidates it.

## 14. Documentation updates per tranche

Every issue must update the docs owned by its contract.

Likely cumulative docs:

- `README.md`;
- `docs/KNOWN-LIMITATIONS.md`;
- `docs/architecture/BOUNDARIES.md`;
- `docs/architecture/ONBOARDING.md`;
- `docs/INSTALL-WINDOWS.md`;
- `docs/FINAL-VERIFICATION.md`;
- `docs/LIVE-VERIFICATION.md`;
- `docs/RELEASE-VALIDATION.md`;
- Chairman/validator/onboarding/model-routing plugin contracts;
- a dedicated adoption architecture document;
- a dedicated credential architecture document;
- a dedicated data-source/catalog architecture document.

Historical acceptance documents remain historical. Do not rewrite prior evidence to make it look as if the new architecture always existed.

## 15. Fresh-session start rule

The next session must begin with issue #163 only.

Do not start #164–#170 early.

Starter instruction:

> Resume Vres-OS from `docs/PREPRODUCTION-BUILD-HANDOFF-2026-09-25.md` and `docs/PREPRODUCTION-ADOPTION-BUILD-PLAN-2026-09-25.md`. Fetch and verify current origin/main. Issues #141, #146 and #159 remain complete. The pre-production work ledger is #163–#170. Start only #163 Credential Broker. Read the complete issue and current secret/local-secret/hook contracts before creating the branch/worktree. Build the smallest secure current-user credential-resource layer, validate it with the issue's automated and protected contracts, commit/PR/merge it, verify post-merge main CI, update the handoff, and stop before #164 unless I explicitly tell you to continue.

## 16. Planning closeout

This planning document authorizes the implementation program but is not implementation evidence.

At plan creation:

- no product source code has been changed;
- #163–#170 are the open execution ledger;
- the first implementation target is #163;
- the integrated real-world proof is #169;
- productionization is #170.
