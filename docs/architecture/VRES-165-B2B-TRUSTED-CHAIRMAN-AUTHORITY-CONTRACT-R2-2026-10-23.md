# Vres-OS #165 — B2B Trusted Chairman Authority Contract, REVISED DESIGN R2

**Date:** 2026-10-23, Europe/Athens.
**Status:** R2 DESIGN DRAFT; INDEPENDENT R2 SECURITY REVIEW NOT_RUN; NO AUTHORITY ISSUED; NO IMPLEMENTATION OR LIVE OPERATIONS.
**Repository:** vosser24/Vres-OS. **Documentation branch:** docs/chatgpt-continuity-20261023.
**Accepted offline source:** feature/165-chairman-policy-foundation-20261023 at 32847410952e9d4620bf7046cbee4a41a7ddc73b.
**Earlier documents:** original v0 (blob 851f5323888bfd3043ba992abc8096834ee356d0) and R1 (blob d020d19afefbc18bd731ca2d79975128787e4eef) remain unchanged and independently DESIGN_REVISE. R1 was reviewed by Claude at operator-provided docs HEAD abde7e8086f1dfd3efd70318e24312112fcf314e, marker VRES_165_B2B_R1_DESIGN_REVIEW_COMPLETE.
**Issue:** #165 OPEN/PARTIAL; external authenticated-history/protected-authority gap F1 OPEN.

This R2 design is an attempt to answer R1 review findings R1-01 through R1-13. It has NOT passed an independent R2 review. Writing a specification does not generate authenticated operator consent, grant a trust token, bind an installed binary, cause protected Fable validation or change the installed Chairman model.

## 1. Security objective and negative authority rule

B2A R3 is accepted only as an inert comparison of canonical candidate history bytes to CALLER-SUPPLIED expected count/history/latest SHA-256. An adversary controlling both inputs can make them agree. No code in B2A authorizes a model change. The B2B trust service, when separately designed and approved, must prove the provenance of the expected history, independently bind operator intention and protected validation, and govern deployment at the real runtime enforcement point.

Positive authority is **not currently available**: there is no selected independently permissioned consent service, anchor store, trusted release source, validator attestation interface, runtime loader, installer or signing capability. B2B-1 MAY eventually define DENY-ONLY data schemas, serializers and negative checks that return only REFUSED(code) or INDETERMINATE(code). B2B-1 MUST NOT return approval, a permit class, successful validation, trusted anchor persistence, an installer capability, positive trust issuance or a model-activation API. B2B-2/B2C/B2D require separate security architecture review and explicit operator permission.

The requested Chairman Opus/medium policy remains candidate-only. Windows personal Vres remains at installed Sonnet/high. A refused installation may leave known old bytes intact but MUST NOT claim the proposed model was activated.

## 2. Trust actors, attacker tiers and runtime enforcement (R1-02)

**T1:** untrusted chat, pasted words, proposal JSON/rationale, telemetry, model descriptions, candidate files/manifests and claimed hashes.

**T2:** AI-agent/plugin/subprocess code with arbitrary normal same-Windows-user rights, including file/registry writes, ordinary same-user DPAPI, process and prompt spoofing, writable program settings, user-scoped installed artifacts and log manipulation. Claude Code permission dialogs, agent-driven scripts, user-writable config, a chat "AUTHORIZE" and agent-produced signed-looking artifacts have NO authority. Windows Hello UserConsentVerifier with a caller-chosen message and a result delivered to the same-user caller is NOT alone a T2-resistant consent ceremony.

**T3:** elevated admin/SYSTEM or compromised independent provider infrastructure; outside a claimed T2-resistance guarantee. Such exclusions must be explicit and operationally reviewed, not implied.

**Core enforcement distinction:** T2-resistant consent/anchor storage does NOT itself protect runtime-loaded files. Before real installation, a separate audit must identify the actual Chairman definition that the runtime loads, all override/search paths, ACLs, reparse points and who can modify them. These facts are NOT verified by this design; do not infer them from a Git checkout.

