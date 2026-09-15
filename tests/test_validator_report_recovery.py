import json

import pytest

from vres_os.validation import observed_validator_report


def _report(request_key: str = "VAL-1", outcome: str = "passed") -> dict:
    return {
        "request_key": request_key,
        "outcome": outcome,
        "checks": [{"status": outcome, "evidence": "verified"}],
    }


def _assistant(text: str, model: str = "claude-fable-5-1") -> dict:
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "model": model,
            "content": [{"type": "text", "text": text}],
        },
    }


def _handback(text: str, *, name: str = "SubagentHandback") -> dict:
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "model": "claude-fable-5-1",
            "content": [
                {
                    "type": "tool_use",
                    "name": name,
                    "input": {"message": text},
                }
            ],
        },
    }


def test_valid_final_message_is_preferred_over_transcript_fallback():
    final = json.dumps(_report("VAL-final"))
    records = [_assistant(json.dumps(_report("VAL-old")))]

    report, source = observed_validator_report(final, records)

    assert report["request_key"] == "VAL-final"
    assert source == "last_assistant_message"


def test_trailing_prose_recovers_latest_canonical_assistant_report():
    report_json = json.dumps(_report("VAL-recovered"))
    records = [
        _assistant(report_json),
        _assistant("Report delivered. Nothing further is needed from me."),
    ]

    report, source = observed_validator_report(
        "Report delivered. Nothing further is needed from me.", records
    )

    assert report["request_key"] == "VAL-recovered"
    assert report["outcome"] == "passed"
    assert source == "assistant_transcript"


def test_real_handback_shape_recovers_report_before_trailing_prose():
    request_key = "VAL-53eda87e1363484b"
    report_json = json.dumps(_report(request_key))
    final_prose = (
        "Report delivered. Nothing further is needed from me; the validation is complete "
        f"and the JSON verdict (passed, request_key {request_key}) has been handed back to the caller."
    )
    records = [
        _handback(report_json),
        _assistant(final_prose),
    ]

    report, source = observed_validator_report(final_prose, records)

    assert report["request_key"] == request_key
    assert report["outcome"] == "passed"
    assert source == "assistant_transcript"


def test_fallback_uses_newest_valid_assistant_report():
    records = [
        _assistant(json.dumps(_report("VAL-older"))),
        _assistant("working..."),
        _assistant(json.dumps(_report("VAL-newer", "failed"))),
        _assistant("done"),
    ]

    report, source = observed_validator_report("done", records)

    assert report["request_key"] == "VAL-newer"
    assert report["outcome"] == "failed"
    assert source == "assistant_transcript"


def test_tool_result_json_is_never_eligible_for_recovery():
    tool_result = {
        "type": "user",
        "message": {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": json.dumps(_report("VAL-tool")),
                }
            ],
        },
    }

    with pytest.raises(ValueError, match="not found"):
        observed_validator_report("plain prose", [tool_result])


def test_arbitrary_assistant_tool_use_is_not_eligible_for_recovery():
    record = _handback(json.dumps(_report("VAL-other-tool")), name="SomeOtherTool")

    with pytest.raises(ValueError, match="not found"):
        observed_validator_report("plain prose", [record])


def test_user_authored_handback_shape_is_not_eligible_for_recovery():
    record = _handback(json.dumps(_report("VAL-user-handback")))
    record["type"] = "user"
    record["message"]["role"] = "user"

    with pytest.raises(ValueError, match="not found"):
        observed_validator_report("plain prose", [record])


def test_invalid_assistant_json_does_not_bypass_report_contract():
    invalid = json.dumps(
        {
            "request_key": "VAL-invalid",
            "outcome": "passed",
            "checks": [{"status": "not_run", "evidence": "missing live check"}],
        }
    )

    with pytest.raises(ValueError, match="not found"):
        observed_validator_report("plain prose", [_assistant(invalid)])


def test_invalid_handback_json_does_not_bypass_report_contract():
    invalid = json.dumps(
        {
            "request_key": "VAL-invalid-handback",
            "outcome": "passed",
            "checks": [{"status": "not_run", "evidence": "missing live check"}],
        }
    )

    with pytest.raises(ValueError, match="not found"):
        observed_validator_report("plain prose", [_handback(invalid)])


def test_json_text_block_can_be_recovered_when_same_message_has_trailing_text_block():
    report_json = json.dumps(_report("VAL-block"))
    records = [
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "model": "claude-fable-5-1",
                "content": [
                    {"type": "text", "text": report_json},
                    {"type": "text", "text": "Thanks."},
                ],
            },
        }
    ]

    report, source = observed_validator_report("Thanks.", records)

    assert report["request_key"] == "VAL-block"
    assert source == "assistant_transcript"
