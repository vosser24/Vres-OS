import json

from vres_os.validation_audit import _specific_contract_reason, extract_request_key


def _assistant_handback(report: str) -> dict:
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "model": "claude-fable-5-1",
            "content": [
                {
                    "type": "tool_use",
                    "name": "SubagentHandback",
                    "input": {"message": report},
                }
            ],
        },
    }


def test_invalid_canonical_handback_keeps_fresh_request_identity_and_specific_error(tmp_path):
    fresh = "VAL-fresh123"
    old = "VAL-old456"
    report = json.dumps(
        {
            "request_key": fresh,
            "outcome": "passed",
            "checks": [{"status": "not_run", "evidence": "post-completion check"}],
        }
    )
    transcript = tmp_path / "validator.jsonl"
    transcript.write_text(
        json.dumps(_assistant_handback(report))
        + "\n"
        + json.dumps(
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "model": "claude-fable-5-1",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Historical {old}; current {fresh}. Report delivered.",
                        }
                    ],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    payload = {
        "last_assistant_message": f"Historical {old}; current {fresh}. Report delivered.",
        "agent_transcript_path": str(transcript),
    }

    assert extract_request_key(payload) == fresh
    reason = _specific_contract_reason(
        payload,
        "Validator report was not found in the final assistant message or observed assistant transcript",
    )
    assert reason == "A skipped or failed check cannot establish PASS"


def test_ambiguous_prose_request_keys_do_not_bind_to_first_mention():
    assert (
        extract_request_key(
            {"last_assistant_message": "Prior VAL-old and fresh VAL-new are both discussed."}
        )
        is None
    )


def test_single_prose_request_key_remains_supported():
    assert (
        extract_request_key(
            {"last_assistant_message": "Validation VAL-only failed before canonical JSON."}
        )
        == "VAL-only"
    )