Two conceivable future guarantees are:
- **Prevention:** independently privileged writer and runtime loader enforce use of the protected release, with no T2-writable override path.
- **Detection/fail-closed at each use:** a verifier independent from T2 checks actual loaded bytes against the currently protected anchor at load/use time and refuses execution if they differ. A one-time file digest at install time is insufficient.

If neither can be demonstrated under a separately authorized physical audit, live model-governance integrity against T2 is NOT ESTABLISHED; transition to actual policy use stays BLOCKED. A personal same-user writable installation MUST NOT be described as T2-proof merely because an anchor CAS succeeded. This decision is an architectural requirement, not a claim about the current installed directory.

## 3. Independently trusted release provenance (R1-01) and first enrollment H_0 (R1-03)

The approved Chairman **release identity, source provenance, template bytes, render algorithm, protected validator pins, evidence-schema allowlist and model-family matching rules** must originate from a separately verified release trust root or the already protected PRE-STATE anchor H_n. Never elevate a hash of bytes submitted by the agent to approved-release status. GitHub source commit IDs or git ls-remote alone cannot authenticate a release when T2 may control the credentials or working directory.

Future positive validation must:
1. Obtain reviewed release identity/manifest from a T2-resistant release-verification channel whose exact trust source and permission principal were separately approved.
2. Fetch/verify exact immutable release artifact and template bytes through that channel, verify the protected release manifest and approved template digest, and recompute rendered Chairman bytes deterministically from trusted template plus explicitly proposed canonical policy. Reject altered body instructions even when model/effort frontmatter looks valid.
3. Bind approved source commit, template hash, renderer identity/hash, rendered hash, protected old worker/validator pins, target, installed baseline and proposed policy across the consent screen, independent validation, CAS intent, installation warrant and final readback. The trusted provider must show whether template/pins/release identity changed, with a clear change warning, not only opaque SHA strings.
4. Treat template, renderer, protected pin, schema-allowlist or family-rule changes as separate explicitly disclosed policy changes. A candidate or newly proposed policy cannot silently replace the current trust root.

**First-ever trusted anchor H_0 is not an ordinary upgrade.** A future separate genesis/enrollment ceremony MUST:
- Establish a previously reviewed manufacturer/release/root manifest through a channel independent of current same-user installed files.
- Independently verify the full starting template/release bytes, existing protected worker/validator pins, canonical target/machine and user scope, accepted schema/family rules and proposed initial history head. Local installed Sonnet/high settings alone cannot certify any of these.
- Present a trusted provider-rendered human-readable enrollment summary with explicit user-presence and target identity, and verify its event under a T2-resistant origin.
- Atomically persist epoch 0 and independently protected genesis reference with no prior anchor. All future H_n descend from this externally verified genesis. If a trustworthy genesis release or T2-resistant store cannot be established, refuse enrollment and leave all positive authority unavailable.

A fake unit-test H_0 or locally self-written release allowlist is NEVER an authoritative genesis. **No genesis service/store/credential is installed by B2B R2.** The currently installed Chairman is NOT being enrolled.

## 4. Canonical types, trust source precedence and target scope (R1-05, R1-10, R1-12)

The protected independent root controls trust-provider identity, release provenance, accepted evidence schema/version set and initial validator/model-family rules. After H_0, the current independently verified installed/governing H_n owns the authorized continuity values. Provider/root constraints are the outer limit; a candidate cannot widen them. An enrolled H_n must match the root-bound target and release policy; conflict among independently verified H_n, protected root and observed installed evidence means BLOCKED/INDETERMINATE, not selection of a convenient value.

**Pre-state validator pins** come from the currently verified governing installed release as authenticated through H_n under root constraints. Never from the new candidate or a pending successor. A proposed pin change must be independently validated under OLD governing pins and separately consented, and cannot take effect until authenticated installation/observation. Root/H_n/installed-pin disagreement blocks even a benign policy request.

