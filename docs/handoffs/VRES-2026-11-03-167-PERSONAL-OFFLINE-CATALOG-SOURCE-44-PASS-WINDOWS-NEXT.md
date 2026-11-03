# Vres-OS — 2026-11-03 PERSONAL #167 offline data-source/catalog foundation, safe parallel to pending M2

**Evidence class:** GitHub source and tests committed on ONE independent feature branch; **44 selected tests PASS in an isolated Linux development container on exact source/test Git blobs**, exit0, no native Windows execution. New #167 Windows test **NOT_RUN**. No PostgreSQL, user profile, native Claude hooks, real credentials, installed Vres or real legacy project were contacted by this work.

**Repo:** https://github.com/vosser24/Vres-OS
**Canonical documentation branch:** docs/chatgpt-continuity-20261023. Previous verified GitHub docs HEAD at source build start: **b2f79db82a6614941567ba7e4635a64b404d6a3c**, tree **815badd26a9639ace58c76c837056e081841e3f8**. Always verify actual newest docs READ FIRST before the next step.

## 1. Product/scope and safety invariants (NOT waived)

Vres-OS is a practical PERSONAL application for ONE Windows user's daily operations, not enterprise IAM/multi-tenant governance. Keep one Chairman and existing governed workers, actual useful project/task continuity, current-user credentials, reversible install, fresh/legacy project understanding and relevant experience; original V-01..V-42 functionality remains in full.

**LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL contact, EVEN SELECT**, direct/indirect via Vres CLI, MCP, bootstrap, doctor, hooks, migrations, F2, restore or any client. **HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN:** seven historic native Claude Code Read/Grep posttool automatic routes refused. NO ordinary native Claude startup or installed hook/plugin execution. Stage1–6 original P2 hook provenance and three matcher-only differences stand; no Stage7 repeat or hot patch.

Independently trusted F1 positive issuer/protected Fable-high still NOT granted. No actual installed P2 upgrade, global Claude/PRISM changes, Credential Locker retrieval, real legacy project, model activation, main PR/merge or go-live without a separate exact P2 approval and pertinent incident clearance. This source feature intentionally neither opens a database nor claims to clear either incident.

## 2. Version lineage and independence from pending release

- **Product main:** 9a8acc5d464b96432a93cb95daa9581412fb07ee, unchanged.
- **Original P2 last observed locally installed source:** 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c / tree 205c081277ece483c634e1c801c39595abd4549c; current local Windows installation was NOT freshly inspected.
- **A18 source accepted:** 7bace7758e5c7f9a00f26179eb741ef3a319bc77, guarded historical 49 Windows PASS, NOT installed.
- **M1 accepted offline:** 28120eb49b6b950c7402455db19dcbdcf6d991a6 / tree 815fce697f16509bae150729891738d879d6ca9c; 110 selected Windows PASS, synthetic P2 rollback, preflight output omission preserved.
- **M2-HOST accepted source:** 526fb9d61e4a61c26c19931f9adf2d68eecd1bc8 / tree 9919f363a8608e31e4c5a6f66adb765c7021b484; 63 Windows selected PASS with explicit excerpt limitations.
- **Separate pending M2 rollback proof candidate:** a65215a3b8b91ad4ab374c928ae3cf667e5b0f95 / tree 942a4a4d29bdae64314de6490e4e8f99674dbf3e, parent accepted M2-HOST. New Windows **NOT_RUN**; its original SHA-pinned Windows script was already archived at docs/handoffs/VRES-PERSONAL-M2-INTEGRATED-ROLLBACK-GUARDED-WINDOWS-2026-10-30.ps1, Git blob b19642db12837f0e5866de463ecd23bfb83af848. **Do not merge or overwrite this branch** with #167 while pending.
- **NEW parallel #167 feature:** branch feature/167-personal-offline-source-catalog-20261103, **HEAD 16f8df95a001527bdd1ed94dfd3a963016109384**, **tree 54cc836906b1f63e074e0aebf2e24cb5e7b875fd**, direct sole **accepted M2-HOST parent 526fb9d61e4a61c26c19931f9adf2d68eecd1bc8**. It deliberately excludes pending unaccepted M2 rollback-protection code. No main merge/PR or installed change.

**Exact GitHub commit:** https://github.com/vosser24/Vres-OS/commit/16f8df95a001527bdd1ed94dfd3a963016109384

