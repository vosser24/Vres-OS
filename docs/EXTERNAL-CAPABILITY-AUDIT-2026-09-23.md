# Phase B — External Capability Discovery & Audit

Status: **CLASSIFICATION CORRECTED — FRESH INDEPENDENT VALIDATION REQUIRED**

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

## 7. Physical installed-environment inventory — COMPLETE

A read-only target-Windows inventory was completed on 2026-09-23 in the clean Phase-B worktree under Vres task `TASK-20260923-61212f431e`, using Claude Code 2.1.280.

The inventory reported `PHASE_B_PHYSICAL_INVENTORY = PASS` and made no configuration/authentication/install/use mutation.

Observed external surface:

- 7 account/session MCP/connectors;
- 0 installed external plugins;
- 15 account-synced skills;
- 17 host-bundled skills;
- 6 host-built-in agents/subagents.

It also confirmed that JEV Browser and Superpowers are **not installed**.

Inventory limitations were retained rather than hidden:

- interactive `/mcp`, `/plugin`, `/skills`, and `/agents` UIs were not physically opened from the model turn;
- exact versions are unavailable for most host/account-provided items;
- provenance of some host-bundled skills is host-internal rather than file-backed;
- unauthenticated connectors expose names/auth surfaces but not their full post-auth tool schema.

The inventory nevertheless covered every capability visibly registered to the session or discoverable in the checked managed/user/project/local/plugin scopes without reading secret values.

The following collection rules remain authoritative.

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

## 9. Final external-capability classification matrix

The physical inventory found **45 installed/visible external capability items**. Every item has exactly one Phase-B classification.

Classification totals:

- `USE`: 3
- `USE WITH GUARDS`: 25
- `DEVELOPMENT REQUIRED`: 8
- `DECLINE`: 9

JEV Browser and Superpowers are excluded from those totals because the target Windows inventory confirmed that neither is installed.

### 9.1 Account/session MCP and connectors

| Capability | Classification | Phase-B rationale / mandatory guard |
|---|---|---|
| claude-in-chrome | USE WITH GUARDS | Useful browser execution surface, but can navigate/click/type/upload and act in authenticated browser sessions. Use only for an explicit Vres task/step; user approval for irreversible/external writes; browser evidence is not Vres validation/completion evidence. |
| claude.ai Claude Docs | USE WITH GUARDS | Can create/update/delete external docs. Vres owns task/provenance; external document mutation needs explicit scope and post-action verification. |
| claude.ai Canva | USE WITH GUARDS | Visible but unauthenticated at inventory time. Interactive connector can create/edit designs after auth. Authentication/adoption is user-authorized and external writes remain scoped. |
| claude.ai Gmail | USE WITH GUARDS | Visible but unauthenticated at inventory time. Email read/write capability after auth includes sending/replying/forwarding, so any such action is an external side effect. Require explicit task intent and native connector approval; never persist credentials. |
| claude.ai Google Calendar | USE WITH GUARDS | Visible but unauthenticated at inventory time. After auth it can create/update/delete/respond to events. External mutation requires explicit Vres task intent and postcondition/evidence. |
| claude.ai Google Drive | USE WITH GUARDS | Visible but unauthenticated at inventory time. After auth it can search/read and also upload/share/move/trash. External mutation requires explicit scope/approval and evidence; connector content is not automatically durable Vres knowledge. |
| claude.ai Notion | USE WITH GUARDS | Visible but unauthenticated at inventory time. After auth it is a remote workspace connector with potential read/write effects. Require explicit Vres task intent, least-privilege auth, and external-write verification. |

Public-source basis checked 2026-09-23:

- Anthropic connector documentation describes remote connectors as tools that can retrieve data **and take actions**, inheriting the connected user's service permissions.
- Anthropic's Google Workspace connector documentation explicitly documents Gmail send/reply/forward, Calendar create/update/delete, and Drive share/move/trash/upload actions with approval controls.
- Anthropic's Claude-in-Chrome documentation states that it can read, click, type, navigate and fill forms and explicitly warns that browser automation remains risky.
- Anthropic's interactive-connector documentation identifies Canva as an interactive create/edit design surface.

### 9.2 Account-synced skills

