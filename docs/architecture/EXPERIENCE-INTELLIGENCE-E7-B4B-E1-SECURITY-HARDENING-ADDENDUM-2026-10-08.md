# E7 Boundary 4B — E1 security-hardening addendum (design freeze, 2026-10-08)

Status: **DESIGN FREEZE FOR INDEPENDENT REVIEW. Nothing is implemented.** No product code changed, B4B not resumed,
Chunk 6 / held-out / full PostgreSQL acceptance / release gate not run.
RED evidence commit (product branch `issue-176-e7-benchmark-security`): `c3a7f2331736a65c698f1800fd58fc1ef2ba29a2`.
Canonical documentation baseline: `8870fd8451d81e767794950b3c57b080583b7b48`. Canonical task: `TASK-20261006-6cd9d80a92`.
Prior accepted boundaries (Chunk 5 matrix 16 PASS / 0 FAIL / 1 N/A / 3 OWNER_GAP; Boundary 4A) are unchanged and not reopened.

## 1. Control and cleanup status (honest)

- **Not verified from this session.** This session ran inside the live fixture: its MCP server and database setting point
  at the disposable `_test` fixture, so it cannot prove the fixture, its three roles, its isolated data directory and
  the recovery state are gone, and it must not delete the database it is bound to.
- Required from the **normal control session** (user-run, launcher-owned): run the verified ignored cleanup path
  (`-CleanupSuffix <fixture suffix>`), then confirm the database, three roles, data directory and recovery file are absent.
