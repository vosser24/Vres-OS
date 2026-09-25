import copy
import hashlib
import json
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

import vres_os.claude_experiment as producer
from vres_os import processes
from vres_os.claude_experiment import (
    NESTED_ENV_MARKERS,
    OVERRIDE_ENV_MARKERS,
    ClaudeExperimentError,
    parse_claude_result,
    run_claude_experiment,
)
from vres_os.model_experiments import _host_evidence
from vres_os.processes import ProcessResult

COST = "0.0024652000000000003"
PROMPT = "Reply with exactly: OK"
PROMPT_DIGEST = hashlib.sha256(PROMPT.encode("utf-8")).hexdigest()

# Sanitized from a real `claude 2.1.281 --safe-mode --print --output-format json` capture
# (Sonnet, effort medium, prompt "Reply with exactly: OK"). Only the session/result ids are
# replaced; the schema, key order and the float-artifact cost text are as observed.
_CAPTURED = {
    "duration_api_ms": 723,
    "stop_reason": "end_turn",
    "session_id": "00000000-0000-4000-8000-00000000c0de",
    "total_cost_usd": "@@COST@@",
    "usage": {
        "input_tokens": 2,
        "cache_creation_input_tokens": 533,
        "cache_read_input_tokens": 1446,
        "output_tokens": 4,
        "output_tokens_details": {"thinking_tokens": 0},
        "server_tool_use": {"web_search_requests": 0, "web_fetch_requests": 0},
        "service_tier": "standard",
    },
    "modelUsage": {
        "claude-sonnet-5": {
            "inputTokens": 2,
            "outputTokens": 4,
            "cacheReadInputTokens": 1446,
            "cacheCreationInputTokens": 533,
            "webSearchRequests": 0,
            "costUSD": "@@COST@@",
            "contextWindow": 1000000,
            "maxOutputTokens": 128000,
            "thinkingTokens": 0,
            "canonicalModel": "claude-sonnet-5",
            "provider": "firstParty",
            "costBasis": "list",
        }
    },
    "permission_denials": [],
    "terminal_reason": "completed",
    "is_error": False,
    "num_turns": 1,
    "subtype": "success",
    "result": "OK",
    "type": "result",
    "duration_ms": 788,
    "uuid": "00000000-0000-4000-8000-00000000beef",
}


def envelope_text(mutate=None, *, cost=COST):
    """Render the captured envelope; a "@@RAW:<text>@@" string becomes that raw JSON token."""
    data = copy.deepcopy(_CAPTURED)
    if mutate:
        mutate(data)
    text = json.dumps(data).replace('"@@COST@@"', cost)
    return re.sub(r'"@@RAW:(.*?)@@"', lambda m: m.group(1), text)


def parse(text=None, **overrides):
    kwargs = dict(
        family="sonnet",
        effort="medium",
        input_digest=PROMPT_DIGEST,
        runtime_ms=42,
        claude_code_version="2.1.281",
    )
    return parse_claude_result(envelope_text() if text is None else text, **(kwargs | overrides))


def _model(data):
    return data["modelUsage"]["claude-sonnet-5"]


def _rename_model(data, name, *, canonical=None):
    entry = data["modelUsage"].pop("claude-sonnet-5")
    entry["canonicalModel"] = canonical or name
    data["modelUsage"][name] = entry


# ---------------------------------------------------------------- parsing (fail closed)


def test_captured_envelope_parses_to_exact_host_observation():
    obs = parse()
    assert obs.physical_model == "claude-sonnet-5" and obs.requested_family == "sonnet"
    assert obs.host_result_id.endswith("beef") and obs.host_session_id.endswith("c0de")
    assert (obs.input_tokens, obs.output_tokens) == (2, 4)
    assert (obs.cache_read_input_tokens, obs.cache_creation_input_tokens) == (1446, 533)
    assert obs.thinking_tokens == 0 and obs.context_window == 1_000_000
    assert obs.host_cost_usd == obs.host_total_cost_usd == COST  # exact host text, no float rounding
    assert obs.estimated_cost == Decimal("0.002465")
    assert obs.input_digest == PROMPT_DIGEST
    assert obs.output_digest == hashlib.sha256(b"OK").hexdigest()
    assert obs.host_provider_label == "firstParty" and obs.host_cost_basis == "list"
    assert obs.claude_code_version == "2.1.281"
    assert obs.host_model_usage_raw["costUSD"] == COST


