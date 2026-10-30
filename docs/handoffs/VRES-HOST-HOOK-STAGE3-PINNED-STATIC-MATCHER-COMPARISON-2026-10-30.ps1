& {
    $ErrorActionPreference = 'Stop'
    Write-Host '=== VRES NATIVE CLAUDE HOOK STAGE3 STATIC MATCHER COMPARISON ==='

    $source = 'C:\Projects\Vres-ChatGPT-Review-168-Record-Leaf-Rebind-A18-20261030\plugins\vres-os\hooks\hooks.json'
    $installed = Join-Path $env:USERPROFILE '.claude\skills\vres-os\hooks\hooks.json'
    $sourceHash = '88EA7AE078821A2DE85693DF0EE785EEEA847EA100469818DD0FBE0E4F1142B2'
    $installedHash = '700BF6AD711212C3A3A22419E42E0E5D62A491A7454C55C07AFED8409F0C34F7'

    function Read-Pinned-HookManifest([string]$label,[string]$path,[string]$expectedHash) {
        $full = [IO.Path]::GetFullPath($path)
        if ($full.StartsWith('\\') -or $full.StartsWith('//')) {
            throw "STOP: $label points to a network path"
        }
        $cursor = $full
        while (-not [string]::IsNullOrEmpty($cursor)) {
            if (Test-Path -LiteralPath $cursor) {
                $entry = Get-Item -LiteralPath $cursor -Force -ErrorAction Stop
                if (($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                    throw "STOP: $label contains a junction or link"
                }
            }
            $next = [IO.Path]::GetDirectoryName($cursor)
            if ([string]::IsNullOrEmpty($next) -or $next -ceq $cursor) { break }
            $cursor = $next
        }
        $file = Get-Item -LiteralPath $full -Force -ErrorAction Stop
        if ($file.PSIsContainer -or $file.Length -gt 1048576) {
            throw "STOP: $label not a bounded regular manifest"
        }
        $hash = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash
        if ($hash -cne $expectedHash) {
            throw "STOP: $label SHA256 differs from the Stage2 evidence"
        }
        $document = [IO.File]::ReadAllText($full) | ConvertFrom-Json -ErrorAction Stop
        if ($null -eq $document -or $document.hooks -isnot [pscustomobject]) {
            throw "STOP: $label does not contain a hooks event object"
        }
        Write-Host "PASS: $($label)_PINNED_SHA256_AND_JSON"
        return $document.hooks
    }

    function Get-Matches([object]$table,[string]$event,[string]$tool) {
        $groups = 0; $commands = 0; $mcp = 0; $other = 0
        $property = $table.PSObject.Properties[$event]
        if ($null -eq $property) {
            return [pscustomobject]@{ Groups=0; Command=0; Mcp=0; Other=0 }
        }
        foreach ($group in @($property.Value)) {
            if ($null -eq $group) { throw "STOP: null group in $event" }
            $matcher = $group.PSObject.Properties['matcher']
            $hit = $true
            if ($null -ne $matcher) {
                if ($matcher.Value -isnot [string]) { throw "STOP: invalid matcher type in $event" }
                try {
                    $hit = [regex]::IsMatch(
                        $tool, $matcher.Value,
                        [Text.RegularExpressions.RegexOptions]::None,
                        [TimeSpan]::FromMilliseconds(100)
                    )
                } catch { throw "STOP: invalid or timed-out matcher in $event" }
            }
            if (-not $hit) { continue }
            $groups++
            if ($null -eq $group.hooks) { throw "STOP: missing hooks in $event" }
            foreach ($hook in @($group.hooks)) {
                if ($null -eq $hook) { throw "STOP: null hook in $event" }
                if ($hook.type -ceq 'command') { $commands++ }
                elseif ($hook.type -ceq 'mcp_tool') { $mcp++ }
                else { $other++ }
            }
        }
        return [pscustomobject]@{
            Groups=$groups; Command=$commands; Mcp=$mcp; Other=$other
        }
    }

    $src = Read-Pinned-HookManifest 'ACCEPTED_A18_SOURCE' $source $sourceHash
    $ins = Read-Pinned-HookManifest 'INSTALLED_VRES' $installed $installedHash
    $events = @('PreToolUse','PostToolUse','PostToolUseFailure')
    $tools = @('Read','Glob','Grep','ReadFile','Bash','Write','Edit',
               'TaskOutput','ToolSearch','AskUserQuestion')
    $sourceReadPosts = 0; $installedReadPosts = 0; $different = 0

    foreach ($event in $events) {
        foreach ($tool in $tools) {
            $a = Get-Matches $src $event $tool
            $b = Get-Matches $ins $event $tool
            Write-Host "MATCH EVENT=$event TOOL=$tool SOURCE_GROUPS=$($a.Groups) SOURCE_COMMANDS=$($a.Command) SOURCE_MCP=$($a.Mcp) INSTALLED_GROUPS=$($b.Groups) INSTALLED_COMMANDS=$($b.Command) INSTALLED_MCP=$($b.Mcp) SOURCE_OTHER=$($a.Other) INSTALLED_OTHER=$($b.Other)"
            if ($a.Groups -ne $b.Groups -or $a.Command -ne $b.Command -or
                $a.Mcp -ne $b.Mcp -or $a.Other -ne $b.Other) { $different++ }
            if ($tool -in @('Read','Glob','Grep') -and
                $event -in @('PostToolUse','PostToolUseFailure')) {
                $sourceReadPosts += $a.Command + $a.Mcp + $a.Other
                $installedReadPosts += $b.Command + $b.Mcp + $b.Other
            }
        }
    }

    foreach ($event in @('SessionStart','UserPromptSubmit','PreCompact',
                         'PostCompact','Stop','SessionEnd','SubagentStop')) {
        foreach ($label in @('SOURCE','INSTALLED')) {
            $table = if ($label -ceq 'SOURCE') { $src } else { $ins }
            $count = 0; $groups = 0
            $property = $table.PSObject.Properties[$event]
            if ($null -ne $property) {
                foreach ($group in @($property.Value)) {
                    if ($null -eq $group -or $null -eq $group.hooks) {
                        throw "STOP: malformed lifecycle group in $event"
                    }
                    $groups++
                    $count += @($group.hooks).Count
                }
            }
            Write-Host "LIFECYCLE MANIFEST=$label EVENT=$event GROUPS=$groups DECLARED_ENTRIES=$count"
        }
    }

    Write-Host "STATIC_TOOL_EVENT_MATCH_DIFFERENCES=$different"
    Write-Host "SOURCE_READ_GLOB_GREP_POSTHOOK_ENTRIES=$sourceReadPosts"
    Write-Host "INSTALLED_READ_GLOB_GREP_POSTHOOK_ENTRIES=$installedReadPosts"
    if ($installedReadPosts -gt 0) {
        Write-Host 'INSTALLED_READ_POSTHOOK_MATCH_RISK=DETECTED'
    } else {
        Write-Host 'INSTALLED_READ_POSTHOOK_MATCH_RISK=NOT_DETECTED_FOR_EXACT_TOOL_NAMES'
    }
    Write-Host 'STATIC_MATCH_IS_NOT_EFFECTIVE_HOOK_ENABLEMENT_OR_CAUSAL_PROOF'
    Write-Host 'OTHER_PLUGINS_AND_LIFECYCLE_HOOKS_NOT_CLEARED'
    Write-Host 'HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN'
    Write-Host 'LIVE_SCHEMA_048_INCIDENT=OPEN'
    Write-Host 'NO_CLAUDE_NO_HOOK_EXECUTION_NO_POSTGRESQL'
    Write-Host 'VRES_HOST_HOOK_STAGE3_STATIC_MATCHER_COMPARISON_COMPLETE'
}