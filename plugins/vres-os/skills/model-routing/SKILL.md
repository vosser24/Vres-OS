---
name: model-routing
description: Select a configured model for a work phase while keeping the strongest configured validator protected.
---

Use `model_recommend` with phase plan, build, validate, summarize, research, analyze or debug. Validation/review/audit maps to the protected validator. Delegate to `vres-os:validator` without a weaker model override. If that model is unavailable, stop that validation and report the capability gap.

Recommendations are configuration, not a model switch by themselves. The Chairman remains the parent; dispatch compatible workers using Claude's available tools. Ordinary Claude subagents cannot recursively create subagents: directors return bounded specialist requests to the Chairman rather than promising a nonexistent nested hierarchy.

Only record runtime/tokens actually observed. `model_record_run` is an audit of reported metrics, not trusted paired replay. Empirical automatic routing changes are held in this preview. Do not optimize away the validator or claim that a separate model executed when it did not.
