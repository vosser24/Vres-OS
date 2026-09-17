from __future__ import annotations

from types import SimpleNamespace

from vres_os import mcp_server


def test_capability_resolve_passes_current_project_scope(monkeypatch):
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        mcp_server,
        "_project",
        lambda *args, **kwargs: (42, SimpleNamespace(root=".")),
    )

    def fake_resolve(self, query, limit=5, *, project_id=None):
        seen.update(query=query, limit=limit, project_id=project_id)
        return [
            {
                "capability_key": "cap.project.test",
                "project_id": project_id,
                "proven_count": 0,
            }
        ]

    monkeypatch.setattr(mcp_server.CapabilityService, "resolve", fake_resolve)

    result = mcp_server.capability_resolve("rare project expertise", 7)

    assert seen == {
        "query": "rare project expertise",
        "limit": 7,
        "project_id": 42,
    }
    assert result == [
        {
            "capability_key": "cap.project.test",
            "project_id": 42,
            "proven_count": 0,
        }
    ]
