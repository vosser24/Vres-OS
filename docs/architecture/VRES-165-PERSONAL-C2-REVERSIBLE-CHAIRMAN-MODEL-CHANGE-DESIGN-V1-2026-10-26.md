# Vres-OS #165 — PERSONAL C2 reversible Chairman model-selection DESIGN V1 (separate revision after v0 DESIGN_REVISE)

**Design date:** 2026-10-26, Europe/Athens.
**Repository:** vosser24/Vres-OS.
**Canonical docs branch:** docs/chatgpt-continuity-20261023.
**Status:** **C2_D0_DESIGN_V1_DRAFT / INDEPENDENT_V1_DESIGN_REVIEW_NOT_RUN / TESTS_NOT_RUN / SOURCE_MODIFICATION_NOT_RUN / NO_AUTHORITY_ISSUED / NO_MODEL_ACTIVATION**.
**v0 independent reviewer verdict:** **DESIGN_REVISE**, v0 original Git blob **b08ef92fc72df90651545503c638923eec157412**. Preserve the ORIGINAL v0 artifact and review; do not rewrite its SHA.
**Exact historical reviewer marker:** VRES_165_PERSONAL_C2_REVERSIBLE_MODEL_SWITCH_DESIGN_REVIEW_COMPLETE. The marker named v0, not this new v1.
**Next new independent marker:** VRES_165_PERSONAL_C2_REVERSIBLE_MODEL_SWITCH_V1_DESIGN_REVIEW_COMPLETE.
**Scope:** DESIGN ONLY of an eventual reversible single-user Chairman configuration release. No current installed file, global settings, provider or PostgreSQL interaction. Future E/V/CAS/W trusted authority remains unavailable and is not supplied by a design.

## 0. Read first and reviewer finding disposition

Read docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md and docs/handoffs/VRES-165-PERSONAL-C2-D0-V0-INDEPENDENT-DESIGN-REVISE-AND-V1-REPAIR-2026-10-26.md, then this V1 and:
- Immutable V0 design blob b08ef92fc72df90651545503c638923eec157412 (historical REVISE).
- Previously independently accepted DENY-ONLY R3 design: docs/architecture/VRES-165-B2B-TRUSTED-CHAIRMAN-AUTHORITY-CONTRACT-R3-2026-10-26.md, blob **110ccffcbc1c1f00f5b674b4836fed432708f4ea**.
- Mandatory R3 postreview erratum docs/architecture/VRES-165-B2B-R3-POSTREVIEW-ERRATUM-2026-10-26.md, blob **e7536be90246ad3894befb8a2f5e158d3088028d**.
- Current-user installed P2 bytes observation: docs/handoffs/VRES-165-PERSONAL-C2-INSTALLED-CHAIRMAN-MANAGED-RELEASE-BYTES-READONLY-PASS-AND-REVERSIBLE-C2-DESIGN-NEXT-2026-10-26.md.
- C1 R1 source/test independent OFFLINE_ACCEPT and manual source-checkout READ-ONLY preview at source SHA 7ac041018d4ec5a06be07318ecce5e140faccd91; this did NOT approve an installed model.

### V0 independent Claude finding --> V1 normative disposition

| ID | Claude v0 finding | This v1 decision and STOP |
| --- | --- | --- |
| **B-01 BLOCKING** | Sonnet-default doctrine and hardcoded Sonnet test pins contradict only-frontmatter Opus candidate | **§2, §3.** REQUIRES coordinated policy-aware body and test-pin disposition before any release eligibility. Original P2-only Opus frontmatter digest b73e... is **DIAGNOSTIC_ONLY_INVALID_FOR_INSTALLATION**; no valid new candidate hash exists now. |
| **D-1** | Reviewer saw old docs checkout installer, not original P2 manifest sources | **§1, §4.** Provenance explicitly segregates reviewer reads from ChatGPT separate P2 GitHub reads; no claim Claude read original P2. |
| **D-2** | Full installer has disproportionate venv/pip/doctor/global settings/launchers/PATH effects | **§4.** Preferred FUTURE **minimal plugin-policy-only new immutable release/transition**, reusing already installed runtime if independently proven compatible. Existing full install.ps1 is NOT a safe switch API. |
| **D-3** | Abandoned Opus proposal causes B1 adjacent-repeat block | **§8.** User-visible blocked retry; no fake Sonnet hop; real interposed choice needs its own full E/V/CAS. |
| **D-4** | Revocation after first installed write missing | **§7.** Explicit row keeps Q pending/RECOVERY until trusted installed+LOADED original G and protected ABANDON or fresh W-backed RESTORE_GOVERNING. |
| **D-5** | Plugin/pointer/journal/release tuples not enumerated | **§6–§7.** State matrix over observed pointer P, managed plugin M, pending journal J and release R, with fail-closed reconciliation; old same-user journal NOT protected authority. |
| **D-6** | Need explicit user CHOICE whether to consider separate non-F1 personal experiment | **§9.** CHOICE NOT MADE; no shortcut currently approved. Separate independent design/permission only if user later explicitly asks; NEVER call it #165/F1 success. |
| **D-7** | Bounded data allowlist and two-screen E/W proportionate | **§5 and §9.** Retained without enterprise ceremony additions. |
| **Manifest versioning** | Older verifier/new unknown schema refusal underexplained | **§4.** Original P2 artifact VERSION=2 strict; future policy-bound new version demands explicit parser/schema and older verifier hard refusal. |

