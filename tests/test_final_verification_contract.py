import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = [f"F-{i:02d}" for i in range(16)]


def test_finalization_runbook_and_matrix_stay_aligned():
    runbook = (ROOT / "docs" / "FINAL-VERIFICATION.md").read_text(encoding="utf-8")
    with (ROOT / "docs" / "final-results-template.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert [row["test_id"] for row in rows] == EXPECTED
    assert len({row["test_id"] for row in rows}) == len(EXPECTED)
    for test_id in EXPECTED:
        assert f"### {test_id} —" in runbook
    assert "Surface-triggered regression policy after finalization" in runbook
    assert "A prior live PASS may be marked **REUSED** only when all of these are true" in runbook


def test_historical_live_runbook_is_explicitly_a_regression_catalog():
    text = (ROOT / "docs" / "LIVE-VERIFICATION.md").read_text(encoding="utf-8")
    assert "[FINAL-VERIFICATION.md](FINAL-VERIFICATION.md)" in text
    assert "exhaustive historical/regression catalog" in text
    assert "Do not rerun every LV/PA/UE case by default" in text


def test_readme_points_to_finalization_before_full_catalog():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    final = text.index("[finalization verification](docs/FINAL-VERIFICATION.md)")
    full = text.index("[full regression catalog](docs/LIVE-VERIFICATION.md)")
    assert final < full