GitHub remote readback verified HEAD, tree, direct parent, and exact **TWO ADDED paths**, no modified release/installed/DB/credential/hook files:
1. **A src/vres_os/personal_data_sources.py**, Git blob **ad08616bf89d34c0c5f52affff30813562d7a2f7**, 313 source lines, SHA256 0ba00a08d17b645c3f4c5c7ca385d34686955f4f32d51979297c3ffe0eb798f4.
2. **A tests/test_personal_data_sources.py**, Git blob **f669097b93618ba2213f5d2db3e6f8d3d4ca380b**, 289 Git lines, SHA256 20c2a6ee5fcc4fa5e0df5cb848ae1052d2ba59d1b185ed1e2cb5cf93dfb28556.

## 3. What the new PERSONAL #167 code actually builds (not what remains)

**One pure offline metadata owner** that receives the current-user namespace from the established Credential Broker, a **nonsecret CredentialBroker.lookup-like metadata callback**, and optional caller-provided document bytes. It never reads Credential Locker, connects to DB, runs SQL, performs network I/O or writes user files. It does NOT create another credential vault, another Vres task store, enterprise IAM or a master agent.

- Register only a canonical PostgreSQL **nonsecret identity** of the form host:port/database + existing credential resource handle, requiring explicit user-authorization signal; metadata callback must prove credential resource ID/service_type/postgres origin alignment. Malformed or secret-bearing DSNs/URLs refused. No automatically approved database connection or source permissions.
- Stable source ID bound to current-user namespace, canonical origin and credential resource handle, with bounded canonical JSON representation. One user namespace cannot reload another user's catalog; JSON duplicate keys, malformed sources, snapshots, links, NaN and oversized data refuse. The document is still *same-user mutable metadata*, not a signed authority receipt.
- Explicit project A / B binding to a source requires authorization independently for each project. Project C remains denied without its own binding even if it guesses source ID. Unlink A does not remove B. Methods operate in memory and return document bytes for a future approved storage adapter; this code doesn't create a real user-profile registry.
- Strict bounded structural schema: schema/table/view identifiers, columns/type/nullability, primary/foreign key relationships. Reconstructed metadata accepts no comments, arbitrary SQL, sample values, original credentials or freeform prompt bodies. Refs must point to objects/columns included in the bounded schema; fake/inapplicable targets refuse.
- Deterministic canonical structure SHA256 supports cheap same-catalog reuse and **DRIFT_REVIEW_REQUIRED** for a changed proposed metadata snapshot; stale expected fingerprint refuses. Snapshot changes require both explicit reviewed and authorized signals and have fail-closed in-memory mutation semantics. Catalog is always labeled **caller_supplied_unverified** — neither connector-observed, cryptographically trusted, database-verified nor allowed to trigger a query.
- Callers cannot mutate returned metadata by changing a returned object; defensive deep copy. Data-source and binding quotas prevent unbounded personal local context growth.

This **does not** yet implement a complete #167 durable local registry/Windows ACL adapter, real current-user vault-backed binding via running Vres, live schema acquisition, read-only PostgreSQL introspection, semantic data-source learning, native task/Chairman UX, production DB health or full issue closure. All remain pending. It is the concrete offline/source foundation, not a claim of actual daily-installed capability.

## 4. Actual executed development-container evidence (not Windows)

Before publication, an isolated Python 3.12-compatible pure Python module and pytest test file were constructed in the independent development container. A final replay after synchronizing the final exact source bytes into the import location ran:

PYTHONPATH=/mnt/data/vres_m5_offline PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -B -m pytest -q -ra -p no:cacheprovider /mnt/data/vres_m5_offline/tests/test_personal_data_sources.py

**Observed result:** **44 PASSED, 0 visible FAILED, exit 0** in 0.11s. Tests cover A/B authorized binding, unbound C refusal, credential-resource metadata mismatch/unknown handle, malicious DSN rejection before lookup, canonical JSON byte roundtrip, user-namespace separation, bounded table/column/FK metadata validation, illegal SQL/comment/row-value rejection, canonical fingerprint under reordered structures, changed fingerprint review/stale refusal, anti-forgery label, immutable returned records and no DB/file/network import surface.

**Exact provenance:** development-container local Git hash-object returned **ad08616bf89d34c0c5f52affff30813562d7a2f7** for the final tested module and **f669097b93618ba2213f5d2db3e6f8d3d4ca380b** for the test file; GitHub create_blob returned those exact IDs, then GitHub remote file readback verified them. The developer initially ran the tests against a pre-final import copy, then copied the FINAL module into the import path and reran 44 PASS against the exact blob: **the latter** is the acceptance evidence. No Python package install, PostgreSQL, native Claude or Windows runtime executed.

