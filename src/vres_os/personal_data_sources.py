"""Pure offline current-user PostgreSQL data-source and schema-metadata catalog.

No connection, SQL, credential value, filesystem, or user-profile operation is present.
A caller must supply a real current-user CredentialBroker.lookup-like *metadata*
callback and explicitly persist returned document bytes through an approved adapter.
Caller-supplied schema is NOT verified database evidence or permission to query.
"""
from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any, Callable


class DataSourceRefused(ValueError):
    """No catalog or project authorization claim may be inferred on refusal."""


_FORMAT = "vres-personal-offline-data-sources"
_VERSION = 1
_NAMESPACE = re.compile(r"[0-9a-f]{64}\Z")
_CREDENTIAL = re.compile(r"credential-[0-9a-f]{32}\Z")
_PROJECT = re.compile(r"project:[0-9a-f]{24}\Z")
_SOURCE = re.compile(r"data-source-[0-9a-f]{32}\Z")
_IDENTIFIER = re.compile(r"[^\W\d][\w$]{0,62}\Z", re.UNICODE)
_TYPE = re.compile(r"[A-Za-z_][A-Za-z0-9_. ,()\[\]]{0,79}\Z")
_ORIGIN = re.compile(r"(?:\[[0-9a-f:.]+\]|[a-z0-9][a-z0-9.-]{0,252}):([0-9]{1,5})/([a-z0-9_.-]{1,128})\Z")
_KINDS = frozenset({"table", "view", "materialized_view", "foreign_table"})
_MAX_BYTES = 512 * 1024
_MAX_OBJECTS = 128
_MAX_COLS = 64


def _reject(reason: str) -> None:
    raise DataSourceRefused(reason)


def _required_str(value: Any, pattern: re.Pattern[str], label: str) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        _reject(f"Invalid {label}; no data source was authorized")
    return value


def _origin(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 400 or value != value.casefold():
        _reject("Database origin must be canonical credential metadata without a DSN or password")
    match = _ORIGIN.fullmatch(value)
    if not match or not (1 <= int(match.group(1)) <= 65535):
        _reject("Database origin must be a canonical host:port/database without credentials")
    return value


def _object_name(value: Any) -> str:
    return _required_str(value, _IDENTIFIER, "structural identifier")


def _schema(raw: Any) -> dict[str, Any]:
    """Strictly structural only; never store SQL, comments, row data or freeform text."""
    if not isinstance(raw, dict) or set(raw) != {"objects"} or not isinstance(raw["objects"], list):
        _reject("Structural snapshot must contain only an objects list")
    if len(raw["objects"]) > _MAX_OBJECTS:
        _reject("Structural snapshot exceeds the object budget")
    objects: dict[tuple[str, str], dict[str, Any]] = {}
    for item in raw["objects"]:
        keys = {"schema", "name", "kind", "columns", "primary_key", "foreign_keys"}
        if not isinstance(item, dict) or set(item) != keys:
            _reject("Structural objects must have only the approved metadata fields")
        schema, name = _object_name(item["schema"]), _object_name(item["name"])
        if not isinstance(item["kind"], str) or item["kind"] not in _KINDS or not isinstance(item["columns"], list):
            _reject("Structural object kind or columns are invalid")
        if not (1 <= len(item["columns"]) <= _MAX_COLS):
            _reject("Structural object has no columns or exceeds the column budget")
        cols: dict[str, dict[str, Any]] = {}
        for column in item["columns"]:
            if not isinstance(column, dict) or set(column) != {"name", "type", "nullable"}:
                _reject("Columns may contain only name, type and nullable")
            colname = _object_name(column["name"])
            if (not isinstance(column["type"], str) or not _TYPE.fullmatch(column["type"])
                    or type(column["nullable"]) is not bool or colname in cols):
                _reject("Column contains invalid or duplicate structural metadata")
            cols[colname] = {"name": colname, "type": column["type"], "nullable": column["nullable"]}
        if not isinstance(item["primary_key"], list) or any(not isinstance(x, str) for x in item["primary_key"]):
            _reject("Primary key must be a list of column names")
        pk = list(item["primary_key"])
        if len(pk) != len(set(pk)) or any(x not in cols for x in pk):
            _reject("Primary key references missing or repeated columns")
        fks: list[dict[str, Any]] = []
        if not isinstance(item["foreign_keys"], list) or len(item["foreign_keys"]) > 32:
            _reject("Foreign-key metadata exceeds bounds")
        for fk in item["foreign_keys"]:
            if not isinstance(fk, dict) or set(fk) != {"columns", "ref_schema", "ref_object", "ref_columns"}:
                _reject("Foreign key must be structural; no SQL or values are allowed")
            left, right = fk["columns"], fk["ref_columns"]
            if (not isinstance(left, list) or not isinstance(right, list) or
                    not 1 <= len(left) == len(right) <= 16 or
                    any(not isinstance(c, str) or c not in cols for c in left) or
                    any(not isinstance(c, str) for c in right) or
                    len(set(left)) != len(left) or len(set(right)) != len(right)):
                _reject("Foreign key columns are invalid")
            fks.append({"columns": list(left), "ref_schema": _object_name(fk["ref_schema"]),
                        "ref_object": _object_name(fk["ref_object"]),
                        "ref_columns": [_object_name(x) for x in right]})
        key = (schema, name)
        if key in objects:
            _reject("Duplicate schema object")
        objects[key] = {"schema": schema, "name": name, "kind": item["kind"],
                        "columns": [cols[c] for c in sorted(cols)], "primary_key": pk,
                        "foreign_keys": sorted(fks, key=lambda v: json.dumps(v, sort_keys=True))}
    for entry in objects.values():
        for fk in entry["foreign_keys"]:
            referenced = objects.get((fk["ref_schema"], fk["ref_object"]))
            if referenced is None:
                _reject("Foreign key references an object outside this bounded snapshot")
            columns = {c["name"] for c in referenced["columns"]}
            if any(c not in columns for c in fk["ref_columns"]):
                _reject("Foreign key references unknown target columns")
    return {"objects": [objects[k] for k in sorted(objects)]}


def _encode(value: dict[str, Any]) -> bytes:
    data = (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                       separators=(",", ":")) + "\n").encode("utf-8")
    if len(data) > _MAX_BYTES:
        _reject("Catalog exceeds the maximum document size")
    return data


