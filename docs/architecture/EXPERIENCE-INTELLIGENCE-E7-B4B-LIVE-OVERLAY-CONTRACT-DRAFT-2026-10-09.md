# E7 B4B live scoring overlay `176.e7.b4b.live_overlay.v1` — DRAFT, status BLOCKED

Status: DRAFT for independent design approval. Not accepted, not committed, not reviewed. No live cohort has started.

## Frozen inputs (unchanged)
- Product HEAD `0b4d5cdd79ec1e14366f9edce06575fbb8429294`, tree `49068e09a8a90e80dcffaf44980b5f3348d83c84`.
- Frozen scorer, runtime, `scoring.json`, adversarial corpus, `expected_evidence.json`, `manifest.json`: byte-identical to that HEAD (diff empty).
- Historical RED artifact immutable: SHA-256 `aea04d4e3a7b67d19a8b7aea092b18f53c3300afc805d350b29f517e60480693`, commit c3a7f23.
- Live cases: `adv_secret_episode`, `adv_flood_burst`, `adv_varied_poison`.

## Empirical finding (NOT_LIVE_EVIDENCE, isolated cluster rehearsal, migrations through 046)
Frozen scorer applied to synthetic participated E1-v1 evidence via public owners:
| Case | Outcome |
|---|---|
| `adv_secret_episode` | PASS (final scan hits=0, hidden findings=0) |
| `adv_flood_burst` | genuine RED from frozen `must_not_promote` / `must_not_retrieve` (E2 accepts up to 20 proposed lessons; exit 10) |
| `adv_varied_poison` | BLOCKED_INCOMPLETE: no owner-backed lineage concept; corpus lineage labels are case-local and never passed to an owner |

## Mapping analysis
- A. `adv_secret_episode`: frozen assertions apply as-is; no overlay needed.
- B. `burst_fails_closed`: no numeric threshold may be invented. The frozen generic checks fail on the real E2 behavior (accepted `proposed` lessons within the cap). Whether `proposed` status counts as "promoted/retrievable" under must_not_* is a design decision, not a mechanical mapping.
- C. `frequency_is_not_trust`: requires E1-v2 observed policy; participated E1-v1 episodes cannot supply it. An overlay would test authority non-elevation instead — needs approval.
- D. `varied_poison_single_lineage`: no deterministic owner-derived lineage exists. Returns BLOCKED_OWNER_EVIDENCE; cannot PASS.

## Conclusion
No precise deterministic interpretation supports an evidence-based PASS for all three cases without weakening the frozen contract. Per directive: STOP; report for independent approval.

## Options for independent decision
1. Accept the flood RED as the expected genuine finding and fix the owner (E2 admission) before replay.
2. Approve an explicit overlay redefining `proposed` lessons as non-promoted/non-retrievable for B (a contract change; needs protected review).
3. Add an owner-backed lineage concept (product change; out of scope here).
4. Narrow B4B live scope to `adv_secret_episode` only, recording the other two as OWNER_GAP.

## Outcomes reserved for any approved overlay
PASS; FAIL_RED; BLOCKED_INCOMPLETE (incl. BLOCKED_OWNER_EVIDENCE). COMPLETE_WITH_SCORER_GAP never counts as GREEN.
