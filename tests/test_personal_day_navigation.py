"""Pure operator-guidance tests; no original owner, IO or GUI is invoked."""
import pytest
from vres_os.personal_day_navigation import next_read_only_step


@pytest.mark.parametrize(("kwargs", "route"), [
    ({"day_loaded": False, "selected_kind": None}, "refresh"),
    ({"day_loaded": True, "selected_kind": None}, "home"),
    ({"day_loaded": True, "selected_kind": "ACTIVE_TASK"}, "next_action"),
    ({"day_loaded": True, "selected_kind": "ACTIVE_TASK", "action_seen": True}, "focus"),
    ({"day_loaded": True, "selected_kind": "ACTIVE_TASK", "focused": True,
      "stage": "TASK_SELECTED_NO_PROJECT"}, "project_tab"),
    ({"day_loaded": True, "selected_kind": "ACTIVE_TASK", "focused": True,
      "stage": "PROJECT_SELECTED_NO_RESULT"}, "project_tab"),
    ({"day_loaded": True, "selected_kind": "ACTIVE_TASK", "focused": True,
      "stage": "RESULT_REVIEW_READY_SEPARATE_DECISION"}, "briefing"),
    ({"day_loaded": True, "selected_kind": "ACTIVE_TASK", "focused": True,
      "stage": "RESULT_REVIEW_READY_SEPARATE_DECISION", "briefing_seen": True}, "decision"),
    ({"day_loaded": True, "selected_kind": "ACTIVE_TASK", "focused": True,
      "stage": "RESULT_REVIEW_READY_SEPARATE_DECISION", "decision_ready": True}, None),
    ({"day_loaded": True, "selected_kind": "SAVED_COMPLETED_RESULT"}, None),
    ({"day_loaded": True, "selected_kind": "SAVED_COMPLETED_RESULT",
      "history_clear": True}, "focus"),
    ({"day_loaded": True, "selected_kind": "SAVED_COMPLETED_RESULT",
      "history_clear": True, "focused": True}, None),
    ({"day_loaded": True, "selected_kind": "ACTIVE_TASK",
      "manual_recovery_hold": True}, "home"),
    ({"day_loaded": True, "selected_kind": "ACTIVE_TASK",
      "focused": True, "stage": "INVALID_UNKNOWN_STAGE"}, None),
    ({"day_loaded": True, "selected_kind": "ACTIVE_TASK",
      "decision_ready": True}, None),
    ({"day_loaded": True, "selected_kind": "SAVED_COMPLETED_RESULT",
      "briefing_seen": True, "history_clear": True}, None),
    ({"day_loaded": "yes", "selected_kind": "ACTIVE_TASK"}, None),
    ({"day_loaded": True, "selected_kind": "NOT_AN_ORIGINAL_KIND"}, None),
])
def test_next_step_is_only_a_read_or_navigation_hint(kwargs, route):
    result = next_read_only_step(**kwargs)
    assert result["route"] == route
    assert set(result) == {"route", "label"}
    assert result["label"] and isinstance(result["label"], str)
    assert result["route"] in {None, "refresh", "home", "next_action", "focus",
                               "project_tab", "briefing", "decision"}


def test_hints_have_no_nonlocal_operations_or_dynamic_imports():
    import ast
    import inspect
    from vres_os import personal_day_navigation as navigation
    tree = ast.parse(inspect.getsource(navigation))
    imports = [node for node in ast.walk(tree)
               if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert len(imports) == 1 and isinstance(imports[0], ast.ImportFrom)
    assert imports[0].module == "__future__"
    assert not any(isinstance(node, (ast.Import, ast.With, ast.AsyncWith))
                   for node in ast.walk(tree))
