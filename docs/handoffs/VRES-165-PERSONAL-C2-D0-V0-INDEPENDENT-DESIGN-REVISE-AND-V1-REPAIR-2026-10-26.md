# Vres-OS #165 — PERSONAL C2 design D0 v0 independently DESIGN_REVISE: preserve reviewer findings, source-grounded B-01 and next v1 repair

**Date:** 2026-10-26, Europe/Athens.
**Repository:** vosser24/Vres-OS.
**Canonical documentation branch:** docs/chatgpt-continuity-20261023.
**Historical immutable reviewed design:** docs/architecture/VRES-165-PERSONAL-C2-REVERSIBLE-CHAIRMAN-MODEL-CHANGE-DESIGN-V0-2026-10-26.md, Git blob **b08ef92fc72df90651545503c638923eec157412**, in documentation commit **384a9adc3a4bfa59c75cad02452c320e51ae7d7d**, tree **3c25db0b7be38f742a7aac10e73340b936b602b7**, direct parent **baab8c59fa064fdec37dd3bbf443f529f8979002**.
**User-pasted independent Claude Code result:** **DESIGN_REVISE**, exactly ONE material **BLOCKING B-01** plus D-1..D-7 informational/repair matters; final marker **VRES_165_PERSONAL_C2_REVERSIBLE_MODEL_SWITCH_DESIGN_REVIEW_COMPLETE**. Reviewer did not execute Git/Python/pytest/installer/Vres tasks, touch PostgreSQL, use a provider, edit files or activate any model.
**No other verdict:** v0 NOT accepted. No C2 v1 acceptance until a SEPARATE fresh reviewer report at the new exact v1 Git blob. Historical v0 remains UNMODIFIED, NOT superseded by rewriting its bytes.

## 0. Exact independent review provenance and coverage

Reviewer identities and digests were OPERATOR/CHATGPT supplied, NOT verified by Claude Git/hashing. Claude reported its detached docs-review checkout's install.ps1 is NOT the original P2 installer; it copied source plugins from the checkout without a Git-object staging manifest. P2 install.ps1, P2 release_artifact.py and install_recovery.py were NOT present in that docs checkout; Claude could NOT confirm their original P2 behavior from that review. Source comparisons below are subsequent separate ChatGPT GitHub reads and must never be attributed to Claude.

Claude reported FULL reads:
- C2 v0 design 1..203 **numbered source lines**; API-style line splitting by ChatGPT may show 204 strings including final newline, not a disagreement about content.
- Normative R3 design 1..262.
- R3 erratum 1..38.
- Prior C2 installed-file proof 1..135.
- Historical docs-worktree install.ps1 1..296.
- Historical docs-worktree docs/INSTALL-WINDOWS.md 1..181.

PARTIAL Claude reads:
- Continuity index lines 1..12 plus Grep elsewhere.
- C1 R1 OFFLINE_ACCEPT handoff lines 1..40.
- docs-worktree plugins/vres-os/agents/chairman.md Grep hits 2..5 and 74.
- tests/test_aigo_orchestration_contract.py lines 175..189.

NOT read by reviewer: the complete 200+ file source/test tree, chairman_selection_preview.py, original P2 installer/release_artifact/install_recovery and original P2 plugin body. The reviewer explicitly disclosed these limitations, and no unsupported provenance should be inferred.

## 1. Exact independently reported BLOCKING B-01

**B-01** source in v0: §3 lines 66..72, §4 line 83, §9 lines 185..186. A frontmatter-only policy materialization for Opus/medium contradicts an existing Chairman doctrine and test pins:
- The docs checkout Chairman.md line 74 described Sonnet as its default control plane and Opus as never the default shell.
- tests/test_aigo_orchestration_contract.py:182 asserts model: sonnet for Chairman.
- v0 calls preserving the entire current P2 agent body unchanged a safety property but does NOT require any doctrine/test-pin disposition before a future Opus candidate can be called valid.
- The reviewer offered three explicit design choices: coordinated body+test amendment; explicitly labelled override; OR acknowledgement that it contradicts current routing policy. Reviewer would not accept silently treating model/effort-only rendered bytes as a releasable valid candidate.