Evidence is canonical, versioned and **domain separated** with a type/purpose/version discriminator INSIDE bytes being hashed, for instance: consent event, protected pre-anchor, new anchor intent, validation record, installation warrant, revoke event, recovery event and installation observation each have separate domains. SHA-256 shape alone never makes digests interchangeable. Accepted B1/B2A canonical history hashes remain the same legacy format and are bound as content identifiers, not silently redefined.

A trusted provider must independently DERIVE machine identity, SID, Vres install instance, physical canonical target root and current protected release identity. Agent-supplied target paths/IDs are assertions to check, never the authoritative source. At the future write/load boundary independently re-resolve paths, refuse Windows junctions/reparse points and any write or load path escaping the approved target. No currently installed target path is claimed verified.

The accepted schema-version allowlist and family-matching policy come from pre-state H_n/root; a candidate proposing weaker schemas or a wider model-family rule requires separately rendered consent and protected validation, never self-expands the validation criteria.

## 5. Strict authority ordering, consent presentation and provenance (R1-04, R1-09)

**H_n is a protected prior authorization anchor**, NOT a candidate-history document. C is the proposed successor canonical history and Chairman policy. E is a T2-resistant provider-confirmed explicit operator event. V is the independent protected validation record. H_(n+1) is a protected pending INSTALL INTENT created after CAS. W is a *different* future install-authorization event; W never equals E.

The only legal future policy-authority sequence is:
1. A T2-resistant authority provider independently reads H_n (epoch e_n, digest h_n, approved release/template/render provenance, current-governing pins, target identity, installed-observation binding and pending-operation status). H_0 must first be safely enrolled through §3. No independent provider exists today: if the read cannot be authenticated, INDETERMINATE, never positive.
2. A source proposes C with bounded canonical bytes. A **trusted validation component** (not the agent invoking arbitrary code) checks its history starts with actual H_n history and is a valid append/supersession. C does NOT define expected anchor values.
3. The trusted consent provider obtains exact canonical policy, history, release and target facts from independent protected services. It constructs a human-readable dialog FROM those verified facts (not agent text): old → new family/effort/version; exact history prior/proposed head and counts; machine/SID/install instance; changed-template yes/no and source/release identity; changed-validator-pins yes/no and old pins; approved model-family resolution rule; expected runtime effect, and explicit warning that installation/host physical observation are separate. Show bounded opaque digests alongside meaningful names. The UI must not allow an agent-chosen message to masquerade as provider-rendered consent. Record what canonical fields were actually displayed and attested.
4. The real operator may confirm, refuse or cancel. E is created only by a separately authenticated T2-resistant user-presence action, with provider-generated nonce/event ID, principal/session/channel/purpose, attested displayed-field digest, H_n digest/epoch, C/history/policy/release/target bindings and approval disposition. No user-controllable text, CLI token, ordinary Windows Hello caller-message result, clipboard string or model self-report is E.
5. The trusted protected validator obtains C/E/H_n and release bytes DIRECTLY through trusted-boundary reads, validates according to §6 with pre-state pins and returns a provenance-attested V. A model claim by itself is not the validation outcome.
6. The protected B2B authority service recomputes EVERY equality and runs atomic CAS as specified in §7. CAS consumes E/nonce and advances to H_(n+1), storing a pending install-intent reference to E/V/C. E never references the future H_(n+1) as independently anchored truth.
7. The later B2C installer cannot derive install permission merely from H_(n+1); it must obtain a separate W under §8. Host-observed model evidence remains still later.

The initial R1 suggestion of a "proposed successor summary" is REPLACED by the explicit fields in step 3. The provider must display template/renderer/release provenance and whether it differs from prior reviewed artifacts; opaque hash strings alone are not meaningful consent. To mitigate T2-triggered approval fatigue, future providers must rate-limit prompts, show request origin without presenting that origin as trustworthy, and allow cancellation without persistent positive tokens.

## 6. Protected validator as an independent, injection-resistant check (R1-07)