| Skill | Classification | Phase-B rationale / mandatory guard |
|---|---|---|
| pdf | USE WITH GUARDS | Official/source-available document skill. Local artifact read/write is acceptable only inside the routed task's declared artifact/file scope; generated output still needs task acceptance evidence. |
| pptx | USE WITH GUARDS | Same document-artifact guard; local scripts/subprocesses do not gain task/validation authority. |
| xlsx | USE WITH GUARDS | Same; spreadsheet writes must remain within declared file scope and be verified mechanically where possible. |
| docx | USE WITH GUARDS | Same; document generation/editing is artifact work, not completion evidence. |
| docs | USE WITH GUARDS | Depends on Claude Docs external document surface; applies the connector's external-write guards. |
| import-memory | DECLINE | Competes directly with Vres durable continuity/knowledge authority and can create a second ungoverned memory truth source. |
| skill-creator | DEVELOPMENT REQUIRED | Potentially valuable for authoring skills, but Vres currently has no governed external-skill acquisition/registration/proof contract comparable to project-agent governance. Generated skills are candidates only until such a path exists. |
| morning | DEVELOPMENT REQUIRED | Scheduling/recurring execution is explicitly outside current Vres runtime governance. Needs a separately authorized scheduler contract, provenance, retry/failure semantics and target-Windows validation. |
| memory | DECLINE | Its purpose is an additional memory workflow/source outside the Vres durable task/knowledge authority. Adopting it in governed sessions would risk a second, non-Vres memory truth source, so Vres declines it rather than asserting a stronger mechanism than the inventory proved. |
| code-reviewer | USE WITH GUARDS | Advisory review is useful, but the installed skill text also mentions automated fixes. Review-only use can provide advisory evidence; any fix/edit mode must be treated as an ordinary scoped implementation write. It can never substitute for protected Vres validation, set PASS, or satisfy completion authority. |
| prism | DECLINE | Inventory reports default/automatic loading on substantive messages. That competes with Vres routing/planning authority and adds hidden context behavior; do not adopt in governed sessions. |
| senior-fullstack | DEVELOPMENT REQUIRED | Useful expertise candidate, but as a synced skill it can scaffold/write broadly outside Vres governed agent/work-unit provenance. Adoption requires conversion/integration into a governed capability/agent contract rather than direct autonomous use. |
| senior-backend | DEVELOPMENT REQUIRED | Same: useful expertise, but current skill form can scaffold/migrate/test and write broadly without Vres worker provenance/write-scope ownership. |
| vercel-react-best-practices | USE WITH GUARDS | Public Vercel reference guidance is useful inside an already authorized React/Next.js work unit. It does not get routing, write-scope, validation or completion authority. |
| dedeman-ms | USE WITH GUARDS | Narrow user-uploaded XLSX translation/build utility. Use only on explicitly declared spreadsheet artifacts, preserve source files, and verify outputs; no authority beyond the current Vres work unit. |

Public/source provenance checked where discoverable:

- `pdf`, `pptx`, `xlsx`, `docx`: Anthropic public `anthropics/skills` repository; Anthropic notes the production document skills are source-available and should be tested in the target environment before critical reliance.
- `vercel-react-best-practices`: public `vercel-labs/agent-skills`, MIT, Vercel-authored React/Next.js performance guidance.
- `senior-backend` and `senior-fullstack`: public Borghei Claude-Skills definitions describe scaffolding, database/API/architecture and quality-analysis behavior.
- `code-reviewer`: multiple public skills use this generic name; the installed account-backed copy's exact upstream was not provable from the inventory, so classification relies on the observed local manifest/description and read-only nature rather than falsely attributing it.
- `memory`, `import-memory`, `morning`, `prism`, and `dedeman-ms`: exact upstream provenance was not safely recoverable from the target inventory; that uncertainty is retained.

### 9.3 Host-bundled skills

Host-bundled skills are treated as Claude host capabilities, not Vres-owned capabilities. Where source/behavior was not independently inspectable, Phase B uses the conservative class rather than inferring authority from the name.

