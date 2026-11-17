#requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$WithEmbeddings,
    [switch]$WithCodex,
    [switch]$UseRemotePostgres,
    [switch]$Update,
    # Required: the full 40-hex source commit the operator approved; this checkout's HEAD must be it.
    [string]$SourceCommit,
    [string]$SourceTree,
    [string]$GitExecutable,
    [string]$GitSha256,
    [string]$WheelhouseDir,
    [string]$WheelLockFile,
    [string]$WheelLockSha256
)
# Installation is interactive, user-scoped and conservative. No database credentials here.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# ORIGINAL installer source-owned mechanical hold BEFORE any installed P2,
# Claude profile, source Python, release staging or rollback operation.
$W4SourceInterlock = 'HELD_SOURCE_ONLY'
$W4HoldsPath = Join-Path $PSScriptRoot 'w4-operations-holds.json'
if (-not (Test-Path -LiteralPath $W4HoldsPath -PathType Leaf)) {
    throw 'VRES_W4_HELD: operation-hold ledger missing; no installation started.'
}
try { $W4Holds = Get-Content -Raw -Encoding UTF8 -LiteralPath $W4HoldsPath | ConvertFrom-Json }
catch { throw 'VRES_W4_HELD: operation-hold ledger invalid; no installation started.' }
$W4RequestedGate = if ($Update.IsPresent) { $W4Holds.windows_update } else { $W4Holds.fresh_install }
if ($W4SourceInterlock -cne 'REVIEWED_RELEASE_CLEARED' -or
    $W4Holds.schema -cne 'vres-w4-operations-holds/1' -or
    $W4Holds.status -cne 'REVIEWED_RELEASE_CLEARED' -or
    $W4RequestedGate -cne 'REVIEWED_RELEASE_CLEARED') {
    throw 'VRES_W4_HELD: original installer SOURCE ONLY; no P2, native Claude, DB, stage or rollback permitted.'
}
# Independent source-owned gate: changing only the generic hold cannot unlock
# unverified interpreter/Tk/whole-product wheels or the OPEN host incidents.
$W4RuntimeClosureInterlock = 'HELD_INTERPRETER_TK_AND_HASH_LOCKED_WHEELS'
$W4HostInterlock = 'HELD_SCHEMA_048_AND_NATIVE_CLAUDE_HOOKS'
if ($W4RuntimeClosureInterlock -cne 'INDEPENDENTLY_VERIFIED_AND_AUTHORIZED' -or
    $W4HostInterlock -cne 'INCIDENTS_RESOLVED_AND_AUTHORIZED') {
    throw 'VRES_W4_HELD_CLOSURE: runtime wheels, Schema-048 and native Claude are not cleared.'
}
# A direct call to the ORIGINAL installer must pass the ORIGINAL updater's
# pinned Git checkout verification, not just a 40-character commit string.
# Holds ABOVE remain first, and an independent trusted source gate is still required.
if ($SourceCommit -notmatch '^[0-9a-fA-F]{40}\z' -or
    $SourceTree -notmatch '^[0-9a-fA-F]{40}\z') {
    throw 'Installation refused: independently approved full -SourceCommit and -SourceTree required.'
}
& (Join-Path $PSScriptRoot 'update.ps1') -PreflightOnly -SourceCommit $SourceCommit -SourceTree $SourceTree -GitExecutable $GitExecutable -GitSha256 $GitSha256

