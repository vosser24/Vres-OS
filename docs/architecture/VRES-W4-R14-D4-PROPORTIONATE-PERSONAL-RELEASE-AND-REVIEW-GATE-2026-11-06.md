# Vres-OS — W4 R14-D4 PROPOSED proportionate PERSONAL Windows release and integration-safety decision

**Date:** 2026-11-06 (Europe/Athens). **Status:** DESIGN-ONLY / OWNER-DIRECTED REBASELINE PROPOSAL / EXTERNAL INDEPENDENT REVIEW NOT_RUN / NO EXECUTION AUTHORITY.
**Product:** a proper, maintainable, production-quality **PERSONAL daily-operations application for ONE Windows user**; existing Chairman, original task, decision, memory and credential owners. No enterprise IAM, multitenant product, second Chairman, cloned task database or disconnected applications.
**Decision motivation:** owner explicitly requested proceeding with recalibration after asking whether the R14 review was aimed at personal usage or a distributed commercial product. This permits drafting a proportionate proposal; it does not approve a new Windows command, code branch, installer, source publication, trust key or incident clearance.

## 1. Problem statement; what is actually required

The original W4 R14-D1/D2/D3 designs protect against a powerful adversarial source distributor, mutable candidate, and replacement of an initial verifier/trust-policy. D3 proposes a native authenticated Windows verifier, out-of-band approved binary, isolated ECDSA P-256 signer, bespoke exact-byte manifest and fresh per-release approval. This design is technically motivated for high-assurance independent-publisher releases, but **the owner has not requested public distribution** and its initial trust root does not exist. Making a new publisher/key/certificate/recovery stack the mandatory next development cycle is disproportionate to a single-user personal workflow, *unless the owner consciously chooses that stronger threat model later*. D3 remains an archived OPTION with no operational authority; it is not adopted, silently erased or falsely marked unsafe.

The actual priority is to deliver one daily-use Windows Vres-OS: helpful conversational Chairman, task continuity, simple fresh/legacy onboarding, evidence-backed recall and same-user resource reuse, reliable recoverable update, real Visual Studio UAT and a limited pilot. Preserve **all** V-01 through V-42 and M0 through M8 without falsely declaring deferred items complete. Source-of-truth functional and planned milestones are the 2026-10-22 full functionality register, 2026-10-30 personal daily-operations plan, 2026-10-31 full Windows acceptance board, and 2026-11-05 complete personal development/release/UAT plan.

## 2. Security boundary and the required honest trust statement

**Proposed accepted-risk profile, not yet accepted by reviewer/operator:**
- Protected: accidental corruption, ambiguous releases, wrong working directory, accidental hook/DB activation, stale task/adoption inputs, ordinary untrusted downloaded source substitutions, secrets in logs, unauthorized changes to the existing installation, unrecoverable update, erroneous ZIP/path handling, irreversible user-data mutation.
- Assumed for a PERSONAL offline gate only: Windows installation and available built-in verification tools are trusted, the user deliberately selects a **specific** pinned source commit and expected SHA-256 provenance, a trusted official Python runtime is independently validated where applicable, source/test outputs remain in separately approved disposable locations, no active same-user adversary races the verifier or replaces both launch mechanism and policy, and the local admin/kernel are not malicious.
- **Not protected by a Git checkout SHA, source digest or PSF Authenticode alone:** malicious GitHub account/repository provenance, an already compromised Windows admin/kernel, or same-user active substitution of an executable after a path-based hash check. Git SHA-1 is an object identity, not a publisher signature. A valid Python Software Foundation signature authenticates Python's producer, **not** Vres source or its publisher. Any risk-acceptance of these limits requires informed owner approval *after* an independent review.
- Avoid claims that merely using Windows Defender, Smart App Control, App Control for Business, a signed PowerShell script, file hashing or a non-writable attribute authenticates the app source or guarantees containment. Microsoft describes script-enforcement limitations, notably for third-party script hosts. None of these controls has been inventoried or tested on the actual PC.

**Proportional future trust baseline (proposal, not presently approved):** exact GitHub commit/tree/blob verification plus independent exact SHA-256 inventory bound to an operator-selected release identity, reviewed source/test changes and validated official Windows tooling; clear identification of trust dependencies on GitHub, Windows, Python, source reviewer, and local operator. No self-signed in-repo key, fabricated immutable binary, unsigned network bootstrap script, monkeypatch or R13 bypass. Add signed publisher release channels **only** if separately needed and provisioned.

