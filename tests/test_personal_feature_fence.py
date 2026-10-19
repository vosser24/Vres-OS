"""P2-A2 personal-release feature fence. Offline: no PostgreSQL, Codex, model, promotion or credential.

Every disabled operation is invoked once inside the personal profile with each of its
side-effect seams replaced by a tripwire, so a test fails if the operation got as far
as a database, a process launch, a credential store or a file write.
"""
from __future__ import annotations

import io
import json
import shutil
import sys
from importlib import resources
from pathlib import Path

import pytest
from typer.testing import CliRunner

from vres_os import (
    claude_experiment,
    cli,
    codex_handoff,
    control_preflight,
    local_secrets,
    mcp_server,
    personal_profile,
    release_inputs,
    replay,
)
from vres_os.codex_handoff import CodexHandoffService
from vres_os.config import ConfigStore, VresConfig
from vres_os.credential_broker import CredentialBroker
from vres_os.executor import ProcedureExecutorService
from vres_os.personal_profile import CapabilityDisabled
from vres_os.project import ProjectIdentity
from vres_os.replay import ReplayService

# Captured at import, before conftest pins the platform decision for each unit test.
_REAL_PERSONAL_PLATFORM = personal_profile._personal_platform
_VRES = "mcp__plugin_vres-os_vres__"
_ROOT = Path(__file__).resolve().parents[1]


def _tripwire(name: str):
    def fired(*_args, **_kwargs):
        pytest.fail(f"side effect reached: {name}")

    return fired


@pytest.fixture(autouse=True)
def _scratch_data(monkeypatch, tmp_path):
    monkeypatch.setenv("VRES_DATA_DIR", str(tmp_path / "data"))


def _output(result) -> str:
    return result.output + (getattr(result, "stderr", "") or "")


# 6. The versioned contract


def test_contract_is_versioned_and_denies_unlisted_capabilities(personal_profile):
    contract = personal_profile.describe()

    assert (contract["profile"], contract["version"], contract["default"]) == ("vres-personal", 1, "deny")
    assert contract["active"] is True
    assert {name for name, row in contract["capabilities"].items() if row["approved"]} == set()
    for name in (*personal_profile.CAPABILITIES, "anything_not_listed"):
        assert personal_profile.capability_enabled(name) is False
        with pytest.raises(CapabilityDisabled, match="disabled in the Vres personal release"):
            personal_profile.require_capability(name)


@pytest.mark.parametrize("platform,active", [("win32", True), ("linux", False)])
def test_profile_follows_the_platform_only_never_the_environment(monkeypatch, platform, active):
    for name in ("VRES_PROFILE", "VRES_PERSONAL_PROFILE", "VRES_ALLOW_CODEX", "VRES_DEVELOPER"):
        monkeypatch.setenv(name, "0" if active else "1")
    monkeypatch.setattr(personal_profile, "_personal_platform", _REAL_PERSONAL_PLATFORM)
    monkeypatch.setattr(personal_profile.sys, "platform", platform)

    assert personal_profile.personal_profile_active() is active
    assert personal_profile.capability_enabled(personal_profile.CODEX_HANDOFF_EXECUTE) is not active


# 1. Codex handoff execution


def test_codex_handoff_execute_is_refused_before_any_read_launch_or_promotion(personal_profile, monkeypatch, tmp_path):
    monkeypatch.setattr(codex_handoff, "run_bounded", _tripwire("codex process"))
    monkeypatch.setattr(CodexHandoffService, "_locate_prepared_event", _tripwire("handoff read"))
    monkeypatch.setattr(CodexHandoffService, "_claim_started", _tripwire("handoff claim"))
    service = CodexHandoffService(repository=object(), task_decisions=object(), connect_fn=_tripwire("database"))

    with pytest.raises(CapabilityDisabled, match="codex_handoff_execute"):
        service.execute(project_id=1, project_root=tmp_path, handoff_key="HANDOFF-1", session_id="S-1")
    with pytest.raises(CapabilityDisabled):
        CodexHandoffService._run_execution("codex", tmp_path, "prompt")
    with pytest.raises(CapabilityDisabled):
        service._promote(
            project_id=1, project_root=tmp_path, task_key="T-1", session_id="S-1", prepared_payload={},
            disposable_changed_paths=frozenset(), patch_file=tmp_path / "patch", postconditions=(),
        )
    assert not (tmp_path / "patch").exists()


