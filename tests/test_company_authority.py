from __future__ import annotations

from pathlib import Path

import pytest

from test_audit_regressions import ScriptedConnection
from vres_os import approvals, capabilities, procedures, registry
from vres_os.approvals import ApprovalService, require_company_approval
from vres_os.authority import company_subject
from vres_os.capabilities import CapabilityService, capability_register_subject
from vres_os.procedures import ProcedureService, procedure_accept_subject
from vres_os.registry import RegistryService, registry_publish_subject
from vres_os.sources import SourceService, source_publish_subject

ROOT = Path(__file__).parents[1]


def test_company_subject_is_order_stable_redacted_and_content_bound():
    first, safe = company_subject(
        "registry_publish",
        {"name": "Pricing", "metadata": {"api_key": "secret-value"}},
    )
    reordered, _ = company_subject(
        "registry_publish",
        {"metadata": {"api_key": "secret-value"}, "name": "Pricing"},
    )
    changed, _ = company_subject(
        "registry_publish",
        {"name": "Pricing v2", "metadata": {"api_key": "secret-value"}},
    )
    assert first == reordered
    assert changed != first
    assert safe["metadata"]["api_key"] == "[REDACTED]"
    assert "secret-value" not in first


def test_company_approval_records_exact_action_and_subject(monkeypatch):
    subject = registry_publish_subject(
        "REG-pricing",
        "process",
        "Pricing policy",
        "Approved pricing policy",
        "active",
        "1",
        "commercial-director",
        {},
    )
    subject_key, _ = company_subject("registry_publish", subject)
    conn = ScriptedConnection(
        [
            ("FROM vres.tasks", {"id": 4, "project_id": 7}),
            ("FROM vres.task_events", {"id": 9, "payload": {"text": "Approved"}}),
            ("pg_advisory_xact_lock", None),
            ("SELECT approval_type,subject_key", []),
            ("INSERT INTO vres.approval_events", {"approval_key": "APP-company"}),
        ]
    )
    monkeypatch.setattr(approvals, "_connect", lambda: conn)
    result = ApprovalService().record_company_approval(
        task_key="TASK-1",
        action="registry_publish",
        subject=subject,
        statement="Publish this exact registry object company-wide",
    )
    assert result["approval_key"] == "APP-company"
    assert result["approval_type"] == "company_registry_publish"
    assert result["subject_key"] == subject_key
    insert_params = conn.calls[-1][1]
    assert insert_params[1] == 7
    assert insert_params[4] == "company_registry_publish"
    assert insert_params[5] == subject_key


def test_company_approval_cannot_authorize_changed_content():
    subject = capability_register_subject(
        "cap.pricing",
        "Pricing",
        "Evaluate pricing",
        "commercial",
        "commercial-director",
    )
    subject_key, _ = company_subject("capability_register", subject)
    conn = ScriptedConnection(
        [
            (
                "approval_events",
                {
                    "id": 3,
                    "project_id": 7,
                    "approval_type": "company_capability_register",
                    "subject_key": subject_key,
                },
            )
        ]
    )
    changed = dict(subject, description="Evaluate and automatically change pricing")
    with pytest.raises(ValueError, match="exact subject"):
        require_company_approval(conn, "APP-1", "capability_register", changed)


def test_procedure_subject_binds_full_contract_and_baseline_metrics():
    subject = procedure_accept_subject(
        procedure_key="PROC-pricing",
        name="Pricing review",
        description="Review monthly pricing",
        task_family="commercial",
        input_contract={"required": ["price-list"]},
        method=["load", "compare", "review"],
        invariants=["never publish automatically"],
        validation_contract=["chairman approval"],
        output_contract={"artifact": "review.json"},
        implementation_ref="scripts/pricing.py?token=secret",
        initial_metrics={
            "quality_score": 1.0,
            "runtime_ms": 120,
            "input_tokens": 50,
            "output_tokens": 20,
            "validation": {"accepted_by_user": True},
        },
    )
    original_key, safe = company_subject("procedure_accept", subject)
    changed_method_key, _ = company_subject(
        "procedure_accept",
        dict(subject, method=["load", "compare", "publish"]),
    )
    changed_metrics_key, _ = company_subject(
        "procedure_accept",
        dict(
            subject,
            initial_metrics=dict(subject["initial_metrics"], runtime_ms=80),
        ),
    )
    assert changed_method_key != original_key
    assert changed_metrics_key != original_key
    assert "secret" not in safe["implementation_ref"]


def test_company_services_fail_closed_without_approval(monkeypatch):
    with pytest.raises(ValueError, match="explicit exact-scope approval"):
        SourceService().register_in_conn(
            object(),
            source_type="policy",
            title="Company policy",
            project_id=None,
        )

    cap_conn = ScriptedConnection([])
    monkeypatch.setattr(capabilities, "_connect", lambda: cap_conn)
    with pytest.raises(ValueError, match="explicit exact-scope approval"):
        CapabilityService().register(
            "cap.finance", "Finance", "Finance analysis", "finance", "finance-director"
        )

    registry_conn = ScriptedConnection([])
    monkeypatch.setattr(registry, "_connect", lambda: registry_conn)
    with pytest.raises(ValueError, match="explicit exact-scope approval"):
        RegistryService().register(
            object_key="REG-1",
            object_type="process",
            name="Monthly close",
            project_id=None,
        )

    procedure_conn = ScriptedConnection([("pg_advisory_xact_lock", None)])
    monkeypatch.setattr(procedures, "_connect", lambda: procedure_conn)
    with pytest.raises(ValueError, match="explicit exact-scope approval"):
        ProcedureService().accept_baseline(
            procedure_key="PROC-1",
            name="Monthly close",
            description="Close the books",
            task_family="finance",
            project_id=None,
            input_contract={},
            method=["close"],
            invariants=["reconcile"],
            validation_contract=["controller approval"],
            output_contract={"artifact": "close.json"},
            approval_key=None,
        )


def test_source_approval_subject_strips_uri_credentials_and_secret_query_values():
    subject = source_publish_subject(
        source_type="web",
        title="Pricing feed",
        path_or_uri="https://user:password@example.invalid/feed?token=secret&lang=el",
    )
    assert "user:" not in subject["path_or_uri"]
    assert "password" not in subject["path_or_uri"]
    assert "secret" not in subject["path_or_uri"]
    assert "lang=el" in subject["path_or_uri"]


def test_company_mcp_extension_is_the_installed_entrypoint():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    wrapper = (ROOT / "plugins" / "vres-os" / "bin" / "vres-mcp.ps1").read_text(
        encoding="utf-8"
    )
    tools = (ROOT / "src" / "vres_os" / "company_mcp.py").read_text(encoding="utf-8")
    assert 'vres-mcp = "vres_os.company_mcp:main"' in pyproject
    assert "-m vres_os.company_mcp" in wrapper
    for function in [
        "company_approval_record",
        "company_source_register",
        "company_knowledge_propose",
        "company_registry_register",
        "company_capability_register",
        "company_procedure_accept",
    ]:
        assert f"def {function}(" in tools
