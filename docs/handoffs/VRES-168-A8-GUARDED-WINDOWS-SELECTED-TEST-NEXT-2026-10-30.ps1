& {
    $ErrorActionPreference = 'Stop'
    $repo = 'C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
    $prior = 'C:\Projects\Vres-ChatGPT-Review-168-Legacy-Plan-A7-20261030'
    $review = 'C:\Projects\Vres-ChatGPT-Review-168-Plan-Findings-A8-20261030'
    $branch = 'feature/168-personal-offline-plan-findings-a8-20261030'
    $head = 'f197ca9997b86bccb0fcb9bf6009dbc534d43391'
    $tree = 'd282d7b6ad42470857e0b4f73a6f865478e1133c'
    $parent = '65b2b41061f1c9f7815ff157570c73c9b5859668'
    $parentTree = '34d2c29543091fa1e4ef06e6a77ace876d32745e'

    function OneGit([string]$where, [string[]]$arguments) {
        $result = @(& git -C $where @arguments)
        if ($LASTEXITCODE -ne 0 -or $result.Count -ne 1) {
            throw "STOP: one-line Git verification failed in $where"
        }
        return [string]$result[0]
    }
    function Equal([string]$label, [string]$actual, [string]$expected) {
        if ($actual -cne $expected) {
            throw "STOP: $label mismatch: got $actual; expected $expected"
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
        Write-Host '=== PERSONAL 168_A8 ONE ATOMIC WINDOWS PREFLIGHT ==='
        foreach ($directory in @($repo, $prior)) {
            if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
                throw "STOP: required checkout absent: $directory"
            }
        }
        if (Test-Path -LiteralPath $review) {
            throw 'STOP: new A8 worktree destination already exists; do not reuse'
        }

        Equal 'Original P2 anchor HEAD' (OneGit $repo @('rev-parse','HEAD')) '82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
        Clean $repo 'Original P2 anchor checkout'
        Equal 'Prior tested A7 HEAD' (OneGit $prior @('rev-parse','HEAD')) $parent
        Equal 'Prior tested A7 tree' (OneGit $prior @('rev-parse','HEAD^{tree}')) $parentTree
        Clean $prior 'Prior tested A7 checkout'

        $origin = OneGit $repo @('remote','get-url','origin')
        if ($origin -cnotin @('https://github.com/vosser24/Vres-OS','https://github.com/vosser24/Vres-OS.git')) {
            throw 'STOP: origin is not the official GitHub repository'
        }
        Write-Host 'PASS: Official GitHub origin'

        $remote = @(& git -C $repo ls-remote --heads origin "refs/heads/$branch")
        if ($LASTEXITCODE -ne 0 -or $remote.Count -ne 1) {
            throw 'STOP: A8 remote branch lookup not exactly one result'
        }
        Equal 'Remote A8 HEAD' (($remote[0] -split '\s+')[0]) $head

        & git -C $repo fetch --no-tags origin "refs/heads/$branch"
        if ($LASTEXITCODE -ne 0) { throw 'STOP: A8 fetch failed' }
        Equal 'Fetched A8 HEAD' (OneGit $repo @('rev-parse','FETCH_HEAD')) $head

        & git -C $repo worktree add --detach $review $head
        if ($LASTEXITCODE -ne 0) { throw 'STOP: A8 worktree creation failed' }
        Equal 'A8 detached mode' (OneGit $review @('rev-parse','--abbrev-ref','HEAD')) 'HEAD'
        Equal 'A8 HEAD' (OneGit $review @('rev-parse','HEAD')) $head
        Equal 'A8 tree' (OneGit $review @('rev-parse','HEAD^{tree}')) $tree
        Equal 'A8 single parent' (OneGit $review @('rev-list','--parents','-n','1','HEAD')) "$head $parent"

        $blobs = [ordered]@{
            'src/vres_os/cli.py' = 'beaf4e6d12e14da706ae55dbb12348155184e68c'
            'src/vres_os/project_adoption.py' = 'b2da85d99ed196b8a31a9b03b803e6bbcef67bf4'
            'tests/test_project_adoption_plan_findings.py' = '5a984d15e125ad2820addd1aad92b848ecf4be90'
            'tests/test_project_adoption_legacy_plan_review.py' = '344ff34646255c9ebd31d03b011f43ae2e12d5d2'
            'tests/test_project_adoption_legacy_architecture_fence.py' = 'f83f9f8615609c6f93301e68dacce4a30741d33a'
            'src/vres_os/bootstrap.py' = 'd7268b4f2a4dca3b631a7ff461a03077e754a818'
            'tests/test_project_adoption_plan_template.py' = 'dfc1788dfb23dbe9b6e3e9c32a4ca0a59c9341a2'
            'tests/test_project_adoption_cli_plan.py' = '7ff102421584c86b1ffcb898e888b17294d2151b'
            'src/vres_os/paths.py' = '1456cf9c53ff18cfe950f63255956c17756a8620'
            'tests/test_project_adoption_alignment.py' = '1d1eeafb597e5e6a5e6385c3f3dc7ddd58586b0b'
            'tests/test_project_adoption_architecture_gate.py' = '7bd17ab1bccd3873343c338914be85a56a2ec760'
            'src/vres_os/architecture_governance.py' = '091d6a46523122c05eaf66a3a3dc56a4089eeda6'
            'src/vres_os/architecture_plan.py' = 'a6e45acbc48ae6ee370ad6cd5f6f9d637ef0ced3'
            'src/vres_os/architecture_policy.py' = '26bab7b8ba009a97776ed3aac517a04208ea69bc'
            'tests/test_project_adoption.py' = '135fef2426441b1137e96fd0cc5f19f726108ff3'
            'tests/test_architecture_governance.py' = '4d89e0791c622a9e1cfa9dd235c8138aa810cd9b'
            'tests/test_cli_status_json.py' = 'b9dd745e55ccdd02f4476b2df8bf770d6bf04b57'
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
        if ($LASTEXITCODE -ne 0 -or $changed.Count -ne 3 -or
            $changed[0] -cne ("M" + [char]9 + 'src/vres_os/cli.py') -or
            $changed[1] -cne ("M" + [char]9 + 'src/vres_os/project_adoption.py') -or
            $changed[2] -cne ("A" + [char]9 + 'tests/test_project_adoption_plan_findings.py')) {
            throw 'STOP: A8 exact three-path change allowlist mismatch'
        }
        Write-Host 'PASS: A8 exactly M CLI + M adoption + A new regression tests'
        $check = @(& git -C $review diff --no-ext-diff --check $parent HEAD --)
        if ($LASTEXITCODE -ne 0 -or $check.Count -ne 0) {
            throw 'STOP: A8 git diff --check failed'
        }
        Write-Host 'PASS: A8 diff integrity'
        Clean $review 'A8 checkout before tests'
        Write-Host 'VRES_PERSONAL_168_A8_PREFLIGHT_PASS'

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
                Write-Host '=== PERSONAL 168_A8 GUARDED OFFLINE SELECTED PYTEST ==='
                Write-Host 'PYTEST_PLUGIN_AUTOLOAD=DISABLED'
                Write-Host 'PASS: process DB/PG/integration variables isolated'
                & py -3.12 -B -m pytest -q -rA -p 'no:cacheprovider' 'tests/test_project_adoption_plan_findings.py' 'tests/test_project_adoption_legacy_plan_review.py::test_held_legacy_template_is_incomplete_deterministic_and_no_write' 'tests/test_project_adoption_legacy_plan_review.py::test_in_process_operator_plan_template_and_plan_check_for_legacy' 'tests/test_project_adoption_legacy_plan_review.py::test_legacy_claude_surface_change_blocks_plan_template_and_check' 'tests/test_project_adoption_legacy_architecture_fence.py::test_keep_drop_decisions_remain_usable_but_cannot_activate_established_legacy' 'tests/test_project_adoption_cli_plan.py::test_valid_plan_command_only_prints_non_authorizing_readonly_result'
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

        Write-Host '=== PERSONAL 168_A8 POSTTEST GIT INTEGRITY ==='
        Equal 'Posttest A8 HEAD' (OneGit $review @('rev-parse','HEAD')) $head
        Equal 'Posttest A8 tree' (OneGit $review @('rev-parse','HEAD^{tree}')) $tree
        foreach ($path in $blobs.Keys) {
            Equal "Posttest Git blob $path" (OneGit $review @('rev-parse',"HEAD:$path")) $blobs[$path]
        }
        Clean $review 'A8 checkout after tests'
        Clean $prior 'Prior tested A7 checkout unchanged'
        Write-Host "168_A8_TEST_EXIT_CODE=$testExit"
        if ($testExit -ne 0) { throw "STOP: A8 selected pytest exited with code $testExit" }
        Write-Host 'VRES_PERSONAL_168_A8_WINDOWS_SELECTED_TEST_COMPLETE'
    }
    catch {
        Write-Host "VRES_PERSONAL_168_A8_ABORTED: $($_.Exception.Message)"
        throw
    }
}
