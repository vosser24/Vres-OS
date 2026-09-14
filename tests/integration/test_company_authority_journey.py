import uuid

import pytest

pytest.importorskip("psycopg")

from vres_os.approvals import ApprovalService
from vres_os.capabilities import CapabilityService, capability_register_subject
from vres_os.company_mcp import _knowledge_subject
from vres_os.db import connect
from vres_os.knowledge import KnowledgeService
from vres_os.procedures import ProcedureService, procedure_accept_subject
from vres_os.registry import RegistryService, registry_publish_subject
from vres_os.repository import Repository
from vres_os.sources import SourceService, source_publish_subject


def _approve(repo, task_key, action, subject):
    repo.record_event(task_key, "USER_INSTRUCTION", "user", {"text": "Approved"})
    return ApprovalService().record_company_approval(
        task_key=task_key,
        action=action,
        subject=subject,
        statement=f"Approve exact company-wide {action}",
    )["approval_key"]


def test_exact_company_publication_and_catalog_authority(pg_project):
    marker = uuid.uuid4().hex[:10]
    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Company authority integration",
        "Verify exact-scope company-wide publication on PostgreSQL",
        "test",
        "chairman",
    )
    registry_key = f"REG-{marker}"
    capability_key = f"cap.{marker}"
    knowledge_key = f"KNOW-{marker}"
    procedure_key = f"PROC-{marker}"
    source_key = None

    try:
        registry_subject = registry_publish_subject(
            registry_key,
            "process",
            "Monthly pricing review",
            "Reviewed pricing workflow",
            "active",
            "1",
            "commercial-director",
            {"fixture": marker},
        )
        registry_approval = _approve(
            repo, task_key, "registry_publish", registry_subject
        )
        RegistryService().register(
            object_key=registry_key,
            object_type="process",
            name="Monthly pricing review",
            description="Reviewed pricing workflow",
            project_id=None,
            version="1",
            owner_role="commercial-director",
            metadata={"fixture": marker},
            approval_key=registry_approval,
        )

        with pytest.raises(ValueError, match="exact subject"):
            RegistryService().register(
                object_key=registry_key,
                object_type="process",
                name="Monthly pricing review",
                description="Changed after approval",
                project_id=None,
                version="1",
                owner_role="commercial-director",
                metadata={"fixture": marker},
                approval_key=registry_approval,
            )

        capability_subject = capability_register_subject(
            capability_key,
            "Pricing analysis",
            "Analyze pricing decisions with validated evidence",
            "commercial",
            "commercial-director",
        )
        capability_approval = _approve(
            repo, task_key, "capability_register", capability_subject
        )
        CapabilityService().register(
            capability_key,
            "Pricing analysis",
            "Analyze pricing decisions with validated evidence",
            "commercial",
            "commercial-director",
            approval_key=capability_approval,
        )

        source_subject = source_publish_subject(
            source_type="policy",
            title="Pricing authority fixture",
            origin="pytest",
            content_hash=marker * 6 + "abcd",
            version="1",
            authority_level="approved",
            metadata={"fixture": marker},
        )
        source_approval = _approve(repo, task_key, "source_publish", source_subject)
        source_key, _ = SourceService().register(
            source_type="policy",
            title="Pricing authority fixture",
            origin="pytest",
            content_hash=marker * 6 + "abcd",
            version="1",
            project_id=None,
            authority_level="approved",
            metadata={"fixture": marker},
            approval_key=source_approval,
        )

        knowledge_subject = _knowledge_subject(
            knowledge_key=knowledge_key,
            knowledge_type="decision",
            title="Company pricing decision fixture",
            statement="Use the approved pricing review workflow.",
            status="canonical",
            confidence=1.0,
            scope={"fixture": marker},
            review_after=None,
            source_owner="chairman",
        )
        knowledge_approval = _approve(
            repo, task_key, "knowledge_publish", knowledge_subject
        )
        KnowledgeService().propose(
            key=knowledge_key,
            knowledge_type="decision",
            title="Company pricing decision fixture",
            statement="Use the approved pricing review workflow.",
            status="canonical",
            scope={"fixture": marker},
            confidence=1.0,
            source_owner="chairman",
            project_id=None,
            approval_key=knowledge_approval,
        )

        baseline_metrics = {
            "quality_score": 1.0,
            "runtime_ms": 120,
            "input_tokens": 80,
            "output_tokens": 25,
            "model_calls": 1,
            "validation": {"accepted_by_user": True, "source": "pytest"},
        }
        procedure_subject = procedure_accept_subject(
            procedure_key=procedure_key,
            name="Monthly pricing review",
            description="Review pricing before publication",
            task_family="commercial",
            input_contract={"required": ["price-list"]},
            method=["load", "compare", "review"],
            invariants=["never publish automatically"],
            validation_contract=["chairman approval"],
            output_contract={"artifact": "pricing-review.json"},
            implementation_ref="scripts/pricing_review.py",
            initial_metrics=baseline_metrics,
        )
        procedure_approval = _approve(
            repo, task_key, "procedure_accept", procedure_subject
        )
        ProcedureService().accept_baseline(
            procedure_key=procedure_key,
            name="Monthly pricing review",
            description="Review pricing before publication",
            task_family="commercial",
            project_id=None,
            input_contract={"required": ["price-list"]},
            method=["load", "compare", "review"],
            invariants=["never publish automatically"],
            validation_contract=["chairman approval"],
            output_contract={"artifact": "pricing-review.json"},
            approval_key=procedure_approval,
            implementation_ref="scripts/pricing_review.py",
            initial_metrics=baseline_metrics,
        )

        with pytest.raises(ValueError, match="exact subject"):
            ProcedureService().accept_baseline(
                procedure_key=procedure_key,
                name="Monthly pricing review",
                description="Review pricing before publication",
                task_family="commercial",
                project_id=None,
                input_contract={"required": ["price-list"]},
                method=["load", "compare", "publish"],
                invariants=["never publish automatically"],
                validation_contract=["chairman approval"],
                output_contract={"artifact": "pricing-review.json"},
                approval_key=procedure_approval,
                implementation_ref="scripts/pricing_review.py",
                initial_metrics=baseline_metrics,
            )

        with connect() as conn:
            registry_row = conn.execute(
                "SELECT project_id,scope_approval_event_id FROM vres.registry_objects WHERE object_key=%s",
                (registry_key,),
            ).fetchone()
            capability_row = conn.execute(
                "SELECT scope_approval_event_id FROM vres.capabilities WHERE capability_key=%s",
                (capability_key,),
            ).fetchone()
            source_row = conn.execute(
                "SELECT project_id,scope_approval_event_id FROM vres.sources WHERE source_key=%s",
                (source_key,),
            ).fetchone()
            knowledge_row = conn.execute(
                "SELECT project_id,approval_event_id,scope_approval_event_id "
                "FROM vres.knowledge_items WHERE knowledge_key=%s",
                (knowledge_key,),
            ).fetchone()
            procedure_row = conn.execute(
                "SELECT p.project_id,p.scope_approval_event_id,v.approval_event_id "
                "FROM vres.procedures p JOIN vres.procedure_versions v "
                "ON v.procedure_id=p.id AND v.version_no=p.preferred_version "
                "WHERE p.procedure_key=%s",
                (procedure_key,),
            ).fetchone()
        assert registry_row["project_id"] is None
        assert registry_row["scope_approval_event_id"] is not None
        assert capability_row["scope_approval_event_id"] is not None
        assert source_row["project_id"] is None
        assert source_row["scope_approval_event_id"] is not None
        assert knowledge_row["project_id"] is None
        assert knowledge_row["approval_event_id"] == knowledge_row["scope_approval_event_id"]
        assert procedure_row["project_id"] is None
        assert procedure_row["approval_event_id"] == procedure_row["scope_approval_event_id"]
    finally:
        with connect() as conn, conn.transaction():
            conn.execute(
                "DELETE FROM vres.knowledge_items WHERE knowledge_key=%s", (knowledge_key,)
            )
            if source_key:
                conn.execute("DELETE FROM vres.sources WHERE source_key=%s", (source_key,))
            conn.execute(
                "DELETE FROM vres.registry_objects WHERE object_key=%s", (registry_key,)
            )
            conn.execute(
                "DELETE FROM vres.capabilities WHERE capability_key=%s", (capability_key,)
            )
            conn.execute(
                "DELETE FROM vres.procedures WHERE procedure_key=%s", (procedure_key,)
            )
