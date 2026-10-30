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
    assert "$ClaudeHome=if ($env:CLAUDE_CONFIG_DIR)" in text
    assert "$home=" not in text.lower()
    assert "-m vres_os.statusline remove --claude-home $ClaudeHome" in text
    assert "-m vres_os.claude_contract remove-global --claude-home $ClaudeHome" in text
    assert text.index("-m vres_os.statusline remove") < text.index("Remove-Item -LiteralPath $plugin")


def test_update_uses_same_transaction_implementation():
    text = (ROOT/'update.ps1').read_text()
    assert "install.ps1') -Update" in text
    assert 'pip install' not in text and 'Remove-Item' not in text

def test_maintenance_update_refuses_missing_active_release_before_native_commands():
    """Update cannot silently become an initial install or create a partial Vres plugin."""
    text = (ROOT / 'install.ps1').read_text(encoding='utf-8')
    start = text.index('if ($Update -and (-not (Test-Path -LiteralPath $ActivePath -PathType Leaf)')
    native = text.index('$cv = & claude --version')
    mutation = text.index('New-Item -ItemType Directory -Force -Path $InstallRoot,$ReleaseRoot')
    assert start < native < mutation
    assert '-not (Test-Path -LiteralPath $PluginTarget -PathType Container)' in text[start:native]
    assert 'Update requires an existing active Vres release and installed managed plugin' in text[start:native]


def test_maintenance_update_never_acquires_external_packages_or_checks_postgres_service():
    """No winget/npm/PG prerequisite checks are reachable on the Update path."""
    text = (ROOT / 'install.ps1').read_text(encoding='utf-8')
    prereqs = text.split('foreach ($item in @(', 1)[1].split('# Personal-release inputs', 1)[0]
    assert 'if ($Update) { throw "Update refused: missing $($item[0])' in prereqs
    assert "if ($Update) { throw 'Update refused: compatible Python is missing" in prereqs
    assert prereqs.index('if ($Update) { throw "Update refused: missing') < prereqs.index('Winget-Install $item[1]')
    assert prereqs.index("if ($Update) { throw 'Update refused: compatible Python") < prereqs.index("Winget-Install 'Python.Python.3.12'")
    postgres = text.split('# Maintenance updates never inspect/provision local PostgreSQL', 1)[1]
    assert "if (-not $Update -and -not $UseRemotePostgres" in postgres.split("if ($WithCodex", 1)[0]
    codex = text.split("if ($WithCodex -and -not (Have 'codex'))", 1)[1].split('# Personal plugin discovery', 1)[0]
    assert codex.index("if ($Update) { throw 'Update refused: optional Codex is missing") < codex.index("Run 'npm'")


def test_maintenance_update_preserves_current_user_path_from_recovery_gap():
    """Update leaves the registry-backed user PATH untouched, even if Vres bin is absent."""
    text = (ROOT / 'install.ps1').read_text(encoding='utf-8')
    section = text.split("    $userPath=[Environment]::GetEnvironmentVariable('Path','User')", 1)[1]
    section = section.split("    Remove-Item -LiteralPath (Join-Path $InstallRoot 'pending-install.json')", 1)[0]
    assert 'if ($Update) {' in section
    update, initial_install = section.split('} elseif ($parts -notcontains $Bin) {', 1)
    assert "SetEnvironmentVariable('Path'" not in update
    assert 'will not modify PATH' in update
    assert "[Environment]::SetEnvironmentVariable('Path', (($parts+$Bin)-join ';'), 'User')" in initial_install




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
    assert "Run $NewPython @('-B','-c','from vres_os.cli import app; from vres_os.mcp_server import mcp; from vres_os.db import migrate; from vres_os.autocompact import install_autocompact')" in text
    assert 'Vres import gate passed' not in text


def test_installer_manages_native_autocompact_conservatively_and_transactionally():
    text = (ROOT / 'install.ps1').read_text()
    assert "autocompact_owned" in text
    assert "vres_os.autocompact install" in text
    assert "--owned-before $OwnedBeforeArg" in text
    assert "15% of the native auto-compact window" in text
    assert "~85% of that window remains free" in text
    assert "CLAUDE_CODE_AUTO_COMPACT_WINDOW" not in text
    assert "$ClaudeSettingsBefore" in text
    assert "[IO.File]::WriteAllBytes($ClaudeSettingsPath, $ClaudeSettingsBefore)" in text


def test_uninstall_removes_only_recorded_vres_owned_autocompact_before_runtime_removal():
    text = (ROOT / 'uninstall.ps1').read_text()
    assert "$state.PSObject.Properties['autocompact_owned']" in text
    assert "vres_os.autocompact remove" in text
    assert "--owned $AutoCompactOwnedArg" in text
    assert text.index("-m vres_os.autocompact remove") < text.index("Remove-Item -LiteralPath $plugin")


def test_personal_windows_launchers_use_process_only_remotesigned_not_bypass():
    installer = (ROOT / "install.ps1").read_text(encoding="utf-8")
    assert installer.count("-ExecutionPolicy RemoteSigned -File") == 2
    assert "-ExecutionPolicy Bypass" not in installer
    assert 'vres-launch.ps1`" %*' in installer
    assert 'vres-mcp-launch.ps1`"' in installer
    assert "Set-ExecutionPolicy" not in installer


def test_postinstall_python_imports_disable_bytecode_and_are_rechecked_last():
    installer = (ROOT / "install.ps1").read_text(encoding="utf-8")
    assert "Run $NewPython @('-B','-c','from vres_os.cli import app;" in installer
    assert "Run $NewPython @('-B','-m','vres_os.cli','doctor','--allow-unconfigured','--skip-database')" in installer
    assert "'-B','-m','vres_os.claude_contract','install-global'" in installer
    assert "'-B','-m','vres_os.statusline','install'" in installer
    assert "& $NewPython -I -B -X utf8 -m vres_os.autocompact install" in installer
    last_gate = "Run $Python @('-I','-B','-X','utf8',$ArtifactTool,'verify-installed','--manifest',$ReleaseManifest,'--package-dir',$PackageDir)"
    assert installer.count(last_gate) == 1
    assert installer.index(last_gate) > installer.index('Could not configure Vres-managed native auto-compaction.')
    assert installer.index(last_gate) < installer.index("Remove-Item -LiteralPath (Join-Path $InstallRoot 'pending-install.json') -ErrorAction SilentlyContinue")
