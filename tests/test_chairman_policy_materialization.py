"""#165 phase A: pure offline Chairman policy/materialization (NO activation)."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from vres_os.chairman_policy import (
    DEFAULT_CHAIRMAN_POLICY,
    POLICY_SCHEMA,
    ChairmanPolicy,
    ChairmanPolicyError,
    materialize_chairman,
)

ROOT = Path(__file__).parents[1]
AGENTS = ROOT / "plugins" / "vres-os" / "agents"


def _template() -> bytes:
    return (AGENTS / "chairman.md").read_bytes()


def _frontmatter(blob: bytes) -> dict[str, str]:
    text = blob.decode("utf-8")
    header, sep, _body = text[4:].partition("\n---\n")
    assert sep and text.startswith("---\n")
    return dict(line.split(": ", 1) for line in header.split("\n"))


def test_initial_chairman_control_policy_is_versioned_opus_medium_without_generation_pin():
    policy = DEFAULT_CHAIRMAN_POLICY
    assert policy == ChairmanPolicy(version=1, family="opus", effort="medium")
    assert policy.to_document() == (
        b'{"effort":"medium","family":"opus","schema":"vres-chairman-control/1","version":1}'
    )
    assert b"claude-opus-" not in policy.to_document()
    assert POLICY_SCHEMA == "vres-chairman-control/1"


def test_policy_round_trip_is_deterministic_and_immutable():
    candidate = ChairmanPolicy(version=42, family="sonnet", effort="high")
    encoded = candidate.to_document()
    assert ChairmanPolicy.from_document(encoded) == candidate
    assert ChairmanPolicy.from_document(encoded).to_document() == encoded
    with pytest.raises(AttributeError):
        candidate.family = "opus"


@pytest.mark.parametrize(
    "values",
    [
        {"version": True, "family": "opus", "effort": "medium"},
        {"version": 0, "family": "opus", "effort": "medium"},
        {"version": -1, "family": "opus", "effort": "medium"},
        {"version": 1000001, "family": "opus", "effort": "medium"},
        {"version": "1", "family": "opus", "effort": "medium"},
        {"version": 1, "family": "claude-opus-5-5", "effort": "medium"},
        {"version": 1, "family": "auto", "effort": "medium"},
        {"version": 1, "family": "fable", "effort": "medium"},
        {"version": 1, "family": "Opus", "effort": "medium"},
        {"version": 1, "family": "opus", "effort": "unknown"},
        {"version": 1, "family": "opus", "effort": "MEDIUM"},
    ],
)
def test_unknown_or_ambiguous_policy_fails_without_substituting_model(values):
    with pytest.raises(ChairmanPolicyError):
        ChairmanPolicy(**values)


@pytest.mark.parametrize(
    "document",
    [
        b"",
        b"not-json",
        b"[]",
        b'{"schema":"wrong","version":1,"family":"opus","effort":"medium"}',
        b'{"schema":"vres-chairman-control/1","version":1,"family":"opus"}',
        b'{"schema":"vres-chairman-control/1","version":1,"family":"opus","effort":"medium","extra":1}',
        b'{"schema":"vres-chairman-control/1","version":1,"family":"opus","family":"sonnet","effort":"medium"}',
        b'{"schema":"vres-chairman-control/1","version":true,"family":"opus","effort":"medium"}',
        b"\xff",
        b" " * 4097,
    ],
)
def test_policy_document_refuses_unknown_duplicate_and_malformed_data(document):
    with pytest.raises(ChairmanPolicyError):
        ChairmanPolicy.from_document(document)


def test_candidate_render_is_byte_deterministic_and_preserves_the_exact_body():
    source = _template()
    assert _frontmatter(source)["model"] == "sonnet"  # installed source has NOT switched policy
    assert _frontmatter(source)["effort"] == "high"
    first = materialize_chairman(source, DEFAULT_CHAIRMAN_POLICY)
    second = materialize_chairman(source, DEFAULT_CHAIRMAN_POLICY)
    assert first == second
    assert first.content != source
    header = _frontmatter(first.content)
    assert header["name"] == "chairman"
    assert header["model"] == "opus"
    assert header["effort"] == "medium"
    assert set(header) == {"name", "description", "model", "effort"}
    assert source.partition(b"\n---\n")[2] == first.content.partition(b"\n---\n")[2]
    assert b"model: claude-opus-" not in first.content
    assert first.manifest() == second.manifest()
    assert first.manifest()["template_sha256"] == hashlib.sha256(source).hexdigest()
    assert first.manifest()["rendered_sha256"] == hashlib.sha256(first.content).hexdigest()
    assert first.manifest()["policy_sha256"] == hashlib.sha256(
        DEFAULT_CHAIRMAN_POLICY.to_document()
    ).hexdigest()
    assert "observed_model" not in first.manifest()  # never invent host evidence
    assert "installed" not in first.manifest()  # candidate is not active installation proof


def test_template_identity_when_existing_sonnet_high_is_explicitly_requested():
    source = _template()
    unchanged = materialize_chairman(source, ChairmanPolicy(1, "sonnet", "high"))
    assert unchanged.content == source


def test_review_candidate_policy_changes_only_model_and_effort_frontmatter_fields():
    source = _template()
    candidate = materialize_chairman(source, DEFAULT_CHAIRMAN_POLICY).content
    old = _frontmatter(source)
    new = _frontmatter(candidate)
    assert new == dict(old, model="opus", effort="medium")


@pytest.mark.parametrize(
    "bad_template",
    [
        b"",
        b"not-a-template",
        b"---\nname: chairman\n",
        b"---\nname: validator\ndescription: x\nmodel: sonnet\neffort: high\n---\nbody\n",
        b"---\nname: chairman\ndescription: x\nmodel: sonnet\neffort: high\nmodel: opus\n---\nbody\n",
        b"---\nname: chairman\ndescription: x\nmodel: opus\neffort: high\nunknown: x\n---\nbody\n",
        b"---\nname: chairman\ndescription: x\nmodel: auto\neffort: high\n---\nbody\n",
        b"---\nname: chairman\ndescription: x\nmodel: sonnet\neffort: high\n---\n",
        b"---\r\nname: chairman\r\n---\r\nbody\r\n",
        b"\xef\xbb\xbf---\nname: chairman\n---\nbody\n",
        b"\xff" * 8,
        b"x" * (512 * 1024 + 1),
    ],
)
def test_unsafe_or_nonchairman_template_fails_closed(bad_template):
    with pytest.raises(ChairmanPolicyError):
        materialize_chairman(bad_template, DEFAULT_CHAIRMAN_POLICY)


def test_other_governed_agents_stay_pinned_and_untouched_by_chairman_materialization():
    frozen = {
        "validator.md": ("fable", "high"),
        "routing-arbiter.md": ("fable", "high"),
        "sonnet-expert.md": ("sonnet", "medium"),
        "opus-expert.md": ("opus", "high"),
    }
    source_bytes = {name: (AGENTS / name).read_bytes() for name in frozen}
    _ = materialize_chairman(_template(), DEFAULT_CHAIRMAN_POLICY)
    for name, expected in frozen.items():
        assert (AGENTS / name).read_bytes() == source_bytes[name]
        assert (_frontmatter(source_bytes[name])["model"], _frontmatter(source_bytes[name])["effort"]) == expected


def test_no_filesystem_write_is_part_of_pure_candidate_render(monkeypatch):
    # A materializer must not open config, database, vault or installation paths.
    import vres_os.chairman_policy as module
    assert "ConfigStore" not in vars(module)
    assert "SecretStore" not in vars(module)
    assert "connect" not in vars(module)
    assert "write" not in vars(module)
    materialize_chairman(_template(), DEFAULT_CHAIRMAN_POLICY)
