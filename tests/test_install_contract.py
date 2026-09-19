"""Static Windows deployment contracts. These do NOT execute PowerShell or certify Windows."""
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_installer_defers_credentials_and_requires_operator_consent():
    text = (ROOT/'install.ps1').read_text()
    for pkg in ('Anthropic.ClaudeCode','PostgreSQL.PostgreSQL.17','Python.Python.3.12','@openai/codex'):
        assert pkg in text
    assert 'Read-Host' in text and 'start vres' in text
    assert 'getpass' not in text and 'CREATE ROLE' not in text
    assert 'controlled-live-test preview' in text


def test_python_runtime_staged_before_active_pointer_changes():
    text = (ROOT/'install.ps1').read_text()
    assert "Join-Path $ReleaseRoot $ReleaseId" in text
    assert text.index("Run $NewPython @('-m','pip','check')") < text.index('Write-JsonAtomic $ActivePath')
    assert text.index("Run 'claude' @('plugin','validate',$StagedPlugin)") < text.index('Write-JsonAtomic $ActivePath')
    assert "[IO.File]::Replace" in text and "$oldPointer" in text
    assert 'Move-Item -LiteralPath $PluginBackup -Destination $PluginTarget' in text
    assert 'plugin marketplace remove' not in text


def test_atomic_pointer_replace_uses_real_backup_path_on_windows_powershell():
    text = (ROOT / 'install.ps1').read_text()
    atomic = text.split('function Write-JsonAtomic', 1)[1].split('function Assert-Managed', 1)[0]
    assert '$backup = "$Path.$id.bak"' in atomic
    assert '[IO.File]::Replace($tmp, $Path, $backup)' in atomic
    assert '[IO.File]::Replace($tmp, $Path, $null)' not in atomic
    assert 'Remove-Item -LiteralPath $backup -Force -ErrorAction SilentlyContinue' in atomic
    assert 'Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue' in atomic


def test_statusline_install_is_transactional_and_uses_staged_runtime():
    text = (ROOT / 'install.ps1').read_text()
    assert "$ClaudeSettingsPath = Join-Path $ClaudeHome 'settings.json'" in text
    assert "$ClaudeSettingsBefore" in text
    assert "'-m','vres_os.statusline','install'" in text
    assert "'--runtime-python',$NewPython" in text
    assert text.index("Write-JsonAtomic $ActivePath") < text.index("'-m','vres_os.statusline','install'")
    assert "[IO.File]::WriteAllBytes($ClaudeSettingsPath, $ClaudeSettingsBefore)" in text
    assert "Remove-Item -LiteralPath $ClaudeSettingsPath -Force -ErrorAction SilentlyContinue" in text


def test_uninstall_removes_only_vres_owned_statusline_before_runtime_removal():
    text = (ROOT / 'uninstall.ps1').read_text()
    assert "-m vres_os.statusline remove --claude-home $home" in text
    assert text.index("-m vres_os.statusline remove") < text.index("Remove-Item -LiteralPath $plugin")


def test_update_uses_same_transaction_implementation():
    text = (ROOT/'update.ps1').read_text()
    assert "install.ps1') -Update" in text
    assert 'pip install' not in text and 'Remove-Item' not in text


def test_uninstall_is_owned_paths_only_and_preserves_data_by_default():
    text=(ROOT/'uninstall.ps1').read_text()
    assert '[switch]$RemoveLocalData' in text and '.vres-managed' in text
    assert 'PostgreSQL databases' in text
    assert 'DROP DATABASE' not in text and 'DROP ROLE' not in text
    assert 'if ($RemoveLocalData)' in text
    assert 'Remove-Item -LiteralPath $root -Recurse' not in text
    assert text.index('SecretStore().delete') < text.index('Remove-Item -LiteralPath $plugin')


def test_launchers_isolate_python_and_preserve_unicode():
    for rel in ['scripts/windows/vres-launch.ps1','scripts/windows/vres-mcp-launch.ps1',
                'plugins/vres-os/bin/vres-hook.ps1','plugins/vres-os/bin/vres-mcp.ps1']:
        text=(ROOT/rel).read_text()
        assert '-I -X utf8 -m vres_os.' in text
        assert 'resolve-runtime.ps1' in text
    hook=(ROOT/'plugins/vres-os/bin/vres-hook.ps1').read_text()
    assert '[Console]::In.ReadToEnd()' not in hook
    assert '1048576' in hook and '.Exception.Message' not in hook


def test_windows_cli_launcher_preserves_unbound_multi_token_argv():
    launcher = (ROOT / 'scripts/windows/vres-launch.ps1').read_text()
    installer = (ROOT / 'install.ps1').read_text()
    assert 'ValueFromRemainingArguments' not in launcher
    assert 'param(' not in launcher.lower()
    assert '@args' in launcher
    assert '& $python -I -X utf8 -m vres_os.cli @args' in launcher
    # The cmd shim owns only runtime dispatch; the PowerShell wrapper must receive
    # the complete original tail so `secret run --env ... -- <child...>` survives.
    assert 'vres-launch.ps1`" %*' in installer


def test_static_windows_release_path_cannot_be_parent_traversal():
    root = Path(__file__).parents[1]
    resolver = (root / "scripts/windows/resolve-runtime.ps1").read_text()
    uninstall = (root / "uninstall.ps1").read_text()
    for text in (resolver, uninstall):
        assert r"^\d{14}-[a-f0-9]{8}$" in text
        assert "Get-Content -Raw -Encoding UTF8" in text
    assert "Get-CimInstance" in uninstall
    assert "pending-install.json" in uninstall


def test_static_python_discovery_checks_supported_side_by_side_versions():
    text = (Path(__file__).parents[1] / "install.ps1").read_text()
    assert "@('-3.13','-3.12')" in text


def test_static_python_probe_treats_missing_selector_as_dependency_absence():
    text = (ROOT / "install.ps1").read_text()
    assert "function Probe-Python" in text
    probe = text.split("function Probe-Python", 1)[1].split("function Find-Python", 1)[0]
    assert "$savedErrorActionPreference = $ErrorActionPreference" in probe
    assert "$ErrorActionPreference = 'SilentlyContinue'" in probe
    assert "$ErrorActionPreference = $savedErrorActionPreference" in probe
    find = text.split("function Find-Python", 1)[1].split("function Write-JsonAtomic", 1)[0]
    assert "Probe-Python 'py'" in find
    assert "Probe-Python 'python'" in find


def test_static_windows_import_smoke_avoids_nested_native_quoting():
    text = (ROOT / "install.ps1").read_text()
    assert "Run $NewPython @('-c','from vres_os.cli import app; from vres_os.mcp_server import mcp; from vres_os.db import migrate')" in text
    assert 'Vres import gate passed' not in text
