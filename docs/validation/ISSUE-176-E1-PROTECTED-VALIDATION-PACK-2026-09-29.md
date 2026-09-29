# Issue #176 E1 — Protected Validation Pack

Date: 2026-09-29  
Repository: `vosser24/Vres-OS`  
Issue: #176  
PR: #179  
Tranche: **E1 only — contracts + immutable episode ledger**  
Authoritative base: `fe31e30e593a44b8b5ab565fa0db859bbefec0c6`

This file is the frozen operator/validator packet for the first protected E1 acceptance boundary.

It does **not** authorize E2, merge, or issue closure by itself.

## Exact-head rule

The protected validation must bind to the **current PR head at invocation time**.

Before validation:

1. read `origin/main` and require it to remain exactly the authoritative base above, unless an explicit history-preserving integration is performed and all exact-head evidence is rerun;
2. read PR #179 head;
3. require GitHub CI SUCCESS on that exact head;
4. do not mutate the branch/task state after protected validation preparation;
5. record the exact head SHA in the protected validation report.

If the head changes after validation, the protected PASS is stale and must be rerun.

## E1 scope under review

Allowed implementation:
- versioned Experience Intelligence episode policy;
- immutable bounded `experience_episodes` ledger;
- deterministic capture only from mechanically known terminal task/work-unit state;
- canonical source/payload digests;
- explicit participation/trust/security disposition;
- #164 sanitizer reuse;
- hidden/private-reasoning rejection;
- project/scope enforcement;
- relation edges into existing task/decision/procedure/capability/validation/source/artifact truth owners;
- unit/migration/PostgreSQL evidence.

Explicitly out of scope:
- E2 consolidation or transition verifier;
- recurrence/materiality thresholds;
- unified experience retrieval;
- temporal revocation/forgetting;
- retrieval observations;
- automatic lesson/procedure promotion;
- capability scoring;
- Chairman experience-pack injection;
- company-wide memory promotion;
- #165 or later work.

## Non-negotiable acceptance invariants

The validator must independently verify all of these:

1. **No second generic memory authority.** Tasks/checkpoints, decisions, knowledge, procedures, capabilities, relations and raw evidence remain the existing truth owners.
2. **No hidden/private chain-of-thought persistence.** Raw assistant reasoning, scratchpads, hidden reasoning/internal monologue and equivalent fields cannot be written into an episode.
3. **Mechanically sourced capture only.** Callers choose task/work-unit identity; they do not supply arbitrary durable narrative payload.
4. **Terminal-state gate.** Task episodes require completed/cancelled tasks; work-unit episodes require passed/failed work units.
5. **Failure integrity.** Failed/cancelled trajectories stay failed/cancelled and are not silently transformed into positive procedures or lessons.
6. **Secret-safe persistence.** #164 sanitization is reused; safely sanitizable content may persist only sanitized; residual credential-like content fails closed; raw credential values are not intentionally persisted by E1.
7. **Scope isolation.** Project-local episodes cannot be read or semantically linked across unrelated project scope.
8. **Immutable history.** Existing episode rows cannot be silently updated/deleted under normal runtime authority.
9. **Deterministic provenance.** Policy version/digest, source digest and payload digest are stable and fail closed on policy drift.
10. **Idempotency/concurrency.** Repeated/concurrent capture of the same terminal source produces the same immutable episode, with uniqueness/advisory-lock race protection.
11. **Transactional evidence links.** Episode + relation edges use the existing relations/evidence system and commit/rollback atomically.
12. **No authority promotion.** External/untrusted text cannot become approval, company rule, permission, validation-policy mutation, preferred procedure or credential merely because it appears in an episode.
13. **#163/#164/#174 preserved.** Credential Broker, secret-safe onboarding, and Engineering Architecture Governance boundaries remain intact.
14. **No E2+ implementation.** The diff contains no consolidation/retrieval/promotion/Chairman-learning behavior.

## Required evidence to inspect

Primary files:
- `docs/architecture/EXPERIENCE-INTELLIGENCE-E1-CONTRACT-2026-09-29.md`
- `src/vres_os/migrations/037_experience_episode_ledger.sql`
- `src/vres_os/experience.py`
- `src/vres_os/relations.py`
- `tests/test_experience.py`
- `tests/test_migration_contract.py`
- `tests/integration/test_experience_episode_journey.py`
- `tests/integration/test_migrator_resume_journey.py`
- `tests/integration/conftest.py`
- `docs/handoffs/ISSUE-176-E1-20260929.md`