def test_adapter_runtime_is_distinct_from_host_durations():
    obs = parse(runtime_ms=5)
    evidence = obs.execution_evidence()
    assert evidence["runtime_ms"] == 5 and evidence["runtime_source"] == "adapter_monotonic"
    assert evidence["host_duration_ms"] == 788 and evidence["host_duration_api_ms"] == 723


def test_evidence_is_recordable_and_never_uses_provider_response_id():
    obs = parse()
    evidence = obs.execution_evidence()
    assert "provider_response_id" not in evidence
    assert evidence["evidence_kind"] == "claude_code_host"
    assert evidence["adapter"] == "vres-claude-code-print"
    assert evidence["identity_source"] == evidence["usage_source"] == "claude_code_host_result"
    assert evidence["host_result_id"] == obs.host_result_id
    assert _host_evidence(
        provider="claude",
        model=obs.physical_model,
        effort="medium",
        success=True,
        runtime_ms=obs.runtime_ms,
        input_tokens=obs.input_tokens,
        output_tokens=obs.output_tokens,
        execution_evidence=evidence,
        estimated_cost=obs.estimated_cost,
    )


def test_integer_cost_and_missing_optional_fields_are_accepted():
    def mutate(data):
        del data["duration_ms"], data["duration_api_ms"], _model(data)["thinkingTokens"]

    obs = parse(envelope_text(mutate, cost="0"))
    assert obs.host_cost_usd == "0" and obs.estimated_cost == Decimal("0.000000")
    assert obs.host_duration_ms is None and obs.thinking_tokens == 0  # from usage.output_tokens_details


def _set(path, value):
    def mutate(data):
        node = data
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value

    return mutate


def _delete(path):
    def mutate(data):
        node = data
        for key in path[:-1]:
            node = node[key]
        del node[path[-1]]

    return mutate


def _add_model(data):
    data["modelUsage"]["claude-opus-5-5"] = dict(_model(data), canonicalModel="claude-opus-5-5")


def _zero(data, pairs):
    for model_key, usage_key in pairs:
        _model(data)[model_key] = 0
        data["usage"][usage_key] = 0


