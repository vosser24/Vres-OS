---
name: procedural-learning
description: Reuse and register accepted repeatable workflows; evaluate improvements without changing their accepted business outcome.
---

Before solving a repeated task, call `procedure_match`, then `procedure_get` and check the input/output contracts. Semantic similarity discovers candidates; it never proves compatibility. Execute the recorded method or verified implementation artifact. Do not silently change aggregation, ranking metrics, units, ties, or filters.

After the user unconditionally accepts a reusable result, use `procedure_accept` with the task and exact procedure key. Capture the input contract, method, invariants, validation contract, output contract, and known corrections. A literal persisted user approval establishes the baseline, not an invented independent-validation PASS. Ask only when approval is conditional or ambiguous. Never reinterpret “OK but change X” as an unchanged baseline approval.

Use `procedure_feedback` for corrections and rejected approaches. Measured execution data may be recorded with `procedure_record_run`; unknown values are not zero.

For a possible improvement, compare baseline and candidate on the same representative inputs. Use `procedure_evaluate_candidate`. Automatic promotion is intentionally held in this preview because host-measured paired replay is not implemented. Do not claim a candidate ran merely because it was registered. User-reviewed changes can use `procedure_decide_candidate`. “Keep mine” or “reject” is rejection, not acceptance. Changed objectives require a separate business proposal.

Never call removed tools such as an ad-hoc optimization gate. The Python Pareto function is a tested policy helper, not a publish permission or proof of independent replay.
