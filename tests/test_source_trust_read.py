"""#176 E7 G7 Chunk 3A: read-only source-trust status/inspect service (unit, no database).

Written RED-first against the accepted R3 contract. The service module is imported lazily so a missing
implementation fails each test on its own instead of one collection error. Fake connections record one ordered log of
connection-attribute assignments and statements passed to ``execute`` (contract T1/T2).
"""
from __future__ import annotations

import ast
import datetime as dt
import importlib
import inspect
import re
from pathlib import Path
from types import SimpleNamespace

import psycopg
import pytest

POLICY_DIGEST = "f20b037b00d0a5711666fd6c1d98538101708d99e7f6f32cf5a490ff6b96cf03"
ATTESTATION = "user_authored_event_in_database_not_host_authenticated_g8_open"
SENTINEL_PID = 987654321
SENTINEL_SID = 876543210
SRC = Path(__file__).resolve().parents[1] / "src" / "vres_os"
TS = dt.datetime(2026, 10, 12, 10, 0, tzinfo=dt.timezone.utc)
D = "d" * 64


@pytest.fixture
def mod():
    return importlib.import_module("vres_os.source_trust_read")


class Cursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class Rig:
    """Shared ordered log + scripted responses + connection factory."""

    def __init__(self, mod, *, source=("active", "trusted_project_source"), reader="unverified",
                 ledger=(), tx=("repeatable read", "on"), fail_attr=None, started=False):
        self.mod, self.log, self.connections, self.purposes = mod, [], 0, []
        self.source, self.reader, self.tx, self.fail_attr, self.started = source, reader, tx, fail_attr, started
        self.ledger = list(ledger)  # [(action, supersedes_ordinal|None)]

    def connect(self, **kw):
        rig = self
        rig.connections += 1
        rig.purposes.append(kw.get("purpose"))

        class Conn:
            info = SimpleNamespace(transaction_status=(
                psycopg.pq.TransactionStatus.INTRANS if rig.started else psycopg.pq.TransactionStatus.IDLE))

            def __setattr__(self, name, value):
                rig.log.append(("attr", name, value))
                if rig.fail_attr == name:
                    raise psycopg.ProgrammingError("refused")
                object.__setattr__(self, name, value)

            def execute(self, sql, params=()):
                rig.log.append(("sql", sql, tuple(params)))
                return Cursor(rig.respond(sql, tuple(params)))

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        class Ctx:
            def __enter__(self_):
                return Conn()

            def __exit__(self_, *a):
                return False

        return Ctx()

    def events(self):
        out = []
        for i, (action, target) in enumerate(self.ledger, start=1):
            out.append({"ordinal": i, "event_key": "STE-%032x" % i, "action": action, "created_at": TS,
                        "content_digest": D, "descriptor_digest": D, "target": target})
        return out

    def respond(self, sql, params):
        m = self.mod
        if sql == m._S0:
            return [{"transaction_isolation": self.tx[0], "transaction_read_only": self.tx[1]}]
        if sql == m._S1:
            if self.source is None:
                return []
            return [{"id": SENTINEL_SID, "status": self.source[0], "authority_level": self.source[1]}]
        if sql == m._S2:
            return [{"effective_trust": self.reader}]
        evs = self.events()
        revoked = {e["target"] for e in evs if e["action"] == "revoke"}
        unrevoked = [e for e in evs if e["action"] == "grant" and e["ordinal"] not in revoked]
        if sql == m._S3:
            n = evs[-1] if evs else None
            return [{"ledger_total": len(evs), "unrevoked_grant_count": len(unrevoked),
                     "distinct_unrevoked_digest_pairs": 1 if unrevoked else 0,
                     "newest_ordinal": n and n["ordinal"], "newest_event_key": n and n["event_key"],
                     "newest_action": n and n["action"], "newest_created_at": n and n["created_at"]}]
        if sql == m._S4:
            limit = params[-1]
            rows = []
            for e in reversed(evs[-limit:] if limit < len(evs) else evs):
                tgt = evs[e["target"] - 1] if e["target"] else None
                by = [r for r in evs if r["action"] == "revoke" and r["target"] == e["ordinal"]]
                rows.append({"ordinal": e["ordinal"], "event_key": e["event_key"], "action": e["action"],
                             "created_at": e["created_at"], "content_digest": e["content_digest"],
                             "descriptor_digest": e["descriptor_digest"],
                             "revokes_event_key": tgt and tgt["event_key"],
                             "target_action": tgt and tgt["action"], "target_ordinal": tgt and tgt["ordinal"],
                             "has_supersedes": e["target"] is not None, "superseding_count": len(by),
                             "revoked_by_event_key": by[0]["event_key"] if by else None, "ledger_total": len(evs)})
            return rows
        raise AssertionError("statement outside the contract allowlist: %r" % sql)

    def service(self):
        return self.mod.SourceTrustReadService(connect_fn=self.connect)

    def sql_log(self):
        return [e[1] for e in self.log if e[0] == "sql"]