**Independent ChatGPT source-grounding after review, NOT Claude-reviewed:**
- Original P2 source commit **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c**, immutable Chairman Git blob **6f2239c4dd0d52090d31415c17f763505f93b900**, has frontmatter model sonnet / effort high at lines 4..5. Its REAL line 74 explicitly says "The Chairman itself runs on Sonnet as the default control plane" and that Opus is never the default shell or routine routing model.
- Feature source **7ac041018d4ec5a06be07318ecce5e140faccd91**, plugin agent blob **64cba93d6f69960350a0006b594734288f087ccc**, line 74 has ALREADY changed the doctrine to say Chairman's model is defined by pinned policy/frontmatter, though it still says Opus is never the default shell or routine routing model. Therefore the newer accepted C1 **source preview** is not directly reusable as the original installed P2 body.
- Existing orchestration test **tests/test_aigo_orchestration_contract.py**, Git blob **e50c4bfa3a7920b91bdfefbc2bd14f1e9a14fee8**, source at original P2/feature/docs checkout, contains TWO independent static assertions pinning the Chairman SOURCE to Sonnet: **line 109** and **line 182**; router Fable and worker Sonnet/Opus pins at lines 183..185 MUST stay protected. The legacy source test is NOT automatically a valid constraint on a separately derived installed policy, but its original meaning must be explicitly reviewed and tests added/changed before a new release.
- Accepted Phase A renderer **src/vres_os/chairman_policy.py** blob **36e62d6a2712ac305fd4070bac658b94d61d155e** changes ONLY the frontmatter model/effort of supplied bytes. Existing **tests/test_chairman_policy_materialization.py** blob **4a9e2ea4540bd074351179fb0a68a677acd113f8** tests at lines 140..145 require unchanged body for the given SOURCE template; this pure contract must not be silently weakened. Instead future source work must separately establish a reviewed **POLICY-AWARE TEMPLATE BODY**, then render policy frontmatter from that separately reviewed template. Source-default Sonnet tests may legitimately remain tests of an unmaterialized template, if future new tests strongly validate the derived installed Opus release. Merely deleting or replacing Sonnet assertions without a reviewed semantic disposition is prohibited.
- **Design revision required:** a new v1 must label the calculated original-P2 frontmatter-only SHA **b73e7497454a464f6b6bc1df00f42422696da786a07eb2936ae73ad73abedf54** as **DIAGNOSTIC-ONLY / INELIGIBLE FOR INSTALLATION** under B-01. It is a correct SHA computation, NOT a valid release candidate. No valid replacement body/render SHA exists until the doctrine and tests are deliberately amended and reviewed. No source change is implemented by these documents.

This B-01 is a GENUINE compatibility issue, not a reason to abandon the user-selected Opus/medium goal or skip protected worker/validator boundaries.

## 2. Every reviewer INFORMATIONAL / repair recommendation preserved

**D-1: installer provenance gap.** The documentation-review checkout's old install.ps1 (Claude read all 296 lines) has no pinned source-manifest staging. The real installed original P2 version was a different commit. Subsequent separate GitHub P2 source verification by ChatGPT confirms install.ps1 blob **29a5f0da235021cc8c5607eb92218e5ea98145fa**, src/vres_os/release_artifact.py blob **ddfc1beacad98199b489dc6f56456baf4d519c6a** and src/vres_os/install_recovery.py blob **1c0d585645280678af4875f2842a3350f9805e0a** under P2 **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c**. Reviewer could NOT verify those in its docs checkout. Future v1 must distinguish exact P2 provenance verified by ChatGPT from historical docs-checkout installer observations, and avoid claiming reviewer inspected original P2 files.

