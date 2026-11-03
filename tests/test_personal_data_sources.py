"""No database, Credential Locker or local-user profile. Pure synthetic metadata only."""
from __future__ import annotations

import ast
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from vres_os.personal_data_sources import DataSourceRefused, PersonalDataSources

NAMESPACE = "a" * 64
ANOTHER_USER = "b" * 64
CREDENTIAL = "credential-" + "a" * 32
ORIGIN = "example.gr:5432/vres_app"
A, B, C = ("project:" + letter * 24 for letter in "abc")


def _lookup(credential_id):
    if credential_id != CREDENTIAL:
        raise KeyError("not in Credential Broker")
    return SimpleNamespace(resource_id=CREDENTIAL, service_type="postgres", origin=ORIGIN)


def _registry():
    return PersonalDataSources(NAMESPACE, _lookup)


def _linked():
    catalog = _registry()
    sid = catalog.register_postgres(ORIGIN, CREDENTIAL, authorized=True)
    catalog.bind(sid, A, authorized=True)
    return catalog, sid


def _schema():
    return {"objects": [
        {"schema": "public", "name": "customers", "kind": "table",
         "columns": [{"name": "id", "type": "integer", "nullable": False},
                     {"name": "name", "type": "character varying(255)", "nullable": True}],
         "primary_key": ["id"], "foreign_keys": []},
        {"schema": "public", "name": "orders", "kind": "table",
         "columns": [{"name": "id", "type": "integer", "nullable": False},
                     {"name": "customer_id", "type": "integer", "nullable": False}],
         "primary_key": ["id"], "foreign_keys": [
             {"columns": ["customer_id"], "ref_schema": "public", "ref_object": "customers",
              "ref_columns": ["id"]}]},
    ]}


def test_create_serialize_reload_idempotent_and_empty():
    a = _registry()
    data = a.to_document()
    assert b"postgres" not in data and b"password" not in data
    b = PersonalDataSources(NAMESPACE, _lookup, document=data)
    assert b.to_document() == data
    assert json.loads(data)["revision"] == 0


def test_register_never_implicitly_binds_and_requires_real_metadata():
    a = _registry()
    with pytest.raises(DataSourceRefused, match="explicit"):
        a.register_postgres(ORIGIN, CREDENTIAL, authorized=False)
    sid = a.register_postgres(ORIGIN, CREDENTIAL, authorized=True)
    assert sid.startswith("data-source-")
    assert a.register_postgres(ORIGIN, CREDENTIAL, authorized=True) == sid
    with pytest.raises(DataSourceRefused, match="explicit project binding"):
        a.summary_for(sid, A)
    assert json.loads(a.to_document())["revision"] == 1


@pytest.mark.parametrize("origin", [
    "postgresql://user:secret@example.gr:5432/vres_app", "example.gr/vres_app",
    "example.gr:0/vres_app", "example.gr:65536/vres_app", "example.gr:5432/vres_app?x=1",
    "example.gr:5432/vres_app#x", "user@example.gr:5432/vres_app",
    "EXAMPLE.GR:5432/VRES_APP", "example.gr:5432/vres_app\nSECRET=abc",
])
def test_unsafe_or_noncanonical_origins_refuse_without_credential_lookup(origin):
    calls = []
    a = PersonalDataSources(NAMESPACE, lambda rid: calls.append(rid))
    with pytest.raises(DataSourceRefused):
        a.register_postgres(origin, CREDENTIAL, authorized=True)
    assert calls == [] and json.loads(a.to_document())["revision"] == 0


@pytest.mark.parametrize("service,origin,rid", [
    ("website", ORIGIN, CREDENTIAL), ("postgres", "elsewhere.gr:5432/vres_app", CREDENTIAL),
    ("postgres", ORIGIN, "credential-" + "b" * 32),
])
def test_credential_metadata_identity_must_match(service, origin, rid):
    a = PersonalDataSources(NAMESPACE, lambda _: SimpleNamespace(service_type=service, origin=origin, resource_id=rid))
    with pytest.raises(DataSourceRefused, match="Credential resource"):
        a.register_postgres(ORIGIN, CREDENTIAL, authorized=True)
    assert json.loads(a.to_document())["revision"] == 0


def test_unknown_credential_broker_handle_fail_closed():
    a = PersonalDataSources(NAMESPACE, lambda _: (_ for _ in ()).throw(KeyError("absent")))
    with pytest.raises(DataSourceRefused, match="could not be verified"):
        a.register_postgres(ORIGIN, CREDENTIAL, authorized=True)


