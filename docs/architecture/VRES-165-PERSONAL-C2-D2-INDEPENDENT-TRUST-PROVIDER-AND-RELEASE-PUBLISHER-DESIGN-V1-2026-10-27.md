# Vres-OS #165 PERSONAL — C2-D2 independent trust/provider and release-publisher DESIGN V1 (V0 DESIGN_REVISE repair)

**Date:** 2026-10-27, Europe/Athens.
**Repo:** vosser24/Vres-OS. **Scope:** one current-user PERSONAL Windows Vres.
**STATUS:** AUTHOR_D2_V1_REVISED_DESIGN_DRAFT / ORIGINAL_V0_INDEPENDENT_DESIGN_REVISE / V1_INDEPENDENT_DESIGN_REVIEW_NOT_RUN / SOURCE_MODIFICATION_NOT_RUN / TESTS_NOT_RUN / NO_PROVIDER_SELECTED / NO_AUTHORITY_ISSUED / NO_MODEL_ACTIVATION / NO_RELEASE_OR_INSTALL.
**Most recent accepted source:** C2-D1B Source R0 independently OFFLINE_ACCEPTED strictly as model-neutral PERSONAL offline source/tests at immutable feature HEAD **e26cc43acfed9664e497067189962ac847ad266f**, tree **65a468ab8b3846219bb37edf1606eb6e1ef67cba**, direct accepted pure D1 parent **358b3554075f87f5b8287fbb37d66fa95ad68b7c**. Preceding one Windows selected 10-module offline pytest operator evidence has 193 individual printed PASSED IDs/exit0 and zero unexpected in-process fence refusals; independent Claude ZERO-TOOLS later accepted the transcribed evidence despite seven documented limitations. This grants NO real F1 trust or installed-model proof.
**ABSOLUTE SAFETY:** LIVE_SCHEMA_048_INCIDENT=OPEN; **NO PostgreSQL contact even SELECT**, directly or through Vres task/bootstrap/doctor/health/CLI/hook/migration/F2. VRES_REPLY_GUARD_WARNING and VRES_PERSISTENCE_WARNING unresolved; do not attempt database/task-state repair.

## 0. Purpose and authority type boundaries

**Independent V0 review outcome retained at its OWN immutable SHA:** Claude's Read/Grep-only independent review of D2 V0 design Git blob f6b4e37113ee59e241b46a6224389b9b86e795b1 (docs design HEAD 6d422d46a6ff9a523e2e435607bd6114030af822) returned **DESIGN_REVISE**, ZERO reported fail-open findings, **THREE BLOCKING findings B-1/B-2/B-3** and **THIRTEEN INFORMATIONAL I-1..I-13**. Reviewer final marker VRES_165_PERSONAL_C2_D2_TRUST_PROVIDER_DESIGN_REVIEW_COMPLETE. The complete visible reviewer report is preserved separately in docs/handoffs/VRES-165-PERSONAL-C2-D2-V0-INDEPENDENT-CLAUDE-DESIGN-REVISE-REPORT-2026-10-27.txt (LF-normalized text; original uploaded CRLF SHA256 e75a95f14efe6336c5df43646bba19f3733fb32a784dafcbe8126ef060c73140). Its separate reviewed SHA, source-read coverage and all findings are retained in docs/handoffs/VRES-165-PERSONAL-C2-D2-V0-INDEPENDENT-DESIGN-REVISE-AND-V1-REPAIR-HANDOFF-2026-10-27.md. This V1 is an AUTHOR REPAIR PROPOSAL ONLY; it is **NOT independently DESIGN_ACCEPTED**. No source or installed action occurred.


C2-D1B established a policy-neutral Chairman SOURCE body and deterministic offline negative tests. It did NOT enroll trust H_0, issue a user presence event E, run independently attested Fable validation V, consume an event in a linearizable CAS, create a separate installation warrant W, authenticate a release publisher or prove which physical model Claude actually loaded.

**This C2-D2 document defines a PROPOSED independently rooted trust-provider and release-publisher contract for later security review. It does NOT select a provider, author a service or create any positive approval API.** No user-provider account, hardware enrollment, keyring, credential, hosted service, new profile, trusted signer, release manifest or installer may be set up by this draft.

Later slices remain separate:
- **C2-D3:** independently reviewed policy-bearing release artifact schema (distinct from v2) and a minimal protected current-user plugin-only transition with its own rollback/P/M/J/R crash tests.
- **C2-D4 / #169:** genuine host/provider-observed effective Chairman family/effort and runtime loader/override/fallback proof.
- A successful D2 architecture review is NOT permission to perform either D3/D4.

A source hash or B2B denial-only matching descriptor must never be promoted to trusted APPROVE by an elimination-of-negative-checks oracle.

## 1. Exact GitHub source provenance inspected and its limits

The author reviewed relevant content via READ-ONLY GitHub, not local installed user configuration or a database connection. The design review must still re-read primary normative contracts and disclose FULL/PARTIAL/NOT_READ. Read canonical docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md first and the newest C2-D1B independent acceptance handoff.