def test_codex_handoff_execute_tool_reports_the_fence_without_touching_the_project(personal_profile, monkeypatch):
    monkeypatch.setattr(mcp_server, "_project", _tripwire("project/database"))
    monkeypatch.setattr(mcp_server, "CodexHandoffService", _tripwire("handoff service"))

    result = mcp_server.codex_handoff_execute("HANDOFF-1", "S-1")

    assert result["ok"] is False and result["reason"] == "disabled_in_personal_profile"
    assert result["task_completed"] is False and result["worktree_preserved"] is False


def test_codex_handoff_execute_tool_is_unchanged_outside_the_personal_profile(monkeypatch):
    class Reached(Exception):
        pass

    monkeypatch.setattr(mcp_server, "_project", lambda: (_ for _ in ()).throw(Reached()))

    with pytest.raises(Reached):
        mcp_server.codex_handoff_execute("HANDOFF-1", "S-1")


# 2. Unattended procedure auto-promotion


def test_direct_replay_auto_promotion_is_refused_before_assessment_or_write(personal_profile, monkeypatch):
    monkeypatch.setattr(ReplayService, "assess", _tripwire("assessment"))
    monkeypatch.setattr(replay, "_connect", _tripwire("database"))

    with pytest.raises(CapabilityDisabled, match="procedure_auto_promotion"):
        ReplayService().promote_attested("REPLAY-1")


def _finalize(monkeypatch, tmp_path, promote):
    monkeypatch.setattr(ReplayService, "attest", lambda self, **_kw: {"id": 7})
    monkeypatch.setattr(
        ReplayService, "assess",
        lambda self, _key: {"auto_promote": True, "reason": "Pareto-superior", "quality_basis": "replay"},
    )
    monkeypatch.setattr(ReplayService, "promote_attested", promote)
    return ProcedureExecutorService().finalize_replay(
        replay_key="REPLAY-1", request_key="REQ-1", task_key="T-1", project_id=1, root=tmp_path
    )


def test_finalize_replay_keeps_the_assessment_but_never_promotes_in_the_personal_profile(
    personal_profile, monkeypatch, tmp_path
):
    result = _finalize(monkeypatch, tmp_path, _tripwire("promotion"))

    assert result["decision"] == "not_promoted" and result["attestation_id"] == 7
    assert result["auto_promote"] is False and "disabled in the Vres personal release" in result["reason"]
    assert result["quality_basis"] == "replay"


def test_finalize_replay_promotion_is_unchanged_outside_the_personal_profile(monkeypatch, tmp_path):
    promoted = []

    def promote(self, key):
        promoted.append(key)
        return {"decision": "auto_promoted", "preferred_version": 2, "replay_key": key}

    result = _finalize(monkeypatch, tmp_path, promote)

    assert promoted == ["REPLAY-1"] and result["decision"] == "auto_promoted"


# 3. Live model experiments


def test_live_model_experiment_is_refused_before_any_executable_or_model_call(personal_profile, monkeypatch):
    for name in ("assert_not_nested", "find_native_claude", "run_bounded", "_claude_version"):
        monkeypatch.setattr(claude_experiment, name, _tripwire(name))

    with pytest.raises(CapabilityDisabled, match="model_experiment_execution"):
        claude_experiment.run_claude_experiment(prompt="hello", family="sonnet", effort="low")


def test_model_experiment_cli_is_refused_before_project_database_or_model_access(
    personal_profile, monkeypatch, tmp_path
):
    monkeypatch.setattr(cli, "discover_project", _tripwire("project discovery"))
    monkeypatch.setattr(cli, "Repository", _tripwire("database"))
    monkeypatch.setattr(claude_experiment, "run_claude_experiment", _tripwire("model call"))
    output = tmp_path / "result.txt"

    result = CliRunner().invoke(cli.app, [
        "model-experiment", "run", "--task-key", "T-1", "--phase", "plan", "--family", "sonnet",
        "--effort", "low", "--prompt-file", str(tmp_path / "prompt.txt"), "--output-file", str(output),
    ])

    assert result.exit_code == 2, _output(result)
    assert "model_experiment_execution" in _output(result)
    assert not output.exists()


# 4. Legacy secret aliases; Credential Broker stays available


