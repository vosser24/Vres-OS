& {
    $ErrorActionPreference = 'Stop'
    $repo = 'C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
    $accepted = 'C:\Projects\Vres-ChatGPT-Review-168-Record-Ancestors-A13-R1-20261030'
    $prior = 'C:\Projects\Vres-ChatGPT-Review-168-Unambiguous-JSON-A16-20261030'
    $previous = 'C:\Projects\Vres-ChatGPT-Review-168-State-Schema-Types-A15-20261030'
    $a14 = 'C:\Projects\Vres-ChatGPT-Review-168-State-Root-Binding-A14-20261030'
    $failed = 'C:\Projects\Vres-ChatGPT-Review-168-Record-Read-A12-20261030'
    $priorRejected = 'C:\Projects\Vres-ChatGPT-Review-168-Record-Ancestors-A13-20261030'
    $review = 'C:\Projects\Vres-ChatGPT-Review-168-Finite-JSON-Float-A17-20261030'
    $branch = 'feature/168-personal-finite-float-a17-20261030'
    $head = 'edcc347cd51c7a14e553a034d89bb7bb45da63ae'
    $tree = '4ad82002b11198877353c85153e12398c6293094'
    $parent = 'fc2e52ab8feac3ce784bbb6a4484e4a37e3f4bf5'
    $a15Head = '9d63044012e59663fbeb9448a08e9aabae5dbe7d'
    $a14Head = '06fc9ddb488f7aa7ef1f980f0bfbe59b3a29b0fc'
    $parentTree = '95d46b0297bef84efe0850390a786356a6d741f6'
    $a15Tree = '46f6e00d6bc5e8baa9c7eae4f57b3cd76b2b85d6'
    $a14Tree = 'bd19a0237b4889553c974663e08ac0ada832eab4'
    $priorRejectedHead = 'cdaa39aaa774cef88a4831bf6b157e380fbb69d9'
    $priorRejectedTree = '59979714d813c6b72a885b33dff13da62bdeef8c'
    $failedHead = '345a568b551ac23183c54f10611335adee903b96'
    $failedTree = '0851934f4a79e297e136d512f6ae6d1e6f707e2d'
    $acceptedHead = '007a51b05d6c0e3d43086a864558fb666853d58d'
    $acceptedTree = '1bc85ebbbe2ac4e62dc96aa89c896395b239aef3'
    $a12R1Head = '80cee6fe9f0f0dbe55c70d2103e54c1d9bc5b966'
    $intermediate = '6730da195ba3d4e4bb62841e7c03ee11ec0e004a'
    $a11Head = 'd58db1b5cea0c74040f1d25a219e80e0180c8efd'

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
        Write-Host '=== PERSONAL 168_A17 ONE ATOMIC WINDOWS PREFLIGHT ==='
        foreach ($directory in @($repo, $prior, $previous, $a14, $accepted, $failed, $priorRejected)) {
            if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
                throw "STOP: required checkout absent: $directory"
            }
        }
        if (Test-Path -LiteralPath $review) {
            throw 'STOP: fresh A17 worktree destination already exists; do not reuse'
        }
        Equal 'Original P2 anchor HEAD' (OneGit $repo @('rev-parse','HEAD')) '82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
        Clean $repo 'Original P2 anchor checkout'
        Equal 'Prior accepted A13 R1 HEAD' (OneGit $accepted @('rev-parse','HEAD')) $acceptedHead
        Equal 'Prior accepted A13 R1 tree' (OneGit $accepted @('rev-parse','HEAD^{tree}')) $acceptedTree
        Clean $accepted 'Prior accepted A13 R1 checkout'
        Equal 'Prior Windows selected A16 HEAD' (OneGit $prior @('rev-parse','HEAD')) $parent
        Equal 'Prior Windows selected A16 tree' (OneGit $prior @('rev-parse','HEAD^{tree}')) $parentTree
        Clean $prior 'Prior Windows selected A16 checkout'
        Equal 'Prior accepted A15 HEAD' (OneGit $previous @('rev-parse','HEAD')) $a15Head
        Equal 'Prior accepted A15 tree' (OneGit $previous @('rev-parse','HEAD^{tree}')) $a15Tree
        Clean $previous 'Prior accepted A15 checkout'
        Equal 'Prior accepted A14 HEAD' (OneGit $a14 @('rev-parse','HEAD')) $a14Head
        Equal 'Prior accepted A14 tree' (OneGit $a14 @('rev-parse','HEAD^{tree}')) $a14Tree
        Clean $a14 'Prior accepted A14 checkout'
        Equal 'Original rejected A12 HEAD' (OneGit $failed @('rev-parse','HEAD')) $failedHead
        Equal 'Original rejected A12 tree' (OneGit $failed @('rev-parse','HEAD^{tree}')) $failedTree
        Clean $failed 'Original rejected A12 checkout'
        Equal 'Original rejected A13 HEAD' (OneGit $priorRejected @('rev-parse','HEAD')) $priorRejectedHead
        Equal 'Original rejected A13 tree' (OneGit $priorRejected @('rev-parse','HEAD^{tree}')) $priorRejectedTree
        Clean $priorRejected 'Original rejected A13 checkout'

        $origin = OneGit $repo @('remote','get-url','origin')
        if ($origin -cnotin @('https://github.com/vosser24/Vres-OS','https://github.com/vosser24/Vres-OS.git')) {
            throw 'STOP: Git origin differs from the official repository'
        }
        Write-Host 'PASS: Official GitHub origin'

        $remote = @(& git -C $repo ls-remote --heads origin "refs/heads/$branch")
        if ($LASTEXITCODE -ne 0 -or $remote.Count -ne 1) {
            throw 'STOP: A17 remote branch lookup not exactly one result'
        }
        Equal 'Remote A17 HEAD' (($remote[0] -split '\s+')[0]) $head

        & git -C $repo fetch --no-tags origin "refs/heads/$branch"
        if ($LASTEXITCODE -ne 0) { throw 'STOP: A17 fetch failed' }
        Equal 'Fetched A17 HEAD' (OneGit $repo @('rev-parse','FETCH_HEAD')) $head

        & git -C $repo worktree add --detach $review $head
        if ($LASTEXITCODE -ne 0) { throw 'STOP: A17 detached worktree creation failed' }
        Equal 'A17 detached mode' (OneGit $review @('rev-parse','--abbrev-ref','HEAD')) 'HEAD'
        Equal 'A17 HEAD' (OneGit $review @('rev-parse','HEAD')) $head
        Equal 'A17 tree' (OneGit $review @('rev-parse','HEAD^{tree}')) $tree
        Equal 'A17 single parent' (OneGit $review @('rev-list','--parents','-n','1','HEAD')) "$head $parent"
        Equal 'A16 direct A15 parent' (OneGit $review @('rev-list','--parents','-n','1',$parent)) "$parent $a15Head"
        Equal 'Accepted A15 direct accepted A14 parent' (OneGit $review @('rev-list','--parents','-n','1',$a15Head)) "$a15Head $a14Head"
        Equal 'Accepted A14 direct accepted A13 R1 parent' (OneGit $review @('rev-list','--parents','-n','1',$a14Head)) "$a14Head $acceptedHead"
        Equal 'Accepted A13 R1 original rejected A13 parent' (OneGit $review @('rev-list','--parents','-n','1',$acceptedHead)) "$acceptedHead $priorRejectedHead"
        Equal 'Original rejected A13 accepted A12 R1 parent' (OneGit $review @('rev-list','--parents','-n','1',$priorRejectedHead)) "$priorRejectedHead $a12R1Head"
        Equal 'Accepted A12 R1 intermediate parent' (OneGit $review @('rev-list','--parents','-n','1',$a12R1Head)) "$a12R1Head $intermediate"
        Equal 'R1 intermediate original rejected-A12 parent' (OneGit $review @('rev-list','--parents','-n','1',$intermediate)) "$intermediate $failedHead"
        Equal 'Rejected A12 original accepted-A11 parent' (OneGit $review @('rev-list','--parents','-n','1',$failedHead)) "$failedHead $a11Head"

        $blobs = [ordered]@{
            'src/vres_os/project_adoption.py' = '533268f834cc3079890cdaaf694ad7a249665c99'
            'tests/test_project_adoption_finite_float.py' = 'a746dbb97bd84363abf007778f86edac623e6e97'
            'tests/test_project_adoption_unambiguous_json.py' = '52282d05ec31889edba2972d05346bcd21cd1b7e'
            'tests/test_project_adoption_state_schema_types.py' = '2f7eb491d10ca6553dc0f1291738c5e053939bf9'
            'tests/test_project_adoption_state_root_binding.py' = 'c77b05b66732c9e77940c95255dd1552a645701d'
            'tests/test_project_adoption_record_ancestors.py' = 'eb8a67704d0c38030ff7d700d2b52ae8d8afb138'
            'tests/test_project_adoption_record_read_fence.py' = 'b0a2fae7875049a37a3420e5b3f63905229c9f75'
            'tests/test_project_adoption_decision_integrity.py' = '17827ec3f75ef328bf0f4b75ae561846ecb0ff04'
            'src/vres_os/project_preview.py' = '58c769d4dc46eee90201963f0ed17887b8471d73'
            'tests/test_project_preview_review_gates.py' = 'bf18a080fe836b2a9ac5074f3f9f37cc661ca42d'
            'src/vres_os/cli.py' = 'a70b843bc9b535231f1992e2f3bbefafc4ac7ac3'
            'tests/test_project_preview.py' = '697669ee7472806bc639b14d98fec78368dfa6f5'
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
        if ($LASTEXITCODE -ne 0 -or $changed.Count -ne 2 -or
            $changed[0] -cne ("M" + [char]9 + 'src/vres_os/project_adoption.py') -or
            $changed[1] -cne ("A" + [char]9 + 'tests/test_project_adoption_finite_float.py')) {
            throw 'STOP: A17 exact M/A two-file allowlist mismatch'
        }
        Write-Host 'PASS: A17 exactly one modified JSON float reader and one finite-float regression module'
        $diffCheck = @(& git -C $review diff --no-ext-diff --check $parent HEAD --)
        if ($LASTEXITCODE -ne 0 -or $diffCheck.Count -ne 0) {
            throw 'STOP: A17 git diff --check failed'
        }
        Write-Host 'PASS: A17 diff integrity'
        Clean $review 'A17 checkout before tests'
        Write-Host 'VRES_PERSONAL_168_A17_PREFLIGHT_PASS'

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
                Write-Host '=== PERSONAL 168_A17 GUARDED OFFLINE SELECTED PYTEST ==='
                Write-Host 'PYTEST_PLUGIN_AUTOLOAD=DISABLED'
                Write-Host 'PASS: process DB/PG/integration variables isolated'
                & py -3.12 -B -m pytest -q -rA -p 'no:cacheprovider' 'tests/test_project_adoption_finite_float.py' 'tests/test_project_adoption_unambiguous_json.py::test_normal_nested_json_remains_roundtrip_and_no_write' 'tests/test_project_adoption_unambiguous_json.py::test_duplicate_top_level_state_rejected' 'tests/test_project_adoption_unambiguous_json.py::test_unicode_escape_alias_is_detected_as_duplicate_key' 'tests/test_project_adoption_unambiguous_json.py::test_bare_nan_rejected' 'tests/test_project_adoption_unambiguous_json.py::test_nested_positive_infinity_rejected' 'tests/test_project_adoption_unambiguous_json.py::test_duplicate_persisted_state_blocks_activation_authority' 'tests/test_project_adoption_state_schema_types.py::test_boolean_true_version_is_rejected_even_though_true_equals_one' 'tests/test_project_adoption_record_read_fence.py::test_json_depth_exact_policy_limit_is_accepted' 'tests/test_project_adoption_decision_integrity.py::test_valid_p2d_decisions_still_activate_and_rollback_synthetic_small_legacy'
                $testExit = $LASTEXITCODE
                Write-Host "PYTEST_EXIT_CODE=$testExit"
            }
            finally { Pop-Location }
        }
        finally {
            foreach ($key in $keys) {
                [Environment]::SetEnvironmentVariable($key,$saved[$key],'Process')
            }
            $environmentDifferences = @($keys | Where-Object {
                [Environment]::GetEnvironmentVariable($_,'Process') -cne $saved[$_]
            })
            if ($environmentDifferences.Count -ne 0) {
                throw 'STOP: PROCESS_ENVIRONMENT_RESTORATION_MISMATCH'
            }
            Write-Host 'PASS: PROCESS_ENVIRONMENT_RESTORED_AND_VERIFIED'
        }

        Write-Host '=== PERSONAL 168_A17 POSTTEST GIT INTEGRITY ==='
        Equal 'Posttest A17 HEAD' (OneGit $review @('rev-parse','HEAD')) $head
        Equal 'Posttest A17 tree' (OneGit $review @('rev-parse','HEAD^{tree}')) $tree
        foreach ($path in $blobs.Keys) {
            Equal "Posttest Git blob $path" (OneGit $review @('rev-parse',"HEAD:$path")) $blobs[$path]
        }
        Clean $review 'A17 checkout after tests'
        Clean $failed 'Original rejected A12 checkout preserved'
        Clean $priorRejected 'Original rejected A13 checkout preserved'
        Clean $accepted 'Previously accepted A13 R1 checkout unchanged'
        Clean $prior 'Previously selected A16 checkout unchanged'
        Clean $previous 'Previously accepted A15 checkout unchanged'
        Clean $a14 'Previously accepted A14 checkout unchanged'
        Write-Host "168_A17_TEST_EXIT_CODE=$testExit"
        if ($testExit -ne 0) { throw "STOP: A17 selected pytest exited with code $testExit" }
        Write-Host 'VRES_PERSONAL_168_A17_WINDOWS_SELECTED_TEST_COMPLETE'
    }
    catch {
        Write-Host "VRES_PERSONAL_168_A17_ABORTED: $($_.Exception.Message)"
        throw
    }
}