BAD_ENVELOPES = {
    "subtype error": (_set(["subtype"], "error_max_turns"), "successful"),
    "not result type": (_set(["type"], "assistant"), "successful"),
    "is_error true": (_set(["is_error"], True), "error result"),
    "is_error missing": (_delete(["is_error"]), "error result"),
    "two turns": (_set(["num_turns"], 2), "one turn"),
    "bool turn": (_set(["num_turns"], True), "one turn"),
    "result not string": (_set(["result"], None), "result text"),
    "result surrogate": (_set(["result"], "\ud800"), "UTF-8"),
    "session missing": (_delete(["session_id"]), "session_id"),
    "session blank": (_set(["session_id"], ""), "session_id"),
    "uuid missing": (_delete(["uuid"]), "uuid"),
    "uuid whitespace": (_set(["uuid"], "a b"), "uuid"),
    "wrong family opus": (lambda d: _rename_model(d, "claude-opus-5-5"), "requested family"),
    "haiku": (lambda d: _rename_model(d, "claude-haiku-5"), "requested family"),
    "fable": (lambda d: _rename_model(d, "claude-fable-1"), "requested family"),
    "alias not physical": (lambda d: _rename_model(d, "sonnet"), "requested family"),
    "two models": (_add_model, "exactly one physical model"),
    "no models": (_set(["modelUsage"], {}), "exactly one physical model"),
    "canonical mismatch": (_set(["modelUsage", "claude-sonnet-5", "canonicalModel"], "claude-sonnet-4"), "canonicalModel"),
    "canonical missing": (_delete(["modelUsage", "claude-sonnet-5", "canonicalModel"]), "canonicalModel"),
    "provider mismatch": (_set(["modelUsage", "claude-sonnet-5", "provider"], "bedrock"), "firstParty"),
    "provider missing": (_delete(["modelUsage", "claude-sonnet-5", "provider"]), "firstParty"),
    "cost basis missing": (_delete(["modelUsage", "claude-sonnet-5", "costBasis"]), "costBasis"),
    "zero output": (lambda d: _zero(d, [("outputTokens", "output_tokens")]), "no observed usage"),
    "zero input": (
        lambda d: _zero(
            d,
            [
                ("inputTokens", "input_tokens"),
                ("cacheReadInputTokens", "cache_read_input_tokens"),
                ("cacheCreationInputTokens", "cache_creation_input_tokens"),
            ],
        ),
        "no observed usage",
    ),
    "usage input mismatch": (_set(["usage", "input_tokens"], 3), "disagrees"),
    "usage cache read mismatch": (_set(["usage", "cache_read_input_tokens"], 1), "disagrees"),
    "usage missing": (_delete(["usage"]), "top-level usage"),
    "fractional tokens": (_set(["modelUsage", "claude-sonnet-5", "inputTokens"], "@@RAW:2.5@@"), "integer"),
    "cost as string": (_set(["modelUsage", "claude-sonnet-5", "costUSD"], "0.0024652000000000003"), "costUSD"),
    "negative tokens": (_set(["modelUsage", "claude-sonnet-5", "inputTokens"], -1), "integer"),
    "thinking mismatch": (_set(["usage", "output_tokens_details", "thinking_tokens"], 9), "thinking"),
    "context window zero": (_set(["modelUsage", "claude-sonnet-5", "contextWindow"], 0), "contextWindow"),
    "negative duration": (_set(["duration_ms"], -1), "duration_ms"),
    "float duration": (_set(["duration_api_ms"], "12"), "duration_api_ms"),
    "model cost missing": (_delete(["modelUsage", "claude-sonnet-5", "costUSD"]), "costUSD"),
    "total cost missing": (_delete(["total_cost_usd"]), "total_cost_usd"),
    "model/total cost mismatch": (_set(["modelUsage", "claude-sonnet-5", "costUSD"], "@@RAW:0.5@@"), "disagree"),
    "model cost negative": (_set(["modelUsage", "claude-sonnet-5", "costUSD"], "@@RAW:-0.5@@"), "costUSD"),
}


@pytest.mark.parametrize("name", BAD_ENVELOPES)
def test_parser_rejects_untrustworthy_envelopes(name):
    mutate, message = BAD_ENVELOPES[name]
    with pytest.raises(ClaudeExperimentError, match=message):
        parse(envelope_text(mutate))


@pytest.mark.parametrize(
    "cost",
    ["-0.1", "NaN", "Infinity", "-Infinity", "1e999999", "100000000"],
)
def test_parser_rejects_negative_non_finite_or_unstorable_cost(cost):
    with pytest.raises(ClaudeExperimentError):
        parse(envelope_text(cost=cost))


@pytest.mark.parametrize(
    "text",
    [
        "",
        "not json",
        "[]",
        '"result"',
        envelope_text() + "\n" + envelope_text(),
        envelope_text() + " trailing warning",
        "warning: something\n" + envelope_text(),
        envelope_text().replace('"type": "result"', '"type": "result", "type": "result"'),
        "[earlier output omitted]\n" + envelope_text(),
    ],
)
def test_parser_requires_exactly_one_json_result_object(text):
    with pytest.raises(ClaudeExperimentError):
        parse(text)


def test_parser_rejects_unsupported_family_and_effort():
    with pytest.raises(ValueError, match="sonnet and opus"):
        parse(family="fable")
    with pytest.raises(ValueError, match="effort"):
        parse(effort="extreme")


def test_raw_model_usage_entry_is_dropped_when_unsafe():
    def mutate(data):
        _model(data)["note"] = "password = hunter2hunter2"

    assert parse(envelope_text(mutate)).host_model_usage_raw is None


# ---------------------------------------------------------------- running


