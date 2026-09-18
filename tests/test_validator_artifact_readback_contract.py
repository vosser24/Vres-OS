from pathlib import Path


def test_validator_requires_artifact_get_for_registration_readback():
    text = (
        Path(__file__).parents[1]
        / "plugins"
        / "vres-os"
        / "agents"
        / "validator.md"
    ).read_text(encoding="utf-8")

    assert "artifact_get" in text
    assert "registry_get" in text
    assert "must not be used as a substitute" in text
