# Vres-OS

## Project identity
Vres-OS is a Python/PostgreSQL runtime and Claude Code plugin for governed task continuity, capability routing, project agents, evidence, and assurance.

Machine-wide engineering rules are owned by `rules/vres-rules.md` and installed through the Vres-managed import in `~/.claude/CLAUDE.md`. Keep this project file specific to the Vres-OS repository.

## Before changing code
- Read `README.md`, `constitution/CONSTITUTION.md`, and `docs/KNOWN-LIMITATIONS.md`.
- Follow the smallest evidence-backed change.
- Reuse an existing Vres/native-Claude primitive before creating a new abstraction.
- Apply the Vres Engineering Architecture Constitution: local change, predictable impact, explicit dependencies, shared truth, isolated failures.
- Released migrations are immutable; add a new migration.
- Live verification is a separate gate from CI.

## Build / Test / Lint
- Install dev runtime: `python -m pip install ".[full,dev]"`
- Affected test: `python -m pytest <test-file> -q`
- Full test suite: `python -m pytest`
- Release gate: `python scripts/release_gate.py --output <outside-checkout-directory>`
- Windows install/update: CURRENTLY HELD, including Git preflight. Do not run the original installer, native Claude/hooks or PostgreSQL contact. Future separately authorized usage requires the ORIGINAL `update.ps1`/`install.ps1`, approved exact COMMIT/TREE, independent Git.exe/Python.exe SHA-256 pins, externally approved complete offline wheelhouse/lock and original recovery. See `docs/INSTALL-WINDOWS.md` rather than obsolete one-argument examples.

## Repository boundaries
- Git owns code, tests, engineering docs, migrations, and this project contract.
- PostgreSQL owns operational state, provenance, routing/work-unit state, and semantic indexes.
- The OS credential store owns secrets.
- Native Claude executes agents; Vres governs routing, scope, evidence, dependencies, and assurance.
- Project agents belong in the target project's `.claude/agents/`, not in Vres global state by default.

## References
- Engineering Architecture Constitution: `docs/architecture/ENGINEERING-CONSTITUTION.md`
- Architecture profiles: `docs/architecture/ENGINEERING-PROFILES.md`
- Architecture boundaries: `docs/architecture/BOUNDARIES.md`
- AIGO heritage: `docs/architecture/AIGO_MERGE.md`
- Live verification: `docs/LIVE-VERIFICATION.md`
- Release evidence: `docs/RELEASE-VALIDATION.md`