| Reference | Git blob | Authoritative role |
| --- | --- | --- |
| B2B R3 design | 110ccffcbc1c1f00f5b674b4836fed432708f4ea | docs/architecture/VRES-165-B2B-TRUSTED-CHAIRMAN-AUTHORITY-CONTRACT-R3-2026-10-26.md, DESIGN_ACCEPT for B2B-1 DENY-ONLY, not positively trusted F1 |
| B2B R3 mandatory erratum | e7536be90246ad3894befb8a2f5e158d3088028d | docs/architecture/VRES-165-B2B-R3-POSTREVIEW-ERRATUM-2026-10-26.md, NF-05..NF-10 and R3-N01/N02/N06/N07 remain OPEN |
| C2 V1 reviewed design | 407e36528c5cda925517ae0a9db6ba826069aac9 | docs/architecture/VRES-165-PERSONAL-C2-REVERSIBLE-CHAIRMAN-MODEL-CHANGE-DESIGN-V1-2026-10-26.md, §4/§5/§10 D2/D3/D4 gates |
| B2B-1 current denied-only code | b7c7e9871f669f6420eed8b20e77fe76e44a489f | src/vres_os/chairman_b2b_denial_contract.py, frozen caller-claimed inputs, Refused/Indeterminate only |
| B1 immutable history | e19d913714d3625afaeb91d0fccfcfe43d13d195 | src/vres_os/chairman_policy_history.py, canonical 1..128 B1 chain, no fake count-zero document |
| Current v2 release | ddfc1beacad98199b489dc6f56456baf4d519c6a | src/vres_os/release_artifact.py, FORMAT vres-personal-release-artifact VERSION=2, original Git-object SHA bound |
| Original installer | 29a5f0da235021cc8c5607eb92218e5ea98145fa | install.ps1, full venv/pip/launchers/global config/pointer flow, NOT approved for a policy-only change |
| Recovery | 1c0d585645280678af4875f2842a3350f9805e0a | src/vres_os/install_recovery.py VERSION=2 snapshot/recovery is not a trusted H_n/Q journal |
| Phase A renderer | 36e62d6a2712ac305fd4070bac658b94d61d155e | src/vres_os/chairman_policy.py, pure model/effort frontmatter and LF/CRLF body preservation |
| Accepted D1B SOURCE Chairman | bc160273c1a1f8cfb8a844041da206c90a00769b | plugins/vres-os/agents/chairman.md, SONNET/high source baseline, OPUS/medium only an inert derived candidate |

**Coverage:** The author inspected R3 design main threat/genesis/consent/CAS/warrant/loader/model sections, full erratum, accepted C2 V1 relevant design sections, B2B-1 refusal API, release v2 manifest and full-installer bounded sections, history/recovery module interfaces. This is a bounded GitHub analysis, not a complete source-wide trust implementation audit; there is no native host/runtime/physical observation. Independent reviewer must not infer actual provider availability from text.

## 2. Attacker tiers and independence

**T1:** untrusted chat, agent/model proposals, JSON, claimed hashes, source template and prompt injection.
**T2:** an adversarial AI agent/plugin/subprocess with arbitrary normal same-Windows-user rights: may modify user-writable config/plugins/registry/DPAPI-protected same-user secrets/logs, impersonate command line and prompts, launch subprocesses and tamper with apparently local "trust" stores or user Git credentials.
**T3:** elevated ADMIN/SYSTEM or compromised genuinely independent provider/service infrastructure, excluded from a precisely evidenced T2-specific claim; no blanket claim of protection.

**Five functionally separate mandatory trust roles:**
1. **Independent release publisher/root**: authenticates protected source/template/renderer/pins and versioned release identity independently of source author credentials; publishes withdrawal/revocation state.
2. **Independent protected head+history storage**: authenticates genesis H_0 and monotonically advances H_n, separate L/G/Q, event/nonce revocation and correct atomic CAS ordering.
3. **Authentic trusted operator-presence UI/event service**: independently renders verified E proposal and later separate W installation screen, binds principal/current SID/machine/install scope, exact values shown and nonces.
4. **Independent validator wrapper**: obtains actual protected prestate and bytes, deterministic checks plus an independently attested correct protected Fable/high model, never text-only Fable PASS.
5. **Protected deployment/loader and host model observer**: D3/D4 future verified write and per-load/per-use or preventive model enforcement; one-time file hash is insufficient against T2.

These are FUNCTIONS, not proof of five distinct security services. A concrete provider may combine functions only if their transaction domain, T2 independence, event provenance and permissions are independently demonstrated. **NO concrete independently protected provider is selected or installed.** Calling a class TrustedProvider does not make it trusted.

In particular, same-user DPAPI, user-held GitHub source credentials, source SHA, clipboard approval, Claude permission dialog, user-selected Windows Hello text/results, or a one-time original plugin file hash MUST NOT be treated as T2-resistant origin.

### 2.1 B-2 repair — independently evidenced provider-selection gates, NOT an invented service

No real trust provider or publisher is selected, credentialed, deployed, operated or proven. An actor *class* is a hypothesis, not a provider. A concrete future candidate can be evaluated only against the following mandatory independent evidence checklist; absence, ambiguity, T2 impersonation or unresolved races are **BLOCKED_PROVIDER_EVIDENCE_UNAVAILABLE (design label only)**. Authenticated root/principal, trusted GUI and atomic head are not established by a marketing claim or a product name.

| Provider elimination gate | Exact evidence a future independently reviewed candidate must supply |
| --- | --- |
| P01 identity and T2 separation | Documented protected security principal, access control, actor identity/caller authentication and independently adversarial evidence that arbitrary same-user T2 software cannot impersonate, read issuer credentials, modify head/keys or issue E/V/W |
| P02 verified enrollment/origin | An independently rooted release/issuer trust chain, origin outside user-authored Git/Claude/DPAPI state, authenticated role keys/permissions/epoch, identity of the actual verifier and protected machine/SID/install instance |
| P03 authentic human screen/input | Evidence that the provider renders canonical old G/latest L and exact E/W facts, binds displayed content into the returned event and resists normal same-user overlays, automation and caller-supplied dialog spoofing |
| P04 linearizable authority storage | Reviewed single-order transaction semantics and fault/race tests for H_n head+epoch, unique nonce consumption, independent cancellation and revocation visibility, and pending Q; no eventual-consistency check-before-CAS |
| P05 trusted freshness | Named independent provider clock/monotonic source, measured error/drift/reset/rollback, authenticated time binding, E→V→CAS duration and separate W→install deadline without dependence on T2 system time |
| P06 credential custody | Concrete key custodians, issuer principal and verifier root for E, protected V wrapper, CAS service and W; issuance scopes, lifecycle, independently authenticated rotation, compromise response, backup and withdrawal |
| P07 release root | Independently verified publisher root outside AI/source Git author credentials, trusted source/template/renderer/pins, signed/attested approved release and external withdrawal notices with enforceable freshness |
| P08 validator provenance | Protected wrapper identity and verifiable Fable/high resolved model evidence from vendor/provider under old G pins, documented physical/vendor assumptions and explicit failure when source is absent or untrustworthy |
| P09 loaded runtime | Actual Claude source/override/load-path audit and a protected loader/per-use or preventative enforcement path; user-writable plugin SHA or installed file check alone fails |
| P10 outage/recovery | Availability, catastrophic head/key/provider loss, recovery/rollover and no-reset lineage continuity, immutable audit retention and honest BLOCKED/stop-loss UX; no locally reconstructed genesis |
| P11 one-user UX and cost | Only two genuinely distinct E/W human confirmations for consequential stages, rate limits and cancel behavior, clear recovery risk, staffing/cost/infrastructure evidence; no enterprise assumptions |
| P12 D3 boundary | Proof that future installer and journal are protected, not legacy install.ps1 or install_recovery.py; revocation checked at final byte write and actual load; no weakening of source-v2 manifest or D4 physical model proof |

