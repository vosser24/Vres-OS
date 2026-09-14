# Tests and evidence

Run `python scripts/release_gate.py --output <outside-checkout-directory>` for the local gate.
Unit/boundary tests include real format parsers and subprocesses as well as scripted DB interactions. Scripted
SQL is not PostgreSQL execution. Windows text-contract tests are not PowerShell execution. The manifest records
these boundaries and actual skip reasons.

Real PostgreSQL tests are opt-in and require a dedicated database whose name ends in `_test`:

```powershell
$env:VRES_TEST_DATABASE_URL = '<dedicated test DSN obtained locally; never paste into chat>'
$env:VRES_ALLOW_TEST_DB = '1'
python -m pytest tests\integration -ra
Remove-Item Env:VRES_TEST_DATABASE_URL
Remove-Item Env:VRES_ALLOW_TEST_DB
```

Prefer supplying the DSN through a local secure prompt instead of terminal history; see LIVE-VERIFICATION.md.
The tests create uniquely scoped projects and delete only their own records, never the schema/database.
They still apply migrations to the nominated test DB; the suffix/acknowledgment gate is not permission to use production.

`fixtures/live` contains two synthetic Excel pairs and expected JSON. They intentionally contain duplicate
SKUs, leading zeroes, a negative return, a decoy second worksheet and unit counts whose ranking differs from
Net Sales. Day two changes values so stale output replay cannot masquerade as procedure reuse.
