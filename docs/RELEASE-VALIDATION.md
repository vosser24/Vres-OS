# Release validation: what the evidence means

## Reproduce the local gate

From the repository root, using Python 3.12 or 3.13:

```powershell
python -m pip install ".[full,dev]"
python scripts\release_gate.py --output C:\VresEvidence\static
```

The gate writes actual logs, JUnit, coverage JSON, a file ledger and wheel-content checks to the nominated
output directory. Use a directory outside the checkout. A nonzero exit is a failed gate, not a warning to
ignore. Dependency installation needs network access unless an independently prepared package mirror exists.

This gate executes local tests and Python compilation; parses JSON/frontmatter; checks package and migration
manifests; builds an actual wheel without dependency resolution; compares packaged Python/SQL bytes to source;
smoke-imports selected installed modules in a separate directory; checks local documentation links; and runs
`git diff --check` when a Git checkout is available.

It does NOT execute PowerShell, PostgreSQL or a live model. Structural migration checks are not a SQL parser
or a guarantee that PostgreSQL accepts the schema. Any integration skips are reported, never counted as passes.
Tests using scripted DB connections prove submitted SQL/parameters and application branching, not DB semantics.

## Release artifact protocol

1. Finish source changes and run the gate successfully.
2. Commit the source, tests and docs. Never label uncommitted files a release commit.
3. Re-run the gate on that clean commit and capture its full SHA/tree ID.
4. Export source with `git archive`, and full history with `git bundle create ... --all`.
5. Restore the bundle into a separate checkout, run `git fsck`, and run the tests there.
6. Compare every source ZIP member byte-for-byte with the committed Git blob.
7. Inspect the wheel, including every migration. A wheel alone is not the Windows distribution: it excludes
   the top-level installer/plugin/docs by design.
8. Produce a manifest with artifact SHA-256 hashes, commit/tree IDs, environment inventory and exact results.
9. Include gate logs and a per-file evidence ledger. Preserve unavailable dependencies as NOT RUN.

Do not place a wheel inside the source commit and then imply the commit produced itself. Generated release
artifacts belong beside the source export; record their hashes in a separate release manifest.

## Labels

- **Local gate passed:** the exact local commands in the evidence log passed in the recorded environment.
- **Controlled-live-test preview:** a packaged checkpoint with known held capabilities, ready to be evaluated
  on a disposable target; it is not yet proved usable by a novice.
- **Windows acceptance passed:** the exact live matrix was executed and reviewed against the exact artifact.
- **Production ready:** requires a separate operational/security/recovery acceptance; this audit does not claim it.

## Historical recovery

The recoverable ZIP reproduced 41 tests with two PostgreSQL test modules skipped. Larger historical chat
counts and claims of ten migrations were not present in that source. This audit preserves the recovered
001–006 migration bytes and adds 007–009. Only the current generated evidence manifest determines the current
count; do not copy an old number into a README as if it were a fresh test result.

## Validator independence

The local code review in this delivery was performed by this assistant and deterministic tools. A separate
live Claude/Codex validator was not invoked here. Product-side validator hooks are code under test, not proof
that an independent model reviewed this build. The strongest protected validation role must be observed in
LIVE-VERIFICATION.md before trusting its application-level completion decisions.