**Candidate classes requiring future assessment, none approved:**
- A separately permissioned **Windows service principal, ACL-protected head store and secure-desktop UI**: a service name/ACL does not by itself prevent same-user impersonation, IPC abuse, desktop overlay, T2 launch/credential theft or solve publisher/atomic loader; actual security boundary/secure-desktop channel and CAS proof required.
- A **second-device approver** with authenticated channel: requires display bound to exact canonical facts, non-relay/non-replay user action and separate T2-independent head/nonce transaction and publisher; a phone approval alone is not CAS.
- A **display-equipped hardware token**: independent physical on-device display/input and request digest/nonce evidence may help E/W, but a generic TPM/USB/Windows Hello callback does not prove protected head, clock, publisher, Fable wrapper or loaded model.
- An **independently permissioned remote broker**: might supply protected records and presence UI, but requires actual approved account, endpoint, clock, transaction and credentials, availability/withdrawal policy and D3 loader interface. No account/cloud/enterprise IAM entitlement is assumed.
- An **ordinary same-user app, file, DPAPI blob, user GitHub credential, Claude permission dialog or generic Hello caller-return value**: INSUFFICIENT for this T2 model, regardless of internally consistent SHA values.

**Personal minimum viable architecture (I-12):** five distinct logical trust roles need not mean five installed apps/accounts. A truly T2-independent broker could combine transactionally coupled H_n/head/nonce/revocation and purpose-separated E/W issuers, while a separately rooted publisher and protected Fable validator/loader proofs remain genuinely independent. Role-specific keys, security principal and separately authenticated E/W displays are still required. Until a concrete candidate independently satisfies ALL P01–P12, **no C2-D2 positive provider or issuer is selected**. If no feasible candidate exists, keep the original #165/F1 model switch BLOCKED; a distinct weaker experiment was never authorized.


## 3. H_0 enrollment and closed current-state model

**H_0 GENESIS is a distinct authentic enrollment**, not a fake accepted B1 history with zero proposals:
- protected release root and independently verified original source/installed baseline, immutable current-user machine/SID/install lineage, trusted target/loader identity, source/renderer/pin identities and domain-separated enrollment record;
- epoch=0, proposal_count=0, history_sha256=null, latest_proposal_sha256=null are typed PRE-HISTORY absence, not a digest of empty JSON;
- independently rendered operator enrollment event and protected storage; cannot self-choose a fresh install ID to bypass an existing protected lineage (NF-08);
- no real H_0 exists yet. Without independently verifiable enrolled source, root and storage, return **BLOCKED_NO_AUTHENTICATED_GENESIS (DESIGN OUTCOME, NOT IMPLEMENTED)**.

For each verified H_n:
- **L_n** is the most recently appended immutable B1 proposal history and its exact count/full canonical SHA/latest proposal SHA, including refused/abandoned entries.
- **G_n** is the LAST independently COMPLETED installed-and-loaded governing policy/release and prestate validator pins, which may differ from L_n.
- **Q_n** is null, PENDING(intent), or RECOVERY(intent,investigation), at most one; Q not null blocks another proposal. A pending candidate never overwrites G.
- **Epoch n** advances for COMPLETE/ABANDON too, and is NOT B1 proposal count p.
- At p=0 require canonical B1.begin with exactly one sequence/version1 proposal and null predecessor, do not call B2A against a fabricated zero-history document. At p>=1 reconstruct old prefix as a standalone canonical B1 history from first p entries of C, check it against independently authenticated L_n and append exactly ONE p+1 linked successor. Preserve B1 cap128, never silently rewrite, delete, rewind, fake a Sonnet intervening hop, or bypass adjacent identical policy no-op refusal.

Caller-supplied B2B-1 claimed H/L/G/Q and digests may yield only Refused or Indeterminate. A real positive transition would require independently protected provider reads and a *separately reviewed new API*, never a third enum case added to deny-only B2B-1.

### 3.1 B-1 repair — H_0 role-identity verification bootstrap and protected lifecycle

**H_0 must enroll the issuer AND its independent verifier, not merely a release and baseline.** The independently authenticated genesis record includes a canonical protected *role issuer registry*, trust root/key-chain and active registry epoch for FOUR role purposes, even if one genuinely independent service later hosts multiple roles:

| Required role in H_0 and current H_n | Required independently authenticated verification fields |
| --- | --- |
| E proposal consent issuer | issuer principal/realm, root+verification key identifier and fingerprint, allowed algorithm/version, PURPOSE=E_PROPOSAL domain, independently observed user-presence/display identity, target SID/install instance, validity/revocation epoch |
| V protected Fable/high wrapper | independently permissioned wrapper principal and verification root/key, PURPOSE=V_VALIDATION domain, trusted fetch/deterministic evidence policy and independently observed Fable/high identity grade, OLD G_n approved validator pin binding |
| H_n CAS/nonce/revocation store | protected service owner and authenticated head-signing/verifying root, PURPOSE=ANCHOR_TRANSITION domain, linearizable transaction/nonce/revocation ordering capability, target, monotonic epoch/rollback resistance |
| W installation consent issuer | separate issuer principal/verifying key/root and PURPOSE=W_INSTALL domain, NEW independent human-presence screen, fresh nonce and pending epoch/target/release binding distinct from E |