def walk(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from walk(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from walk(v)
    else:
        yield value


A_LEDGER = (("grant", None), ("grant", None), ("revoke", 1))  # Scenario A


# ---- T1 / T2 / S0 ordering -------------------------------------------------------------------------------------
def test_t1_attributes_precede_first_execute_and_s0_is_first(mod):
    r = Rig(mod, ledger=A_LEDGER)
    r.service().status(7, "k")
    kinds = [e[0] for e in r.log]
    assert kinds[:2] == ["attr", "attr"] and kinds[2] == "sql"
    assert r.log[0][1:] == ("isolation_level", psycopg.IsolationLevel.REPEATABLE_READ)
    assert r.log[1][1:] == ("read_only", True)
    assert r.log[2][1] == mod._S0
    assert r.connections == 1 and r.purposes == ["runtime"]
    assert not any(re.match(r"\s*(BEGIN|SET|START)", s, re.I) for s in r.sql_log())


@pytest.mark.parametrize("kw", [{"tx": ("read committed", "on")}, {"tx": ("repeatable read", "off")},
                                {"fail_attr": "isolation_level"}, {"fail_attr": "read_only"},
                                {"started": True}])
def test_t1_fail_closed_runs_no_s1_to_s4(mod, kw):
    r = Rig(mod, ledger=A_LEDGER, **kw)
    with pytest.raises((RuntimeError, ValueError)) as ei:
        r.service().status(7, "SENTINEL-KEY")
    assert "SENTINEL-KEY" not in str(ei.value)
    assert not set(r.sql_log()) & {mod._S1, mod._S2, mod._S3, mod._S4}
    assert len(r.sql_log()) <= 1


def test_t2_exact_application_sql_per_call(mod):
    for call, expect in (
        (lambda s: s.status(7, "k"), lambda m: [m._S0, m._S1, m._S2, m._S3]),
        (lambda s: s.inspect(7, "k", 20), lambda m: [m._S0, m._S1, m._S2, m._S3, m._S4]),
    ):
        r = Rig(mod, ledger=A_LEDGER)
        call(r.service())
        assert r.sql_log() == expect(mod)
    r = Rig(mod, source=None)
    with pytest.raises(ValueError, match="source not found in the current project"):
        r.service().status(7, "k")
    assert r.sql_log() == [mod._S0, mod._S1]


def test_t2_allowlist_shape_and_scoping(mod):
    for s in (mod._S0, mod._S1, mod._S2, mod._S3, mod._S4):
        assert s.lstrip().upper().startswith("SELECT")
        assert not re.search(r"WITH", s.upper())
        assert not re.search(r"\b(INSERT|UPDATE|DELETE|CALL|DO|SET|RESET|COMMIT|ROLLBACK|SAVEPOINT|LOCK|CREATE|DROP)\b",
                             s.upper().replace("SET_CONFIG", ""))
    assert "project_id" in mod._S1 and "source_key" in mod._S1
    assert "source_effective_trust" in mod._S2
    for s in (mod._S3, mod._S4):
        # every scan of the ledger table is scoped by project and source (no unscoped table reference)
        scans = s.count("FROM vres.source_trust_events")
        assert scans >= 1 and s.count("project_id=%s") == scans and s.count("source_id=%s") == scans
        assert "vres.source_trust_events" in s and "vres.sources" not in s
    assert "count(*)" in mod._S3 and "FILTER" in mod._S3 and "LIMIT %s" in mod._S4
    assert "ORDER BY ev.ordinal DESC" in mod._S4 and "supersedes_event_id" in mod._S4
    r = Rig(mod, ledger=A_LEDGER)
    r.service().inspect(7, "k", 5)
    params = {e[1]: e[2] for e in r.log if e[0] == "sql"}
    assert params[mod._S1] == ("k", 7)
    assert params[mod._S2] == (SENTINEL_SID,)
    assert params[mod._S3] == (7, SENTINEL_SID) * 3
    assert params[mod._S4] == (7, SENTINEL_SID) * 4 + (5,)


# ---- validation (V1-V3) ----------------------------------------------------------------------------------------
BAD_KEYS = [None, 5, b"k", "", "   ", "k" * 201, "a\x00b", "a\nb", "a\rb", "a\x1fb", "a\x7fb", ["k"]]
BAD_LIMITS = [0, 51, -1, True, False, 1.5, "5", None, [1]]


@pytest.mark.parametrize("key", BAD_KEYS)
def test_v1_bad_source_key_zero_connections(mod, key):
    r = Rig(mod)
    for call in (lambda: r.service().status(7, key), lambda: r.service().inspect(7, key, 5)):
        with pytest.raises(ValueError):
            call()
    assert r.connections == 0 and r.log == []


@pytest.mark.parametrize("limit", BAD_LIMITS)
def test_v1_bad_limit_zero_connections(mod, limit):
    r = Rig(mod)
    with pytest.raises(ValueError):
        r.service().inspect(7, "k", limit)
    assert r.connections == 0 and r.log == []


def test_v2_errors_do_not_echo_values(mod):
    r = Rig(mod)
    secret = "SENTINEL-" + "x" * 300
    with pytest.raises(ValueError) as ei:
        r.service().status(7, secret)
    assert "SENTINEL" not in str(ei.value)
    with pytest.raises(ValueError) as ei:
        r.service().inspect(7, "k", "SENTINEL-LIMIT")
    assert "SENTINEL" not in str(ei.value)


def test_v3_boundaries(mod):
    r = Rig(mod, ledger=A_LEDGER)
    r.service().status(7, "k" * 200)
    for lim in (1, 50):
        r.service().inspect(7, "k", lim)
    r.service().inspect(7, "k")  # default limit 20
    assert r.sql_log()[-1] == mod._S4 and r.log[-1][2][-1] == 20


# ---- output (N1, L7, L8, L10, G1, X4, I1) ---------------------------------------------------------------------
def test_status_shape_scenario_a(mod):
    r = Rig(mod, ledger=A_LEDGER)
    out = r.service().status(7, "k")
    assert list(out) == ["source_key", "effective_trust", "source_status", "declared_authority_level",
                         "label_is_evidence", "policy_version", "policy_digest", "attestation_class",
                         "host_authenticated", "g8", "ledger_total", "newest_event", "mutation"]
    assert out["effective_trust"] == "unverified" and out["label_is_evidence"] is False
    assert out["policy_version"] == "176.g7.v1" and out["policy_digest"] == POLICY_DIGEST
    assert out["attestation_class"] == ATTESTATION and out["host_authenticated"] is False and out["g8"] == "open"
    assert out["ledger_total"] == 3
    assert out["newest_event"] == {"ordinal": 3, "event_key": "STE-%032x" % 3, "action": "revoke",
                                   "created_at": TS.isoformat()}
    assert list(out["newest_event"]) == ["ordinal", "event_key", "action", "created_at"]
    assert out["mutation"] == {"available": False, "reason": "g8_host_ingress_open"}


def test_empty_ledger_newest_event_null(mod):
    out = Rig(mod).service().status(7, "k")
    assert out["ledger_total"] == 0 and out["newest_event"] is None


def test_inspect_inventory_scenario_a(mod):
    r = Rig(mod, ledger=A_LEDGER)
    out = r.service().inspect(7, "k", 20)
    inv = out["inventory"]
    assert inv["ordering"] == "ordinal_descending" and inv["limit"] == 20 and inv["returned"] == 3
    assert inv["ledger_total"] == 3 and inv["truncated"] is False and inv["inventory_complete"] is True
    ev = inv["events"]
    assert [e["ordinal"] for e in ev] == [3, 2, 1]
    assert {k: ev[0][k] for k in ("ordinal", "event_key", "action", "created_at")} == out["newest_event"]
    assert ev[0]["is_newest"] is True and ev[0]["grant_state"] is None
    assert ev[0]["revokes_event_key"] == "STE-%032x" % 1 and ev[0]["revoked_by_event_key"] is None
    assert ev[1]["grant_state"] == "unrevoked" and ev[2]["grant_state"] == "revoked"
    assert ev[2]["revoked_by_event_key"] == "STE-%032x" % 3
    assert all(e["matches_current"] == "not_evaluated" for e in ev)
    ex = out["trust_explanation"]
    assert ex["situations"] == ["newest_event_is_revoke", "newest_revoke_with_unrevoked_grants_present"]
    assert ex["executed"] is False and ex["no_universal_repair_sequence"] is True
    assert ex["production_execution"] == "disabled_g8_open" and "recovered" not in ex
    assert ex["newest_event_action"] == "revoke" and ex["unrevoked_grant_count"] == 1
    assert ex["source_active"] is True and ex["reader_result"] == "unverified" and ex["inventory_complete"] is True


def test_truncation_keeps_full_ledger_facts(mod):
    r = Rig(mod, ledger=A_LEDGER)
    out = r.service().inspect(7, "k", 1)
    inv = out["inventory"]
    assert inv["returned"] == 1 and inv["truncated"] is True and inv["inventory_complete"] is False
    assert inv["ledger_total"] == 3 and out["ledger_total"] == 3 and out["newest_event"]["ordinal"] == 3
    assert out["trust_explanation"]["inventory_complete"] is False


def test_matches_current_only_for_newest_verified_grant(mod):
    r = Rig(mod, reader="verified_trusted", ledger=(("grant", None), ("grant", None)))
    ev = r.service().inspect(7, "k", 20)["inventory"]["events"]
    assert [e["matches_current"] for e in ev] == ["verified_by_reader", "not_evaluated"]
    assert r.service().inspect(7, "k", 20)["trust_explanation"]["situations"] == ["effective"]
    r2 = Rig(mod, reader="unverified", ledger=(("grant", None),))
    assert r2.service().inspect(7, "k", 20)["inventory"]["events"][0]["matches_current"] == "not_evaluated"


@pytest.mark.parametrize("src,ledger,expect", [
    (("active", None), (), ["no_ledger_events"]),
    (("revoked", None), (("grant", None),), ["source_not_active"]),
    (("active", None), (("grant", None),), ["newest_grant_unrevoked_reader_unverified"]),
    (("active", None), (("grant", None), ("revoke", 1)), ["newest_event_is_revoke"]),
])
def test_situation_codes(mod, src, ledger, expect):
    assert Rig(mod, source=src, ledger=ledger).service().inspect(7, "k", 5)["trust_explanation"]["situations"] == expect


def test_label_truncated_and_not_evidence(mod):
    out = Rig(mod, source=("a" * 90, "L" * 90)).service().status(7, "k")
    assert len(out["declared_authority_level"]) == 64 and len(out["source_status"]) == 64
    assert out["label_is_evidence"] is False and out["effective_trust"] == "unverified"
    assert Rig(mod, source=("active", None)).service().status(7, "k")["declared_authority_level"] is None


def test_reader_value_is_verbatim_or_fails_closed(mod):
    assert Rig(mod, reader="verified_trusted").service().status(7, "k")["effective_trust"] == "verified_trusted"
    with pytest.raises(RuntimeError):
        Rig(mod, reader="trusted").service().status(7, "k")


def test_isolation_no_project_or_physical_ids_in_output(mod):
    r = Rig(mod, ledger=A_LEDGER)
    for out in (r.service().status(SENTINEL_PID, "k"), r.service().inspect(SENTINEL_PID, "k", 20)):
        flat = list(walk(out))
        assert not {"project_id", "project_key", "project_name", "id", "supersedes_event_id"} & set(
            x for x in flat if isinstance(x, str))
        assert SENTINEL_PID not in flat and SENTINEL_SID not in flat
        assert str(SENTINEL_PID) not in repr(out) and str(SENTINEL_SID) not in repr(out)


def test_unknown_foreign_company_errors_identical(mod):
    msgs = set()
    for key in ("unknown", "foreign", "company"):
        with pytest.raises(ValueError) as ei:
            Rig(mod, source=None).service().status(7, key)
        msgs.add(str(ei.value))
    assert msgs == {"source not found in the current project"}


# ---- inventory fail-closed (L9) -------------------------------------------------------------------------------
def _corrupt(mod, patch):
    r = Rig(mod, ledger=A_LEDGER)
    orig = r.respond

    def respond(sql, params):
        rows = orig(sql, params)
        return patch(sql, rows) if sql == mod._S4 else rows
    r.respond = respond
    with pytest.raises(RuntimeError, match="source trust inventory inconsistent") as ei:
        r.service().inspect(7, "k", 20)
    assert "STE-" not in str(ei.value)


def test_l9_fail_closed_cases(mod):
    def no_target(sql, rows):
        for x in rows:
            if x["action"] == "revoke":
                x["revokes_event_key"] = x["target_action"] = x["target_ordinal"] = None
        return rows

    def grant_with_target(sql, rows):
        rows[1]["has_supersedes"] = True
        return rows

    def target_not_grant(sql, rows):
        rows[0]["target_action"] = "revoke"
        return rows

    def target_not_lower(sql, rows):
        rows[0]["target_ordinal"] = 3
        return rows

    def double_revoke(sql, rows):
        rows[2]["superseding_count"] = 2
        return rows

    def dup_ordinal(sql, rows):
        rows[1]["ordinal"] = 3
        return rows

    def total_drift(sql, rows):
        rows[0]["ledger_total"] = 4
        return rows

    def newest_drift(sql, rows):
        rows[0]["event_key"] = "STE-" + "f" * 32
        return rows

    for p in (no_target, grant_with_target, target_not_grant, target_not_lower, double_revoke, dup_ordinal,
              total_drift, newest_drift):
        _corrupt(mod, p)


# ---- authority (X1-X3) ----------------------------------------------------------------------------------------
def test_x1_service_module_has_no_write_authority(mod):
    src = Path(inspect.getsourcefile(mod)).read_text(encoding="utf-8")
    for banned in ("record_source_trust_decision", "source_trust_digests", "migrator", "owner", "hashlib",
                   "database_boundary", "user_event_id", "approval_key", "authority_level=", "sha256", "INSERT",
                   "UPDATE ", "DELETE"):
        assert banned not in src, banned
    tree = ast.parse(src)
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    imported |= {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert not {m for m in imported if m and ("boundary" in m or "hashlib" in m or "source_revocation" in m)}
    for fn in (mod.SourceTrustReadService.status, mod.SourceTrustReadService.inspect):
        names = set(inspect.signature(fn).parameters)
        assert not names & {"user_event_id", "approval_key", "authority_level", "task_key"}


def test_x3_public_names(mod):
    public = {n for n in dir(mod) if not n.startswith("_") and getattr(getattr(mod, n), "__module__", None) == mod.__name__}
    assert public == {"SourceTrustReadService"}
    methods = {n for n in dir(mod.SourceTrustReadService) if not n.startswith("_")}
    assert methods == {"status", "inspect", "validate_source_key", "validate_limit"}


def test_x4_g1_every_response(mod):
    r = Rig(mod, ledger=A_LEDGER)
    for out in (r.service().status(7, "k"), r.service().inspect(7, "k", 3)):
        assert out["host_authenticated"] is False and out["g8"] == "open"
        assert out["attestation_class"] == ATTESTATION
        assert out["mutation"] == {"available": False, "reason": "g8_host_ingress_open"}
        text = repr(out)
        assert "executed': True" not in text and "recovered" not in text


def test_determinism(mod):
    r = Rig(mod, ledger=A_LEDGER)
    assert r.service().inspect(7, "k", 20) == r.service().inspect(7, "k", 20)