## 1. Exact scoped evidence: original P2 installer vs docs checkout

**User/operator-reported observed managed Windows installation**, now supported by exact two-file snapshot:
- Current-user Vres active pointer release **20261022172833-4d82147b**, product Vres-OS, exact current-user managed plugin root.
- Managed Chairman file AND matching release distribution Chairman copy both **sonnet/high**, **LF**, **24208 UTF-8 bytes**, **SHA-256 a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73**.
- This is FILE-LEVEL identity, not host/session model or independent user intent attestation. The pasted Windows excerpt starts after the script's initial environment preamble, so do not claim those lines were present.
- ChatGPT separately read the ORIGINAL immutable P2 source commit **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c**, agent file Git blob **6f2239c4dd0d52090d31415c17f763505f93b900**, and computed the same SHA-256 over 24208 LF UTF-8 bytes. This is proof of source-to-observed digest consistency, NOT provider-signed release trust.

**Source provenance distinction explicitly mandated after D-1:**
- Original P2 commit 82c82430... has **install.ps1 blob 29a5f0da235021cc8c5607eb92218e5ea98145fa**, **src/vres_os/release_artifact.py blob ddfc1beacad98199b489dc6f56456baf4d519c6a**, **src/vres_os/install_recovery.py blob 1c0d585645280678af4875f2842a3350f9805e0a**. ChatGPT verified P2 contents separately via GitHub.
- The independent v0 Claude reviewer read an OLD DIFFERENT install.ps1 in its docs-only worktree. That file creates a venv/pip etc. but does NOT have the later P2 pinned release-artifact manifest; the P2 Python source modules were absent there. Claude truthfully COULD NOT independently verify the original P2 implementation and this v1 does not attribute any such verification to it.
- The original P2 installer at lines 186..307 ALSO performs staging and substantial **venv/pip/dependency/doctor/Claude global rules/statusline/compaction/launchers/PATH** operations. Both observations support a minimal PERSONAL policy-only change path; executing the current old installer is not approved.
- In original P2 release_artifact.py, **FORMAT = vres-personal-release-artifact**, **VERSION = 2**, **OBJECT_FORMAT=sha1**. Its load_manifest refuses format/version mismatch, unexpected each-file entry keys, wrong file SHA shape, malformed path or unmatched scope. Stage uses immutable Git object bytes; modified rendered plugin bytes are NOT equal to their originally recorded Git blob/SHA. This is an actual current P2 behavior verified by ChatGPT, not a claim by Claude, Git alone cannot establish an independently trusted publisher identity.

Current accepted C1 R1 source **7ac041018d4ec5a06be07318ecce5e140faccd91** has a DIFFERENT Chairman source plugin Git blob **64cba93d6f69960350a0006b594734288f087ccc**. C1 one-shot Windows SOURCE-checkout CRLF candidate digest **d0cd8821fcddb6ef76344d513e0f33595ab6fc2954db800c5960c1198d64550f** is NOT the original P2 installed-release candidate. Never copy a source preview or C1 body over a P2 managed plugin.

## 2. B-01 CLOSED AS A DESIGN CONTRACT — a frontmatter-only candidate is ineligible

### 2.1 Source-grounded doctrinal and test-pin contradiction

**Original installed P2 agent**, plugins/vres-os/agents/chairman.md, Git blob **6f2239c4dd0d52090d31415c17f763505f93b900**:
- Lines 4–5 source frontmatter model: sonnet / effort: high.
- **Line 74 explicitly states the Chairman itself runs on Sonnet as the default control plane** and Opus is never the default shell or routine routing model. Only changing the two YAML fields to Opus/medium makes this exact original body internally contradictory.

**Existing source tests** tests/test_aigo_orchestration_contract.py, Git blob **e50c4bfa3a7920b91bdfefbc2bd14f1e9a14fee8**, **lines 109 and 182** each demand literal **model: sonnet** in the Chairman SOURCE text. Its line 183 still demands Fable/high for routing arbiter, line 184 Sonnet for routine worker, line 185 Opus/high for deep worker; those worker/validator pins are PROTECTED and do not change with Chairman control-plane selection. The independent Claude review located line 182; ChatGPT separately verified both Sonnet assertions against the immutable source.
 
**Accepted Phase A** src/vres_os/chairman_policy.py blob **36e62d6a2712ac305fd4070bac658b94d61d155e** intentionally preserves the entire SOURCE body when materializing a caller-specified policy. Existing tests/test_chairman_policy_materialization.py blob **4a9e2ea4540bd074351179fb0a68a677acd113f8** lines 140–145 validate that pure frontmatter-only rendering contract; DO NOT weaken/alter the accepted materializer to silently patch body text.