Baseline truth-owner/security files to cross-check:
- `src/vres_os/redaction.py`
- `src/vres_os/sensitive_policy.py`
- `src/vres_os/knowledge.py`
- `src/vres_os/procedures.py`
- `src/vres_os/capabilities.py`
- `src/vres_os/task_decisions.py`
- `src/vres_os/validation.py`
- `src/vres_os/repository.py`
- `docs/architecture/ENGINEERING-CONSTITUTION.md`

## Protected validator contract

Required validator:
- agent: `vres-os:validator`;
- model: protected Fable;
- effort: high;
- substitute model: **not allowed**;
- caller/model override: **not allowed**.

The validator should:
- inspect the exact PR diff against authoritative main;
- inspect the files above;
- use the exact-head CI evidence;
- rerun or inspect targeted PostgreSQL/security tests where the host contract allows;
- check scope/provenance/security boundaries independently;
- explicitly state whether any acceptance invariant is unsupported, ambiguous, or violated;
- return **PASS** only if there is no unresolved critical/major E1 defect and no E2+ scope leak.

## Required report fields

The durable protected result must include:
- validation request key;
- exact reviewed Git SHA;
- authoritative base SHA;
- PR number;
- host-observed validator/model identity;
- protected/Fable/high assurance statement;
- PASS/FAIL;
- findings with severity;
- exact tests/evidence inspected or rerun;
- explicit verdict for all 14 invariants above;
- confirmation that E2 has not started;
- any deferred physical/live criteria carried to #169.

## Copy/paste Chairman instruction for the host session

> Resume #176 E1 protected acceptance only. Read the canonical checklist, resume handoff, issue #176, the frozen Experience Intelligence plan, and `docs/validation/ISSUE-176-E1-PROTECTED-VALIDATION-PACK-2026-09-29.md`. Verify authoritative main and the exact PR #179 head. Require exact-head CI success. Freeze/checkpoint the final reviewed E1 state before `validation_prepare`; do not mutate task state while validation is in flight. Invoke only the canonical protected `vres-os:validator` under pinned Fable/high with no substitute or model override. Validate only E1 contracts + episode ledger against the 14 invariants in the pack. If PASS, persist the exact request/head/model evidence; do not start E2 until E1 closure evidence is complete. If FAIL, keep E1 active and fix only the bounded defect.

## Machine-readable validation manifest

```json
{
  "manifest_version": "176.e1.validation.v1",
  "issue": 176,
  "pull_request": 179,
  "tranche": "E1",
  "authoritative_base": "fe31e30e593a44b8b5ab565fa0db859bbefec0c6",
  "candidate_head": "resolve_from_pr_179_at_validation_time",
  "required_ci": {
    "repository": "vosser24/Vres-OS",
    "workflow": "Vres-OS CI",
    "exact_head_success_required": true
  },
  "validator": {
    "agent": "vres-os:validator",
    "model_class": "Fable",
    "effort": "high",
    "protected": true,
    "substitute_allowed": false,
    "override_allowed": false
  },
  "scope": {
    "allowed": [
      "versioned experience policy",
      "immutable bounded episode ledger",
      "mechanically sourced terminal capture",
      "source and payload digests",
      "secret-safe sanitization",
      "private-reasoning rejection",
      "scope enforcement",
      "existing relation evidence links",
      "E1 tests and handoff"
    ],
    "forbidden": [
      "E2 consolidation",
      "E3 retrieval",
      "E4 lifecycle or revocation",
      "E5 capability/procedure learning integration",
      "E6 retrieval observations or utility credit",
      "E7 benchmark implementation",
      "E8 Chairman experience injection",
      "#165 or later implementation"
    ]
  },
  "acceptance_invariant_count": 14,
  "pass_requires": [
    "exact-head CI success",
    "no critical or major unresolved E1 defect",
    "no scope leakage into E2+",
    "no security, scope, provenance or authority regression",
    "host-observed protected Fable/high identity"
  ],
  "after_pass": "record evidence and complete E1 closure boundary before considering E2",
  "after_fail": "fix only bounded E1 defects and rerun exact-head CI plus protected validation"
}
```

## Freeze condition

Once this validation-pack commit is on PR #179 and exact-head CI is green, do not add narrative/documentation commits merely to report success. Record CI/protected-validation evidence in the PR/issue thread so the reviewed Git SHA remains frozen.
