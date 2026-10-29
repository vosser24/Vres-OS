& {
    $ErrorActionPreference = 'Stop'
    $repo = 'C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
    $prior = 'C:\Projects\Vres-ChatGPT-Review-168-Architecture-Gate-R1-20261029'
    $review = 'C:\Projects\Vres-ChatGPT-Review-168-Plan-Assessment-20261029'

    $branch = 'feature/168-personal-architecture-plan-contract-20261029'
    $head = '3ce27dd2fa46b9b2f3bb921c92e953926bcf8c8d'
    $tree = '76fa41d6561fc26454eb46149f4ddabd308d5f36'
    $parent = 'fa54b68cd8bfdf86c9de6782040858957976dd02'
    $parentTree = '5f57c7d9b06d45ba18c14369409d59461d508e10'
    $adoption = 'src/vres_os/project_adoption.py'
    $newtest = 'tests/test_project_adoption_alignment.py'
    $bootstrap = 'src/vres_os/bootstrap.py'

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
        Write-Host '=== PERSONAL 168_A2 ONE ATOMIC WINDOWS PREFLIGHT ==='
        foreach ($directory in @($repo, $prior)) {
            if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
                throw "STOP: required source checkout absent: $directory"
            }
        }
        if (Test-Path -LiteralPath $review) {
            throw 'STOP: NEW 168_A2 checkout directory already exists; do not reuse'
        }

        Equal 'Original P2 anchor HEAD' (OneGit $repo @('rev-parse','HEAD')) '82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
        Clean $repo 'Original P2 anchor checkout'
        Equal 'Prior tested #168 R1 HEAD' (OneGit $prior @('rev-parse','HEAD')) $parent
        Equal 'Prior tested #168 R1 tree' (OneGit $prior @('rev-parse','HEAD^{tree}')) $parentTree
        Clean $prior 'Prior tested #168 R1 validation checkout'

        $origin = OneGit $repo @('remote','get-url','origin')
        if ($origin -cnotin @('https://github.com/vosser24/Vres-OS','https://github.com/vosser24/Vres-OS.git')) {
            throw 'STOP: Git origin differs from the official repository'
        }
        Write-Host 'PASS: Official GitHub origin'

        $remote = @(& git -C $repo ls-remote --heads origin "refs/heads/$branch")
        if ($LASTEXITCODE -ne 0 -or $remote.Count -ne 1) {
            throw 'STOP: remote 168_A2 branch not exactly one result'
        }
        Equal 'Remote 168_A2 HEAD' (($remote[0] -split '\s+')[0]) $head

        & git -C $repo fetch --no-tags origin "refs/heads/$branch"
        if ($LASTEXITCODE -ne 0) { throw 'STOP: 168_A2 fetch failed' }
        Equal 'Fetched 168_A2 HEAD' (OneGit $repo @('rev-parse','FETCH_HEAD')) $head

        & git -C $repo worktree add --detach $review $head
        if ($LASTEXITCODE -ne 0) { throw 'STOP: detached 168_A2 worktree creation failed' }
        Equal '168_A2 detached mode' (OneGit $review @('rev-parse','--abbrev-ref','HEAD')) 'HEAD'
        Equal '168_A2 HEAD' (OneGit $review @('rev-parse','HEAD')) $head
        Equal '168_A2 tree' (OneGit $review @('rev-parse','HEAD^{tree}')) $tree
        Equal '168_A2 single parent' (OneGit $review @('rev-list','--parents','-n','1','HEAD')) "$head $parent"

        $blobs = [ordered]@{
            $adoption = '7747d2ea5891debda173fa2b5d71bc0699303304'
            $newtest = '1d1eeafb597e5e6a5e6385c3f3dc7ddd58586b0b'
            $bootstrap = '9d8e0b2229f0580e2a63ef14c5c12c09543b15ec'
            'tests/test_project_adoption_architecture_gate.py' = '7bd17ab1bccd3873343c338914be85a56a2ec760'
            'src/vres_os/architecture_governance.py' = '091d6a46523122c05eaf66a3a3dc56a4089eeda6'
            'src/vres_os/architecture_plan.py' = 'a6e45acbc48ae6ee370ad6cd5f6f9d637ef0ced3'
            'src/vres_os/architecture_policy.py' = '26bab7b8ba009a97776ed3aac517a04208ea69bc'
            'tests/test_project_adoption.py' = '135fef2426441b1137e96fd0cc5f19f726108ff3'
            'tests/test_architecture_governance.py' = '4d89e0791c622a9e1cfa9dd235c8138aa810cd9b'
            'tests/conftest.py' = '1c33bb206dbf42691a6af9a709514bf3cc9994af'
            'plugins/vres-os/hooks/hooks.json' = 'e286e4be47d058ee6ed6a3169fc45803aedc0df1'
            'tests/test_hook_readonly_posttool_fence.py' = '97c2bb75ae31ff98a5ce66c450d4f51d6e12f15a'
            'plugins/vres-os/agents/chairman.md' = 'bc160273c1a1f8cfb8a844041da206c90a00769b'
            'install.ps1' = '29a5f0da235021cc8c5607eb92218e5ea98145fa'
        }
        foreach ($path in $blobs.Keys) {
            Equal "Git blob $path" (OneGit $review @('rev-parse',"HEAD:$path")) $blobs[$path]
        }
        $changed = @(& git -C $review diff --no-ext-diff --name-status --no-renames $parent HEAD --)
        if ($LASTEXITCODE -ne 0 -or $changed.Count -ne 2 -or
            $changed[0] -cne ("M" + [char]9 + $adoption) -or
            $changed[1] -cne ("A" + [char]9 + $newtest)) {
            throw 'STOP: 168_A2 two-file allowlist mismatch'
        }
        Write-Host 'PASS: exactly one modified adoption source and one added assessment test'
        $diffCheck = @(& git -C $review diff --no-ext-diff --check $parent HEAD --)
        if ($LASTEXITCODE -ne 0 -or $diffCheck.Count -ne 0) {
            throw 'STOP: 168_A2 diff integrity check failed'
        }
        Write-Host 'PASS: 168_A2 git diff --check'
        Clean $review '168_A2 checkout before tests'
        Write-Host 'VRES_PERSONAL_168_A2_PREFLIGHT_PASS'

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
                Write-Host '=== PERSONAL 168_A2 GUARDED OFFLINE SELECTED PYTEST ==='
                Write-Host 'PYTEST_PLUGIN_AUTOLOAD=DISABLED'
                Write-Host 'PASS: process DB/PG/integration variables isolated'
                Write-Host 'TEST_COMMAND=py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_project_adoption_alignment.py tests/test_project_adoption_architecture_gate.py::test_established_source_without_claude_is_review_required_not_active tests/test_project_adoption_architecture_gate.py::test_genuinely_fresh_small_source_still_scaffolds_once tests/test_architecture_governance.py::test_complete_alignment_plan_is_ready_for_fable_but_never_activates tests/test_architecture_governance.py::test_plan_stale_audit_digest_fails_closed'
                & py -3.12 -B -m pytest -q -rA -p 'no:cacheprovider' $newtest 'tests/test_project_adoption_architecture_gate.py::test_established_source_without_claude_is_review_required_not_active' 'tests/test_project_adoption_architecture_gate.py::test_genuinely_fresh_small_source_still_scaffolds_once' 'tests/test_architecture_governance.py::test_complete_alignment_plan_is_ready_for_fable_but_never_activates' 'tests/test_architecture_governance.py::test_plan_stale_audit_digest_fails_closed'
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

        Write-Host '=== PERSONAL 168_A2 POSTTEST GIT INTEGRITY ==='
        Equal 'Posttest 168_A2 HEAD' (OneGit $review @('rev-parse','HEAD')) $head
        Equal 'Posttest 168_A2 tree' (OneGit $review @('rev-parse','HEAD^{tree}')) $tree
        foreach ($path in $blobs.Keys) {
            Equal "Posttest blob $path" (OneGit $review @('rev-parse',"HEAD:$path")) $blobs[$path]
        }
        Clean $review '168_A2 worktree after selected test'
        Clean $prior 'Prior tested #168 R1 worktree unchanged'
        Write-Host "168_A2_TEST_EXIT_CODE=$testExit"
        if ($testExit -ne 0) { throw "STOP: 168_A2 selected pytest exited with code $testExit" }
        Write-Host 'VRES_PERSONAL_168_A2_WINDOWS_SELECTED_TEST_COMPLETE'
    }
    catch {
        Write-Host "VRES_PERSONAL_168_A2_ABORTED: $($_.Exception.Message)"
        throw
    }
}
