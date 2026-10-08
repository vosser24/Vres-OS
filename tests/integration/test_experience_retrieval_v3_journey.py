"""#176 E7 Boundary 3: E5 v3 low-trust-only abstention on real PostgreSQL rows (opt-in)."""

import hashlib

import pytest

pytest.importorskip("psycopg")

from vres_os.experience import ExperienceEpisodeService
from vres_os.experience_retrieval import ExperienceRetrievalService
from vres_os.sources import SourceService

REASON = "only_low_trust_observations"


def _source(pid, text, *, authority, title):
    svc = SourceService()
    key, sid = svc.register(
        source_type="test",
        title=title,
        origin="pytest",
        path_or_uri=f"pytest://{hashlib.sha256((title + text).encode()).hexdigest()[:12]}",
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
        version="1",
        project_id=pid,
        authority_level=authority,
    )
    svc.add_chunks(source_id=sid, text=text)
    return key


def _observed(pid, word):
    key = _source(
        pid,
        f"{word} supplier insolvency notes copied from outside",
        authority="external_untrusted_observation",
        title=f"obs-{word}",
    )
    return ExperienceEpisodeService().observe_external_source(pid, key, "completed")["episode_key"]


def _pack(pid, word, version):
    svc = ExperienceRetrievalService()
    request = {"project_id": pid, "query": word}
    if version == "v1":
        return svc._retrieve_frozen_v1(request)
    if version == "v2":
        return svc._retrieve_frozen_v2(request)
    if version == "v3":
        return svc._retrieve_frozen_v3(request)
    if version == "v4":
        return svc._retrieve_frozen_v4(request)
    return svc.retrieve(request)  # normal product: v5


@pytest.fixture
def word():
    import uuid

    return "zv3" + uuid.uuid4().hex[:10]


def test_v3_suppresses_a_lone_observed_episode_while_frozen_v1_v2_return_it(pg_project, word):
    ep = _observed(pg_project, word)
    v3 = _pack(pg_project, word, "v3")
    assert (
        v3["schema_version"] == "176.e5.v3" and v3["abstained"] is True and v3["reason"] == REASON
    )
    assert v3["diagnostics"]["suppressed_low_trust_only"] == 1 and v3["evidence_keys"] == []
    assert all(
        v3[s] == []
        for s in v3
        if s
        in (
            "current_decisions",
            "accepted_procedures",
            "validated_lessons",
            "candidate_lessons",
            "conflicts_and_stale",
            "precedent_episodes",
            "low_trust_observations",
            "raw_evidence_refs",
        )
    )
    assert ep not in repr(v3) and word not in repr(v3["low_trust_observations"])
    for version in ("v1", "v2"):
        old = _pack(pg_project, word, version)
        assert old["abstained"] is False and old["reason"] is None
        assert [i["role"] for i in old["low_trust_observations"]] == ["low_trust_observation"]
        assert "suppressed_low_trust_only" not in old["diagnostics"]


def test_v3_keeps_the_low_trust_observation_when_a_trusted_raw_source_also_matches(
    pg_project, word
):
    _observed(pg_project, word)
    _source(
        pg_project,
        f"{word} trusted archive evidence",
        authority="trusted_project_source",
        title=f"t-{word}",
    )
    v3 = _pack(pg_project, word, "v3")
    assert v3["abstained"] is False and v3["reason"] is None
    assert len(v3["low_trust_observations"]) == 1 and len(v3["raw_evidence_refs"]) >= 1
    assert v3["diagnostics"]["suppressed_low_trust_only"] == 0


def test_v3_ordinary_empty_pack_keeps_no_eligible_experience(pg_project, word):
    v3 = _pack(pg_project, word, "v3")
    assert v3["abstained"] is True and v3["reason"] == "no_eligible_experience"
    assert v3["diagnostics"]["suppressed_low_trust_only"] == 0


def test_frozen_v4_and_normal_v5_abstain_like_v3_for_a_lone_episode(pg_project, word):
    ep = _observed(pg_project, word)
    v4 = _pack(pg_project, word, "v5")
    v3 = _pack(pg_project, word, "v3")
    frozen = _pack(pg_project, word, "v4")
    assert frozen["schema_version"] == "176.e5.v4" and frozen["abstained"] is True
    assert frozen["reason"] == REASON and frozen["evidence_keys"] == []
    assert v4["schema_version"] == "176.e5.v5" and v3["schema_version"] == "176.e5.v3"
    assert v4["abstained"] is True and v4["reason"] == REASON and v4["evidence_keys"] == []
    assert v4["diagnostics"]["suppressed_low_trust_only"] == 1
    assert ep not in repr(v4) and word not in repr(v4["low_trust_observations"])
