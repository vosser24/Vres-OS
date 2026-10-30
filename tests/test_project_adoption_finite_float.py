"""#168 A17: valid JSON exponents must not produce infinite saved values.

All state, files and projects are synthetic disposable fixtures; no real
installation, Claude hooks, model/issuer, credentials or PostgreSQL.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from vres_os import project_adoption
from vres_os.project import ProjectIdentity
from vres_os.project_adoption import AdoptionError


def _file(tmp_path: Path, raw: str) -> Path:
    root = tmp_path / "record"
    root.mkdir(exist_ok=True)
    target = root / "state.json"
    target.write_text(raw, encoding="utf-8")
    return target


def _files(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def _deny(path: Path) -> None:
    before = _files(path.parent)
    with pytest.raises(AdoptionError, match="unreadable; recovery") as result:
        project_adoption._read_json(path)
    assert "Nonfinite" not in str(result.value)
    assert _files(path.parent) == before


def test_normal_finite_float_roundtrips_without_write(tmp_path):
    path = _file(tmp_path, '{"price":1.25e2,"negative":-2.5e1}')
    before = path.read_bytes()
    assert project_adoption._read_json(path) == {"price": 125.0, "negative": -25.0}
    assert path.read_bytes() == before


def test_max_finite_exponent_still_supported(tmp_path):
    path = _file(tmp_path, '{"value":1e308}')
    assert project_adoption._read_json(path)["value"] == 1e308


def test_positive_overflowing_exponent_is_denied(tmp_path):
    _deny(_file(tmp_path, '{"value":1e999}'))


def test_negative_overflowing_exponent_is_denied(tmp_path):
    _deny(_file(tmp_path, '{"value":-1e999}'))


def test_overflow_from_decimal_mantissa_is_denied(tmp_path):
    _deny(_file(tmp_path, '{"value":9.999e999}'))


def test_overflow_nested_inside_object_is_denied(tmp_path):
    _deny(_file(tmp_path, '{"metadata":{"data":1.234e999}}'))


def test_overflow_nested_inside_array_is_denied(tmp_path):
    _deny(_file(tmp_path, '{"data":[0,1e999,2]}'))


def test_zero_with_large_exponent_remains_finite(tmp_path):
    path = _file(tmp_path, '{"zero":0e99999}')
    assert project_adoption._read_json(path) == {"zero": 0.0}


def test_very_small_finite_exponent_does_not_get_false_overflow(tmp_path):
    path = _file(tmp_path, '{"small":1e-20}')
    assert project_adoption._read_json(path) == {"small": 1e-20}


def test_quoted_exponent_is_literal_text_not_numeric_overflow(tmp_path):
    path = _file(tmp_path, '{"note":"1e999"}')
    assert project_adoption._read_json(path) == {"note": "1e999"}


def test_nan_and_infinity_literal_denials_remain_intact(tmp_path):
    for raw in ("NaN", "Infinity", "-Infinity"):
        _deny(_file(tmp_path, raw))


def test_duplicate_decoded_keys_still_refuse(tmp_path):
    _deny(_file(tmp_path, '{"state":1,"st\\u0061te":2}'))


def _held(tmp_path: Path):
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "CLAUDE.md").write_text("# Existing instructions\n", encoding="utf-8")
    project = ProjectIdentity(root=root.resolve(), key="project:finite-numbers",
                              name=root.name, remote_url=None, branch=None)
    data = tmp_path / "state"
    assert project_adoption.start(project, data_root=data)["state"] == "awaiting_operator"
    return project, data


def _inject_exponent(project, data) -> None:
    path = project_adoption._state_dir(project, data) / "state.json"
    before = path.read_text(encoding="utf-8").rstrip()
    assert before.endswith("}")
    path.write_text(before[:-1] + ',"metric":1e999}', encoding="utf-8")


def test_saved_state_overflow_refuses_status_without_writes(tmp_path):
    project, data = _held(tmp_path)
    _inject_exponent(project, data)
    before_state, before_source = _files(data), _files(project.root)
    with pytest.raises(AdoptionError, match="unreadable; recovery"):
        project_adoption.status(project, data_root=data)
    assert _files(data) == before_state
    assert _files(project.root) == before_source


def test_saved_state_overflow_refuses_start_without_repair(tmp_path):
    project, data = _held(tmp_path)
    _inject_exponent(project, data)
    before_state, before_source = _files(data), _files(project.root)
    with pytest.raises(AdoptionError, match="unreadable; recovery"):
        project_adoption.start(project, data_root=data)
    assert _files(data) == before_state
    assert _files(project.root) == before_source


def test_saved_state_overflow_cannot_prompt_activation_authority(tmp_path):
    project, data = _held(tmp_path)
    _inject_exponent(project, data)
    called = []
    before_state, before_source = _files(data), _files(project.root)

    def forbidden(statement):
        called.append(statement)
        pytest.fail("Overflowing JSON numeric reached activation authority")

    with pytest.raises(AdoptionError, match="unreadable; recovery"):
        project_adoption.activate(project, authority=forbidden, data_root=data)
    assert called == []
    assert _files(data) == before_state
    assert _files(project.root) == before_source
    assert not list(data.rglob("journal.json"))