**D-2: disproportionate full installer.** Reviewer observed the docs-checkout installer creates a venv, pip install, doctor, global CLAUDE.md/rules/settings, launchers and PATH updates. Original P2 installer also has multiple such side effects (P2 original installer lines 186..307). Rebuilding an entire personal runtime solely to choose a Chairman family is operationally heavy. The best design proposes a minimal **SUPPORTED POLICY/PLUGIN-ONLY RELEASE TRANSITION** with truthful new immutable policy/release identity, existing runtime/launchers/global settings untouched unless proven separately required, rather than executing the old full installer as a model-change shortcut. The design must not pretend such a supported narrow updater exists already.

**D-3: history adjacency after abandonment.** Accepted B1 prohibits adjacent equal model/effort policy proposals. If most recent *abandoned/revoked pending proposal* was Opus/medium while installed governing G stayed Sonnet/high, an immediate identical Opus/medium proposal is **REFUSED**, despite current G remaining Sonnet/high. R3 §7.1 and R3-N07 forbid fabricating an intermediate Sonnet/high dummy policy merely to bypass this. Operator UX must say retry is blocked until a genuine, separately authorized intervening policy proposal (with its own E/V/CAS etc.) or a separately reviewed history schema change; do not automatically produce an alternate model hop.

**D-4: revocation after first installed write.** Add an explicit failure-state matrix row: after first byte/path move/write, a revocation must leave protected Q pending/in RECOVERY; only independent evidence of installed AND runtime-loaded bytes corresponding exactly to previous completed G plus separately protected ABANDON may clear Q, OR a fresh W-backed RESTORE_GOVERNING with protected readback/recovery. Never clear pending solely on local file restore; never reuse consumed E/W, never automatically demote.

**D-5: actual installer tuple reconciliation.** Reviewer noted existing plugin directory moves, pointer writes (including a later rewrite), single same-user pending-install.json journal and manual crash-recovery. v1 should detail observable tuples of (active pointer, managed plugin, pending journal, candidate release) and safe BLOCKED/reconciliation behavior. The P2 original installer order independently confirmed by ChatGPT: stage complete release, create recovery snapshot, write pending-install.json, move prior plugin to backup, copy candidate plugin, verify, update launchers, publish new active pointer, update global rules/statusline/compaction, rewrite active pointer, then remove journal. None of these is a single atomic multi-file write and the journal is NOT a T2-resistant authority service.

**D-6: optional non-F1 personal experiment.** The reviewer explicitly DID NOT RECOMMEND a shortcut or weakening. It stated user may separately decide whether to seek an accurately labelled experimental, NON-F1 path outside the protected #165 model-switch acceptance. v1 must record an explicit **USER DECISION NOT MADE**, no implicit implementation or approval; an independent, separate design and authorization would be needed if ever requested, and cannot be called completion of #165. Under the current #165 governance path positive authority remains BLOCKED until real provider exists.

**D-7: proportionality.** The bounded evidence allowlist and E/W dual confirmation are appropriate for the PERSONAL single-user experience; preserve this without gratuitous enterprise IAM/process overlays.

Other reviewer remarks:
- No source tests run; existing trusted-release manifest and Git-blob staging unverifiable in its docs checkout.
- Manifest versioning contract should explicitly require older verifier refusal of unknown/new manifests and future verifier refusal of unrecognized fields, schemas and unknown future versions. **ChatGPT separately confirmed original P2 source release_artifact.py uses FORMAT vres-personal-release-artifact, VERSION=2; strict load_manifest currently refuses version != 2 and requires each file entry to have exactly path/mode/git_blob/bytes/sha256.** Any policy-derived materialization changes format/version and MUST NOT silently treat derived bytes as original Git blob bytes.
- Consent/authority section is directionally sound: prior G/L/Q distinct, protected E/V/CAS, separate W, F1 provider missing, T2 threat model retained.
- Actual running physical model is still unverified; installed bytes/same-user SHA do not prove model dispatch.
- Reviewer’s detailed crash comments: v0 already disallows invented atomic multi-file rollback, but needs explicit D-4/D-5. The whole v0 is not accepted until revision.
- Recommended next action: a SHORT v1 design revision correcting B-01, D-1 and D-4 as the minimum, and also D-2/D-3/D-5/D-6 and versioning to avoid another review churn. After separately accepted design, consider tiny C2-D1 pure offline planner (caller-supplied bytes ONLY, no filesystem I/O, REFUSE unresolved doctrine/test pins); NO real trusted provider or installer yet.

