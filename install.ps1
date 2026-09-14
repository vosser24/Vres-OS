#requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$WithEmbeddings,
    [switch]$WithCodex,
    [switch]$UseRemotePostgres,
    [switch]$Update
)
# Installation is interactive, user-scoped and conservative. No database credentials here.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$RepoRoot = $PSScriptRoot
$InstallRoot = Join-Path $env:LOCALAPPDATA 'VresOS'
$Bin = Join-Path $InstallRoot 'bin'
$ReleaseRoot = Join-Path $InstallRoot 'releases'
$ActivePath = Join-Path $InstallRoot 'active-install.json'
$ClaudeHome = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE '.claude' }
$SkillRoot = Join-Path $ClaudeHome 'skills'
$PluginTarget = Join-Path $SkillRoot 'vres-os'
$BackupRoot = Join-Path $InstallRoot 'backups'

function Confirm-Choice([string]$Question, [bool]$Default=$false) {
    $hint = if ($Default) { 'Y/n' } else { 'y/N' }
    $answer = Read-Host "$Question [$hint]"
    if ([string]::IsNullOrWhiteSpace($answer)) { return $Default }
    return $answer.Trim().ToLowerInvariant() -in @('y','yes')
}
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
}
function Have([string]$Name) { return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue) }
function Run([string]$Exe, [string[]]$Arguments) {
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "A required executable failed (exit $LASTEXITCODE): $Exe. Installation stopped." }
}
function Winget-Install([string]$Id) {
    if (-not (Have 'winget')) { throw 'Windows App Installer / winget is required. Install it from Microsoft Store and rerun.' }
    Run 'winget' @('show','--id',$Id,'--exact','--source','winget','--accept-source-agreements')
    Run 'winget' @('install','--id',$Id,'--exact','--source','winget','--accept-package-agreements','--accept-source-agreements')
    Refresh-Path
}
function Probe-Python([string]$Exe, [string[]]$Arguments) {
    # Native launchers such as py.exe write selector-missing messages to stderr.
    # Under the installer's global Stop preference, Windows PowerShell can turn
    # that expected probe failure into a terminating NativeCommandError before
    # Find-Python can inspect LASTEXITCODE. Suppress native probe errors only
    # for this bounded discovery call, then restore strict installer behavior.
    $savedErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'SilentlyContinue'
        $result = & $Exe @Arguments 2>$null
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $savedErrorActionPreference
    }
    if ($exitCode -eq 0) { return ($result | Select-Object -Last 1) }
    return $null
}
function Find-Python {
    # A newer unsupported default Python must not hide an installed supported version.
    $probe = "import sys; print(sys.executable); raise SystemExit(0 if (3,12) <= sys.version_info[:2] < (3,14) else 1)"
    if (Have 'py') {
        foreach ($selector in @('-3.13','-3.12')) {
            $result = Probe-Python 'py' @($selector,'-c',$probe)
            if ($result) { return $result }
        }
    }
    if (Have 'python') {
        $result = Probe-Python 'python' @('-c',$probe)
        if ($result) { return $result }
    }
    return $null
}
function Write-JsonAtomic([string]$Path, $Value) {
    $id = [guid]::NewGuid().ToString('N')
    $tmp = "$Path.$id.tmp"
    $backup = "$Path.$id.bak"
    try {
        [IO.File]::WriteAllText($tmp, ($Value | ConvertTo-Json -Depth 10), (New-Object System.Text.UTF8Encoding $false))
        if (Test-Path -LiteralPath $Path) {
            # Windows PowerShell 5.1 can bind a PowerShell $null passed to File.Replace's
            # backup-path parameter as an illegal empty path. A real same-directory backup
            # keeps replacement atomic and avoids that native/.NET binder edge case.
            [IO.File]::Replace($tmp, $Path, $backup)
        } else {
            [IO.File]::Move($tmp, $Path)
        }
    } finally {
        Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $backup -Force -ErrorAction SilentlyContinue
    }
}
function Assert-Managed([string]$Path) {
    if (Test-Path -LiteralPath $Path) {
        $marker = Join-Path $Path '.vres-managed'
        if (-not (Test-Path -LiteralPath $marker) -or (Get-Content -Raw -Encoding UTF8 -LiteralPath $marker).Trim() -ne 'Vres-OS') {
            throw "Refusing to replace an unmanaged directory: $Path"
        }
        if ((Get-Item -LiteralPath $Path).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Managed path cannot be a junction or symlink.' }
    }
}

if ($env:OS -ne 'Windows_NT') { throw 'This installer is for native Windows only.' }
if ($env:VRES_DATA_DIR -and [IO.Path]::GetFullPath($env:VRES_DATA_DIR) -ne [IO.Path]::GetFullPath($InstallRoot)) { throw 'Remove VRES_DATA_DIR override before using the managed Windows installer.' }
if (Test-Path (Join-Path $InstallRoot 'pending-install.json')) { throw 'An interrupted installation journal exists. Follow docs/INSTALL-WINDOWS.md recovery before retrying.' }
if ((Test-Path $InstallRoot) -and ((Get-Item -LiteralPath $InstallRoot).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Install root must not be a junction or symlink.' }
# A detached worker can outlive Claude. Do not overwrite a runtime used by such a process.
$runningVres = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" -ErrorAction Stop | Where-Object {
    $_.ExecutablePath -and $_.ExecutablePath.StartsWith(($InstallRoot.TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)
})
if ($runningVres.Count -gt 0) { throw 'A Vres Python worker is still running. Let it finish or stop that specific process before updating.' }

if (-not (Test-Path (Join-Path $RepoRoot 'pyproject.toml')) -or -not (Test-Path (Join-Path $RepoRoot 'plugins\vres-os\.claude-plugin\plugin.json'))) {
    throw 'Extract the COMPLETE source ZIP before running install.ps1.'
}
if (Get-Process -Name 'claude','codex' -ErrorAction SilentlyContinue) {
    throw 'Close Claude Code and Codex sessions first, then run the installer in a separate PowerShell window.'
}
if (Test-Path $ActivePath) {
    if (-not $Update -and -not (Confirm-Choice 'Vres is already installed. Stage an updated runtime?' $false)) { exit 0 }
}
if (Test-Path (Join-Path $InstallRoot 'venv')) {
    throw 'A legacy in-place Vres runtime exists. Preserve its config/credential and follow the migration section in docs/INSTALL-WINDOWS.md; it will not be overwritten.'
}
Assert-Managed $PluginTarget
Write-Host 'Vres-OS controlled-live-test preview. Not production-verified.' -ForegroundColor Yellow
Write-Host 'A secure separate window will request database credentials after you type start vres in Claude.'
if (-not (Confirm-Choice 'Install this preview for a disposable project and dedicated test database?' $false)) { exit 0 }
foreach ($item in @(@('git','Git.Git'), @('claude','Anthropic.ClaudeCode'))) {
    if (-not (Have $item[0])) {
        if (-not (Confirm-Choice "$($item[0]) is missing. Install its Windows package?" $true)) { throw "$($item[0]) is required." }
        Winget-Install $item[1]
    }
}
$Python = Find-Python
if (-not $Python) {
    if (-not (Confirm-Choice 'Python 3.12 or 3.13 is missing. Install Python 3.12?' $true)) { throw 'Compatible Python is required.' }
    Winget-Install 'Python.Python.3.12'
    $Python = Find-Python
    if (-not $Python) { throw 'Open a fresh terminal so Python becomes visible, then rerun.' }
}
# The user-scoped skills-directory plugin facility requires a current Claude version.
$cv = & claude --version
if ($LASTEXITCODE -ne 0 -or "$cv" -notmatch '(\d+\.\d+\.\d+)') { throw 'Could not determine Claude Code version.' }
if ([version]$Matches[1] -lt [version]'2.1.246') { throw 'Update Claude Code to 2.1.246 or newer, then rerun. This preview does not emulate older plugin APIs.' }
if (-not $UseRemotePostgres -and -not (Have 'psql') -and -not (Get-Service -Name 'postgresql*' -ErrorAction SilentlyContinue)) {
    if (Confirm-Choice 'Local PostgreSQL was not detected. Install PostgreSQL 17?' $true) { Winget-Install 'PostgreSQL.PostgreSQL.17' }
    else { throw 'Install PostgreSQL, or rerun with -UseRemotePostgres for an existing server.' }
}
if ($WithCodex -and -not (Have 'codex')) {
    if (-not (Have 'npm')) { Winget-Install 'OpenJS.NodeJS.LTS' }
    Run 'npm' @('install','-g','@openai/codex')
    Refresh-Path
}
# Personal plugin discovery avoids destructive marketplace removal and cache re-registration.
$installedPlugins = & claude plugin list --json
if ($LASTEXITCODE -ne 0) { throw 'Claude plugin inspection failed.' }
if ("$installedPlugins" -match 'vres-os@vres-os') {
    throw 'An older marketplace copy of Vres is enabled. Remove that Vres copy explicitly using the migration guide; unrelated plugins are never touched.'
}
New-Item -ItemType Directory -Force -Path $InstallRoot,$ReleaseRoot,$BackupRoot,$SkillRoot | Out-Null
$installLock = [IO.File]::Open((Join-Path $InstallRoot 'installation.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
$ReleaseId = (Get-Date -Format 'yyyyMMddHHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
$NewRelease = Join-Path $ReleaseRoot $ReleaseId
$DistributionRoot = Join-Path $NewRelease 'distribution'
$StagedPlugin = Join-Path $DistributionRoot 'vres-os'
$PluginBackup = Join-Path $BackupRoot $ReleaseId
$oldPointer = if (Test-Path $ActivePath) { Get-Content -Raw -Encoding UTF8 $ActivePath | ConvertFrom-Json } else { $null }
$pluginMoved = $false
$published = $false
try {
    New-Item -ItemType Directory -Force -Path $NewRelease,$DistributionRoot | Out-Null
    # Build venv at its permanent path: Windows entry points contain absolute paths.
    Run $Python @('-m','venv',(Join-Path $NewRelease 'venv'))
    $NewPython = Join-Path $NewRelease 'venv\Scripts\python.exe'
    $extras = if ($WithEmbeddings) { 'full,embeddings' } else { 'full' }
    Run $NewPython @('-m','pip','install',"$RepoRoot[$extras]")
    Run $NewPython @('-m','pip','check')
    Run $NewPython @('-c','from vres_os.cli import app; from vres_os.mcp_server import mcp; from vres_os.db import migrate')
    $freeze = & $NewPython -m pip freeze --all
    if ($LASTEXITCODE -ne 0) { throw 'Dependency inventory failed.' }
    [IO.File]::WriteAllLines((Join-Path $NewRelease 'resolved-dependencies.txt'), [string[]]$freeze, (New-Object System.Text.UTF8Encoding $false))
    Copy-Item -Recurse -LiteralPath (Join-Path $RepoRoot 'plugins\vres-os') -Destination $StagedPlugin
    [IO.File]::WriteAllText((Join-Path $StagedPlugin '.vres-managed'), 'Vres-OS')
    Run 'claude' @('plugin','validate',$StagedPlugin)
    Run $NewPython @('-m','vres_os.cli','doctor','--allow-unconfigured')
    Write-JsonAtomic (Join-Path $InstallRoot 'pending-install.json') @{ product='Vres-OS'; new_release=$ReleaseId; previous=$oldPointer; plugin_backup=$PluginBackup; plugin_path=$PluginTarget; had_plugin=(Test-Path $PluginTarget) }
    # Only now change the selected runtime/plugin. Roll back both on failure.
    if (Test-Path $PluginTarget) { Move-Item -LiteralPath $PluginTarget -Destination $PluginBackup; $pluginMoved=$true }
    Copy-Item -Recurse -LiteralPath $StagedPlugin -Destination $PluginTarget
    Run 'claude' @('plugin','validate',$PluginTarget)
    New-Item -ItemType Directory -Force -Path $Bin | Out-Null
    # Backup launcher scripts too: old runtimes must not depend on a new, incompatible launcher.
    $BinBackup = Join-Path $NewRelease 'previous-bin'
    Copy-Item -Recurse -LiteralPath $Bin -Destination $BinBackup
    Copy-Item -Force -Path (Join-Path $RepoRoot 'scripts\windows\*.ps1') -Destination $Bin
    [IO.File]::WriteAllText((Join-Path $Bin 'vres.cmd'), "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"%~dp0vres-launch.ps1`" %*`r`n", [Text.Encoding]::ASCII)
    [IO.File]::WriteAllText((Join-Path $Bin 'vres-mcp.cmd'), "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"%~dp0vres-mcp-launch.ps1`"`r`n", [Text.Encoding]::ASCII)
    Write-JsonAtomic $ActivePath @{product='Vres-OS'; release=$ReleaseId; previous=$oldPointer; plugin_path=$PluginTarget; installed_at=(Get-Date -Format o)}
    $published=$true
    $userPath=[Environment]::GetEnvironmentVariable('Path','User')
    $parts=@($userPath -split ';' | Where-Object { $_ })
    if ($parts -notcontains $Bin) { [Environment]::SetEnvironmentVariable('Path', (($parts+$Bin)-join ';'), 'User') }
    Remove-Item -LiteralPath (Join-Path $InstallRoot 'pending-install.json') -ErrorAction SilentlyContinue
    Write-Host 'Vres preview installed. This does not certify Windows live behavior.' -ForegroundColor Green
    Write-Host "Release: $ReleaseId"
    Write-Host 'Open a fresh terminal, enter a disposable project, launch claude, then say: start vres'
    Write-Host 'Credentials belong in the separate setup console, never in Claude chat.'
} catch {
    if ($published) {
        if ($oldPointer) { Write-JsonAtomic $ActivePath $oldPointer }
        elseif (Test-Path $ActivePath) { Remove-Item -LiteralPath $ActivePath }
    }
    if (Test-Path (Join-Path $NewRelease 'previous-bin')) {
        Remove-Item -LiteralPath $Bin -Recurse -Force
        Copy-Item -Recurse -LiteralPath (Join-Path $NewRelease 'previous-bin') -Destination $Bin
    }
    if (Test-Path (Join-Path $InstallRoot 'pending-install.json')) {
        if (Test-Path $PluginTarget) { Assert-Managed $PluginTarget; Remove-Item -LiteralPath $PluginTarget -Recurse -Force }
        if ($pluginMoved -and (Test-Path $PluginBackup)) { Move-Item -LiteralPath $PluginBackup -Destination $PluginTarget }
    }
    if (Test-Path (Join-Path $InstallRoot 'pending-install.json')) { Remove-Item -LiteralPath (Join-Path $InstallRoot 'pending-install.json') }
    Write-Warning 'Installation failed. Previous runtime/plugin restored where they existed. A failed staged release is retained for diagnosis. No database migration was performed by this installer.'
    throw
} finally {
    $installLock.Dispose()
}
