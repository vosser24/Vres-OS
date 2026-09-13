---
name: engineering-execution
description: Use for software design/build/debug/refactor work. Preserves AIGO's measured engineering discipline behind the Vres Chairman/CTO without exposing slash commands.
---

# Engineering execution

The current repository is authority. A plan is a hypothesis until code/tests prove it.

## Stage 0 — risk/staffing

Do not classify complexity for ceremony. Identify the actual capabilities/risk surfaces needed. State internally which stages are required and why; skip only with evidence.

## Plan/design

1. Convert the request into verifiable acceptance outcomes.
2. Read existing implementation/tests/docs before architecture proposals.
3. Compute impact from fresh evidence: imports/references, affected tests, git co-change, schema/API boundaries, plus Vres semantic relationships. Do not persist a fake complete code dependency graph.
4. For non-trivial work, write a concise `docs/plans/<slug>-plan.md` covering scope, contracts, affected surfaces, validation commands, rollback, and unresolved material facts.
5. Build one end-to-end vertical slice that proves the architecture before broadening it.

## Build

- Minimum code that solves the goal; no speculative abstractions/configuration.
- Surgical changes: every changed line should trace to the request or a proven dependency.
- Match the repository's established patterns unless evidence justifies change.
- Prefer deterministic implementation over model calls when deterministic code can satisfy the contract.

## Validate

Dispatch the dedicated `validator` agent in a fresh context for material work. It must verify, not author/fix. Evidence taxonomy: verified / relayed / inferred / assumed.

A green unit test proves only the behavior it exercised. Validate wiring/reachability/integration when those are part of the claim. Compare actual change surface with planned/impact surface.

## Debug

Find root cause from evidence; do not patch symptoms. Add/retain the regression test that demonstrates the defect where practical.

## Security

Run focused security review when auth, secrets, permissions, external input, file handling, data access, dependency/supply chain, or network boundaries change. Do not add ceremonial security work to unrelated typo-level changes.

## Deliver

Completion means acceptance outcome met + material validation complete + task state checkpointed. Never make the user invoke `/impact`, `/build`, `/save`, or `/resume`; these concepts are internal machinery.
