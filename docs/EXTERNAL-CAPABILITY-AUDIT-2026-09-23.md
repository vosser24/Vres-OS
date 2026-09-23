# Phase B — External Capability Discovery & Audit

Status: **IN PROGRESS**

GitHub issue: #145

Branch baseline: `main@c35fa192fc44a8ed726b28dd8ea6c45cd9d15090`

Date opened: 2026-09-23

## 1. Purpose

This document is the evidence record for Phase B of the post-finalization roadmap.

Phase B is an audit, not an adoption phase.

The goal is to inventory every capability visible to the installed Claude/Vres environment and classify each **external** MCP server, plugin, skill/command, and agent/subagent as exactly one of:

- `USE`
- `USE WITH GUARDS`
- `DEVELOPMENT REQUIRED`
- `DECLINE`

Installation or visibility is not authority to use a capability.

No capability is installed, removed, enabled, disabled, promoted, or integrated merely because it appears in this audit.

Phase C must not start until this audit is complete or the user explicitly reprioritizes.

## 2. Governing Vres constraints

Every classification must preserve these existing boundaries:

1. Vres owns the durable task and current task/session binding.
2. Vres owns routing and model/effort selection for governed work.
3. Protected validation and task completion remain Vres-owned authority.
4. External tools/agents cannot manufacture Vres worker, validation, completion, or provenance evidence.
5. Write-capable execution remains bounded by explicit scope and acceptance evidence.
6. Secrets stay in native/local authentication surfaces and are never copied into durable prompts/evidence.
7. Company/global publication remains separately approved.
8. Capability discovery does not imply capability proof or company-wide adoption.

Existing project-agent registration already enforces an important Phase-B rule: a project agent definition must live under `.claude/agents/`, must cite known owned capability keys, and **must not set model or effort in frontmatter**, because Vres routing owns the execution tier.

## 3. Classification definitions

### USE

The capability is useful, its authority fits existing Vres boundaries, and ordinary Vres controls are sufficient. It does not introduce a competing model/routing/completion authority or an unbounded side-effect surface.

### USE WITH GUARDS

The capability is useful but needs explicit runtime or operating guards before Vres relies on it. Typical reasons include external model decisions, write/irreversible actions, credentials, lifecycle hooks, automatic invocation, or overlap with Vres planning/routing.

### DEVELOPMENT REQUIRED

The capability is potentially valuable but cannot yet be adopted safely because Vres lacks a required adapter, evidence contract, permission boundary, lifecycle integration, deterministic verification, or target-platform validation.

### DECLINE

The capability is redundant, conflicts with Vres authority, requires unsafe/unbounded execution, duplicates an existing governed capability without material benefit, or cannot meet the evidence/security bar.

## 4. Vres-owned baseline — not external audit subjects

These components are the internal baseline against which external overlap/conflict is judged.

### MCP

Vres packages one project/plugin MCP server:

- `vres` — launched through the Vres plugin's PowerShell MCP launcher.

### Skills

Current packaged Vres skills:

- assumption-firewall
- company-refresh
- engineering-execution
- knowledge-capture
- local-secrets
- model-routing
- onboarding
- procedural-learning
- start-vres

### Governed agents

Current packaged Vres agents:

- chairman
- challenger
- commercial-director
- cto
- data-director
- digital-director
- finance-director
- knowledge-steward
- legal-risk-director
- marketing-director
- opus-expert
- people-director
- routing-arbiter
- sales-director
- sonnet-expert
- supply-chain-director
- validator

These are Vres-owned surfaces. They are **not** classified as external capabilities in the matrix below.

## 5. Claude Code extension-layer facts relevant to the audit

Current Claude Code documentation distinguishes these extension surfaces:

- Skills: reusable knowledge/workflows; descriptions may be visible each turn and content loads when invoked.
- Subagents: isolated execution contexts that return results to the caller.
- MCP: external tools/data; connected server tool names are visible and full schemas load on demand.
- Hooks: lifecycle-triggered external actions.
- Plugins: packaging/distribution for skills, agents, hooks, MCP servers and related components.