- The single control checkpoint ("Boundary 4B RED accepted for hardening review." / next action "implement and validate
  the independently frozen E1 security-hardening contract.") is **pending**; it must be made once in the control
  environment after cleanup is proven. It was not written to the fixture task.

## 2. RED evidence review

Observed (artifact `authority_closure_adversarial_live.json`): the first adversarial path (`adv_secret_episode`) ran the
full chain (task, bind, discover, prepare, real Fable route, plan, one report-only unit, start, public `fail_work_unit`,
terminal readback `failed`, E1-v1 `capture`). `capture` returned a row. The scorer's exact-canary count was 4:
`experience_episodes` 1, `tasks` 1, `task_state` 1, `checkpoints` 1. The run stopped per the RED rule.

Established by code reading and a read-only probe matrix (no writes):

1. **Source of the canary.** The frozen objective reads "…the pipeline printed the service key `<<CANARY_n>>` in its log…".
   `Repository.begin_task` stores the objective in `tasks`, `task_state` and a checkpoint; `ExperienceEpisodeService.capture`
   copies `task["objective"]` into `payload_source` and the persisted episode payload.
2. **Why E1 copied it.** Both `begin_task` (via `redact`) and capture (`_prepare_source_evidence`, `_prepare_payload` →
   `sensitive_policy.sanitize_extracted_text` → `redaction.sanitize_text`, sanitizer 164.1) use the canonical sanitizer.
   That sanitizer does not recognize "service key <value>" as a credential: `_KEYWORD` has no `service` qualifier, so
   `_PHRASE`/`_KV` do not match, and the fail-closed residual postcondition (`_RESIDUAL_*`, qualifiers
   api|private|signing|encryption|master|client|access) does not flag it either. Result: neither redaction nor rejection.
   The same root cause explains all four surfaces.
3. **Why `security_disposition=sanitized`.** That string is the *neutral default* returned when the sanitizer reports
   nothing found. A redaction event returns `sensitive_sanitized`. The earlier findings sentence "security_disposition=sanitized
   did not remove it" is ambiguous and is corrected here: **"sanitized" is not evidence that a redaction ran.**
4. **Realistic synthetic credentials.** Forms already covered (password, api key, access token, bearer, URI userinfo,
   provider shapes, private-key blocks, `api_key=`, client secret) are redacted or rejected. The defect is a keyword-coverage
   gap for other credential qualifiers, not a failure of the whole pipeline. The literal marker is incidental: a realistic
   `service_key=<value>` shows the same class of gap.
5. **Observed vs inferred.** Observed: the four hit counts, the disposition label, that `capture` returned, the probe results.
   Inferred: that fixing the sanitizer also zeroes `tasks`/`task_state`/`checkpoints` (same code path via `begin_task`).
   This must be proven in GREEN, not assumed.
6. **Missing scorer pieces.** Only the exact-canary assertion executed. The hybrid-hit count, hidden-reasoning scan and
   credential-leak scan were `NOT_EXECUTED` because the run stopped on first RED. `check_must_not_persist` is a conjunction
   (canary declared AND exact hits == 0 AND hybrid hits == 0), so one failed conjunct already fails it: **the RED stands
   without them**. It is accepted as a *scorer-equivalent partial* RED. The unexecuted checks cannot turn it green; they
   matter only for completeness of the GREEN proof. The RED is not weakened.

## 3. Security-contract ambiguity — decisions

- **Is task-source storage itself forbidden persistence?** The E7 contract says no raw secret/canary in *any persisted row or
  response*; the B4B handoff narrowed it to experience/retrieval/public-memory surfaces. **Decision: the contract text governs
  (strictest reading); the handoff narrowing is not relied on.** Task rows are not exempt. `begin_task` already redacts by
  design, so a raw secret in `tasks` is a defect, not a legitimate task-source copy.
- **Scope of the rule:** all durable storage written by the exercised authority path, as the scorer's all-base-tables count measures.
- **Full scoring without changing the classifier:** the frozen scorer, corpus and expected evidence stay untouched. The hardening
  is product-side (sanitizer). GREEN passes if the unchanged scorer counts 0 on every table after the same path.
- **If GREEN does not reach 0** on a table outside the sanitizer path (a surface that stores raw user input by design), the
  correction is a *separately approved, documented scoped overlay* (named surface, justification, tests). It is **not**
  adopted now, and the harness may not pre-scrub the objective to avoid the finding.
- The harness creating a canary-bearing task is legitimate: it models a user mentioning a secret. It stays unchanged.

## 4. Hardening design (smallest security-correct)

Owner: `src/vres_os/redaction.py` (canonical, shared). No new layer, no E1-local sanitizer, no `CANARY` special case.

1. **Credential vocabulary.** Add a closed, documented qualifier set to the keyword family: service, deploy, deployment,
   webhook, license/licence, ssh, admin, integration, bot, automation (alongside existing api/private/signing/encryption/
   master/client/access). Chosen from general credential vocabulary, not from the canary.
2. **Secret-valued gating (phrase form).** "<qualifier> key|credential|secret|token <value>" is redacted only when the value
   token is secret-looking (at least 4 chars with a digit or symbol), reusing the existing `_PHRASE` gate, so prose such as
   "service key rotation" is unchanged. The KV form (`service_key=<value>`) follows `_KV` rules.
3. **Fail-closed residual.** Mirror the new qualifiers in `_RESIDUAL_ASSIGNMENT` / `_RESIDUAL_KEY_MARKER` so any form that
   still survives redaction makes capture reject (`sensitive_review_required`) instead of persisting.
4. **Safe objective handling.** E1 capture shape is unchanged: it keeps sanitizing source evidence and payload, now with the
   corrected vocabulary. `begin_task` inherits the same fix, so control-plane rows share one owner.
5. **Provenance and idempotency preserved.** Digests are computed over the sanitized payload exactly as today; for inputs the
   sanitizer does not change, `source_digest` / `payload_digest` are byte-identical.
6. **Excluded on purpose:** `session`, `auth`, `root`, `ci`, `cd`, `pipeline`. A read-only prototype scan of 375 repository
   files (corpus, docs, src, tests) found the candidate rule matching only the frozen corpus line plus `session_key = …`
   identifiers in code and tests, so `session` is a demonstrated false-positive source and stays out. The final qualifier
   list is frozen only after the corpus-wide diff gate in section 6.

Counterexamples the design must handle: "service key rotation policy" (unchanged); `primary key`, `foreign key`, `sort key`,
`session_key` identifiers (unchanged); "Service key = <secret-looking value>" (redacted); `deploy_key: <secret-looking value>`
(redacted); quoted or multi-line values (existing multiline rules apply); an unrecognized shape that still reaches the
residual check (capture rejects, never persists).

## 5. Acceptance criteria

- A1. The frozen `adv_secret_episode` objective yields 0 exact hits in every `vres` base table via the unchanged scorer.
- A2. Realistic synthetic credentials for each added qualifier are redacted or rejected; none persisted verbatim.
- A3. Benign prose and identifiers from section 4 are byte-unchanged; the corpus-wide before/after sanitizer diff shows only intended changes.
- A4. Legitimate prior memory, project isolation, E1-v2 observed distinction, episode immutability and digests are unchanged
  for non-secret inputs; no hidden reasoning or raw secret is persisted.
- A5. Deterministic failure behavior: a rejected capture raises the same typed rejection and leaves no partial rows.
- A6. The 16 / 0 / 1 / 3 deterministic matrix is unchanged.

## 6. RED→GREEN validation plan

Fresh `_test` databases with isolated data directories; never the control database.

- **Unit (`tests/test_redaction.py`):** parametrized cases per added qualifier (redact and residual fail-closed), idempotence,
  linear-time shape, benign negatives, the frozen sentence with a neutral placeholder value.
- **Integration (`tests/integration/test_experience_episode_journey.py` plus one new focused module):** real `begin_task`,
  failed work unit, `capture`; assert the canary is absent from `tasks`, `task_state`, `checkpoints`, `experience_episodes`
  and every other base table via the frozen `exact_canary_hits`; public capture/rejection behavior; retrieval and public-memory
  surfaces; legitimate memory preserved; source-digest/idempotency regression; existing E1/E2 security regressions
  (`tests/test_audit_regressions.py`).
- **Scans:** hidden-reasoning and credential-leak scans over the fixture; hybrid-hit count; full frozen scorer, or a formally
  accepted scoped overlay per section 3.
- **Corpus gate:** before/after sanitizer diff across repository text and the adversarial/development corpora.
- **Independent GREEN:** a reviewer other than the implementer re-runs the focused set. Only then repeat the live B4B cohort,
  in a **new** disposable fixture (the RED fixture is never reused).

## 7. Proposed sequence

1. Control session: prove fixture cleanup; write the single control checkpoint.
2. Independent review of this addendum, including the qualifier list and the section 3 decisions.
3. Write failing unit and integration tests (RED), then the minimal `redaction.py` change (GREEN), then the corpus diff.
4. Focused tests, then independent GREEN review.
5. New fixture; rerun the B4B adversarial cohort from the start.

## 8. Not claimed

No fix exists; cleanup and the control checkpoint are unverified; B4B has one executed path, not 32; nothing here is a
release, a validation PASS or Chunk 6 readiness.
