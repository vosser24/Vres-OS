& {
    $ErrorActionPreference = 'Stop'
    $review = 'C:\Projects\Vres-ChatGPT-Review-Personal-PT2D-20261029'
    $expectedHead = 'a5913288b7748693adafc36c9c1cb35af3ea3949'
    $expectedTree = 'd45ffc91781be6681124ff369af5df4d06300ce9'

    try {
        Write-Host '=== VRES CLAUDE CODE NO-LAUNCH REVIEW PREFLIGHT ==='
        Write-Host 'MODE=READ_ONLY_PREFLIGHT; NO_CLAUDE_EXECUTION'

        if (-not (Test-Path -LiteralPath $review -PathType Container)) {
            throw 'STOP: expected clean PT2D review checkout does not exist'
        }
        $head = @(& git -C $review rev-parse HEAD)
        if ($LASTEXITCODE -ne 0 -or $head.Count -ne 1 -or $head[0] -cne $expectedHead) {
            throw 'STOP: PT2D review HEAD does not match expected source pin'
        }
        Write-Host 'PASS: published PT2D source HEAD'

        $tree = @(& git -C $review rev-parse 'HEAD^{tree}')
        if ($LASTEXITCODE -ne 0 -or $tree.Count -ne 1 -or $tree[0] -cne $expectedTree) {
            throw 'STOP: PT2D review tree does not match expected identity'
        }
        Write-Host 'PASS: published PT2D source tree'

        $changes = @(& git -C $review status --porcelain=v1 --untracked-files=all)
        if ($LASTEXITCODE -ne 0 -or $changes.Count -ne 0) {
            throw 'STOP: PT2D review checkout is not clean'
        }
        Write-Host 'PASS: detached PT2D review checkout clean'

        $commands = @(Get-Command -Name claude -All -ErrorAction Stop)
        Write-Host "CLAUDE_COMMAND_COUNT=$($commands.Count)"
        foreach ($cmd in $commands) {
            Write-Host ("CLAUDE_COMMAND={0}/{1}" -f $cmd.CommandType, [IO.Path]::GetFileName($cmd.Source))
        }
        $direct = @($commands | Where-Object {
            $_.CommandType -eq 'Application' -and
            [IO.Path]::GetExtension($_.Source) -ieq '.exe'
        })
        $exactCommand = ($commands.Count -eq 1 -and $direct.Count -eq 1)
        Write-Host "SINGLE_DIRECT_CLAUDE_EXE=$exactCommand"

        $key = [Environment]::GetEnvironmentVariable('ANTHROPIC_API_KEY','Process')
        $apiAvailable = -not [string]::IsNullOrWhiteSpace($key)
        $key = $null
        Write-Host "BARE_MODE_API_KEY_ALREADY_AVAILABLE=$apiAvailable"

        $endpointOverride = -not [string]::IsNullOrWhiteSpace(
            [Environment]::GetEnvironmentVariable('ANTHROPIC_BASE_URL','Process')
        )
        Write-Host "ANTHROPIC_ENDPOINT_OVERRIDE_PRESENT=$endpointOverride"
        Write-Host 'CLAUDE_VERSION=NOT_CHECKED_NO_LAUNCH'
        Write-Host 'INSTALLED_HOOKS=NOT_READ'
        Write-Host 'NATIVE_CLAUDE_CODE_REVIEW=NOT_RUN'

        if (-not $exactCommand) {
            Write-Host 'DECISION=STOP_AMBIGUOUS_CLAUDE_COMMAND'
        } elseif (-not $apiAvailable) {
            Write-Host 'DECISION=STOP_BARE_MODE_AUTH_NOT_AVAILABLE'
        } elseif ($endpointOverride) {
            Write-Host 'DECISION=STOP_CUSTOM_ENDPOINT_REQUIRES_SEPARATE_REVIEW'
        } else {
            Write-Host 'DECISION=PREREQUISITES_SEEN_BUT_BARE_MODE_NOT_YET_ATTESTED'
        }
        Write-Host 'VRES_CLAUDE_CODE_NO_LAUNCH_PREFLIGHT_COMPLETE'
    }
    catch {
        Write-Host "VRES_CLAUDE_CODE_NO_LAUNCH_PREFLIGHT_ABORTED: $($_.Exception.Message)"
        throw
    }
}
