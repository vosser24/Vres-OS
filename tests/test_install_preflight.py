"""P2-F local update preflight: the installer never contacts PostgreSQL, an update asks an accurate
question, and pip's dependency report is recorded as audit evidence only. Offline: database, secret
store and prerequisites are mocked; PowerShell, pip, Claude and PostgreSQL are never run.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

_ROOT = Path(__file__).resolve().parents[1]


def _installer() -> str:
    return (_ROOT / "install.ps1").read_text(encoding="utf-8")


# ------------------------------------------------------------------- doctor --skip-database (T1-T3)

@pytest.fixture
def configured_doctor(monkeypatch):
    """cli.doctor with a configured installation, every prerequisite present, and a recording database."""
    import vres_os.cli as cli
    import vres_os.db as db
    import vres_os.secrets as secrets

    calls = {"connect": 0, "secret": 0}

    def connect(*a, **k):
        calls["connect"] += 1
        raise RuntimeError("Vres refused to contact 127.0.0.1:5432/vres_os: it has not been approved")

    def secret(*a, **k):
        calls["secret"] += 1
        raise AssertionError("no credential may be read")

    prerequisites = {"git": True, "claude": True, "codex": False}
    present = {"psycopg": True, "mcp": True, "keyring": True}
    monkeypatch.setattr(cli, "prerequisite_status", lambda: dict(prerequisites))
    monkeypatch.setattr(cli, "ConfigStore", lambda: SimpleNamespace(load=lambda: SimpleNamespace(configured=True)))
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object() if present.get(name, True) else None)
    monkeypatch.setattr(db, "connect", connect)
    monkeypatch.setattr(secrets.SecretStore, "get", secret)
    return cli, calls, prerequisites, present


def _doctor(cli, *args):
    return CliRunner().invoke(cli.app, ["doctor", *args])


@pytest.mark.parametrize("args", [["--allow-unconfigured", "--skip-database"], ["--skip-database"]])
def test_skip_database_never_connects_or_reads_a_credential(configured_doctor, args):
    cli, calls, _, _ = configured_doctor

    result = _doctor(cli, *args)

    assert result.exit_code == 0, result.output
    assert calls == {"connect": 0, "secret": 0}
    assert re.search(r"PostgreSQL\s*.\s*NOT CHECKED", result.output)
    assert "Connected" not in result.output


@pytest.mark.parametrize("missing", ["git", "claude", "psycopg", "mcp", "keyring"])
def test_skip_database_still_fails_on_every_other_missing_prerequisite(configured_doctor, missing):
    cli, calls, prerequisites, present = configured_doctor
    if missing in prerequisites:
        prerequisites[missing] = False
    else:
        present[missing] = False

    result = _doctor(cli, "--allow-unconfigured", "--skip-database")

    # Exit 2 must come from the health table, not from an unknown-option usage error.
    assert result.exit_code == 2 and "No such option" not in result.output
    assert re.search(rf"{missing}\s*.\s*MISSING", result.output), result.output
    assert calls == {"connect": 0, "secret": 0}


def test_ordinary_doctor_still_contacts_through_the_guard_and_fails_on_refusal(configured_doctor):
    cli, calls, _, _ = configured_doctor  # positive control: behaviour without the flag is unchanged

    result = _doctor(cli, "--allow-unconfigured")

    assert result.exit_code == 2 and calls["connect"] == 1
    assert "refused to contact" in result.output and "NOT CHECKED" not in result.output


def test_skip_database_does_not_change_the_unconfigured_rules(monkeypatch):
    import vres_os.cli as cli

    monkeypatch.setattr(cli, "prerequisite_status", lambda: {"git": True, "claude": True})
    monkeypatch.setattr(cli, "ConfigStore", lambda: SimpleNamespace(load=lambda: SimpleNamespace(configured=False)))
    monkeypatch.setattr(cli, "last_setup_result", lambda: None)
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object())

    assert _doctor(cli, "--skip-database").exit_code == 2  # unconfigured still needs --allow-unconfigured
    assert _doctor(cli, "--allow-unconfigured", "--skip-database").exit_code == 0


@pytest.mark.parametrize("args,code", [(["--allow-unconfigured", "--skip-database"], 0), (["--skip-database"], 2)])
def test_skip_database_shows_not_checked_for_an_unconfigured_installation_too(monkeypatch, args, code):
    import vres_os.cli as cli
    import vres_os.db as db
    import vres_os.secrets as secrets

    def forbidden(*a, **k):
        raise AssertionError("no database contact or credential read")

    monkeypatch.setattr(cli, "prerequisite_status", lambda: {"git": True, "claude": True})
    monkeypatch.setattr(cli, "ConfigStore", lambda: SimpleNamespace(load=lambda: SimpleNamespace(configured=False)))
    monkeypatch.setattr(cli, "last_setup_result", lambda: None)
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(db, "connect", forbidden)
    monkeypatch.setattr(secrets.SecretStore, "get", forbidden)

    result = _doctor(cli, *args)

    assert result.exit_code == code, result.output
    assert re.search(r"PostgreSQL\s*.\s*NOT CHECKED", result.output), result.output


# --------------------------------------------------------------------------- installer contract (T4)

def test_installer_preflight_never_contacts_the_database_and_keeps_its_integrity_gates():
    text = _installer()
    at = text.index

    doctor_calls = re.findall(r".*vres_os\.cli','doctor'.*", text)
    assert doctor_calls == ["    Run $NewPython @('-B','-m','vres_os.cli','doctor','--allow-unconfigured','--skip-database')"]
    assert "'selftest'" not in text and "'migrate'" not in text and "'setup'" not in text
    # Source identity, staging, package verification, journal and rollback are unchanged and in order.
    stage = at("'stage','--root',$RepoRoot,'--out',$StagedSource,'--manifest',$ReleaseManifest,'--source-commit',"
               "$SourceCommit")
    assert at("if ($SourceCommit -notmatch '^[0-9a-fA-F]{40}$')") < at("'check','--root',$RepoRoot") < stage
    verify = at("'verify-installed','--manifest',$ReleaseManifest")
    assert verify < at("from vres_os.cli import app") < at("'doctor','--allow-unconfigured','--skip-database'")
    assert at("'doctor','--allow-unconfigured','--skip-database'") < at("'pending-install.json') @{")
    for kept in ("'--dir',$PluginTarget,'--allow-extra','.vres-managed'", "install_recovery.py'),'snapshot'",
                 "Move-Item -LiteralPath $PluginBackup -Destination $PluginTarget", "$GlobalClaudeBefore",
                 "$ClaudeSettingsBefore", "resolved-dependencies.txt"):
        assert kept in text
    success = at("Write-Host 'Vres preview installed.")
    assert success < at("Database health was not checked") < at("} catch {")


# ---------------------------------------------------------------- update-specific confirmation (T4b)

def test_update_asks_an_accurate_question_that_defaults_to_no():
    text = _installer()
    branch = text.split("if ($Update) {", 1)[1].split("} else {", 1)
    update, fresh = branch[0], branch[1].split("}", 1)[0]

    prompt = re.search(r"Confirm-Choice '([^']*)' \$false\)\) \{ exit 0 \}", update)
    assert prompt, "the update confirmation must default to No and exit without changes"
    question = prompt.group(1)
    for phrase in ("existing Vres installation for this Windows user", "will NOT be checked",
                   "No PostgreSQL access is authorized", "remain blocked until separately accepted"):
        assert phrase in update, phrase
    assert "pinned commit" in question
    # The original first-install safeguard is kept for its own mode.
    assert "Confirm-Choice 'Install this preview for a disposable project and dedicated test database?' $false" in fresh
    # Confirm-Choice still needs a typed yes; an empty answer is the default (No). No bypass parameter exists.
    confirm = text.split("function Confirm-Choice", 1)[1].split("function Refresh-Path", 1)[0]
    assert "Read-Host" in confirm and "return $Default" in confirm and "@('y','yes')" in confirm
    params = text.split("param(", 1)[1].split(")", 1)[0]
    assert not re.search(r"\$(Yes|Force|Confirm|NonInteractive|AssumeYes)\b", params, re.I)


# -------------------------------------------------------------------- import smoke has no contact (T5)

def test_installer_import_smoke_and_skipped_doctor_make_no_database_or_secret_contact(tmp_path):
    smoke = re.search(r"Run \$NewPython @\('-B','-c','([^']+)'\)", _installer()).group(1)
    probe = (
        "import sys, psycopg, keyring\n"
        "calls = []\n"
        "def boom(*a, **k):\n"
        "    calls.append(1); raise SystemExit('database or secret contact attempted')\n"
        "psycopg.connect = boom\n"
        "psycopg.Connection.connect = classmethod(boom)\n"
        "keyring.get_password = boom\n"
        f"exec({smoke!r})\n"
        "print('NO_CONTACT', len(calls))\n"
    )
    env = {**os.environ, "PYTHONPATH": str(_ROOT / "src")}
    done = subprocess.run([sys.executable, "-B", "-c", probe], capture_output=True, text=True, env=env, timeout=120,
                          cwd=tmp_path)

    assert done.returncode == 0, done.stderr
    assert "NO_CONTACT 0" in done.stdout


# ------------------------------------------------------------- dependency audit report (T7, T4c)

def _report_check() -> str:
    line = re.search(r"\$PipReportCheck = '(.+)'\r?$", _installer(), re.M).group(1)
    return line.replace("''", "'")


def _run_check(tmp_path, content) -> subprocess.CompletedProcess:
    report = tmp_path / "pip-install-report.json"
    report.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
    return subprocess.run([sys.executable, "-I", "-c", _report_check(), str(report)], capture_output=True,
                          text=True, timeout=60)


_HASHED = {"metadata": {"name": "typer", "version": "0.12.5"},
           "download_info": {"url": "https://files.pythonhosted.org/packages/typer-0.12.5-py3-none-any.whl",
                             "archive_info": {"hashes": {"sha256": "0" * 64}}}}
_LOCAL = {"metadata": {"name": "vres-os", "version": "0.2.0a1"},
          "download_info": {"url": "file:///C:/release/source", "dir_info": {}}}


def test_the_dependency_report_is_validated_and_counts_entries_without_an_archive_hash(tmp_path):
    done = _run_check(tmp_path, {"version": "1", "install": [_HASHED, _LOCAL]})

    assert done.returncode == 0, done.stderr
    assert done.stdout.split() == ["2", "1"]  # two packages, one (the local staged source) without a hash


@pytest.mark.parametrize("report", [
    "not json",
    [],
    {"version": "0", "install": [_HASHED]},
    {"version": "1", "install": []},
    {"version": "1"},
    {"version": "1", "install": [{"metadata": {"version": "1"}}]},
    {"version": "1", "install": ["typer"]},
], ids=["not-json", "not-object", "wrong-version", "empty", "no-install", "no-name", "not-entry"])
def test_an_unusable_dependency_report_stops_the_installation(tmp_path, report):
    assert _run_check(tmp_path, report).returncode != 0


def _entry(name, download_info):
    return {"metadata": {"name": name, "version": "1.0"}, "download_info": download_info}


def _archive(hashes):
    return {"url": "https://files.pythonhosted.org/x.whl", "archive_info": {} if hashes is None else {"hashes": hashes}}


@pytest.mark.parametrize("download_info,missing", [
    (_archive({"sha256": "a" * 64}), 0),
    (_archive({"sha256": "ABCDEF0123456789" * 4}), 0),
    (_archive(None), 1),                                   # no hashes at all
    (_archive({}), 1),                                     # empty hash map
    (_archive({"md5": "0" * 32}), 1),                      # MD5 only
    (_archive({"sha256": "a" * 63}), 1),                   # too short
    (_archive({"sha256": "g" * 64}), 1),                   # not hexadecimal
    (_archive({"sha256": ["a" * 64]}), 1),                 # not a string
    (_archive(["sha256", "a" * 64]), 1),                   # hashes not a map
    ({"url": "file:///C:/release/source", "dir_info": {}}, 1),  # the local staged Vres source
], ids=["sha256", "sha256-upper", "no-hashes", "empty-map", "md5-only", "short", "non-hex", "non-string",
        "hashes-not-map", "local-source"])
def test_only_a_well_formed_recorded_sha256_counts_as_hash_evidence(tmp_path, download_info, missing):
    done = _run_check(tmp_path, {"version": "1", "install": [_entry("pkg", download_info)]})

    assert done.returncode == 0, done.stderr
    assert done.stdout.split() == ["1", str(missing)]


def _pip_gate(version: str) -> int:
    gate = re.search(r"\$PipVersionCheck = '(.+)'\r?$", _installer(), re.M).group(1).replace("''", "'")
    stub = f"import sys, types; sys.modules['pip'] = types.SimpleNamespace(__version__={version!r}); exec({gate!r})"
    return subprocess.run([sys.executable, "-I", "-c", stub], capture_output=True, timeout=60).returncode


@pytest.mark.parametrize("version,accepted", [
    ("22.2", False), ("22.3.1", False), ("21.0", False), ("not-a-version", False),
    ("23.0", True), ("23.2.1", True), ("24.1b1", True), ("25.0.1", True),
])
def test_the_pip_gate_requires_installation_report_schema_1_support(version, accepted):
    # Installation-report schema version 1 is stable from pip 23.0; 22.2-22.x wrote an experimental schema.
    assert (_pip_gate(version) == 0) is accepted


def test_no_unverified_claim_that_the_whole_installer_avoids_the_database():
    install, docs = _installer(), (_ROOT / "docs/INSTALL-WINDOWS.md").read_text(encoding="utf-8")
    for text in (install, docs):
        for claim in ("installation never contacts PostgreSQL", "installer never contacts PostgreSQL",
                      "Installation preflight never contacts PostgreSQL", "never contacts a database"):
            assert claim not in text, claim
    for label in ("VERIFIED DESIGN", "NOT VERIFIED", "PROHIBITED", "PENDING"):
        assert label in docs, label
    assert "No PostgreSQL access is authorized" in install and "No PostgreSQL access is authorized" in docs
    assert "schema-048 incident database" in docs


def test_installer_records_the_dependency_report_without_claiming_reproducibility():
    text = _installer()
    at = text.index

    pip = at("Run $NewPython @('-m','pip','install','--no-compile','--report',$PipReport,\"$StagedSource[$extras]\")")
    assert "$PipReport = Join-Path $NewRelease 'pip-install-report.json'" in text
    assert at("$PipVersionCheck") < at("Run $NewPython @('-I','-c',$PipVersionCheck)") < pip
    assert "(23, 0)" in text  # installation-report schema version 1 is stable from pip 23.0
    # The report is checked only after the installed package is verified, and before anything is activated.
    assert at("'verify-installed','--manifest',$ReleaseManifest") < at("Run $Python @('-I','-c',$PipReportCheck,$PipReport)")
    assert at("$PipReportCheck,$PipReport") < at("'pending-install.json') @{")
    summary = text[at("Dependency report:"):].split("\n", 1)[0]
    assert "not a hash-locked or reproducible resolution" in summary and "build" in summary
    assert "--index-url" not in text and "--extra-index-url" not in text and "--find-links" not in text


# ------------------------------------------------------------------------------- documentation (T6)

def test_docs_explain_the_database_free_installation_preflight_and_operator_update():
    text = (_ROOT / "docs/INSTALL-WINDOWS.md").read_text(encoding="utf-8")

    for phrase in ("skips database contact", "PostgreSQL: NOT CHECKED", "`vres doctor`",
                   "separate Windows PowerShell", "Close Claude Code and Codex", "pip-install-report.json",
                   "not a hash-locked", "schema-048 incident database", ".\\update.ps1 -SourceCommit <commit>"):
        assert phrase in text, phrase
