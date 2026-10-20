"""#176 E6 Chunk 1: hook registration, launcher and fail-safe behavior (no database)."""
import hashlib
import io
import json
import os
import subprocess
from pathlib import Path

import pytest

from vres_os import experience_observability as eo
from vres_os import hooks

ROOT = Path(__file__).resolve().parents[1]
HOOKS = json.loads((ROOT / "plugins/vres-os/hooks/hooks.json").read_text(encoding="utf-8"))
LAUNCHER = ROOT / "plugins/vres-os/bin/vres-experience-observe.ps1"
TOOL = "mcp__plugin_vres-os_vres__experience_retrieve"


def test_hooks_json_registers_one_successful_posttooluse_observer():
    entries = [e for e in HOOKS["hooks"]["PostToolUse"] if "vres-experience-observe" in json.dumps(e)]
    assert len(entries) == 1
    import re  # Chunk 2 broadened the matcher to every tool except the SubagentHandback event; retrieve is still matched
    assert re.search(entries[0]["matcher"], TOOL) and not re.search(entries[0]["matcher"], "SubagentHandback")
    assert entries[0]["hooks"][0]["timeout"] == 10
    assert all("vres-experience-observe" not in json.dumps(v) for k, v in HOOKS["hooks"].items() if k != "PostToolUse")
    assert "PostToolUseFailure" in HOOKS["hooks"]  # present, yet carries no reference/observation capture
    assert "vres-experience-observe" not in json.dumps(HOOKS["hooks"]["PostToolUseFailure"])


def _canonical_lf(raw: bytes) -> bytes:
    """The LF bytes of an LF checkout, or of exactly its all-CRLF form (a core.autocrlf checkout); nothing else."""
    lf = raw.replace(b"\r\n", b"\n")
    if b"\r" in lf or raw not in (lf, lf.replace(b"\n", b"\r\n")):
        raise ValueError("line endings are neither LF nor exactly the CRLF form of LF")
    return lf


def _launcher_text(raw: bytes) -> str:
    assert not raw.startswith(b"\xef\xbb\xbf")  # checked on the raw bytes
    return _canonical_lf(raw).decode("utf-8")


def test_launcher_is_bounded_utf8_nobom_and_fail_safe():
    text = _launcher_text(LAUNCHER.read_bytes())
    assert "1048577" in text and "1048576" in text and "UTF8Encoding $false" in text
    assert "-m vres_os.cli hook experience-observe" in text
    assert "exit $LASTEXITCODE" not in text and text.rstrip().endswith("exit 0\n}".strip())
    assert "$payload" not in text.split("catch {", 1)[1]  # the failure path never logs the payload


@pytest.mark.parametrize("damage", ["mixed-endings", "cr-only", "stray-cr", "bom", "invalid-utf8"])
def test_launcher_check_refuses_malformed_bytes(tmp_path, damage):
    lf = _canonical_lf(LAUNCHER.read_bytes())
    lines = lf.split(b"\n")
    malformed = {
        "mixed-endings": b"\r\n".join(lines[:3]) + b"\n" + b"\n".join(lines[3:]),
        "cr-only": lf.replace(b"\n", b"\r"),
        "stray-cr": lf.replace(b"\n", b"\r\n").replace(b"exit 0\r\n", b"exit 0\r\r\n"),
        "bom": b"\xef\xbb\xbf" + lf,
        "invalid-utf8": lf.replace(b"exit 0", b"exit \xff0"),
    }[damage]
    fixture = tmp_path / "vres-experience-observe.ps1"  # a disposable copy; the real launcher is never touched
    fixture.write_bytes(malformed)

    with pytest.raises((ValueError, AssertionError)):  # UnicodeDecodeError is a ValueError
        _launcher_text(fixture.read_bytes())