For ALL records pin the allowed evidence schemas, issuer public verification keys or independently attested equivalents, provider/root chain, algorithm policy, role+purpose separation, key activation/deactivation, domain-separated payload type/version, canonical audience/machine/SID/install identity, rotation authority and revocation registry generation. **Verification trusts only H_0 or the latest independently authenticated H_n role registry under the publisher/root policy.** Neither a local code module, JSON schema, user GitHub commit, candidate C or agent prompt can establish a verifying root, and overlapping roles must remain purpose-separated even if they share one protected service. No actual key/issuer/algorithm is chosen by this design.

**Hard fail-closed rule:** any missing, unknown, mismatched, withdrawn, expired, T2-editable or unauthenticated E/V/CAS/W issuer identity, verifying key, root link, accepted domain/algorithm or current role epoch means **BLOCKED_UNENROLLED_ROLE_ISSUER (design-level status only)**. A matching signed-looking claim is not enough if the verification root itself is not protected.

**Separate role-key ROTATION or COMPROMISE ceremony:**
1. The independent provider presents a domain-separated ROTATE_ROLE_ISSUER/REVOKE_ROLE_ISSUER event bound to prior trusted root/H_n epoch, exact old/new role/key fingerprints, issuer, reason, operator/target, affected active E/V/W/Q, nonce, revocation and recovery impact; no same-user "just overwrite key file".
2. Independent root-controlled recovery principals verify the new identity/chain and the actually authorized human ceremony. A compromised old role key **cannot authorize its own replacement**; root compromise requires distinct independently authenticated rollover or BLOCKED.
3. Protected store atomically advances a monotonic registry/head epoch and current issuer revocations within its event/nonces ordering semantics, invalidates unconsumed affected events/validations and leaves Q pending/recovery blocked until separately authorized resolution. Previously used issuer signatures remain historical with recorded epoch/revocation disposition, not reusable live permits.
4. Future E/V/W/CAS checks independently fetch current protected issuer epoch and check signatures/attestations with purpose-specific roots. Stale or forked issuer registry refuses. Missing provider, lost root or uncertain compromised epoch => no positive operation.

**I-7 genesis provenance:** last observed P2 Sonnet/high was installed by same-user install.ps1 from a human-typed commit; that is NOT a trusted H_0 publisher or physical baseline. A real genesis must reconstruct approved SOURCE template/renderer/worker+validator pins from independently authenticated publisher-pinned Git/release objects and independently compare verified installed AND runtime-loaded governing baseline for the canonical machine/SID/install lineage before enrollment. If no trustworthy root or baseline/loader observation is available, H_0 stays UNENROLLED. A new install ID cannot bypass existing lineage.

**I-3 future positive G_n schema:** the existing B2B-1 ClaimedGoverningReference only identifies caller-claimed kind/sequence/proposal-SHA. A real positive API MUST define its own independently authenticated G with last completed policy/release, root-approved prestate validator pins, target, trusted load evidence and completion epoch; never upcast denial-only claimed G.

**I-8/I-9 B1 truth in user-facing refusal:** B1's 128-proposal limit is LIFETIME under that accepted history format, not a window/reset allowance. If latest abandoned Opus proposal cannot be immediately repeated due adjacent B1 no-op, show BLOCKED_HISTORY_RETRY_UNREPRESENTABLE and require a separately reviewed history-schema change or no model switch; do not manufacture alternate Sonnet hops. B1 compares adjacent proposals only, so an initial C equal to prehistory independently rooted governing G_0 may be syntactically valid. Future real positive issuer must separately identify and REFUSE that first-governing-policy no-op before creating E, unless a new independently reviewed explicit policy defines otherwise; this is NOT a change to existing B1 denial-only code.


## 4. E proposal and protected V, never authored by Chairman

Order before any policy intent may be anchored:
1. Trusted provider independently reads H_n (including protected current G, latest L, pending Q), enrolled publisher/release root, canonical current-user target, approved source-template/renderer digest and old Fable/high validator/model-family rules. Missing trust => **BLOCKED**.
2. Check one bounded canonical candidate C, old history P as above and old G vs latest L separately. Candidate code may propose data but never assert trusted expected values.
3. Provider renders a meaningful **E PROPOSAL consent screen FROM VERIFIED FACTS**, including completed installed G and latest L/disposition as separate fields (R3-N06); old/new family/effort/version, changes in source/body/tests/validator pins, original vs derived output identity, source publisher, target/SID/install instance, current epoch/nonce and implications. T2 cannot substitute its own screen text. Bound the actual displayed-fields digest and throttle agent-induced prompt fatigue.
4. Provider authenticates actual operator user-presence and creates one type/domain/version-separated E with APPROVE disposition, principal/session/target/release/H_n epoch+digest/C policy+history hashes, displayed digest, provider-owned challenge/nonce, freshness and non-revocation. Reject ambiguous/cancel/reject/unknown provider status. User chat saying "I authorize" is NOT E, and source-level testing approval is NOT model-change consent.
5. Protected V wrapper fetches actual canonical E/H_n/C/release/template/renderer/old pins DIRECTLY from protected providers, not through untrusted agent prose. Deterministic code checks schema, history, hashes, target, nonce and source identities. Fable/high analysis treats candidate rationale and model text as untrusted DATA. The wrapper must attest actual model identity and check result, not trust a free-form Fable PASS or silently substituted family (NF-10).
6. Neither E nor V grants installation. Only protected authority service may proceed to CAS if every old-head/revocation/validator and source/release claim is independently verified and fresh.

Current R3 architectural proposed E freshness ≤300s from independently authenticated provider confirmation to CAS; the real provider-owned clock/freshness semantics and bound are NOT validated/implemented. No use of T2-controlled OS time/agent timestamp.

### 4.1 B-3 repair — NF-10 validator identity: proposed evidence grades, verifier and truthful feasibility

**Validator pins derive only from the last independently COMPLETED, load-verified governing G_n and protected root family rules — NEVER from candidate C, latest proposed L_n, pending Q_n, agent-provided validator override or a new source file.** A proposed validator-pin change is evaluated under the OLD G_n pins; only a later separately warranted and independently load-verified COMPLETE_INSTALL may update G. B2B R3 already requires this rule, and V1 now states it expressly.

