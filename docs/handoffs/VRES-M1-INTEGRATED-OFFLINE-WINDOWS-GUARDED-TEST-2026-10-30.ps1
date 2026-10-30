# VRES M1 — ONE ATOMIC P1 WINDOWS SOURCE/INTEGRATED DISPOSABLE ROLLBACK TEST
# NO installed Vres, native Claude/hooks, credentials, PostgreSQL, pip, installer, PR or main changes.
# Do not change these SHA pins. Run in Windows PowerShell 5.1 (NOT in Claude Code).
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$anchor = 'C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
$checkout = 'C:\Projects\Vres-ChatGPT-Review-Personal-M1-Upgrade-20261030'
$branch = 'feature/personal-m1-integrated-upgrade-rollback-20261030'
$p2 = '82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
$base = '7bace7758e5c7f9a00f26179eb741ef3a319bc77'
$candidate = '28120eb49b6b950c7402455db19dcbdcf6d991a6'
$tree = '815fce697f16509bae150729891738d879d6ca9c'
$blobs = [ordered]@{
    'install.ps1' = '29a5f0da235021cc8c5607eb92218e5ea98145fa'
    'src/vres_os/release_inputs.py' = 'a0cdf3195f0cf0f2a61ce32521a74f78260832f7'
    'src/vres_os/release_artifact.py' = 'ddfc1beacad98199b489dc6f56456baf4d519c6a'
    'src/vres_os/install_recovery.py' = 'ac780fab49d8ca94d343f91e3d4b774f8be3bf46'
    'plugins/vres-os/hooks/hooks.json' = 'e286e4be47d058ee6ed6a3169fc45803aedc0df1'
    'scripts/personal_upgrade_rehearsal.py' = 'f0375e307c90c69608398a8368f1911692cb0ceb'
    'tests/test_backup_recovery.py' = '90b590aa6276049346ae3bf4b71014ac732ebaa7'
    'src/vres_os/database_targets.py' = 'cf292984331cf6e7aca07e9fc573f0ade0e9e579'
    'src/vres_os/chairman_policy.py' = '36e62d6a2712ac305fd4070bac658b94d61d155e'
}
function Run-Git([string]$directory, [string[]]$arguments) {
    $output = & git -c core.hooksPath=NUL -c core.fsmonitor=false -C $directory @arguments
    if ($LASTEXITCODE -ne 0) { throw ('Git operation refused: {0}' -f ($arguments -join ' ')) }
    return (($output | Out-String).Trim())
}
function Assert-SHA([string]$actual, [string]$expected, [string]$label) {
    if ($actual -cne $expected) { throw ('MISMATCH {0}: observed={1} expected={2}' -f $label,$actual,$expected) }
    Write-Host ('PASS: {0}' -f $label)
}
function Assert-TreeBlobs([string]$phase) {
    foreach ($entry in $blobs.GetEnumerator()) {
        $observed = Run-Git $checkout @('rev-parse',('HEAD:' + $entry.Key))
        Assert-SHA $observed $entry.Value ($phase + ' ' + $entry.Key)
    }
}
if ($env:OS -ne 'Windows_NT') { throw 'Native Windows is required; refusing.' }
if (-not (Test-Path -LiteralPath $anchor -PathType Container)) { throw 'Protected original P2 Git anchor missing.' }
if (Test-Path -LiteralPath $checkout) { throw 'Refusing to modify/reuse an existing M1 review path.' }
Assert-SHA (Run-Git $anchor @('rev-parse','HEAD')) $p2 'original P2 anchor HEAD'
$anchorStatus = Run-Git $anchor @('status','--porcelain=v1','--untracked-files=all')
if ($anchorStatus) { throw 'Original P2 anchor is not clean.' }
$origin = Run-Git $anchor @('remote','get-url','origin')
if ($origin -notin @('https://github.com/vosser24/Vres-OS.git','https://github.com/vosser24/Vres-OS')) {
    throw 'Original P2 anchor is not connected to the official origin.'
}
Run-Git $anchor @('fetch','--no-tags','origin',('refs/heads/' + $branch)) | Out-Null
Assert-SHA (Run-Git $anchor @('rev-parse','FETCH_HEAD')) $candidate 'remote M1 candidate HEAD'
Run-Git $anchor @('worktree','add','--detach',$checkout,$candidate) | Out-Null
Assert-SHA (Run-Git $checkout @('rev-parse','HEAD')) $candidate 'M1 detached checkout HEAD'
Assert-SHA (Run-Git $checkout @('rev-parse','HEAD^{tree}')) $tree 'M1 tree'
Assert-SHA (Run-Git $checkout @('rev-parse','HEAD^')) $base 'M1 direct accepted A18 parent'
Run-Git $checkout @('merge-base','--is-ancestor',$p2,$candidate) | Out-Null
Write-Host 'PASS: P2 is ancestor of candidate'
$observedChanges = @(& git -c core.hooksPath=NUL -C $checkout diff --name-status $base $candidate)
if ($LASTEXITCODE -ne 0) { throw 'Cannot compare exact M1 changed files.' }
$expectedChanges = @(
    ('A' + [char]9 + 'scripts/personal_upgrade_rehearsal.py'),
    ('M' + [char]9 + 'src/vres_os/install_recovery.py'),
    ('M' + [char]9 + 'tests/test_backup_recovery.py')
)
if (@(Compare-Object $expectedChanges $observedChanges).Count -ne 0) {
    throw ('Changed-path allowlist mismatch: ' + ($observedChanges -join '; '))
}
Write-Host 'PASS: exact three-path M1 change allowlist'
Run-Git $checkout @('diff','--check',$base,$candidate) | Out-Null
Write-Host 'PASS: diff whitespace integrity'
Assert-TreeBlobs 'PRE'
if (Run-Git $checkout @('status','--porcelain=v1','--untracked-files=all')) {
    throw 'M1 checkout has uncommitted changes before tests.'
}

