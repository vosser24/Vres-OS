"""Standalone personal Chairman CLI: only a disposable template read."""
from __future__ import annotations

from pathlib import Path

import pytest

from vres_os.chairman_selection_cli import main

_TEMPLATE = (
    b"---\n"
    b"name: chairman\n"
    b"description: Disposable C1 fixture, never an installed agent.\n"
    b"model: sonnet\n"
    b"effort: high\n"
    b"---\n"
    b"\n"
    b"Original Chairman body is not modified by a preview.\n"
)


@pytest.fixture
def source_root(tmp_path: Path) -> Path:
    """Only pytest-owned disposable temp receives a fixture file."""
    target = tmp_path / "plugins" / "vres-os" / "agents"
    target.mkdir(parents=True)
    (target / "chairman.md").write_bytes(_TEMPLATE)
    return tmp_path


def _args(source_root: Path, *extra: str) -> list[str]:
    return [
        "--source-root", str(source_root),
        "--reported-model", "sonnet",
        "--reported-effort", "high",
        "--proposed-model", "opus",
        "--proposed-effort", "medium",
        *extra,
    ]


def test_user_command_prints_ascii_only_preview_no_apply_and_no_changes(source_root, capsys):
    target = source_root / "plugins" / "vres-os" / "agents" / "chairman.md"
    before = target.read_bytes()
    assert main(_args(source_root)) == 0
    printed = capsys.readouterr()
    assert printed.err == ""
    assert all(ord(character) < 128 for character in printed.out)
    assert "Vres Chairman - PERSONAL READ-ONLY PREVIEW" in printed.out
    assert "Reported baseline (NOT live-verified): sonnet/high" in printed.out
    assert "Proposed candidate (NOT installed): opus/medium" in printed.out
    assert "  - Model: sonnet -> opus" in printed.out
    assert "  - Effort: high -> medium" in printed.out
    assert "Supplied template SHA-256:" in printed.out
    assert "Rendered candidate SHA-256:" in printed.out
    assert "No approval, settings change, model activation or installation" in printed.out
    assert target.read_bytes() == before


def test_single_fixed_repository_relative_file_is_read_once(source_root, capsys, monkeypatch):
    target = source_root / "plugins" / "vres-os" / "agents" / "chairman.md"
    original_open = Path.open
    observed: list[tuple[Path, str]] = []

    def observe_open(self, mode="r", *args, **kwargs):
        observed.append((self, mode))
        if self != target or mode != "rb":
            raise AssertionError("Unexpected template read/write path")
        return original_open(self, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe_open)
    assert main(_args(source_root)) == 0
    assert observed == [(target, "rb")]
    assert "NOT installed" in capsys.readouterr().out


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"], ids=["lf", "crlf"])
def test_both_native_newline_styles_preview_without_writing(source_root, capsys, newline):
    target = source_root / "plugins" / "vres-os" / "agents" / "chairman.md"
    content = _TEMPLATE.replace(b"\n", newline)
    target.write_bytes(content)
    assert main(_args(source_root)) == 0
    assert target.read_bytes() == content
    assert "Rendered candidate SHA-256:" in capsys.readouterr().out


def test_identical_model_effort_has_explicit_noop_display(source_root, capsys):
    args = _args(source_root)
    args[args.index("--proposed-model") + 1] = "sonnet"
    args[args.index("--proposed-effort") + 1] = "high"
    assert main(args) == 0
    out = capsys.readouterr().out
    assert "No difference in the supplied model, effort or version" in out
    assert "Proposed candidate (NOT installed): sonnet/high" in out


@pytest.mark.parametrize(
    "proposed_model, proposed_effort, changed, absent",
    [
        ("opus", "high", "Model: sonnet -> opus", "Effort: high -> medium"),
        ("sonnet", "medium", "Effort: high -> medium", "Model: sonnet -> opus"),
    ],
)
def test_model_only_and_effort_only_are_distinct(
    source_root, capsys, proposed_model, proposed_effort, changed, absent
):
    args = _args(source_root)
    args[args.index("--proposed-model") + 1] = proposed_model
    args[args.index("--proposed-effort") + 1] = proposed_effort
    assert main(args) == 0
    report = capsys.readouterr().out
    assert changed in report
    assert absent not in report