## 3. Exact independently reported conclusion and statuses

    DESIGN_REVISE
    DESIGN_ONLY
    TESTS_NOT_RUN
    SOURCE_MODIFICATION_NOT_RUN
    NO_AUTHORITY_ISSUED
    NO_MODEL_ACTIVATION
    NO_POSTGRESQL_CONTACT_BY_REVIEWER
    VRES_165_PERSONAL_C2_REVERSIBLE_MODEL_SWITCH_DESIGN_REVIEW_COMPLETE

No provider E/V/W or T2-resistant anchor was tested. Reviewer stated VRES_PERSISTENCE_WARNING and VRES_REPLY_GUARD_WARNING were displayed; it made NO Vres task/DB call and did not fix persistence. These are separate task-continuity issues, not a source test.

## 4. Next exact design and review checkpoint

1. Author a DISTINCT docs/architecture/VRES-165-PERSONAL-C2-REVERSIBLE-CHAIRMAN-MODEL-CHANGE-DESIGN-V1-2026-10-26.md. Do **NOT** rewrite the reviewed immutable v0 blob **b08ef92fc72df90651545503c638923eec157412** or independently accepted B2B R3 blob **110ccffcbc1c1f00f5b674b4836fed432708f4ea**/erratum **e7536be90246ad3894befb8a2f5e158d3088028d**.
2. v1 must start by acknowledging prior **DESIGN_REVISE B-01** and exact reviewer gaps, carry a B-01 / D-1..D-7 disposition matrix, declare frontmatter-only P2 candidate invalid as an install target until coordinated body/pins/test disposition, and include explicit tuple/revocation/history/manifest-versioning correctness.
3. Commit strictly documentation paths (this reviewer handoff ADD, separate v1 design ADD, canonical index MODIFY); verify doc feature source HEAD **7ac041018d4ec5a06be07318ecce5e140faccd91** unchanged, no install/PG/user-global/model effects.
4. NEXT operator new guarded Windows docs detached review checkout at exact new docs SHA and fresh Claude DESIGN-ONLY Read/Glob/Grep focused on v1 changes and source-mismatch limits; new independent verdict DESIGN_ACCEPT / DESIGN_REVISE / DESIGN_BLOCKED with marker **VRES_165_PERSONAL_C2_REVERSIBLE_MODEL_SWITCH_V1_DESIGN_REVIEW_COMPLETE**. An independent design acceptance never implies positive authority, source test or model switch.

**HARD HOLDS:** LIVE_SCHEMA_048_INCIDENT=OPEN, ABSOLUTELY NO PostgreSQL even SELECT. The user-installed PERSONAL current-user Chairman remains Sonnet/high LF/24208 bytes SHA **a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73**, release **20261022172833-4d82147b**. The invalid frontmatter-only diagnostic Opus/medium P2 candidate digest is **b73e7497454a464f6b6bc1df00f42422696da786a07eb2936ae73ad73abedf54** NOT installed. Original F1/#165 OPEN; real trusted publisher/E/V/CAS/W/loader/host attestation missing. No vault/credentials, Fable/provider, global Claude hooks/settings/plugins changes, installer, signing, production merge or PR, physical #169 live trial or release. D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 blocked, L-04 OPEN, PA-01..08 incomplete; original V-01..V-42 program roadmap and all older independently accepted/rejected SHA/test/procedure evidence remain in canonical continuity index.
