#requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$WithEmbeddings,
    [switch]$WithCodex,
    [switch]$UseRemotePostgres,
    [string]$SourceCommit,
    [string]$SourceTree,
    [switch]$PreflightOnly
)
# W4: operator fetches an independently approved Git commit OUTSIDE this script.
# This is a checkout-integrity tripwire, NOT a publisher signature, trusted
# Windows/source verifier, independent #185 approval or installation authority.
# Both modes are authored, NOT_RUN. Do not invoke under open operational holds.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# W4 source-only accident interlock: refuse before ANY Git invocation,
# including -PreflightOnly. Neither this script nor its JSON ledger can
# authenticate a release; both need a new independently reviewed commit.
$W4SourceInterlock = 'HELD_SOURCE_ONLY'
$W4HoldsPath = Join-Path $PSScriptRoot 'w4-operations-holds.json'
if (-not (Test-Path -LiteralPath $W4HoldsPath -PathType Leaf)) {
    throw 'VRES_W4_HELD: operation-hold ledger missing; no Git or installation attempted.'
}
try { $W4Holds = Get-Content -Raw -Encoding UTF8 -LiteralPath $W4HoldsPath | ConvertFrom-Json }
catch { throw 'VRES_W4_HELD: operation-hold ledger invalid; no Git or installation attempted.' }
$W4RequestedGate = if ($PreflightOnly.IsPresent) { $W4Holds.git_preflight } else { $W4Holds.windows_update }
if ($W4SourceInterlock -cne 'REVIEWED_RELEASE_CLEARED' -or
    $W4Holds.schema -cne 'vres-w4-operations-holds/1' -or
    $W4Holds.status -cne 'REVIEWED_RELEASE_CLEARED' -or
    $W4RequestedGate -cne 'REVIEWED_RELEASE_CLEARED') {
    throw 'VRES_W4_HELD: Windows Git preflight and update remain blocked at this source commit.'
}

if ($SourceCommit -notmatch '^[0-9a-fA-F]{40}\z') {
    throw 'Update refused: supply the independently approved full 40-hex -SourceCommit. No installation started.'
}
$SourceCommit = $SourceCommit.ToLowerInvariant()
if ($SourceTree -notmatch '^[0-9a-fA-F]{40}\z') {
    throw 'Update refused: supply separately reviewed exact 40-hex -SourceTree.'
}
$SourceTree = $SourceTree.ToLowerInvariant()
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
$HeadTree = @(& git @GitOptions rev-parse --verify 'HEAD^{tree}')
if ($LASTEXITCODE -ne 0 -or $HeadTree.Count -ne 1 -or [string]$HeadTree[0] -cne $SourceTree) {
    throw 'Update refused: HEAD tree differs from the separately reviewed exact tree.'
}
$Dirty = @(& git @GitOptions status --porcelain=v1 --untracked-files=all)
if ($LASTEXITCODE -ne 0 -or $Dirty.Count -ne 0) {
    throw 'Update refused: checkout contains changed or untracked files.'
}
foreach ($Path in @(
    'install.ps1', 'update.ps1', 'w4-operations-holds.json', 'pyproject.toml',
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
    Write-Host "Observed TREE: $HeadTree"
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