def test_launcher_check_accepts_only_lf_and_its_exact_crlf_form(tmp_path):
    lf = _canonical_lf(LAUNCHER.read_bytes())
    for name, data in (("lf.ps1", lf), ("crlf.ps1", lf.replace(b"\n", b"\r\n"))):
        (tmp_path / name).write_bytes(data)
        assert _launcher_text((tmp_path / name).read_bytes()) == lf.decode("utf-8")


def _committed_launchers() -> dict[str, bytes]:
    """{path: bytes} of every committed PowerShell launcher, read from HEAD's git objects and re-hashed."""
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(GIT_NO_REPLACE_OBJECTS="1", GIT_OPTIONAL_LOCKS="0")
    listing = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "-r", "-z", "HEAD", "--", "plugins/vres-os/bin",
                              "scripts/windows"], capture_output=True, check=True, env=env, timeout=60).stdout
    blobs = {}
    for entry in filter(None, listing.split(b"\0")):
        meta, path = entry.split(b"\t", 1)
        mode, kind, oid = meta.decode("ascii").split()
        if path.endswith(b".ps1"):
            body = subprocess.run(["git", "-C", str(ROOT), "cat-file", "blob", oid], capture_output=True,
                                  check=True, env=env, timeout=60).stdout
            assert (mode, kind) == ("100644", "blob")
            assert hashlib.sha1(b"blob %d\0" % len(body) + body).hexdigest() == oid  # the object, not a checkout
            blobs[path.decode("utf-8")] = body
    return blobs


@pytest.mark.skipif(not (ROOT / ".git").exists(), reason="the committed launcher bytes need the git checkout")
def test_committed_launcher_blobs_are_ascii_lf_without_bom():
    blobs = _committed_launchers()
    on_disk = sorted(p.relative_to(ROOT).as_posix() for d in ("plugins/vres-os/bin", "scripts/windows")
                     for p in (ROOT / d).glob("*.ps1"))
    assert sorted(blobs) == on_disk and "plugins/vres-os/bin/vres-experience-observe.ps1" in blobs
    for path, body in blobs.items():
        assert not body.startswith(b"\xef\xbb\xbf"), path
        assert b"\r" not in body and body.endswith(b"\n"), path
        body.decode("ascii")
        assert _canonical_lf((ROOT / path).read_bytes()) == body, path  # the checkout is this blob, or its CRLF form
    assert _launcher_text(blobs["plugins/vres-os/bin/vres-experience-observe.ps1"]).rstrip().endswith("exit 0\n}")


def test_cli_registers_command():
    from vres_os.cli import hook_app

    assert "experience-observe" in [c.name for c in hook_app.registered_commands]


class _Conn:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, *a):
        return self

    def fetchone(self):
        return {"id": 5}


def _run(monkeypatch, capsys, payload, tmp_path, observer):
    monkeypatch.setattr(hooks.sys, "stdin", io.StringIO(json.dumps(payload)))
    monkeypatch.setattr(hooks, "logs_dir", lambda: tmp_path)
    cfg = type("Cfg", (), {"configured": True})()
    monkeypatch.setattr(hooks, "ConfigStore", lambda: type("S", (), {"load": lambda self: cfg})())
    monkeypatch.setattr(hooks, "connect", lambda: _Conn())
    monkeypatch.setattr(eo, "observe_retrieval", observer)
    hooks.experience_observe()
    return capsys.readouterr()


def test_hook_failure_is_silent_bounded_and_never_logs_payload(monkeypatch, capsys, tmp_path):
    secret = "PRIVATE-QUERY-TEXT-xyz"

    def boom(payload, project_id):
        raise RuntimeError(secret)

    out = _run(monkeypatch, capsys, {"cwd": str(tmp_path), "tool_input": {"query": secret}}, tmp_path, boom)
    assert out.out == "" and out.err == ""
    log = (tmp_path / "hook-errors.log").read_text(encoding="utf-8")
    assert "event=ExperienceObserve code=RuntimeError" in log and secret not in log


