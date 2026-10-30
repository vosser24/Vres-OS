& {
    $ErrorActionPreference = 'Stop'
    Write-Host '=== VRES HOST-HOOK STAGE5 PINNED IN-MEMORY MATCHER REMEDIATION PREFLIGHT ==='
    Write-Host 'READ_ONLY_NO_CLAUDE_NO_HOOK_NO_POSTGRESQL'

    $source = 'C:\Projects\Vres-ChatGPT-Review-168-Record-Leaf-Rebind-A18-20261030\plugins\vres-os\hooks\hooks.json'
    $installed = Join-Path $env:USERPROFILE '.claude\skills\vres-os\hooks\hooks.json'
    $sourceSha = '88EA7AE078821A2DE85693DF0EE785EEEA847EA100469818DD0FBE0E4F1142B2'
    $installedSha = '700BF6AD711212C3A3A22419E42E0E5D62A491A7454C55C07AFED8409F0C34F7'

    function Read-Pinned([string]$label,[string]$path,[string]$expected) {
        $full = [IO.Path]::GetFullPath($path)
        if ($full.StartsWith('\\') -or $full.StartsWith('//')) {
            throw "STOP: $label network path refused"
        }
        $cursor = $full
        while (-not [string]::IsNullOrEmpty($cursor)) {
            if (Test-Path -LiteralPath $cursor) {
                $part = Get-Item -LiteralPath $cursor -Force -ErrorAction Stop
                if (($part.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                    throw "STOP: $label pathname has a reparse component"
                }
            }
            $next = [IO.Path]::GetDirectoryName($cursor)
            if ([string]::IsNullOrEmpty($next) -or $next -ceq $cursor) { break }
            $cursor = $next
        }
        $file = Get-Item -LiteralPath $full -Force -ErrorAction Stop
        if ($file.PSIsContainer -or $file.Length -gt 1048576) {
            throw "STOP: $label must be a bounded file"
        }
        $before = (Get-FileHash -LiteralPath $full -Algorithm SHA256 -ErrorAction Stop).Hash
        if ($before -cne $expected) {
            throw "STOP: $label original manifest SHA256 changed"
        }
        $value = [IO.File]::ReadAllText($full) | ConvertFrom-Json -ErrorAction Stop
        if ($null -eq $value -or $value.hooks -isnot [pscustomobject]) {
            throw "STOP: $label JSON structure invalid"
        }
        $after = (Get-FileHash -LiteralPath $full -Algorithm SHA256 -ErrorAction Stop).Hash
        if ($after -cne $expected) {
            throw "STOP: $label changed during inspection"
        }
        Write-Host "PASS: $($label)_PINNED_AND_UNCHANGED"
        return $value
    }

    function Without-Matcher([object]$group) {
        $fields = [ordered]@{}
        foreach ($p in $group.PSObject.Properties) {
            if ($p.Name -cne 'matcher') { $fields[$p.Name] = $p.Value }
        }
        return (ConvertTo-Json -InputObject $fields -Depth 80 -Compress)
    }

    function Hook-Count([object]$hooks,[string]$event,[string]$tool) {
        $count = 0
        $prop = $hooks.PSObject.Properties[$event]
        if ($null -eq $prop) { return 0 }
        foreach ($group in @($prop.Value)) {
            if ($null -eq $group -or $null -eq $group.hooks) {
                throw "STOP: invalid $event group"
            }
            $matcher = $group.PSObject.Properties['matcher']
            $hit = $true
            if ($null -ne $matcher) {
                if ($matcher.Value -isnot [string]) {
                    throw "STOP: invalid $event matcher type"
                }
                try {
                    $hit = [regex]::IsMatch(
                        $tool, $matcher.Value,
                        [Text.RegularExpressions.RegexOptions]::None,
                        [TimeSpan]::FromMilliseconds(100)
                    )
                } catch {
                    throw "STOP: invalid or timed out $event regex"
                }
            }
            if ($hit) { $count += @($group.hooks).Count }
        }
        return $count
    }

    $src = Read-Pinned 'ACCEPTED_A18_SOURCE' $source $sourceSha
    $ins = Read-Pinned 'INSTALLED_VRES' $installed $installedSha
    $srcTop = @($src.PSObject.Properties.Name | Sort-Object)
    $insTop = @($ins.PSObject.Properties.Name | Sort-Object)
    if (($srcTop -join '|') -cne ($insTop -join '|')) {
        throw 'STOP: top-level manifest field sets differ'
    }
    $srcEvents = @($src.hooks.PSObject.Properties.Name | Sort-Object)
    $insEvents = @($ins.hooks.PSObject.Properties.Name | Sort-Object)
    if (($srcEvents -join '|') -cne ($insEvents -join '|')) {
        throw 'STOP: event sets differ'
    }

    $readTools = @('Read','Glob','Grep')
    $postEvents = @('PostToolUse','PostToolUseFailure')
    $beforeTotal = 0
    foreach ($event in $postEvents) {
        foreach ($tool in $readTools) {
            $beforeTotal += Hook-Count $ins.hooks $event $tool
        }
    }
    if ($beforeTotal -ne 9) {
        throw "STOP: previously observed installed read post-hook count is now $beforeTotal, not 9"
    }
    Write-Host 'PASS: INSTALLED_READ_POSTHOOK_COUNT_BEFORE_SIMULATION=9'

    $deltaCount = 0
    $groupsCompared = 0
    $expectedDeltas = @(
        'PostToolUse:2',
        'PostToolUse:4',
        'PostToolUseFailure:1'
    )
    $actualDeltas = @()

    foreach ($event in $srcEvents) {
        $left = @($src.hooks.PSObject.Properties[$event].Value)
        $right = @($ins.hooks.PSObject.Properties[$event].Value)
        if ($left.Count -ne $right.Count -or $left.Count -gt 50) {
            throw "STOP: unexpected group count in $event"
        }
        for ($j = 0; $j -lt $left.Count; $j++) {
            $a = $left[$j]
            $b = $right[$j]
            if ($null -eq $a -or $null -eq $b -or
                $null -eq $a.hooks -or $null -eq $b.hooks) {
                throw "STOP: invalid $event group"
            }
            if ((Without-Matcher $a) -cne (Without-Matcher $b)) {
                throw "STOP: nonmatcher hook payload differs in $event"
            }
            $groupsCompared++
            $am = $a.PSObject.Properties['matcher']
            $bm = $b.PSObject.Properties['matcher']
            if (($null -eq $am) -ne ($null -eq $bm)) {
                throw "STOP: matcher field presence differs in $event"
            }
            if ($null -eq $am) { continue }
            if ($am.Value -isnot [string] -or $bm.Value -isnot [string]) {
                throw "STOP: matcher value has unexpected type"
            }
            if (-not [string]::Equals(
                $am.Value,$bm.Value,[StringComparison]::Ordinal
            )) {
                $id = $event + ':' + ($j + 1)
                if ($id -cnotin $expectedDeltas) {
                    throw "STOP: unexpected matcher delta at $id"
                }
                # This changes only the in-memory ConvertFrom-Json object.
                $bm.Value = $am.Value
                $actualDeltas += $id
                $deltaCount++
            }
        }
    }

    if ($groupsCompared -ne 17 -or $deltaCount -ne 3 -or
        (($actualDeltas | Sort-Object) -join '|') -cne
        (($expectedDeltas | Sort-Object) -join '|')) {
        throw 'STOP: exact 17-group/3-matcher delta contract not satisfied'
    }
    Write-Host 'PASS: EXACTLY_THREE_EXPECTED_MATCHERS_REPLACED_IN_MEMORY'
    Write-Host 'PASS: SEVENTEEN_GROUPS_AND_NONMATCHER_PAYLOADS_PRESERVED'

    $sourceCanonical = ConvertTo-Json -InputObject $src -Depth 80 -Compress
    $simulatedCanonical = ConvertTo-Json -InputObject $ins -Depth 80 -Compress
    if ($sourceCanonical -cne $simulatedCanonical) {
        throw 'STOP: simulated full JSON structure does not match accepted source'
    }
    Write-Host 'PASS: SIMULATED_FULL_MANIFEST_STRUCTURALLY_EQUALS_A18_SOURCE'

    $sampleTools = @('Read','Glob','Grep','ReadFile','Bash',
                     'Write','Edit','TaskOutput','ToolSearch','AskUserQuestion')
    $sampleEvents = @('PreToolUse','PostToolUse','PostToolUseFailure')
    $checks = 0
    foreach ($event in $sampleEvents) {
        foreach ($tool in $sampleTools) {
            if ((Hook-Count $src.hooks $event $tool) -ne
                (Hook-Count $ins.hooks $event $tool)) {
                throw "STOP: post-simulation mismatch for $event and $tool"
            }
            $checks++
        }
    }
    if ($checks -ne 30) { throw 'STOP: sample count incomplete' }
    $postRead = 0
    foreach ($event in $postEvents) {
        foreach ($tool in $readTools) {
            $postRead += Hook-Count $ins.hooks $event $tool
        }
    }
    if ($postRead -ne 0) {
        throw 'STOP: simulated Read/Glob/Grep post-hooks remain matched'
    }
    Write-Host 'PASS: THIRTY_SOURCE_VS_SIMULATED_TOOL_EVENT_CHECKS_EQUAL'
    Write-Host 'PASS: SIMULATED_READ_GLOB_GREP_POSTHOOK_ENTRIES=0'

    $afterSource = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    $afterInstalled = (Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash
    if ($afterSource -cne $sourceSha -or $afterInstalled -cne $installedSha) {
        throw 'STOP: on-disk source or installed hook manifest changed'
    }
    Write-Host 'PASS: BOTH_ON_DISK_MANIFEST_HASHES_UNCHANGED'
    Write-Host 'IN_MEMORY_SIMULATION_ONLY=TRUE'
    Write-Host 'BACKUP_CREATED=FALSE'
    Write-Host 'ROLLBACK_TESTED=FALSE'
    Write-Host 'INSTALLED_REMEDIATION_AUTHORIZED=FALSE'
    Write-Host 'EFFECTIVE_RUNTIME_HOOK_SAFETY=NOT_ESTABLISHED'
    Write-Host 'HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN'
    Write-Host 'LIVE_SCHEMA_048_INCIDENT=OPEN'
    Write-Host 'NO_CLAUDE_NO_HOOK_NO_POSTGRESQL_NO_INSTALLED_WRITES'
    Write-Host 'VRES_HOST_HOOK_STAGE5_IN_MEMORY_DRY_RUN_COMPLETE'
}