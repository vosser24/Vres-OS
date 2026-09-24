# Capability onboarding — Superpowers (JEV withdrawn)

Status: **SUPERPOWERS-ONLY ONBOARDING — JEV WITHDRAWN BY USER BEFORE PROOF**

GitHub issue: #148

Branch baseline: `main@cb715a0b45f921d447e0a933c70c883137a49ae4`

Date: 2026-09-24

## 1. Current user-authorized scope

The user explicitly withdrew JEV Browser from the Vres build/onboarding path after
learning that live use requires an external TypeSafe/System One API key and API
dependency that had not been knowingly selected.

JEV is therefore not an active Vres capability target.

This phase now onboards only **Superpowers** as an optional methodology capability.

The E-11 browser-audit capstone remains held until the Superpowers onboarding is
complete. The later parked items remain out of scope:

- seamless Vres-managed <=15% native context rollover / auto-compaction;
- model-generation calibration and governed adoption (#146).

## 2. Historical JEV disposition

JEV reached governed discovery and project capability acquisition before the user
withdrew it.

Historical record:

- capability key: `jev-browser-guarded-external-control-v1`;
- acquisition event: 2585;
- project-scoped;
- proven_count: 0;
- product/onboarding disposition: **withdrawn by user before proof**.

The historical row/evidence is retained for auditability. It must not be marked
proven, treated as an active product dependency, or silently deleted/re-written.

No TypeSafe API key was supplied to Vres/Claude, and no authenticated JEV browser
acceptance was completed.

The disposable local JEV MCP/source/fixture created during preparation must be
removed from the target Windows environment. Vres ships no JEV-specific MCP guard
or browser policy after this cleanup.

## 3. Active candidate — Superpowers

Frozen onboarding evidence snapshot:

- repository: `obra/superpowers`;
- upstream commit: `5bf4e78011075bcfc0dc295f0724994cd123ee71`;
- plugin version: `6.4.1`;
- license: MIT;
- Claude plugin name: `superpowers`;
- SessionStart matcher: `startup|clear|compact`.

The pinned snapshot contains 15 skills.

Reviewed advisory methodology skills:

- brainstorming;
- systematic-debugging;
- test-driven-development;
- verification-before-completion;
- requesting-code-review;
- receiving-code-review;
- writing-plans;
- diagnosing-superpowers.

Execution/orchestration/capability-authoring workflows denied while an unfinished
Vres task is active:

- using-superpowers;
- subagent-driven-development;
- executing-plans;
- dispatching-parallel-agents;
- using-git-worktrees;
- finishing-a-development-branch;
- writing-skills.

A future Superpowers version is not implicitly onboarded. Its skill inventory and
hook behavior require re-review before upgrade/adoption.

## 4. Superpowers authority class

Superpowers is an **optional methodology capability**, not a Vres runtime
dependency and not an alternative orchestration system.

While an unfinished Vres task is active:

- Vres owns task/session state;
- Vres owns routing/model/effort authority;
- Vres owns governed worker identity/provenance;
- Vres owns work-unit orchestration;
- Vres owns protected validation and completion;
- reviewed Superpowers advisory methods may contribute process guidance only;
- Superpowers execution/worktree/subagent workflows may not replace Vres
  orchestration;
- generic/plugin/custom execution agents may not silently become Vres workers.

Outside an active Vres task, Vres does not claim general authority over
Superpowers workflows.

## 5. Existing governed capability record

The governed capability record already acquired for this project is:

- key: `superpowers-advisory-methodology-v1`;
- acquisition event: 2586;
- project-scoped;
- status: active;
- proven_count: 0.

The resolver fix shipped through #150/#151 ensures the original governed
capability need resolves to this existing record. Do not create a replacement
record or direct-write aliases.

Installation alone does not prove the capability.

`capability_mark_proven` remains gated on a completed task with passing protected
validation.

## 6. Mechanical runtime guard

Implementation module:

`src/vres_os/external_capability_preflight.py`

Wrapper:

`plugins/vres-os/bin/vres-external-capability-preflight.ps1`

The external-capability PreToolUse hook now matches only:

- `Skill`;
- `Agent`.

It does not match MCP tools.

### 6.1 Superpowers Skill policy

During an active Vres task:

- every reviewed advisory skill in the pinned 6.4.1 inventory is allowed;
- every reviewed execution/worktree/subagent/capability-authoring skill is denied;
- pinned bare aliases and reviewed namespaced invocation forms are normalized;
- unknown namespaced Superpowers skills fail closed;
- unknown arbitrary bare skill names are not attributed to Superpowers without
  evidence of origin.

### 6.2 Agent policy

During an active Vres task:

- canonical `vres-os:*` agents continue to the existing Vres agent preflight;
- `Explore`, `Plan` and `claude-code-guide` remain advisory helpers only;
- `general-purpose`, `claude`, plugin/custom execution agents and missing
  agent identities are denied by this guard.

The existing canonical agent preflight retains Vres model-frontmatter/model-tier
authority.

## 7. SessionStart bootstrap boundary

Pinned Superpowers 6.4.1 reads the full
`skills/using-superpowers/SKILL.md` during SessionStart and injects it as
additional context.

That injection occurs before any later `Skill` PreToolUse call and therefore
cannot be erased by the mechanical Skill guard.

The authority boundary is deliberately layered:

1. Vres/user/project rules govern instruction precedence and ownership.
2. The external capability PreToolUse guard blocks later incompatible
   Superpowers Skill/Agent execution.
3. Existing Vres routing/model/validation/completion contracts remain
   authoritative.

Claude Code merges hooks from different sources; Superpowers does not replace
the Vres SessionStart hook.

## 8. Hook timeout limitation

The external-capability wrapper exits blocking on runtime/policy errors and
returns structured deny decisions for policy violations.

The hook intentionally has no short artificial timeout.

Current Claude Code command-hook semantics still permit a host timeout to fall
back to normal permission flow. This is a host-level residual limitation and
must not be described as absolute/cryptographic fail-closed enforcement.

Superpowers remains methodology-only, so acceptance does not depend on this hook
as the sole control for a production-risk external action.

## 9. Physical Superpowers acceptance

Use the pinned source checkout at:

`5bf4e78011075bcfc0dc295f0724994cd123ee71`

Load it only in the disposable onboarding Claude session via `--plugin-dir`.
Do not install a marketplace/latest version during acceptance.

Disable optional telemetry for the acceptance session.

Acceptance must prove:

1. Vres resumes the existing onboarding task and authority survives the
   Superpowers SessionStart bootstrap.
2. The plugin identity/version is Superpowers 6.4.1 at the pinned source commit.
3. One reviewed advisory skill such as `systematic-debugging` loads successfully
   for a synthetic reasoning-only example.
4. `using-git-worktrees` is denied while the Vres task is active.
5. `general-purpose` Agent execution is denied.
6. Canonical Vres agent/routing/model authority remains unchanged.
7. No repository file is edited by acceptance.
8. No new worktree is created by Superpowers.
9. No external output becomes Vres protected validation/completion evidence.
10. The capability remains proven_count 0 before final task completion.
11. Fresh protected validation independently reviews the physical evidence.
12. Only after protected PASS and task completion may
    `superpowers-advisory-methodology-v1` be marked proven.

## 10. Local JEV cleanup

Before Superpowers-only acceptance, remove the previously prepared disposable
JEV surface:

- remove local MCP server `jev-browser` from the disposable project;
- remove the pinned JEV checkout and disposable browser fixture;
- no TypeSafe credential should exist or be requested;
- repository state must remain clean.

Playwright browser binaries downloaded into the user's shared Playwright cache are
not Vres runtime dependencies. They may be left for other tooling or removed by
the user separately; Vres does not depend on them after JEV withdrawal.

## 11. Held after onboarding

After Superpowers onboarding completes:

1. proceed to E-11 browser-audit capstone using the separately selected browser
   approach for that phase;
2. then address the parked <=15% context rollover work;
3. then address model-generation calibration / #146.

JEV is not part of that roadmap unless the user explicitly re-authorizes it in a
future task.