**Hypothetical hash calculation remains accurate but INVALID for policy installation:** If ONLY model/effort fields of that ORIGINAL installed P2 template change, computed Opus/medium LF 24208-byte SHA-256 is **b73e7497454a464f6b6bc1df00f42422696da786a07eb2936ae73ad73abedf54**. This is now classified **DIAGNOSTIC_ONLY_INVALID_FOR_INSTALLATION: DOCTRINE_AND_TEST_DISPOSITION_MISSING**. It cannot be put in approved release manifest, E, V, W, installation authority or host "active" claims. It never existed as an on-disk candidate, and no user decision or checksum upgrades it. **A VALID Opus Chairman release candidate digest is UNDETERMINED as of v1.**

### 2.2 Chosen resolution, not just a disclaimer

**V1 chooses coordinated policy-aware TEMPLATE-BODY and TEST-contract amendment in a FUTURE separately reviewed source commit.** The other v0-reviewer choices—silently overriding old doctrine or knowingly shipping an inconsistency—are NOT chosen for governed #165.

Future source tranche MUST:
1. Author a separately versioned and reviewed Chairman agent SOURCE template body whose **control-plane model/effort are determined by a separately approved installed policy**, not fixed prose. Required disambiguation: a model family selected for Chairman control-plane is DISTINCT from a governed **Opus-expert routed worker**; ordinary deterministic worker assignment still uses Sonnet; ambiguous routing and protected validator remain Fable/high; every actual Opus worker escalation still requires protected Fable validation. Do NOT preserve "Opus is never the default shell" unqualified if an authorized Opus Chairman can be the default user-facing shell. Proposed clarifying sentence for consideration, NOT committed implementation: "Chairman's control-plane family and effort follow the independently approved, installed Chairman policy; this does not promote Opus workers into routine deterministic routes or bypass any protected Fable validation required for Opus workers."
2. Preserve the historical P2 source bytes and release as immutable provenance; the new policy-aware template body is a NEW source Git blob with different content and a distinct approved release identity. Only AFTER reviewing that body may the existing Phase A pure frontmatter materializer produce an Opus/medium candidate from the new input. No in-place manipulation of installed 20261022172833-4d82147b.
3. Review every impacted static test contract. At minimum: tests/test_aigo_orchestration_contract.py **lines 109 and 182** and policy materialization tests. If source template frontmatter continues to be Sonnet/high as a pre-policy default, retain Sonnet SOURCE-only assertions but RELABEL them as template-baseline assertions and ADD tests on the DERIVED installed-release plugin with **Opus/medium**. If template becomes policy-neutral or source frontmatter changes, CHANGE the old static source assertions with clear reviewer-approved semantics. Do not simply delete tests or globally replace Sonnet with Opus.
4. Preserve or strengthen tests that the separately routed Sonnet worker is pinned, deep Opus worker remains appropriate, Fable/high arbiter and validator cannot be demoted; verify current source header/body policies do not contradict derived rendered policy. A future "coordinator Opus" change MUST NOT silently change the route complexity thresholds or remove required Fable protection.
5. Reject any candidate whose body contains a live contradictory default-shell / control-plane claim, unless the contradiction is **explicitly adjudicated and approved as a new reviewed policy-body change**, with exact source/renderer/policy and test evidence. Planner cannot merely trust user-supplied "body reviewed" text or an agent-made assertion; before any positive release eligibility, independently verified candidate/template+tests and real external F1 authority must exist. If review is unavailable, return **REFUSED/INDETERMINATE** and keep preview diagnostic-only.
6. Future source-review coverage scans exact file body, explicit routing-doctrine invariants and impacted tests, not only header line equality. Record source-template SHA and generated DERIVED candidate SHA separately. Any old P2 diagnostic b73e... digest remains historical, not accepted.

**No code or test file was changed in this v1 design.** B-01 is resolved at the DESIGN LEVEL only by a concrete must-do future coordination contract; the code and valid release candidate remain BLOCKED pending separate source commit and review.

## 3. Candidate readiness states: bounded, non-authoritative, no oracle

Pure read-only planning may show:
- SOURCE_BASELINE_IDENTIFIED (untrusted observed bytes, source body and SHA, not proof of authority);
- PREVIEW_DIAGNOSTIC (candidate hash may be computed only for display, explicitly NOT releasable);
- POLICY_BODY_CONFLICT / SOURCE_TEST_PIN_UNRESOLVED / RELEASE_SCHEMA_UNSUPPORTED / TRUST_PROVIDER_MISSING (closed neutral REFUSED or INDETERMINATE reason);
- separately externally REVIEWED_TEMPLATE_AND_TESTS_CLAIM (a claimed descriptor, STILL not authority); no local positive "safe to install" result unless an entirely separate real trusted provider is built and reviewed.

The first C2-D1 pure planner, if later authorized, takes **caller-supplied bytes and explicitly claimed descriptors only**, reads no filesystem/registry and runs no process/provider. It MUST refuse installation eligibility if body/test-pin disposition unresolved, while still optionally displaying a clearly invalid diagnostic digest. Avoid a boolean "can_install" or return value that treats Indeterminate as nonblocking. No permit/authorize/install/release type is exposed by C2-D1 or B2B-1.