def test_hook_rejection_logs_only_bounded_code(monkeypatch, capsys, tmp_path):
    def reject(payload, project_id):
        raise eo.ObservationRejected("pack_keys")

    out = _run(monkeypatch, capsys, {"cwd": str(tmp_path)}, tmp_path, reject)
    assert out.out == ""
    assert "code=pack_keys" in (tmp_path / "hook-errors.log").read_text(encoding="utf-8")


def test_hook_success_prints_nothing_and_passes_resolved_project(monkeypatch, capsys, tmp_path):
    seen = {}

    def ok(payload, project_id):
        seen["pid"] = project_id
        return {}

    out = _run(monkeypatch, capsys, {"cwd": str(tmp_path)}, tmp_path, ok)
    assert out.out == "" and seen["pid"] == 5


def _run_raw(monkeypatch, capsys, raw, tmp_path):
    monkeypatch.setattr(hooks.sys, "stdin", io.StringIO(raw))
    monkeypatch.setattr(hooks, "logs_dir", lambda: tmp_path)
    cfg = type("Cfg", (), {"configured": True})()
    monkeypatch.setattr(hooks, "ConfigStore", lambda: type("S", (), {"load": lambda self: cfg})())
    monkeypatch.setattr(hooks, "connect", lambda: _Conn())
    monkeypatch.setattr(eo, "observe_retrieval", lambda payload, project_id: pytest.fail("observer must not run"))
    hooks.experience_observe()
    return capsys.readouterr()


@pytest.mark.parametrize("raw", ["", "   ", "{not json PRIVATE-RAW-xyz", "[1, 2]", "null"])
def test_unusable_host_payload_logs_only_the_fixed_code(monkeypatch, capsys, tmp_path, raw):
    out = _run_raw(monkeypatch, capsys, raw, tmp_path)
    assert out.out == "" and out.err == ""
    lines = (tmp_path / "hook-errors.log").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and lines[0].endswith("event=ExperienceObserve code=host_payload_unavailable")
    assert "PRIVATE-RAW" not in lines[0] and "JSON" not in lines[0]


@pytest.mark.parametrize("outcome", ["session_not_found", "session_ambiguous"])
def test_bounded_non_success_outcome_leaves_a_fixed_diagnostic(monkeypatch, capsys, tmp_path, outcome):
    def observer(payload, project_id):
        return {"outcome": outcome, "observation_key": None, "attribution_state": None, "item_count": 1}

    out = _run(monkeypatch, capsys, {"cwd": str(tmp_path), "session_id": "SESSION-ID-xyz", "tool_use_id": "TOOLUSE-xyz"},
               tmp_path, observer)
    assert out.out == "" and out.err == ""
    lines = (tmp_path / "hook-errors.log").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and lines[0].endswith(f"event=ExperienceObserve code=observation_{outcome}")
    assert "SESSION-ID" not in lines[0] and "TOOLUSE" not in lines[0] and str(tmp_path) not in lines[0]


@pytest.mark.parametrize("outcome", ["recorded", "duplicate"])
def test_recorded_and_duplicate_are_not_errors(monkeypatch, capsys, tmp_path, outcome):
    out = _run(monkeypatch, capsys, {"cwd": str(tmp_path)}, tmp_path,
               lambda payload, project_id: {"outcome": outcome, "observation_key": "ERO-" + "0" * 32})
    assert out.out == "" and out.err == ""
    assert not (tmp_path / "hook-errors.log").exists()


def test_unknown_outcome_is_bounded_to_a_fixed_code(monkeypatch, capsys, tmp_path):
    _run(monkeypatch, capsys, {"cwd": str(tmp_path)}, tmp_path, lambda payload, project_id: {"outcome": "PRIVATE-OUTCOME-xyz"})
    log = (tmp_path / "hook-errors.log").read_text(encoding="utf-8")
    assert "code=observation_outcome_unexpected" in log and "PRIVATE-OUTCOME" not in log
