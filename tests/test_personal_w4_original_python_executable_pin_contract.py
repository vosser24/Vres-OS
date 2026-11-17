"""W4 Python bootstrap pin SOURCE-ONLY contract; AUTHORED / NOT_RUN.

Reading source text is an authored future regression. Never run this test on
the owner's Windows machine or treat it as Python/Tk DLL/publisher trust.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_original_updater_to_installer_python_pin_is_one_identity():
    updater, install = _read("update.ps1"), _read("install.ps1")
    for script in (updater, install):
        assert "$W4SourceInterlock = 'HELD_SOURCE_ONLY'" in script
        assert "[string]$PythonExecutable" in script
        assert "[string]$PythonSha256" in script
    pins = "-PythonExecutable $PythonExecutable -PythonSha256 $PythonSha256"
    assert pins in updater and pins in install
    assert updater.index("VRES_W4_HELD") < updater.index("Get-FileHash -LiteralPath $PythonExecutable")
    assert install.index("VRES_W4_HELD_CLOSURE") < install.index("function Confirm-PinnedPython")
    assert install.index("$Python = Confirm-PinnedPython") < install.index(
        "Run $Python @('-I','-B','-X','utf8'")
    assert "Find-Python" not in install and "Probe-Python" not in install
    assert "Winget-Install 'Python.Python.3.12'" not in install


def test_direct_pin_must_be_rechecked_before_any_bootstrap_python():
    install = _read("install.ps1")
    checker = install.split("function Confirm-PinnedPython", 1)[1].split(
        "function Write-JsonAtomic", 1)[0]
    assert "Get-FileHash -LiteralPath $approved -Algorithm SHA256" in checker
    assert checker.index("Get-FileHash") < checker.index("& $approved -I -S -B -c $probe")
    assert "[IO.FileAttributes]::ReparsePoint" in checker
    assert "sys.version_info[:2] < (3,14)" in checker
    assert "sys.maxsize > 2**32" in checker
    assert "[StringComparison]::OrdinalIgnoreCase" in checker
    assert "return $approved" in checker


def test_original_release_and_recovery_were_not_replaced():
    install = _read("install.ps1")
    update = _read("update.ps1")
    for token in ("release_artifact.py", "verify-root-wheel",
                  "install_recovery.py", "pending-install.json",
                  "Write-JsonAtomic $ActivePath"):
        assert token in install
    assert "install.ps1') -Update" in update
    assert "git_preflight" in update and "windows_update" in update
