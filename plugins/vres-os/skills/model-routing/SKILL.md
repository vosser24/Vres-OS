---
name: model-routing
description: Select a configured model for a work phase while keeping the strongest configured validator protected.
---

Use `model_recommend` with phase plan, build, validate, summarize, research, analyze or debug. Validation/review/audit maps to the protected validator. Delegate to `vres-os:validator` without a weaker model override. If that model is unavailable, stop that validation and report the capability gap.

Recommendations are configuration, not a model switch by themselves. The Chairman remains the parent; dispatch compatible workers using Claude's available tools. Ordinary Claude subagents cannot recursively create subagents: directors return bounded specialist requests to the Chairman rather than promising a nonexistent nested hierarchy.

All routed expert roles use the same canonical governed worker surfaces: `vres-os:sonnet-expert` when the persisted route says `execution_tier="sonnet"`, and `vres-os:opus-expert` when it says `execution_tier="opus"`. Pass the persisted routed role in the bounded assignment and require that worker to file `orchestration_expert_report`. Do not launch role-specific agents such as `vres-os:commercial-director`, `vres-os:finance-director`, or the other legacy director/steward surfaces for governed execution; host preflight denies them before execution so worker-model evidence cannot bypass the canonical ledger.

For a routed `challenger` seat, use `vres-os:sonnet-expert` or `vres-os:opus-expert` according to its persisted tier, set the assignment role to `challenger`, and require `orchestration_expert_report` with `report_type="challenge"`. Do not launch `vres-os:challenger` directly; that legacy surface is denied before execution for the same reason.

Only record runtime/tokens actually observed. `model_record_run` is an audit of reported metrics, not trusted paired replay. Empirical automatic routing changes are held in this preview. Do not optimize away the validator or claim that a separate model executed when it did not.
