"""AUTHORED, NOT_RUN. All examples are inert source strings."""
from __future__ import annotations

import pytest

from vres_os import personal_w4_windows_closure as closure


def test_original_python_module_identity():
    assert closure._module_name("src/vres_os/personal_day_desktop.py") == (
        "vres_os.personal_day_desktop"
    )
    assert closure._module_name("src/vres_os/__init__.py") == "vres_os"
    with pytest.raises(closure.WindowsClosureRefused):
        closure._module_name("src/other/surrogate.py")


def test_static_imports_are_conservative_and_do_not_execute():
    code = b"""from . import personal_day_plan
from .personal_day_plan import render_manual_day_plan
import pathlib
import vres_os.cli
"""
    known = frozenset({
        "vres_os", "vres_os.personal_day_desktop",
        "vres_os.personal_day_plan", "vres_os.cli",
    })
    report = closure._scan(code, "vres_os.personal_day_desktop", False, known)
    assert report["static_modules"] == [
        "vres_os", "vres_os.cli", "vres_os.personal_day_plan"
    ]
    assert report["external_import_roots_unclassified"] == ["pathlib"]
    assert report["unresolved_internal_candidates"] == []
    assert report["potential_dynamic_sites"] == []


def test_dynamic_import_sites_are_reported_not_followed():
    code = b"""import importlib
module = importlib.import_module("vres_os.cli")
other = __import__("os")
"""
    known = frozenset({"vres_os", "vres_os.personal_day_desktop"})
    report = closure._scan(code, "vres_os.personal_day_desktop", False, known)
    assert report["external_import_roots_unclassified"] == ["importlib"]
    assert [site["call"] for site in report["potential_dynamic_sites"]] == [
        "import_module", "__import__"
    ]


def test_reachable_graph_refuses_incomplete_source():
    graph = {
        "vres_os": {"static_modules": []},
        "vres_os.personal_day_desktop": {
            "static_modules": ["vres_os.personal_day_plan"]
        },
        "vres_os.personal_day_plan": {"static_modules": []},
    }
    assert closure._reachable("vres_os.personal_day_desktop", graph) == [
        "vres_os", "vres_os.personal_day_desktop", "vres_os.personal_day_plan"
    ]
    graph["vres_os.personal_day_plan"]["static_modules"] = ["vres_os.missing"]
    with pytest.raises(closure.WindowsClosureRefused):
        closure._reachable("vres_os.personal_day_desktop", graph)


def test_full_original_inventory_refuses_wrong_recipe():
    with pytest.raises(closure.WindowsClosureRefused):
        closure.inventory_original_windows_closure(b"{}", {})