Real release eligibility will be a DISTINCT future protected positive-verification service after review, never inferred from the absence of known local diagnostic failures.

## 4. D-1 / D-2: minimal immutable policy-bearing release transition, truthful manifests and old-verifier refusal

**Preferred FUTURE PERSONAL deployment route:** a **minimal new immutable plugin-policy release** with an explicitly versioned artifact binding and a supported, reviewed installer transition that reuses the already installed Vres Python runtime/venv, launchers, global CLAUDE.md, native hooks/settings, PATH and database state if independently proven compatible. Do not rerun the full legacy installer solely to change Chairman family: its venv/pip/doctor/Claude global config/launchers/PATH operations are disproportionate and would increase incident exposure. **No dedicated policy-only updater exists as of v1.** If compatibility cannot be established without a full runtime update, STOP pending separately authorized full release design; do not silently expand scope.

A minimal "plugin-only" transition still requires a truthful NEW immutable **RELEASE/POLICY IDENTITY**, not an untracked edit of managed plugin. It must reconcile the release distribution copy, manifest, current-user managed plugin, pointer, journal and rollback provenance. Because the current P2 installer does not support this path, packaging/installer artifacts and separate physical tests must be authored in future tranches.

**Existing P2 manifest v2 is strict (source-grounded):**
- FORMAT "vres-personal-release-artifact"; VERSION=2; source_commit/source_tree, git_blob and SHA-256 per file.
- Current P2 v2 stage copies actual approved Git object bytes and verifies tree. It CANNOT claim a rendered Opus plugin with a different SHA is identical to an original Sonnet Git blob.
- Current P2 v2 load_manifest REFUSES any version !=2 and fixed entry-key mismatch. Reviewer of the docs-only checkout did NOT see this P2 source; these are separate ChatGPT GitHub observations.

**Versioned future plan (NOT IMPLEMENTED):**
1. Add an explicitly named distinct policy-artifact schema/version (e.g. a future VERSION=3), NOT a silent v2 extension. Bind immutable reviewed source-release commit/tree, original policy-aware template Git blob/hash, exact renderer module identity, canonical requested Chairman family/effort/version and policy digest, trusted publisher provenance when available, unchanged worker/validator pin identities, actual derived output digest/byte count/newline type and exact target plugin release ID. Distinguish SOURCE template bytes from DERIVED installed agent bytes in separate typed fields.
2. An **existing old v2 installer/verifier** encountering a future policy-artifact v3 must **REFUSE** unsupported version, not ignore new fields, assume v2 source identity, fall back to Sonnet, or overwrite the pending release. The future v3 verifier must REFUSE unrecognized versions including any future v4, unknown/duplicate/missing keys, mismatched bindings, unknown renderer semantics, wrong original template/body/test disposition, cross-type digests, mixed newlines and any target/manifest version substitution.
3. Backward read-only inspection of a historical valid v2 P2 release remains permitted under v2 semantics; do NOT use that v2 manifest to approve v3 rendered bytes. A v3 source-publisher/validator can choose narrowly reviewed backward v2 history references but cannot coerce them into signed, authenticated release evidence.
4. Future release packaging may choose a reviewed **pinned pre-rendered Git blob** instead of derivation at install. It still needs a separately reviewed provenance chain that ties the coordinated doctrine/test changes and requested policy to exact bytes; alone it is not F1 consent or an installed model switch.
5. The plugin-only updater must prove the CURRENT runtime/launcher is compatible with the NEW plugin policy artifact and unchanged plugin contracts. If it would need to touch other global Claude files or restart Vres, disclose exact extra paths and obtain separate approval before expanding; never silently run pip, doctor, bootstrap, migrations or network operations.

No v3 manifest or plugin-only updater is created by v1. Any future test uses synthetic/disposable managed roots and independently reviewed no-DB fences, not the installed personal release. **LIVE_SCHEMA_048 forbids PostgreSQL even SELECT**.

## 5. Trusted F1 operator and release authority remains a hard STOP (unchanged R3)

The independently reviewed B2B R3 design blob 110ccffcbc1c1f00f5b674b4836fed432708f4ea is **DESIGN_ACCEPT strictly for B2B-1 DENY-ONLY**, with mandatory postreview erratum blob e7536be90246ad3894befb8a2f5e158d3088028d. Neither document supplies real trusted positive authority.