The initial trusted execution problem is not magically solved by downgrading high-assurance requirements. The revised threat assumptions must be externally reviewed; if they are not consciously accepted, **the existing R14-D3 external trust-root BLOCK still applies to operational staging**. An untrusted W4 Python direct-file entrypoint runs import/bootstrap logic **before** its R13 refusal; it is NOT a trusted Phase A verifier.

## 3. Hard technical and incident boundaries, NOT changed by this proposal

- R13 feature HEAD bcf62460d68caebfdbd0e838d44c5997992c5fbc, tree 9bbc5615fef4a8f785e9ddb0056e9430ffe25d63 and sole parent 0badcd34d1eafbce5f815512a489d70cb240eecd must remain intact. R13 build_no_launch() operational staging universally refuses; direct-file bootstrap before refusal is not an independent trust anchor. The original release_artifact.stage() and POSIX BoundOutput can still write separately and must not be used as a Windows release workaround. Destructive interruption rollback remains STATIC_REJECT.
- LIVE_SCHEMA_048_INCIDENT=OPEN: **NO PostgreSQL even SELECT**, directly or indirectly, including startup/health, hooks, plugins, migrations, legacy introspection or tests that touch a live DB.
- HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: **NO ordinary native Claude Code or installed hooks**. Original P3 incident OPEN. No independently trusted F1/Fable positive authority granted.
- No installed P2 modification or actual UAT; current installed P2 physical state NOT_REVERIFIED (historical source 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c). Historical Chairman Sonnet/high; Opus/medium NOT_INSTALLED.
- Do not touch real credentials, user-profile, PRISM, legacy project, protected worktrees, Windows Sandbox R2, Vres runtime, installer, migration, completed TASK-DAY-01 original note/desk, product main, or protected portable P1 copies. No real Windows source/test/output roots, commands, network-dependent installed-host tooling, or staging under this document. New exact operator consent and *prior independent security clearance* are mandatory.
- No real credential request; no operational key generation/signature; no crypto verifier implementation; no R13 guard bypass, monkeypatch or weakening; no destructive cleanup, no POSIX stage.

## 4. Coherent personal product delivery strategy

Keep **ONE unified delivery train**, not an additional standalone P1 app and not an endless chain of cryptographic microtests. Preserve the accepted historical W1/W2/W3 narrow offline Windows evidence without upgrading its acceptance scope. Preserve the full V-01..V-42 trace register; an incomplete row remains open.

| Order | Integrated milestone | User-visible proof / exit | Holds |
|---|---|---|---|
| W0 (existing) | Exact baseline and integration gap reconciliation | Verified main/docs/W3/R13 ancestry, original owners, installed P2 known-vs-unverified status, source/release contract | Docs and read-only only now |
| W1–W3 (accepted narrowly) | Task-to-outcome continuity, first-use/onboarding, safe memory and resource reuse | Original accepted offline adapters and selected real P1 Daily Review preserved; no new second state stores | Do not infer full installed/host acceptance |
| W4-PERSONAL (revised proposal) | One coherent source-only, reversible, personal Windows release/recovery boundary, not public distribution | Pre-execution source identification, full original-owner inventory, deterministic original source-only package, explicit held runtime dependencies, no side effects on protected locations, reproducible evidence | **Implementation NOT_AUTHORIZED until separate independent review and owner approval** |
| G1 | Independently dispose of P3 host-hook and schema-048 DB incidents through an approved safe method | Exact incident-specific approved evidence, not a generic PASS or paper clearance | NO host/native Claude/DB contact while OPEN |
| P2 | One separately consented protected current-user release update | Actual signed-off target, before/after hashes, backup/restore, unchanged older copies | No current permission |
| U1 | #169 actual Windows / Visual Studio / scoped legacy UAT | Real observed approved flows and error/recovery evidence | NOT_RUN |
| U2 | #170 bounded personal daily-use pilot | Repeated useful tasks, fault recovery and user signoff | NOT_RUN |
| M8 | Full long-term optional/held breadth | V-08, V-10, V-13–16, V-18, V-20/21, V-25/26, V-37 and other exact register entries explicitly maintained | No false deletion or acceptance |

