from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_capability_resolve_wrapper_passes_current_project_scope():
    source = (ROOT / "src" / "vres_os" / "mcp_server.py").read_text(encoding="utf-8")
    start = source.index("def capability_resolve(")
    end = source.index("\n\n@mcp.tool()\ndef capability_register", start)
    block = source[start:end]

    assert "pid, _ = _project()" in block
    assert "CapabilityService().resolve(need, limit, project_id=pid)" in block
    assert "proven" not in block.split('"""', 2)[1].lower()
