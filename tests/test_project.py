from pathlib import Path

from vres_os import project
from vres_os.processes import ProcessResult
from vres_os.project import discover_project


def test_project_identity_is_stable_for_plain_directory(tmp_path: Path):
    a = discover_project(tmp_path)
    b = discover_project(tmp_path)
    assert a.key == b.key
    assert a.root == tmp_path.resolve()


def test_git_discovery_never_inherits_mcp_stdin_and_is_tree_bounded(monkeypatch, tmp_path: Path):
    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return ProcessResult(True, str(tmp_path), 0)

    monkeypatch.setattr(project, "run_bounded", fake_run)

    result = project._run_git(tmp_path, "rev-parse", "--show-toplevel")

    assert result == str(tmp_path)
    assert calls[0][0] == ["git", "-C", str(tmp_path), "rev-parse", "--show-toplevel"]
    assert calls[0][1]["stdin_devnull"] is True
    assert calls[0][1]["timeout"] == 5
    assert calls[0][1]["redact_output"] is False
    assert calls[0][1]["max_output_bytes"] == 64 * 1024


def test_git_discovery_fails_closed_on_bounded_subprocess_failure(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        project,
        "run_bounded",
        lambda *_args, **_kwargs: ProcessResult(False, "Worker timed out", 124),
    )
    assert project._run_git(tmp_path, "config", "--get", "remote.origin.url") is None
