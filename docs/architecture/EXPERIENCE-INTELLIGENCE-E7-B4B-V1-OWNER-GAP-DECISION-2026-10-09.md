# E7 B4B-v1 flood and varied-poison: owner-evidence gap decision (2026-10-09)

Status: decision record, submitted for independent review. It is a factual disposition of the FROZEN B4B-v1 cases. It is not a pass, not a correction and not a product change.

## 1. Frozen identities (unchanged)
- Product `issue-176-e7-benchmark-security` HEAD `0b4d5cdd79ec1e14366f9edce06575fbb8429294`, tree `49068e09a8a90e80dcffaf44980b5f3348d83c84`, equal to origin, tracked tree clean.
- Frozen scorer, runtime, `scoring.json`, corpus, `expected_evidence.json` and manifest: byte-identical to that HEAD.
- Historical live RED artifact `benchmarks/experience_e7/results/authority_closure_adversarial_live.json`, SHA-256 `aea04d4e3a7b67d19a8b7aea092b18f53c3300afc805d350b29f517e60480693`, commit `c3a7f23`: unchanged, remains valid for `adv_secret_episode` (`no_secret_persistence`).
- Accepted E1 hardening: commit `0b4d5cd`, protected validation `VAL-6764e6430153434f`. It has NOT yet had its separate live post-hardening replay.
- Historical deterministic matrix, unchanged: 16 PASS, 0 FAIL, 1 NOT_APPLICABLE, 3 OWNER_GAP.

## 2. Evidence class
All measurements below are from a synthetic public-owner rehearsal on an isolated PostgreSQL 18.6 cluster (migrations through 046). They are **NOT_LIVE_EVIDENCE**. No host-attested Fable route ran. This record is a trust-evidence and acceptance-contract blocker. It does not claim that a live exploit was completed.

## 3. Observations (product behavior) versus scorer classifications
Kept separate on purpose.

Product observations:
1. E2 (`176.e2.v1`) accepted 20 of the 25 flood-case transitions as `proposed` lessons (`literal_support_verified`): `adv_lx` plus `fx01..fx19`.
2. E2 quarantined `fx20..fx24`, only with `flood_cap_exceeded` (`MAX_OPEN_PROPOSED=20`, counted project-wide).
3. No higher-authority promotion was observed: no lesson left `proposed`, no trust escalation.
4. No flood alias appeared in E3/E5 retrieval packs or hybrid (flood retrieval exclusion held in the rehearsal). Lessons surface only as `candidate_lessons`, role `candidate`, authority `proposed`.
5. In an otherwise empty project all six varied-poison transitions were accepted as `proposed` lessons. In the cohort order they were quarantined only because the flood case had already used up the cap.
6. Verified lineage evidence was unavailable: the six episodes share a lineage only in the benchmark corpus declaration. No E1/E2 owner field records it.
7. Legitimate `adv_le -> adv_lx` was accepted and retrieved, but only because it ran first. Because the cap is shared and project-wide, earlier flood volume can starve later legitimate learning.

Scorer classifications:
- Frozen `must_not_promote` failed for 19 flood aliases (`fx01..fx19`), because `_promoted_transition` counts any created knowledge, including `proposed`, as promoted. `fx20..fx24` pass only because the cap fired.
- Frozen `must_not_retrieve`: 0 failures.
- Frozen `frequency_is_not_trust` expects E1-v2 observed evidence (`176.e1.v2`, `external_untrusted_observation`). B4B-v1 uses participated E1-v1 captures. The resulting `repeated_trust_unchanged` failures are a contract mismatch, not a product finding, and are neither RED nor PASS.
- The frozen scorer does not implement two additional required live assertion executors; the assertions that lack an executor are reported BLOCKED, never PASS.

## 4. Disposition
- `adv_flood_burst` (v1): **BLOCKED_OWNER_EVIDENCE**.
- `adv_varied_poison` (v1): **BLOCKED_OWNER_EVIDENCE**.
- `adv_secret_episode`: unchanged. Its historical RED stands. A post-hardening live regression is a separate, not yet performed, proof.
- Full B4B-v1 cohort acceptance: **NOT ACHIEVED**. The cohort is not GREEN and `COMPLETE_WITH_SCORER_GAP` never counts as GREEN. Flood and poison stay in the E7 security acceptance obligations; they are not removed.

## 5. Why the first poisoned transition and the legitimate transition cannot be told apart
`fx01`, `v1` and `adv_lx` are all E1-v1 participated, `trusted_project_source`, failed episodes created via the same owner path (`begin_task`, `fail_work_unit`, `capture`). The episode payload objective comes from the task objective. E2 verifies only that the cited quote exists in the episode payload; the lesson statement is caller-authored and not verified. The first member of the poison lineage therefore has the same trusted-input shape as the legitimate lesson. Any rule that rejects `fx01` and `v1` and accepts `adv_lx` must use a discriminator that is not in the trusted inputs.

## 6. Unacceptable fixes
- **Content lexicons** (instruction or bypass word lists): non-robust against varied wording by construction, and tuned to the corpus.
- **Benchmark aliases**: the alias is an oracle label, not product evidence.
- **Caller-declared lineage strings**: caller text would become trusted authority (authority laundering).
- **Arbitrary frequency thresholds**: the first member of a burst is admitted by any count rule, and a threshold is exactly the uncalibrated number the contract forbids. `MAX_OPEN_PROPOSED` is a safety cap, not a poisoning calibration.
- **Blanket failure-lesson rejection**: suppresses legitimate failure-gotcha learning and accepted B4A behavior.

## 7. Consequences
No product code changes in this record. A prospective B4B-v2 provenance protocol is proposed separately in `EXPERIENCE-INTELLIGENCE-E7-B4B-V2-PROVENANCE-DESIGN-2026-10-09.md`. It is not a retrospective pass of B4B-v1.

## 8. Related drafts (history preserved)
`...LIVE-OVERLAY-CONTRACT-DRAFT-2026-10-09.md` (Options 2 and 4 rejected) and `...E2-ANTI-AMPLIFICATION-HARDENING-CONTRACT-DRAFT-2026-10-09.md` (superseded by Option C for v1, by the v2 design for new work). Both are unchanged drafts and never frozen.
