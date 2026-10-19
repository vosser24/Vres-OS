import pytest


@pytest.fixture(autouse=True)
def _unit_tests_never_see_a_real_installation(request, monkeypatch):
    """Unit tests run as a non-managed installation, whatever this machine has installed.

    Integration tests keep the real personal-release contact guard, so on a managed
    workstation they reach only database targets the operator approved.
    """
    if "integration" in request.node.path.parts:
        return
    from vres_os import database_targets

    monkeypatch.setattr(database_targets, "personal_release_root", lambda: None)