Before ANY governed user-current-model switch, a future trusted implementation must:
1. Independently authenticate trusted release publisher/root, a valid enrolled H_0 or currently protected H_n, last completed governing policy/pins G, latest immutable proposal history L, pending intent Q and exact machine/SID/install target. A locally matched SHA is not a T2-resistant authenticated genesis or publisher.
2. Canonically append exactly one B1 policy proposal C to protected L (special independently enrolled H_0 case), never overwrite old history, silently rebase abandoned proposals, forge intermediate policy hops or assume G=L. If Q=PENDING or RECOVERY, block a new policy proposal.
3. Obtain independent provider-rendered, user-presence verified proposal E with exact old G/current L/new C, policy-aware template/test/release changes, candidate digest, protected worker/validator pins, target/principal/alias rules, nonce and freshness. A ChatGPT user message, yes/no prompt, Claude permission dialog, JSON or same-user DPAPI record is NOT E.
4. Independently fetch protected sources and validate V under pre-state G/validated old Fable/high pins, protected E and policy/template artifacts; enforce distinct digest domains. An agent's "Fable PASS" text is never trusted V.
5. Perform independently protected linearizable H_n CAS atomically consuming E/nonce and creating pending Q. This is NOT an installation.
6. Get a DISTINCT fresh user-approved trusted installation warrant W showing current G, pending Q, exact immutable policy plugin release, new digest, alias rule, target and recovery implications. E is consumed and cannot serve as W. Check trusted freshness (proposed max age 300s for E and separately W only under real provider-owned time), cancellations, revocations and trusted publisher withdrawal at the actual final boundary.
7. Deploy only through a separate reviewed B2C trusted actor after rechecking target/release, with actual managed-byte readback and independent loader/per-use enforcement; perform protected COMPLETE_INSTALL bound to exact Q/E/V/W and observed release bytes, not just mutable files. Exact physical model alias/effort, fallback and protected validator family require independently qualified host evidence later. If no provider/warrant/loader exists, STOP with REFUSED/INDETERMINATE.

F1 positive trusted authority, publisher, H0, consent service, protected Fable evidence and B2C are NOT implemented/authorized. No C2 diagram/candidate digest/readback labels alone may grant real model switching.

## 6. D-5: concrete P/M/J/R file-and-pointer reconciliation matrix

Define four independent file-level observations (none are protected authority):
- **P (active pointer)**: O = names prior approved P2 release; N = names newly intended policy-plugin release; U = malformed/missing/unexpected.
- **M (current-user managed plugin byte-set)**: O = exact prior P2 plugin/Chairman hashes; N = exact separately verified candidate release plugin bytes; X = missing/partial/drifted/unexpected.
- **J (pending install/recovery journal)**: 0 = absent; 1 = present and structurally valid; X = missing where the protected install stage expects it, malformed, untrusted or tampered. Existing same-user pending-install.json is diagnostic ONLY, never a trusted authorization root.
- **R (immutable candidate release staged)**: 0 = absent; 1 = complete and independently verified plugin-policy release/distribution/manifest; X = incomplete/unverifiable/reparse/withdrawn/stale.

For a future explicit installed change, ALL four snapshots must be bound to the independently protected intent Q, E/V/W, target, publisher and last completed G. An old/same-user pointer is NEVER independently trusted G. Combinations below are NOT instructions for executing repairs now.

| P | M | J | R | Meaning and fail-closed C2 behavior |
| --- | --- | --- | --- | --- |
| O | O | 0 | 0 or 1 | Stable old Sonnet/high snapshot, if genuinely verified and no protected pending Q. A staged inert release R=1 does NOT imply consent. |
| O | O | 1 | 1 | New release prepared and journal opened but no managed write yet: **BLOCKED pending protected reconciliation**, discard inert staging only if old G identity independently reverified and protected state allows it. |
| O | X | 1 | 1 | Old plugin was moved/partial, new plugin not proven; prior pointer still old. **RECOVERY/BLOCKED**; cannot say current old or new model; protected W-backed RESTORE_GOVERNING or equivalent independent recovery. |
| O | N | 1 | 1 | New plugin copied/verified while active pointer still OLD: **BLOCKED**. No transient "Opus active", no clearing Q; protected installed/load inspection and distinct recovery/continuation decision. |
| N | N | 1 | 1 | New pointer published but journal still exists (possibly global installer step incomplete). **BLOCKED** until independently verified manifest, loader, W and protected COMPLETE; no automatic journal deletion. |
| N | N | 0 | 1 | Candidate looks structurally complete from files only. **NOT TRUSTED COMPLETE** until independent Q/E/V/W, loader/per-use evidence and protected completion CAS; absence of same-user journal proves nothing. |
| N | O | 0 or 1 | 1 | New pointer but old managed plugin: **BLOCKED** release mismatch, no activation/readiness claim, protected reconciliation needed. |
| O | N | 0 | 1 | Old pointer with new plugin and missing journal: **BLOCKED unexpected orphan**; no heuristic overwrite or fabricated intent. |
| O or N or U | X or unknown | 0, 1 or X | 0, 1 or X | Any unmatched hash, tamper, absent expected release, journal disagreement, reparse/alias mismatch, withdrawn release: **REFUSED/BLOCKED**, no automatic repair or model-switch success. |

Original P2 installer sequence (ChatGPT separately verified original P2 install.ps1 lines 184..310, NOT read by Claude in its docs checkout): stage release R=1 -> recovery snapshot -> same-user pending J=1 -> move old plugin to backup (transient M=X) -> copy and verify new M=N -> update launchers -> publish new pointer P=N -> change global Claude rules/statusline/autocompact -> rewrite P=N -> delete journal J=0. It cannot atomically publish pointer and managed plugin together, and repeats pointer writes. The **new narrow plugin-only installer** must not copy these global side effects automatically and must include an independent protected journal mechanism if it claims F1-consistent recovery.

