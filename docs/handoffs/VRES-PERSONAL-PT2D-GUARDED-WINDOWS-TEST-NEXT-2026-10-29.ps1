& {
    $ErrorActionPreference = 'Stop'
    $repo = 'C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
    $pt2c = 'C:\Projects\Vres-ChatGPT-Review-Personal-PT2C-20261029'
    $review = 'C:\Projects\Vres-ChatGPT-Review-Personal-PT2D-20261029'

    $branch = 'feature/personal-governed-chairman-pt2d-offline-release-candidate-20261029'
    $head = 'a5913288b7748693adafc36c9c1cb35af3ea3949'
    $tree = 'd45ffc91781be6681124ff369af5df4d06300ce9'
    $parent = '81149beab52750c93db91453e18efbd5f7a21da4'
    $parentTree = 'f7ad6c6ef07c5b60c698ac4aae0487e1a8976f35'
    $impl = 'src/vres_os/personal_chairman_release_candidate.py'
    $spec = 'tests/test_personal_chairman_release_candidate.py'

    function OneGit([string]$where, [string[]]$arguments) {
        $result = @(& git -C $where @arguments)
        if ($LASTEXITCODE -ne 0 -or $result.Count -ne 1) {
            throw "STOP: one-line Git verification failed in $where"
        }
        return [string]$result[0]
    }
    function Equal([string]$label, [string]$actual, [string]$expected) {
        if ($actual -cne $expected) {
            throw "STOP: $label mismatch. Got $actual; expected $expected"
        }
        Write-Host "PASS: $label"
    }
    function Clean([string]$where, [string]$label) {
        $lines = @(& git -C $where status --porcelain=v1 --untracked-files=all)
        if ($LASTEXITCODE -ne 0 -or $lines.Count -ne 0) {
            throw "STOP: $label not clean"
        }
        Write-Host "PASS: $label"
    }

    try {
        Write-Host '=== PERSONAL PT2D ONE ATOMIC WINDOWS PREFLIGHT ==='
        foreach ($directory in @($repo, $pt2c)) {
            if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
                throw "STOP: required source checkout absent: $directory"
            }
        }
        if (Test-Path -LiteralPath $review) {
            throw 'STOP: NEW PT2D checkout directory already exists; do not reuse'
        }

        Equal 'Original P2 anchor HEAD' (OneGit $repo @('rev-parse','HEAD')) '82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
        Clean $repo 'Original P2 anchor checkout'
        Equal 'Prior PT2C HEAD' (OneGit $pt2c @('rev-parse','HEAD')) $parent
        Equal 'Prior PT2C tree' (OneGit $pt2c @('rev-parse','HEAD^{tree}')) $parentTree
        Clean $pt2c 'Prior PT2C validation checkout'

        $origin = OneGit $repo @('remote','get-url','origin')
        if ($origin -cnotin @('https://github.com/vosser24/Vres-OS','https://github.com/vosser24/Vres-OS.git')) {
            throw 'STOP: Git origin differs from the official repository'
        }
        Write-Host 'PASS: Official GitHub origin'

        $remote = @(& git -C $repo ls-remote --heads origin "refs/heads/$branch")
        if ($LASTEXITCODE -ne 0 -or $remote.Count -ne 1) {
            throw 'STOP: remote PT2D branch not exactly one result'
        }
        Equal 'Remote PT2D HEAD' (($remote[0] -split '\s+')[0]) $head

        & git -C $repo fetch --no-tags origin "refs/heads/$branch"
        if ($LASTEXITCODE -ne 0) { throw 'STOP: PT2D fetch failed' }
        Equal 'Fetched PT2D HEAD' (OneGit $repo @('rev-parse','FETCH_HEAD')) $head

        & git -C $repo worktree add --detach $review $head
        if ($LASTEXITCODE -ne 0) { throw 'STOP: detached PT2D worktree creation failed' }
        Equal 'PT2D detached mode' (OneGit $review @('rev-parse','--abbrev-ref','HEAD')) 'HEAD'
        Equal 'PT2D HEAD' (OneGit $review @('rev-parse','HEAD')) $head
        Equal 'PT2D tree' (OneGit $review @('rev-parse','HEAD^{tree}')) $tree
        Equal 'PT2D single parent' (OneGit $review @('rev-list','--parents','-n','1','HEAD')) "$head $parent"

        $blobs = [ordered]@{
            $impl = '2f6d69508e0dceb68e45610d2c3dd59565232c1a'
            $spec = '28ab0476f1a82bc4e875d7500eff6d4d07744291'
            'src/vres_os/personal_chairman_release_reconciliation.py' = '68b0f430ebfe3dd8128a4c834f4a28966ecb51fe'
            'tests/test_personal_chairman_release_reconciliation.py' = '6459dfff36b829c4edced19c2dd24e7636f5303b'
            'src/vres_os/personal_chairman_recovery_journal.py' = '5b9a0ed4f52a4e4d95201d48a131e2186f9c06c8'
            'tests/test_personal_chairman_recovery_journal.py' = '0d6e5a8263dcdb8463d8a2794468c20a5b4f4aa4'
            'src/vres_os/personal_chairman_transition_plan.py' = '0aa49e386432c7e080da18831a9b6c6afb200ad8'
            'tests/test_personal_chairman_transition_plan.py' = '463f6c291a4f52f4056056ab6659237c386ed498'
            'src/vres_os/personal_chairman_preview.py' = '045969e7a0b6f2b4320f9edba5e1629a4b50ec6e'
            'tests/test_personal_chairman_preview.py' = 'fcdbc695107d6cc1d9f9c66e5fa6469bc6be64a3'
            'plugins/vres-os/agents/chairman.md' = 'bc160273c1a1f8cfb8a844041da206c90a00769b'
            'tests/conftest.py' = '1c33bb206dbf42691a6af9a709514bf3cc9994af'
            'src/vres_os/release_artifact.py' = 'ddfc1beacad98199b489dc6f56456baf4d519c6a'
            'src/vres_os/install_recovery.py' = '1c0d585645280678af4875f2842a3350f9805e0a'
            'install.ps1' = '29a5f0da235021cc8c5607eb92218e5ea98145fa'
        }
        foreach ($path in $blobs.Keys) {
            Equal "Git blob $path" (OneGit $review @('rev-parse',"HEAD:$path")) $blobs[$path]
        }
        $changed = @(& git -C $review diff --no-ext-diff --name-status --no-renames $parent HEAD --)
        if ($LASTEXITCODE -ne 0 -or $changed.Count -ne 2 -or
            $changed[0] -cne ("A" + [char]9 + $impl) -or
            $changed[1] -cne ("A" + [char]9 + $spec)) {
            throw 'STOP: PT2D two-file allowlist mismatch'
        }
        Write-Host 'PASS: exactly two PT2D source/test additions'
        $diffCheck = @(& git -C $review diff --no-ext-diff --check $parent HEAD --)
        if ($LASTEXITCODE -ne 0 -or $diffCheck.Count -ne 0) {
            throw 'STOP: PT2D diff integrity check failed'
        }
        Write-Host 'PASS: PT2D git diff --check'
        Clean $review 'PT2D checkout before tests'
        Write-Host 'VRES_PERSONAL_PT2D_PREFLIGHT_PASS'

        $unsafe = @(Get-ChildItem Env: | Where-Object {
            $_.Name -match '^(PG|POSTGRES|DATABASE|VRES_.*(DB|DATABASE|INTEGRATION)|VRES_DATA_DIR$)'
        } | ForEach-Object { $_.Name })
        $controlled = @('PYTHONPATH','PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_ADDOPTS',
                        'PYTEST_PLUGINS','PYTHONDONTWRITEBYTECODE')
        $keys = @(@($unsafe) + @($controlled) | Sort-Object -Unique)
        $saved = @{}
        foreach ($key in $keys) {
            $saved[$key] = [Environment]::GetEnvironmentVariable($key,'Process')
        }
        $testExit = $null
        try {
            foreach ($key in $unsafe) {
                [Environment]::SetEnvironmentVariable($key,$null,'Process')
            }
            [Environment]::SetEnvironmentVariable('PYTHONPATH',(Join-Path $review 'src'),'Process')
            [Environment]::SetEnvironmentVariable('PYTEST_DISABLE_PLUGIN_AUTOLOAD','1','Process')
            [Environment]::SetEnvironmentVariable('PYTEST_ADDOPTS',$null,'Process')
            [Environment]::SetEnvironmentVariable('PYTEST_PLUGINS',$null,'Process')
            [Environment]::SetEnvironmentVariable('PYTHONDONTWRITEBYTECODE','1','Process')
            Push-Location -LiteralPath $review
            try {
                Write-Host '=== PERSONAL PT2D GUARDED OFFLINE SELECTED PYTEST ==='
                Write-Host 'PYTEST_PLUGIN_AUTOLOAD=DISABLED'
                Write-Host 'PASS: process DB/PG/integration variables isolated'
                Write-Host 'TEST_COMMAND=py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_personal_chairman_release_candidate.py'
                & py -3.12 -B -m pytest -q -rA -p 'no:cacheprovider' $spec
                $testExit = $LASTEXITCODE
                Write-Host "PYTEST_EXIT_CODE=$testExit"
            }
            finally { Pop-Location }
        }
        finally {
            foreach ($key in $keys) {
                [Environment]::SetEnvironmentVariable($key,$saved[$key],'Process')
            }
            Write-Host 'PASS: PROCESS_ENVIRONMENT_RESTORED'
        }

        Write-Host '=== PERSONAL PT2D POSTTEST GIT INTEGRITY ==='
        Equal 'Posttest PT2D HEAD' (OneGit $review @('rev-parse','HEAD')) $head
        Equal 'Posttest PT2D tree' (OneGit $review @('rev-parse','HEAD^{tree}')) $tree
        foreach ($path in $blobs.Keys) {
            Equal "Posttest blob $path" (OneGit $review @('rev-parse',"HEAD:$path")) $blobs[$path]
        }
        Clean $review 'PT2D worktree after selected test'
        Clean $pt2c 'Prior PT2C worktree unchanged'
        Write-Host "PT2D_TEST_EXIT_CODE=$testExit"
        if ($testExit -ne 0) { throw "STOP: PT2D selected pytest exited with code $testExit" }
        Write-Host 'VRES_PERSONAL_PT2D_WINDOWS_SELECTED_TEST_COMPLETE'
    }
    catch {
        Write-Host "VRES_PERSONAL_PT2D_ABORTED: $($_.Exception.Message)"
        throw
    }
}
