import pytest

import vres_os.company_mcp as company_mcp


def test_approved_company_promotion_routes_directly_to_idempotent_service(monkeypatch):
    class FakeReplayService:
        def preview_company_promotion(self, replay_key):
            pytest.fail(f"approved retry must not preview stale replay {replay_key}")

        def promote_company_attested(self, replay_key, approval_key):
            return {
                "decision": "company_promoted",
                "replay_key": replay_key,
                "approval_key": approval_key,
            }

    monkeypatch.setattr(company_mcp, "ReplayService", FakeReplayService)
    result = company_mcp.company_procedure_replay_promote(
        "REPLAY-1",
        approval_key="APPROVAL-1",
    )
    assert result == {
        "decision": "company_promoted",
        "replay_key": "REPLAY-1",
        "approval_key": "APPROVAL-1",
    }


def test_company_promotion_without_approval_still_previews(monkeypatch):
    class FakeReplayService:
        def preview_company_promotion(self, replay_key):
            assert replay_key == "REPLAY-2"
            return {
                "subject": {
                    "phase": "promote_attested",
                    "procedure_key": "PROC-GLOBAL",
                    "candidate_version": 2,
                    "replay_key": replay_key,
                },
                "assessment": {"technically_eligible": True},
            }

        def promote_company_attested(self, replay_key, approval_key):
            pytest.fail("preview request must not promote")

    monkeypatch.setattr(company_mcp, "ReplayService", FakeReplayService)
    result = company_mcp.company_procedure_replay_promote("REPLAY-2")
    assert result["requires_company_approval"] is True
    assert result["phase"] == "promote_attested"
    assert result["replay_key"] == "REPLAY-2"
    assert result["approval"]["action"] == "procedure_optimize"
