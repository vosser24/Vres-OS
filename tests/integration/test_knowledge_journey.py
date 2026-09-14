import uuid
import pytest
pytest.importorskip("psycopg")
from vres_os.knowledge import KnowledgeService


def test_observation_is_retrievable_later(pg_project):
    svc = KnowledgeService()
    key = "KNOW-" + uuid.uuid4().hex[:10]
    svc.propose(
        key=key, knowledge_type="observation", title="Heat and ice cubes",
        statement="Ice-cube unit sales were materially higher during high-temperature days.",
        status="observed", confidence=.78, scope={"period": "one week"}, source_owner="test",
        project_id=pg_project,
    )
    hits = svc.search("ice cubes temperature", project_id=pg_project)
    assert any(h["knowledge_key"] == key for h in hits)