The independent trusted authority selects validator identity and protected worker/validator family/effort pins from the pre-state H_n/root; candidate C cannot nominate its own validator or relax its rules. Candidate pin changes are evaluated under PRE-STATE governance.

A future protected service—not an untrusted agent forwarding selected text—retrieves the canonical release/template, E, H_n, C and requested policy from protected sources and binds them in V: type/version, event digest, prior epoch/head, candidate count/history/head digests, canonical policy hash/family/effort, release/source/template/render identities, canonical target, validator identity/pre-state pins, schema/family rule, validation purpose, outcome and freshness.

**Deterministic code** under the protected boundary must perform structural, digest, target, sequence and old-pin checks. Model-based Fable analysis may assess bounded governed requirements but is never sole authority over these deterministic facts. Candidate rationale/template/chat content is explicitly untrusted DATA in a non-instruction position; prompt-injection text cannot choose the validator, alter tool permissions, select input bytes or produce an authority token. The protected wrapper must attest which data it fetched and what checks it performed, independently of the model's generated narrative. A textual "Fable PASS" or a model-produced signature is NOT positive validation.

B2B R2 has neither this provider nor an actual Fable run. No protected validation result is claimed.

## 7. Exhaustive protected CAS contract (R1-04, R1-05, R1-08)

**CAS is owned solely by the future protected B2B authority service**, not by installer B2C or an agent. One service/transaction domain must atomically enforce head advancement AND nonce/event consumption; if event/anchor registries are distinct and atomicity cannot be demonstrated, refuse. Failed-CAS retries do not revive a consumed event or accept an outdated H_n; any new try needs a fresh independently verified current head and separately valid event, unless a future reviewed service can prove same-attempt idempotent replay without new authorization.

Before CAS, the protected service MUST independently read and check ALL preconditions against its own verified records (never pass through alleged comparisons performed by the agent):
1. Root/genesis H_0 provenance verified; H_n is the sole latest protected head, epoch and prev digest exact, with no split-brain or schema downgrade.
2. H_n refers to the same verified OS user/machine/install instance, release/installed baseline and protected target; root constraints and installed-governing pin evidence agree.
3. There is **no unresolved pending-install or recovery interlock** at current H_n. A pending H_(n+1) cannot be used as the governing pre-state for a new proposal. Only a distinct authenticated revoke/recovery authority path can resolve pending state, and it cannot auto-install.
4. C has bounded canonical bytes, exact type/schema/policy digest, permissible family and effort, and verified prefix/supersession from H_n under the B1 chain rules. The trusted component first validates FULL C as a canonical, internally linked history. It extracts the canonical PRE-CHANGE prefix P containing exactly H_n.proposal_count historical entries; P may be derived from C but its content is NOT trusted until checked. It creates ExpectedChairmanHistoryIdentity from the independently authenticated H_n proposal count, canonical prior-history SHA-256 and latest prior-proposal SHA-256, then invokes require_canonical_history_match(P_bytes, expected_from_H_n). Only a matching prior prefix is accepted. Separately, it verifies that C extends that prefix by EXACTLY ONE newly proposed successor entry for this operator event, with correct prior-latest SHA link and monotonic policy version; it binds the FULL proposed C digest, policy and successor separately to E/V/CAS. It must NEVER compare the entire future C against the OLD H_n expected digest (a valid append would mismatch), and must NEVER derive an expected full-C digest solely from untrusted C and call that proof of independent trust.
5. Approved source, release manifest, template, renderer and deterministic rendered bytes are sourced from the independent reviewed release root or H_n. Their hashes match C/E/V and the provider-rendered human changes; changes to those trusted elements were expressly approved.
6. E was issued via T2-resistant interactive provider; exact principal/session/current-user SID, nonce, purpose and scope are verified, the displayed canonical values match C/H_n/release/target and the disposition is explicit APPROVE. Decline/cancel/unknown purpose always refuses.
7. E binds the exact H_n h_n/e_n as PRE-head and the proposed C digests; E does not pretend H_(n+1) is a preexisting trusted anchor. Event/nonce unspent, non-revoked and fresh under §8.
8. V comes from pre-state-pinned independent protected validator, NOT C, with an independently attested acceptable outcome; V.event_digest equals digest(E), V.prev_h_n equals h_n/e_n, V.C/policy/source/template/renderer/target/pins/family-rule all match E, C and verified H_n, and V is fresh under §8.
9. Current trusted provider head is still exact H_n/e_n; no competing writer, divergent history, revocation record, schema downgrade, pending operation, trust-root or target change occurred since pre-read.
10. On all checks PASS under a genuine future provider, atomically CAS H_n→H_(n+1), increment epoch exactly once, record digest(E), digest(V), C/history identity and pending-install intent, and consume E/nonce in the SAME protected transaction; any write/availability conflict is fail-closed.