class _NoStore:
    def __init__(self):
        self.calls = []

    def get(self, key):
        self.calls.append(("get", key))
        pytest.fail("credential store read")

    def set(self, key, value):
        self.calls.append(("set", key))
        pytest.fail("credential store write")

    def delete(self, key):
        self.calls.append(("delete", key))
        pytest.fail("credential store delete")


def test_legacy_secret_alias_service_is_refused_without_touching_stored_values(personal_profile, monkeypatch, tmp_path):
    monkeypatch.setattr(local_secrets, "run_bounded", _tripwire("process launch"))
    store = _NoStore()
    project = ProjectIdentity(tmp_path, "project-key", "Project", None, None)
    manager = local_secrets.LocalSecretManager(project, store=store)
    calls = [
        lambda: manager.set("api", "value"),
        lambda: manager.get("api"),
        lambda: manager.delete("api"),
        lambda: manager.list(),
        lambda: manager.environment(["API=api"]),
        lambda: manager.run(["tool"], ["API=api"]),
        lambda: manager.materialize("api"),
    ]
    for call in calls:
        with pytest.raises(CapabilityDisabled, match="legacy_secret_aliases"):
            call()

    assert store.calls == []
    assert not (tmp_path / "data").exists() or not any((tmp_path / "data").rglob("*"))
    assert not (tmp_path / ".vres").exists()


@pytest.mark.parametrize("command", [["list"], ["set", "api"], ["delete", "api", "--yes"], ["cleanup"]])
def test_legacy_secret_cli_commands_are_refused_before_they_run(personal_profile, monkeypatch, command):
    monkeypatch.setattr(cli, "LocalSecretManager", _tripwire("legacy secret manager"))
    monkeypatch.setattr(cli.getpass, "getpass", _tripwire("secret prompt"))

    result = CliRunner().invoke(cli.app, ["secret", *command])

    assert result.exit_code == 2, _output(result)
    assert "legacy_secret_aliases" in _output(result)


def test_credential_broker_resources_and_cleanup_remain_available(personal_profile, tmp_path):
    project = ProjectIdentity(tmp_path, "project-key", "Project", None, None)
    store = _NoStore()
    broker = CredentialBroker(store=store, registry_path=tmp_path / "credential-registry.json")

    assert broker.list_resources(project) == []
    assert broker.cleanup_materialized(project) == 0
    assert local_secrets.LocalSecretManager(project, store=store).cleanup_materialized() == 0
    assert store.calls == []


# 7. Control preflight while Vres is unconfigured


def _preflight(monkeypatch, capsys, tool_name, *, configured):
    ConfigStore().save(VresConfig(configured=configured))
    answers = {
        "read_only_hold_for_session": None,
        "contaminated_sessions_for_host_session": [],
        "work_scope_for_agent": None,
    }
    for name, answer in answers.items():
        if configured:
            monkeypatch.setattr(control_preflight, name, lambda *_a, answer=answer: answer)
        else:
            monkeypatch.setattr(control_preflight, name, _tripwire(f"database: {name}"))
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool_name, "session_id": "host-session", "tool_input": {}}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    assert control_preflight.main() == 0
    out = capsys.readouterr().out.strip()
    return json.loads(out) if out else None


