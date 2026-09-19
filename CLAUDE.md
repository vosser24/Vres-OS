# Vres-OS

## Project identity
Vres-OS is a Python/PostgreSQL runtime and Claude Code plugin for governed task continuity, capability routing, project agents, evidence, and assurance.

Machine-wide engineering rules are owned by `rules/vres-rules.md` and installed through the Vres-managed import in `~/.claude/CLAUDE.md`. Keep this project file specific to the Vres-OS repository.

## Before changing code
- Read `README.md`, `constitution/CONSTITUTION.md`, and `docs/KNOWN-LIMITATIONS.md`.
- Follow the smallest evidence-backed change.
- Reuse an existing Vres/native-Claude primitive before creating a new abstraction.
- Released migrations are immutable; add a new migration.
- Live verification is a separate gate from CI.

## Build / Test / Lint
- Install dev runtime: `python -m pip install ".[full,dev]"`
- Affected test: `python -m pytest <test-file> -q`
- Full test suite: `python -m pytest`
- Release gate: `python scripts/release_gate.py --output <outside-checkout-directory>`
- Windows install/update: `.\install.ps1` / `.\update.ps1`

## Repository boundaries
- Git owns code, tests, engineering docs, migrations, and this project contract.
- PostgreSQL owns operational state, provenance, routing/work-unit state, and semantic indexes.
- The OS credential store owns secrets.
- Native Claude executes agents; Vres governs routing, scope, evidence, dependencies, and assurance.
- Project agents belong in the target project's `.claude/agents/`, not in Vres global state by default.

## References
- Architecture boundaries: `docs/architecture/BOUNDARIES.md`
- AIGO heritage: `docs/architecture/AIGO_MERGE.md`
- Live verification: `docs/LIVE-VERIFICATION.md`
- Release evidence: `docs/RELEASE-VALIDATION.md`
