from pathlib import Path

from vres_os.config import ConfigStore, VresConfig


def test_config_roundtrip_without_secret(tmp_path: Path):
    path = tmp_path / "config.json"
    store = ConfigStore(path)
    cfg = VresConfig(configured=True)
    store.save(cfg)
    text = path.read_text(encoding="utf-8")
    assert "password" not in text.lower() or "password_key" in text
    loaded = store.load()
    assert loaded.configured
    assert loaded.database.database == "vres_os"