def _fingerprint(value: dict[str, Any]) -> str:
    return hashlib.sha256(_encode(value)).hexdigest()


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            _reject("Duplicate JSON key in catalog")
        obj[key] = value
    return obj


def _load(raw: bytes, namespace: str) -> dict[str, Any]:
    if not isinstance(raw, bytes) or not 0 < len(raw) <= _MAX_BYTES:
        _reject("Catalog bytes are missing or oversized")
    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicates,
                         parse_constant=lambda _: _reject("Nonfinite JSON value refused"))
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise DataSourceRefused("Catalog JSON is unreadable or malformed") from exc
    if (not isinstance(obj, dict) or set(obj) != {"format", "version", "user_namespace", "revision", "sources", "bindings"}
            or obj["format"] != _FORMAT or type(obj["version"]) is not int or obj["version"] != _VERSION
            or obj["user_namespace"] != namespace or type(obj["revision"]) is not int
            or not 0 <= obj["revision"] <= 1000000 or
            not isinstance(obj["sources"], dict) or len(obj["sources"]) > 32 or
            not isinstance(obj["bindings"], dict) or len(obj["bindings"]) > 64):
        _reject("Catalog version, current-user scope or shape is invalid")
    for sid, source in obj["sources"].items():
        if (not isinstance(source, dict) or set(source) != {"engine", "origin", "credential_resource_id", "snapshot"}
                or source["engine"] != "postgres"):
            _reject("Data-source record is malformed")
        origin, cred = _origin(source["origin"]), _required_str(source["credential_resource_id"], _CREDENTIAL, "credential handle")
        if sid != _source_id(namespace, origin, cred):
            _reject("Data-source identity does not match its canonical credential resource")
        snapshot = source["snapshot"]
        if snapshot is not None:
            if (not isinstance(snapshot, dict) or set(snapshot) != {"assurance", "fingerprint", "schema"}
                    or snapshot["assurance"] != "caller_supplied_unverified"):
                _reject("Unsupported schema evidence claim")
            schema = _schema(snapshot["schema"])
            if schema != snapshot["schema"] or snapshot["fingerprint"] != _fingerprint(schema):
                _reject("Stored schema fingerprint or canonical structure is invalid")
    for project, links in obj["bindings"].items():
        _required_str(project, _PROJECT, "project key")
        if (not isinstance(links, list) or any(not isinstance(sid, str) for sid in links)
                or sorted(set(links)) != links or any(sid not in obj["sources"] for sid in links)):
            _reject("Project binding is malformed or refers to a missing source")
    return obj


def _source_id(namespace: str, origin: str, credential_id: str) -> str:
    return "data-source-" + hashlib.sha256((namespace + "\0postgres\0" + origin + "\0" + credential_id).encode()).hexdigest()[:32]


