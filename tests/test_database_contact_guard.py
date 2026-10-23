"""P2-A1 personal-release database contact guard and migration-before-mutation sequencing.

Every test here is offline. PostgreSQL connections and credential reads are replaced
with tripwires that fail the test if reached; scripted connections stand in for the
server wherever a test needs one to answer catalog queries.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
from contextlib import contextmanager, nullcontext
from importlib import resources
from pathlib import Path
from types import SimpleNamespace

import psycopg
import pytest

from vres_os import bootstrap, database_boundary, database_targets, db
from vres_os.config import ConfigStore, VresConfig
from vres_os.database_boundary import BoundaryCredentials
from vres_os.db import DatabaseTargetRefused, MigrationDrift

# Captured at import, before conftest forces the guard on for each unit test.
_REAL_GUARDED_PLATFORM = database_targets._guarded_platform
_MUTATION = re.compile(r"\b(CREATE|ALTER|DROP|INSERT|UPDATE|DELETE|GRANT|REVOKE|TRUNCATE)\b|pg_advisory_lock")
_SECRET = "SuperSecret-Example-Value"
_DSN_ENV = (
    "VRES_DATABASE_URL",
    "VRES_TEST_DATABASE_URL",
    "VRES_ALLOW_TEST_DB",
    "VRES_MIGRATION_DATABASE_URL",
    "VRES_PROVENANCE_WRITER_DATABASE_URL",
)


class _Tripwires:
    def __init__(self):
        self.connections: list[str] = []
        self.secret_reads: list[str] = []


@pytest.fixture(autouse=True)
def tripwires(monkeypatch, tmp_path):
    """No real PostgreSQL connection, credential read, user config or DSN environment."""
    wires = _Tripwires()

    def no_connection(*_args, **_kwargs):
        wires.connections.append("psycopg")
        raise AssertionError("A PostgreSQL connection was attempted")

    class NoSecrets:
        def get(self, key):
            wires.secret_reads.append(key)
            raise AssertionError("A credential was read")

    monkeypatch.setattr(psycopg, "connect", no_connection)
    monkeypatch.setattr(psycopg.Connection, "connect", no_connection)
    refusing_driver = SimpleNamespace(connect=no_connection)
    for module in (db, bootstrap, database_boundary):
        monkeypatch.setattr(module, "_driver", lambda: refusing_driver)
    monkeypatch.setattr(db, "SecretStore", NoSecrets)
    monkeypatch.setattr(
        "vres_os.secrets._secure_keyring", lambda: (_ for _ in ()).throw(AssertionError("keyring used"))
    )
    for name in (*_DSN_ENV, *database_targets.ROUTING_ENVIRONMENT):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("VRES_DATA_DIR", str(tmp_path / "data"))
    yield wires
    assert wires.connections == [], "PostgreSQL was contacted"


@pytest.fixture
def personal_root():
    """The real registry root decision, over the private LocalAppData that conftest provides."""
    root = database_targets.personal_release_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _registry(root: Path, *, approved=(), held=()) -> None:
    approved = [
        {"host": h, "port": p, "dbname": d, "approved_at": "2026-10-19T00:00:00+00:00", "approved_by": "test"}
        for h, p, d in approved
    ]
    held = [
        {"host": h, "port": p, "dbname": None, "reason": "schema-048 incident", "held_at": "2026-10-19T00:00:00+00:00"}
        for h, p in held
    ]
    (root / database_targets.REGISTRY_NAME).write_text(
        json.dumps({"version": 1, "approved": approved, "held": held}), encoding="utf-8"
    )


def _configure(*, host="localhost", port=5432, database="vres_personal", boundary=True) -> VresConfig:
    cfg = VresConfig(configured=True)
    cfg.database.host, cfg.database.port, cfg.database.database = host, port, database
    cfg.database.user = "vres_runtime"
    if boundary:
        cfg.database.provenance_writer_user = "vres_writer"
        cfg.database.migration_user = "vres_migrator"
        cfg.database.provenance_boundary_version = 1
    ConfigStore().save(cfg)
    return cfg


# A. Held targets


@pytest.mark.parametrize("purpose", ["runtime", "writer", "migrator"])
def test_held_target_is_refused_before_connection_or_credential_read(personal_root, tripwires, purpose):
    _configure(database="vres_os")
    _registry(personal_root, approved=[("localhost", 5432, "vres_os")], held=[("localhost", 5432)])

    with pytest.raises(DatabaseTargetRefused, match="held for this installation"):
        db.build_dsn(purpose)
    with pytest.raises(DatabaseTargetRefused, match="held"):
        with db.connect(purpose=purpose):
            pass  # pragma: no cover

    assert tripwires.secret_reads == []


@pytest.mark.parametrize(
    "host",
    [
        "localhost", "localhost.", "127.0.0.1", "127.0.0.1.", "127.0.0.2",
        "127.254.7.9", "::1", "0:0:0:0:0:0:0:1", "::ffff:127.0.0.2", "LOCALHOST",
    ],
)
@pytest.mark.parametrize("purpose", ["runtime", "writer", "migrator"])
def test_held_server_covers_every_database_and_loopback_spelling(personal_root, host, purpose):
    _configure(host=host, database="a_new_personal_db")
    _registry(personal_root, approved=[(host.lower(), 5432, "a_new_personal_db")], held=[("localhost", 5432)])

    with pytest.raises(DatabaseTargetRefused, match="held"):
        db.build_dsn(purpose)


def test_held_target_cannot_be_approved_even_interactively(personal_root, monkeypatch):
    _registry(personal_root, held=[("localhost", 5432)])
    monkeypatch.setattr(database_targets, "_interactive", lambda: True)
    asked = []

    with pytest.raises(DatabaseTargetRefused, match="cannot be approved"):
        database_targets.confirm_target_for_setup(
            "localhost", 5432, "vres_os", ask=lambda prompt: asked.append(prompt) or "vres_os"
        )

    assert asked == []
    assert json.loads((personal_root / database_targets.REGISTRY_NAME).read_text())["approved"] == []


@pytest.mark.parametrize("host", ["127.0.0.2", "127.254.7.9", "::ffff:127.0.0.2", "localhost."])
def test_held_loopback_alias_refuses_admin_contact_and_setup_approval(personal_root, monkeypatch, host):
    _registry(personal_root, held=[("localhost", 5432)])
    with pytest.raises(DatabaseTargetRefused, match="held"):
        database_targets.require_admin_contact(
            f"host={host} port=5432 dbname=postgres", "vres_personal"
        )
    monkeypatch.setattr(database_targets, "_interactive", lambda: True)
    with pytest.raises(DatabaseTargetRefused, match="cannot be approved"):
        database_targets.confirm_target_for_setup(
            host, 5432, "vres_personal", ask=lambda _prompt: pytest.fail("approval prompt reached")
        )
    assert json.loads((personal_root / database_targets.REGISTRY_NAME).read_text())["approved"] == []


@pytest.mark.parametrize("host", ["127.0.0.2", "localhost.", "::ffff:127.0.0.2"])
def test_loopback_hold_matching_never_expands_exact_approval(personal_root, tripwires, host):
    _configure(host=host)
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        db.build_dsn("runtime")
    assert tripwires.secret_reads == []


@pytest.mark.parametrize("host", ["128.0.0.1", "192.0.2.5", "::ffff:192.0.2.5", "localhost.invalid"])
def test_loopback_hold_does_not_match_unrelated_literal_or_dns_name(personal_root, host):
    _registry(personal_root, approved=[(host, 5432, "vres_personal")], held=[("localhost", 5432)])
    # Permission check only. Do not resolve the hostname, read a credential or contact a server.
    database_targets.require_contact(f"host={host} port=5432 dbname=vres_personal")


# B2. Windows/libpq numeric aliases must not become independent approvals.

@pytest.mark.parametrize(
    "host",
    [
        "127.1", "127.0.1", "2130706433", "0x7f000001", "0x7f.0.0.1",
        "0177.0.0.1", "127.000.000.001", "127..1", "[::1]",
        "::1%1", "::ffff:127.1", "0.0.0.0", "::", "::ffff:0.0.0.0",
        "/tmp", r"C:\\temp", "localhost..",
    ],
)
@pytest.mark.parametrize("purpose", ["runtime", "writer", "migrator"])
def test_ambiguous_windows_host_cannot_use_even_an_existing_exact_approval(
    personal_root, tripwires, host, purpose,
):
    _configure(host=host)
    _registry(personal_root, approved=[(host, 5432, "vres_personal")], held=[("localhost", 5432)])
    with pytest.raises(DatabaseTargetRefused, match="ambiguous|unspecified"):
        db.build_dsn(purpose)
    assert tripwires.secret_reads == []


@pytest.mark.parametrize(
    "host", ["127.1", "2130706433", "0x7f000001", "0177.0.0.1", "127.000.000.001", "[::1]", "::1%1", "0.0.0.0", "::"],
)
def test_ambiguous_windows_host_refused_before_admin_or_setup_prompt(
    personal_root, monkeypatch, host,
):
    _registry(personal_root, held=[("localhost", 5432)])
    with pytest.raises(DatabaseTargetRefused, match="ambiguous|unspecified"):
        database_targets.require_admin_contact(
            f"host={host} port=5432 dbname=postgres", "vres_personal"
        )
    monkeypatch.setattr(database_targets, "_interactive", lambda: True)
    with pytest.raises(DatabaseTargetRefused, match="ambiguous|unspecified"):
        database_targets.confirm_target_for_setup(
            host, 5432, "vres_personal",
            ask=lambda _prompt: pytest.fail("unsafe host reached an approval prompt"),
        )
    assert json.loads((personal_root / database_targets.REGISTRY_NAME).read_text())["approved"] == []


@pytest.mark.parametrize(
    "dsn",
    [
        "host=127.1 port=5432 dbname=vres_personal",
        "host=0x7f000001 port=5432 dbname=vres_personal",
        "host=[::1] port=5432 dbname=vres_personal",
        "postgresql://127.1:5432/vres_personal",
        "postgresql://%5B%3A%3A1%5D:5432/vres_personal",
        "postgresql://0x7f000001:5432/vres_personal",
    ],
)
def test_ambiguous_host_is_refused_from_environment_and_uri_routes(personal_root, monkeypatch, tripwires, dsn):
    _registry(personal_root, held=[("localhost", 5432)])
    monkeypatch.setenv("VRES_DATABASE_URL", dsn)
    with pytest.raises(DatabaseTargetRefused) as exc:
        db.build_dsn("runtime")
    assert "No connection was attempted." in str(exc.value)
    assert tripwires.secret_reads == []


def test_standard_ipv6_uri_to_held_server_is_refused(personal_root, tripwires):
    _registry(personal_root, held=[("localhost", 5432)])
    with pytest.raises(DatabaseTargetRefused):
        database_targets.require_contact("postgresql://[::1]:5432/vres_personal")
    assert tripwires.secret_reads == []


@pytest.mark.parametrize("held_alias", ["127.0.0.2", "::ffff:127.0.0.2", "::1"])
def test_reverse_loopback_alias_hold_refuses_localhost(personal_root, held_alias):
    _configure(host="localhost")
    _registry(
        personal_root,
        approved=[("localhost", 5432, "vres_personal")],
        held=[(held_alias, 5432)],
    )
    with pytest.raises(DatabaseTargetRefused, match="held"):
        db.build_dsn("runtime")


def test_hold_target_deduplicates_aliased_loopback_server(personal_root):
    _registry(personal_root, held=[("127.0.0.2", 5432)])
    database_targets.hold_target("localhost", 5432, reason="second hold")
    registry = json.loads((personal_root / database_targets.REGISTRY_NAME).read_text())
    assert len(registry["held"]) == 1
    assert registry["held"][0]["host"] == "127.0.0.2"


@pytest.mark.parametrize("host", ["192.0.2.5", "2001:db8::1", "localhost.invalid"])
def test_unrelated_canonical_host_remains_exactly_approvable(personal_root, host):
    _registry(
        personal_root,
        approved=[(host, 5432, "vres_personal")],
        held=[("localhost", 5432)],
    )
    database_targets.require_contact(
        f"host={host} port=5432 dbname=vres_personal"
    )


# B3. Abstract socket hosts and IPv4-translation aliases never become approved.

@pytest.mark.parametrize("host", ["@vres", "@/tmp/vres", "bad_host", "space name", "bad@host", "δοκιμή"])
@pytest.mark.parametrize("purpose", ["runtime", "writer", "migrator"])
def test_abstract_socket_and_invalid_hostname_refused_before_credential_or_contact(
    personal_root, tripwires, host, purpose,
):
    _configure(host=host)
    _registry(personal_root, approved=[(host, 5432, "vres_personal")], held=[("localhost", 5432)])
    with pytest.raises(DatabaseTargetRefused, match="ambiguous or unsafe"):
        db.build_dsn(purpose)
    assert tripwires.secret_reads == []


@pytest.mark.parametrize("host", ["@vres", "@/tmp/vres", "bad_host"])
def test_abstract_socket_host_refused_before_admin_and_setup_approval(personal_root, monkeypatch, host):
    _registry(personal_root, held=[("localhost", 5432)])
    with pytest.raises(DatabaseTargetRefused, match="ambiguous or unsafe"):
        database_targets.require_admin_contact(
            f"host={host} port=5432 dbname=postgres", "vres_personal"
        )
    monkeypatch.setattr(database_targets, "_interactive", lambda: True)
    with pytest.raises(DatabaseTargetRefused, match="ambiguous or unsafe"):
        database_targets.confirm_target_for_setup(
            host, 5432, "vres_personal",
            ask=lambda _prompt: pytest.fail("unsafe socket host reached approval prompt"),
        )
    assert json.loads((personal_root / database_targets.REGISTRY_NAME).read_text())["approved"] == []


@pytest.mark.parametrize("dsn", [
    "host=@vres port=5432 dbname=vres_personal",
    "postgresql://%40vres:5432/vres_personal",
    "postgresql:///vres_personal?host=%40vres&port=5432",
])
def test_abstract_socket_env_connection_strings_fail_closed(personal_root, monkeypatch, tripwires, dsn):
    _registry(personal_root, held=[("localhost", 5432)])
    monkeypatch.setenv("VRES_DATABASE_URL", dsn)
    with pytest.raises(DatabaseTargetRefused):
        db.build_dsn("runtime")
    assert tripwires.secret_reads == []


@pytest.mark.parametrize("host", [
    "::7f00:1", "::127.0.0.1", "::ffff:0:127.0.0.1",
    "64:ff9b::7f00:1", "2002:7f00:100::",
])
def test_ipv6_embedded_loopback_translation_is_not_independently_approvable(
    personal_root, tripwires, host,
):
    _configure(host=host)
    _registry(personal_root, approved=[(host, 5432, "vres_personal")], held=[("localhost", 5432)])
    with pytest.raises(DatabaseTargetRefused, match="ambiguous or unsafe"):
        db.build_dsn("runtime")
    assert tripwires.secret_reads == []


@pytest.mark.parametrize("host", ["2001:db8::1", "::ffff:192.0.2.5", "db-01.example.internal"])
def test_normal_ipv6_mapped_remote_and_dns_names_preserve_exact_approvals(personal_root, host):
    _registry(personal_root, approved=[(host, 5432, "vres_personal")], held=[("localhost", 5432)])
    database_targets.require_contact(f"host={host} port=5432 dbname=vres_personal")


# B4. Historical unsafe holds cannot break the add-only incident mechanism.

@pytest.mark.parametrize("legacy_host", ["127.1", "@vres", "0x7f000001"])
def test_legacy_unclassifiable_hold_refuses_contact_but_allows_new_holds(
    personal_root, legacy_host, capsys, tripwires,
):
    _configure(host="db.example.internal")
    _registry(
        personal_root,
        approved=[("db.example.internal", 5432, "vres_personal")],
        held=[(legacy_host, 5432)],
    )
    # An unknown historical host may actually be an alias of this server.
    # Fail closed for ALL contacts on this port, but preserve new hold writes.
    with pytest.raises(DatabaseTargetRefused, match="held"):
        db.build_dsn("runtime")
    assert database_targets.main(["status"]) == 0
    assert "held for this installation" in capsys.readouterr().out
    database_targets.hold_target("db.example.internal", 5432, reason="new incident hold")
    registry = json.loads((personal_root / database_targets.REGISTRY_NAME).read_text())
    assert [row["host"] for row in registry["held"]] == [legacy_host, "db.example.internal"]
    with pytest.raises(DatabaseTargetRefused, match="held"):
        db.build_dsn("runtime")
    assert tripwires.secret_reads == []


def test_legacy_bracketed_loopback_hold_remains_effective_and_deduplicates(personal_root):
    _configure(host="localhost")
    _registry(
        personal_root,
        approved=[("localhost", 5432, "vres_personal")],
        held=[("[::1]", 5432)],
    )
    with pytest.raises(DatabaseTargetRefused, match="held"):
        db.build_dsn("runtime")
    database_targets.hold_target("127.0.0.2", 5432, reason="same held loopback")
    registry = json.loads((personal_root / database_targets.REGISTRY_NAME).read_text())
    assert [(row["host"], row["port"]) for row in registry["held"]] == [("[::1]", 5432)]
    database_targets.hold_target("db.example.internal", 5432, reason="other host")
    registry = json.loads((personal_root / database_targets.REGISTRY_NAME).read_text())
    assert len(registry["held"]) == 2


# B5. Equivalent non-loopback host spellings share HELDS, not approvals.

@pytest.mark.parametrize(
    "held_host,alias_host",
    [
        ("2001:db8::5", "2001:0db8::5"),
        ("2001:db8::5", "2001:db8:0:0:0:0:0:5"),
        ("2001:0db8::5", "2001:db8::5"),
        ("10.0.0.5", "::ffff:10.0.0.5"),
        ("::ffff:a00:5", "10.0.0.5"),
        ("10.0.0.5", "10.0.0.5."),
        ("db.example.internal", "db.example.internal."),
        ("db.example.internal.", "DB.EXAMPLE.INTERNAL"),
    ],
)
@pytest.mark.parametrize("purpose", ["runtime", "writer", "migrator"])
def test_nonloopback_held_alias_refused_before_credentials(
    personal_root, tripwires, held_host, alias_host, purpose,
):
    _configure(host=alias_host)
    _registry(
        personal_root,
        approved=[(alias_host.lower(), 5432, "vres_personal")],
        held=[(held_host, 5432)],
    )
    with pytest.raises(DatabaseTargetRefused, match="held"):
        db.build_dsn(purpose)
    assert tripwires.secret_reads == []


@pytest.mark.parametrize(
    "held_host,alias_host",
    [
        ("2001:db8::5", "2001:db8:0:0:0:0:0:5"),
        ("10.0.0.5", "::ffff:a00:5"),
        ("db.example.internal", "db.example.internal."),
    ],
)
def test_nonloopback_alias_hold_refuses_admin_and_setup(
    personal_root, monkeypatch, held_host, alias_host,
):
    _registry(personal_root, held=[(held_host, 5432)])
    with pytest.raises(DatabaseTargetRefused, match="held"):
        database_targets.require_admin_contact(
            f"host={alias_host} port=5432 dbname=postgres",
            "vres_personal",
        )
    monkeypatch.setattr(database_targets, "_interactive", lambda: True)
    with pytest.raises(DatabaseTargetRefused, match="cannot be approved"):
        database_targets.confirm_target_for_setup(
            alias_host, 5432, "vres_personal",
            ask=lambda _prompt: pytest.fail("held alias reached approval prompt"),
        )


@pytest.mark.parametrize(
    "existing,second",
    [
        ("2001:db8::5", "2001:0db8:0:0:0:0:0:5"),
        ("10.0.0.5", "::ffff:10.0.0.5"),
        ("db.example.internal", "db.example.internal."),
    ],
)
def test_nonloopback_alias_hold_is_deduplicated(personal_root, existing, second):
    _registry(personal_root, held=[(existing, 5432)])
    database_targets.hold_target(second, 5432, reason="same physical spelling")
    registry = json.loads((personal_root / database_targets.REGISTRY_NAME).read_text())
    assert len(registry["held"]) == 1
    assert registry["held"][0]["host"] == existing


@pytest.mark.parametrize(
    "approved_host,other_spelling",
    [
        ("2001:db8::5", "2001:0db8::5"),
        ("10.0.0.5", "::ffff:10.0.0.5"),
        ("db.example.internal", "db.example.internal."),
    ],
)
def test_nonloopback_hold_identity_never_expands_approval(
    personal_root, tripwires, approved_host, other_spelling,
):
    _configure(host=other_spelling)
    _registry(personal_root, approved=[(approved_host, 5432, "vres_personal")])
    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        db.build_dsn("runtime")
    assert tripwires.secret_reads == []


@pytest.mark.parametrize(
    "held_host,unrelated",
    [
        ("2001:db8::5", "2001:db8::6"),
        ("10.0.0.5", "10.0.0.6"),
        ("db.example.internal", "db2.example.internal"),
    ],
)
def test_unrelated_approved_server_not_affected_by_nonloopback_hold(
    personal_root, held_host, unrelated,
):
    _registry(
        personal_root,
        approved=[(unrelated, 5432, "vres_personal")],
        held=[(held_host, 5432)],
    )
    database_targets.require_contact(
        f"host={unrelated} port=5432 dbname=vres_personal"
    )


@pytest.mark.parametrize("bad_port", ["²", "٥٤٣٢", "５４３２"])
def test_non_ascii_port_spelling_fails_closed_as_database_target_refused(bad_port):
    with pytest.raises(DatabaseTargetRefused, match="invalid port"):
        database_targets._target_from_params(
            {"host": "localhost", "port": bad_port, "dbname": "vres_personal"}
        )


def test_status_reports_legacy_invalid_approvals_and_config_without_exiting(
    personal_root, capsys,
):
    _configure(host="@vres")
    _registry(
        personal_root,
        approved=[
            ("@vres", 5432, "vres_personal"),
            ("db.example.internal", 5433, "vres_personal"),
        ],
        held=[("@vres", 5432)],
    )
    assert database_targets.main(["status"]) == 0
    output = capsys.readouterr().out
    assert "approved (inactive): unsafe historical target at port 5432" in output
    assert "approved: database 'vres_personal' at db.example.internal:5433" in output
    assert "held server: @vres:5432" in output
    assert "blocks EVERY host on port 5432" in output
    assert "configured target: REFUSED" in output


def test_status_explains_port_wide_legacy_hold_without_registry_mutation(
    personal_root, capsys,
):
    _configure(host="db.example.internal")
    _registry(
        personal_root,
        approved=[("db.example.internal", 5432, "vres_personal")],
        held=[("127.1", 5432)],
    )
    before = (personal_root / database_targets.REGISTRY_NAME).read_bytes()
    assert database_targets.main(["status"]) == 0
    output = capsys.readouterr().out
    assert "blocks EVERY host on port 5432" in output
    assert "held for this installation" in output
    assert (personal_root / database_targets.REGISTRY_NAME).read_bytes() == before


def test_unverified_nat64_48_is_refused_even_with_exact_approval(
    personal_root, tripwires,
):
    host = "64:ff9b:1::1234"
    _configure(host=host)
    _registry(personal_root, approved=[(host, 5432, "vres_personal")])
    with pytest.raises(DatabaseTargetRefused, match="ambiguous or unsafe"):
        db.build_dsn("runtime")
    assert tripwires.secret_reads == []


# B. Unknown and ambiguous targets


def test_unknown_target_is_refused_before_any_connection(personal_root, tripwires):
    _configure()

    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        db.build_dsn("runtime")
    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        db.migrate()

    assert tripwires.secret_reads == []
    assert not (personal_root / database_targets.REGISTRY_NAME).exists()


def test_approval_is_exact_host_port_and_database(personal_root, monkeypatch):
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    monkeypatch.setattr(db, "SecretStore", lambda: SimpleNamespace(get=lambda _key: "synthetic-runtime-password"))

    for host, port, database in [
        ("localhost", 5432, "vres_os"),
        ("127.0.0.1", 5432, "vres_personal"),
        ("localhost", 5433, "vres_personal"),
        ("localhost", 5432, "VRES_PERSONAL"),
    ]:
        _configure(host=host, port=port, database=database)
        with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
            db.build_dsn("runtime")

    _configure()
    assert "dbname=vres_personal" in db.build_dsn("runtime")


@pytest.mark.parametrize(
    "dsn,reason",
    [
        ("host=a,b port=5432,5432 dbname=vres_personal", "several servers"),
        ("service=vres port=5432 dbname=vres_personal", "'service'"),
        ("host=localhost hostaddr=10.0.0.9 port=5432 dbname=vres_personal", "'hostaddr'"),
        ("port=5432 dbname=vres_personal", "explicitly"),
        ("host=localhost dbname=vres_personal", "explicitly"),
        ("host=localhost port=5432", "explicitly"),
        ("host=localhost port=5432 dbname='host=elsewhere dbname=other'", "embeds another"),
        (f"host=localhost port=5432 dbname=x password='{_SECRET}", "could not parse"),
        ("postgresql://localhost:5432/vres_personal?service=other", "'service'"),
    ],
)
def test_ambiguous_connection_strings_are_refused_without_echoing_them(personal_root, monkeypatch, dsn, reason):
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    monkeypatch.setenv("VRES_DATABASE_URL", dsn)

    with pytest.raises(DatabaseTargetRefused, match=re.escape(reason)) as exc:
        db.build_dsn("runtime")

    assert _SECRET not in str(exc.value) and exc.value.__cause__ is None


@pytest.mark.parametrize(
    "content",
    [
        "{not json",
        json.dumps({"version": 2, "approved": [], "held": []}),
        json.dumps({"version": True, "approved": [], "held": []}),
        json.dumps({"version": 1.0, "approved": [], "held": []}),
        json.dumps({"version": 1, "approved": [], "held": [], "bypass": True}),
        json.dumps({"version": 1, "approved": [{"host": "localhost", "port": "5432", "dbname": "x",
                                                "approved_at": "t", "approved_by": "t"}], "held": []}),
        json.dumps({"version": 1, "approved": [{"host": "localhost", "port": 5432, "dbname": "vres_personal",
                                                "approved_at": None, "approved_by": "t"}], "held": []}),
        json.dumps({"version": 1, "approved": "*", "held": []}),
    ],
)
def test_unreadable_registry_refuses_every_target(personal_root, content):
    _configure()
    (personal_root / database_targets.REGISTRY_NAME).write_text(content, encoding="utf-8")

    with pytest.raises(DatabaseTargetRefused, match="could not read its database target registry"):
        db.build_dsn("runtime")


def test_libpq_routing_environment_makes_an_approved_target_ambiguous(personal_root, monkeypatch):
    _configure()
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    monkeypatch.setenv("PGHOSTADDR", "10.9.8.7")

    with pytest.raises(DatabaseTargetRefused, match="PGHOSTADDR") as exc:
        db.build_dsn("runtime")

    assert "10.9.8.7" not in str(exc.value)


# C. Environment-provided DSNs


@pytest.mark.parametrize(
    "purpose,variables",
    [
        ("runtime", {"VRES_DATABASE_URL": None}),
        ("writer", {"VRES_PROVENANCE_WRITER_DATABASE_URL": None}),
        ("migrator", {"VRES_MIGRATION_DATABASE_URL": None}),
        ("runtime", {"VRES_TEST_DATABASE_URL": None, "VRES_ALLOW_TEST_DB": "1"}),
    ],
)
def test_environment_dsn_cannot_bypass_the_guard(personal_root, monkeypatch, tripwires, purpose, variables):
    dsn = f"postgresql://vres_user:{_SECRET}@db.example.internal:5432/vres_live_test"
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    for name, value in variables.items():
        monkeypatch.setenv(name, value or dsn)

    with pytest.raises(DatabaseTargetRefused, match="has not been approved") as exc:
        with db.connect(purpose=purpose):
            pass  # pragma: no cover

    assert _SECRET not in str(exc.value) and "vres_user" not in str(exc.value)
    assert tripwires.secret_reads == []


def test_data_dir_override_cannot_supply_an_approval(personal_root, tmp_path):
    _configure()
    data_dir = tmp_path / "data"
    _registry(data_dir, approved=[("localhost", 5432, "vres_personal")])

    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        db.build_dsn("runtime")


# B1. No installation state, marker or environment variable authorizes contact on Windows


@pytest.mark.parametrize(
    "markers",
    [(), ("active-install.json",), ("pending-install.json",), ("active-install.json", "pending-install.json")],
    ids=["source-checkout-no-markers", "installed", "interrupted-install", "both-markers"],
)
def test_every_windows_process_is_guarded_whatever_the_installation_state(personal_root, tripwires, markers):
    for name in markers:
        (personal_root / name).write_text("{}", encoding="utf-8")
    _configure()

    assert database_targets.personal_release_root() == personal_root
    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        db.build_dsn("runtime")
    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        database_targets.require_admin_contact("host=localhost port=5432 dbname=postgres", "vres_personal")
    assert tripwires.secret_reads == []


def test_missing_registry_root_is_a_guarded_installation_that_approves_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(database_targets, "_known_local_app_data", lambda: str(tmp_path / "never-created"))
    _configure()

    assert database_targets.personal_release_root() == tmp_path / "never-created" / "VresOS"
    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        db.build_dsn("runtime")


@pytest.mark.parametrize(
    "variable", ["LOCALAPPDATA", "WIN_PD_OVERRIDE_LOCAL_APPDATA", "VRES_DATA_DIR", "VRES_ALLOW_TEST_DB", "OS"]
)
def test_environment_variables_cannot_disable_or_relocate_the_guard(personal_root, monkeypatch, tmp_path, variable):
    elsewhere = tmp_path / "elsewhere"
    _registry_dir = elsewhere / "VresOS"
    _registry_dir.mkdir(parents=True)
    _registry(_registry_dir, approved=[("localhost", 5432, "vres_personal")])
    _configure()
    monkeypatch.setenv(variable, str(elsewhere) if variable != "VRES_ALLOW_TEST_DB" else "1")

    assert database_targets.personal_release_root() == personal_root
    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        db.build_dsn("runtime")


def test_guarded_platform_follows_the_interpreter_platform_only(monkeypatch):
    # conftest forces the guard on for unit tests; this checks the real rule captured at import.
    assert _REAL_GUARDED_PLATFORM() is (sys.platform == "win32")
    for name in ("OS", "LOCALAPPDATA", "WIN_PD_OVERRIDE_LOCAL_APPDATA", "VRES_DATA_DIR", "VRES_ALLOW_TEST_DB"):
        monkeypatch.setenv(name, "Linux")
    assert _REAL_GUARDED_PLATFORM() is (sys.platform == "win32")


@pytest.mark.skipif(sys.platform != "win32", reason="Windows known-folder resolution")
def test_installation_root_is_resolved_from_the_shell_not_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("WIN_PD_OVERRIDE_LOCAL_APPDATA", str(tmp_path))

    resolved = Path(database_targets._shell_local_app_data())

    assert resolved.is_absolute() and resolved != tmp_path


def test_non_windows_process_is_outside_the_guard_and_keeps_legacy_dsn_behaviour(monkeypatch):
    """Explicit boundary: the personal release cannot run off Windows (Linux CI is outside it)."""
    monkeypatch.setattr(database_targets, "_guarded_platform", lambda: False)
    monkeypatch.setenv("VRES_DATABASE_URL", "legacy opaque test value")

    assert database_targets.personal_release_root() is None
    assert db.build_dsn("runtime") == "legacy opaque test value"


# B2. Marker/registry ambiguity is refusal, never absence


def _fake_lstat(real, path_suffix, outcome):
    def fake(path):
        if str(path).endswith(path_suffix):
            if isinstance(outcome, BaseException):
                raise outcome
            return outcome
        return real(path)

    return fake


@pytest.mark.parametrize(
    "suffix,outcome,message",
    [
        ("VresOS", PermissionError(13, "denied"), "could not inspect its database target registry root"),
        ("VresOS", OSError(1921, "cannot resolve"), "could not inspect its database target registry root"),
        (database_targets.REGISTRY_NAME, PermissionError(13, "denied"), "could not inspect its database target registry"),
        (database_targets.REGISTRY_NAME, NotADirectoryError(20, "not a dir"), "could not inspect"),
        (database_targets.REGISTRY_NAME, OSError(5, "access denied"), "could not inspect"),
    ],
)
def test_inaccessible_root_or_registry_is_refused_not_treated_as_absent(
    personal_root, monkeypatch, suffix, outcome, message
):
    _configure()
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    monkeypatch.setattr(database_targets, "_lstat", _fake_lstat(database_targets._lstat, suffix, outcome))

    with pytest.raises(DatabaseTargetRefused, match=message):
        db.build_dsn("runtime")


def test_reparse_point_or_wrong_type_is_refused(personal_root, monkeypatch):
    _configure()
    registry = personal_root / database_targets.REGISTRY_NAME
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    real = database_targets._lstat
    plain = real(registry)
    reparse = SimpleNamespace(
        st_mode=plain.st_mode, st_size=plain.st_size, st_ino=plain.st_ino, st_dev=plain.st_dev,
        st_file_attributes=database_targets.stat.FILE_ATTRIBUTE_REPARSE_POINT,
    )
    for suffix, outcome in (
        (database_targets.REGISTRY_NAME, reparse),
        ("VresOS", SimpleNamespace(st_mode=plain.st_mode, st_file_attributes=0)),  # root is a file
        (database_targets.REGISTRY_NAME, real(personal_root)),  # registry is a directory
    ):
        monkeypatch.setattr(database_targets, "_lstat", _fake_lstat(real, suffix, outcome))
        with pytest.raises(DatabaseTargetRefused, match="link, junction or unexpected file type"):
            db.build_dsn("runtime")


@pytest.mark.skipif(sys.platform != "win32", reason="Windows directory junction")
def test_real_junction_as_registry_root_is_refused(monkeypatch, tmp_path):
    import _winapi

    target = tmp_path / "target" / "VresOS"
    target.mkdir(parents=True)
    _registry(target, approved=[("localhost", 5432, "vres_personal")])
    local = tmp_path / "local"
    local.mkdir()
    _winapi.CreateJunction(str(target), str(local / "VresOS"))
    monkeypatch.setattr(database_targets, "_known_local_app_data", lambda: str(local))
    _configure()

    with pytest.raises(DatabaseTargetRefused, match="link, junction"):
        db.build_dsn("runtime")


def test_registry_swapped_between_inspection_and_read_is_refused(personal_root, monkeypatch):
    _configure()
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    registry = personal_root / database_targets.REGISTRY_NAME
    inspected = database_targets._lstat(registry)
    swapped = SimpleNamespace(
        st_mode=inspected.st_mode, st_size=inspected.st_size, st_ino=inspected.st_ino + 1,
        st_dev=inspected.st_dev, st_file_attributes=0,
    )
    monkeypatch.setattr(
        database_targets, "_lstat", _fake_lstat(database_targets._lstat, database_targets.REGISTRY_NAME, swapped)
    )

    with pytest.raises(DatabaseTargetRefused, match="could not read its database target registry"):
        db.build_dsn("runtime")


def test_installer_markers_are_never_created_or_changed_by_the_guard(personal_root):
    _configure()
    with pytest.raises(DatabaseTargetRefused):
        db.build_dsn("runtime")

    assert sorted(p.name for p in personal_root.iterdir()) == []


# D/E. Migration metadata is inspected read-only before any lock or DDL


class _Cursor:
    def __init__(self, row=None, rows=()):
        self._row, self._rows = row, list(rows)

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows

    def __iter__(self):
        return iter(self._rows)


class _LedgerConnection:
    """Scripted server: answers the migration catalog queries and records every statement."""

    def __init__(self, *, schema=True, ledger=True, checksum_column=True, rows=(), objects=0, database="vres_personal"):
        self.schema, self.ledger, self.checksum_column = schema, ledger, checksum_column
        self.rows, self.objects, self.database, self.log = list(rows), objects, database, []

    def execute(self, sql, params=None):
        text = " ".join(str(sql).split())
        self.log.append(text)
        if text.startswith("SELECT to_regnamespace"):
            return _Cursor({"schema_present": self.schema, "ledger_present": self.ledger})
        if text.startswith("SELECT EXISTS (SELECT 1 FROM pg_attribute"):
            return _Cursor({"present": self.checksum_column})
        if text.startswith("SELECT version"):
            return _Cursor(rows=[{"version": v, "checksum": c} for v, c in self.rows])
        if text.startswith("SELECT (SELECT count(*)"):
            return _Cursor({"n": self.objects})
        if text.startswith("SELECT current_database()"):
            return _Cursor({"name": self.database})
        if text == "SELECT 1 FROM pg_namespace WHERE nspname='vres'":
            return _Cursor({"present": 1} if self.schema else None)
        if "pg_get_userbyid(nspowner)" in text:
            return _Cursor({"owner": "vres_migrator"})
        if text.startswith("SELECT to_regclass("):
            return _Cursor({"present": True})
        return _Cursor()

    def transaction(self):
        return nullcontext()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def _package_ledger(upto: int | None = None) -> list[tuple[str, str]]:
    root = resources.files("vres_os").joinpath("migrations")
    names = sorted(p.name for p in root.iterdir() if p.name.endswith(".sql"))
    return [(n, db._digest(root.joinpath(n).read_text(encoding="utf-8"))) for n in names][:upto]


def _scripted(monkeypatch, cfg, *connections):
    opened, queue = [], list(connections)

    @contextmanager
    def fake_connect(*, autocommit=False, purpose="runtime"):
        opened.append((purpose, autocommit))
        yield queue.pop(0)

    monkeypatch.setattr(db, "connect", fake_connect)
    monkeypatch.setattr(db, "ConfigStore", lambda: SimpleNamespace(load=lambda: cfg))
    monkeypatch.setattr(db, "_test_single_role_dsn", lambda: None)
    return opened


def _certified() -> VresConfig:
    cfg = VresConfig(configured=True)
    cfg.database.user, cfg.database.provenance_writer_user = "vres_runtime", "vres_writer"
    cfg.database.migration_user, cfg.database.provenance_boundary_version = "vres_migrator", 1
    return cfg


def _assert_read_only(conn: _LedgerConnection) -> None:
    assert conn.log[0] == "SET TRANSACTION READ ONLY"
    assert not [s for s in conn.log if _MUTATION.search(s)], conn.log


def test_newer_ledger_raises_drift_with_zero_ddl_and_zero_lock(monkeypatch):
    preflight = _LedgerConnection(rows=[*_package_ledger(), ("048_source_effective_trust.sql", "f" * 64)])
    opened = _scripted(monkeypatch, _certified(), preflight)

    with pytest.raises(MigrationDrift, match="absent from this package: \\['048_source_effective_trust.sql'\\]"):
        db.migrate()

    assert opened == [("migrator", False)]
    _assert_read_only(preflight)


@pytest.mark.parametrize(
    "rows,message",
    [
        ([("001_initial.sql", "0" * 64)], "differs from package"),
        ([("001_initial.sql", None)], "no recorded checksum"),
        ([("001_initial.sql", 7)], "ambiguous rows"),
    ],
)
def test_mismatched_or_ambiguous_ledger_refuses_without_mutation(monkeypatch, rows, message):
    preflight = _LedgerConnection(rows=rows)
    opened = _scripted(monkeypatch, _certified(), preflight)

    with pytest.raises(MigrationDrift, match=message):
        db.migrate()

    assert opened == [("migrator", False)]
    _assert_read_only(preflight)


@pytest.mark.parametrize("objects", [3, 0], ids=["counted-objects", "no-counted-objects"])
def test_existing_vres_schema_without_a_ledger_is_never_treated_as_empty(monkeypatch, objects):
    """Object counts cannot inventory every PostgreSQL object type, so none is taken."""
    preflight = _LedgerConnection(ledger=False, objects=objects)
    opened = _scripted(monkeypatch, _certified(), preflight)

    with pytest.raises(MigrationDrift, match="exists but has no migration ledger"):
        db.migrate()

    assert opened == [("migrator", False)]
    _assert_read_only(preflight)
    assert not [s for s in preflight.log if "count(*)" in s]


def test_single_role_runtime_also_refuses_an_unledgered_schema(monkeypatch):
    preflight = _LedgerConnection(schema=True, ledger=False)
    _scripted(monkeypatch, VresConfig(), preflight)
    monkeypatch.setattr(db, "_test_single_role_dsn", lambda: "approved disposable test target")

    with pytest.raises(MigrationDrift, match="exists but has no migration ledger"):
        db.migrate()
    _assert_read_only(preflight)


@pytest.mark.parametrize(
    "locked_rows",
    [
        [*_package_ledger(40), ("042_experience_retrieval_policy_v2.sql", "e" * 64)],
        _package_ledger(39),
        [*_package_ledger(39), (_package_ledger(40)[-1][0], "d" * 64)],
    ],
    ids=["unknown-appended", "row-removed", "checksum-rewritten"],
)
def test_metadata_change_between_preflight_and_lock_fails_closed_before_ddl(monkeypatch, locked_rows):
    preflight = _LedgerConnection(rows=_package_ledger(40))
    locked = _LedgerConnection(rows=locked_rows)
    opened = _scripted(monkeypatch, _certified(), preflight, locked)

    with pytest.raises(MigrationDrift):
        db.migrate()

    assert opened == [("migrator", False), ("migrator", True)]
    _assert_read_only(preflight)
    assert locked.log[0] == "SELECT pg_advisory_lock(8675309001)"
    assert not [s for s in locked.log[1:] if _MUTATION.search(s)], locked.log


def test_concurrent_valid_migration_is_accepted_under_the_lock(monkeypatch):
    preflight = _LedgerConnection(rows=_package_ledger(40))
    locked = _LedgerConnection(rows=_package_ledger())
    _scripted(monkeypatch, _certified(), preflight, locked)

    assert db.migrate() == []
    assert not [s for s in locked.log if s.startswith(("CREATE TABLE", "ALTER TABLE vres.schema_migrations"))]


# F. Explicitly approved empty database keeps its initialization path


class _ScriptedDriver:
    """Stands in for psycopg after the guard; records the conninfo of every connection it is asked for."""

    OperationalError = psycopg.OperationalError
    InterfaceError = psycopg.InterfaceError
    ClientCursor = psycopg.ClientCursor

    def __init__(self, *connections):
        self.queue, self.conninfo = list(connections), []

    def connect(self, conninfo, **kwargs):
        self.conninfo.append((conninfo, kwargs.get("autocommit", False)))
        return self.queue.pop(0)


def test_empty_approved_database_initializes_after_read_only_preflight(personal_root, monkeypatch):
    """The state secure setup leaves in a new database: the schema with its empty ledger."""
    _configure(database="vres_personal_test")
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal_test")])
    preflight, locked = _LedgerConnection(), _LedgerConnection()
    driver = _ScriptedDriver(preflight, locked)
    monkeypatch.setattr(db, "_driver", lambda: driver)
    monkeypatch.setattr(db, "SecretStore", lambda: SimpleNamespace(get=lambda _key: "synthetic-migrator-password"))

    applied = db.migrate()

    assert applied == [name for name, _ in _package_ledger()]
    assert [autocommit for _, autocommit in driver.conninfo] == [False, True]
    assert all("dbname=vres_personal_test" in info and "user=vres_migrator" in info for info, _ in driver.conninfo)
    _assert_read_only(preflight)
    lock = locked.log.index("SELECT pg_advisory_lock(8675309001)")
    first_ddl = next(i for i, s in enumerate(locked.log) if _MUTATION.search(s) and i != lock)
    assert lock == 0 and first_ddl > lock
    assert not [s for s in locked.log if s.startswith(("CREATE TABLE vres.schema_migrations", "CREATE SCHEMA"))]


def test_single_role_test_database_bootstraps_its_schema_after_the_lock(monkeypatch):
    preflight, locked = _LedgerConnection(schema=False, ledger=False), _LedgerConnection(schema=False, ledger=False)
    cfg = VresConfig()
    _scripted(monkeypatch, cfg, preflight, locked)
    monkeypatch.setattr(db, "_test_single_role_dsn", lambda: "approved disposable test target")

    assert len(db.migrate()) == len(_package_ledger())
    _assert_read_only(preflight)
    assert locked.log.index("CREATE SCHEMA IF NOT EXISTS vres") > locked.log.index("SELECT pg_advisory_lock(8675309001)")


# G. Startup against a held target


def test_start_against_held_target_returns_sanitized_refusal(personal_root, tripwires, monkeypatch, tmp_path):
    from vres_os.project import ProjectIdentity

    _configure(database="vres_os")
    _registry(personal_root, held=[("localhost", 5432)])
    # P2-D: file-only project adoption runs before any database step, so an eligible (fresh) project is
    # discovered first; registration must still never be reached after the database refusal.
    (tmp_path / "eligible").mkdir()
    project = ProjectIdentity(tmp_path / "eligible", "project:held-target", "eligible", None, None)
    monkeypatch.setattr(bootstrap, "discover_project", lambda *_a: project)
    monkeypatch.setattr(bootstrap, "Repository", lambda: pytest.fail("project registered after refusal"))

    result = bootstrap.start_for_project(".")

    assert result["status"] == "DATABASE_TARGET_REFUSED"
    assert "held for this installation" in result["message"]
    assert "made no database connection" in result["action"]
    assert "password" not in json.dumps(result).lower()
    assert tripwires.secret_reads == []


def test_secure_setup_refuses_held_target_before_prompting_for_any_password(personal_root, monkeypatch):
    _registry(personal_root, held=[("localhost", 5432)])
    store = ConfigStore()
    store.save(VresConfig())
    results = []
    monkeypatch.setattr(bootstrap, "_ask", lambda _prompt, default: default)
    monkeypatch.setattr(bootstrap, "_yes_no", lambda *_a: False)
    monkeypatch.setattr(bootstrap.getpass, "getpass", lambda *_a: pytest.fail("password requested"))
    monkeypatch.setattr(bootstrap, "_write_setup_result", lambda status, **kw: results.append((status, kw)))
    monkeypatch.setattr(bootstrap, "SecretStore", lambda: SimpleNamespace(get=lambda _k: None))

    with pytest.raises(SystemExit) as exc:
        bootstrap._interactive_setup()

    assert exc.value.code == 2
    assert results[-1][0] == "failed" and results[-1][1]["cleanup"] == "no_resources_created"
    assert store.load().configured is False


# H. Administrator connections and approval recording


def test_admin_connections_require_an_approved_database_on_that_server(personal_root, monkeypatch, tripwires):
    cfg = _configure(boundary=False)
    admin = f"host=localhost port=5432 dbname=postgres user=postgres password={_SECRET}"
    monkeypatch.setattr(bootstrap, "_ask", lambda _prompt, default: default)
    monkeypatch.setattr(bootstrap.getpass, "getpass", lambda *_a: _SECRET)
    creds = BoundaryCredentials("vres_writer", "w", "vres_migrator", "m")
    provisioned = bootstrap._ProvisionedLocalDatabase("r", admin, "vres_personal", "vres_runtime")
    calls = [
        lambda: bootstrap._provision_local_database(
            host="localhost", port=5432, database="vres_personal", runtime_user="vres_runtime", sslmode="prefer"
        ),
        lambda: bootstrap._cleanup_provisioned_local_database(provisioned),
        lambda: bootstrap._test_database(
            host="localhost", port=5432, database="vres_personal", user="vres_runtime", password=_SECRET, sslmode="prefer"
        ),
        lambda: database_boundary.provision_boundary(cfg, admin_dsn=admin),
        lambda: database_boundary.rollback_boundary_provision(cfg, creds, admin_dsn=admin),
    ]
    for call in calls:
        with pytest.raises(DatabaseTargetRefused, match="has not been approved") as exc:
            call()
        assert _SECRET not in str(exc.value)

    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")], held=[("127.0.0.1", 5432)])
    for call in calls:
        with pytest.raises(DatabaseTargetRefused, match="held"):
            call()


def test_approved_admin_contact_reaches_the_driver_only_for_that_server(personal_root, monkeypatch):
    cfg = _configure(boundary=False)
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    reached = []

    class Reached(Exception):
        pass

    def record(conninfo, **_kwargs):
        reached.append(conninfo)
        raise Reached

    monkeypatch.setattr(database_boundary, "_driver", lambda: SimpleNamespace(connect=record))

    with pytest.raises(Reached):
        database_boundary.provision_boundary(cfg, admin_dsn="host=localhost port=5432 dbname=postgres user=postgres")
    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        database_boundary.provision_boundary(cfg, admin_dsn="host=localhost port=5433 dbname=postgres user=postgres")
    assert len(reached) == 1


def test_setup_approval_needs_the_interactive_console_and_the_exact_name(personal_root, monkeypatch):
    path = personal_root / database_targets.REGISTRY_NAME
    monkeypatch.setattr(database_targets, "_interactive", lambda: False)
    with pytest.raises(DatabaseTargetRefused, match="interactive secure setup console"):
        database_targets.confirm_target_for_setup("localhost", 5432, "vres_personal", ask=pytest.fail)
    assert not path.exists()

    monkeypatch.setattr(database_targets, "_interactive", lambda: True)
    for typed in ("", "VRES_PERSONAL", "vres_personal "):
        with pytest.raises(DatabaseTargetRefused, match="was not approved"):
            database_targets.confirm_target_for_setup("localhost", 5432, "vres_personal", ask=lambda _p, t=typed: t)
    assert not path.exists()

    database_targets.confirm_target_for_setup("LocalHost", 5432, "vres_personal", ask=lambda _p: "vres_personal")
    approved = json.loads(path.read_text(encoding="utf-8"))["approved"]
    assert [(a["host"], a["port"], a["dbname"], a["approved_by"]) for a in approved] == [
        ("localhost", 5432, "vres_personal", "secure-setup")
    ]
    database_targets.confirm_target_for_setup("localhost", 5432, "vres_personal", ask=pytest.fail)


def test_console_approval_is_interactive_only_and_refuses_held_servers(personal_root, monkeypatch, capsys):
    path = personal_root / database_targets.REGISTRY_NAME
    argv = ["approve", "--host", "localhost", "--port", "5432", "--dbname", "vres_disposable_test"]
    monkeypatch.setattr("builtins.input", lambda _prompt: "vres_disposable_test")

    monkeypatch.setattr(database_targets, "_interactive", lambda: False)
    assert database_targets.main(argv) == 2 and not path.exists()

    monkeypatch.setattr(database_targets, "_interactive", lambda: True)
    assert database_targets.main(argv) == 0
    assert json.loads(path.read_text())["approved"][0]["approved_by"] == "operator-console"
    assert "does not prove which PostgreSQL" in capsys.readouterr().out

    _registry(personal_root, held=[("localhost", 5432)])
    assert database_targets.main([*argv[:-1], "another_test"]) == 2
    assert json.loads(path.read_text())["approved"] == []


def test_hold_and_status_never_contact_postgresql(personal_root, monkeypatch, capsys, tripwires):
    _configure(database="vres_os")

    assert database_targets.main(["hold", "--host", "localhost", "--port", "5432", "--reason", "schema-048"]) == 0
    assert database_targets.main(["hold", "--host", "127.0.0.1", "--port", "5432", "--reason", "same"]) == 0
    assert database_targets.main(["status"]) == 0

    out = capsys.readouterr().out
    assert "held server: localhost:5432 (schema-048)" in out
    assert "configured database 'vres_os' at localhost:5432: Vres refused" in out
    assert len(json.loads((personal_root / database_targets.REGISTRY_NAME).read_text())["held"]) == 1
    assert tripwires.secret_reads == []


# I. Setup establishes migration compatibility before any provenance mutation

_SCHEMA_048_LEDGER = [*_package_ledger(), ("048_source_effective_trust.sql", "f" * 64)]
_ADMIN = "host=localhost port=5432 dbname=vres_personal user=postgres"


class _AdminDriver:
    """The administrator connection secure setup opens for the provenance role split."""

    def __init__(self, conn):
        self.conn, self.opened = conn, []

    def connect(self, conninfo, **kwargs):
        self.opened.append(kwargs.get("autocommit", False))
        return self.conn


def _mutations(conn: _LedgerConnection) -> list[str]:
    return [s for s in conn.log if _MUTATION.search(s)]


def _provenance_setup(monkeypatch, personal_root, conn, *, configured):
    """Run secure setup up to the provenance step against a scripted administrator connection."""
    cfg = _configure(boundary=False)
    if not configured:
        cfg.configured = False
        ConfigStore().save(cfg)
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    driver = _AdminDriver(conn)
    vault = {cfg.database.password_key: "synthetic-runtime-credential"}
    results, persisted = [], []
    monkeypatch.setattr(database_boundary, "_driver", lambda: driver)
    monkeypatch.setattr(bootstrap, "SecretStore", lambda: SimpleNamespace(
        get=vault.get, set=vault.__setitem__, delete=lambda k: vault.pop(k, None)))
    monkeypatch.setattr(bootstrap, "_ask", lambda _prompt, default: default)
    monkeypatch.setattr(bootstrap, "_yes_no", lambda *_a: False)
    monkeypatch.setattr(bootstrap.getpass, "getpass", lambda *_a: _SECRET)
    monkeypatch.setattr(bootstrap, "_test_database", lambda **_kw: None)
    monkeypatch.setattr(bootstrap, "_write_setup_result", lambda status, **kw: results.append((status, kw)))
    monkeypatch.setattr(bootstrap, "persist_boundary_credentials", lambda *a, **kw: persisted.append(a))
    monkeypatch.setattr(bootstrap, "migrate", lambda **_kw: pytest.fail("migrate reached after refusal"))
    with pytest.raises(SystemExit) as exc:
        bootstrap._interactive_setup()
    assert exc.value.code == 2
    assert persisted == [] and driver.opened == [True]
    return results[-1]


@pytest.mark.parametrize("configured", [True, False], ids=["boundary-upgrade", "existing-database-setup"])
def test_unknown_schema_048_ledger_prevents_every_provenance_mutation_in_setup(personal_root, monkeypatch, configured):
    conn = _LedgerConnection(rows=_SCHEMA_048_LEDGER, database="vres_personal")

    status, detail = _provenance_setup(monkeypatch, personal_root, conn, configured=configured)

    assert status == "failed"
    error = str(detail["error"])
    assert "absent from this package" in error and "048_source_effective_trust.sql" in error
    assert conn.log[0] == "SET TRANSACTION READ ONLY"
    assert _mutations(conn) == [], conn.log
    assert not [s for s in conn.log if "pg_roles" in s]  # refused before even the role-name inventory


def test_unknown_schema_048_ledger_prevents_provision_boundary_mutation(personal_root, monkeypatch):
    cfg = _configure(boundary=False)
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    conn = _LedgerConnection(rows=_SCHEMA_048_LEDGER, database="vres_personal")
    monkeypatch.setattr(database_boundary, "_driver", lambda: _AdminDriver(conn))

    with pytest.raises(MigrationDrift, match="absent from this package"):
        database_boundary.provision_boundary(cfg, admin_dsn=_ADMIN)

    assert conn.log[0] == "SET TRANSACTION READ ONLY"
    assert _mutations(conn) == [], conn.log


@pytest.mark.parametrize(
    "conn,message",
    [
        (_LedgerConnection(database="postgres"), "could not confirm it is connected"),
        (_LedgerConnection(database=None), "could not confirm it is connected"),
        (_LedgerConnection(schema=True, ledger=False), "exists but has no migration ledger"),
        (_LedgerConnection(rows=[("001_initial.sql", "0" * 64)]), "differs from package"),
        (_LedgerConnection(rows=[("001_initial.sql", None)]), "no recorded checksum"),
    ],
    ids=["other-database", "unidentified-database", "unledgered-schema", "rewritten", "unrecorded"],
)
def test_setup_refuses_unidentified_or_incompatible_database_before_any_role_change(
    personal_root, monkeypatch, conn, message
):
    cfg = _configure(boundary=False)
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    monkeypatch.setattr(database_boundary, "_driver", lambda: _AdminDriver(conn))

    with pytest.raises(MigrationDrift, match=message):
        database_boundary.provision_boundary(cfg, admin_dsn=_ADMIN)

    assert _mutations(conn) == [], conn.log


def test_current_ledger_passes_the_preflight_and_is_rechecked_inside_the_ownership_transaction(
    personal_root, monkeypatch
):
    cfg = _configure(boundary=False)
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    conn = _LedgerConnection(rows=_package_ledger(22))
    monkeypatch.setattr(database_boundary, "_driver", lambda: _AdminDriver(conn))

    database_boundary.provision_boundary(cfg, admin_dsn=_ADMIN)

    first_mutation = conn.log.index(_mutations(conn)[0])
    assert conn.log[0] == "SET TRANSACTION READ ONLY"
    assert conn.log.index("SELECT current_database() AS name") < first_mutation
    assert "CREATE ROLE" in conn.log[first_mutation]
    recheck = conn.log.index("SELECT current_database() AS name", first_mutation)
    assert recheck < next(i for i, s in enumerate(conn.log) if "OWNER TO" in s or "REVOKE" in s)


def test_genuinely_new_database_gets_its_ledger_with_its_schema(personal_root, monkeypatch):
    cfg = _configure(boundary=False)
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    conn = _LedgerConnection(schema=False, ledger=False)
    monkeypatch.setattr(database_boundary, "_driver", lambda: _AdminDriver(conn))

    database_boundary.provision_boundary(cfg, admin_dsn=_ADMIN)

    schema = next(i for i, s in enumerate(conn.log) if "CREATE SCHEMA vres AUTHORIZATION" in s)
    assert conn.log[schema + 1].startswith("CREATE TABLE vres.schema_migrations(")
    assert "ALTER TABLE vres.schema_migrations OWNER TO" in conn.log[schema + 2]
    assert "vres_runtime_migrator" in conn.log[schema + 2]


# J. Registry changes are serialized; a hold always wins over an approval


def test_hold_recorded_while_an_approval_is_pending_refuses_it_and_survives(personal_root, monkeypatch):
    monkeypatch.setattr(database_targets, "_interactive", lambda: True)

    def operator_types_name_while_another_process_holds_the_server(_prompt):
        database_targets.hold_target("127.0.0.1", 5432, reason="schema-048 incident")
        return "vres_personal"

    with pytest.raises(DatabaseTargetRefused, match="held for this installation while its approval was pending"):
        database_targets.confirm_target_for_setup(
            "localhost", 5432, "vres_personal", ask=operator_types_name_while_another_process_holds_the_server
        )

    registry = json.loads((personal_root / database_targets.REGISTRY_NAME).read_text())
    assert registry["approved"] == []
    assert [(h["host"], h["port"]) for h in registry["held"]] == [("127.0.0.1", 5432)]


def test_completed_approval_never_drops_a_hold_recorded_after_its_first_read(personal_root, monkeypatch):
    monkeypatch.setattr(database_targets, "_interactive", lambda: True)

    def concurrent_hold_on_another_server(_prompt):
        database_targets.hold_target("db.example.internal", 5432, reason="schema-048 incident")
        return "vres_personal"

    database_targets.confirm_target_for_setup("localhost", 5432, "vres_personal", ask=concurrent_hold_on_another_server)

    registry = json.loads((personal_root / database_targets.REGISTRY_NAME).read_text())
    assert [(a["host"], a["dbname"]) for a in registry["approved"]] == [("localhost", "vres_personal")]
    assert [h["host"] for h in registry["held"]] == ["db.example.internal"]
    with pytest.raises(DatabaseTargetRefused, match="held"):
        database_targets.require_contact("host=db.example.internal port=5432 dbname=anything")


def test_registry_lock_serializes_a_hold_behind_another_process(personal_root, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(Path(__file__).parents[1] / "src"))
    script = (
        "import sys\nfrom pathlib import Path\nfrom vres_os.database_targets import _registry_lock\n"
        "with _registry_lock(Path(sys.argv[1])):\n    print('locked', flush=True)\n    sys.stdin.readline()\n"
    )
    holder = subprocess.Popen(
        [sys.executable, "-c", script, str(personal_root)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )
    try:
        assert holder.stdout.readline().strip() == "locked"
        done = threading.Event()
        worker = threading.Thread(
            target=lambda: (database_targets.hold_target("localhost", 5432, reason="incident"), done.set())
        )
        worker.start()
        assert not done.wait(0.5), "the hold was written while another process held the registry lock"
        holder.stdin.write("\n")
        holder.stdin.flush()
        worker.join(15)
        assert done.is_set()
    finally:
        holder.stdin.close()
        holder.wait(10)
    held = json.loads((personal_root / database_targets.REGISTRY_NAME).read_text())["held"]
    assert [(h["host"], h["port"]) for h in held] == [("localhost", 5432)]


@pytest.mark.skipif(sys.platform != "win32", reason="msvcrt byte-range lock")
def test_unobtainable_registry_lock_records_nothing(personal_root, monkeypatch):
    import msvcrt

    def busy(_fd, mode, _n):
        if mode != msvcrt.LK_UNLCK:
            raise OSError("locked by another process")

    monkeypatch.setattr(msvcrt, "locking", busy)

    with pytest.raises(DatabaseTargetRefused, match="could not lock"):
        database_targets.hold_target("localhost", 5432, reason="incident")
    assert not (personal_root / database_targets.REGISTRY_NAME).exists()


@pytest.mark.parametrize("host", ["127.0.0.2", "my-workstation", "192.168.1.20"])
def test_loopback_hold_covers_only_the_recognized_spellings(personal_root, host):
    """Documented limitation: other names or addresses of this machine are distinct targets to the guard."""
    _registry(personal_root, approved=[(host, 5432, "vres_personal")], held=[("localhost", 5432)])

    database_targets.require_contact(f"host={host} port=5432 dbname=vres_personal")
    with pytest.raises(DatabaseTargetRefused, match="held"):
        database_targets.require_contact("host=::1 port=5432 dbname=vres_personal")
