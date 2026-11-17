# W4 original-owner OFFLINE Personal Day source packet — source-only integration contract

**Date:** 2026-11-17. **Candidate branch:** \`feature/personal-w4-original-day-offline-source-bundle-20261117\`. **Base:** exact original-owner source \`179dbfc81a076f2aa1600e3392f538885c8178b3\` / TREE \`219fb4a7147a029a36a7db89f98497dd39dd59af\`. **Authority:** owner approved code authoring only; Windows, database, native host and production release operations remain held.

## What this actually integrates
New \`src/vres_os/personal_w4_source_packet.py\` forms an in-memory deterministic ZIP and SHA-256 receipt from exactly 20 pinned original Personal Day startup/owner source files. Nothing is read, written, executed, extracted, staged, downloaded or installed by the packet builder. The corresponding \`tests/test_personal_w4_source_packet.py\` exercises exact source pins, deterministic bytes, archive names, metadata, refusal on modified/missing/extra files, and held embedded bootstrap behavior — **AUTHORED, NOT_RUN**. The original Desktop, CLI, daily plan, task/session/result/history files and P1 delivery remain unmodified.

This is a **small, deliberately held, OFFLINE PERSONAL DAY slice**, NOT the promised first-FULL Vres-OS (V-01..V-42). The ZIP contains only original code files, \`__main__.py\` and the manifest; it does not include database code, original full-release installer, migrations, third-party wheels, credential modules or other global Claude/host integrations. User-requested real PostgreSQL, Chairman, memory, credentials, project adoption and learning remain REQUIRED by the original roadmap and OPEN/HELD under relevant issues.

## Exact safety and trust boundaries
- All original-source Git blobs are matched bytewise against the observed immutable base commit; each is additionally recorded by SHA-256. These are integrity values **not publisher authentication**. A separate operator-held release identity and independently approved pre-execution verifier are still REQUIRED.
- The ZIP is built only in memory; no archive or root is created. Fixed entries, ZIP_STORED and timestamp/mode settings support reproducibility. Confirm cross-runtime ZIP determinism only after permitted real tests.
- Embedded \`__main__.py\` has a preview flag **HELD by default**, environment guard against Vres data/DB overrides, and accident-only Python audit/import tripwires against known host, DB, native effects. It would import the existing original Desktop if intentionally enabled. These tripwires are **not** a kernel sandbox or trust root, and setting the preview flag does not grant execution approval.
- The current 20-file list is **observed startup/owner material**, not a proven complete static/runtime import closure; optional routes may require excluded modules and must fail closed. Exact Tk/Tcl/Python \`-I -S -B\` zipimport behavior, native Python module/stdlib closure, Windows path/ACL/reparse/ADS/hardlink/case alias protections, official interpreter identity, and all launch/test effects remain **NOT_RUN**.
- DO NOT use original \`personal_portable_delivery.py\` (historical pins/128KiB cap), \`release_artifact.stage()\`, direct-file R13 bootstrap, \`install.ps1\`, \`uninstall.ps1\`, native Claude/hooks, PostgreSQL (even SELECT), or any Windows/P2/profile/credential/legacy/PRISM operation for this source packet.

## Next integrated engineering and operations gates
1. Independently review the source diff and reconcile the separate Claude \`THREAT_MODEL=REVISE\` / \`RELEASE_DESIGN=DESIGN_REVISE\` feedback and issue #185 full text. Reviewer cannot be the original source author.
2. Complete externally reviewed pre-execution source/runtime verification, Windows launcher and opt-in capability matrix; do not claim a wheel-free first-FULL release. Prepare a full original-owner feature/capability closure without invoking held DB/host routes.
3. Before any source tests or compilation, independently verify the whole exact source and a disposable kernel-enforced no-network/no-child route. If not proven, tests remain NOT_RUN. Windows GUI/packaging and user-profile/install operations require separately authorized procedures, physically verified ACLs and backups.
4. Only after incident resolution and fresh informed permission move to real local Claude/PostgreSQL/Windows integrated UAT on the owner's computer. Protected P2, main and R13 remain unchanged until their own gates.

Original V-01..V-42, M0..M8, W0..W3, W4 R1..R13, C2B/K0 and October 22/30/31 + November 5 plans are preserved. No automated rollback.
