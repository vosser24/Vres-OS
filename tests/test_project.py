from pathlib import Path

from vres_os.project import discover_project


def test_project_identity_is_stable_for_plain_directory(tmp_path: Path):
    a = discover_project(tmp_path)
    b = discover_project(tmp_path)
    assert a.key == b.key
    assert a.root == tmp_path.resolve()