def test_two_project_reuse_only_by_two_explicit_bindings_and_c_denied():
    a, sid = _linked()
    for key in (B, C):
        with pytest.raises(DataSourceRefused, match="explicit project binding"):
            a.summary_for(sid, key)
    assert a.summary_for(sid, A)["credential_resource_id"] == CREDENTIAL
    with pytest.raises(DataSourceRefused, match="explicit"):
        a.bind(sid, B, authorized=False)
    assert a.bind(sid, B, authorized=True) is True
    assert a.bind(sid, B, authorized=True) is False
    assert a.summary_for(sid, B)["origin"] == ORIGIN
    with pytest.raises(DataSourceRefused):
        a.summary_for(sid, C)
    assert a.unlink(sid, A, authorized=True) is True
    assert a.unlink(sid, A, authorized=True) is False
    with pytest.raises(DataSourceRefused):
        a.summary_for(sid, A)
    assert a.summary_for(sid, B)["engine"] == "postgres"


def test_reloading_document_keeps_a_b_bindings_and_never_grants_c():
    a, sid = _linked()
    a.bind(sid, B, authorized=True)
    recovered = PersonalDataSources(NAMESPACE, _lookup, document=a.to_document())
    assert recovered.summary_for(sid, A)["origin"] == ORIGIN
    assert recovered.summary_for(sid, B)["origin"] == ORIGIN
    with pytest.raises(DataSourceRefused):
        recovered.summary_for(sid, C)


def test_caller_supplied_catalog_has_no_verified_db_claim_and_is_reusable_after_binding():
    a, sid = _linked()
    candidate = _schema()
    preview = a.preview_schema(sid, A, candidate)
    assert preview["status"] == "NOT_CATALOGUED" and preview["current_fingerprint"] is None
    assert preview["assurance"] == "caller_supplied_unverified"
    with pytest.raises(DataSourceRefused, match="review and authorization"):
        a.accept_schema(sid, A, candidate, expected_current_fingerprint=None,
                        reviewed=False, authorized=True)
    assert a.accept_schema(sid, A, candidate, expected_current_fingerprint=None,
                           reviewed=True, authorized=True)
    assert a.catalog_for(sid, A)["status"] == "AVAILABLE_UNVERIFIED"
    assert a.catalog_for(sid, A)["assurance"] == "caller_supplied_unverified"
    assert a.preview_schema(sid, A, candidate)["status"] == "UNCHANGED"
    assert a.accept_schema(sid, A, candidate, expected_current_fingerprint=preview["candidate_fingerprint"],
                           reviewed=True, authorized=True) is False
    a.bind(sid, B, authorized=True)
    assert a.catalog_for(sid, B)["fingerprint"] == preview["candidate_fingerprint"]
    with pytest.raises(DataSourceRefused):
        a.catalog_for(sid, C)
    restored = PersonalDataSources(NAMESPACE, _lookup, document=a.to_document())
    assert restored.catalog_for(sid, B)["schema"]["objects"][1]["name"] == "orders"


def test_catalog_is_returned_as_independent_copy():
    a, sid = _linked()
    a.accept_schema(sid, A, _schema(), expected_current_fingerprint=None,
                    authorized=True, reviewed=True)
    old = a.to_document()
    a.catalog_for(sid, A)["schema"]["objects"].clear()
    assert a.to_document() == old


def test_reordered_metadata_has_stable_canonical_fingerprint():
    a, sid = _linked()
    x = _schema()
    y = deepcopy(x)
    y["objects"].reverse()
    for obj in y["objects"]:
        obj["columns"].reverse()
    assert a.preview_schema(sid, A, x)["candidate_fingerprint"] == a.preview_schema(sid, A, y)["candidate_fingerprint"]


def test_drift_preview_requires_exact_prior_fingerprint_and_review():
    a, sid = _linked()
    x = _schema()
    a.accept_schema(sid, A, x, expected_current_fingerprint=None, authorized=True, reviewed=True)
    old = a.catalog_for(sid, A)["fingerprint"]
    y = _schema()
    y["objects"][0]["columns"].append({"name": "email", "type": "text", "nullable": True})
    p = a.preview_schema(sid, A, y)
    assert p["status"] == "DRIFT_REVIEW_REQUIRED" and p["current_fingerprint"] == old
    snapshot = a.to_document()
    with pytest.raises(DataSourceRefused, match="stale acceptance"):
        a.accept_schema(sid, A, y, expected_current_fingerprint=None, authorized=True, reviewed=True)
    assert a.to_document() == snapshot
    assert a.accept_schema(sid, A, y, expected_current_fingerprint=old, authorized=True, reviewed=True)
    assert a.catalog_for(sid, A)["fingerprint"] == p["candidate_fingerprint"]


