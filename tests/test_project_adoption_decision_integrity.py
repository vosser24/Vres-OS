"""#168 A11: stored KEEP/DROP data cannot override inventory choice restrictions.

All tests run against synthetic temporary small legacy projects and an isolated
data directory. No database, native Claude hooks, provider or installed Vres.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from vres_os import project_adoption
from vres_os.project import ProjectIdentity
from vres_os.project_adoption import AdoptionError

_SECRET = "sk-live-1234567890abcdefghijklmnop"


def _project(tmp_path: Path, *, secret: bool = False):
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "main.py").write_text("VALUE=1\n", encoding="utf-8")
    (root / "CLAUDE.md").write_text("# Original instructions\n", encoding="utf-8")
    settings = root / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({
        "hooks": {"PreToolUse": [{"hooks": [{"command": "DO_NOT_RUN"}]}]}
    }), encoding="utf-8")
    if secret:
        (root / ".claude" / ".env").write_text(
            "TOKEN=" + _SECRET + "\n", encoding="utf-8"
        )
    identity = ProjectIdentity(
        root=root.resolve(), key="project:decision-integrity", name=root.name,
        remote_url=None, branch=None,
    )
    data = tmp_path / "state"
    record = project_adoption.start(identity, data_root=data)
    assert record["state"] == "awaiting_operator"
    assert "architecture_review_required" not in record
    return identity, data


def _files(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def _approve(statement: str) -> dict:
    return {"confirmed": True, "kind": "synthetic_operator", "statement": statement}


def _decide_all(project, data) -> None:
    items = project_adoption.status(project, data_root=data)["items"]
    for item in items:
        choice = "KEEP" if "KEEP" in item["options"] else "DROP"
        project_adoption.decide(
            project, item["number"], choice, authority=_approve, data_root=data
        )
    assert project_adoption.status(project, data_root=data)["pending"] == []


def _record(data: Path) -> Path:
    records = list(data.rglob("decisions.json"))
    assert len(records) == 1
    return records[0]


def _corrupt(data: Path, change) -> None:
    path = _record(data)
    raw = json.loads(path.read_text(encoding="utf-8"))
    change(raw)
    path.write_text(json.dumps(raw), encoding="utf-8")


def _by_path(project, data):
    return {
        item["path"]: str(item["number"])
        for item in project_adoption.status(project, data_root=data)["items"]
    }


def _refused_before_authority_or_writes(project, data) -> None:
    before_source, before_state = _files(project.root), _files(data)
    authority_calls = []

    def forbid(statement):
        authority_calls.append(statement)
        pytest.fail("ACTIVATE operator authority invoked on untrusted decisions")

    with pytest.raises(AdoptionError, match="Stored decision"):
        project_adoption.activate(project, authority=forbid, data_root=data)
    assert authority_calls == []
    assert _files(project.root) == before_source
    assert _files(data) == before_state
    assert not list(data.rglob("journal.json"))
    assert not list(data.rglob("result.json"))


def test_valid_p2d_decisions_still_activate_and_rollback_synthetic_small_legacy(tmp_path):
    project, data = _project(tmp_path)
    before = _files(project.root)
    _decide_all(project, data)
    assert project_adoption.status(project, data_root=data)["pending"] == []

    result = project_adoption.activate(project, authority=_approve, data_root=data)

    assert result["state"] == "active"
    assert ".claude/settings.json" in result["removed"]
    assert not (project.root / ".claude" / "settings.json").exists()
    restored = project_adoption.rollback(project, authority=_approve, data_root=data)
    assert restored["state"] == "awaiting_operator"
    assert _files(project.root) == before


def test_forged_keep_for_executable_drop_only_surface_is_refused(tmp_path):
    project, data = _project(tmp_path)
    _decide_all(project, data)
    number = _by_path(project, data)[".claude/settings.json"]
    _corrupt(data, lambda raw: raw["decisions"][number].update(decision="KEEP"))
    _refused_before_authority_or_writes(project, data)


def test_forged_drop_for_sensitive_keep_only_surface_is_refused(tmp_path):
    project, data = _project(tmp_path, secret=True)
    _decide_all(project, data)
    number = _by_path(project, data)[".claude/.env"]
    before = _files(project.root)
    _corrupt(data, lambda raw: raw["decisions"][number].update(decision="DROP"))
    _refused_before_authority_or_writes(project, data)
    assert _files(project.root) == before
    assert _SECRET.encode() not in b"".join(_files(data).values())


def test_wrong_path_with_correct_source_hash_is_refused(tmp_path):
    project, data = _project(tmp_path)
    _decide_all(project, data)
    number = _by_path(project, data)["CLAUDE.md"]
    _corrupt(data, lambda raw: raw["decisions"][number].update(path="../other.md"))
    _refused_before_authority_or_writes(project, data)


def test_wrong_sha_with_permitted_choice_is_refused(tmp_path):
    project, data = _project(tmp_path)
    _decide_all(project, data)
    number = _by_path(project, data)["CLAUDE.md"]
    _corrupt(data, lambda raw: raw["decisions"][number].update(sha256="a" * 64))
    _refused_before_authority_or_writes(project, data)


def test_missing_operator_evidence_is_refused(tmp_path):
    project, data = _project(tmp_path)
    _decide_all(project, data)
    number = _by_path(project, data)["CLAUDE.md"]
    _corrupt(data, lambda raw: raw["decisions"][number].update(authority={}))
    _refused_before_authority_or_writes(project, data)


def test_false_confirmation_is_refused(tmp_path):
    project, data = _project(tmp_path)
    _decide_all(project, data)
    number = _by_path(project, data)["CLAUDE.md"]
    _corrupt(data, lambda raw: raw["decisions"][number]["authority"].update(confirmed=False))
    _refused_before_authority_or_writes(project, data)


def test_nonstr_authority_kind_is_refused(tmp_path):
    project, data = _project(tmp_path)
    _decide_all(project, data)
    number = _by_path(project, data)["CLAUDE.md"]
    _corrupt(data, lambda raw: raw["decisions"][number]["authority"].update(kind=12))
    _refused_before_authority_or_writes(project, data)


def test_missing_recorded_decision_timestamp_is_refused(tmp_path):
    project, data = _project(tmp_path)
    _decide_all(project, data)
    number = _by_path(project, data)["CLAUDE.md"]
    _corrupt(data, lambda raw: raw["decisions"][number].pop("at"))
    _refused_before_authority_or_writes(project, data)


def test_unknown_item_number_even_with_valid_other_decisions_is_refused(tmp_path):
    project, data = _project(tmp_path)
    _decide_all(project, data)
    number = _by_path(project, data)["CLAUDE.md"]
    _corrupt(data, lambda raw: raw["decisions"].update({"999": copy.deepcopy(raw["decisions"][number])}))
    _refused_before_authority_or_writes(project, data)


def test_decisions_array_instead_of_mapping_is_refused(tmp_path):
    project, data = _project(tmp_path)
    _decide_all(project, data)
    _corrupt(data, lambda raw: raw.update(decisions=[]))
    _refused_before_authority_or_writes(project, data)


def test_outdated_inventory_version_does_not_reuse_old_decisions(tmp_path):
    project, data = _project(tmp_path)
    _decide_all(project, data)
    _corrupt(data, lambda raw: raw.update(inventory_version="a" * 64))
    before_source, before_state = _files(project.root), _files(data)
    asked = []
    with pytest.raises(AdoptionError, match="Undecided items"):
        project_adoption.activate(
            project, authority=lambda text: asked.append(text), data_root=data
        )
    assert asked == []
    assert _files(project.root) == before_source
    assert _files(data) == before_state


def test_missing_decisions_remain_pending_without_creating_them(tmp_path):
    project, data = _project(tmp_path)
    before = _files(data)
    current = project_adoption.status(project, data_root=data)
    assert current["pending"] == [1, 2]
    assert not list(data.rglob("decisions.json"))
    assert _files(data) == before


def test_missing_hash_field_on_sensitive_keep_only_record_is_refused(tmp_path):
    project, data = _project(tmp_path, secret=True)
    _decide_all(project, data)
    number = _by_path(project, data)[".claude/.env"]
    _corrupt(data, lambda raw: raw["decisions"][number].pop("sha256"))
    _refused_before_authority_or_writes(project, data)


def test_decisions_root_array_is_refused(tmp_path):
    project, data = _project(tmp_path)
    _decide_all(project, data)
    _record(data).write_text("[]", encoding="utf-8")
    _refused_before_authority_or_writes(project, data)