The future T2-independent wrapper must be a pinned V issuer from H_0/current H_n §3.1. A verified V observation, if one eventually exists, needs exact wrapper principal/key/issuer epoch, trusted vendor endpoint/account/TLS certificate-validation provenance, ROOT-approved model-family matching rule, request ID and nonce, old G_n Fable/high pin and effort, protected request/response binding, independently observed endpoint model identifier and effort status if provided, canonical E/C/H_n/release/target digests, provider-authenticated time, deterministic wrapper checks and domain-separated V payload. An agent message claiming "used Fable/high" and any model-written PASS are UNTRUSTED, and the wrapper is not allowed to select a validator from C.

**NF-10 evidence alternatives — candidate definitions only, none selected or actually available:**

| Evidence grade | Trust interpretation and residual limitations |
| --- | --- |
| A. Vendor-signed resolved model attestation | If a real vendor emits a signed nonce/request-bound family/effort/model statement with independently validated publisher key and correct protected wrapper link, a reviewer MAY evaluate it as a cryptographic provider-origin claim. No such field/key is currently established for this environment; do not invent one |
| B. Independently permissioned wrapper sees vendor endpoint-reported resolved model over authenticated TLS | T2-resistant wrapper authenticates the actual vendor endpoint and binds request/response/model field under its own independently verifiable V issuer. This observes a VENDOR-REPORTED model, NOT a vendor-signed cryptographic assertion about computation; T3 vendor endpoint honesty/schema and model mapping must be explicitly trusted. Alias labels or missing effort are not physical proof. This requires a separate reviewer judgment about acceptable assurance; it is NOT automatically V success |
| C. Same-user Claude logs, response narrative, request alias, local plugin frontmatter, unverified telemetry | T2-editable/insufficient; no positive V and no claimed Fable/high protected execution |