class PersonalDataSources:
    """Offline document owner. Mutations require consent and persist nowhere automatically."""

    def __init__(self, namespace: str, credential_metadata_lookup: Callable[[str], Any], document: bytes | None = None):
        self.namespace = _required_str(namespace, _NAMESPACE, "current-user namespace")
        if not callable(credential_metadata_lookup):
            _reject("A Credential Broker metadata lookup callback is required")
        self._lookup = credential_metadata_lookup
        if document is None:
            self._state: dict[str, Any] = {"format": _FORMAT, "version": _VERSION,
                                          "user_namespace": namespace, "revision": 0,
                                          "sources": {}, "bindings": {}}
        else:
            self._state = _load(document, namespace)

    def to_document(self) -> bytes:
        return _encode(self._state)

    def _finish(self, next_state: dict[str, Any]) -> None:
        """Atomic in-memory CAS-like transition: refusal never corrupts current state."""
        next_state["revision"] = self._state["revision"] + 1
        _load(_encode(next_state), self.namespace)
        self._state = next_state

    def register_postgres(self, origin: str, credential_id: str, *, authorized: bool) -> str:
        if authorized is not True:
            _reject("Registering a data source requires explicit current-user authorization")
        origin = _origin(origin)
        credential_id = _required_str(credential_id, _CREDENTIAL, "credential handle")
        try:
            metadata = self._lookup(credential_id)
        except Exception as exc:
            raise DataSourceRefused("Credential resource metadata could not be verified") from exc
        if (getattr(metadata, "resource_id", None) != credential_id or
                getattr(metadata, "service_type", None) != "postgres" or
                getattr(metadata, "origin", None) != origin):
            _reject("Credential resource does not match this PostgreSQL service identity")
        sid = _source_id(self.namespace, origin, credential_id)
        if sid in self._state["sources"]:
            return sid
        if len(self._state["sources"]) >= 32:
            _reject("Data-source budget exceeded")
        next_state = deepcopy(self._state)
        next_state["sources"][sid] = {"engine": "postgres", "origin": origin,
                                       "credential_resource_id": credential_id, "snapshot": None}
        self._finish(next_state)
        return sid

    def bind(self, source_id: str, project_key: str, *, authorized: bool) -> bool:
        if authorized is not True:
            _reject("Project data-source linking requires explicit current-user authorization")
        _required_str(project_key, _PROJECT, "project key")
        if source_id not in self._state["sources"]:
            _reject("Data source is not registered")
        existing = self._state["bindings"].get(project_key, [])
        if source_id in existing:
            return False
        if len(self._state["bindings"]) >= 64 and project_key not in self._state["bindings"]:
            _reject("Project binding budget exceeded")
        next_state = deepcopy(self._state)
        next_state["bindings"][project_key] = sorted([*existing, source_id])
        self._finish(next_state)
        return True

    def unlink(self, source_id: str, project_key: str, *, authorized: bool) -> bool:
        if authorized is not True:
            _reject("Project data-source unlink requires explicit current-user authorization")
        _required_str(project_key, _PROJECT, "project key")
        existing = self._state["bindings"].get(project_key, [])
        if source_id not in existing:
            return False
        left = [s for s in existing if s != source_id]
        next_state = deepcopy(self._state)
        if left:
            next_state["bindings"][project_key] = left
        else:
            next_state["bindings"].pop(project_key, None)
        self._finish(next_state)
        return True

    def _bound(self, source_id: str, project_key: str) -> dict[str, Any]:
        _required_str(project_key, _PROJECT, "project key")
        source = self._state["sources"].get(source_id)
        if source is None or source_id not in self._state["bindings"].get(project_key, []):
            _reject("Data-source metadata requires an explicit project binding")
        return source

    def preview_schema(self, source_id: str, project_key: str, candidate: dict[str, Any]) -> dict[str, Any]:
        source = self._bound(source_id, project_key)
        schema = _schema(candidate)
        digest = _fingerprint(schema)
        current = source["snapshot"]
        previous = current["fingerprint"] if current is not None else None
        return {"status": "NOT_CATALOGUED" if previous is None else
                ("UNCHANGED" if previous == digest else "DRIFT_REVIEW_REQUIRED"),
                "candidate_fingerprint": digest, "current_fingerprint": previous,
                "assurance": "caller_supplied_unverified"}

    def accept_schema(self, source_id: str, project_key: str, candidate: dict[str, Any], *,
                      expected_current_fingerprint: str | None, authorized: bool, reviewed: bool) -> bool:
        if authorized is not True or reviewed is not True:
            _reject("Structural metadata needs explicit current-user review and authorization")
        source = self._bound(source_id, project_key)
        preview = self.preview_schema(source_id, project_key, candidate)
        if expected_current_fingerprint != preview["current_fingerprint"]:
            _reject("Catalog snapshot changed since review; stale acceptance refused")
        if preview["status"] == "UNCHANGED":
            return False
        schema = _schema(candidate)
        next_state = deepcopy(self._state)
        next_state["sources"][source_id]["snapshot"] = {
            "assurance": "caller_supplied_unverified",
            "fingerprint": preview["candidate_fingerprint"], "schema": schema,
        }
        self._finish(next_state)
        return True

    def catalog_for(self, source_id: str, project_key: str) -> dict[str, Any]:
        source = self._bound(source_id, project_key)
        if source["snapshot"] is None:
            return {"status": "NOT_CATALOGUED", "assurance": "none", "schema": None}
        return {"status": "AVAILABLE_UNVERIFIED", **deepcopy(source["snapshot"])}

    def summary_for(self, source_id: str, project_key: str) -> dict[str, Any]:
        source = self._bound(source_id, project_key)
        return {"engine": source["engine"], "origin": source["origin"],
                "credential_resource_id": source["credential_resource_id"],
                "snapshot_fingerprint": None if source["snapshot"] is None else source["snapshot"]["fingerprint"],
                "assurance": "none" if source["snapshot"] is None else "caller_supplied_unverified"}
