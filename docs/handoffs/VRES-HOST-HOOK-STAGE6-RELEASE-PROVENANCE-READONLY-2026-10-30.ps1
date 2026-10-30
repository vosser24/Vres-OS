& {
    $ErrorActionPreference = 'Stop'
    Write-Host '=== VRES HOST HOOK STAGE6 INSTALLED RELEASE PROVENANCE — READ ONLY ==='
    Write-Host 'NO_CLAUDE_NO_HOOK_NO_POSTGRESQL_NO_WRITES'

    $installRoot = Join-Path $env:LOCALAPPDATA 'VresOS'
    $active = Join-Path $installRoot 'active-install.json'
    $installed = Join-Path $env:USERPROFILE '.claude\skills\vres-os\hooks\hooks.json'
    $source = 'C:\Projects\Vres-ChatGPT-Review-168-Record-Leaf-Rebind-A18-20261030\plugins\vres-os\hooks\hooks.json'
    $activeSha = '33D775BBDEE13FE0B4C8552B1DA24C29DDFB20B502B298014F0501BBD9263A59'
    $installedSha = '700BF6AD711212C3A3A22419E42E0E5D62A491A7454C55C07AFED8409F0C34F7'
    $sourceSha = '88EA7AE078821A2DE85693DF0EE785EEEA847EA100469818DD0FBE0E4F1142B2'

    function Inspect-Local-File([string]$label, [string]$path, [long]$maxBytes) {
        $full = [IO.Path]::GetFullPath($path)
        if ($full.StartsWith('\\') -or $full.StartsWith('//')) {
            throw "STOP: $label network path refused"
        }
        $cursor = $full
        while (-not [string]::IsNullOrEmpty($cursor)) {
            if (Test-Path -LiteralPath $cursor) {
                $part = Get-Item -LiteralPath $cursor -Force -ErrorAction Stop
                if (($part.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                    throw "STOP: $label reparse path refused"
                }
            }
            $next = [IO.Path]::GetDirectoryName($cursor)
            if ([string]::IsNullOrEmpty($next) -or $next -ceq $cursor) { break }
            $cursor = $next
        }
        $item = Get-Item -LiteralPath $full -Force -ErrorAction Stop
        if ($item.PSIsContainer -or $item.Length -le 0 -or $item.Length -gt $maxBytes) {
            throw "STOP: $label is absent, not an ordinary file, or exceeds the size policy"
        }
        $sha = (Get-FileHash -LiteralPath $full -Algorithm SHA256 -ErrorAction Stop).Hash
        return [pscustomobject]@{ Path=$full; Bytes=$item.Length; Sha256=$sha }
    }

    $activeFile = Inspect-Local-File 'ACTIVE_INSTALL' $active 131072
    $installedFile = Inspect-Local-File 'INSTALLED_HOOKS' $installed 1048576
    $sourceFile = Inspect-Local-File 'ACCEPTED_A18_HOOKS' $source 1048576
    if ($activeFile.Sha256 -cne $activeSha -or
        $installedFile.Sha256 -cne $installedSha -or
        $sourceFile.Sha256 -cne $sourceSha) {
        throw 'STOP: Stage2/Stage5 pinned file hashes changed'
    }
    Write-Host 'PASS: PINNED_ACTIVE_POINTER_AND_BOTH_HOOK_MANIFEST_HASHES'

    try {
        $pointer = [IO.File]::ReadAllText($active) | ConvertFrom-Json -ErrorAction Stop
    } catch { throw 'STOP: installed active pointer is unreadable JSON' }
    if ($null -eq $pointer -or $pointer.product -cne 'Vres-OS' -or
        $pointer.release -isnot [string] -or
        $pointer.release -cnotmatch '^[0-9]{14}-[0-9a-fA-F]{8}$' -or
        $pointer.plugin_path -isnot [string]) {
        throw 'STOP: active installation pointer has unexpected release metadata'
    }

    $expectedPlugin = [IO.Path]::GetFullPath(
        (Join-Path $env:USERPROFILE '.claude\skills\vres-os')
    ).TrimEnd('\')
    $actualPlugin = [IO.Path]::GetFullPath($pointer.plugin_path).TrimEnd('\')
    if (-not [string]::Equals(
        $expectedPlugin, $actualPlugin, [StringComparison]::OrdinalIgnoreCase
    )) {
        throw 'STOP: active-install plugin path differs from inspected current-user plugin'
    }
    Write-Host 'PASS: ACTIVE_INSTALL_RELEASE_ID_AND_PLUGIN_LOCATION_VALID'

    $releaseRoot = Join-Path (Join-Path $installRoot 'releases') $pointer.release
    $releaseManifestPath = Join-Path $releaseRoot 'release-manifest.json'
    $stagedHookPath = Join-Path $releaseRoot 'distribution\vres-os\hooks\hooks.json'
    $manifestFile = Inspect-Local-File 'RELEASE_MANIFEST' $releaseManifestPath 4194304
    $stagedFile = Inspect-Local-File 'RELEASE_STAGED_HOOKS' $stagedHookPath 1048576
    try {
        $manifest = [IO.File]::ReadAllText($releaseManifestPath) |
            ConvertFrom-Json -ErrorAction Stop
    } catch { throw 'STOP: release manifest is invalid JSON' }
    if ($null -eq $manifest -or
        $manifest.source_commit -isnot [string] -or
        $manifest.source_commit -cnotmatch '^[0-9a-f]{40}$' -or
        $manifest.source_tree -isnot [string] -or
        $manifest.source_tree -cnotmatch '^[0-9a-f]{40}$' -or
        $null -eq $manifest.files) {
        throw 'STOP: release manifest has unexpected source identity or file structure'
    }
    $hookRecords = @($manifest.files | Where-Object {
        $_.path -ceq 'plugins/vres-os/hooks/hooks.json'
    })
    if ($hookRecords.Count -ne 1 -or
        $hookRecords[0].sha256 -isnot [string] -or
        $hookRecords[0].sha256 -cnotmatch '^[0-9a-f]{64}$' -or
        $hookRecords[0].git_blob -isnot [string] -or
        $hookRecords[0].git_blob -cnotmatch '^[0-9a-f]{40}$') {
        throw 'STOP: release manifest must identify exactly one bounded Vres hooks file'
    }
    $releasedHook = $hookRecords[0]
    $expectedSha = $releasedHook.sha256.ToUpperInvariant()
    $stagedMatch = $stagedFile.Sha256 -ceq $expectedSha
    $installedMatch = $installedFile.Sha256 -ceq $expectedSha

    Write-Host "RELEASE_SOURCE_COMMIT=$($manifest.source_commit)"
    Write-Host "RELEASE_SOURCE_TREE=$($manifest.source_tree)"
    Write-Host "RELEASE_HOOK_GIT_BLOB=$($releasedHook.git_blob)"
    Write-Host "RELEASE_MANIFEST_SHA256=$($manifestFile.Sha256)"
    Write-Host "RELEASE_HOOK_EXPECTED_SHA256=$expectedSha"
    Write-Host "STAGED_HOOK_SHA256=$($stagedFile.Sha256)"
    Write-Host "STAGED_HOOK_MATCHES_RELEASE_MANIFEST=$stagedMatch"
    Write-Host "INSTALLED_HOOK_MATCHES_RELEASE_MANIFEST=$installedMatch"
    if (-not $stagedMatch -or -not $installedMatch) {
        Write-Host 'RELEASE_INTEGRITY_STATUS=DRIFT_OR_INCOMPLETE'
        throw 'STOP: release manifest and installed/staged plugin not in the expected state'
    }
    Write-Host 'PASS: INSTALLED_AND_STAGED_HOOKS_MATCH_PINNED_RELEASE'
    Write-Host 'SINGLE_FILE_MATCHER_PATCH_WOULD_DIVERGE_RELEASE_MANIFEST=TRUE'

    $endFiles = @(
        [pscustomobject]@{ Label='ACTIVE_INSTALL'; Path=$active; Sha=$activeSha; Max=131072 }
        [pscustomobject]@{ Label='INSTALLED_HOOKS'; Path=$installed; Sha=$installedSha; Max=1048576 }
        [pscustomobject]@{ Label='ACCEPTED_A18_HOOKS'; Path=$source; Sha=$sourceSha; Max=1048576 }
        [pscustomobject]@{ Label='RELEASE_MANIFEST'; Path=$releaseManifestPath; Sha=$manifestFile.Sha256; Max=4194304 }
        [pscustomobject]@{ Label='RELEASE_STAGED_HOOKS'; Path=$stagedHookPath; Sha=$stagedFile.Sha256; Max=1048576 }
    )
    foreach ($check in $endFiles) {
        $now = Inspect-Local-File $check.Label $check.Path $check.Max
        if ($now.Sha256 -cne $check.Sha) {
            throw 'STOP: a pinned source or installed release file changed during inspection'
        }
    }
    Write-Host 'PASS: ALL_FIVE_ON_DISK_FILE_HASHES_UNCHANGED'
    Write-Host 'NO_BACKUP_CREATED_NO_REPAIR_NO_ROLLBACK_PERFORMED'
    Write-Host 'INSTALLED_CHANGE_AUTHORIZED=FALSE'
    Write-Host 'HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN'
    Write-Host 'LIVE_SCHEMA_048_INCIDENT=OPEN'
    Write-Host 'NO_CLAUDE_NO_HOOK_NO_POSTGRESQL_NO_FILES_WRITTEN'
    Write-Host 'VRES_HOST_HOOK_STAGE6_RELEASE_PROVENANCE_READONLY_COMPLETE'
}