def test_explicit_policy_versions_are_display_only(source_root, capsys):
    assert main(_args(source_root, "--reported-version", "1", "--proposed-version", "2")) == 0
    result = capsys.readouterr().out
    assert "Policy version: 1 -> 2" in result
    assert "Proposed candidate (NOT installed): opus/medium (policy v2)" in result


@pytest.mark.parametrize("bad_version", ["0", "-1", "1000001", "auto", "1.5", "01", "+1"])
def test_invalid_version_is_argparse_error_before_any_template_read(
    source_root, capsys, monkeypatch, bad_version
):
    def no_read(self, *args, **kwargs):
        raise AssertionError("Unexpected read for an invalid argument")

    monkeypatch.setattr(Path, "open", no_read)
    with pytest.raises(SystemExit) as exc:
        main(_args(source_root, "--proposed-version", bad_version))
    assert exc.value.code == 2
    assert "Version must be" in capsys.readouterr().err


@pytest.mark.parametrize(
    "argument, bad_value",
    [
        ("--reported-model", "fable"),
        ("--reported-effort", "auto"),
        ("--proposed-model", "auto"),
        ("--proposed-effort", "extreme"),
    ],
)
def test_invalid_model_or_effort_never_falls_back(source_root, capsys, argument, bad_value):
    args = _args(source_root)
    args[args.index(argument) + 1] = bad_value
    with pytest.raises(SystemExit) as exc:
        main(args)
    assert exc.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_missing_explicit_source_root_is_refused_before_disk_read(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--reported-model", "sonnet", "--reported-effort", "high",
              "--proposed-model", "opus", "--proposed-effort", "medium"])
    assert exc.value.code == 2
    assert "required" in capsys.readouterr().err


def test_missing_source_template_is_neutral_and_does_not_echo_root(tmp_path, capsys):
    assert main(_args(tmp_path)) == 2
    printed = capsys.readouterr()
    assert printed.out == ""
    assert "PREVIEW_REFUSED: Source checkout Chairman template not available" in printed.err
    assert str(tmp_path) not in printed.err


@pytest.mark.parametrize(
    "bad_content",
    [
        b"",
        b"not valid frontmatter",
        b"---\nname: validator\ndescription: x\nmodel: sonnet\neffort: high\n---\nbody\n",
        b"\xff",
        b"x" * (512 * 1024 + 1),
    ],
)
def test_invalid_source_bytes_are_refused_without_rendering(
    source_root, capsys, bad_content
):
    target = source_root / "plugins" / "vres-os" / "agents" / "chairman.md"
    target.write_bytes(bad_content)
    assert main(_args(source_root)) == 2
    printed = capsys.readouterr()
    assert printed.out == ""
    assert "PREVIEW_REFUSED:" in printed.err
    assert target.read_bytes() == bad_content


def test_baseline_disagreement_is_refused_not_a_live_model_check(source_root, capsys):
    args = _args(source_root)
    args[args.index("--reported-model") + 1] = "opus"
    assert main(args) == 2
    printed = capsys.readouterr()
    assert "PREVIEW_REFUSED: Supplied Chairman template differs" in printed.err
    assert printed.out == ""


def test_missing_requested_template_subpath_is_not_scanned_or_guessed(tmp_path, capsys):
    (tmp_path / "chairman.md").write_bytes(_TEMPLATE)
    assert main(_args(tmp_path)) == 2
    assert "not available" in capsys.readouterr().err


def test_module_has_no_db_installer_or_provider_integration_surface():
    import vres_os.chairman_selection_cli as module

    names = set(vars(module))
    assert {"connect", "install", "apply", "approve", "psycopg", "keyring",
            "subprocess", "socket", "ConfigStore", "SecretStore",
            "ModelPolicyService", "bootstrap"}.isdisjoint(names)
    assert module.__all__ == ["main"]
