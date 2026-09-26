---
name: engineering-architecture
description: Use for application architecture, new-app boundaries, existing-project architecture audits, dependency ownership, and adoption alignment planning. User interaction remains Chairman-led; never expose internal architecture commands.
---

# Engineering architecture governance

Authoritative policy:

- `docs/architecture/ENGINEERING-CONSTITUTION.md`
- `docs/architecture/ENGINEERING-PROFILES.md`

Engineering maxim:

**Local change. Predictable impact. Explicit dependencies. Shared truth. Isolated failures.**

## User interaction

The user states intent normally. Do not ask the user to run architecture, validation, dependency, MCP or Vres maintenance commands.

The only user-facing control phrases are `start vres` and native `clear`.

Use internal deterministic/MCP capabilities yourself and report outcomes in plain language.

## Every software change

Before implementation determine internally:

1. the owning module/domain/platform responsibility;
2. whether a matching implementation already exists;
3. whether the new behavior is local, reusable business/domain logic, or generic infrastructure;
4. the permitted dependency direction;
5. public API impact;
6. dependency-map impact;
7. failure-isolation impact.

Do not broaden an ordinary feature request into unrelated architecture cleanup. Fix only the boundary required for safe implementation and surface unrelated debt separately.

## New applications

Select the smallest appropriate architecture profile.

Do not manufacture empty enterprise-style layers. Establish explicit boundaries as soon as the responsibilities exist.

Substantive modules get short local `CLAUDE.md` files containing only:

- purpose/ownership;
- routes/APIs owned;
- allowed dependencies;
- prohibited dependencies;
- source-of-truth/business assumptions;
- required tests.

Do not duplicate the global constitution in local files.

## Existing-project adoption

An existing codebase always requires a deterministic architecture audit before an adoption alignment plan.

Use the internal `architecture_audit` tool. Do not execute application code to obtain the audit.

Chairman then creates one incremental alignment plan that covers every material finding through either:

- a bounded reversible migration tranche; or
- an explicit reviewed defer/exception.

Use `architecture_plan_check` to mechanically verify plan shape and coverage. Preserve its exact `audit_digest` and `plan_digest`.

A mechanical PASS is **not** authority to implement.

### Mandatory protected plan validation

Before any architecture-changing adoption work or activation:

1. freeze the exact plan together with its `audit_digest` and `plan_digest` as the review artifact/state;
2. call the normal Vres protected validation preparation flow;
3. delegate exactly to `vres-os:validator`;
4. require host-observed Fable/high evidence;
5. require PASS on the exact plan/audit state;
6. if the plan or audit changes afterward, invalidate the review and obtain a new protected PASS before activation.

If Fable/high is unavailable, overridden, stale, or cannot validate the exact plan, adoption-plan state is BLOCKED.

Never substitute Sonnet, Opus, Codex, another reviewer, or a caller-supplied boolean.

Fable validates the plan. Chairman remains user-facing. The user retains decision authority.

## Migration method

Existing applications use a strangler migration:

1. target one boundary;
2. introduce compatibility/public seam;
3. migrate one responsibility;
4. run functional + architecture checks;
5. preserve rollback;
6. regenerate evidence;
7. continue only after the tranche is accepted.

Never perform a giant repository reorganization merely to make folders look compliant.

## Plan contract

The plan must explicitly name the target architecture profile(s).

Each tranche must identify:

- stable key/title;
- findings addressed;
- dependencies;
- affected scope;
- target boundary;
- compatibility strategy;
- rollback/reversibility;
- acceptance criteria;
- explicit non-goals.

Every material finding is addressed or explicitly deferred/excepted with an owner and revisit trigger.

## Boundaries

This skill does not replace:

- #168's full fresh/legacy adoption state, KEEP/DROP activation or canonical scaffold wiring;
- #169's integrated Windows/Visual Studio acceptance;
- protected Vres validation/completion.

It is the architecture-governance foundation those flows must consume.