@pytest.fixture
def harness(monkeypatch, tmp_path):
    for name in (*NESTED_ENV_MARKERS, *OVERRIDE_ENV_MARKERS):
        monkeypatch.delenv(name, raising=False)
    exe = tmp_path / "bin" / "claude.exe"
    exe.parent.mkdir()
    exe.write_bytes(b"")
    monkeypatch.setattr(producer.shutil, "which", lambda name: str(exe))
    state = SimpleNamespace(exe=exe, calls=[], reply=ProcessResult(True, envelope_text(), 0), version="2.1.281 (Claude Code)")

    def fake(args, **kwargs):
        if args[1:] == ["--version"]:
            return ProcessResult(True, state.version, 0)
        kwargs["cwd_listing"] = sorted(p.name for p in Path(kwargs["cwd"]).iterdir())
        state.calls.append((args, kwargs))
        return state.reply

    monkeypatch.setattr(producer, "run_bounded", fake)
    ticks = iter([1_000_000_000, 1_042_900_000])
    monkeypatch.setattr(producer, "time", SimpleNamespace(monotonic_ns=lambda: next(ticks)))
    return state


def test_run_uses_exact_argv_stdin_prompt_empty_cwd_and_no_shell(harness, tmp_path):
    obs = run_claude_experiment(prompt=PROMPT, family="sonnet", effort="medium", timeout=60)
    (args, kwargs), = harness.calls
    assert args == [
        str(harness.exe),
        "--safe-mode",
        "--print",
        "--model",
        "sonnet",
        "--effort",
        "medium",
        "--output-format",
        "json",
        "--max-turns",
        "1",
        "--permission-prompts",
        "none",
        "--tools",
        "",
        "--disallowedTools",
        "mcp__*",
        "--no-session-persistence",
    ]
    assert "--bare" not in args and isinstance(args, list)
    assert kwargs["prompt"] == PROMPT  # delivered through run_bounded stdin, never argv
    assert PROMPT not in " ".join(args)
    assert kwargs["redact_output"] is False and kwargs["timeout"] == 60
    assert "shell" not in kwargs and not kwargs.get("stdin_devnull")
    assert kwargs["cwd_listing"] == []  # fresh empty directory
    assert Path(kwargs["cwd"]).resolve() != Path.cwd().resolve()
    assert not Path(kwargs["cwd"]).exists()  # temporary directory removed afterwards
    assert obs.runtime_ms == 42 and obs.host_duration_ms == 788  # adapter clock, not host clock
    assert obs.input_digest == PROMPT_DIGEST
    assert obs.claude_code_version == "2.1.281"


def test_producer_reuses_the_shared_bounded_runner():
    source = Path(producer.__file__).read_text(encoding="utf-8")
    assert "from .processes import" in source and "run_bounded" in source
    assert "subprocess" not in source and "shell=" not in source
    assert producer.run_bounded is processes.run_bounded


@pytest.mark.parametrize("marker", [*NESTED_ENV_MARKERS, *OVERRIDE_ENV_MARKERS])
def test_run_refuses_nested_claude_environment_without_scrubbing(harness, monkeypatch, marker):
    monkeypatch.setenv(marker, "1")
    with pytest.raises(ClaudeExperimentError, match=marker):
        run_claude_experiment(prompt=PROMPT, family="sonnet", effort="medium")
    assert harness.calls == []


@pytest.mark.parametrize("name", ["claude.cmd", "claude.bat", "claude.ps1"])
def test_wrapper_executables_are_rejected(harness, monkeypatch, tmp_path, name):
    wrapper = tmp_path / name
    wrapper.write_bytes(b"")
    monkeypatch.setattr(producer.shutil, "which", lambda _name: str(wrapper))
    with pytest.raises(ClaudeExperimentError, match="wrapper"):
        run_claude_experiment(prompt=PROMPT, family="sonnet", effort="medium")
    assert harness.calls == []


