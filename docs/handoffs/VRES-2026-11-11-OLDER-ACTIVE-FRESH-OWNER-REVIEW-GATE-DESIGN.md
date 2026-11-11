# Vres-OS — 2026-11-11: Owner-reviewed older active-fresh records — DESIGN ONLY

**Status: PROPOSED, NOT IMPLEMENTED, NOT APPROVED FOR WINDOWS OR PROTECTED OPERATIONS.**
**Original owners:** #168 project adoption and canonical scaffold; #174 architecture governance.
**Product:** ONE personal Windows user, one Chairman and one original project-adoption state store.
**Restriction:** the historical fresh scaffold SHA is unknown if the old active state did not persist it. Today's SHA is not trustworthy evidence of yesterday's accepted bytes.

## Trigger, non-goals and refusal

An ORIGINAL #168 saved record with state active, no activation record, created exactly ["CLAUDE.md"], and no scaffold_sha256 is an older active-fresh record. Current start/status refuse it rather than guessing a digest or treating its label as activation authority. An ambiguous fresh/legacy mixture must also refuse. A real activated legacy record uses the original activation identifier, inventory version, removed/created lists and saved activation result/restore manifest; it is a different path. A reviewed legacy project does not become "fresh" simply because its root CLAUDE.md exists.

No automatic repair of the state JSON, no scaffold replacement, no deletion of external Claude files, no silent new store, no forced adoption, no import of DB-connected services, no Claude Code or hooks, no installer/P2/main/R13 change. A read-only observation is NOT owner approval or independent F1/Fable validation.

## Future, explicitly owner-reviewed transition plan

**Gate 0 — stop and preserve:** Surface a non-authorizing OLD_ACTIVE_FRESH_MISSING_DIGEST diagnostic in the ORIGINAL project-adoption/Chairman review path. Keep the saved active record and original project bytes unchanged. Show only redacted project identity and actions; never print secrets or sensitive project content.

**Gate 1 — independent read-only evidence:** With the owner selecting the exact project and agreeing to the proposed host access in a future independently cleared session, inspect canonical project-root binding, bounded state-file identity, journal/recovery presence, the exact ordinary root CLAUDE.md, current Claude configuration inventory and original #174 audit. Establish which evidence is historical vs current; do not infer original scaffold SHA from current bytes. If any path is a reparse point/link, unreadable, ambiguous, changed mid-review or has an interrupted journal, stop for manual recovery.

**Gate 2 — explicit informed choice:** Chairman presents a numbered, source-bound, redacted owner review with at least: (A) leave adoption BLOCKED, preserving all bytes; (B) start the ORIGINAL reviewed legacy KEEP/DROP and #174 alignment workflow if current source/configuration warrants it, with independently trusted Fable/high validation when required; (C) separately propose a carefully reviewed fresh-state reinitialization only when there is independent, trustworthy pre-image evidence, no contradictory project/configuration facts, a reversible plan, and new explicit approval. NEVER show "trust today's SHA as the old SHA" as a valid choice. Missing historical proof means choices B or A, not a fabricated C.

**Gate 3 — proposed implementation, not current authority:** Only after the owner explicitly authorizes a concrete transition and all held host/trust gates are independently cleared, persist an exact reviewed before-image and recovery journal using the ORIGINAL #168 store. Require root/key/version matching, serializable owner decision evidence, independent architectural approval where applicable, bounded path identities, last-moment inventory/architecture recheck, exclusive journal creation, recovery/rollback plan and no state overwrite on refusal. Revalidate the committed transition on readback. Fail closed on any race or unknown historical gap; never claim this is an atomic Windows filesystem transaction.

**Gate 4 — proof and acceptance:** Use synthetic fixtures for missing historical digest, forged activation/mixed keys, valid saved legacy activation, incomplete audit, inventory drift before/after authorization, links/special files, journal interruption, and bad recovery pre-images. Show source-only/NOT_RUN provenance until exact pinned safe imports and focused tests are possible. One final owner-selected nonsensitive Windows dummy-project Claude UAT is much later and requires NEW host consent, incident clearance and trusted F1/Fable authority. Do not use a real legacy project as a fixture now.

## Owner, risk and requirement trace

Keep original #168 fresh/legacy/adopted/interrupted lifecycle, numbered KEEP/DROP, original Credential Broker/Data Source Registry links and #174 protected alignment. Integrate proposed review into the existing Chairman conversational UX (the user should not need a new CLI or second control plane). Preserve original V-01..V-42 / M0..M8 / W0..W3 / W4 R1..R13. Avoid enterprise IAM, multitenancy and duplicate task, memory, project or data-source stores.

This proposal creates NO release permission and NO Windows command. Original LIVE_SCHEMA_048_INCIDENT, HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED, P3, independent F1/Fable and R13 staging holds all remain OPEN.