Any observed P/M/J/R status transition should be treated as a **point-in-time physical file snapshot**, not proof that Claude actually loads Opus, not completed G and not authority to mutate. Future reversible design cannot assume an old trusted event still valid or an unprotected file can clear Q.

## 7. D-4: explicit revocation after FIRST installed-file write and full crash ordering

At every stage, the protected service must separately recheck event validity and current trusted head. Pending policy Q is never cleared solely by restoring bytes locally.

| Future interruption/revocation boundary | Required protected state and permissible claim |
| --- | --- |
| READ-ONLY preview or inert staging before any CAS | G and installed original bytes unchanged. No E/W authority, discard inert copy only. |
| E refused, V refused, H_n CAS failed | No pending permission/installed change. Do not retry or interpret refusal as partial success. |
| Protected H_(n+1) Q=PENDING but no W | G remains last completed Sonnet/high. No installed write, no new competing proposal while Q pending. |
| W issued but BEFORE first active file change, then revoked/expired | Abort without any installed write, mark failed attempt and protect pending disposition; W unusable again. New independent terminal/recovery event needed. |
| **REVOKE/EXPIRE AFTER first managed plugin/active-pointer write, before final load/completion** | **Q MUST REMAIN PENDING or protected RECOVERY; never clear on a same-user rollback.** If independently protected readback proves installed AND runtime-loaded bytes equal exactly last completed G, a separate independently authenticated protected ABANDON may clear Q with a forward epoch; otherwise require a separate fresh W-backed RESTORE_GOVERNING under independent trusted write/load recovery and protected reconciliation. No old E/W reuse. |
| Files report P=N, M=N but protected COMPLETE_INSTALL not recorded | No authority to claim new G. BLOCKED pending exact Q/E/V/W binding plus trusted loaded bytes, then protected forward completion or new recovery. |
| Protected intent recovered with corrupt/missing journal | Refuse ordinary replay; protect immutable evidence, require new authenticated incident/recovery decision, no auto promotion/demotion. |
| Physical loaded model or provider alias differs from intended | Record FAILED/DEGRADED, never "Opus active"; protect G/Q state and require separate reviewed remediation. |
| Future intentional revert to Sonnet/high after completed Opus policy | NEW candidate C and new E/V/CAS/W, preserve latest L, do NOT rewind history or reuse old consent. Original immutable P2 bytes may be an intended CONTENT target, not a replayable historical approval. |

A rollback described as "automatic" is forbidden unless separately reviewed with real protected authority, crash-safe journal and load verification. Windows multi-file changes cannot be advertised atomic without a demonstrated transactional implementation; a pre-install backup is a recovery material, not evidence of protected approval.

R3 postreview erratum R3-N01 specifically requires not clearing Q after partial write unless original completed G installed AND LOADED state independently matches, or a separately warranted RESTORE_GOVERNING is performed. R3-N02 requires COMPLETE_INSTALL to bind the exact proposed Q/E/V/W/render/release, never untrusted file bytes alone.

## 8. D-3: honest abandoned Opus retry outcome, no fabricated intermediate proposals

**Case:** G=Sonnet/high from original completed release; latest appended L entry was a proposed Opus/medium C that is subsequently ABANDONED or REVOKED before installation; Q eventually has a protected independent disposition and G still remains Sonnet/high. L includes the abandoned Opus entry because immutable proposal history NEVER rewinds.

**B1 adjacent no-repeat consequence:** an immediate next Opus/medium entry identical in model/effort to last L is **REFUSED as an adjacent duplicate**, even though G is Sonnet/high. The interface must inform the user, plainly: "The latest Opus proposal was abandoned; repeating the same adjacent proposal is blocked by the history contract. No switch has happened. A separately reviewed history-policy change or genuine, independently warranted different intervening policy would be necessary." No invented automatic dummy Sonnet/high hop to make Opus appear permissible.

If a real separate user-desired policy change naturally intervenes, it needs its OWN proposal E, protected V, CAS (and W if installed) before later subsequent Opus can be contemplated. That is not a mandated workaround or automatic upgrade path. If policy/lineage cannot represent an honest retry, return REFUSED/BLOCKED pending future separately reviewed history-schema revision; do not silently drop abandoned entries, fake counts or infer new consent from old E.

Likewise a completed Opus->Sonnet revert is a genuine NEW policy proposal, NOT a roll back of proposal ledger L, and must follow full protection.

## 9. D-6/D-7: separate non-F1 personal experiment decision and proportional UX

The reviewer raised a legitimate potential PRODUCT CHOICE, not a recommendation to bypass protections:

**USER_DECISION_ON_NON_F1_PERSONAL_EXPERIMENT=NOT_MADE.**

