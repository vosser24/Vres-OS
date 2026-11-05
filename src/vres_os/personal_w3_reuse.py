"""W3: synthetic-only composition of existing #163 broker and #176 E5 memory.

No registry, database, vault, project or agent writes. This is a bounded
read-only preview, NOT an authorization to resolve credentials, query a data
source, promote memory, activate Claude or issue independent Fable approval.
Only explicitly supplied synthetic owner instances/metadata are accepted.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .credential_broker import CredentialResource, CredentialBroker
from .personal_project_intake import PersonalIntakeRefused, _plain_project_root
from .sensitive_policy import sanitize_extracted_text

SCHEMA = "vres-personal-w3-reuse-preview/1"
E5_SCHEMA = "176.e5.v1"
SOURCE_SCHEMA = "vres-w3-synthetic-data-source-metadata/1"
_SECTIONS = (
    "current_decisions", "accepted_procedures", "validated_lessons", "candidate_lessons",
    "conflicts_and_stale", "precedent_episodes", "low_trust_observations", "raw_evidence_refs",
)
_REUSABLE = ("current_decisions", "accepted_procedures", "validated_lessons")
_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@/-]{0,127}$")
_HEX = re.compile(r"^[0-9a-f]{64}$")
_INJECTION = re.compile(
    r"(?i)(?:\b(?:ignore|disregard|bypass|override)\s+(?:all\s+|the\s+|prior\s+|previous\s+)?"
    r"(?:instructions?|rules|prompts?|polic(?:y|ies)|guards?|approvals?)\b|"
    r"\b(?:reveal|send|print|leak|exfiltrate)\s+(?:all\s+|the\s+|your\s+)?"
    r"(?:secrets?|passwords?|tokens?|credentials?|api[ -]?keys?)\b|"
    r"\byou\s+(?:must|should|will)\s+(?:always|never|now)\b|system prompt)"
)
_MAX_PACKET = 14_000


class PersonalW3Refusal(ValueError):
    """Refused unsafe reuse; error messages never echo input values."""


def _canonical(value: Any, *, bound: int = 20_000) -> bytes:
    try:
        result = json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                            separators=(",", ":")).encode("ascii")
    except (ValueError, TypeError, OverflowError, UnicodeError, RecursionError) as exc:
        raise PersonalW3Refusal("Unbounded or invalid preview structure") from exc
    if len(result) > bound:
        raise PersonalW3Refusal("Preview material exceeds the bounded limit")
    return result


def _key(value: Any) -> bool:
    return type(value) is str and bool(_KEY.fullmatch(value))


def _sha(value: Any) -> bool:
    return type(value) is str and bool(_HEX.fullmatch(value))


def _scope(project: Any, project_id: Any, broker: Any) -> tuple[Path, str, str]:
    if type(project_id) is not int or project_id <= 0 or not _key(getattr(project, "key", None)):
        raise PersonalW3Refusal("Explicit project scope and positive owner project ID required")
    try:
        root = _plain_project_root(project.root)
    except (PersonalIntakeRefused, AttributeError, TypeError, OSError, ValueError) as exc:
        raise PersonalW3Refusal("Selected project root is redirected or invalid") from exc
    if type(broker) is not CredentialBroker:
        raise PersonalW3Refusal("Expected the established credential owner")
    namespace = broker.user_namespace
    # This increment deliberately forbids real current-user or profile use.
    if type(namespace) is not str or not namespace.startswith("synthetic-") or not _key(namespace):
        raise PersonalW3Refusal("W3 is restricted to explicit synthetic user namespaces")
    return root, project.key, namespace


def _memories(pack: Any, project_id: int) -> list[dict[str, Any]]:
    if type(pack) is not dict or pack.get("schema_version") != E5_SCHEMA or type(pack.get("policy")) is not dict:
        raise PersonalW3Refusal("Expected existing E5 owner-shaped retrieval pack")
    if pack["policy"].get("version") != E5_SCHEMA or type(pack.get("abstained")) is not bool:
        raise PersonalW3Refusal("E5 policy or abstention invalid")
    if any(type(pack.get(section)) is not list for section in _SECTIONS):
        raise PersonalW3Refusal("E5 sections must be bounded lists")
    if sum(len(pack[s]) for s in _SECTIONS) > 24 or len(_canonical(pack, bound=16_384)) > 16_384:
        raise PersonalW3Refusal("E5 retrieval pack exceeds the original bounded policy")
    if pack["abstained"] != (not any(pack[s] for s in _SECTIONS)):
        raise PersonalW3Refusal("E5 abstention inconsistent with emitted sections")
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for section in _REUSABLE:
        for item in pack[section]:
            if type(item) is not dict or not _key(item.get("memory_key")):
                raise PersonalW3Refusal("Malformed memory item")
            key = item["memory_key"]
            if key in seen:
                raise PersonalW3Refusal("Duplicated memory identity")
            seen.add(key)
            if (type(item.get("project_id")) is not int or item["project_id"] != project_id
                    or item.get("scope") != "project"):
                # Do not reveal, reuse or claim cross-project/global memory authority.
                continue
            if item.get("role") != "instruction" or item.get("flags") != []:
                continue  # stale, conflict, revoked, historical, warning: never reused as an instruction.
            ok = (
                (section == "current_decisions" and item.get("memory_class") == "decision"
                 and item.get("status") == "active" and item.get("authority_class") == "decision_current_task")
                or (section == "accepted_procedures" and item.get("memory_class") == "procedural"
                    and item.get("status") == "active" and item.get("authority_class") == "accepted_procedure")
                or (section == "validated_lessons" and item.get("memory_class") == "semantic"
                    and item.get("status") in ("validated", "canonical")
                    and item.get("authority_class") == "validated_or_canonical_knowledge")
            )
            if not ok:
                continue
            applicability = item.get("applicability")
            if type(applicability) is not dict or applicability.get("premise_status") == "mismatch":
                continue
            if applicability.get("premise_mismatches") not in ([], None):
                continue
            evidence = item.get("evidence")
            if (type(evidence) is not list or not 1 <= len(evidence) <= 10
                    or any(not _key(e) for e in evidence)):
                raise PersonalW3Refusal("Missing or malformed source provenance")
            source = item.get("text")
            if type(source) is not str or not 1 <= len(source.strip()) <= 450:
                raise PersonalW3Refusal("Unbounded or empty memory text")
            if _INJECTION.search(source) or sanitize_extracted_text(source).status is not None:
                raise PersonalW3Refusal("Unsafe memory text refused before reuse")
            # Evidence remains a reference, not an approval or privileged instruction.
            output.append({"memory_key": key, "memory_class": item["memory_class"],
                           "excerpt": source.strip(), "source_evidence_keys": sorted(set(evidence)),
                           "scope": "project", "authority_is_not_upgraded": True})
            if len(output) >= 4:
                return output
    return output


def _resources(project: Any, root: Path, broker: CredentialBroker,
               resource_ids: Any) -> list[str]:
    if type(resource_ids) not in (list, tuple) or len(resource_ids) > 8 or len(set(map(str, resource_ids))) != len(resource_ids):
        raise PersonalW3Refusal("Credential ID list invalid")
    if any(not _key(rid) for rid in resource_ids):
        raise PersonalW3Refusal("Credential resource identity invalid")
    # Existing #163 registry reader is read-only and returns metadata only.
    # Its stored path check supplements CredentialResource.bound_to_project.
    registry = broker._read()
    bindings = registry["bindings"].get(project.key)
    if bindings is not None and (type(bindings) is not dict or bindings.get("root") != str(root)):
        raise PersonalW3Refusal("Credential project root does not match its recorded binding")
    approved = []
    for rid in resource_ids:
        # Do not enumerate unbound credential resources in result.
        try:
            resource = broker.lookup(rid, project)
        except Exception as exc:
            raise PersonalW3Refusal("Credential metadata lookup refused") from exc
        if type(resource) is not CredentialResource or resource.resource_id != rid:
            raise PersonalW3Refusal("Credential owner response invalid")
        if resource.bound_to_project is True and bindings is not None and rid in bindings["resources"]:
            approved.append(rid)
    return sorted(approved)


def _data_sources(source_rows: Any, project_key: str, namespace: str,
                  approved_credentials: list[str]) -> list[dict[str, str]]:
    if type(source_rows) is not list or len(source_rows) > 8:
        raise PersonalW3Refusal("Synthetic data-source metadata invalid")
    result: list[dict[str, str]] = []
    names: set[str] = set()
    for record in source_rows:
        if type(record) is not dict or set(record) != {
            "schema", "source_key", "namespace", "project_key", "credential_resource_id",
            "catalog_fingerprint", "observed_fingerprint", "read_only", "synthetic_only",
        }:
            raise PersonalW3Refusal("Source record does not match synthetic metadata contract")
        sid = record["source_key"]
        if not _key(sid) or sid in names:
            raise PersonalW3Refusal("Duplicate or invalid source identity")
        names.add(sid)
        if (record["schema"] != SOURCE_SCHEMA or record["synthetic_only"] is not True
                or record["read_only"] is not True or not _key(record["project_key"])
                or not _key(record["namespace"]) or not _key(record["credential_resource_id"])
                or not _sha(record["catalog_fingerprint"]) or not _sha(record["observed_fingerprint"])):
            raise PersonalW3Refusal("Invalid synthetic source provenance")
        if record["namespace"] != namespace or record["project_key"] != project_key:
            continue  # Other projects/users never surface even as source names.
        if record["catalog_fingerprint"] != record["observed_fingerprint"]:
            raise PersonalW3Refusal("Stale synthetic schema metadata refused")
        if record["credential_resource_id"] not in approved_credentials:
            continue
        result.append({"source_key": sid, "catalog_fingerprint": record["catalog_fingerprint"],
                       "mode": "SYNTHETIC_METADATA_ONLY_NO_DATABASE_CONTACT"})
    return sorted(result, key=lambda r: r["source_key"])


def preview_personal_w3_reuse(project: Any, *, project_id: int, broker: CredentialBroker,
                              experience_pack: Any, resource_ids: list[str],
                              source_metadata: list[dict[str, Any]]) -> dict[str, Any]:
    """Compose one strictly scoped preview: never read vault values or touch a DB."""
    root, key, namespace = _scope(project, project_id, broker)
    memories = _memories(experience_pack, project_id)
    resources = _resources(project, root, broker, resource_ids)
    sources = _data_sources(source_metadata, key, namespace, resources)
    payload = {
        "schema": SCHEMA,
        "scope": "synthetic_current_user_personal_preview_only",
        "project_binding_sha256": hashlib.sha256(_canonical([namespace, key, str(root), project_id])).hexdigest(),
        "memory_previews": memories,
        "credential_resource_ids_bound_metadata_only": resources,
        "data_sources_synthetic_metadata_only": sources,
        "retrieval_source": "existing_176_e5_pack_untrusted_caller_preview_not_verified_live_owner",
        "credential_source": "existing_163_broker_metadata_owner_no_vault_value_read",
        "source_registry_live_167": "NOT_RUN_POSTGRESQL_INCIDENT_OPEN",
        "authority": {
            "real_operator_consent_verified": False, "credentials_resolved": False,
            "source_queries_permitted": False, "experience_promoted": False,
            "fable_positive_granted": False, "native_claude_allowed": False,
            "postgresql_contact_permitted": False, "installed_state_changed": False,
        },
    }
    digest = hashlib.sha256(_canonical(payload, bound=_MAX_PACKET)).hexdigest()
    packet = {**payload, "packet_sha256": digest}
    _canonical(packet, bound=_MAX_PACKET)
    return packet


def require_current_personal_w3_reuse(project: Any, packet: Any, *, project_id: int,
                                      broker: CredentialBroker, experience_pack: Any,
                                      resource_ids: list[str], source_metadata: list[dict[str, Any]]) -> dict[str, Any]:
    """Require exact structural and type integrity of a freshly recomputed preview."""
    if type(packet) is not dict:
        raise PersonalW3Refusal("Expected immutable preview packet")
    current = preview_personal_w3_reuse(
        project, project_id=project_id, broker=broker, experience_pack=experience_pack,
        resource_ids=resource_ids, source_metadata=source_metadata,
    )
    if _canonical(packet, bound=_MAX_PACKET) != _canonical(current, bound=_MAX_PACKET):
        raise PersonalW3Refusal("Personal reuse preview changed or became stale")
    return current