# Save every process environment variable changed below, with original existence and value.
$names = @('PYTHONPATH','PYTHONDONTWRITEBYTECODE','PYTEST_DISABLE_PLUGIN_AUTOLOAD',
           'VRES_DATA_DIR','VRES_ALLOW_TEST_DB','VRES_TEST_DATABASE_URL','VRES_INTEGRATION_OPT_IN',
           'DATABASE_URL','PGHOST','PGPORT','PGDATABASE','PGUSER','PGPASSWORD','PGSERVICE',
           'PGSERVICEFILE','PGPASSFILE','PGOPTIONS','CLAUDE_CONFIG_DIR')
$originalEnv = @{}
foreach ($name in $names) {
    $value = Get-Item -Path ('Env:' + $name) -ErrorAction SilentlyContinue
    $originalEnv[$name] = @{ Exists=($null -ne $value); Value=$(if ($null -ne $value) { $value.Value } else { $null }) }
}
$originalLocation = (Get-Location).Path
$stage = 'NOT_RUN'; $rollback = 'NOT_RUN'; $tests = 'NOT_RUN'
try {
    foreach ($name in $names) { Remove-Item -Path ('Env:' + $name) -ErrorAction SilentlyContinue }
    $sandbox = Join-Path ([IO.Path]::GetTempPath()) ('Vres-M1-Offline-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $sandbox -Force | Out-Null
    $env:VRES_DATA_DIR = Join-Path $sandbox 'isolated-data'
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
    $env:VRES_INTEGRATION_OPT_IN = '0'
    Set-Location -LiteralPath $checkout

    # Pure Git-object package/plugin stage and BOTH synthetic interruption paths;
    # no installer, pip, native Claude, Vres CLI, hook or PostgreSQL invocation.
    $output = & py -3.12 -I -B -X utf8 scripts/personal_upgrade_rehearsal.py --root $checkout --source-commit $candidate
    $rehearsalExit = $LASTEXITCODE
    $output | Out-Host
    if ($rehearsalExit -ne 0) { throw ('Offline release/rollback rehearsal failed: ' + $rehearsalExit) }
    $result = ($output | Out-String) | ConvertFrom-Json
    if ($result.status -cne 'OFFLINE_REHEARSAL_PASS' -or
        $result.candidate_commit -cne $candidate -or
        $result.candidate_tree -cne $tree -or
        $result.exact_p2_rollback -cne 'PASS_DISPOSABLE_ONLY' -or
        $result.tampered_backup_refused_without_mutation -cne 'PASS_DISPOSABLE_ONLY') {
        throw 'Unexpected M1 offline rehearsal result contract.'
    }
    $stage='PASS'; $rollback='PASS'
    Write-Host 'PASS: actual pinned release stage, staged package/plugin verification, synthetic P2 restore and corrupt-backup refusal'

    & py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_release_artifact.py tests/test_install_contract.py
    $firstTests=$LASTEXITCODE
    if ($firstTests -ne 0) { throw ('Release/installer offline pytest failed: ' + $firstTests) }

    $selected = 'interrupted_install_recovers_exactly_from_the_persisted_snapshot or recovery_never_touches_native_claude_authentication_or_other_plugins or ambiguous_recovery_is_refused_without_any_change or v2_plugin_backup_must_match_snapshot_before_any_recovery or v2_backup_missing_digest_is_refused_without_recovery or missing_backup_with_an_unprovable_plugin_refuses_and_keeps_the_journal or interruption_before_the_plugin_moved_is_proven_by_the_snapshot_digest or version_1_snapshot_cannot_prove_plugin_identity'
    & py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_backup_recovery.py -k $selected
    $secondTests=$LASTEXITCODE
    if ($secondTests -ne 0) { throw ('Selected offline recovery pytest failed: ' + $secondTests) }
    $tests='PASS'
    Write-Host 'PASS: release + installer contract modules and selected recovery negatives'
} finally {
    Set-Location -LiteralPath $originalLocation
    foreach ($name in $names) {
        if ($originalEnv[$name].Exists) {
            Set-Item -Path ('Env:' + $name) -Value $originalEnv[$name].Value
        } else {
            Remove-Item -Path ('Env:' + $name) -ErrorAction SilentlyContinue
        }
    }
    $failedRestores = @()
    foreach ($name in $names) {
        $current = Get-Item -Path ('Env:' + $name) -ErrorAction SilentlyContinue
        if ($originalEnv[$name].Exists) {
            if ($null -eq $current -or $current.Value -cne $originalEnv[$name].Value) { $failedRestores += $name }
        } elseif ($null -ne $current) { $failedRestores += $name }
    }
    if ($failedRestores.Count -gt 0) { throw ('PROCESS ENV RESTORE FAILED: ' + ($failedRestores -join ',')) }
    Write-Host 'PASS: PROCESS_ENVIRONMENT_RESTORED_AND_VERIFIED'
}
Assert-SHA (Run-Git $checkout @('rev-parse','HEAD')) $candidate 'POST M1 HEAD'
Assert-SHA (Run-Git $checkout @('rev-parse','HEAD^{tree}')) $tree 'POST M1 tree'
Assert-TreeBlobs 'POST'
if (Run-Git $checkout @('status','--porcelain=v1','--untracked-files=all')) {
    throw 'M1 detached checkout changed during validation.'
}
Write-Host ('M1 OFFLINE RESULTS: stage={0}; rollback={1}; tests={2}; no actual installation or PostgreSQL contact requested' -f $stage,$rollback,$tests)
Write-Host 'VRES_PERSONAL_M1_WINDOWS_OFFLINE_EXECUTION_PASS_PENDING_EVIDENCE_EVALUATION'