Under existing protected issue #165, positive authority cannot be issued by current same-user tooling or ChatGPT. The user has NOT authorized an alternate experimental switching mode. We neither build nor run one based on the current "proceed" to DESIGN revision; DO NOT relabel the F1-mandated model-governance switch as a less strict personal experiment behind the scenes.

If the user later explicitly requests a distinct LOCAL EXPERIMENT outside F1/#165 acceptance, FIRST draft a separate user-reviewed design that truthfully labels what is and is not guaranteed, its reversible target and current-user risk, with no protected authority claim, no database contact, no global/credential/provider acts without distinct permission. That request would NOT complete #165/F1 or override its release/governance rules. No such alternative is approved in V1.

For the protected version, present two concise, independently rendered screens **E for proposal** and **W for actual installation**, showing meaningful old/new, source/body/pins/release changes, exact target and reversal consequence. Two stages match different consequential actions and are proportionate even for one current Windows user. A SOURCE preview needs neither privileged screen and must remain non-authoritative.

## 10. Implementation slices AFTER independently accepted v1, all future and not authorized now

**C2-D0 V1 — only these docs and independent design review:** immutable v0 DESIGN_REVISE preserved; THIS v1 draft separately committed, not reviewed/tested yet. Zero source changes, no host task/test calls.

**C2-D1 — smallest candidate-only pure offline planner (FUTURE, NOT APPROVED YET):** caller-supplied original/source template bytes, explicit claimed policy bytes and doctrine/test-pin descriptor, deterministic digest output; no file/registry/network/process/clock/crypto-keystore/PG/Claude imports. If doctrine or test-pin disposition UNRESOLVED, return REFUSED/INDETERMINATE and label any hash DIAGNOSTIC_ONLY, never install-ready. Reuse accepted Phase A materializer without weakening body-byte invariants. Only if later authorized, create a **new source SHA** and one focused test module, independent STATIC review first, one selected Windows offline pytest behind protected conftest, then independent OFFLINE_ACCEPT. No trusted provider permit output.

**C2-D1B — separately reviewed coordinated source policy-aware template/body and test contracts (FUTURE, NOT APPROVED):** author changed template body and narrow test changes/new installed-artifact fixtures, verify no affected routing worker/validator pins, immutable P2 remains preserved. Candidate real rendered SHA only after this and immutable source/policy/release proven. No moving/running installed Vres.

**C2-D2 — real independent trust/provider and release-publisher design (FUTURE BLOCKED):** review authenticated H0/anchor, true T2-resistant provider E and separate W, protected validator V and current prestate protected pins, linearizable CAS/revocation, genuine reviewed release publisher, unknown version refusal and effective runtime model load-path. R3 NF-05..NF-10 still real mandatory integration gates. No fake signer/DPAPI/local-authorized boolean.

**C2-D3 — policy-only protected release transition (FUTURE BLOCKED):** author future policy-artifact version and minimal plugin-only transition, manifest-compatible immutable release ID, exact baseline/current-header/source/body/pins, protected old/new snapshots, provider warrant W, P/M/J/R reconciliation with interruption tests. Preserve venv/launchers/global config unless explicit separately approved compatibility proof demands changes. Never run old install.ps1/doctor or the schema-048 database. Simulate only in isolated disposable Windows profile after separately scoped approvals and static-first review.

**C2-D4 — trusted loaded and physical model validation #169 (FUTURE BLOCKED):** the physical resolved Opus family/medium effort cannot be inferred from managed file; validate actual native host launcher, override precedence, no silent fallback, routine Sonnet workers, Opus deep workers, Fable/high arbiter/validator using trustworthy host evidence under separately approved conditions. Never claim source/test/designed policy was installed or real provider usage measured in v1.

## 11. Independent v1 design review focus and immutable review verdict

A fresh Claude Code session from a NEW guarded detached docs checkout at the eventual exact v1 docs commit should:
1. Read THIS v1 in FULL and v0 + reviewer findings (handoff) enough to verify B-01/D-1..D-7, R3 norm and erratum.
2. Independently challenge **§2**: does mandatory source template body + unit tests disposition solve real P2 and test line109/182 contradictions? Is original P2-only digest expressly invalid for installation? Does preserving Phase A pure body-byte semantics make sense with a separately amended template?
3. Challenge **§4**: P2 exact VERSION=2 checked from GitHub by ChatGPT, not Claude's historical docs-worktree; does proposed v3 or distinct schema reject unknown/older verifier safely and make plugin-only pathway truly supported without current installer side effects?
4. Challenge **§6/§7** P/M/J/R and post-first-write revocation, exact safe Q recovery, no false all-files-atomic promise or same-user journal authority.
5. Challenge **§8** adjacent repeat and legitimate independent Sonnet intervention only; no dummy policy bypass.
6. Challenge **§9** non-F1 experimental choice explicitly user undecided; no auto fallback or unauthorized activation.
7. Confirm all positive F1 E/V/CAS/W, independent release publisher/loader and physical host model observation BLOCKED, historical B2B R3 only accepted for offline DENY-ONLY.
8. Return **DESIGN_ACCEPT / DESIGN_REVISE / DESIGN_BLOCKED**, file+line findings and exact full vs partial file coverage, no Git/source/code/pytest/DB. Required statuses DESIGN_ONLY; TESTS_NOT_RUN; SOURCE_MODIFICATION_NOT_RUN; NO_AUTHORITY_ISSUED; NO_MODEL_ACTIVATION; NO_POSTGRESQL_CONTACT_BY_REVIEWER. End marker **VRES_165_PERSONAL_C2_REVERSIBLE_MODEL_SWITCH_V1_DESIGN_REVIEW_COMPLETE**.