def test_missing_or_non_file_executable_is_rejected(harness, monkeypatch, tmp_path):
    monkeypatch.setattr(producer.shutil, "which", lambda _name: None)
    with pytest.raises(ClaudeExperimentError, match="not found"):
        run_claude_experiment(prompt=PROMPT, family="sonnet", effort="medium")
    monkeypatch.setattr(producer.shutil, "which", lambda _name: str(tmp_path / "missing" / "claude.exe"))
    with pytest.raises(ClaudeExperimentError, match="regular file"):
        run_claude_experiment(prompt=PROMPT, family="sonnet", effort="medium")


@pytest.mark.parametrize(
    "prompt",
    [
        pytest.param("", id="empty"),
        pytest.param("   ", id="blank"),
        pytest.param("api_key = abcdefghijklmnop", id="api-key"),
        pytest.param("Authorization: Bearer abcdefghijklmnop", id="bearer"),
        pytest.param("x" * (64 * 1024 + 1), id="oversized"),
    ],
)
def test_unsafe_prompts_never_reach_claude(harness, prompt):
    with pytest.raises(ClaudeExperimentError):
        run_claude_experiment(prompt=prompt, family="sonnet", effort="medium")
    assert harness.calls == []


@pytest.mark.parametrize("family", ["fable", "haiku", "SONNET", ""])
def test_only_sonnet_and_opus_can_run(harness, family):
    with pytest.raises(ClaudeExperimentError, match="sonnet and opus"):
        run_claude_experiment(prompt=PROMPT, family=family, effort="medium")
    assert harness.calls == []


@pytest.mark.parametrize(
    "code,output,message",
    [
        (1, "boom", "exited with code 1"),
        (124, "Worker timed out; execution terminated.", "timed out"),
        (125, "Worker exceeded its output budget; execution terminated.", "output budget"),
    ],
)
def test_process_failures_are_rejected(harness, code, output, message):
    harness.reply = ProcessResult(False, output, code)
    with pytest.raises(ClaudeExperimentError, match=message):
        run_claude_experiment(prompt=PROMPT, family="sonnet", effort="medium")


def test_zero_exit_with_stderr_noise_is_rejected(harness):
    harness.reply = ProcessResult(True, "warning: something\n" + envelope_text(), 0)
    with pytest.raises(ClaudeExperimentError, match="exactly one JSON"):
        run_claude_experiment(prompt=PROMPT, family="sonnet", effort="medium")


def test_unreadable_version_is_rejected(harness):
    harness.version = "claude something"
    with pytest.raises(ClaudeExperimentError, match="version"):
        run_claude_experiment(prompt=PROMPT, family="sonnet", effort="medium")
    assert harness.calls == []


def test_opus_family_maps_to_opus_model(harness):
    harness.reply = ProcessResult(
        True,
        envelope_text(lambda d: _rename_model(d, "claude-opus-5-5")),
        0,
    )
    obs = run_claude_experiment(prompt=PROMPT, family="opus", effort="high")
    assert obs.physical_model == "claude-opus-5-5"
    assert harness.calls[0][0][3:7] == ["--model", "opus", "--effort", "high"]


# ---------------------------------------------------------------- CLI

runner = CliRunner()


class FakeService:
    def __init__(self):
        self.recorded = []
        self.open_error = None
        FakeService.last = self

    def assert_task_open(self, task_key, project_id):
        if self.open_error:
            raise self.open_error

    def record_host_run(self, **kwargs):
        self.recorded.append(kwargs)
        return 77


@pytest.fixture
def cli(monkeypatch, tmp_path):
    import vres_os.cli as cli_module
    import vres_os.model_experiments as experiments

    for name in (*NESTED_ENV_MARKERS, *OVERRIDE_ENV_MARKERS):
        monkeypatch.delenv(name, raising=False)
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(cli_module, "discover_project", lambda _start=".": SimpleNamespace(root=project_root))
    monkeypatch.setattr(cli_module, "Repository", lambda: SimpleNamespace(ensure_project=lambda _p: 7))
    monkeypatch.setattr(experiments, "ModelExperimentService", FakeService)
    calls = []

    def fake_run(**kwargs):
        calls.append(kwargs)
        return parse(runtime_ms=42)

    monkeypatch.setattr(producer, "run_claude_experiment", fake_run)
    prompt = project_root / "prompt.txt"
    prompt.write_bytes(PROMPT.encode("utf-8"))
    return SimpleNamespace(app=cli_module.app, root=project_root, prompt=prompt, calls=calls)


