# SQL ownership

Canonical executable migrations are `src/vres_os/migrations/*.sql` and are packaged inside the wheel.
This directory intentionally does not duplicate them. `scripts/migration-baseline.json` records the recovered
001–006 SHA-256 bytes. The migration runner also stores applied checksums and rejects drift/unknown newer migrations.
Static checks do not prove PostgreSQL syntax, privilege behavior, data backfill or locking; execute the live DB gate.
