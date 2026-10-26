# Vres-OS #165 — Independent R3 reviewer post-review ERRATUM for denial-only B2B-1

Date: 2026-10-26, Europe/Athens.
**Status:** Author-written documentation required by the independent Claude R3 DESIGN_ACCEPT FOR B2B-1 DENY-ONLY. The erratum itself has NOT been independently reviewed/tested. It does NOT change the independently reviewed original R3 Git blob 110ccffcbc1c1f00f5b674b4836fed432708f4ea or authorize real positive trust.

## 1. Reviewer-mandated fields before any B2B-1 code handoff

**R3-N03 governing G reference.** A strict tagged union: PRE_HISTORY_BASELINE, meaning the independently described pre-history installed baseline with no B1 proposal entry; OR L_ENTRY, meaning an existing B1 entry with bounded sequence 1..128 and exact lowercase 64-hex proposal SHA. No implied latest-proposal-to-governing coercion. Neither a syntactically well-formed claim nor a user-supplied SHA becomes trusted proof in B2B-1. An initial H_0 may use PRE_HISTORY_BASELINE; it is never a valid empty B1 history.

**R3-N05 pending Q.** A strict tagged union: NONE (JSON null), PENDING(intent), or RECOVERY(intent, investigation_ref). RECOVERY is STILL pending, blocks a new proposal and does not clear Q, install, approve, authorize or repair. Reject unknown/missing/extra tags/fields and spoofed COMPLETE/INSTALLED labels. Future protected resolution belongs to new separately reviewed APIs, not deny-only A1.

**R3-N04 canonical C and digest domains.** Candidate raw B1 history must have exact bytes type, bounded input and strict canonical equality: parse under accepted B1 source, compute parsed.to_document() and demand raw bytes equal canonical bytes. B1 acceptance of noncanonical valid JSON is insufficient. The rule applies at p=0 genesis too. Legacy B1 history SHA (hash of canonical standalone B1 whole-history bytes) is distinct from a NEW B2B evidence hash computed over explicitly type/purpose/schema-domain-separated canonical claimed evidence. Cross-type digests must be refused. For p>=1, prior prefix P must be rebuilt as a standalone B1 canonical history and matched against a real externally authenticated head; A1 has no such trusted head. At p=0 no fake empty history, no B2A count-zero call: use typed genesis nulls and exactly one first B1 version1 proposal shape. A claimed internally matching C+hash NEVER means approval.

## 2. R3-N08 normative future security STOP requirements NF-05..NF-10

R3's original table mentioned requirements but did not insert their normative texts into the referenced sections. These mandatory gates remain OPEN:
- NF-05 real B2B-2: protected head CAS digest+epoch, nonce/event consumption and cancellation/revocation visibility must share provably linearizable transaction semantics; check-then-commit across untrusted stores forbidden.
- NF-06 real B2C/B2D: independently assess and enforce ALL inputs determining actual effective Chairman family/effort, including source definition bytes, user/project/global configurations, CLI/session flags, environment, override/search/load paths, provider alias resolution and fallback. One-time installed file hash is not proof of physical model identity.
- NF-07 real B2B-2: reviewed source/template/render release trust publisher must be independently secured from T2 same-user agents and AI-author GitHub credentials, with human verification of exact artifacts; GitHub commit identity alone confers no native trust.
- NF-08 real B2B-2: authenticated genesis enrolled once per protected machine/SID/install lineage; changing instance identity cannot create unlinked H_0; rollover requires distinct reviewed ceremony.
- NF-09 real B2C: W issuance/commit must re-check non-withdrawn trusted release root, pending epoch/age, policy family rule, exact target/bytes and revocation; stale pending must not auto-install.
- NF-10 real B2B-2: independent V must attest the actual provider-resolved protected validator model identity; silent fallback/mismatch/unattested execution cannot be positive Fable validation.
Adding docs does NOT demonstrate implementation/physical verification of any of these.

## 3. R3-N09 stale references and historical integrity

In the immutable R3 artifact, phrases "only after independent R2 design acceptance" or "if R2 accepted" must be interpreted for forward execution as "independent R3 DESIGN_ACCEPT **only for B2B-1 deny-only**, subject to this erratum." Original R3 table references to "§5.1" or "§7.4" mean step 1 of §5 and item 4 of §7, not literal headings. Do not edit the independently reviewed R3 SHA/blob to hide the historical wording.

## 4. Other R3 findings remain for real B2B-2 / B2C design

**R3-N01:** ABANDON/REVOKE after a partial byte write cannot clear pending unless actual installed and loaded bytes independently match governing G; design a separately W-warranted RESTORE_GOVERNING or alternative fail-closed recovery for later. **R3-N02:** COMPLETE must bind new G to EXACT proposed Q/E/V/W proposal/release/render, not merely observed mutable bytes. **R3-N06:** consent displays both completed installed G and latest L with disposition. **R3-N07:** do not manufacture alternate-model transitions; each genuine intermediary needs full E/V/CAS, with equal-to-G request/revoke issuer criteria separately reviewed. None of these is a B2B-1 positive-operation permission.

## 5. A1 permitted shape and testing conditions

Only inert frozen/slots explicitly UNVERIFIED claimed descriptors, bounded schema-valid/canonical/domain-separated bytes, CLOSED NEUTRAL refusal codes and Refused(code)/Indeterminate(code) outputs. Neither result can ever authorize through bool()/==True or reason-code elimination. Future positive issuance must be a DISTINCT real-provider-owned type/API, subject to independent review and explicit user authorization; not a third denial enum variant. No file/network/registry/DB/credentials/signing/provider/installer imports, no storage, no user-presence or host model runtime. B2B-1 code is NOT created/tested by this erratum.

Live schema-048 PostgreSQL incident OPEN (NO contacts even SELECT); F1/#165 OPEN, installed Chairman Sonnet/high and Opus/medium remains a candidate only.
