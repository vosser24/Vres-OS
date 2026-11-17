#requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$WithEmbeddings,
    [switch]$WithCodex,
    [switch]$UseRemotePostgres,
    [string]$SourceCommit,
    [switch]$PreflightOnly
)
# W4: operator fetches an independently approved Git commit OUTSIDE this script.
# This is a checkout-integrity tripwire, NOT a publisher signature, trusted
# Windows/source verifier, independent #185 approval or installation authority.
# Both modes are authored, NOT_RUN. Do not invoke under open operational holds.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($SourceCommit -notmatch '^[0-9a-fA-F]{40}$') {
    throw 'Update refused: supply the independently approved full 40-hex -SourceCommit. No installation started.'
}
$SourceCommit = $SourceCommit.ToLowerInvariant()
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Update refused: Git for Windows is required. No installation started.'
}

# No network, fetch, checkout, local Vres profile, Claude or database access here.
# Disable optional index locks and filesystem monitor integration for these reads.
$GitOptions = @('--no-optional-locks', '-C', $PSScriptRoot, '-c', 'core.fsmonitor=false')
$GitRoot = @(& git @GitOptions rev-parse --show-toplevel)
if ($LASTEXITCODE -ne 0 -or $GitRoot.Count -ne 1) {
    throw 'Update refused: script must run in a Git checkout. No installation started.'
}
$ExpectedRoot = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd([char[]]@('\', '/'))
$ActualRoot = [IO.Path]::GetFullPath([string]$GitRoot[0]).TrimEnd([char[]]@('\', '/'))
if (-not [string]::Equals($ExpectedRoot, $ActualRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Update refused: this script is not at the Git checkout root.'
}

# A remote URL comparison catches accidental use of another repository.
# It cannot authenticate GitHub, the remote commit, the fetched bytes or host Git.
$Origin = @(& git @GitOptions remote get-url origin)
if ($LASTEXITCODE -ne 0 -or $Origin.Count -ne 1 -or [string]$Origin[0] -notin @(
    'https://github.com/vosser24/Vres-OS.git',
    'https://github.com/vosser24/Vres-OS',
    'git@github.com:vosser24/Vres-OS.git',
    'git@github.com:vosser24/Vres-OS'
)) {
    throw 'Update refused: origin is not the expected Vres-OS GitHub remote.'
}
$Head = @(& git @GitOptions rev-parse --verify 'HEAD^{commit}')
if ($LASTEXITCODE -ne 0 -or $Head.Count -ne 1 -or [string]$Head[0] -cne $SourceCommit) {
    throw 'Update refused: HEAD is not the independently approved exact commit.'
}
$Dirty = @(& git @GitOptions status --porcelain=v1 --untracked-files=all)
if ($LASTEXITCODE -ne 0 -or $Dirty.Count -ne 0) {
    throw 'Update refused: checkout contains changed or untracked files.'
}
foreach ($Path in @(
    'install.ps1', 'update.ps1', 'pyproject.toml',
    'src/vres_os/release_artifact.py',
    'src/vres_os/release_inputs.py',
    'rules/vres-rules.md',
    'plugins/vres-os/.claude-plugin/plugin.json'
)) {
    if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $Path) -PathType Leaf)) {
        throw 'Update refused: the complete original Git installer inputs are missing.'
    }
}

if ($PreflightOnly) {
    Write-Host 'VRES_W4_PINNED_GIT_CHECKOUT_MATCH_ONLY'
    Write-Host "Observed HEAD: $Head"
    Write-Host 'NO installation, DB, Claude, migration, credential, profile or release action performed.'
    Write-Host 'NOT publisher/source trust; NOT Windows runtime proof; NOT operational authorization.'
    return
}

# Preserve the original update owner and staging/recovery path: never install
# fresh implicitly and never fall back to an alternate release/stage method.
if (-not (Test-Path -LiteralPath (Join-Path $env:LOCALAPPDATA 'VresOS\active-install.json') -PathType Leaf)) {
    throw 'Update requires an existing managed Vres installation; use separately approved install.ps1 for first installation.'
}
& (Join-Path $PSScriptRoot 'install.ps1') -Update -WithEmbeddings:$WithEmbeddings -WithCodex:$WithCodex -UseRemotePostgres:$UseRemotePostgres -SourceCommit $SourceCommit