Specific open functional issues #165–170 and #176 retain their current/historical program state, not closed just because the release plan is simplified. #163/#164/#174 historical status remains separately preserved. Original P1, W0, W1, W2, W3 and W4 R1–R13 security findings and rejected attempts A12/A13/A16/A19 remain evidence, never erased.

**Next actual development goal after separate security clearance:** reconcile/complete an integrated personal source-only release candidate that composes existing original owners and accepted functional adapters, without invoking the callable R13 production writer or legacy stage. Select a dedicated exact-parent source feature branch only after explicit permission; keep R13 hold untouched. One coherent offline gate is preferable to serial artificial proof exercises.

## 5. Proposed P0/P1/P2/P3 proportional change gates

These are **suggested interpretations**, not a revision of any historical approvals:
- P0: read-only GitHub metadata/source/architecture and docs-only changes clearly approved by the owner; no execution, secret, host, or installed state.
- P1: permitted, separately authorized disposable **synthetic offline** test on reviewed exact bytes with reviewed command, explicit allowed path, expected external effects, and unchanged neighbors; no real user state, hooks, PostgreSQL, or network. Source-only functionality can be assessed here without a commercial signing chain if the narrow trusted-tool/source assumptions were independently reviewed and explicitly accepted.
- P2: protected current-user install/profile/governance/credential or data changes, only after G1 clearance, exact impact, independently reviewed rollback/recovery evidence and fresh informed consent.
- P3: high-consequence uncertain incident/authority/destructive activity; keep refused until specific independent evidence and explicit owner authorization. Never convert an OPEN incident into P1 by changing a label.

For the current work, **ONLY P0 documentation design is authorized**. The previous work's P1/P2/P3 historical nomenclature and approvals must be cross-checked before implementing any gate.

## 6. Safe reviewed release design criteria, not an executable plan

A future independent reviewer must validate all of these before any Windows gate:
1. **Trust origin:** how the approved commit/source SHA-256 and official Windows/Python tooling are independently obtained and checked; exactly which attacker classes are excluded. If GitHub or local Windows is compromised, do not promise protection.
2. **Pre-execution boundary:** no W4 candidate module import, direct-file bootstrap, Vres CLI, hooks, network or database contact before a trusted source preflight. Proposed approved preflight tooling must itself have a defensible provenance. Pure GitHub GET review now is safe; no local commands yet.
3. **Original owner compatibility:** exact release_artifact / release_inputs owner APIs, accepted W3 R2 base and 13 pins, full source inventory, SOURCE-MANIFEST.json, 001–041 inert SQL SHA-256, 042+ exclusion and recorded dependency-wheel closure NOT_RUN. Existing R13 _zip_bytes is source-only test helper but is behind the operational guard and may not be monkeypatched into a Windows release. Establish a separate reviewed legitimate production path.
4. **Windows filesystem boundary:** never rely on POSIX mkdir/lstat/dir_fd alone, post-close pathname stability, Win32 string prefix, ACL assumptions or symbolic root names. Any future write requires scoped disposable Windows NTFS testing and identity/reparse/ADS/hardlink/collision/rename/crash/post-close evidence. Initially favor in-memory/data-only verification to minimize write attack surface.
5. **Noncontact:** no original user notes, installed P2, credential broker real secrets, live DB or host hook routes; a permitted synthetic fixture is not proof of installed behavior.
6. **Single evidence-rich integrated gate:** positive correct **original-owner** source-only packaging and real SHA-256, fail-closed negative input swaps/hidden migration/extra paths/changed owners/policy mismatch/interruption, unchanged R13 refusal, unchanged protected state, exact command and independently observed result. Authored pytest count alone is not PASS. No fake positive forged by replacing stage guard.
7. **Recovery and practical use:** accurate version/manifest, one named disposable candidate root, explicit rollback **plan** not destructive action, user-visible task journey, no repeated approval ceremony for ordinary low-risk functions; real install/rollback only much later after separate consent.

**No new source/test/output root, Windows PowerShell, Python, build, key or installer is authorized by this document.**

## 7. Independent review brief: precise questions and mandatory verdict

Assign a genuinely distinct reviewer with read-only GitHub access and NO access to live Windows host / native Claude/hooks / PostgreSQL. That reviewer must read this D4 draft **against** R14-D1/D2/D3, W4 R13 source/tests, original owner release_artifact/release_inputs, 2026-11-05 personal integrated roadmap and original V-01..V-42 register; verify latest GitHub refs, trees, sole parent/diffs/blobs and accepted W3 ancestry.