**Limit:** Linux-container pytest is not Windows/installed behavioral proof, not a physical all-system no-network attestation, not test of actual Credential Broker or immutable authorization. Tests use only synthetic metadata values, fake Credential Broker metadata callback and in-memory objects. No user/private data or credentials are in the tests.

## 5. One planned Windows acceptance gate, without another ceremony treadmill

**Self-contained Windows PowerShell 5.1 script archived:** docs/handoffs/VRES-167-PERSONAL-OFFLINE-SOURCE-CATALOG-WINDOWS-GATE-2026-11-03.ps1, Git blob **f47b20690f62fc34421a80eef72fd3c49437ea00**. Provide entire source as one inline code block if the operator is ready. It is a P1 new detached worktree and selected offline tests ONLY, not an installer.

The script uses original protected P2 anchor C:\Projects\Vres-P2F-Postinstall-Hardening-20261022; validates official GitHub origin, protected P2 exact/clean, fetched #167 commit, standalone fresh detached checkout C:\Projects\Vres-ChatGPT-Review-167-Offline-Catalog-20261103 (refuses existing), exact HEAD/tree/sole accepted M2-HOST parent and source diff **ADD two paths only**, pre/post **9 pinned Git blobs**, own isolated process DB/PG/Python/Vres env scrub and original-value restore, plugin autoload disabled, single **py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_personal_data_sources.py**. Final success marker expected only if execution really completes: **VRES_PERSONAL_167_OFFLINE_CATALOG_WINDOWS_SELECTED_TEST_COMPLETE_PENDING_EVALUATION** with PYTEST_EXIT_CODE=0.

**Next user Windows priority remains M2 rollback proof first** (previously given full inline PowerShell), then #167 pure catalog if suitable. Do NOT run actual installer, Vres CLI/doctor/hooks, PostgreSQL/Claude or real credentials under open incidents. No repeat of accepted M1 110 or M2 first 63 for paperwork. Record every actual Windows PASS/FAIL with precise SHA and avoid treating this Linux 44 PASS as Windows PASS.

## 6. Remaining roadmap / next operation

- **M2 rollback candidate** await one existing Windows offline test and independent evidence evaluation; then determine separate host-hook incident closure/approved versioned install. Schema-048 incident remains independent, database no-contact.
- **M3:** low-ceremony Chairman, task/session persistence, relevant experience reuse (#165/#176), governed specialists and honest model observation. Source-only offline work can continue on independent accepted parent; native host activation held.
- **M4:** #166 current-user Claude/PRISM adoption and #168 fresh/legacy project architecture audit, reversible user KEEP/DROP and constrained Fable approval. No real host or real project without P2.
- **M5:** complete #167 durable same-user metadata store, safe real Credential Broker adapter, project key lifecycle, offline semantic catalog and drift, later read-only acquisition ONLY after M2-DB independently cleared and explicitly approved safe target. Current source is initial reusable offline foundation.
- **M6:** full Visual Studio #169 real-project integration only after separately accepted prereqs and consent.
- **M7:** personal actual task/day pilot and #170 readiness, source and installed coherent, rollback and secure outcomes; not yet production.
- **M8:** keep advanced V-01..V-42 capabilities alive as optional after baseline, no enterprise ceremony. Prior closed #163/#164/#174 are source status, not all actual installed functionality proven.

**Historical failures retained:** original rejected A12 345a568b551ac23183c54f10611335adee903b96 18PASS/1FAIL exit1; original rejected A13 cdaa39aaa774cef88a4831bf6b157e380fbb69d9 28PASS/1FAIL exit1; corrected R1 separate; A16 original env restoration script-copy ambiguity, A19 blocked/uncommitted. Protect all original Windows worktrees and PT1/PT2A–D, Hook-R1, Stage1–6, E7/E8/C2B/R0/F2 records; never convert historical FAIL into PASS.

**Hard 20-assistant-reply or conservative >50%-context checkpoint:** active turns only. At trigger, stop, verify exact docs/product/feature SHAs/parents, commit all authorized completed source/tests/docs by nonforce expected-SHA update, archive dated full continuity+index newest READ FIRST, give ONE full copyable inline next-chat resume prompt, recommend new session. Precise context meter and local Windows unpushed state are unavailable here; do not invent.