**The above is a future positive-service contract, not a B2B-1 authorization algorithm.** B2B-1 cannot execute or mock a success path: it lacks all protected reads and may only reject malformed claimed descriptors or return INDETERMINATE where true provenance is absent.

No subsequent candidate may supersede a pending-intent head. New policy, pin change or rollback requires resolving pending state with separately reviewed trusted mechanisms; installed pre-state pins do not change merely because policy intent was anchored.

## 8. Two distinct freshness windows, installation warrant and revocation (R1-06, R1-11)

**Policy approval event E:** proposed maximum age **300 seconds from the trusted provider's completed human confirmation to successful protected CAS**, measured with provider-authenticated monotonic/freshness evidence, not an OS clock controlled by T2. The protected V outcome MUST be generated after verified E and while H_n stays current, and also be within E's window. Expired E/V, unknown provider time, stale head, changed user/target or pending revocation refuses CAS. E is consumed at CAS and must NEVER be re-used to install or recover.

**Installation event W (distinct trust domain):** because E has been consumed, a future B2C installation requires a **new trusted provider-rendered operator confirmation** explicitly bound to current H_(n+1) pending intent, approved release/target/rendered bytes, exact installed baseline, expected outcome and fresh nonce. The prospective **300-second window from W confirmation to atomic installed-byte commit** must be separately approved. It is not proof that the runtime will load those bytes; independent load verification is still required. W cannot be produced without a real trusted provider. Any installer failure, expiry, mismatch or crash consumes/invalidates the particular attempt; retry requires a separately authenticated NEW W or a distinct independently approved recovery event. A single W must never cover a different epoch, release, target or model family.

**Revocation/refusal:** uses its OWN domain-separated event type, authenticated issuer/principal, target, reason code, prior protected epoch and fresh provider challenge. It may require real user presence according to future consent-provider policy; a T2 agent may cause denials but cannot forge an authoritative positive cancel/approval transition. A genuine revoke BEFORE CAS defeats E; revocation AFTER H_(n+1) but before install blocks W and requires a protected FORWARD epoch decision; revocation after install creates separately approved remediation, never silent demotion. Any conflict between revocation and install is checked by protected service at the final write boundary. An event after a consumed E cannot resurrect E, and recovery cannot bypass revocation.

Actual trusted clocks, nonces, event stores, installer warrants and revocation verifiers are NOT implemented and do not run.

## 9. Non-authoritative staging, installer owner, crash recovery and runtime use (R1-08, R1-02)

**Unique owner/order:**
- Before B2B CAS, a future installer MAY compute/render or stage bytes in a non-executable NON-AUTHORITATIVE temporary area for planning. It may not modify active release, expose an INSTALL_PREPARED or AUTHORIZED capability, or treat an agent-written staged file as trustworthy. This is merely STAGING_CANDIDATE_UNTRUSTED.
- Protected B2B provider owns the §7 CAS, creating an independently anchored **PENDING_AUTHORIZED_INTENT** (a derived description of verified evidence, not an input status field).
- B2C obtains a separate W under §8, independently verifies the approved release and target/source/render identity, recomputes bytes from trusted template and policy, then stages and atomically writes under a trusted execution boundary. It must verify final on-disk bytes and separately observe actual runtime-loaded identity.
- Derived labels are recomputed and never accepted as privileges. There is no authoritative INSTALL_PREPARED state before CAS; staging pre-CAS grants nothing.