Claude Code documents that:

- MCP servers can exist at multiple scopes and name precedence is local > project > user.
- Skills and subagents can exist at user/project/plugin scopes with their own precedence rules.
- `/mcp` is the supported interactive surface for MCP connection inspection.
- `/agents` manages agent configuration.
- `/skills` lists available skills.
- `/plugin` manages plugins.
- Installed plugins are cached under `~/.claude/plugins`.
- On Windows, `~/.claude` resolves to `%USERPROFILE%\.claude` unless `CLAUDE_CONFIG_DIR` overrides it.

Sources checked 2026-09-23:

- https://code.claude.com/docs/en/features-overview
- https://code.claude.com/docs/en/claude-directory
- https://code.claude.com/docs/en/commands

## 6. Named roadmap candidates — public-source pre-audit

The entries below are **named candidates from the roadmap**, not proof that they are installed on the target machine.

### 6.1 JEV Browser

Source audited:

- https://github.com/Ying-Kai-Liao/jev-browser

Public source facts:

- MIT-licensed, unofficial project, not affiliated with TypeSafe.
- Exposes an MCP browser surface backed by Playwright.
- Uses the caller LLM to state goals/text candidates while a TypeSafe System One / Jev request returns probabilistic decisions for element/action/value/done/error/irreversible state.
- Requires `TYPESAFE_API_KEY` for the external API.
- Exposes browser open/do/check/choose/snapshot/act/screenshot/close tools.
- `browser_do` can return `needs_confirmation` before actions it considers irreversible and accepts `allow_irreversible` when explicitly re-called.
- The repository reports its own benchmark results; those results are project claims and are not treated as Vres acceptance evidence.

**Provisional roadmap classification: `USE WITH GUARDS`.**

Reason:

The capability can materially improve browser control and reduce page-state traffic to the caller, but an external model participates in action selection and Playwright performs real browser effects. Vres cannot treat Jev as a governed Vres agent or let it become model/routing authority.

Guards to verify before any Phase-C adoption:

- Vres/Chairman owns the task and step objective.
- Jev is an execution aid, not a governed Vres agent.
- No external model result can satisfy protected validation/completion.
- Irreversible browser actions require explicit user/Vres approval; never auto-set `allow_irreversible=true`.
- Credentials remain outside task prompts/evidence and are supplied through the native MCP/server environment only.
- Browser write/action scope and postconditions must be explicit.
- Screenshots/journey evidence must remain attributable to the Vres task.
- Model pinning inside the external capability must not alter Vres model/effort routing.

Phase B does not implement these guards; it only records them.

### 6.2 Superpowers

Sources audited:

- https://github.com/obra/superpowers
- https://claude.com/plugins/superpowers

Public source facts:

- MIT-licensed external development-methodology plugin.
- Available through Claude Code's official plugin marketplace.
- Provides skills for brainstorming, plans, TDD, debugging, worktrees, code review, subagent-driven development and related workflows.
- Its documented workflow automatically checks for relevant skills and describes several workflows as mandatory.
- It can launch subagent-driven development and create/manage development worktrees.
- It includes a session-start bootstrap in supported harnesses.
- Optional visual-companion telemetry can be disabled with `SUPERPOWERS_DISABLE_TELEMETRY` and related Claude traffic-disable variables.

**Provisional roadmap classification: `USE WITH GUARDS` as optional methodology only.**

This is deliberately narrower than runtime adoption.

The handoff already states that Superpowers must never become a Vres runtime dependency. Its auto-triggering methodology overlaps directly with Vres planning, worker selection, worktree, review and completion governance.

If present/used later, required guards include:

- no replacement of Vres routing/model/effort authority;
- no automatic subagent/worktree workflow that bypasses Vres work-unit governance;
- no independent completion claim replacing Vres validation/completion;
- no runtime dependency from Vres to Superpowers;
- invocation limited to methodology/help where compatible;
- disable optional telemetry if required by the user's privacy/network policy.

Phase E, not Phase B, decides whether/how to use it.

## 7. Physical installed-environment inventory — PENDING

The repo/public audit cannot prove what is installed in the user's Claude Code environment.

A fresh target-Windows Claude session must produce a **read-only, sanitized inventory**.

Required categories:

1. MCP servers/connectors visible to the session.
2. Installed plugins and scope.
3. Available custom/plugin skills and commands.
4. Available custom/plugin agents/subagents.
5. Relevant user/project configuration sources that contribute those items.

Do not capture:

- API keys;
- OAuth tokens;
- passwords;
- full `~/.claude.json` contents;
- plugin secret files;
- MCP environment variable values;
- session transcripts.

For every discovered external item, record only bounded metadata:

| Field | Meaning |
|---|---|
| identity | capability/server/plugin/skill/agent name |
| type | MCP / plugin / skill / agent |
| source | package/repo/marketplace/config origin when known |
| scope | managed/user/project/local/plugin |
| installed/visible version | version if safely observable |
| model/effort behavior | whether it pins/chooses a model or effort |
| actions | read-only / project-write / external-side-effect / irreversible |
| auth | none / native OAuth / environment secret / other, never the value |
| lifecycle | hooks/session-start/auto-trigger behavior |
| context cost | always-loaded / description-only / on-demand / isolated |
| Vres overlap | routing, task, worktree, validation, completion, knowledge, browser, etc. |
| evidence | local observation + public source |
| classification | one of the four Phase-B classes |
| guards/gaps | exact conditions for safe use |

## 8. Physical inventory procedure

Run this only after pulling the Phase-B branch into a clean Windows worktree.

In a fresh Claude Code session, start Vres and instruct Claude to perform **read-only discovery only**.

Claude should inspect the supported interactive surfaces:

- `/mcp`
- `/plugin`
- `/skills`
- `/agents`

and the safe configuration locations needed to establish source/scope, including project/user skills and agents.

The inventory must report names/scopes only and must redact/omit secret values.

It must not:

- install/uninstall plugins;
- add/remove MCP servers;
- enable/disable plugins;
- edit settings;
- modify agent/skill files;
- authenticate a new external service;
- run an external side-effecting tool merely to prove it exists.

The physical output is then brought back to the Phase-B audit and each external item is researched/classified.

## 9. Audit matrix

| Capability | Installed? | Type | Evidence status | Classification | Notes |
|---|---:|---|---|---|---|
| Vres MCP/skills/agents | Yes | internal baseline | repo + installed Vres runtime | N/A — Vres owned | comparison baseline |
| JEV Browser | Unknown pending physical inventory | MCP/browser | public source audited | provisional USE WITH GUARDS | Phase C candidate; do not implement in Phase B |
| Superpowers | Unknown pending physical inventory | plugin/methodology | public source audited | provisional USE WITH GUARDS | Phase E candidate; methodology only, never runtime dependency |
| Other installed MCPs | Pending | MCP | pending physical inventory | pending | classify individually |
| Other installed plugins | Pending | plugin | pending physical inventory | pending | classify individually |
| Other installed skills | Pending | skill | pending physical inventory | pending | classify individually |
| Other installed agents | Pending | agent | pending physical inventory | pending | classify individually |

## 10. Phase-B completion gate

Issue #145 may close only when:

- the physical installed inventory is complete;
- every external installed item has public/source provenance where discoverable;
- every external installed item has exactly one classification;
- guards/development gaps are explicit;
- model/effort and task/validation/completion conflicts have been reviewed;
- no secret was copied into the audit;
- no adoption/configuration mutation was performed merely for discovery;
- JEV Browser and Superpowers remain at their roadmap positions;
- the final matrix is committed and reviewed.

Until then, Phase C is held.
