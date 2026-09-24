# Combined capability onboarding — JEV Browser + Superpowers

Status: **IMPLEMENTATION CANDIDATE — TARGET-WINDOWS VALIDATION PENDING**

GitHub issue: #148

Branch baseline: `main@843895e43b5cad5a31878c1cd391142f3bc0576d`

Date: 2026-09-24

## 1. User-authorized roadmap change

The user explicitly authorized treating JEV Browser Control and Superpowers as one **new-capabilities onboarding** phase.

This replaces the earlier sequencing that evaluated JEV before the E-11 capstone and Superpowers afterward.

The combined onboarding must complete before the E-11 browser-audit capstone starts.

The later parked items remain out of scope:

- seamless Vres-managed <=15% native context rollover / auto-compaction;
- model-generation calibration and governed adoption (#146).

## 2. Why one onboarding task, but two authority classes

Both candidates are external capabilities, but they do different things.

### JEV Browser — execution capability

JEV Browser gives Claude an MCP browser surface backed by Playwright and a separate TypeSafe System One / Jev decision model.

It can navigate and act on external sites, so its output is **execution evidence**, not Vres routing/validation/completion authority.

### Superpowers — methodology capability

Superpowers is a plugin containing skills and a SessionStart hook. Its documented methods include planning, TDD, debugging, worktrees, subagent-driven development, review, and branch finishing.

It may contribute compatible methodology, but it must never become a Vres runtime dependency or an alternative orchestration authority.

## 3. Frozen upstream evidence snapshot

These are evidence pins for this onboarding task, not permanent update pins.

### JEV Browser

- repository: https://github.com/Ying-Kai-Liao/jev-browser
- upstream main observed: `e35ab134f65033d29c528132d92bf06e8d6adcb5`
- package version: `0.1.1`
- license: MIT
- runtime: Node >=20
- MCP executable: `jev-browser-mcp`
- supported Vres onboarding server identity: `jev-browser` (the physical install must use this name)
- major dependencies: MCP SDK, Playwright, Zod
- auth: `TYPESAFE_API_KEY` for Jev/System One decisions
- browser profile option: `JEV_BROWSER_PROFILE`
- optional headed/log modes: `JEV_BROWSER_HEADED`, `JEV_BROWSER_LOG`

Observed MCP tools:

- browser_open
- browser_do
- browser_check
- browser_choose
- browser_snapshot
- browser_act
- browser_screenshot
- browser_close

The upstream MCP describes `browser_do(... allow_irreversible=true)` as the explicit bypass for its irreversible-action pause.

### Superpowers

- repository: https://github.com/obra/superpowers
- upstream main observed: `5bf4e78011075bcfc0dc295f0724994cd123ee71`
- plugin version: `6.4.1`
- license: MIT
- Claude plugin name: `superpowers`
- SessionStart hook matcher: `startup|clear|compact`

Its `using-superpowers` bootstrap says relevant skills should be invoked before any response/action, while also explicitly stating that user instructions take precedence.

Relevant workflow classes:

Advisory/methodology candidates:

- brainstorming
- systematic-debugging
- test-driven-development
- verification-before-completion
- writing-plans
- requesting-code-review
- receiving-code-review
- diagnosing-superpowers

Execution/orchestration/capability-authoring conflicts for active Vres tasks:

- using-superpowers
- subagent-driven-development
- executing-plans
- dispatching-parallel-agents
- using-git-worktrees
- finishing-a-development-branch
- writing-skills

The pinned Superpowers 6.4.1 snapshot contains 15 skills total. All 15 are explicitly
classified by this onboarding as either advisory-allowed or execution/capability-authoring
denied. Claude Code also supports unqualified aliases for plugin skills, so the guard
normalizes the pinned skills' bare aliases as well as namespaced invocation forms.

## 4. Claude Code host facts used by the design

Current Claude Code documentation states that:

- plugins package skills, agents, hooks, MCP servers and related extensions;
- hooks from different sources **merge**, so installing Superpowers does not replace the Vres SessionStart hook—it adds another hook;
- MCP/skills/plugins can exist at user/project/local scopes;
- project/user instructions and plugin features can coexist;
- skills load descriptions at session start and bodies on use;
- MCP tool names load with schemas deferred until use.

Sources re-check before physical onboarding:

- https://code.claude.com/docs/en/features-overview
- https://code.claude.com/docs/en/claude-directory
- https://code.claude.com/docs/en/plugins

## 5. Existing Vres primitives reused

No second capability registry is added.

The onboarding uses:

- current task/session binding;
- orchestration missing-capability discovery;
- governor-blocked capability-gap acquisition;
- project-scoped `CapabilityService.register_project`;
- specialist owner-role requirement;
- protected validation;
- `capability_mark_proven`, which already requires a completed task with passing validation.

Installation is **not** capability proof.

## 6. New guard boundary

Implementation module:

`src/vres_os/external_capability_preflight.py`

Hook wrapper:

`plugins/vres-os/bin/vres-external-capability-preflight.ps1`

The hook matcher runs for:

- `Skill`;
- `Agent`;
- all MCP tool calls.

The Python policy then applies JEV-specific controls only when the MCP server identity
contains the canonical `jev-browser` token (case-insensitive, with underscore/hyphen and
plugin-scoped forms normalized). This closes hook/policy matcher drift without claiming
that an arbitrarily renamed server such as `jev` can be attributed to JEV.

The physical onboarding must therefore install the MCP server as exactly `jev-browser`.
A differently named server is outside the accepted contract and must be re-onboarded.

It does not wrap or vendor either external project.

### 6.1 JEV policy

For JEV tools:

1. An active bound unfinished Vres task is required.
2. Secret-shaped tool input is denied before execution using both the shared Vres redaction
   detector and an external-browser sensitive-key/text detector covering password/pass/passcode,
   OTP/PIN, CVV/card-number, API-key/token/authorization/cookie/private-key families.
3. The explicit `browser_do(allow_irreversible=true)` bypass is denied in V1; the upstream Jev irreversible detector is treated as fallible, so acceptance uses a disposable fixture.
4. Direct `browser_act` is limited to:
   - scroll
   - back
   - hover
5. Direct click/type/select/upload/press/drag/right-click actions are denied in V1.
6. Read/snapshot/check/choose/screenshot/close and reversible `browser_do` remain available under the active task.

The initial acceptance run must use a disposable/non-production fixture.

### 6.2 Superpowers policy

While an unfinished Vres task is active:

Reviewed advisory Superpowers skills may load.

Execution/worktree/orchestration Superpowers skills are denied.

Unknown **namespaced** Superpowers skills are denied until reviewed. Every skill in the pinned
6.4.1 snapshot is also recognized by its bare alias. A future Superpowers version is not accepted
implicitly: its skill inventory must be re-audited and the guard updated before that upgrade is
considered onboarded.

Canonical Vres agents continue through the existing Vres agent preflight.

Only these host advisory agents remain allowed:

- Explore
- Plan
- claude-code-guide

Other host/plugin/custom agents—including general-purpose execution agents—are denied while the Vres task is active.

This prevents Superpowers or another plugin from silently becoming a Vres worker.

Outside an active Vres task, Vres does not claim authority over Superpowers workflows.


### 6.3 Claude Code command-hook timeout limitation

The enforcement wrapper exits with blocking status on internal errors and returns a structured
deny decision for policy violations.

However, current Claude Code host semantics explicitly state that a timed-out `PreToolUse`
**command** hook does not block the tool call; normal permission flow continues. The earlier
explicit 10-second timeout has therefore been removed so this hook uses Claude Code's normal
long command-hook budget for PreToolUse.

This reduces avoidable timeout risk but does not turn a command hook into a cryptographic or
absolute fail-closed policy mechanism. Physical acceptance must verify the hook returns promptly,
and the onboarding must not rely on this mechanism as the sole protection for production-risk
actions. JEV acceptance remains limited to a disposable fixture, and Superpowers remains
methodology-only.

## 7. Prompt-level authority rule

The Vres universal rules now state explicitly:

- external MCP/plugins/skills/agents are capabilities, not authority;
- Vres owns task/session, routing/model/effort, worker provenance, validation and completion;
- external model/browser decisions cannot satisfy Vres validation/completion;
- credentials do not belong in external tool arguments when native/local auth is available;
- Superpowers execution/worktree/subagent workflows cannot replace Vres orchestration.

This rule handles instruction precedence.

The PreToolUse hook remains the mechanical enforcement layer.

## 8. Secrets/authentication

No JEV API key, password, OAuth token, browser cookie or other secret is committed to this repository.

For physical onboarding:

- the TypeSafe API key must be supplied through a native/local environment mechanism outside chat/git;
- login credentials should prefer headed browser/profile login rather than `browser_do.values`;
- Superpowers optional telemetry is disabled for the acceptance run;
- usernames and other non-secret form values may be passed when necessary, but sensitive fields
  covered by the guard are not.

The exact secret provisioning step must be performed by the user outside model-visible text.

## 9. Deterministic test contract

The branch must prove:

### JEV

- denied without an active Vres task;
- read/reversible calls allowed with an active task;
- explicit irreversible-bypass request denied;
- sensitive keys/text such as password/passcode/OTP/CVV/card-number/TYPESAFE_API_KEY denied;
- plugin-scoped, case-varied and `jev-browser-mcp` server forms attributed consistently;
- a server renamed without the canonical `jev-browser` token is explicitly outside the contract;
- direct scroll/back/hover allowed;
- direct click/type/select/upload/etc. denied.

### Superpowers

- reviewed methodology skills allowed during an active task;
- execution/worktree/orchestration/capability-authoring skills denied;
- namespaced, marketplace-qualified, leading-slash and bare aliases of pinned 6.4.1 skills normalized;
- unknown namespaced Superpowers skills denied;
- future Superpowers versions require a fresh skill-inventory review before adoption;
- outside an active Vres task, Vres does not block Superpowers solely because it is installed.

### Agents

- canonical Vres agents continue to the existing agent preflight;
- Explore/Plan/claude-code-guide remain advisory-allowed;
- general-purpose/claude/custom/plugin execution agents are denied during an active Vres task.

### Packaging

- plugin hook references the installed wrapper;
- wrapper exits blocking on policy/runtime errors;
- no artificial 10-second timeout remains on the enforcement hook;
- the documented Claude Code command-hook timeout fail-open limitation is retained explicitly;
- no MCP registration count changes;
- no migration.

## 10. Target-Windows onboarding ladder

Do not execute this ladder until the branch tests and protected pre-install review pass.

1. Update/reinstall Vres from the merged guard build.
2. Create a dedicated disposable onboarding project/worktree.
3. Start one new Vres task for both candidate capabilities.
4. Drive normal Vres discovery so the missing browser/methodology needs are explicit.
5. Let the governor block on the missing needs.
6. Acquire two project-scoped capabilities using the existing governed gap-acquisition path and source/provenance evidence.
7. Install JEV only in that disposable onboarding scope using the exact MCP server name
   `jev-browser`; verify the loaded MCP tool names before exercising it.
8. Supply `TYPESAFE_API_KEY` outside chat/git.
9. Install Superpowers only in that disposable onboarding scope and disable its optional telemetry for the acceptance run.
10. Restart Claude so both plugin/MCP surfaces are physically loaded.
11. Verify Vres continuity and current task binding survive the Superpowers SessionStart hook.
12. Run JEV acceptance against a disposable fixture:
    - browser_open;
    - browser_snapshot;
    - browser_check;
    - browser_screenshot;
    - one reversible browser_do;
    - prove `allow_irreversible=true` is denied and record that this blocks the explicit bypass rather than proving Jev can never misclassify an action;
    - prove password/passcode/OTP/CVV/card-number/TYPESAFE_API_KEY-shaped values are denied;
    - prove unsafe direct browser_act is denied.
13. Invoke one compatible Superpowers methodology skill.
14. Attempt blocked Superpowers execution/worktree/capability-authoring skills using both
    namespaced and bare aliases.
15. Attempt one generic execution Agent path and prove it is denied.
16. Verify canonical Vres Sonnet/Opus/validator paths still work.
17. Run protected validation over the combined evidence.
18. Complete the task only after the protected PASS.
19. Mark the two project-scoped capabilities proven only after completion/pass.

No production account/payment/delete/send/publish action is part of this ladder.

## 11. Held after onboarding

The E-11 account-creation/browser-audit capstone remains held until this combined onboarding is complete.

The <=15% context rollover and model-generation calibration work remain parked after the existing roadmap.