def _run(cli, **overrides):
    values = {
        "--task-key": "TASK-1",
        "--phase": "analyze",
        "--family": "sonnet",
        "--effort": "medium",
        "--prompt-file": str(cli.prompt),
        "--output-file": str(cli.root / "out" / "result.txt"),
    } | overrides
    (cli.root / "out").mkdir(exist_ok=True)
    args = ["model-experiment", "run"]
    for key, value in values.items():
        if value is not None:
            args += [key, str(value)]
    return runner.invoke(cli.app, args)


def test_cli_successful_run_writes_exact_bytes_records_and_prints_summary(cli):
    result = _run(cli)
    assert result.exit_code == 0, result.output
    summary = json.loads(result.stdout)
    output = cli.root / "out" / "result.txt"
    assert output.read_bytes() == b"OK"
    (recorded,) = FakeService.last.recorded
    assert recorded["output_digest"] == summary["output_digest"] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert recorded["input_digest"] == summary["input_digest"] == PROMPT_DIGEST
    assert recorded["estimated_cost"] == Decimal("0.002465") and recorded["project_id"] == 7
    assert recorded["provider"] == "claude" and recorded["model"] == "claude-sonnet-5"
    assert recorded["execution_evidence"]["host_cost_usd"] == COST
    assert cli.calls == [dict(prompt=PROMPT, family="sonnet", effort="medium", timeout=300.0)]
    for key in (
        "run_id",
        "physical_model",
        "requested_family",
        "effort",
        "input_digest",
        "output_digest",
        "runtime_ms",
        "input_tokens",
        "output_tokens",
        "cache_read_input_tokens",
        "cache_creation_input_tokens",
        "estimated_cost",
        "host_result_id",
    ):
        assert key in summary
    assert summary["run_id"] == 77 and summary["estimated_cost"] == "0.002465"
    assert summary["policy_mutation"] == "none" and "estimate" in summary["cost_semantics"]
    assert "evidence" not in result.stdout and COST in result.stdout  # exact cost only; no raw evidence dump


def test_cli_record_failure_after_paid_call_preserves_result_and_says_so(cli, monkeypatch):
    import vres_os.model_experiments as experiments

    class DownService(FakeService):
        def record_host_run(self, **kwargs):
            self.recorded.append("attempted")
            raise RuntimeError("database is down password = hunter2hunter2")

    monkeypatch.setattr(experiments, "ModelExperimentService", DownService)
    result = _run(cli)
    output = cli.root / "out" / "result.txt"
    assert result.exit_code == 1
    assert output.read_bytes() == b"OK"  # exact paid result, intact
    assert len(cli.calls) == 1  # never retried
    assert DownService.last.recorded == ["attempted"]  # one attempt, no fake model_run
    text = " ".join(result.output.split())
    assert "Claude call succeeded" in text and "preserved at out/result.txt" in text
    assert "model_run was NOT recorded" in text
    assert "Do not treat this file as trusted experiment evidence" in text
    assert "not retried" in text
    assert "hunter2hunter2" not in result.output  # secrets are redacted from the reason
    assert "00000000-0000-4000-8000-00000000beef" not in result.output  # host_result_id
    assert "execution_evidence" not in result.output and COST not in result.output


@pytest.mark.parametrize(
    "failure",
    [
        ClaudeExperimentError("Claude Code exited with code 1: boom"),
        ClaudeExperimentError("Claude Code timed out"),
        ValueError("Claude Code output is not exactly one JSON object"),
    ],
)
def test_cli_failure_before_a_successful_call_creates_no_output_file(cli, monkeypatch, failure):
    def failing_run(**kwargs):
        cli.calls.append(kwargs)
        raise failure

    monkeypatch.setattr(producer, "run_claude_experiment", failing_run)
    result = _run(cli)
    assert result.exit_code == 1 and len(cli.calls) == 1
    assert not (cli.root / "out" / "result.txt").exists()
    assert FakeService.last.recorded == []
    assert "NOT recorded" not in result.output  # nothing was paid for, so no partial-failure notice


