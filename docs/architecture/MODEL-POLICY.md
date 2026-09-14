# Model policy and protected validation

The user selects outcomes, not model names on every prompt. `ModelPolicyService.recommend()` normalizes
known phases and rejects unknown phase names rather than guessing a weak default for an unrecognized reviewer.
`validate`, `validation`, `review` and `audit` all return protected Claude Fable/high with no downgrade fallback.
That mapping is a release policy, not a guarantee of future model superiority or account entitlement. On a
new account/version, verify the strongest available permitted model before changing this policy.

Planning/build/summarization use registered bootstrap policies. `model_runs` captures supplied telemetry,
including incomplete values. Unknown token counts stay unknown. Negative/non-finite/invalid measurements are
rejected, but a positive agent-reported number is not thereby host-measured evidence.

**Empirical automatic policy replacement is disabled in this preview.** Registered policy remains the default.
A future promotion mechanism needs independent, task-matched, paired quality/runtime/token measurements and
reliability/security gates. Fewer tokens can still cost more on a different model: record both cost and tokens.
Validation is not a candidate for cheaper-model optimization under the current user policy.

Recommendations do not themselves change the active Claude model. The Chairman must dispatch a supported
worker with the requested model/effort, and the native runtime must confirm it. The Codex adapter is a separate
bounded CLI execution path; Vres neither copies OAuth credentials nor assumes Codex is installed/authenticated.

The mathematical Pareto predicate is tested separately. It does not grant execution authority. A real future
optimizer must include retries, failed attempts, review overhead and comparable inputs/environments rather
than cherry-picking one quick successful run.
