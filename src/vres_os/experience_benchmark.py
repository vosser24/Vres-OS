"""E7 benchmark foundation: strict loader, canonical digests, alias normalization, EvidencePack.

Placement: one flat module beside the experience_* owners (the repository's existing convention).
It depends downward on `sensitive_policy` only. No E1-E6 module imports it (guarded by a test), and
it has no CLI/MCP surface, no SQL and no durable state: manifests, alias maps and packs are Git
artifacts or process state.

Contract: docs/architecture/EXPERIENCE-INTELLIGENCE-E7-CONTRACT-*.md (original + addenda 1 and 2).
Chunk 0 scope only: no corpus, no adapters, no metric scoring, no thresholds.

Conventions fixed here (not contract numerics):
  * Text files are UTF-8 without BOM. CRLF is normalized to LF before parsing and hashing (git
    autocrlf safety); a lone CR is rejected. JSONL files must end with a newline and have no blank
    lines.
  * Floats are forbidden in all benchmark data and digested identity material.
  * File digest = SHA-256 of the LF-normalized bytes. Logical digests are SHA-256 of canonical JSON.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from hashlib import sha256
from pathlib import Path
from typing import Any

from .sensitive_policy import sanitize_extracted_text

SCHEMA_VERSIONS = {
    "corpus": 1,
    "expected_evidence": 1,
    "manifest": 1,
    "scoring": 1,
    "evidence_pack": 1,
}
SPLITS = ("development", "heldout", "adversarial")
DEVELOPMENT_SPLITS = ("development", "adversarial")
ALIAS_PREFIX = {"development": "dev_", "heldout": "held_", "adversarial": "adv_"}
BUNDLE_FILES = ("corpus.jsonl", "expected_evidence.json")
KINDS = ("knowledge", "chunk", "procedure", "experience")

_ID = re.compile(r"[a-z][a-z0-9_]{0,62}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_UNMAPPED = re.compile(r"unmapped_[1-9][0-9]*")
_SCORING_KEYS = {
    "answer",
    "answers",
    "relevant",
    "acceptable",
    "irrelevant",
    "stale",
    "score",
    "scores",
    "scoring",
    "near_duplicate_of",
    "must_abstain",
    "premise",
    "conflict_pair",
    "label",
    "labels",
    "threshold",
    "thresholds",
}
_PROHIBITED_PACK_KEYS = {
    "id",
    "ids",
    "db_id",
    "chunk_id",
    "source_id",
    "knowledge_id",
    "memory_key",
    "runtime_key",
    "chunk_key",
    "knowledge_key",
    "source_key",
    "procedure_key",
    "episode_key",
    "score",
    "rank_score",
    "path",
    "path_or_uri",
    "uri",
    "vector",
    "embedding",
    "reasoning",
    "chain_of_thought",
    "thinking",
}


class BenchmarkError(ValueError):
    """Any fail-closed benchmark input, schema, digest or boundary violation."""


# ---- canonical form and digests ---


def _check_identity_value(value: Any) -> None:
    if value is None or isinstance(value, (bool, int, str)):
        return
    if isinstance(value, float):
        raise BenchmarkError("float values are forbidden in benchmark data and digests")
    if isinstance(value, (list, tuple)):
        for v in value:
            _check_identity_value(v)
        return
    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str):
                raise BenchmarkError("object keys must be strings")
            _check_identity_value(v)
        return
    raise BenchmarkError(f"unsupported value type {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    """UTF-8 JSON, sorted keys, no whitespace, ensure_ascii=False. No floats."""
    _check_identity_value(value)
    text = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    try:
        return text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise BenchmarkError("text is not encodable as UTF-8 (lone surrogate)") from exc


def sha256_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


def normalize_text_bytes(raw: bytes) -> bytes:
    """Validate UTF-8/no-BOM and normalize CRLF to LF. A lone CR is rejected."""
    if raw.startswith(b"\xef\xbb\xbf"):
        raise BenchmarkError("BOM is not allowed (UTF-8 without BOM required)")
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BenchmarkError("file is not valid UTF-8") from exc
    unified = raw.replace(b"\r\n", b"\n")
    if b"\r" in unified:
        raise BenchmarkError("bad line ending: lone CR")
    return unified


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise BenchmarkError(f"duplicate key {key!r} in JSON object")
        out[key] = value
    return out


def _reject_float(text: str) -> Any:
    raise BenchmarkError("float values are forbidden in benchmark data")


def _reject_constant(name: str) -> Any:
    raise BenchmarkError(f"non-finite constant {name} is not allowed")


def loads_strict(text: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_no_duplicates,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except BenchmarkError:
        raise
    except ValueError as exc:
        raise BenchmarkError(f"malformed JSON: {exc}") from exc


def corpus_digest(cases: list[dict]) -> str:
    return sha256_hex(b"".join(canonical_bytes(c) + b"\n" for c in cases))


def expected_digest(expected: dict) -> str:
    return sha256_hex(canonical_bytes(expected))


def scoring_digest(config: dict) -> str:
    return sha256_hex(canonical_bytes(config))


def bundle_digest(files: dict[str, str], case_ids: list[str]) -> str:
    return sha256_hex(canonical_bytes({"case_ids": sorted(case_ids), "files": files}))


# ---- small closed-schema helpers ---


def _closed(obj: Any, required: set[str], optional: set[str], what: str) -> dict:
    if not isinstance(obj, dict):
        raise BenchmarkError(f"{what} must be an object")
    missing = required - set(obj)
    if missing:
        raise BenchmarkError(f"{what} missing field(s) {sorted(missing)}")
    unknown = set(obj) - required - optional
    if unknown:
        raise BenchmarkError(f"{what} has unknown field(s) {sorted(unknown)}")
    return obj


def _schema_version(obj: dict, kind: str) -> None:
    if type(obj["schema_version"]) is not int or obj["schema_version"] != SCHEMA_VERSIONS[kind]:
        raise BenchmarkError(f"{kind} schema_version must be {SCHEMA_VERSIONS[kind]}")


def _is_pos_int(value: Any) -> bool:
    return type(value) is int and value > 0


def _check_alias_syntax(alias: Any) -> str:
    if not isinstance(alias, str) or not _ID.fullmatch(alias):
        raise BenchmarkError(f"invalid alias {alias!r}")
    if alias.startswith("unmapped"):
        raise BenchmarkError(f"reserved alias {alias!r}")
    return alias


def _alias_list(value: Any, declared: set[str], what: str) -> list[str]:
    if not isinstance(value, list):
        raise BenchmarkError(f"{what} must be a list of aliases")
    seen: set[str] = set()
    for alias in value:
        if not isinstance(alias, str) or alias not in declared:
            raise BenchmarkError(f"{what} references unknown alias {alias!r}")
        if alias in seen:
            raise BenchmarkError(f"{what} has duplicate alias {alias!r}")
        seen.add(alias)
    return value


# ---- scoring configuration (shape only; no metric semantics, no thresholds) ---


def validate_scoring_config(cfg: Any) -> dict:
    _closed(cfg, {"schema_version", "latency", "evidence"}, set(), "scoring config")
    _schema_version(cfg, "scoring")
    latency = _closed(cfg["latency"], {"repeats"}, set(), "scoring latency")
    repeats = latency["repeats"]
    if type(repeats) is not int or repeats <= 0 or repeats % 4:
        raise BenchmarkError("latency.repeats must be a positive integer divisible by 4")
    evidence = _closed(cfg["evidence"], {"content_max_code_points"}, set(), "scoring evidence")
    if not _is_pos_int(evidence["content_max_code_points"]):
        raise BenchmarkError("evidence.content_max_code_points must be a positive integer")
    _check_identity_value(cfg)
    return cfg


# ---- corpus / expected-evidence schemas ---


def _scan_scoring_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            if key.startswith("expected") or key in _SCORING_KEYS:
                raise BenchmarkError(f"scoring material {key!r} is not allowed in corpus input")
            _scan_scoring_keys(inner)
    elif isinstance(value, list):
        for inner in value:
            _scan_scoring_keys(inner)


def _validate_case(case: Any, split: str) -> dict:
    _scan_scoring_keys(case)
    _closed(
        case, {"schema_version", "case_id", "category", "query", "aliases"}, {"timeline"}, "case"
    )
    _schema_version(case, "corpus")
    if not isinstance(case["case_id"], str) or not _ID.fullmatch(case["case_id"]):
        raise BenchmarkError(f"invalid case_id {case['case_id']!r}")
    for field in ("category", "query"):
        if not isinstance(case[field], str) or not case[field].strip():
            raise BenchmarkError(f"case {case['case_id']} {field} must be non-empty text")
    aliases = case["aliases"]
    if not isinstance(aliases, list):
        raise BenchmarkError("case aliases must be a list")
    seen: set[str] = set()
    for alias in aliases:
        _check_alias_syntax(alias)
        if alias in seen:
            raise BenchmarkError(f"case {case['case_id']} has duplicate alias {alias!r}")
        seen.add(alias)
        if not alias.startswith(ALIAS_PREFIX[split]):
            raise BenchmarkError(
                f"alias prefix mismatch: {alias!r} in {split} requires {ALIAS_PREFIX[split]!r}"
            )
    for step in case.get("timeline", []):
        _closed(step, {"op"}, {"alias", "args"}, "timeline step")
        if not isinstance(step["op"], str) or not step["op"]:
            raise BenchmarkError("timeline op must be non-empty text")
        if "alias" in step and step["alias"] not in seen:
            raise BenchmarkError(f"timeline references unknown alias {step['alias']!r}")
        if "args" in step and not isinstance(step["args"], dict):
            raise BenchmarkError("timeline args must be an object")
    return case


def parse_corpus(normalized: bytes, split: str) -> list[dict]:
    text = normalized.decode("utf-8")
    if not text.endswith("\n"):
        raise BenchmarkError("malformed JSONL: missing final newline")
    lines = text[:-1].split("\n")
    if lines == [""]:
        raise BenchmarkError("corpus is empty")
    cases, ids = [], set()
    for number, line in enumerate(lines, 1):
        if not line.strip():
            raise BenchmarkError(f"malformed JSONL: blank line {number}")
        case = _validate_case(loads_strict(line), split)
        if case["case_id"] in ids:
            raise BenchmarkError(f"duplicate case id {case['case_id']!r}")
        ids.add(case["case_id"])
        cases.append(case)
    return cases


_LABEL_LISTS = ("relevant", "acceptable", "irrelevant", "stale", "premise")


def _validate_near_duplicates(mapping: Any, declared: set[str]) -> None:
    if not isinstance(mapping, dict):
        raise BenchmarkError("near_duplicate_of must be an object alias->canonical alias")
    for alias, target in mapping.items():
        if alias not in declared or target not in declared:
            raise BenchmarkError(
                f"near_duplicate_of references unknown alias ({alias!r} -> {target!r})"
            )
        if alias == target:
            raise BenchmarkError(f"near_duplicate_of self reference {alias!r}")
    for start in mapping:
        seen, node = {start}, mapping[start]
        while node in mapping:
            if node in seen:
                raise BenchmarkError(f"near_duplicate_of cycle through {node!r}")
            seen.add(node)
            node = mapping[node]
    for alias, target in mapping.items():
        if target in mapping:
            raise BenchmarkError(
                f"near_duplicate_of target {target!r} must be canonical (chain from {alias!r})"
            )


def parse_expected(normalized: bytes, cases: list[dict]) -> dict[str, dict]:
    parsed = loads_strict(normalized.decode("utf-8"))
    _closed(parsed, {"schema_version", "cases"}, set(), "expected evidence")
    _schema_version(parsed, "expected_evidence")
    entries = parsed["cases"]
    if not isinstance(entries, dict):
        raise BenchmarkError("expected evidence cases must be an object")
    declared = {c["case_id"]: set(c["aliases"]) for c in cases}
    unknown = set(entries) - set(declared)
    if unknown:
        raise BenchmarkError(f"expected evidence references unknown case(s) {sorted(unknown)}")
    absent = set(declared) - set(entries)
    if absent:
        raise BenchmarkError(f"expected evidence missing case(s) {sorted(absent)}")
    for case_id, entry in entries.items():
        aliases = declared[case_id]
        _closed(
            entry,
            set(),
            {*_LABEL_LISTS, "conflict_pair", "must_abstain", "near_duplicate_of"},
            f"expected evidence for {case_id}",
        )
        for label in _LABEL_LISTS:
            if label in entry:
                _alias_list(entry[label], aliases, f"{case_id}.{label}")
        for group in entry.get("conflict_pair", []):
            if not isinstance(group, list) or len(group) < 2:
                raise BenchmarkError(f"{case_id}.conflict_pair groups need at least two aliases")
            _alias_list(group, aliases, f"{case_id}.conflict_pair")
        if "must_abstain" in entry and not isinstance(entry["must_abstain"], bool):
            raise BenchmarkError(f"{case_id}.must_abstain must be a boolean")
        if "near_duplicate_of" in entry:
            _validate_near_duplicates(entry["near_duplicate_of"], aliases)
    return entries


# ---- manifest and held-out-safe loader ---


def _validate_rel_path(rel: Any, split: str) -> str:
    if not isinstance(rel, str) or not rel or "\\" in rel or rel.startswith("/") or ":" in rel:
        raise BenchmarkError(f"unsafe path {rel!r}")
    parts = rel.split("/")
    if len(parts) != 2 or parts[0] != split or parts[1] not in BUNDLE_FILES:
        raise BenchmarkError(f"path {rel!r} is not an allowed file of the {split} bundle")
    return parts[1]


def _validate_manifest(m: Any) -> dict:
    _closed(m, {"schema_version", "heldout_version", "consumed", "bundles"}, set(), "manifest")
    _schema_version(m, "manifest")
    if not _is_pos_int(m["heldout_version"]):
        raise BenchmarkError("manifest heldout_version must be a positive integer")
    if not isinstance(m["consumed"], list):
        raise BenchmarkError("manifest consumed must be a list")
    for entry in m["consumed"]:
        _closed(entry, {"version", "reason"}, set(), "manifest consumed entry")
        if not _is_pos_int(entry["version"]) or not isinstance(entry["reason"], str):
            raise BenchmarkError("manifest consumed entry invalid")
    bundles = m["bundles"]
    if not isinstance(bundles, dict) or set(bundles) - set(SPLITS):
        raise BenchmarkError("manifest bundles must be an object keyed by known splits")
    owners: dict[str, str] = {}
    for split, bundle in bundles.items():
        _closed(bundle, {"files", "case_ids", "bundle_digest"}, set(), f"manifest bundle {split}")
        files = bundle["files"]
        if not isinstance(files, dict):
            raise BenchmarkError("manifest files must be an object")
        for rel, digest in files.items():
            _validate_rel_path(rel, split)
            if not isinstance(digest, str) or not _HEX64.fullmatch(digest):
                raise BenchmarkError(f"invalid digest for {rel!r}")
        if set(files) != {f"{split}/{name}" for name in BUNDLE_FILES}:
            raise BenchmarkError(
                f"manifest bundle {split} must list exactly its two files (path set)"
            )
        if not isinstance(bundle["bundle_digest"], str) or not _HEX64.fullmatch(
            bundle["bundle_digest"]
        ):
            raise BenchmarkError(f"invalid bundle digest for {split}")
        ids = bundle["case_ids"]
        if not isinstance(ids, list) or any(
            not isinstance(i, str) or not _ID.fullmatch(i) for i in ids
        ):
            raise BenchmarkError(f"manifest case_ids for {split} invalid")
        if len(set(ids)) != len(ids):
            raise BenchmarkError(f"manifest case_ids for {split} contain duplicates")
        for case_id in ids:
            if case_id in owners:
                raise BenchmarkError(f"case id {case_id!r} registered in more than one bundle")
            owners[case_id] = split
    return m


def _read_normalized(path: str) -> bytes:
    with open(path, "rb") as handle:
        return normalize_text_bytes(handle.read())


def load_manifest(root: str | Path) -> dict:
    manifest_path = os.path.join(os.fspath(root), "manifest.json")
    return _validate_manifest(loads_strict(_read_normalized(manifest_path).decode("utf-8")))


def _bundle_file(root: str, split: str, name: str) -> str:
    real_root = os.path.normcase(os.path.realpath(root))
    split_dir = os.path.join(root, split)
    real_split = os.path.normcase(os.path.realpath(split_dir))
    if os.path.islink(split_dir) or real_split != os.path.join(real_root, split):
        raise BenchmarkError(
            f"path escape: {split} directory is not a plain directory under the root"
        )
    target = os.path.join(split_dir, name)
    if os.path.islink(target) or os.path.normcase(os.path.realpath(target)) != os.path.join(
        real_split, name
    ):
        raise BenchmarkError(f"path escape: {split}/{name} is not a plain file under its bundle")
    return target


def load_development_bundle(
    root: str | Path,
    split: str = "development",
    *,
    case_ids: list[str] | None = None,
    digests: list[str] | None = None,
) -> dict:
    """Load a development or adversarial bundle.

    Held-out input is rejected before any bundle file is opened.

    `case_ids` / `digests`, when supplied, are caller-asserted identities that must not belong to
    the held-out bundle.
    """
    if not isinstance(split, str):
        raise BenchmarkError("split must be text")
    if "heldout" in split.lower():
        raise BenchmarkError("held-out split cannot be loaded by the development loader")
    if split not in DEVELOPMENT_SPLITS:
        raise BenchmarkError(f"unsupported split {split!r}")
    root_s = os.fspath(root)
    manifest = load_manifest(root_s)  # manifest.json only: it lists ids and digests, never answers
    held = manifest["bundles"].get("heldout")
    if held:
        if set(case_ids or ()) & set(held["case_ids"]):
            raise BenchmarkError("held-out case id supplied to the development loader")
        if set(digests or ()) & {held["bundle_digest"], *held["files"].values()}:
            raise BenchmarkError("held-out digest supplied to the development loader")
    bundle = manifest["bundles"].get(split)
    if bundle is None:
        raise BenchmarkError(f"manifest has no {split} bundle")
    raw = {}
    for name in BUNDLE_FILES:
        rel = f"{split}/{name}"
        raw[name] = _read_normalized(_bundle_file(root_s, split, name))
        if sha256_hex(raw[name]) != bundle["files"][rel]:
            raise BenchmarkError(f"file digest mismatch for {rel}")
    if bundle_digest(bundle["files"], bundle["case_ids"]) != bundle["bundle_digest"]:
        raise BenchmarkError(f"bundle digest mismatch for {split}")
    cases = parse_corpus(raw["corpus.jsonl"], split)
    if sorted(c["case_id"] for c in cases) != sorted(bundle["case_ids"]):
        raise BenchmarkError(f"manifest case ids disagree with {split} corpus")
    expected = parse_expected(raw["expected_evidence.json"], cases)
    return {
        "split": split,
        "cases": cases,
        "expected": expected,
        "digests": {
            "corpus": corpus_digest(cases),
            "expected_evidence": expected_digest(expected),
            "bundle": bundle["bundle_digest"],
        },
    }


# ---- alias <-> runtime-key normalization ---


class AliasMap:
    """Case-local alias<->runtime-key map. Runtime keys never appear in `resolve` output."""

    def __init__(self, aliases: list[str]):
        self._declared: set[str] = set()
        for alias in aliases:
            _check_alias_syntax(alias)
            if alias in self._declared:
                raise BenchmarkError(f"duplicate alias {alias!r}")
            self._declared.add(alias)
        self._by_alias: dict[str, str] = {}
        self._by_key: dict[str, str] = {}
        self._unmapped: dict[str, int] = {}

    def __repr__(self) -> str:
        return f"AliasMap(<{len(self._declared)} aliases>)"

    def bind(self, alias: str, runtime_key: str) -> None:
        if alias not in self._declared:
            raise BenchmarkError(f"undeclared alias {alias!r}")
        if not isinstance(runtime_key, str) or not runtime_key:
            raise BenchmarkError("runtime key must be non-empty text")
        if alias in self._by_alias:
            raise BenchmarkError(f"alias {alias!r} already bound")
        if runtime_key in self._by_key:
            raise BenchmarkError("runtime key already bound to an alias")
        self._by_alias[alias] = runtime_key
        self._by_key[runtime_key] = alias

    def alias_for(self, runtime_key: str) -> str | None:
        return self._by_key.get(runtime_key)

    def runtime_key_for(self, alias: str) -> str | None:
        return self._by_alias.get(alias)

    def resolve(self, runtime_keys: list[str]) -> list[str]:
        out = []
        for key in runtime_keys:
            alias = self._by_key.get(key)
            if alias is None:
                alias = f"unmapped_{self._unmapped.setdefault(key, len(self._unmapped) + 1)}"
            out.append(alias)
        return out


# ---- EvidencePack (Addendum 2 B2) ---


def _pack_alias(alias: Any) -> str:
    if isinstance(alias, str) and (
        _UNMAPPED.fullmatch(alias) or (_ID.fullmatch(alias) and not alias.startswith("unmapped"))
    ):
        return alias
    raise BenchmarkError(f"invalid alias {alias!r}")


def _validate_item(item: Any) -> dict:
    if not isinstance(item, dict):
        raise BenchmarkError("evidence item must be an object")
    prohibited = set(item) & _PROHIBITED_PACK_KEYS
    if prohibited:
        raise BenchmarkError(f"prohibited field(s) in evidence item: {sorted(prohibited)}")
    _closed(item, {"alias", "kind", "content", "truncated", "rank"}, set(), "evidence item")
    _pack_alias(item["alias"])
    if item["kind"] not in KINDS or not isinstance(item["kind"], str):
        raise BenchmarkError(f"invalid kind {item['kind']!r}")
    if not _is_pos_int(item["rank"]):
        raise BenchmarkError("rank must be a positive integer")
    if type(item["truncated"]) is not bool:
        raise BenchmarkError("truncated must be a boolean")
    content = item["content"]
    if not isinstance(content, str):
        raise BenchmarkError("content must be text")
    if unicodedata.normalize("NFC", content) != content:
        raise BenchmarkError("content must be NFC-normalized")
    if sanitize_extracted_text(content).status is not None:
        raise BenchmarkError("secret-shaped content in evidence item (fail closed)")
    return item


def validate_pack(items: Any) -> list[dict]:
    if not isinstance(items, list):
        raise BenchmarkError("evidence pack must be a list")
    return [dict(_validate_item(item)) for item in items]


def build_evidence_item(
    alias: str, kind: str, content: str, rank: int, *, max_code_points: int
) -> dict:
    """NFC-normalize, fail closed on secret-shaped text (before any cut), then cut."""
    if not _is_pos_int(max_code_points):
        raise BenchmarkError("max_code_points must be a positive integer")
    if not isinstance(content, str):
        raise BenchmarkError("content must be text")
    text = unicodedata.normalize("NFC", content)
    if sanitize_extracted_text(text).status is not None:
        raise BenchmarkError("secret-shaped content in evidence item (fail closed)")
    truncated = len(text) > max_code_points
    item = {
        "alias": alias,
        "kind": kind,
        "content": text[:max_code_points],
        "truncated": truncated,
        "rank": rank,
    }
    return _validate_item(item)


def build_pack(items: list[dict]) -> list[dict]:
    """Validate and totally order a pack: rank, alias, kind, content (input-order independent)."""
    return sorted(
        validate_pack(items), key=lambda i: (i["rank"], i["alias"], i["kind"], i["content"])
    )


def pack_bytes(pack: list[dict]) -> bytes:
    return canonical_bytes(validate_pack(pack))


def pack_digest(pack: list[dict]) -> str:
    return sha256_hex(pack_bytes(pack))