| Skill | Classification | Phase-B rationale / mandatory guard |
|---|---|---|
| update-config | DECLINE | Direct settings mutation can overwrite/undermine Vres-owned Claude configuration surfaces. Vres installation/update owns its fields and must preserve unrelated settings explicitly. |
| keybindings-help | USE | Informational help; no material Vres authority or side-effect conflict observed. |
| code-review | USE WITH GUARDS | Advisory review only; never protected validation or completion authority. If `--fix`/edit behavior is used, it becomes a normal scoped implementation write. |
| simplify | USE WITH GUARDS | May change code. Only inside a routed write-capable work unit with declared scope and acceptance evidence. |
| fewer-permission-prompts | DECLINE | Explicitly weakens/changes permission prompting and conflicts with Vres's conservative execution/safety posture. |
| loop | DEVELOPMENT REQUIRED | Repeated/background execution needs scheduler/condition/retry/provenance governance that Vres does not currently provide. |
| schedule | DEVELOPMENT REQUIRED | Same scheduling gap; do not treat host scheduling as Vres-governed execution until integrated. |
| claude-api | USE | Documentation/reference capability; no competing Vres execution authority identified. |
| workflow-authoring | DEVELOPMENT REQUIRED | Can create automation/workflow behavior that overlaps Vres orchestration/lifecycle. Needs a governed workflow-registration/execution boundary before adoption. |
| claude-in-chrome | USE WITH GUARDS | Same browser guard as the Chrome connector: explicit step intent, user approval for irreversible actions, and no validation/completion authority. |
| run | DEVELOPMENT REQUIRED | Inventory did not provide enough stable public/host semantics to prove its execution/side-effect boundary. Do not adopt until its exact contract is inspectable and tested. |
| init | DECLINE | Project initialization/CLAUDE contract writes overlap Vres's deliberately bounded project CLAUDE ownership. Vres start/installer remains the owner of that contract. |
| security-review | USE WITH GUARDS | Useful advisory security analysis, but protected Vres validation remains authoritative and must independently verify security acceptance criteria. |
| dataviz | USE WITH GUARDS | Artifact-generation helper; keep output inside declared artifact/file scope and validate the produced artifact. |
| artifact-design | USE WITH GUARDS | Artifact-generation methodology only; no routing/completion authority and outputs remain task-bound. |
| artifact-diagramming | USE WITH GUARDS | Same artifact/evidence boundary. |
| artifact-capabilities | USE WITH GUARDS | May guide artifact workflows; invoke only for an explicit artifact task and keep Vres task/provenance authority. |

### 9.4 Host-built-in agents/subagents

| Agent | Classification | Phase-B rationale / mandatory guard |
|---|---|---|
| claude | DECLINE | General host agent can execute outside Vres work-unit/model/provenance contracts. Do not use as a governed Vres worker. |
| claude-code-guide | USE | Read-only documentation/search helper observed with bounded read/web tools; informational output only. |
| Explore | USE WITH GUARDS | Read-only isolated exploration can assist discovery, but it is not a governed worker and cannot create worker/validation/completion evidence. |
| general-purpose | DECLINE | Broad tool access and no Vres execution-tier/provenance contract; competes directly with governed Sonnet/Opus worker surfaces. |
| Plan | USE WITH GUARDS | Read-only planning may be used as non-authoritative analysis only; Vres routing/orchestration remains the plan/staffing authority. |
| statusline-setup | DECLINE | Can edit status-line configuration that Vres already manages/preserves through its installer/status-line contract. |

### 9.5 External plugins

No external plugin is installed.

Observed plugin state:

- Vres `vres-os@skills-dir`: Vres-owned baseline, not an external audit item.
- Official marketplace catalog: present as a catalog only.
- Account marketplace ("My Uploads"): provenance channel for synced skills, not itself an installed plugin.
- Host-internal plugin usage keys (for example builtin agent/telemetry keys): not user-installed plugin packages and therefore not separate adoption candidates.

### 9.6 Named roadmap candidates not installed

| Candidate | Installed? | Classification | Roadmap handling |
|---|---:|---|---|
| JEV Browser | No | provisional USE WITH GUARDS | The authoritative post-finalization handoff explicitly labels this **Phase C — JEV Browser Control**. Phase B does not install or implement it. |
| Superpowers | No | provisional USE WITH GUARDS | The authoritative post-finalization handoff explicitly labels this **Phase E — Superpowers plugin**. It remains optional methodology only and never a Vres runtime dependency. |

### 9.7 Non-capability finding: stale Claude auto-mode trust metadata

The physical inventory found that user-level `settings.json` contains `autoMode.environment` metadata naming an older Vres worktree rather than the current Phase-B worktree.

Phase B **does not modify it**.

Why it matters:

- Anthropic's auto-mode design states that the environment list defines trusted repositories/infrastructure used by the safety classifier.
- Anthropic Claude Code issue #93405 documents the same user-global auto-mode failure mode: setup can retain an absolute trusted-repo path from the project where setup was originally run. Source: https://github.com/anthropics/claude-code/issues/93405

Phase-B disposition:

- retain as a configuration finding;
- do not weaken permissions;
- do not run auto-mode setup or mutate settings during this audit;
- create/fix only in a separately authorized follow-up if the user reaches that work.


## 10. Phase-B completion gate

Issue #145 may close only when:

- [x] the physical installed inventory is complete;
- [x] every external installed item has public/source provenance where discoverable, with unresolved provenance explicitly retained;
- [x] every external installed item has exactly one classification;
- [x] guards/development gaps are explicit;
- [x] model/effort and task/validation/completion conflicts have been reviewed;
- [x] no secret was copied into the audit;
- [x] no adoption/configuration mutation was performed merely for discovery;
- [x] JEV Browser and Superpowers remain at their roadmap positions;
- [ ] the final matrix has received independent protected validation.

Until the final independent validation passes, Phase C remains held.

Until then, Phase C is held.