A DESIGN_ACCEPT means v1 is conceptually acceptable for a separately scoped inert C2-D1 proposal, NOT software acceptance, F1 consent, actual Opus activation, new installer, OS/provider trust or permissions.

## 12. Canonical program integrity, safety and next session

**LIVE_SCHEMA_048_INCIDENT=OPEN — ABSOLUTELY NO PostgreSQL contact, even SELECT.** No Vres task/DB/bootstrap/health/doctor/recovery to investigate Claude VRES_PERSISTENCE_WARNING or VRES_REPLY_GUARD_WARNING. D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 blocked, L-04 OPEN, PA-01..PA-08 incomplete. No real credentials/vault, signing, global Claude settings/hooks/plugins mutation, native provider/Fable invocation, production main merge, installer or physical #169 host action.

Installed PERSONAL release remains last observed **20261022172833-4d82147b**, managed Chairman Sonnet/high LF/24208 bytes SHA256 **a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73**; physical running Claude model UNKNOWN. Original F1/#165 positive trusted authorization OPEN. Only accepted source at feature HEAD **7ac041018d4ec5a06be07318ecce5e140faccd91** is C1 R1 independent OFFLINE_ACCEPT read-only preview, 29 selected Windows PASS/exit0 plus manual source preview PASS, NOT a deployed switch. Prior old C1 at c545556a4ba9ba48f140e7379da960708a7f3c8d had Windows pytest EXIT1 and remains nonaccepted. C0 pure preview 34 PASS/exit0 OFFLINE_ACCEPT; A1 R2 93 PASS, A1 R1 71 PASS, B2A R3 95 PASS with R3-PROC-01; older source/Phase A/B1/F2/P2-A1 per-SHA accepted/rejected states, B2B R3 denial-only DESIGN_ACCEPT and exact erratum, and all original V-01..V-42 PERSONAL roadmap preserved.

**C2 D0 docs-only transaction:** ADD this distinct V1 design, ADD independent v0 DESIGN_REVISE handoff **docs/handoffs/VRES-165-PERSONAL-C2-D0-V0-INDEPENDENT-DESIGN-REVISE-AND-V1-REPAIR-2026-10-26.md**, MODIFY ONLY docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md on docs/chatgpt-continuity-20261023. Old canonical docs HEAD **384a9adc3a4bfa59c75cad02452c320e51ae7d7d**, tree **3c25db0b7be38f742a7aac10e73340b936b602b7**; feature source HEAD must remain **7ac041018d4ec5a06be07318ecce5e140faccd91**. Require recursive Git old/new tree EXACT these THREE doc paths, no deletions, one-parent unsigned GitHub commit, expected-old-head nonforce move, reread docs and source.

**NEW SESSION RESUME:** v0 independent **DESIGN_REVISE B-01 + D-1..D-7**, immutable v0 SHA b08ef92fc72df90651545503c638923eec157412. ChatGPT independently proved original P2 installed agent body line74 fixes Chairman control plane to Sonnet and tests/test_aigo_orchestration_contract.py SHA e50c4bfa3a7920b91bdfefbc2bd14f1e9a14fee8 pins Sonnet at lines109/182. Phase A renderer intentionally only frontmatter. Hypothetical P2 frontmatter-only Opus candidate b73e7497454a464f6b6bc1df00f42422696da786a07eb2936ae73ad73abedf54 now **DIAGNOSTIC_ONLY_INVALID_FOR_INSTALLATION** until separately reviewed coordinated policy-aware body+tests. New V1 DESIGN DRAFT fixes that contract and detailed P2 provenance VERSION=2, old verifier new version fail closed, minimal plugin-only NEW immutable release preference (NOT implemented), P/M/J/R tuple crash matrix, revocation-after-first-write Q retained, no adjacent abandoned Opus retry/fake Sonnet proposal, non-F1 experiment USER_DECISION_NOT_MADE. No source/tests/provider/installer/global settings/model change. **NEXT** new guarded Windows docs-only detached review checkout at NEW docs SHA and fresh Claude Read/Glob/Grep DESIGN-only v1 review with final marker **VRES_165_PERSONAL_C2_REVERSIBLE_MODEL_SWITCH_V1_DESIGN_REVIEW_COMPLETE**; later design acceptance not installation or F1 authority. LIVE_SCHEMA_048 no PG even SELECT, #165/F1 positive trust and #169 physical host proof OPEN, user-installed release Sonnet/high unchanged, C1 R1 accepted source unchanged, full V-01..V-42 and all accepted/rejected history preserved.