# Complete OFFLINE binary wheel input, approved independently of this checkout.
# Pip must neither reach an index nor build an unpinned sdist or Vres source tree.
if ([string]::IsNullOrWhiteSpace($WheelhouseDir) -or
    [string]::IsNullOrWhiteSpace($WheelLockFile) -or
    -not [IO.Path]::IsPathRooted($WheelhouseDir) -or
    -not [IO.Path]::IsPathRooted($WheelLockFile) -or
    $WheelLockSha256 -notmatch '^[0-9a-fA-F]{64}\z') {
    throw 'Installation refused: absolute -WheelhouseDir, -WheelLockFile and approved -WheelLockSha256 are required.'
}
$WheelhouseDir = [IO.Path]::GetFullPath($WheelhouseDir)
$WheelLockFile = [IO.Path]::GetFullPath($WheelLockFile)
if (-not (Test-Path -LiteralPath $WheelhouseDir -PathType Container) -or
    -not (Test-Path -LiteralPath $WheelLockFile -PathType Leaf)) {
    throw 'Installation refused: locked offline requirements or wheelhouse missing.'
}
foreach ($candidate in @($WheelhouseDir, $WheelLockFile)) {
    if ((Get-Item -LiteralPath $candidate -ErrorAction Stop).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw 'Installation refused: wheelhouse and requirements cannot be reparse points.'
    }
}
$CheckoutPrefix = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd([char[]]@('\','/')) + '\'
if ($WheelhouseDir.StartsWith($CheckoutPrefix, [StringComparison]::OrdinalIgnoreCase) -or
    $WheelLockFile.StartsWith($CheckoutPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Installation refused: offline dependencies must be outside the immutable source checkout.'
}
$WheelFiles = @(Get-ChildItem -Force -LiteralPath $WheelhouseDir -ErrorAction Stop)
if ($WheelFiles.Count -eq 0) { throw 'Installation refused: empty offline wheelhouse.' }
foreach ($wheel in $WheelFiles) {
    if ($wheel.PSIsContainer -or $wheel.Extension -cne '.whl' -or
        ($wheel.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'Installation refused: wheelhouse must contain only ordinary .whl files.'
    }
}
if ((Get-FileHash -LiteralPath $WheelLockFile -Algorithm SHA256).Hash -cne $WheelLockSha256.ToUpperInvariant()) {
    throw 'Installation refused: requirements lock differs from approved SHA-256.'
}
$WheelLockText = [IO.File]::ReadAllText($WheelLockFile)
$ExpectedRootRequirement = if ($WithEmbeddings) { 'vres-os[full,embeddings]==0.2.0a1' } else { 'vres-os[full]==0.2.0a1' }
if ($WheelLockText.IndexOf($ExpectedRootRequirement, [StringComparison]::OrdinalIgnoreCase) -lt 0) {
    throw 'Installation refused: lock lacks the selected original Vres full extras/version.'
}
# No nested -r/-c directives, URLs, index switches or local direct references.
# A regular pip-tools --hash=sha256 continuation is the sole allowed switch.
if ($WheelLockText -match '(?im)^\s*-(?!-hash=sha256:)' -or
    $WheelLockText -match '(?i)(?:https?|ftp|git|file)://' -or
    $WheelLockText -match '(?m)^[^#\r\n]*@') {
    throw 'Installation refused: requirements contain indirect/remote instructions.'
}

# Check all candidate wheel SHA-256 digests BEFORE pip, not just the lock file.
# This is not independent wheel publisher trust or NTFS/ACL/isolation closure.
foreach ($wheel in $WheelFiles) {
    $Digest = (Get-FileHash -LiteralPath $wheel.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($WheelLockText.IndexOf(('--hash=sha256:' + $Digest), [StringComparison]::OrdinalIgnoreCase) -lt 0) {
        throw 'Installation refused: wheelhouse archive SHA-256 absent from approved requirements lock.'
    }
}
$RootWheels = @($WheelFiles | Where-Object {
    $_.Name -cmatch '^vres_os-0[.]2[.]0a1-(?:[0-9][A-Za-z0-9_.]*-)?[A-Za-z0-9_.]+-[A-Za-z0-9_.]+-[A-Za-z0-9_.]+[.]whl$'
})
if ($RootWheels.Count -ne 1) {
    throw 'Installation refused: exactly one original Vres 0.2.0a1 root wheel is required.'
}
$RepoRoot = $PSScriptRoot
$InstallRoot = Join-Path $env:LOCALAPPDATA 'VresOS'
$Bin = Join-Path $InstallRoot 'bin'
$ReleaseRoot = Join-Path $InstallRoot 'releases'
$ActivePath = Join-Path $InstallRoot 'active-install.json'
$ClaudeHome = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE '.claude' }
$SkillRoot = Join-Path $ClaudeHome 'skills'
$PluginTarget = Join-Path $SkillRoot 'vres-os'
$BackupRoot = Join-Path $InstallRoot 'backups'
$GlobalClaudePath = Join-Path $ClaudeHome 'CLAUDE.md'
$GlobalRulesPath = Join-Path $ClaudeHome 'vres-rules.md'
$ClaudeSettingsPath = Join-Path $ClaudeHome 'settings.json'
$GlobalClaudeBefore = $null
$GlobalRulesBefore = $null
$ClaudeSettingsBefore = $null
# Capture protected profile bytes later at the original recovery boundary.

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
function Restore-OriginalBytesAtomic([string]$Path, [byte[]]$Original) {
    # Attempted-change-only restoration. Never delete an originally absent
    # Claude file: it may have been independently created after the snapshot.
    if ($null -eq $Original) {
        if (Test-Path -LiteralPath $Path) {
            throw "Recovery HELD: originally absent Claude file exists: $Path. Keep the journal; do not auto-delete."
        }
        return
    }
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        throw "Recovery HELD: original Claude parent directory is missing: $parent"
    }
    $tmp = "$Path.$([guid]::NewGuid().ToString('N')).tmp"
    $backup = "$Path.$([guid]::NewGuid().ToString('N')).bak"
    try {
        [IO.File]::WriteAllBytes($tmp, $Original)
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            [IO.File]::Replace($tmp, $Path, $backup)
        } elseif (Test-Path -LiteralPath $Path) {
            throw "Recovery HELD: Claude path is not an ordinary file: $Path"
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
if (Test-Path (Join-Path $InstallRoot 'pending-install.json')) { throw "An interrupted installation journal exists. Inspect it with: python -I `"$(Join-Path $RepoRoot 'src\vres_os\install_recovery.py')`" inspect --install-root `"$InstallRoot`" (then recover --confirm), or follow docs/INSTALL-WINDOWS.md." }
if ((Test-Path $InstallRoot) -and ((Get-Item -LiteralPath $InstallRoot).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Install root must not be a junction or symlink.' }
# A detached worker can outlive Claude. Do not overwrite a runtime used by such a process.
$runningVres = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" -ErrorAction Stop | Where-Object {
    $_.ExecutablePath -and $_.ExecutablePath.StartsWith(($InstallRoot.TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)
})
if ($runningVres.Count -gt 0) { throw 'A Vres Python worker is still running. Let it finish or stop that specific process before updating.' }

if (-not (Test-Path (Join-Path $RepoRoot '.git')) -or
    -not (Test-Path (Join-Path $RepoRoot 'pyproject.toml')) -or
    -not (Test-Path (Join-Path $RepoRoot 'plugins\vres-os\.claude-plugin\plugin.json')) -or
    -not (Test-Path (Join-Path $RepoRoot 'rules\vres-rules.md'))) {
    throw 'Run install.ps1 from a complete git checkout of the approved release commit (clone the release git bundle). Source ZIPs are not accepted.'
}
if (Get-Process -Name 'claude','codex' -ErrorAction SilentlyContinue) {
    throw 'Close Claude Code and Codex sessions first, then run the installer in a separate PowerShell window.'
}
# Update mode is maintenance of an existing managed current-user release, never an implicit
# fresh installation. Refuse missing pointers/plugins before any external prerequisite command.
if ($Update -and (-not (Test-Path -LiteralPath $ActivePath -PathType Leaf) -or
                  -not (Test-Path -LiteralPath $PluginTarget -PathType Container))) {
    throw 'Update requires an existing active Vres release and installed managed plugin. No new installation was started.'
}
if (Test-Path $ActivePath) {
    if (-not $Update -and -not (Confirm-Choice 'Vres is already installed. Stage an updated runtime?' $false)) { exit 0 }
}
if (Test-Path (Join-Path $InstallRoot 'venv')) {
    throw 'A legacy in-place Vres runtime exists. Preserve its config/credential and follow the migration section in docs/INSTALL-WINDOWS.md; it will not be overwritten.'
}
Assert-Managed $PluginTarget
# Capture pre-existing surfaces BEFORE any newly staged bin/plugin is created.
$HadPluginBefore = Test-Path -LiteralPath $PluginTarget -PathType Container
$BinExistedBefore = Test-Path -LiteralPath $Bin -PathType Container
Write-Host 'Vres-OS controlled-live-test preview. Not production-verified.' -ForegroundColor Yellow
if ($Update) {
    Write-Host "Update target: the existing Vres installation for this Windows user, from pinned commit $SourceCommit." -ForegroundColor Yellow
    Write-Host 'Database health will NOT be checked during this update. No PostgreSQL access is authorized; database-dependent features remain blocked until separately accepted.' -ForegroundColor Yellow
    if (-not (Confirm-Choice 'Update the existing Vres installation for this Windows user from the pinned commit, without checking the database?' $false)) { exit 0 }
} else {
    Write-Host 'A secure separate window will request database credentials after you type start vres in Claude.'
    if (-not (Confirm-Choice 'Install this preview for a disposable project and dedicated test database?' $false)) { exit 0 }
}
foreach ($item in @(@('git','Git.Git'), @('claude','Anthropic.ClaudeCode'))) {
    if (-not (Have $item[0])) {
        if ($Update) { throw "Update refused: missing $($item[0]); no prerequisite package will be installed during a Vres update." }
        if (-not (Confirm-Choice "$($item[0]) is missing. Install its Windows package?" $true)) { throw "$($item[0]) is required." }
        Winget-Install $item[1]
    }
}
$Python = Find-Python
if (-not $Python) {
    if ($Update) { throw 'Update refused: compatible Python is missing; no prerequisite package will be installed during a Vres update.' }
    if (-not (Confirm-Choice 'Python 3.12 or 3.13 is missing. Install Python 3.12?' $true)) { throw 'Compatible Python is required.' }
    Winget-Install 'Python.Python.3.12'
    $Python = Find-Python
    if (-not $Python) { throw 'Open a fresh terminal so Python becomes visible, then rerun.' }
}
# Personal-release inputs (pinned migrations 001-041, no C2B/R0/F2 experimental files) are
# validated from the source tree before any install root, venv or package is created.
# Hygiene-only reorder; release_artifact still imports release_inputs before
# internal verification. Trusted out-of-band pre-execution proof is NOT provided.
Run $Python @('-I','-B','-X','utf8',(Join-Path $RepoRoot 'src\vres_os\release_artifact.py'),'check','--root',$RepoRoot,'--source-commit',$SourceCommit)
Run $Python @('-I','-B','-X','utf8',(Join-Path $RepoRoot 'src\vres_os\release_inputs.py'),'--root',$RepoRoot)
# The user-scoped skills-directory plugin facility requires a current Claude version.
$cv = & claude --version
if ($LASTEXITCODE -ne 0 -or "$cv" -notmatch '(\d+\.\d+\.\d+)') { throw 'Could not determine Claude Code version.' }
if ([version]$Matches[1] -lt [version]'2.1.246') { throw 'Update Claude Code to 2.1.246 or newer, then rerun. This preview does not emulate older plugin APIs.' }
# Maintenance updates never inspect/provision local PostgreSQL, even to check whether
# an executable/service exists. DB-dependent behavior stays disabled under the incident.
if (-not $Update -and -not $UseRemotePostgres -and -not (Have 'psql') -and -not (Get-Service -Name 'postgresql*' -ErrorAction SilentlyContinue)) {
    if (Confirm-Choice 'Local PostgreSQL was not detected. Install PostgreSQL 17?' $true) { Winget-Install 'PostgreSQL.PostgreSQL.17' }
    else { throw 'Install PostgreSQL, or rerun with -UseRemotePostgres for an existing server.' }
}
if ($WithCodex -and -not (Have 'codex')) {
    if ($Update) { throw 'Update refused: optional Codex is missing; no npm/global package changes during a Vres update.' }
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
$AutoCompactOwnedBefore = $false
if ($oldPointer -and $oldPointer.PSObject.Properties['autocompact_owned']) {
    $AutoCompactOwnedBefore = [bool]$oldPointer.autocompact_owned
}
$pluginMoved = $false
$published = $false
$ClaudeContractAttempted = $false
$ClaudeSettingsAttempted = $false
try {
    New-Item -ItemType Directory -Force -Path $NewRelease,$DistributionRoot | Out-Null
    # Stage the release files of the pinned commit, read from its verified git objects (never from
    # working-tree files), with a manifest of commit/tree/blob ids and SHA-256. Everything below
    # installs from this copy and runs the staged tools; $RepoRoot is not read again.
    $StagedSource = Join-Path $NewRelease 'source'
    $ReleaseManifest = Join-Path $NewRelease 'release-manifest.json'
    Run $Python @('-I','-X','utf8',(Join-Path $RepoRoot 'src\vres_os\release_artifact.py'),'stage','--root',$RepoRoot,'--out',$StagedSource,'--manifest',$ReleaseManifest,'--source-commit',$SourceCommit)
    $ArtifactTool = Join-Path $StagedSource 'src\vres_os\release_artifact.py'
    # Original root wheel must match exact staged Git source before any pip invocation.
    Run $Python @('-I','-X','utf8',$ArtifactTool,'verify-root-wheel','--manifest',$ReleaseManifest,'--wheel',$RootWheels[0].FullName)
    # Build venv at its permanent path: Windows entry points contain absolute paths.
    Run $Python @('-m','venv',(Join-Path $NewRelease 'venv'))
    $NewPython = Join-Path $NewRelease 'venv\Scripts\python.exe'
    # Only the independently pinned, offline complete wheel lock may supply original Vres
    # plus full dependencies. No source build, remote resolver or pip bootstrap is authorized.
    # The pip report is separate audit evidence, not external publisher/toolchain trust.
    $PipVersionCheck = 'import pip, re, sys; m = re.match(''([0-9]+)[.]([0-9]+)'', pip.__version__); sys.exit(0 if m and (int(m[1]), int(m[2])) >= (23, 0) else 1)'
    Run $NewPython @('-I','-c',$PipVersionCheck)
    $PipReport = Join-Path $NewRelease 'pip-install-report.json'
    # No bytecode is written at install time, so the installed package can be verified as exactly the release.
    Run $NewPython @('-I','-m','pip','--isolated','install','--no-compile','--no-index','--no-cache-dir','--only-binary=:all:','--require-hashes','--find-links',$WheelhouseDir,'--report',$PipReport,'-r',$WheelLockFile)
    Run $NewPython @('-I','-m','pip','--isolated','check')
    # Locate the package without importing it (-B: no bytecode), then verify its complete file inventory:
    # exactly the released modules and migrations, no compiled, native, .pth or other file. This is a
    # point-in-time installation check, not ongoing integrity monitoring.
    $PackageDir = & $NewPython -I -B -c 'import importlib.util as u; print(*u.find_spec(''vres_os'').submodule_search_locations)'
    if ($LASTEXITCODE -ne 0) { throw 'Could not locate the installed Vres package.' }
    $PackageDir = "$($PackageDir | Select-Object -Last 1)"
    if (-not $PackageDir.StartsWith((Join-Path $NewRelease 'venv') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'The located Vres package is not inside the new runtime.' }
    Run $Python @('-I','-X','utf8',$ArtifactTool,'verify-installed','--manifest',$ReleaseManifest,'--package-dir',$PackageDir)
    Run $NewPython @('-B','-c','from vres_os.cli import app; from vres_os.mcp_server import mcp; from vres_os.db import migrate; from vres_os.autocompact import install_autocompact')
    $freeze = & $NewPython -I -m pip --isolated freeze --all
    if ($LASTEXITCODE -ne 0) { throw 'Dependency inventory failed.' }
    [IO.File]::WriteAllLines((Join-Path $NewRelease 'resolved-dependencies.txt'), [string[]]$freeze, (New-Object System.Text.UTF8Encoding $false))
    # Validate pip's report and refuse any wheel lacking a recorded SHA-256.
    $PipReportCheck = 'import json, re, sys; g = lambda d, k: d.get(k) if isinstance(d, dict) else None; r = json.load(open(sys.argv[1], encoding=''utf-8'')); i = g(r, ''install''); ok = g(r, ''version'') == ''1'' and isinstance(i, list) and len(i) > 0 and all(isinstance(g(e, ''metadata''), dict) and bool(g(g(e, ''metadata''), ''name'')) and bool(g(g(e, ''metadata''), ''version'')) for e in i); sha = lambda e: g(g(g(g(e, ''download_info''), ''archive_info''), ''hashes''), ''sha256''); sys.exit(1) if not ok else print(len(i), sum(1 for e in i if not (isinstance(sha(e), str) and re.fullmatch(''[0-9a-fA-F]{64}'', sha(e)))))'
    $PipReportCounts = "$(Run $Python @('-I','-c',$PipReportCheck,$PipReport) | Select-Object -Last 1)".Split(' ')
    if ($PipReportCounts.Count -ne 2 -or $PipReportCounts[1] -cne '0') {
        throw 'Installation refused: pip report contains unresolved or un-hashed dependency records.'
    }
    Write-Host "Offline hash-locked pip report: $($PipReportCounts[0]) packages; no un-hashed records reported. Independent wheel trust, Python/Tk/DLLs and host clearance remain separate gates."
    Copy-Item -Recurse -LiteralPath (Join-Path $StagedSource 'plugins\vres-os') -Destination $StagedPlugin
    Run $Python @('-I','-X','utf8',$ArtifactTool,'verify-tree','--manifest',$ReleaseManifest,'--prefix','plugins/vres-os','--dir',$StagedPlugin)
    [IO.File]::WriteAllText((Join-Path $StagedPlugin '.vres-managed'), 'Vres-OS')
    Run 'claude' @('plugin','validate',$StagedPlugin)
    # The doctor preflight skips database contact and reports PostgreSQL NOT CHECKED, not healthy. Database
    # isolation of the other installer subprocesses (pip, claude plugin validate) is not independently verified.
    Run $NewPython @('-B','-m','vres_os.cli','doctor','--allow-unconfigured','--skip-database')
    $GlobalClaudeBefore = if (Test-Path -LiteralPath $GlobalClaudePath -PathType Leaf) { [IO.File]::ReadAllBytes($GlobalClaudePath) } else { $null }
    $GlobalRulesBefore = if (Test-Path -LiteralPath $GlobalRulesPath -PathType Leaf) { [IO.File]::ReadAllBytes($GlobalRulesPath) } else { $null }
    $ClaudeSettingsBefore = if (Test-Path -LiteralPath $ClaudeSettingsPath -PathType Leaf) { [IO.File]::ReadAllBytes($ClaudeSettingsPath) } else { $null }
    # Persist and verify exact snapshots of the Claude files and launchers this installer may change,
    # before the journal and before any mutation, so an interrupted install can be recovered exactly.
    Run $Python @('-I','-X','utf8',(Join-Path $StagedSource 'src\vres_os\install_recovery.py'),'snapshot','--install-root',$InstallRoot,'--claude-home',$ClaudeHome,'--release',$ReleaseId)
    $ClaudeSnapshot = Join-Path $InstallRoot "install-recovery\$ReleaseId"
    Write-JsonAtomic (Join-Path $InstallRoot 'pending-install.json') @{ product='Vres-OS'; new_release=$ReleaseId; previous=$oldPointer; plugin_backup=$PluginBackup; plugin_path=$PluginTarget; had_plugin=$HadPluginBefore; claude_snapshot=$ClaudeSnapshot; claude_home=$ClaudeHome }
    # Only now change the selected runtime/plugin. Roll back both on failure.
    if (Test-Path $PluginTarget) { Move-Item -LiteralPath $PluginTarget -Destination $PluginBackup; $pluginMoved=$true }
    Copy-Item -Recurse -LiteralPath $StagedPlugin -Destination $PluginTarget
    Run $Python @('-I','-X','utf8',$ArtifactTool,'verify-tree','--manifest',$ReleaseManifest,'--prefix','plugins/vres-os','--dir',$PluginTarget,'--allow-extra','.vres-managed')
    Run 'claude' @('plugin','validate',$PluginTarget)
    New-Item -ItemType Directory -Force -Path $Bin | Out-Null
    # Backup launcher scripts too: old runtimes must not depend on a new, incompatible launcher.
    $BinBackup = Join-Path $NewRelease 'previous-bin'
    Copy-Item -Recurse -LiteralPath $Bin -Destination $BinBackup
    Copy-Item -Force -Path (Join-Path $StagedSource 'scripts\windows\*.ps1') -Destination $Bin
    # Process-only RemoteSigned permits our local staged .ps1 launchers on a default Restricted system.
    # Unlike Bypass it still enforces signed-script checks on Mark-of-the-Web scripts.
    [IO.File]::WriteAllText((Join-Path $Bin 'vres.cmd'), "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File `"%~dp0vres-launch.ps1`" %*`r`n", [Text.Encoding]::ASCII)
    [IO.File]::WriteAllText((Join-Path $Bin 'vres-mcp.cmd'), "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File `"%~dp0vres-mcp-launch.ps1`"`r`n", [Text.Encoding]::ASCII)
    # SAME original bin and active release; Desktop remains source-HELD.
    [IO.File]::WriteAllText((Join-Path $Bin 'vres-day.cmd'), "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File `"%~dp0vres-day-launch.ps1`" %*`r`n", [Text.Encoding]::ASCII)
    $InstalledAt = Get-Date -Format o
    Write-JsonAtomic $ActivePath @{
        product='Vres-OS'
        release=$ReleaseId
        previous=$oldPointer
        plugin_path=$PluginTarget
        installed_at=$InstalledAt
        autocompact_owned=$AutoCompactOwnedBefore
    }
    $published=$true
    $ClaudeContractAttempted = $true
    Run $NewPython @(
        '-B','-m','vres_os.claude_contract','install-global',
        '--claude-home',$ClaudeHome,
        '--rules-source',(Join-Path $StagedSource 'rules\vres-rules.md')
    )
    $ClaudeSettingsAttempted = $true
    Run $NewPython @(
        '-B','-m','vres_os.statusline','install',
        '--claude-home',$ClaudeHome,
        '--runtime-python',$NewPython
    )
    $OwnedBeforeArg = if ($AutoCompactOwnedBefore) { 'true' } else { 'false' }
    $AutoCompactOutput = & $NewPython -I -B -X utf8 -m vres_os.autocompact install --claude-home $ClaudeHome --owned-before $OwnedBeforeArg
    if ($LASTEXITCODE -ne 0) { throw 'Could not configure Vres-managed native auto-compaction.' }
    $AutoCompactResult = "$($AutoCompactOutput | Select-Object -Last 1)" | ConvertFrom-Json
    Write-JsonAtomic $ActivePath @{
        product='Vres-OS'
        release=$ReleaseId
        previous=$oldPointer
        plugin_path=$PluginTarget
        installed_at=$InstalledAt
        autocompact_owned=[bool]$AutoCompactResult.owned
    }
    if ($AutoCompactResult.configured) {
        Write-Host 'Claude native auto-compaction: 15% of the native auto-compact window used, Vres-managed (~85% of that window remains free at the trigger when no higher-scope/launch override applies).'
        if ($AutoCompactResult.PSObject.Properties['warning']) {
            Write-Host ("Current installer process also has an external compaction modifier ({0}); user setting ownership was preserved." -f $AutoCompactResult.warning) -ForegroundColor Yellow
        }
    } else {
        Write-Host ("Claude native auto-compaction: existing user/host setting preserved ({0})." -f $AutoCompactResult.reason) -ForegroundColor Yellow
    }
    # Final package gate: Vres import/doctor/configuration steps must not leave any
    # bytecode or unexpected files in the installed package before success.
    Run $Python @('-I','-B','-X','utf8',$ArtifactTool,'verify-installed','--manifest',$ReleaseManifest,'--package-dir',$PackageDir)
    $userPath=[Environment]::GetEnvironmentVariable('Path','User')
    $parts=@($userPath -split ';' | Where-Object { $_ })
    if ($Update) {
        # Original P2 user PATH is an independent protected surface, absent from the
        # existing recovery snapshot. A maintenance update must not change its value.
        if ($parts -notcontains $Bin) {
            Write-Warning 'Vres bin is absent from your user PATH. This update will not modify PATH; request a separately approved fix if launcher discovery fails.'
        }
    } elseif ($parts -notcontains $Bin) {
        [Environment]::SetEnvironmentVariable('Path', (($parts+$Bin)-join ';'), 'User')
    }
    Remove-Item -LiteralPath (Join-Path $InstallRoot 'pending-install.json') -ErrorAction SilentlyContinue
    Write-Host 'Vres preview installed. This does not certify Windows live behavior.' -ForegroundColor Green
    Write-Host 'Database health was not checked: the doctor preflight skipped database contact. No PostgreSQL access is authorized; check database health separately with vres doctor only after approving a non-incident database target.' -ForegroundColor Yellow
    Write-Host "Release: $ReleaseId"
    Write-Host 'Open a fresh terminal, enter a disposable project, launch claude, then say: start vres'
    Write-Host 'Credentials belong in the separate setup console, never in Claude chat.'
} catch {
    if ($published) {
        if ($oldPointer) { Write-JsonAtomic $ActivePath $oldPointer }
        elseif (Test-Path $ActivePath) { Remove-Item -LiteralPath $ActivePath }
    }
    if (Test-Path (Join-Path $NewRelease 'previous-bin')) {
        if (Test-Path $Bin) { Remove-Item -LiteralPath $Bin -Recurse -Force }
        # A brand-new install had no bin directory before this transaction.
        # Never replace that absence with a newly copied empty directory.
        if ($BinExistedBefore) {
            Copy-Item -Recurse -LiteralPath (Join-Path $NewRelease 'previous-bin') -Destination $Bin
        }
    }
    if (Test-Path (Join-Path $InstallRoot 'pending-install.json')) {
        # If the journal was written but the old plugin was NOT yet moved,
        # it is still the user's original plugin. Do not delete it.
        # For a fresh install without an old plugin, remove only our copy.
        if ($pluginMoved -or -not $HadPluginBefore) {
            if (Test-Path $PluginTarget) { Assert-Managed $PluginTarget; Remove-Item -LiteralPath $PluginTarget -Recurse -Force }
        }
        if ($pluginMoved -and (Test-Path $PluginBackup)) { Move-Item -LiteralPath $PluginBackup -Destination $PluginTarget }
    }
    # Only restore profile surfaces the transaction actually attempted to
    # change. Refuse auto-deletion of new files and retain recovery journal
    # on uncertain state; source only, no real Windows recovery testing.
    if ($ClaudeContractAttempted) {
        Restore-OriginalBytesAtomic $GlobalClaudePath $GlobalClaudeBefore
        Restore-OriginalBytesAtomic $GlobalRulesPath $GlobalRulesBefore
    }
    if ($ClaudeSettingsAttempted) {
        Restore-OriginalBytesAtomic $ClaudeSettingsPath $ClaudeSettingsBefore
    }
    if (Test-Path (Join-Path $InstallRoot 'pending-install.json')) {
        # A successful *attempt* at restoration is insufficient: verify the exact
        # preinstall v2 plugin, active pointer, launcher and Claude file bytes.
        # On failure, retain the journal for explicit reviewed recovery.
        Run $Python @('-I','-X','utf8',(Join-Path $StagedSource 'src\vres_os\install_recovery.py'),'verify-restored','--install-root',$InstallRoot,'--claude-home',$ClaudeHome,'--release',$ReleaseId)
        Remove-Item -LiteralPath (Join-Path $InstallRoot 'pending-install.json') -ErrorAction Stop
    }
    Write-Warning 'Installation failed. Previous runtime/plugin/global Claude contract/status-line/auto-compaction settings restored and byte-verified when a recovery journal existed. A failed staged release is retained for diagnosis. No database migration was performed by this installer.'
    throw
} finally {
    $installLock.Dispose()
}