**Crash and recovery semantics:**
- Before CAS: discard inert staging only; no installed change. A failed CAS leaves prior H_n/installed state unchanged.
- After CAS, before B2C commit: H_(n+1) denotes intended, uninstalled policy; verified old Sonnet/high bytes may remain. No automatic install or new successor; recovery remains BLOCKED until a separate valid W/recovery ceremony.
- After file write but before trusted installed-byte readback: neither "INSTALLED" nor "active Opus" may be asserted; reconciliation is BLOCKED. A fresh independently verified operator recovery event and trustworthy target/load-path inspection are required. Do not rewrite anchor from observed user-writable bytes.
- After installed-byte readback but before protected completion record: still BLOCKED pending independent journal and observation reconciliation; duplicate install attempts are not allowed without a fresh verified transaction.
- If a T2 agent can change the runtime-loaded definition after commit or override search paths, a one-time readback does NOT protect execution; no live T2-resistant governance claim until preventive protected load path or trusted per-load/per-use mismatch refusal is separately demonstrated (§2).

A future durable journal must be maintained by a service resistant to T2 mutation; agent-written journal text is not a trust source. No installer/journal/storage is implemented in B2B R2.

## 10. Model alias policy and host-observed evidence (R1-10, R1-13)

The requested generation-tolerant alias opus and effort medium do not alone establish what physical model ran. A trusted pre-state/root-approved family matching rule must define permissible provider-resolved model identities; widening this rule needs new explicit approval and protected validation. If an alias is unavailable or silently resolves to a different family, record FAILED or DEGRADED, never a successful Opus/medium claim. No telemetry-based automatic Chairman promotion or demotion.

Physical host-observed identifiers and timings sourced from same-user Claude Code or logs are T2-modifiable claims, NOT independently authenticated proof. Future #169/B2D must identify a separately trustworthy measurement source (e.g. independently attested provider-side usage evidence) or explicitly classify a field as unverified observation. Source policy, intended configuration, installed bytes, loaded bytes and provider-side physical model are different states.

## 11. Deny-only B2B-1 contract and negative tests (R1-12)

Only after independent R2 design acceptance may B2B-1 implement frozen, explicitly UNVERIFIED descriptors such as ClaimedAnchorHead, CandidateProposal, ClaimedConsentEvent, ClaimedValidationEvidence, InstallTargetIdentity, ClaimedReleaseBinding/TemplateProvenance and ClaimedFamilyRule. Descriptors MUST NOT expose trusted=True, approved=True, a positive-state enum, provider handle, capability token or privileged callback.

**Return type is only Refused(code) or Indeterminate(code), backed by a CLOSED reason-code enumeration** with no echo of untrusted free text or secret-bearing exception. No Permit/Authorized/Approved variant exists in B2B-1. Every caller must treat either result as NOT AUTHORIZED. A future positive result, if ever approved, must come from a NEW, separately reviewed real trusted-provider adapter and a DISTINCT type/API; it cannot be added as a third member of the deny-only result enum.

Pure canonical serializers/parsers may use type/purpose/version-separated SHA-256 and fixed bounded input sizes, rejecting unknown/duplicate/missing keys, old schema, malformed encoding, control bytes, overlarge files and cross-domain digests. Invalid claimed evidence is REFUSED; missing/unknowable real provider state is INDETERMINATE. No wall-clock read or local data/registry/DPAPI/GitHub state may be elevated into trusted proof. Unexpected exceptions fail closed, never return an approval-like boolean.