def test_cli_output_is_create_only(cli):
    output = cli.root / "out" / "result.txt"
    (cli.root / "out").mkdir()
    output.write_bytes(b"precious")
    result = _run(cli)
    assert result.exit_code != 0
    assert output.read_bytes() == b"precious" and cli.calls == []


@pytest.mark.parametrize("target", ["--prompt-file", "--output-file"])
def test_cli_paths_must_stay_inside_the_project(cli, tmp_path, target):
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"x")
    result = _run(cli, **{target: outside if target == "--prompt-file" else tmp_path / "new.txt"})
    assert result.exit_code != 0 and "inside the current project" in result.output
    assert cli.calls == []
    result = _run(cli, **{target: cli.root / ".." / ("outside.txt" if target == "--prompt-file" else "new.txt")})
    assert result.exit_code != 0 and cli.calls == []


def test_cli_rejects_symlink_prompt_and_output(cli, tmp_path):
    link = cli.root / "link.txt"
    try:
        link.symlink_to(cli.prompt)
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links are not available")
    assert _run(cli, **{"--prompt-file": link}).exit_code != 0
    assert _run(cli, **{"--output-file": link}).exit_code != 0
    assert cli.calls == []


@pytest.mark.parametrize("target", ["--prompt-file", "--output-file"])
def test_cli_symlink_check_is_applied_even_where_symlinks_cannot_be_created(cli, monkeypatch, target):
    flagged = cli.prompt if target == "--prompt-file" else cli.root / "out" / "result.txt"
    real_is_symlink = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda self: self == flagged or real_is_symlink(self))
    result = _run(cli)
    assert result.exit_code != 0 and "symbolic link" in result.output and cli.calls == []


def test_cli_prompt_must_be_a_regular_file(cli):
    result = _run(cli, **{"--prompt-file": cli.root / "out"})
    assert result.exit_code != 0 and "regular file" in result.output and cli.calls == []


def test_cli_refuses_nested_claude_session(cli, monkeypatch):
    monkeypatch.setenv("CLAUDECODE", "1")
    result = _run(cli)
    assert result.exit_code == 1 and "inside a Claude Code session" in result.output
    assert cli.calls == [] and not (cli.root / "out" / "result.txt").exists()


def test_cli_checks_task_before_paying_for_a_run(cli, monkeypatch):
    import vres_os.model_experiments as experiments

    class Boom(FakeService):
        def __init__(self):
            super().__init__()
            self.open_error = ValueError("Host model experiment requires an unfinished persistent task")

    monkeypatch.setattr(experiments, "ModelExperimentService", Boom)
    result = _run(cli)
    assert result.exit_code == 1 and "unfinished persistent task" in result.output
    assert cli.calls == []


@pytest.mark.parametrize(
    "override",
    [
        {"--family": "fable"},
        {"--family": "haiku"},
        {"--effort": "extreme"},
        {"--phase": "validate"},
        {"--phase": "review"},
    ],
)
def test_cli_rejects_unsupported_family_effort_and_protected_phase(cli, override):
    result = _run(cli, **override)
    assert result.exit_code != 0 and cli.calls == []


def test_cli_rejects_non_utf8_prompt(cli):
    cli.prompt.write_bytes(b"\xff\xfe\x00bad")
    result = _run(cli)
    assert result.exit_code != 0 and "UTF-8" in result.output and cli.calls == []


def test_producer_is_not_reachable_from_mcp_or_module_import():
    for path in Path(producer.__file__).parent.glob("*mcp*.py"):
        assert "claude_experiment" not in path.read_text(encoding="utf-8"), path.name
    code = (
        "import sys, vres_os.cli, vres_os.mcp_server, vres_os.mcp_entrypoint, vres_os.company_mcp;"
        "assert 'vres_os.claude_experiment' not in sys.modules"
    )
    completed = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120)
    assert completed.returncode == 0, completed.stderr[-2000:]
