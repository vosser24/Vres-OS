import uuid

from vres_os import mcp_server
from vres_os.capabilities import CapabilityService
from vres_os.repository import Repository


def test_mcp_capability_resolve_sees_unproven_project_capability_only_in_owner_scope(
    pg_project, monkeypatch
):
    pid = pg_project
    token = uuid.uuid4().hex
    need = f"rare-{token} regulatory geometry"
    capability_key = f"cap.project.{token}"
    owner_role = f"specialist-{token[:8]}"

    repo = Repository()
    task_key = repo.begin_task(
        pid,
        "Acquire project capability",
        "Create one unproven project-local capability for resolver scoping regression coverage.",
        "aigo-test",
        "chairman",
    )

    CapabilityService().register_project(
        key=capability_key,
        name=f"Rare {token} Regulatory Geometry",
        description=f"Expertise for {need} with bounded project-only use.",
        domain="specialist",
        owner_role=owner_role,
        project_id=pid,
        task_key=task_key,
        acquisition_evidence={"source": "integration-test", "method": "synthetic"},
    )

    direct_owner = CapabilityService().resolve(need, project_id=pid)
    assert direct_owner[0]["capability_key"] == capability_key
    assert direct_owner[0]["project_id"] == pid
    assert direct_owner[0]["proven_count"] == 0

    monkeypatch.setattr(mcp_server, "_project", lambda root=".": (pid, object()))
    wrapped_owner = mcp_server.capability_resolve(need)
    assert wrapped_owner[0]["capability_key"] == capability_key
    assert wrapped_owner[0]["project_id"] == pid
    assert wrapped_owner[0]["proven_count"] == 0

    other_project_id = pid + 1_000_000
    monkeypatch.setattr(
        mcp_server,
        "_project",
        lambda root=".": (other_project_id, object()),
    )
    wrapped_other = mcp_server.capability_resolve(need)
    assert all(row["capability_key"] != capability_key for row in wrapped_other)

    global_only = CapabilityService().resolve(need, project_id=None)
    assert all(row["capability_key"] != capability_key for row in global_only)
