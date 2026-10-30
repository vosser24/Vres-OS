& {
    $ErrorActionPreference = 'Stop'
    Write-Host '=== VRES HOST HOOK STAGE4 PINNED NON-MATCHER PAYLOAD COMPARISON ==='
    Write-Host 'READ_ONLY_NO_CLAUDE_NO_HOOK_NO_POSTGRESQL'

    $source = 'C:\Projects\Vres-ChatGPT-Review-168-Record-Leaf-Rebind-A18-20261030\plugins\vres-os\hooks\hooks.json'
    $installed = Join-Path $env:USERPROFILE '.claude\skills\vres-os\hooks\hooks.json'
    $sourceSha = '88EA7AE078821A2DE85693DF0EE785EEEA847EA100469818DD0FBE0E4F1142B2'
    $installedSha = '700BF6AD711212C3A3A22419E42E0E5D62A491A7454C55C07AFED8409F0C34F7'

    function Read-Pinned([string]$label, [string]$path, [string]$sha) {
        $full = [IO.Path]::GetFullPath($path)
        if ($full.StartsWith('\\') -or $full.StartsWith('//')) {
            throw "STOP: $label UNC path refused"
        }
        $cursor = $full
        while (-not [string]::IsNullOrEmpty($cursor)) {
            if (Test-Path -LiteralPath $cursor) {
                $item = Get-Item -LiteralPath $cursor -Force -ErrorAction Stop
                if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                    throw "STOP: $label path has reparse component"
                }
            }
            $next = [IO.Path]::GetDirectoryName($cursor)
            if ([string]::IsNullOrEmpty($next) -or $next -ceq $cursor) { break }
            $cursor = $next
        }
        $file = Get-Item -LiteralPath $full -Force -ErrorAction Stop
        if ($file.PSIsContainer -or $file.Length -gt 1048576) {
            throw "STOP: $label not bounded manifest file"
        }
        $currentHash = (Get-FileHash -LiteralPath $full -Algorithm SHA256 -ErrorAction Stop).Hash
        if ($currentHash -cne $sha) {
            throw "STOP: $label SHA256 changed from Stage3"
        }
        $json = [IO.File]::ReadAllText($full) | ConvertFrom-Json -ErrorAction Stop
        if ($null -eq $json -or $json.hooks -isnot [pscustomobject]) {
            throw "STOP: $label malformed hooks event object"
        }
        Write-Host "PASS: $($label)_SHA256_AND_STRUCTURE"
        return $json.hooks
    }

    function Without-Matcher-Json([object]$group) {
        $data = [ordered]@{}
        foreach ($field in $group.PSObject.Properties) {
            if ($field.Name -cne 'matcher') {
                $data[$field.Name] = $field.Value
            }
        }
        return (ConvertTo-Json -InputObject $data -Depth 80 -Compress)
    }

    $src = Read-Pinned 'ACCEPTED_SOURCE_A18' $source $sourceSha
    $ins = Read-Pinned 'INSTALLED_VRES' $installed $installedSha
    $srcNames = @($src.PSObject.Properties.Name | Sort-Object)
    $insNames = @($ins.PSObject.Properties.Name | Sort-Object)
    $allEvents = @(@($srcNames) + @($insNames) | Sort-Object -Unique)

    $matcherChanged = 0
    $otherChanged = 0
    $groupCountChanged = 0
    $matcherOnlyInPostEvents = $true
    $evaluatedGroups = 0

    if (($srcNames -join '|') -cne ($insNames -join '|')) {
        $matcherOnlyInPostEvents = $false
        Write-Host 'EVENT_SET_IDENTICAL=False'
    } else {
        Write-Host 'EVENT_SET_IDENTICAL=True'
    }

    foreach ($event in $allEvents) {
        $srcProp = $src.PSObject.Properties[$event]
        $insProp = $ins.PSObject.Properties[$event]
        $left = @()
        if ($null -ne $srcProp) { $left = @($srcProp.Value) }
        $right = @()
        if ($null -ne $insProp) { $right = @($insProp.Value) }
        Write-Host "EVENT=$event SOURCE_GROUPS=$($left.Count) INSTALLED_GROUPS=$($right.Count)"
        if ($left.Count -gt 50 -or $right.Count -gt 50) {
            throw "STOP: oversized $event group set"
        }
        if ($left.Count -ne $right.Count) {
            $groupCountChanged++
            $matcherOnlyInPostEvents = $false
        }
        $common = [Math]::Min($left.Count, $right.Count)
        for ($k = 0; $k -lt $common; $k++) {
            $sourceGroup = $left[$k]
            $installedGroup = $right[$k]
            if ($null -eq $sourceGroup -or $null -eq $installedGroup -or
                $null -eq $sourceGroup.hooks -or $null -eq $installedGroup.hooks) {
                throw "STOP: invalid group at $event index $k"
            }
            $sourceMatcher = $sourceGroup.PSObject.Properties['matcher']
            $installedMatcher = $installedGroup.PSObject.Properties['matcher']
            $matchersEqual = $false
            if ($null -eq $sourceMatcher -and $null -eq $installedMatcher) {
                $matchersEqual = $true
            } elseif ($null -ne $sourceMatcher -and $null -ne $installedMatcher) {
                if ($sourceMatcher.Value -isnot [string] -or
                    $installedMatcher.Value -isnot [string]) {
                    throw "STOP: invalid matcher type at $event index $k"
                }
                $matchersEqual = [string]::Equals(
                    $sourceMatcher.Value, $installedMatcher.Value,
                    [StringComparison]::Ordinal
                )
            }
            $sourceBody = Without-Matcher-Json $sourceGroup
            $installedBody = Without-Matcher-Json $installedGroup
            $nonmatcherEqual = $sourceBody -ceq $installedBody
            $evaluatedGroups++

            if (-not $matchersEqual) {
                $matcherChanged++
                if ($event -cnotin @('PostToolUse','PostToolUseFailure')) {
                    $matcherOnlyInPostEvents = $false
                }
            }
            if (-not $nonmatcherEqual) {
                $otherChanged++
                $matcherOnlyInPostEvents = $false
            }
            $index = $k + 1
            Write-Host "GROUP EVENT=$event INDEX=$index MATCHER_EQUAL=$matchersEqual NONMATCHER_PAYLOAD_EQUAL=$nonmatcherEqual SOURCE_HOOK_ENTRIES=$(@($sourceGroup.hooks).Count) INSTALLED_HOOK_ENTRIES=$(@($installedGroup.hooks).Count)"
        }
    }

    Write-Host "COMPARED_HOOK_GROUPS=$evaluatedGroups"
    Write-Host "GROUP_COUNT_DIFFERENCES=$groupCountChanged"
    Write-Host "MATCHER_DIFFERENT_GROUPS=$matcherChanged"
    Write-Host "NONMATCHER_PAYLOAD_DIFFERENT_GROUPS=$otherChanged"
    Write-Host "ONLY_POSTTOOL_MATCHER_DIFFERENCES=$matcherOnlyInPostEvents"
    if ($matcherOnlyInPostEvents -and $matcherChanged -gt 0 -and
        $otherChanged -eq 0 -and $groupCountChanged -eq 0) {
        Write-Host 'STATIC_NARROW_MATCHER_CORRECTION_CANDIDATE=YES_REVIEW_REQUIRED'
    } else {
        Write-Host 'STATIC_NARROW_MATCHER_CORRECTION_CANDIDATE=NOT_ESTABLISHED'
    }
    Write-Host 'NO_INSTALLED_CONFIG_CHANGE_NO_HOOK_OR_CLAUDE_EXECUTION'
    Write-Host 'NO_POSTGRESQL_CONTACT'
    Write-Host 'STATIC_MANIFEST_COMPARISON_DOES_NOT_CLEAR_EFFECTIVE_HOST_HOOKS'
    Write-Host 'HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN'
    Write-Host 'LIVE_SCHEMA_048_INCIDENT=OPEN'
    Write-Host 'VRES_HOST_HOOK_STAGE4_PAYLOAD_COMPARISON_COMPLETE'
}