**Default feasibility:** **NF-10 feasibility remains UNKNOWN / BLOCKED_VALIDATOR_IDENTITY_UNATTESTED** until an actual independent provider and acceptable grade A or separately reviewed grade B with concrete endpoint and G_n family/effort mapping are proven. If vendor endpoint cannot show actual resolved family, aliases/effort cannot be resolved under root-approved policy, TLS wrapper can be impersonated by T2, evidence lacks nonce/target, or fallback occurs, refuse BEFORE positive V/CAS. This does not claim current Claude exposes a signed model ID, does not issue a provider token, and does not prove a physical loaded Chairman Opus (still D4/#169).

**I-10 time bound:** the R3 proposed E→CAS maximum 300 seconds includes the ENTIRE protected Fable/high V execution AFTER authenticated human E and the final protected CAS. A slow/paused V, expiry, unknown provider clock, changed H_n or exhausted budget requires refusal and a fresh independently authenticated E/V against the latest protected head; never extend E, replay consumed nonce or quietly skip validator work. W has its own future separately reviewed freshness window and cannot reuse E.


## 5. Atomic H_n CAS and pending resolution

**Future protected CAS (NF-05) must be PROVABLY LINEARIZABLE:** within one transaction/ordering domain jointly check and advance the authenticated head epoch/digest, validate old G/L/Q and target/publisher/source, consume the unique E nonce/event and ensure concurrent cancellation/revocation visibility. A separate check-then-write across independent mutable stores is forbidden. If this cannot be proven, positive authority is BLOCKED. A failed/stale CAS cannot reuse old E as a new approval.

On valid CAS H_(n+1) records updated L (full canonical C), **G UNCHANGED**, Q=PENDING(exact C/E/V/release/target). This is a protected proposal INTENT, not Opus installed, not an installer warrant and not completion. Concurrent requests and unresolved Q stay blocked.

Closed future transitions:
- APPEND_PENDING: one new history proposal, bound E/V, atomic CAS; G unchanged.
- COMPLETE_INSTALL: requires distinct NEW W, D3 protected installer final byte proof and independently trusted loader/per-use enforcement, then another protected forward-epoch CAS with EXACT Q/E/V/W/C/source/render/release linkage (R3-N02). Until actual independently load-verified bytes, completion is BLOCKED. Physical provider model family still awaits D4.
- ABANDON/REVOKE: independently authenticated domain-separated terminal event advances epoch, keeps all L entries and old G, and clears Q ONLY on authenticated protected commit.
- RECOVERY: investigative fail closed. After partial installed file write cannot clear pending unless actual installed/loaded state is independently consistent with old G, or a separately W-warranted RESTORE_GOVERNING is designed/proven (R3-N01); never auto-install or auto-revert.
- Latest L may remain abandoned Opus while G stays Sonnet; an immediate identical Opus retry may violate B1 adjacent-repeat, so REFUSE without fake intermediate proposal (R3-N07). No history truncation/replay of consumed E.

## 6. W installation, revocation, publisher and loader gates remain separate

**W is not E.** Once intent CAS consumes E, D3 installation requires distinct independently rendered human-presence W tied to the CURRENT pending H_(n+1) epoch/digest, exact previously completed G, pending C, canonical target, current approved release/publisher, original SOURCE vs DERIVED bytes and expected recovery. Prospective W age ≤300s under separately reviewed provider time. Changing epoch/target/family/bytes, expiry, release withdrawal, revocation, cancel or stale pending must fail closed. W issuance and FINAL byte commit must recheck all those facts at the write boundary (NF-09). A W cannot be re-used on retry after failed/partial install without distinct protected recovery governance.

Publisher (NF-07) must be independently authenticated from T2: reviewed exact source commit/tree, policy-aware template BODY blob, PhaseA renderer code identity, approved policy family/effort/version and hash, source/derived SHA and lengths/newline convention, fixed Sonnet/Opus worker/Fable validator pins and approved schema. Source-author GitHub tokens or local SHA only provide **content identity**, NOT publisher authenticity. Withdrawal should be visible to E/V/CAS and later W/write/load.

**Existing release_artifact.py VERSION=2** stages original exact Git objects. Opus/medium policy rendering changes Chairman header and bytes, so a new DERIVED candidate cannot masquerade as the original Sonnet/high source Git blob in v2. A future explicit v3 (or separately named typed new artifact) and old-v2-verifier fail-closed version handling are D3, NOT implemented/issued by D2.

**Loader and effective model (NF-06)** are NOT proven by managed file readback: project/user/global settings, CLI flags, environment overrides, actual agent lookup paths, junctions/reparse points, provider alias/fallback, source/user-installed release distribution and runtime loaded definition may determine the effective Chairman. Under T2 a same-user writable override path prevents a T2-proof guarantee unless a separate protected loader/per-use check is demonstrated. D3 studies actual target write and D4 independently attests provider-resolved family/effort (do not assume Opus simply from request).

### 6.1 I-1 / I-5 / I-6 / I-13 — cross-service withdrawal, legacy installer exclusion and source/derived identity

**I-1 authenticated cancellation and publisher withdrawal ordering:** a cancellation/revoke event originating in a distinct E/W presence service must enter the protected H_n head/nonce/revocation ordering domain with independently authenticated issuer/purpose/epoch before a relevant CAS may be committed. The publisher's external withdrawal registry is NOT magically atomic with either a head CAS or a Windows filesystem write. A future authority could ONLY conditionally use a monotonically versioned, independently publisher-authenticated withdrawal/root state MIRRORED into that protected head transaction domain, with a separately reviewed and demonstrably enforceable bounded mirror-staleness policy; CAS rechecks its exact generation in the atomic head+nonce/revocation step. No bound is approved here. Unknown/stale/inconsistent/publisher-unavailable mirrors => BLOCKED.

A D3 write-boundary remote withdrawal query remains a check-then-write race; it MUST NOT be presented as full linearizability with the physical install. D3 requires independently reviewed protected fresh-W final-gate/lease semantics PLUS independently enforced per-load/per-use mismatch refusal or protected write prevention and a truthful residual withdrawal exposure assessment. If exact ordering cannot be guaranteed at the claimed assurance, no positive installation. Do not quietly accept an eventually consistent mirror simply because it has a recent timestamp.

**I-5 legacy installer/recovery MUST NOT be reused as protected F1:** current install.ps1 runs venv/pip/launchers/global Claude updates, can auto-recover from a same-user journal and deletes its pending journal after a run. Current install_recovery.py recover --confirm can restore user-writable plugin/pointer from a same-user snapshot; neither is an independent protected B2C actor or authoritative recovery store. Do not call, wrap or rebrand either for positive H_n policy switching or a protected post-partial-write rollback. D3 must design a DISTINCT reviewed, separately W-warranted, independent protected journal/installer and forward-epoch restore-or-block handling. Legacy installer refusal when Claude is open reinforces that actual human E/W screens must be independent trusted provider surfaces, never Claude Code prompts.

**I-6 loader T2 attack surface:** existing install.ps1 can honor CLAUDE_CONFIG_DIR and installs user-writable skills/vres-os. The inspected source did not demonstrate protected managed-settings/ProgramData loader enforcement. Therefore all actual project/user/global config, CLI/session flags, environment, alias, search paths, reparse points and T2-writable override mechanisms require D3/D4 independent inspection; source SHA, installed file hash and protected H_n alone do not prove physical effective Chairman model. If prevention or separately protected per-use observation cannot be demonstrated, F1 remains BLOCKED.

**I-13 v2 top-level key trap:** existing src/vres_os/release_artifact.py load_manifest checks VERSION=2 but does not reject all unknown top-level keys. A policy-specific derived Opus artifact cannot sneak an extra policy field under VERSION=2 and pretend the old verifier approved it. D3 MUST create a distinct explicit new schema/version and require old VERSION=2 verifier to reject it while new verifier refuses unexpected keys, cross-purpose hashes, mismatched output bytes and downgrades. No version3/publisher or installation code is authored at D2.


## 7. Mandatory R3 erratum STOP ledger — explicit future checks

All remain OPEN; naming them does NOT implement them:

- **NF-05:** protected CAS head digest/epoch + E nonce consumption + cancellation/revocation must share provably linearizable semantics, never check-then-commit across untrusted stores.
- **NF-06:** effective family/effort must account for ALL loaded definition/config/search/override/alias/fallback inputs; file SHA is not physical model proof.
- **NF-07:** independently trusted publisher/source/template/release root secured from T2 and AI-author GitHub credentials; explicit human artifact provenance.
- **NF-08:** one trusted H_0 enrollment per protected machine/SID/install lineage; new ID cannot bypass prior root, rollover separate ceremony.
- **NF-09:** independent W issuer and final install recheck of publisher withdrawal, pending epoch/age, target, exact bytes and revocation.
- **NF-10:** independent V wrapper must attest actual protected Fable/high model identity; text PASS or silent substitute cannot issue positive validation.
- **R3-N01:** after partial write, protected restore or fail-closed recovery, do not abandon based on mutable user file or clear Q prematurely.
- **R3-N02:** COMPLETE binds G to EXACT intended Q/E/V/W proposal/render/release, not just whatever bytes a local observer reports.
- **R3-N06:** human E/W disclose last independently completed installed G AND latest immutable proposed L with its disposition separately.
- **R3-N07:** every genuinely required intervening policy proposal has its OWN E/V/CAS; no fake hop; equal-to-G change/revoke disposition requires separately reviewed issuer criteria.

The accepted older C2 V1 seven design informationals, old C2-D1 eight STATIC, C2-D1B DESIGN twelve, R0 STATIC eight and R0 REPORT_ONLY seven informationals remain. None is automatically resolved by this D2 design.

## 8. PERSONAL provider feasibility decision and negative evidence plan

**No actual independently permissioned provider selected:** not a real cloud enterprise IAM service, not an independently approved OS service, not an authenticated trusted publisher, no real genesis, W issuer, CAS store or loader. Do not request credentials, sign anything, connect services, run host checks or access an installed profile merely to make this design look complete.

D2 DESIGN viability decisions:
1. A separately permissioned T2-resistant remote/local protected principal COULD in principle implement head, nonce/revocation and consent roles, but only after concrete independent identity, origin, transactional and loader-interface evidence plus explicit later consequential user authorization. Do NOT assume availability.
2. TPM/Hello/DPAPI/Windows UI by name do not show trusted human-display/caller integrity or atomic head+nonce+revocation; no immediate provider approval.
3. A truly independent publisher/root and host loader must still exist; even a real protected consent service alone cannot safely install/activate a T2-mutable plugin.
4. **If ANY trust role is unavailable, output BLOCKED_TRUST_PROVIDER_UNAVAILABLE (design-level status only, not an implemented enum)**. No local-file mock, fake H_0 or model-generated signature may be substituted.
5. User has not authorized a distinct non-F1 personal experimental model switch. USER_DECISION_ON_NON_F1_PERSONAL_EXPERIMENT=NOT_MADE; the prior authorization for C2-D1B source/tests is NOT authorization to bypass F1.

Later implementation requires an independently accepted DESIGN V0 or revised V1, concrete trusted provider identity and explicit user approval, a separate exact source allowlist/new SHA, STATIC_FIRST, guarded offline tests and evidence gate. D2 itself authorizes no source modification.

**Future NEGATIVE acceptance matrix only (NOT EXECUTED):** no H_0; forged/replayed genesis; target/SID/install mismatch; cross-purpose digest; canonical B1 count0 vs typed genesis; p+1/adjacent-repeat violations; E cancel/expired/revoked/duplicated; spoofed consent screen; old G vs latest L confusion; Fable fallback; changed source BODY/renderer/worker pins; withdrawn publisher; stale/incongruent W; concurrent CAS/nonces/revocation race; Q pending/recovery; partial write and restore; T2-loaded-path override; alias silently resolves Sonnet; unknown artifact/manifest version; 128 proposal cap; old v2 rejecting a future v3; no physically authentic effective host model. Expected output always REFUSED/BLOCKED/INDETERMINATE without privileged actions. There are NO implemented positive success tests or mocked trusted tokens in this design stage.

### 8.1 I-2 / I-4 / I-11 / I-12 — anti-oracle, untrusted rationale, fail-closed lockout and PERSONAL minimum

**I-2 denial-only oracle:** Existing B2B-1 Indeterminate may indicate some CALLER CLAIMS passed local consistency checks (the single Indeterminate result occurs after denial checks). That is NOT authentication of H_n or release, and a future positive service MUST NEVER branch on Indeterminate, not-Refused, a denial-code sequence, a matching caller SHA, or the absence of errors to issue a permit. Only a wholly distinct independently protected positive API with authenticated role keys/head/C/E/V/CAS/W/loader proofs can ever be considered, after future separate security approval. Do not edit frozen B2B-1 source merely to hide this informational limitation.

**I-4 proposal reason remains hostile DATA:** B1 rationale is agent-authored free text (bounded to 512 bytes and filtered for control characters). E/W provider UI, if it displays reason, MUST label it "untrusted proposed reason", escape/render it inert within a visually distinguished area and separately authenticate all old G/latest L/current root/source/release/displayed facts. It may not alter provider prompts, model/tool instructions, canonical challenge, trusted field values or role issuer.

**I-11 provider outage, disaster recovery and honest stopping:** unknown provider, lost/compromised head store, missed publisher withdrawal, lost issuer key, expired nonce, unsupported alias, or permanent unrepresentable B1 retry triggers BLOCKED (not a retry/new H_0). Human-facing status should explain why the last independently verified governing model may remain in use ONLY when a trusted loader has separately proven that state; otherwise model-governance assurance is unavailable and any claimed protected switch must stop. No same-user restore/reset, no spoofed standalone new install lineage. Future independently protected recovery/rollover is a separately reviewed ceremony. The user may explicitly decide to abandon the F1 switching program if no credible provider can meet P01–P12; this cannot silently elect a weaker experiment. USER_DECISION_ON_NON_F1_PERSONAL_EXPERIMENT remains NOT_MADE.

**I-12 proportional minimum viable PERSONAL configuration:** No five-app/enterprise-IAM assumption. A verifiably T2-independent protected broker could conditionally combine protected head/nonce/revocation store and purpose-separated E/W issuing screens with independent approved role keys, while publisher root, protected validator evidence and D3/D4 loader remain separately validated according to genuine trust boundaries. One user still sees TWO genuinely different consequential decisions (E proposal and W install), not repeated ceremonial prompts. No credentials/account/service, budget or vendor is selected/created. The choice is subject to actual feasibility and operational evidence, not rhetoric.

### 8.2 All V0 reviewer findings — exact V1 author repair disposition, NOT independent acceptance

| Original independent reviewer finding | V1 author repair location / still-open fact |
| --- | --- |
| **B-1 BLOCKING** role issuer verification roots/rotation/compromise absent | §3.1 proposed H_0 issuer registry E/V/CAS/W, independent verifier chain, domain-separated rotation/revocation and hard missing-role BLOCKED; real issuer/provider still unselected |
| **B-2 BLOCKING** no provider-selection evidence matrix/candidate classes | §2.1 P01–P12 elimination table and separately unapproved protected-service, second-device, display-token and remote-broker classes; no selected candidate |
| **B-3 BLOCKING** NF-10 model evidence missing/pins vague | §4.1 G_n-only prestate pins, graded signed-vendor vs TLS independent-wrapper reports vs untrusted self-report, explicit T3 trust and UNKNOWN/BLOCKED default |
| I-1 publisher withdrawal/cancellation cross-store race | §6.1 domain-ordered cancellation and rooted mirrored withdrawal, no fabricated atomic remote write check or unreviewed bound |
| I-2 B2B-1 Indeterminate claims-consistent oracle | §8.1 never use denial outcomes as positive API authorization |
| I-3 B2B-1 G narrower than future protected governing state | §3.1 distinct future authenticated G_n schema required |
| I-4 agent-authored reason on trusted screen | §8.1 label and escape as untrusted displayed text |
| I-5 legacy installer/recovery contradicts protected restore | §6.1 explicit prohibition, D3 new trusted W-backed actor |
| I-6 active user-writable loader/CLAUDE_CONFIG_DIR | §6.1 actual T2 loader audit/D3-D4 blocking |
| I-7 same-user P2 genesis not independently authenticated | §3.1 independent publisher reconstructs source plus independently loaded baseline comparison, else no enrollment |
| I-8 abandoned Opus adjacent retry/dead-end, lifetime 128 cap | §3.1 truthful blocked UX and no fake Sonnet hop |
| I-9 first proposal equal pre-history baseline not rejected by B1 | §3.1 separate future positive issuer G_0 no-op check, no B1 source rewrite |
| I-10 300s E window must include V run | §4.1 full E→V→CAS window, expiry requires new E/V |
| I-11 provider disaster-recovery/loss and stop-loss | §8.1 BLOCKED, authenticated recovery or explicit future program stop |
| I-12 five roles/UX disproportionate for PERSONAL | §2.1 and §8.1 minimum logical roles with potentially fewer independent physical components |
| I-13 v2 ignores unknown top-level fields | §6.1 new explicit D3 artifact schema, no policy data under version2 |

**Everything in this matrix is an AUTHOR CLAIM ABOUT V1 TEXT**, not a Claude DESIGN_ACCEPT. The original reviewer B-1/B-2/B-3 remain historical blocking verdicts at their V0 blob/SHA. New independent review of THIS V1 must judge whether all B findings are actually resolved, whether each I is appropriately carried, whether every R3 NF-05..NF-10 and N01/N02/N06/N07 stop remains, and whether provider feasibility is still honestly unproven.


## 9. Independent DESIGN_ONLY review, evidence limits and next operator gate

**Next allowed gate:** commit a DISTINCT D2 V1 document, the complete prior V0 independent design-revise evidence, its reviewer/handoff ledger and the canonical documentation index, retaining original V0 unchanged. After verifying immutable GitHub docs HEAD/tree/design blob/parent and unchanged source feature HEAD e26cc43acfed9664e497067189962ac847ad266f, operator creates ONE new guarded detached Windows DOCS review worktree from clean P2 Git anchor; no D1B SourceR0 checkout change. The docs checkout may have OLDER SOURCE files, so actual current source must be read from preexisting clean D1B R0 checkout if material. All review work remains READ-ONLY.

Independent Claude review tools: **Read, Glob, Grep ONLY**. NO Git/Bash/PowerShell/Python/pytest/MCP/Vres task/DB even SELECT/provider/installed-user files/credentials/DPAPI/Fable/Opus/agent delegation/file edit/new repository commit. Read THIS D2 design FULL, R3 and mandatory erratum and C2 V1 sufficient depth, current denial-only B2B/PhaseA/release v2/install contract relevant portions. Disclose FULL/PARTIAL/NOT_READ and the difference between relayed SHA identity and actual reviewer source observation.

Reviewer must challenge:
- Real vs imagined independent T2 trust provider; no positive authority merely from terminology.
- H_0 typed null genesis vs B1 count=1, L/G/Q/epoch and B1 canonical prefix/supersession; revoke and pending recovery.
- E human-present independently rendered canonical disclosure vs future separate W; both bounded nonce/target/freshness/revocation.
- Prestate-pinned protected Fable/high V identity; deterministic wrapper, data injection isolation and no self-reported PASS.
- Atomic CAS combining head, nonce and revocation, not separate check then write.
- R3 NF-05..NF-10, N01/N02/N06/N07, publisher withdrawal and v2 SOURCE vs DERIVED identity, actual D3/D4 boundary.
- Personal proportionality, source-only/incident no-DB constraint, meaningful BLOCKED provider-unavailable condition.

Return exactly one verdict **DESIGN_ACCEPT / DESIGN_REVISE / EVIDENCE_BLOCKED**, findings BLOCKING versus INFORMATIONAL with file+line evidence, and explicit DESIGN_ONLY / TESTS_NOT_RUN / SOURCE_MODIFICATION_NOT_RUN / NO_AUTHORITY_ISSUED / NO_MODEL_ACTIVATION / NO_POSTGRESQL_CONTACT_BY_REVIEWER. Even DESIGN_ACCEPT is NOT C2-D2 positive source or provider permission. Final exact marker:

**VRES_165_PERSONAL_C2_D2_V1_TRUST_PROVIDER_DESIGN_REVIEW_COMPLETE**

### 9.1 V1 independent-review requirement — not inherited from V0

A new independent reviewer must decide whether B-1 role-issuer/root bootstrap+rotation, B-2 provider-selection elimination evidence and candidate classes, and B-3 protected validator evidence grades with pins from old G were corrected *in this V1*. Each original B and all thirteen I findings remain separate reviewer obligations. A DESIGN_ACCEPT here would accept only this docs architecture, not choose a provider, generate user events, grant positive E/V/CAS/W, publish artifacts or install Opus. New final marker: VRES_165_PERSONAL_C2_D2_V1_TRUST_PROVIDER_DESIGN_REVIEW_COMPLETE. Reviewer tools Read/Glob/Grep ONLY; no actual PostgreSQL including SELECT.

## 10. Installed status and full continuity

Last read-only observed current-user P2 release **20261022172833-4d82147b**, Chairman managed/distribution Sonnet/high, LF 24,208 bytes SHA256 **a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73**. Current running Claude model family unknown. Opus/medium UNINSTALLED. No source/manifest/artifact SHA from D1B indicates a real switch.

Original F1 positive H0/E/V/CAS/W/publisher/loader/#169 all OPEN, LIVE_SCHEMA_048 no PG even SELECT, D2 preproduction OPEN/F2 quarantined and PA-01..08 incomplete. Full PERSONAL V-01..V-42 development roadmap (Visual Studio fresh/legacy project onboarding, secure reusable current-user credential handles, cross-project continuity, expert capabilities) remains. Historical accepted and rejected exact source SHAs, failed test/procedural warnings and informational findings are immutable.

**THIS DISTINCT D2 V1 IS ONLY AN AUTHOR DOCS REPAIR; V0 REVIEW RESULT REMAINS DESIGN_REVISE.** Exactly FOUR doc changes: ADD new V1 Markdown, ADD the V0 independent reviewer visible-text report, ADD a separate V0 reviewer-findings/V1-disposition handoff, MODIFY canonical docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md. Original V0 blob is immutable. One new single-parent docs commit with nonforced expected-old SHA/strict 4-path diff and GitHub readback; accepted source e26cc43acfed9664e497067189962ac847ad266f unchanged, no trusted provider, positive user event, signing, manifest, installed model or runtime action.