Require a written three-part verdict:
- **THREAT_MODEL:** Is the proposed single-user assumption (trusted OS and selected official tooling, pinned source, no same-user/admin hostile actor) defensible for an **offline synthetic source-only gate**? Identify what it definitely DOES NOT protect.
- **RELEASE_DESIGN:** Can a proportionate exact-source, trusted-preflight, no-launch in-memory release candidate avoid D3 publisher hardware ceremonies **without** pretending an attacker-controlled Python entrypoint or Git SHA-1 is an independent trust root? Identify necessary minimum corrections.
- **OPERATIONS:** Explicitly REFUSE or condition each planned Windows command, root creation, Stage, installation, protected-state access, native host hook, DB and destructive rollback. An independent static design endorsement is **NOT** installed-product clearance or a Windows security gate.

Mark no reviewer result as PASS until an actually distinct reviewer produces it. If safety cannot be argued under the narrowly scoped threat model, preserve D3's BLOCK; do not relax R13.

## 8. Current evidence ledger

**PASS read-only:** live canonical docs/main/R13 refs as of design review; raw Git commit tree/parent headers and ancestor comparisons from prior read-only W4 R14-D3 examination; R14-D3 / D2 / D1 exact source documents and original release-scope source paths read; original 2026-10-22/30 and 2026-11-05 roadmaps consulted.
**DESIGN_ONLY:** this proposed proportional personal trust boundary, source release workflow, and independent-review questions.
**NARROW_STATIC_ACCEPT retained:** R13 all-platform operational refusal before selected paths; bounded advisory interruption inventory, not arbitrary safe execution.
**STATIC_REJECT / BLOCKED:** all operational Windows/POSIX staging, destructive rollback, R13 bypass, unverified source execution, install/release.
**NOT_ESTABLISHED / NOT_GRANTED:** alternative source trust root/risk acceptance, independent D4 review, effective Windows trust boundary, owner authorization for any Windows operation, F1/Fable positive authority.
**NOT_RUN:** genuine R13 full original-owner ZIP, 47 authored R13 pytest cases, syntax, crypto interoperability, Windows NTFS gate, physical installed P2 check, runtime wheel closure, #169 UAT, #170 pilot.
**NOT_CREATED:** signer keys, native verifier, signed ZIP; no R14-D4 source branch or executable.

## 9. External references and traceable source-of-truth

- Original personal charter: docs/architecture/VRES-PERSONAL-SINGLE-USER-PRODUCT-CHARTER-AND-METHOD-2026-10-30.md
- Full functional register: docs/roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md
- Original M0–M8 plan: docs/roadmap/VRES-PERSONAL-DAILY-OPERATIONS-DELIVERY-PLAN-2026-10-30.md
- Existing integrated W0/W1/W2/W3/W4/G1/P2/U1/U2 plan: docs/roadmap/VRES-PERSONAL-COMPLETE-PENDING-DEVELOPMENT-RELEASE-AND-REAL-WINDOWS-UAT-PLAN-2026-11-05.md
- High-assurance alternative: docs/architecture/VRES-W4-R14-D3-OUT-OF-BAND-TRUST-BOOTSTRAP-AND-EXACT-SOURCE-ENVELOPE-PROPOSAL-2026-11-06.md; R14-D2 independent review and original R14-D1.
- Official Python executable signing: https://www.python.org/downloads/
- Microsoft's published Windows security/product controls and limitations: https://learn.microsoft.com/en-us/windows/security/book/application-security-application-and-driver-control ; https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/design/script-enforcement

## 10. Exact next operation

**NEXT MILESTONE: W4 R14-D4 genuinely independent READ-ONLY security review of the proportionate PERSONAL release threat model and proposed trusted preflight.** This document is not that independent assessment. On review, distinguish DESIGN_REVISE, NARROW_DESIGN_ACCEPT, STATIC_REJECT; even positive scope approval would require separately named owner consent before any source implementation and later host/Windows gate. Publish resulting documentation-only verdict with exact-source GitHub continuity. No runtime, signing, Python, PowerShell, Windows host, database, hooks or installed profile in this phase.
