> **STATUS (2026-10-09):** historical record of the first, narrow step; the current description is in `EXPERIENCE-INTELLIGENCE-E7-B4B-E1-SECURITY-HARDENING-FINDINGS-2026-10-08.md`. The original RED remains historically valid. Acceptance is recorded only in the Vres validation ledger.
> **SUPERSEDED (2026-10-08):** superseded by `EXPERIENCE-INTELLIGENCE-E7-B4B-E1-SECURITY-HARDENING-FINDINGS-2026-10-08.md`. History retained below.

# E7 Boundary 4B — redaction hardening addendum (2026-10-08)

Trigger: live adversarial RED `no_secret_persistence` at `c3a7f23` (see the LIVE-ADVERSARIAL-FINDINGS doc).

## Diagnosis (measured)
The frozen `adv_secret_episode` objective states "the service key <<CANARY_1>>". The redaction owner's
separator-less phrase rule (`redaction._PHRASE`, added in E7 C5, `9fa82d3`) covered password/passwd/pwd/passphrase/
api key/access token/client secret only. "service key <value>" matched no rule, so E1 `capture` persisted the value
with `security_disposition=sanitized`. Same class as C5; no E1 code defect.

## Change (single owner: `src/vres_os/redaction.py`)
`_PHRASE` head list gains `(service|secret|signing|encryption|master)[_ -]?key` (the key families already in the
residual-assignment postcondition). The existing guard is unchanged: only a value carrying a digit or symbol is
redacted, so prose ("service key policy", "master key ceremony") is kept. No E1/benchmark/scorer/threshold/migration change.

## Evidence
- RED first: `test_service_key_phrase_is_redacted` failed before the change, passes after.
- `test_key_phrase_prose_without_secret_shaped_value_is_kept` passes (false-positive guard).
- Passing after: tests/test_redaction.py, test_experience.py, test_experience_consolidation.py,
  test_experience_benchmark_{corpus,retrieval,security,security_observed,foundation}.py, test_experience_lifecycle_unit.py.
- Not run: full suite, PostgreSQL integration, release gate, protected validation, live re-run.

## Remaining
This is a product-byte change: it needs independent protected validation before acceptance, and the live 4B cohort
(32 failed paths, 31 consolidations) must be re-run from a fresh fixture launched by the user. The earlier RED
artifact stays as history.
