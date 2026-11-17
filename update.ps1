#requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$WithEmbeddings,
    [switch]$WithCodex,
    [switch]$UseRemotePostgres,
    [string]$SourceCommit,
    [string]$SourceTree,
    [string]$GitExecutable,
    [string]$GitSha256,
    [string]$WheelhouseDir,
    [string]$WheelLockFile,
    [string]$WheelLockSha256,
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
# Future separately authorized operation requires an independently selected
# absolute Git executable and out-of-band SHA-256. This is NOT a signer verdict.
if ([string]::IsNullOrWhiteSpace($GitExecutable) -or
    -not [IO.Path]::IsPathRooted($GitExecutable) -or
    $GitSha256 -notmatch '^[0-9a-fA-F]{64}\z') {
    throw 'Update refused: approved absolute -GitExecutable and -GitSha256 are required.'
}
$GitExecutable = [IO.Path]::GetFullPath($GitExecutable)
if (-not (Test-Path -LiteralPath $GitExecutable -PathType Leaf)) {
    throw 'Update refused: pinned Git executable is missing.'
}
if ((Get-Item -LiteralPath $GitExecutable).Attributes -band [IO.FileAttributes]::ReparsePoint) {
    throw 'Update refused: Git executable is a reparse point.'
}
if ((Get-FileHash -LiteralPath $GitExecutable -Algorithm SHA256).Hash -cne $GitSha256.ToUpperInvariant()) {
    throw 'Update refused: pinned Git executable SHA-256 differs.'
}
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.git') -PathType Container)) {
    throw 'Update refused: a separate normal checkout is required, not a linked worktree.'
}
foreach ($fixed in @($PSScriptRoot, (Join-Path $PSScriptRoot '.git'))) {
    if ((Get-Item -LiteralPath $fixed).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw 'Update refused: checkout root or Git metadata is a reparse point.'
    }
}
# Scrub caller-controlled Git/GCM env for the bounded Git calls; always
# restore it in finally. This does NOT establish an OS kernel safety boundary.
$GitOriginalEnvironment = @{}
foreach ($item in @(Get-ChildItem Env:)) {
    if ($item.Name -match '^(GIT_|GCM_|SSH_ASKPASS$)') {
        $GitOriginalEnvironment[$item.Name] = $item.Value
        Remove-Item -LiteralPath ("Env:" + $item.Name) -ErrorAction Stop
    }
}
try {
    $env:GIT_CONFIG_NOSYSTEM = '1'
    $env:GIT_CONFIG_GLOBAL = 'NUL'
    $env:GIT_NO_LAZY_FETCH = '1'
    $env:GIT_NO_REPLACE_OBJECTS = '1'
    $env:GIT_ALLOW_PROTOCOL = 'file'
    $env:GIT_PROTOCOL_FROM_USER = '0'
    $env:GIT_TERMINAL_PROMPT = '0'
    $env:GIT_OPTIONAL_LOCKS = '0'
    $GitOptions = @('--no-optional-locks', '-C', $PSScriptRoot,
                    '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=NUL',
                    '-c', 'credential.helper=', '-c', 'protocol.allow=never')
    $GitRoot = @(& $GitExecutable @GitOptions rev-parse --show-toplevel)
    if ($LASTEXITCODE -ne 0 -or $GitRoot.Count -ne 1) {
        throw 'Update refused: Git could not identify the checkout root.'
    }
    $ExpectedRoot = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd([char[]]@('\', '/'))
    $ActualRoot = [IO.Path]::GetFullPath([string]$GitRoot[0]).TrimEnd([char[]]@('\', '/'))
    if (-not [string]::Equals($ExpectedRoot, $ActualRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Update refused: this script is not at the checkout root.'
    }
    # Read literal local origin; remote get-url may apply insteadOf rewrites.
    $Origin = @(& $GitExecutable @GitOptions config --local --get remote.origin.url)
    if ($LASTEXITCODE -ne 0 -or $Origin.Count -ne 1 -or [string]$Origin[0] -notin @(
        'https://github.com/vosser24/Vres-OS.git',
        'https://github.com/vosser24/Vres-OS',
        'git@github.com:vosser24/Vres-OS.git',
        'git@github.com:vosser24/Vres-OS'
    )) {
        throw 'Update refused: local origin is not the expected repository.'
    }
    $Head = @(& $GitExecutable @GitOptions rev-parse --verify 'HEAD^{commit}')
    if ($LASTEXITCODE -ne 0 -or $Head.Count -ne 1 -or [string]$Head[0] -cne $SourceCommit) {
        throw 'Update refused: HEAD differs from the independently approved commit.'
    }
    $HeadTree = @(& $GitExecutable @GitOptions rev-parse --verify 'HEAD^{tree}')
    if ($LASTEXITCODE -ne 0 -or $HeadTree.Count -ne 1 -or [string]$HeadTree[0] -cne $SourceTree) {
        throw 'Update refused: TREE differs from the separately approved tree.'
    }
    $Sparse = @(& $GitExecutable @GitOptions config --local --get core.sparseCheckout)
    $SparseExit = $LASTEXITCODE
    if ($SparseExit -eq 0 -and ($Sparse | Where-Object { $_ -match '^(true|1|yes|on)$' })) {
        throw 'Update refused: sparse checkout obscures source.'
    }
    if ($SparseExit -notin @(0,1)) {
        throw 'Update refused: sparse-checkout policy is unknown.'
    }
    $IndexFlags = @(& $GitExecutable @GitOptions ls-files -v)
    if ($LASTEXITCODE -ne 0 -or $IndexFlags.Count -eq 0) {
        throw 'Update refused: index inventory unavailable.'
    }
    foreach ($flag in $IndexFlags) {
        if ($flag -cnotmatch '^H ') {
            throw 'Update refused: assume-unchanged, skip-worktree or other flagged index entry.'
        }
    }
    $Stages = @(& $GitExecutable @GitOptions ls-files --stage)
    if ($LASTEXITCODE -ne 0 -or $Stages.Count -ne $IndexFlags.Count) {
        throw 'Update refused: inconsistent Git index stages.'
    }
    # Verify every tracked file's ordinary worktree bytes against its exact
    # index Git blob without clean/smudge filters; reject CRLF transformation.
    foreach ($line in $Stages) {
        if ($line -cnotmatch '^(100644|100755) ([0-9a-f]{40}) 0\t(.+)$') {
            throw 'Update refused: nonregular, unmerged or non-SHA1 index entry.'
        }
        $ExpectedBlob = [string]$Matches[2]
        $Relative = [string]$Matches[3]
        if ($Relative -match '(^/|\\|(^|/)\.\.?(/|$)|[\x00-\x1f])') {
            throw 'Update refused: unsafe tracked path.'
        }
        $TrackedPath = $PSScriptRoot
        foreach ($component in $Relative.Split('/')) {
            $TrackedPath = Join-Path $TrackedPath $component
            if ((Get-Item -LiteralPath $TrackedPath -ErrorAction Stop).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw 'Update refused: tracked path crosses a reparse point.'
            }
        }
        if (-not (Test-Path -LiteralPath $TrackedPath -PathType Leaf)) {
            throw 'Update refused: tracked source is not a regular file.'
        }
        $ActualBlob = @(& $GitExecutable @GitOptions hash-object --no-filters -- $TrackedPath)
        if ($LASTEXITCODE -ne 0 -or $ActualBlob.Count -ne 1 -or [string]$ActualBlob[0] -cne $ExpectedBlob) {
            throw 'Update refused: raw tracked bytes differ from indexed Git blob.'
        }
    }
    $Dirty = @(& $GitExecutable @GitOptions status --porcelain=v1 --untracked-files=all --ignored=matching)
    if ($LASTEXITCODE -ne 0 -or $Dirty.Count -ne 0) {
        throw 'Update refused: modified, ignored or untracked source.'
    }
    foreach ($path in @(
        'install.ps1', 'update.ps1', 'w4-operations-holds.json', 'pyproject.toml',
        'src/vres_os/release_artifact.py', 'src/vres_os/release_inputs.py',
        'rules/vres-rules.md', 'plugins/vres-os/.claude-plugin/plugin.json'
    )) {
        if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $path) -PathType Leaf)) {
            throw 'Update refused: original Git installer inputs are missing.'
        }
    }
} finally {
    foreach ($item in @(Get-ChildItem Env:)) {
        if ($item.Name -match '^(GIT_|GCM_|SSH_ASKPASS$)') {
            Remove-Item -LiteralPath ("Env:" + $item.Name) -ErrorAction Stop
        }
    }
    foreach ($name in $GitOriginalEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $GitOriginalEnvironment[$name], 'Process')
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
& (Join-Path $PSScriptRoot 'install.ps1') -Update -WithEmbeddings:$WithEmbeddings -WithCodex:$WithCodex -UseRemotePostgres:$UseRemotePostgres -SourceCommit $SourceCommit -SourceTree $SourceTree -GitExecutable $GitExecutable -GitSha256 $GitSha256 -WheelhouseDir $WheelhouseDir -WheelLockFile $WheelLockFile -WheelLockSha256 $WheelLockSha256
