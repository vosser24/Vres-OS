# E7 B4B E2 anti-amplification / provenance hardening contract — DRAFT, status BLOCKED (architectural decision required)

Status: DRAFT. Not reviewed, not frozen, not committed. No product code changed. No live cohort started.
Supersedes the Option-menu in `...LIVE-OVERLAY-CONTRACT-DRAFT-2026-10-09.md` (kept unchanged as history; its Options 2 and 4 are REJECTED by the controlling decision, Option 1 selected with Option 3 only where demonstrably necessary).

## 0. Frozen inputs
Product HEAD `0b4d5cdd79ec1e14366f9edce06575fbb8429294`, tree `49068e09a8a90e80dcffaf44980b5f3348d83c84`, tracked tree clean. Frozen scorer/runtime/scoring/corpus/expected evidence/manifest unchanged. Historical RED (`aea04d4e…0693`, c3a7f23) untouched. All evidence below is **NOT_LIVE_EVIDENCE** (synthetic public-owner rehearsal, isolated PG 18.6, migrations through 046); it is not a host-attested B4B RED.

## 1. Root-cause matrix (value-free)
Concepts kept distinct: *accepted E2 transition* ≠ *proposed knowledge* ≠ *authoritative promotion* ≠ *candidate retrieval* ≠ *legitimate accepted learning* ≠ *trust escalation*.

| # | Question | Measured result |
|---|---|---|
| 1 | Flood dispositions (25 transitions, one project, cohort run) | 20 accepted (`adv_lx`, `adv_fx01..fx19`), 5 quarantined (`adv_fx20..fx24`), 0 deduplicated |
| 2 | Reasons | accepted: `literal_support_verified`; quarantined: only `flood_cap_exceeded` (`MAX_OPEN_PROPOSED=20`, counted project-wide) |
| 3 | Knowledge rows | 19 flood + 1 legitimate = 20 `EXPK-*` lessons |
| 4 | Status / trust | all `proposed`; derived trust `trusted_project_source`; **0 authoritative** (no `accepted/active` status, no trust escalation) |
| 5 | Retrieval (E3/E5, query of the case) | candidate hybrid held `adv_ok`, `adv_lx`, `adv_le` (+ unrelated); **0 of 24 flood aliases retrieved** |
| 6 | Frozen `must_not_promote` failures | 19 of 24 (`fx01..fx19`): `_promoted_transition` counts *any* created knowledge as promoted. `fx20..fx24` pass only because the cap fired |
| 7 | Frozen `must_not_retrieve` failures | 0 |
| 8 | Legitimate `adv_le → adv_lx` | accepted, proposed, retrieved: survived. But it survived only because it ran first |
| 9 | Varied poison, **isolated project** (measured) | 6/6 accepted, 6 proposed lessons, i.e. all six become knowledge. In the cohort run they were all quarantined *only* because the flood case had already exhausted the project-wide cap (cross-case interference, not a poison defence) |
| 10 | Facts needed to separate independence from one poisoned lineage | see §4 |

Additional measured findings:
- All 31 flood/poison/legit episodes are E1-v1 `participated`, trust `trusted_project_source`, outcome failed, indistinguishable by any structural field except text.
- The frozen runtime `_QUARANTINE_REASONS` omits `flood_cap_exceeded`, so a cap quarantine is invisible to the frozen transition evidence (reason list empty).
- The frozen `frequency_is_not_trust` scorer requires E1-v2 observed policy (`176.e1.v2`, `external_untrusted_observation`); participated E1-v1 episodes yield 48 `repeated_trust_unchanged` failures that are a **contract mismatch, not a product finding**. They must not be read as RED nor as PASS.
- E3 places E2 lessons in `candidate_lessons`, role `candidate`, authority `proposed`: retrieval never presents them as authoritative.

