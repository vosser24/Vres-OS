& {
    $ErrorActionPreference = 'Stop'
    $repo = 'C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
    $pt2a = 'C:\Projects\Vres-ChatGPT-Review-Personal-PT2A-20261029'
    $review = 'C:\Projects\Vres-ChatGPT-Review-Personal-PT2B-20261029'

    $branch = 'feature/personal-governed-chairman-pt2b-offline-recovery-20261029'
    $head = '361500291601e241b7c579012a25442ff4a95d7d'
    $tree = '903fa86fc9ee9548d20509a5485efa010ae4a3fe'
    $parent = '22122047cc985ffc8fb3e5d0d30e3d68d8d57df9'
    $parentTree = 'a64cdc6cd188e6f9f4186cf5d3887ce82125cf0e'
    $impl = 'src/vres_os/personal_chairman_recovery_journal.py'
    $spec = 'tests/test_personal_chairman_recovery_journal.py'

    function OneGit([string]$where, [string[]]$arguments) {
        $output = @(& git -C $where @arguments)
        if ($LASTEXITCODE -ne 0 -or $output.Count -ne 1) {
            throw "STOP: one-line Git check failed in $where"
        }
        return [string]$output[0]
    }
    function Equal([string]$name, [string]$got, [string]$expected) {
        if ($got -cne $expected) { throw "STOP: $name mismatch" }
        Write-Host "PASS: $name"
    }
    function Clean([string]$where, [string]$name) {
        $status = @(& git -C $where status --porcelain=v1 --untracked-files=all)
        if ($LASTEXITCODE -ne 0 -or $status.Count -ne 0) {
            throw "STOP: $name not clean"
        }
        Write-Host "PASS: $name"
    }

    try {
        Write-Host '=== PERSONAL PT2B ONE ATOMIC WINDOWS PREFLIGHT ==='
        foreach ($d in @($repo, $pt2a)) {
            if (-not (Test-Path -LiteralPath $d -PathType Container)) {
                throw "STOP: required checkout not present: $d"
            }
        }
        if (Test-Path -LiteralPath $review) {
            throw 'STOP: new PT2B review destination already exists'
        }

        Equal 'Original P2 anchor HEAD' (OneGit $repo @('rev-parse','HEAD')) `
            '82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
        Clean $repo 'Original P2 anchor'
        Equal 'Accepted PT2A HEAD' (OneGit $pt2a @('rev-parse','HEAD')) $parent
        Equal 'Accepted PT2A tree' (OneGit $pt2a @('rev-parse','HEAD^{tree}')) $parentTree
        Clean $pt2a 'PT2A original review checkout'

        $origin = OneGit $repo @('remote','get-url','origin')
        if ($origin -cnotin @('https://github.com/vosser24/Vres-OS.git',
                             'https://github.com/vosser24/Vres-OS')) {
            throw 'STOP: unexpected origin'
        }
        Write-Host 'PASS: Official GitHub origin'

        $remote = @(& git -C $repo ls-remote --heads origin "refs/heads/$branch")
        if ($LASTEXITCODE -ne 0 -or $remote.Count -ne 1) {
            throw 'STOP: unexpected remote PT2B branch result'
        }
        Equal 'Remote PT2B HEAD' (($remote[0] -split '\s+')[0]) $head
        & git -C $repo fetch --no-tags origin "refs/heads/$branch"
        if ($LASTEXITCODE -ne 0) { throw 'STOP: targeted PT2B fetch failed' }
        Equal 'Fetched PT2B HEAD' (OneGit $repo @('rev-parse','FETCH_HEAD')) $head

        & git -C $repo worktree add --detach $review $head
        if ($LASTEXITCODE -ne 0) { throw 'STOP: detached PT2B checkout failed' }
        Equal 'PT2B detached mode' (OneGit $review @('rev-parse','--abbrev-ref','HEAD')) 'HEAD'
        Equal 'PT2B HEAD' (OneGit $review @('rev-parse','HEAD')) $head
        Equal 'PT2B tree' (OneGit $review @('rev-parse','HEAD^{tree}')) $tree
        Equal 'PT2B sole parent' (OneGit $review @('rev-list','--parents','-n','1','HEAD')) `
            "$head $parent"

        $blobs = [ordered]@{
            $impl = '5b9a0ed4f52a4e4d95201d48a131e2186f9c06c8'
            $spec = '0d6e5a8263dcdb8463d8a2794468c20a5b4f4aa4'
            'src/vres_os/personal_chairman_transition_plan.py' = '0aa49e386432c7e080da18831a9b6c6afb200ad8'
            'tests/test_personal_chairman_transition_plan.py' = '463f6c291a4f52f4056056ab6659237c386ed498'
            'src/vres_os/personal_chairman_preview.py' = '045969e7a0b6f2b4320f9edba5e1629a4b50ec6e'
            'tests/test_personal_chairman_preview.py' = 'fcdbc695107d6cc1d9f9c66e5fa6469bc6be64a3'
            'plugins/vres-os/agents/chairman.md' = 'bc160273c1a1f8cfb8a844041da206c90a00769b'
            'tests/conftest.py' = '1c33bb206dbf42691a6af9a709514bf3cc9994af'
        }
        foreach ($path in $blobs.Keys) {
            Equal "Git blob $path" (OneGit $review @('rev-parse',"HEAD:$path")) $blobs[$path]
        }
        $changed = @(& git -C $review diff --no-ext-diff --name-status --no-renames $parent HEAD --)
        if ($LASTEXITCODE -ne 0 -or $changed.Count -ne 2 -or
            $changed[0] -cne "A`t$impl" -or $changed[1] -cne "A`t$spec") {
            throw 'STOP: PT2B changed-path allowlist mismatch'
        }
        Write-Host 'PASS: exactly two PT2B added source/test files'
        $integrity = @(& git -C $review diff --no-ext-diff --check $parent HEAD --)
        if ($LASTEXITCODE -ne 0 -or $integrity.Count -ne 0) {
            throw 'STOP: PT2B diff --check failed'
        }
        Write-Host 'PASS: PT2B diff --check'
        Clean $review 'PT2B review clean before tests'
        Write-Host 'VRES_PERSONAL_PT2B_PREFLIGHT_PASS'

        $unsafe = @(Get-ChildItem Env: | Where-Object {
            $_.Name -match '^(PG|POSTGRES|DATABASE|VRES_.*(DB|DATABASE|INTEGRATION)|VRES_DATA_DIR$)'
        } | ForEach-Object { $_.Name })
        $controlled = @('PYTHONPATH','PYTEST_DISABLE_PLUGIN_AUTOLOAD',
                        'PYTEST_ADDOPTS','PYTEST_PLUGINS','PYTHONDONTWRITEBYTECODE')
        $keys = @($unsafe) + @($controlled)
        $keys = @($keys | Sort-Object -Unique)
        $saved = @{}
        foreach ($name in $keys) {
            $saved[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
        }
        $testExit = $null
        try {
            foreach ($name in $unsafe) {
                [Environment]::SetEnvironmentVariable($name, $null, 'Process')
            }
            [Environment]::SetEnvironmentVariable('PYTHONPATH', (Join-Path $review 'src'), 'Process')
            [Environment]::SetEnvironmentVariable('PYTEST_DISABLE_PLUGIN_AUTOLOAD', '1', 'Process')
            [Environment]::SetEnvironmentVariable('PYTEST_ADDOPTS', $null, 'Process')
            [Environment]::SetEnvironmentVariable('PYTEST_PLUGINS', $null, 'Process')
            [Environment]::SetEnvironmentVariable('PYTHONDONTWRITEBYTECODE', '1', 'Process')
            Push-Location -LiteralPath $review
            try {
                Write-Host '=== PERSONAL PT2B GUARDED OFFLINE SELECTED PYTEST ==='
                Write-Host 'PYTEST_PLUGIN_AUTOLOAD=DISABLED'
                Write-Host 'PASS: process database/PG/integration environment isolated'
                Write-Host 'TEST_COMMAND=py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_personal_chairman_recovery_journal.py'
                & py -3.12 -B -m pytest -q -rA -p 'no:cacheprovider' $spec
                $testExit = $LASTEXITCODE
                Write-Host "PYTEST_EXIT_CODE=$testExit"
            }
            finally { Pop-Location }
        }
        finally {
            foreach ($name in $keys) {
                [Environment]::SetEnvironmentVariable($name, $saved[$name], 'Process')
            }
            Write-Host 'PASS: PROCESS_ENVIRONMENT_RESTORED'
        }

        Write-Host '=== PERSONAL PT2B POSTTEST GIT INTEGRITY ==='
        Equal 'Posttest PT2B HEAD' (OneGit $review @('rev-parse','HEAD')) $head
        Equal 'Posttest PT2B tree' (OneGit $review @('rev-parse','HEAD^{tree}')) $tree
        foreach ($path in $blobs.Keys) {
            Equal "Posttest blob $path" (OneGit $review @('rev-parse',"HEAD:$path")) $blobs[$path]
        }
        Clean $review 'PT2B checkout after selected test'
        Clean $pt2a 'PT2A checkout still clean'
        Write-Host "PT2B_TEST_EXIT_CODE=$testExit"
        if ($testExit -ne 0) { throw "STOP: PT2B pytest exit $testExit" }
        Write-Host 'VRES_PERSONAL_PT2B_WINDOWS_SELECTED_TEST_COMPLETE'
    }
    catch {
        Write-Host "VRES_PERSONAL_PT2B_ABORTED: $($_.Exception.Message)"
        throw
    }
}