@pytest.mark.parametrize("mutation", [
    lambda v: v.update({"sample_value": "private"}),
    lambda v: v["objects"][0].update({"sql": "SELECT password FROM users"}),
    lambda v: v["objects"][0]["columns"][0].update({"sample": "abc"}),
    lambda v: v["objects"][0].update({"name": "DROP TABLE users;--"}),
    lambda v: v["objects"][0]["columns"][0].update({"type": "text; DROP TABLE accounts"}),
    lambda v: v["objects"].append(deepcopy(v["objects"][0])),
    lambda v: v["objects"][0]["columns"].append(deepcopy(v["objects"][0]["columns"][0])),
    lambda v: v["objects"][1]["foreign_keys"][0].update({"ref_object": "missing"}),
    lambda v: v["objects"][1]["foreign_keys"][0].update({"ref_columns": ["unknown"]}),
    lambda v: v["objects"][0].update({"kind": ["table"]}),
    lambda v: v["objects"][1]["foreign_keys"][0].update({"columns": [["customer_id"]]}),
])
def test_structural_schema_rejects_untrusted_extra_fields_and_invalid_edges(mutation):
    a, sid = _linked()
    x = _schema()
    mutation(x)
    before = a.to_document()
    with pytest.raises(DataSourceRefused):
        a.preview_schema(sid, A, x)
    assert a.to_document() == before


def test_schema_object_budget_and_document_size_refuse_without_mutation():
    a, sid = _linked()
    many = {"objects": []}
    for index in range(129):
        obj = deepcopy(_schema()["objects"][0])
        obj["name"] = f"table_{index}"
        many["objects"].append(obj)
    with pytest.raises(DataSourceRefused, match="budget"):
        a.preview_schema(sid, A, many)
    assert json.loads(a.to_document())["revision"] == 2


@pytest.mark.parametrize("wrong", [
    lambda d: d.update({"user_namespace": ANOTHER_USER}),
    lambda d: d.update({"version": True}),
    lambda d: d.update({"secret": "no"}),
    lambda d: d["bindings"].update({C: ["data-source-" + "f" * 32]}),
    lambda d: d["sources"].update({"data-source-" + "f" * 32: {"engine": "postgres"}}),
    lambda d: d["bindings"].update({A: [["not an id"]]}),
])
def test_malformed_persisted_document_fail_closed(wrong):
    a, _ = _linked()
    payload = json.loads(a.to_document())
    wrong(payload)
    with pytest.raises(DataSourceRefused):
        PersonalDataSources(NAMESPACE, _lookup, document=json.dumps(payload).encode())


def test_duplicate_json_keys_and_nonfinite_json_refuse():
    for payload in (b'{"version":1,"version":1}', b'{"x":NaN}'):
        with pytest.raises(DataSourceRefused):
            PersonalDataSources(NAMESPACE, _lookup, document=payload)


def test_altered_snapshot_fingerprint_and_assurance_refuse():
    a, sid = _linked()
    a.accept_schema(sid, A, _schema(), expected_current_fingerprint=None, authorized=True, reviewed=True)
    for change in ("assurance", "fingerprint"):
        body = json.loads(a.to_document())
        row = body["sources"][sid]["snapshot"]
        row[change] = "verified_direct_db" if change == "assurance" else "f" * 64
        with pytest.raises(DataSourceRefused):
            PersonalDataSources(NAMESPACE, _lookup, document=json.dumps(body).encode())


def test_wrong_user_namespace_rejects_cross_user_document():
    a, sid = _linked()
    with pytest.raises(DataSourceRefused, match="scope"):
        PersonalDataSources(ANOTHER_USER, _lookup, document=a.to_document())


def test_failed_mutation_does_not_corrupt_active_document():
    a, sid = _linked()
    before = a.to_document()
    with pytest.raises(DataSourceRefused):
        a.accept_schema(sid, A, _schema(), expected_current_fingerprint=None,
                        authorized=False, reviewed=True)
    assert before == a.to_document()
    with pytest.raises(DataSourceRefused):
        a.bind(sid, "project:bad", authorized=True)
    assert before == a.to_document()


def test_module_has_no_database_network_credential_or_file_io_surface():
    path = Path(__file__).resolve().parents[1] / "vres_os" / "personal_data_sources.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    imports.extend(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
    assert all(n.split(".")[0] in {"__future__", "hashlib", "json", "re", "copy", "typing"} for n in imports)
    text = path.read_text(encoding="utf-8")
    for forbidden in ("psycopg", "subprocess", "socket", "SecretStore(", "open(", "requests", "connect("):
        assert forbidden not in text