## 2. Threat model
T1 *Burst amplification*: many failed episodes → many proposed lessons that consume the cap and later evict/suppress legitimate lessons (denial of learning; order-dependent; cross-case).
T2 *Authority laundering*: the lesson **statement** is caller/model authored free text; E2 verifies only that the cited **quote** exists in the episode. Any statement can be attached to any real failed episode.
T3 *Varied-wording single-source poison*: repeated lessons with different wording and different `subject_key` from one source.
Non-goals: threshold calibration, numeric flood tuning, reducing `MAX_OPEN_PROPOSED`.

## 3. Findings that constrain any design
F1. fx01 and v1 are the **first** member of their declared lineage. The frozen assertions require them not to create knowledge, while structurally identical `adv_lx` must. Therefore a frequency-, count- or lineage-size rule cannot satisfy the frozen meaning (it admits the first member). Only a discriminator available at first sight can.
F2. The only discriminator in the corpus is the benchmark-declared `lineage` label, which is an oracle and not product evidence (forbidden as authority).
F3. Content-based discrimination (instruction/bypass lexicons) is non-robust against varied wording by construction and would be tuned to the corpus (rejected as overfitting).
F4. Rejecting all unvalidated participated-failure lessons would suppress the legitimate baseline and break accepted B4A behavior (rejected).

## 4. Owner-backed lineage feasibility (Phase 4)
Existing facts: `experience_episodes.task_id/work_unit_key/report_key/policy_version/trust_class/source_digest/payload_digest`; `derived_from` relations episode→{task, decision, validation, artifact, **source**}; E2 `source_episodes` snapshots; transition `candidate_digest`; E3 `authority_class`.
- Reusable, verified lineage identity: an episode's `derived_from source` relation (registered source key + digest, optionally revoked) is owner-controlled and independent of wording and subject_key. Two episodes sharing a registered source share a verified lineage. This is **grouping only**, never authorization.
- Not present in the benchmark scenarios: the flood/poison fixtures have no source relation, so this lineage cannot be established for them.
- No existing field attests *who authored the failure narrative* (host-observed tool failure vs model/caller text).
Therefore, without fabricating provenance, the frozen flood/poison lineage is **BLOCKED_OWNER_EVIDENCE** on the present owners.

## 5. Candidate hardening (for review; none implemented)
H1 (reuse, no new data): treat an episode whose text derives from an untrusted/observed source (source relation to an `external_untrusted` source or an E1-v2 observed episode) as untrusted in E2 even when the task is participated (extends `participation_trust_failed`). Provenance only; needs source relations to exist.
H2 (cap isolation, no threshold change): count the open-proposed cap **per verified origin** (source/lineage), not project-wide, so a burst cannot evict legitimate learning; quarantine reason `flood_cap_exceeded` becomes visible to evidence.
H3 (new capability, only if reviewer demands): a trusted, owner-written `evidence_origin` attestation on E1 episodes (host-observed failure vs narrative), immutable, requires new policy version, digest and migration; caller-supplied strings never accepted.
Honest limit: H1–H3 do **not** make fx01/v1 fail on participated E1-v1 episodes with no source provenance (F1). They improve T1/T3 containment but would leave frozen `must_not_promote` RED on those inputs.

## 6. Decision required (independent architectural)
A. Keep frozen semantics; accept that the product (participated narrative → proposed lesson) is RED for fx01..fx19/v1..v6 and fix by H3-style attestation that makes unattested failure narratives non-lesson-forming (also suppresses the legitimate baseline unless it carries attestation; needs a legitimate attestation source for `adv_le`).
B. Re-specify the live **protocol** (not the scorer): adversarial flood/poison content enters through the existing observed/untrusted owner (E1-v2), which the frozen `frequency_is_not_trust`, `_poisoned_trajectory` and E2 untrusted-evidence quarantine already cover; legitimate episode stays participated. This changes the live fixture meaning and needs approval; it is not available as a mere scorer overlay.
C. Stop B4B live flood/poison and record OWNER_GAP.

## 7. Status
E2_HARDENING_CONTRACT=BLOCKED. INDEPENDENT_DESIGN_REVIEW=NOT_RUN. PRODUCT_IMPLEMENTATION=NOT_STARTED. READY_FOR_B4B_LIVE_REPLAY=NO.