Negative tests must retain original v0/R1 N-01 through N-21 and add R2 denial cases:
- Claimed source/template/render bytes self-consistent but NOT on independently trusted release allowlist.
- Caller-supplied release hash substituted for protected pre-state release identity.
- Claimed H_0 created solely from same-user installed Sonnet/high file or local DPAPI/registry.
- Claimed current install root is same-user writable with no trusted loader/per-use verifier.
- Proposed full successor C is incorrectly compared for exact equality to the OLD H_n digest; or the expected full-C digest is self-derived from C. Verify prior canonical prefix P against H_n independently, then require EXACTLY ONE new linked successor entry; refuse modified prior entries, missing prefix, multi-entry jump, fork or rollback.
- Mismatch in ANY individual CAS precondition in §7, including E/V event, head, epoch, count, history, pins, target, release, model-family rule, consent rendering or nonce.
- Simultaneous claimed anchor states; pending-intent head used as governing H_n for a new proposal.
- Attempted reuse of E for installation, expired W, recovery without a fresh trusted ceremony, replay of revoke as approve.
- Model validator accepting prompt-injected candidate text as instructions, or agent selecting fetched validation inputs.
- Agent-controlled approval text or Windows Hello caller message presented as trusted rendered consent.
- Obsolete evidence schema or candidate-widened schema/family allowlist, cross-type digest, unverified host model observation.
- B2B-1 enum or callbacks gaining a positive result path, simulated "trusted" provider, test key "approved" behavior, filesystem/registry/credentials/network/DB/installer imports.

Tests prove deny-only behavior under existing tests/conftest.py isolated protected app-data and PostgreSQL/child-process tripwires. They cannot prove a T2-resistant real consent/anchor/loader; such physical evidence belongs to future independently authorized integration reviews.

## 12. Reviewer R1 finding disposition, exact R2 sections

| Finding | Severity | R2 correction / remaining gap |
| --- | --- | --- |
| R1-01 | HIGH | §3 independent release/template/render trust root, provider-computed bytes, changed-template consent; REAL reviewed release root still not selected |
| R1-02 | HIGH, target not observed | §2/§9 separate T2 runtime enforcement or independently trusted load-time refusal; no false prevention claim; real installed ACL/paths NOT VERIFIED |
| R1-03 | HIGH | §3 explicit trusted genesis H_0 enrollment from independent reviewed release with user-presence, pin/target verification; real provider NOT SELECTED |
| R1-04 | MEDIUM | §7 exhaustive CAS preconditions, trusted component ownership and protected comparisons; no positive CAS presently |
| R1-05 | MEDIUM | §4 root/H_n/installed-pin precedence, conflict refusal and pending-install interlock until independently resolved |
| R1-06 | MEDIUM | §8 E validity ends at CAS, V freshness bound to E; separate fresh W for install/recovery, explicit windows and events |
| R1-07 | MEDIUM | §6 trusted boundary input fetching, deterministic checks, candidate text as untrusted data, model not sole verifier |
| R1-08 | MEDIUM | §9 optional inert pre-CAS staging, B2B-owned CAS, B2C-owned independently warranted write; derived conditions corrected |
| R1-09 | LOW | §5 exact human-readable canonical old/new field display, template/pin deltas, source context, rate limits and Windows Hello caveat |
| R1-10 | LOW | §4/§10 allowlist/model-rule sourced from trusted pre-state/root; changes need full consent |
| R1-11 | LOW | §8 domain-separated revoke/refuse event with authenticated issuer and priority at commit |
| R1-12 | LOW | §11 closed refusal codes, no positive-state symbols in B2B-1, future approval a separate API only |
| R1-13 | LOW | §10 same-user host logs untrusted unless independently attested; #169 future physical proof |

R1 original review also reported original F-01 through F-16: v0/R1 historical DESIGN_REVISE evidence remains intact. The wording in R2 is not an independent verification of sufficiency; reviewer must challenge residual trust-root, H_0 enrollment, T2 loader and W installation consistency.

## 13. Open engineering decisions and immutable STOP gates

