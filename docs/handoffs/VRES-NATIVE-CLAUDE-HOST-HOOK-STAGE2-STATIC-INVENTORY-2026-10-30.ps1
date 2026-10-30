& {
    $ErrorActionPreference = 'Stop'
    Write-Host '=== VRES HOST-HOOK STAGE2 STRICT READ-ONLY ==='
    Write-Host 'NO_CLAUDE_NO_HOOK_EXECUTION_NO_DATABASE'

    $sourceManifest = 'C:\Projects\Vres-ChatGPT-Review-168-Record-Leaf-Rebind-A18-20261030\plugins\vres-os\hooks\hooks.json'
    $expectedSourceSha = '88EA7AE078821A2DE85693DF0EE785EEEA847EA100469818DD0FBE0E4F1142B2'
    $defaultHome = Join-Path $env:USERPROFILE '.claude'
    $override = [Environment]::GetEnvironmentVariable('CLAUDE_CONFIG_DIR','Process')
    $homes = @([pscustomobject]@{ Label='DEFAULT_CLAUDE_HOME'; Root=$defaultHome })
    Write-Host "SHELL_CLAUDE_CONFIG_DIR_PRESENT=$([bool](-not [string]::IsNullOrWhiteSpace($override)))"
    if (-not [string]::IsNullOrWhiteSpace($override) -and
        -not [string]::Equals($override,$defaultHome,[StringComparison]::OrdinalIgnoreCase)) {
        $homes += [pscustomobject]@{ Label='SHELL_OVERRIDE_CLAUDE_HOME'; Root=$override }
    }

    function Safe-Item([string]$path) {
        try {
            $full = [IO.Path]::GetFullPath($path)
            if ($full.StartsWith('\\') -or $full.StartsWith('//')) {
                return [pscustomobject]@{ Kind='NETWORK_PATH_REFUSED'; Item=$null }
            }
            $cursor = $full
            while ($cursor) {
                if (Test-Path -LiteralPath $cursor) {
                    $part = Get-Item -LiteralPath $cursor -Force -ErrorAction Stop
                    if (($part.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                        return [pscustomobject]@{ Kind='REPARSE_PATH_REFUSED'; Item=$null }
                    }
                }
                $parent = [IO.Path]::GetDirectoryName($cursor)
                if ([string]::IsNullOrEmpty($parent) -or $parent -ceq $cursor) { break }
                $cursor = $parent
            }
            if (-not (Test-Path -LiteralPath $full)) {
                return [pscustomobject]@{ Kind='NOT_FOUND'; Item=$null }
            }
            $item = Get-Item -LiteralPath $full -Force -ErrorAction Stop
            return [pscustomobject]@{
                Kind=$(if ($item.PSIsContainer) { 'DIRECTORY' } else { 'FILE' })
                Item=$item
            }
        } catch {
            return [pscustomobject]@{ Kind='UNREADABLE_OR_INVALID'; Item=$null }
        }
    }

    function Inspect-File([string]$label,[string]$path,[string]$mode='METADATA') {
        $safe = Safe-Item $path
        Write-Host "SURFACE=$label STATUS=$($safe.Kind)"
        if ($safe.Kind -cne 'FILE') { return }
        if ($safe.Item.Length -gt 2097152) {
            Write-Host "SURFACE=$label OVERSIZE_REFUSED=TRUE"
            return
        }
        try {
            $sha = (Get-FileHash -LiteralPath $path -Algorithm SHA256 -ErrorAction Stop).Hash
        } catch {
            Write-Host "SURFACE=$label HASH_UNREADABLE=TRUE"
            return
        }
        Write-Host "SURFACE=$label BYTES=$($safe.Item.Length) SHA256=$sha"
        if ($mode -ceq 'HOOK_MANIFEST' -or $mode -ceq 'SETTINGS') {
            try {
                $json = [IO.File]::ReadAllText($path) | ConvertFrom-Json -ErrorAction Stop
                Write-Host "SURFACE=$label JSON_VALID=TRUE"
                $events = @()
                if ($null -ne $json -and $json.PSObject.Properties.Name -contains 'hooks' -and
                    $null -ne $json.hooks) {
                    $events = @($json.hooks.PSObject.Properties.Name)
                }
                Write-Host "SURFACE=$label HOOK_EVENT_COUNT=$($events.Count)"
                Write-Host "SURFACE=$label SESSIONSTART=$($events -ccontains 'SessionStart')"
                Write-Host "SURFACE=$label POSTTOOLUSE=$($events -ccontains 'PostToolUse')"
                Write-Host "SURFACE=$label POSTTOOLFAILURE=$($events -ccontains 'PostToolUseFailure')"
                if ($mode -ceq 'SETTINGS') {
                    $entries = @()
                    if ($null -ne $json -and $json.PSObject.Properties.Name -contains 'enabledPlugins' -and
                        $null -ne $json.enabledPlugins) {
                        $entries = @($json.enabledPlugins.PSObject.Properties |
                            Where-Object { $_.Name -match '(?i)vres[-_]?os' })
                    }
                    $enabled = @($entries | Where-Object { $_.Value -eq $true }).Count
                    $disabled = @($entries | Where-Object { $_.Value -eq $false }).Count
                    Write-Host "SURFACE=$label VRES_ENABLED_ENTRIES=$enabled VRES_DISABLED_ENTRIES=$disabled"
                } else {
                    Write-Host "SURFACE=$label MATCHES_ACCEPTED_A18_SOURCE=$($sha -ceq $expectedSourceSha)"
                }
            } catch {
                Write-Host "SURFACE=$label JSON_INVALID_OR_UNREADABLE=TRUE"
            }
        }
    }

    Inspect-File 'ACCEPTED_A18_SOURCE_HOOKS' $sourceManifest 'HOOK_MANIFEST'

    foreach ($homeEntry in $homes) {
        Write-Host "=== $($homeEntry.Label) ==="
        $homeState = Safe-Item $homeEntry.Root
        Write-Host "CLAUDE_HOME_STATUS=$($homeState.Kind)"
        if ($homeState.Kind -cne 'DIRECTORY') { continue }
        Inspect-File 'USER_SETTINGS' (Join-Path $homeEntry.Root 'settings.json') 'SETTINGS'
        Inspect-File 'USER_LOCAL_SETTINGS' (Join-Path $homeEntry.Root 'settings.local.json') 'SETTINGS'
        Inspect-File 'PLUGIN_INSTALLED_REGISTRY' (Join-Path $homeEntry.Root 'plugins\installed_plugins.json')
        Inspect-File 'PLUGIN_MARKETPLACE_REGISTRY' (Join-Path $homeEntry.Root 'plugins\known_marketplaces.json')

        $vresRoot = Join-Path $homeEntry.Root 'skills\vres-os'
        $vresStatus = Safe-Item $vresRoot
        Write-Host "INSTALLED_VRES_SKILL_ROOT=$($vresStatus.Kind)"
        if ($vresStatus.Kind -ceq 'DIRECTORY') {
            Inspect-File 'INSTALLED_VRES_HOOKS' (Join-Path $vresRoot 'hooks\hooks.json') 'HOOK_MANIFEST'
            Inspect-File 'INSTALLED_VRES_PLUGIN_METADATA' (Join-Path $vresRoot '.claude-plugin\plugin.json')
            Inspect-File 'INSTALLED_VRES_MANAGED_MARKER' (Join-Path $vresRoot '.vres-managed')
            Inspect-File 'INSTALLED_VRES_SESSION_HOOK_WRAPPER' (Join-Path $vresRoot 'bin\vres-hook.ps1')
            Inspect-File 'INSTALLED_VRES_TOOL_OBSERVER' (Join-Path $vresRoot 'bin\vres-experience-observe.ps1')
            Inspect-File 'INSTALLED_VRES_CONTROL_PREFLIGHT' (Join-Path $vresRoot 'bin\vres-control-preflight.ps1')
        }

        $cache = Join-Path $homeEntry.Root 'plugins\cache'
        $cacheStatus = Safe-Item $cache
        Write-Host "PLUGIN_CACHE_STATUS=$($cacheStatus.Kind)"
        if ($cacheStatus.Kind -ceq 'DIRECTORY') {
            $markets = @(Get-ChildItem -LiteralPath $cache -Directory -Force -ErrorAction Stop)
            Write-Host "PLUGIN_CACHE_MARKETPLACE_COUNT=$($markets.Count)"
            if ($markets.Count -gt 100) {
                Write-Host 'CACHE_DISCOVERY_INCOMPLETE_MARKETPLACE_LIMIT'
            } else {
                $found = 0
                foreach ($market in $markets) {
                    if ((Safe-Item $market.FullName).Kind -cne 'DIRECTORY') { continue }
                    $plugins = @(Get-ChildItem -LiteralPath $market.FullName -Directory -Force -ErrorAction Stop)
                    if ($plugins.Count -gt 100) {
                        Write-Host 'CACHE_DISCOVERY_INCOMPLETE_PLUGIN_LIMIT'
                        continue
                    }
                    foreach ($plugin in @($plugins | Where-Object { $_.Name -match '(?i)^vres[-_]?os$' })) {
                        if ((Safe-Item $plugin.FullName).Kind -cne 'DIRECTORY') { continue }
                        $versions = @(Get-ChildItem -LiteralPath $plugin.FullName -Directory -Force -ErrorAction Stop)
                        if ($versions.Count -gt 30) {
                            Write-Host 'CACHE_DISCOVERY_INCOMPLETE_VERSION_LIMIT'
                            continue
                        }
                        foreach ($version in $versions) {
                            if ((Safe-Item $version.FullName).Kind -cne 'DIRECTORY') { continue }
                            $found++
                            Inspect-File "CACHED_VRES_HOOKS_$found" (Join-Path $version.FullName 'hooks\hooks.json') 'HOOK_MANIFEST'
                        }
                    }
                }
                Write-Host "CACHED_VRES_VERSION_DIRECTORY_COUNT=$found"
            }
        }
    }

    foreach ($project in @(
        'C:\Projects\Vres-ChatGPT-Review-Personal-PT2D-20261029',
        'C:\Projects\Vres-ChatGPT-Review-168-Record-Leaf-Rebind-A18-20261030'
    )) {
        $label = if ($project -like '*PT2D*') { 'PT2D_PROJECT' } else { 'ACCEPTED_A18_PROJECT' }
        Inspect-File ($label + '_SETTINGS') (Join-Path $project '.claude\settings.json') 'SETTINGS'
        Inspect-File ($label + '_LOCAL_SETTINGS') (Join-Path $project '.claude\settings.local.json') 'SETTINGS'
    }

    $programFiles = if ($env:ProgramFiles) { $env:ProgramFiles } else { 'C:\Program Files' }
    $managed = Join-Path $programFiles 'ClaudeCode'
    Inspect-File 'MANAGED_SETTINGS_CORRECT_WINDOWS_PATH' (Join-Path $managed 'managed-settings.json') 'SETTINGS'
    Inspect-File 'MANAGED_MCP_CONFIG' (Join-Path $managed 'managed-mcp.json')
    $drop = Join-Path $managed 'managed-settings.d'
    $dropStatus = Safe-Item $drop
    Write-Host "MANAGED_DROPINS_STATUS=$($dropStatus.Kind)"
    if ($dropStatus.Kind -ceq 'DIRECTORY') {
        $files = @(Get-ChildItem -LiteralPath $drop -File -Filter '*.json' -Force -ErrorAction Stop)
        Write-Host "MANAGED_DROPINS_JSON_COUNT=$($files.Count)"
        if ($files.Count -gt 30) {
            Write-Host 'MANAGED_DROPINS_DISCOVERY_INCOMPLETE_LIMIT'
        } else {
            $n = 0
            foreach ($file in $files) {
                $n++
                Inspect-File "MANAGED_DROPIN_$n" $file.FullName 'SETTINGS'
            }
        }
    }

    foreach ($scope in @('HKLM','HKCU')) {
        $key = "$($scope):\SOFTWARE\Policies\ClaudeCode"
        try {
            if (-not (Test-Path -LiteralPath $key)) {
                Write-Host "MANAGED_POLICY_$scope=NOT_FOUND"
                continue
            }
            $value = (Get-ItemProperty -LiteralPath $key -Name 'Settings' -ErrorAction Stop).Settings
            if (-not ($value -is [string]) -or $value.Length -gt 2097152) {
                Write-Host "MANAGED_POLICY_$scope=PRESENT_UNREADABLE_OR_OVERSIZE"
                continue
            }
            $policy = ConvertFrom-Json -InputObject $value -ErrorAction Stop
            $hasHooks = $null -ne $policy -and $policy.PSObject.Properties.Name -contains 'hooks'
            Write-Host "MANAGED_POLICY_$scope=PRESENT_JSON_VALID HAS_HOOKS=$hasHooks"
        } catch {
            Write-Host "MANAGED_POLICY_$scope=NOT_VERIFIABLE"
        }
    }

    if ($env:LOCALAPPDATA) {
        Inspect-File 'VRES_ACTIVE_INSTALL_POINTER' (Join-Path $env:LOCALAPPDATA 'VresOS\active-install.json')
    }
    Write-Host 'SERVER_MANAGED_POLICY=NOT_ASSESSED_BY_STATIC_INSPECTION'
    Write-Host 'OTHER_ENABLED_PLUGINS=NOT_EXHAUSTIVELY_AUDITED'
    Write-Host 'NO_CLAUDE_CODE_EXECUTED'
    Write-Host 'NO_HOOK_EXECUTED'
    Write-Host 'NO_POSTGRESQL_COMMAND_EXECUTED'
    Write-Host 'HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN'
    Write-Host 'VRES_HOST_HOOK_STAGE2_STATIC_INVENTORY_COMPLETE'
}