@pytest.mark.parametrize("tool", ["task_begin", "task_complete", "knowledge_promote", "codex_handoff_execute"])
def test_unconfigured_vres_denies_mutation_capable_governed_tools(monkeypatch, capsys, tool):
    decision = _preflight(monkeypatch, capsys, _VRES + tool, configured=False)

    assert decision["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "not configured" in decision["hookSpecificOutput"]["permissionDecisionReason"]


@pytest.mark.parametrize(
    "tool",
    [_VRES + "start_vres", _VRES + "vres_status", _VRES + "task_open_list", "Bash", "Write", "mcp__other__tool"],
    ids=["secure-setup", "status", "read-only-list", "host-bash", "host-write", "other-mcp-server"],
)
def test_unconfigured_vres_keeps_setup_diagnostics_and_unrelated_tools(monkeypatch, capsys, tool):
    assert _preflight(monkeypatch, capsys, tool, configured=False) is None


def test_configured_governed_tool_path_is_unchanged(monkeypatch, capsys):
    assert _preflight(monkeypatch, capsys, _VRES + "task_begin", configured=True) is None


# 5. No production credential override (see also tests/test_secret_store_contract.py)


def test_secret_store_source_has_no_environment_override():
    source = (_ROOT / "src/vres_os/secrets.py").read_text(encoding="utf-8")

    assert "os.environ" not in source and "VRES_SECRET_" not in source


# 8. Release inputs


def _release_tree(tmp_path: Path) -> Path:
    root = tmp_path / "source"
    target = root / release_inputs.MIGRATIONS_DIR
    target.mkdir(parents=True)
    for item in resources.files("vres_os").joinpath("migrations").iterdir():
        if item.name.endswith(".sql"):
            shutil.copyfile(str(item), target / item.name)
    (root / "src/vres_os/cli.py").write_text("# ordinary source\n", encoding="utf-8")
    return root


def test_accepted_tree_and_pinned_migrations_are_a_valid_personal_release_input(tmp_path):
    assert release_inputs.release_input_problems(_ROOT) == []
    assert release_inputs.release_input_problems(_release_tree(tmp_path)) == []
    assert sorted(release_inputs.PERSONAL_MIGRATION_PINS)[-1].startswith("041_")
    assert len(release_inputs.PERSONAL_MIGRATION_PINS) == 41


@pytest.mark.parametrize(
    "change,expected",
    [
        (lambda r: (r / release_inputs.MIGRATIONS_DIR / "042_experience_policy.sql").write_text("SELECT 1;"),
         "042_experience_policy.sql is above 041"),
        (lambda r: (r / release_inputs.MIGRATIONS_DIR / "048_source_effective_trust.sql").write_text("SELECT 1;"),
         "048_source_effective_trust.sql is above 041"),
        (lambda r: (r / release_inputs.MIGRATIONS_DIR / "001_initial.sql").write_text("-- edited\n"),
         "001_initial.sql differs from its pinned"),
        (lambda r: (r / release_inputs.MIGRATIONS_DIR / "041_experience_retrieval_observability.sql").unlink(),
         "pinned migration 041_experience_retrieval_observability.sql is missing"),
        (lambda r: (r / release_inputs.MIGRATIONS_DIR / "017a_hotfix.sql").write_text("SELECT 1;"),
         "not one of the pinned"),
    ],
    ids=["042", "048", "edited-001", "missing-041", "unpinned"],
)
def test_migration_changes_make_the_tree_an_invalid_release_input(tmp_path, change, expected):
    root = _release_tree(tmp_path)
    change(root)

    problems = release_inputs.release_input_problems(root)

    assert any(expected in p for p in problems), problems
    assert release_inputs.main(["--root", str(root)]) == 1


@pytest.mark.parametrize(
    "path,label",
    [
        ("scripts/c2b_shadow_guard.py", "C2B/R0"),
        ("scripts/c2b_r0_read.py", "C2B/R0"),
        ("tests/test_c2b_r0_reader.py", "C2B/R0"),
        ("docs/c2b-r0-operator-procedure.md", "C2B/R0"),
        ("benchmarks/experience_e7/manifest.json", "F2"),
        ("scripts/ci_pg_integration.py", "F2"),
        ("src/vres_os/experience_benchmark_runtime.py", "F2"),
        ("src/vres_os/source_trust_read.py", "F2"),
        ("tests/integration/pg_run_guard.py", "F2"),
        ("tests/integration/test_e7_b4b_security_hardening.py", "F2"),
        ("docs/architecture/EXPERIENCE-INTELLIGENCE-E7-CONTRACT-2026-10-06.md", "F2"),
        ("tests/test_control_compat_048_offline.py", "C2A"),
    ],
)
def test_experimental_files_make_the_tree_an_invalid_release_input(tmp_path, path, label):
    root = _release_tree(tmp_path)
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("experimental\n", encoding="utf-8")

    assert release_inputs.release_input_problems(root) == [
        f"{label} experimental file {path} must not be part of the personal release"
    ]


def test_installer_validates_release_inputs_before_creating_anything():
    installer = (_ROOT / "install.ps1").read_text(encoding="utf-8")
    check = installer.index("src\\vres_os\\release_inputs.py")

    assert installer[installer.rfind("\n", 0, check) + 1:check].startswith("Run $Python @('-I'")
    assert check < installer.index("New-Item -ItemType Directory -Force -Path $InstallRoot")
    assert check < installer.index("'-m','pip','install'")
    gate = (_ROOT / "scripts/release_gate.py").read_text(encoding="utf-8")
    assert gate.index("release_input_problems(ROOT)") < gate.index("migration-baseline.json")
