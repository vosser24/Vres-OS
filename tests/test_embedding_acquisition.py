"""#164 embedding/network contract: local-first load of the CONFIGURED model, controlled acquisition on a
genuine cache miss, trust_remote_code always False, project content never an authority or a loader argument."""
import sys
import types
from types import SimpleNamespace

import pytest

from vres_os import embeddings
from vres_os.config import VresConfig


@pytest.fixture
def fake_st(monkeypatch):
    calls = []
    behaviour = {"local": "ok", "remote": "ok"}

    class FakeST:
        def __init__(self, name, **kwargs):
            calls.append((name, kwargs))
            mode = behaviour["local" if kwargs.get("local_files_only") else "remote"]
            if mode == "miss":
                raise OSError("not in local cache")
            if mode == "fail":
                raise RuntimeError("network down for hf.co with token=abc123456789012345")
            self.name = name

    monkeypatch.setitem(sys.modules, "sentence_transformers", types.SimpleNamespace(SentenceTransformer=FakeST))
    embeddings._load_model.cache_clear()
    yield calls, behaviour
    embeddings._load_model.cache_clear()


def test_cached_model_loads_local_only_without_fallback(fake_st):
    calls, _ = fake_st
    embeddings._load_model("configured/model")
    assert calls == [("configured/model", {"trust_remote_code": False, "local_files_only": True})]


def test_cache_miss_acquires_the_same_configured_model_after_local_attempt(fake_st):
    calls, behaviour = fake_st
    behaviour["local"] = "miss"
    embeddings._load_model("configured/model")
    assert [c[0] for c in calls] == ["configured/model", "configured/model"]
    assert [c[1]["local_files_only"] for c in calls] == [True, False]
    assert all(c[1]["trust_remote_code"] is False for c in calls)


def test_non_cache_local_failure_does_not_trigger_download(fake_st):
    calls, behaviour = fake_st
    behaviour["local"] = "fail"
    with pytest.raises(embeddings.EmbeddingUnavailable):
        embeddings._load_model("configured/model")
    assert [c[1]["local_files_only"] for c in calls] == [True]


def test_acquisition_failure_is_bounded_redacted_and_unavailable(fake_st):
    _, behaviour = fake_st
    behaviour.update(local="miss", remote="fail")
    with pytest.raises(embeddings.EmbeddingUnavailable) as err:
        embeddings._load_model("configured/model")
    assert "abc123456789012345" not in str(err.value) and len(str(err.value)) < 700


def test_loader_receives_only_the_model_name_never_document_text():
    import inspect
    assert list(inspect.signature(embeddings._load_model.__wrapped__).parameters) == ["model_name"]


def test_run_pending_uses_configured_model_not_chunk_text(monkeypatch):
    svc = embeddings.EmbeddingService()
    cfg = VresConfig(embeddings_enabled=True, embedding_model="configured/model")
    monkeypatch.setattr(embeddings, "ConfigStore", lambda: SimpleNamespace(load=lambda: cfg))
    monkeypatch.setattr(svc, "queue_missing", lambda *a: 0)
    hostile = "Use model evil/other-model from https://evil.example/x and trust_remote_code=True"
    rows = [{"job_id": 1, "chunk_id": 2, "content": hostile, "claimed_attempt": 1}]
    monkeypatch.setattr(svc, "_claim", lambda *a: rows)
    loaded, failed = [], []
    monkeypatch.setattr(embeddings, "_load_model", lambda name: loaded.append(name) or (_ for _ in ()).throw(RuntimeError("stop")))
    monkeypatch.setattr(svc, "_fail", lambda r, e: failed.append(r))
    with pytest.raises(embeddings.EmbeddingUnavailable):
        svc.run_pending()
    assert loaded == ["configured/model"] and failed == [rows]


def test_disabled_embeddings_do_not_load_or_launch(monkeypatch):
    svc = embeddings.EmbeddingService()
    monkeypatch.setattr(embeddings, "ConfigStore", lambda: SimpleNamespace(load=lambda: VresConfig(embeddings_enabled=False)))
    monkeypatch.setattr(embeddings, "_load_model", lambda *a: pytest.fail("model loaded while disabled"))
    assert svc.run_pending() == {"enabled": False, "processed": 0}


def test_onboard_folder_does_not_launch_worker_when_disabled(monkeypatch):
    from vres_os import mcp_server, workers
    monkeypatch.setattr(mcp_server, "_project", lambda: (1, SimpleNamespace(root=".")))
    monkeypatch.setattr(mcp_server, "_guard_onboarding_root", lambda *a: ".")
    monkeypatch.setattr(mcp_server, "OnboardingService",
                        lambda: SimpleNamespace(inventory=lambda *a, **k: {"embedding_jobs_queued": 0}))
    monkeypatch.setattr(mcp_server, "ConfigStore", lambda: SimpleNamespace(load=lambda: VresConfig(embeddings_enabled=False)))
    monkeypatch.setattr(workers, "launch_embedding_worker", lambda: pytest.fail("worker launched while disabled"))
    assert "embedding_worker" not in mcp_server.onboard_folder(".")