**No real trust provider is chosen.** The design demands T2-resistant consent, release trust root, genesis, anchored history/CAS, independently governed Fable wrapper and runtime load enforcement or detection, but neither Windows Hello nor DPAPI/registry/GitHub alone is asserted to deliver that. All positive implementations require distinct security evaluation and operator approval, currently absent. Never use this design to justify user presence, pin trust or validated consent.

B2B-0 R2 independent review is NOT_RUN. B2B-1 code waits for DESIGN_ACCEPT or a specifically recorded, narrowly accepted design boundary; B2B-2 positive authority, B2C installer, B2D/#169 host tests and any main merge/install are separately gated. #165 and F1 remain OPEN.

**LIVE_SCHEMA_048_INCIDENT=OPEN.** PostgreSQL last reported STOPPED; NO contact, not even read-only SELECT/health probe; no migration, Vres startup/setup/bootstrap/selftest. D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 blocked, L-04 OPEN, PA-01..PA-08 incomplete; native trust not approved, positive issuance disabled. No real credentials/vault, source signing, global Claude settings/plugins/hooks mutations, model-provider calls, installed release update, PR or main merge.

Last accepted feature source remains 32847410952e9d4620bf7046cbee4a41a7ddc73b: B2A R3 independent Windows offline ACCEPT, 95 PASSED lines/pytest exit 0 and R3-PROC-01 disclosed extra Python version probe. B2A R2 060756b0 independent REJECT (91/92) and original c01152e3 STATIC_REVIEW_REJECT retained. Earlier F2 test followup 36a41b6 3/3, F2 implementation b77e0ee 101/101, B1 history f8237bb 99/99, Phase A R2 11f2f868 53/53, P2-A1 R4 security 3ba41d5 183/183 offline accepted at their separate exact SHAs, with previous rejections preserved.

Installed user Windows Vres release 20261022172833-4d82147b from original P2 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c is unchanged. Installed Chairman stays Sonnet/high; requested Opus/medium is candidate-only. Product main last observed 9a8acc5d464b96432a93cb95daa9581412fb07ee, unchanged. All V-01..V-42 functional development backlog remains active, not installed/production-ready.

## 14. Independent review requirements and next exact step

NEXT: a new isolated detached Windows DOCS review worktree for this separately committed R2 design, preserving the R1 review checkout. Operator rechecks exact remote docs SHA/parent, original R1/v0 blobs, R2 blob, file diff allowlist, diff --check and clean status. Claude must READ the entire R2 draft and original R1 plus R1 DESIGN_REVISE handoff, using Read/Glob/Grep ONLY. Claude may not use Bash, Git, Python, pytest, MCP, subagents, database, vault, network or source edits. Require section-by-section verdict on R1-01 through R1-13, remaining issues, provider and physical target limits, deny-only B2B-1 readiness, and one final DESIGN_ACCEPT / DESIGN_REVISE / DESIGN_BLOCKED. Report DESIGN_ONLY, TESTS_NOT_RUN, NO_AUTHORITY_ISSUED, NO_MODEL_ACTIVATION.

If R2 accepted, proceed only to B2B-1 PURE OFFLINE denial-contract source code in a new exact feature commit and independent isolated Windows review, not to real authorization. If revised again, preserve design failure and append a separately named docs revision. No positive trust issuance.

## 15. New-session continuation

Read docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md then B2B R1 DESIGN_REVISE / R2 security revision handoff, then the R2 architecture and prior v0/R1. The R2 draft is NOT independently reviewed; its committed SHA/blob must be read back, then reviewed by Claude static only in a NEW docs worktree. Previous B2B v0 and R1 were both DESIGN_REVISE; accepted feature source remains B2A R3 at 32847410952e9d4620bf7046cbee4a41a7ddc73b (95 PASS lines, exit 0), F1 and #165 open. No runtime, PostgreSQL, signing, vault, provider, installer, global Claude or main merge actions. ChatGPT develops and commits, Claude reviews independently, user operates guarded Windows. Record all future checks with exact SHAs; don't turn design into proof of trust.
