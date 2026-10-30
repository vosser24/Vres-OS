# VRES M2 — INTEGRATED ROLLBACK-COMPLETION OFFLINE WINDOWS VALIDATION
# RUN ONLY in native Windows PowerShell 5.1 OUTSIDE native Claude Code.
# This is NOT install.ps1. NO Vres/Claude/PRISM hooks, PostgreSQL, Vres CLI,
# credential access, installed profile mutation, PR, main merge, or go-live.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$anchor='C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
$checkout='C:\Projects\Vres-ChatGPT-Review-M2-Rollback-Proof-20261030'
$branch='feature/personal-m2-integrated-rollback-verification-20261030'
$p2='82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
$parent='526fb9d61e4a61c26c19931f9adf2d68eecd1bc8'
$commit='a65215a3b8b91ad4ab374c928ae3cf667e5b0f95'
$tree='942a4a4d29bdae64314de6490e4e8f99674dbf3e'
$blobs=[ordered]@{
    'install.ps1'='8b5dd6dcc3cc8315f7a4c27d0173b4963b52d933'
    'src/vres_os/install_recovery.py'='b35d559758e3b6721f43631dc499095f7895c5f3'
    'tests/test_install_rollback_proof.py'='f6fb2ab35dc6e39302437d7e1931f9e92220a55d'
    'tests/test_install_contract.py'='62310e3ff6af2f9a8f49f310bb32ffea45e53752'
    'tests/test_install_preflight.py'='97a105499e1a64a4bf5b7352f445ca4926453df2'
    'tests/test_backup_recovery.py'='90b590aa6276049346ae3bf4b71014ac732ebaa7'
    'tests/test_release_artifact.py'='a50d8451f415de6b446f60ed2e277615301eddc1'
    'tests/conftest.py'='1c33bb206dbf42691a6af9a709514bf3cc9994af'
    'src/vres_os/release_inputs.py'='a0cdf3195f0cf0f2a61ce32521a74f78260832f7'
    'src/vres_os/release_artifact.py'='ddfc1beacad98199b489dc6f56456baf4d519c6a'
    'plugins/vres-os/hooks/hooks.json'='e286e4be47d058ee6ed6a3169fc45803aedc0df1'
    'src/vres_os/database_targets.py'='cf292984331cf6e7aca07e9fc573f0ade0e9e579'
}
function Invoke-PinnedGit([string]$cwd,[string[]]$arguments) {
    $out=& git -c core.hooksPath=NUL -c core.fsmonitor=false -C $cwd @arguments
    if ($LASTEXITCODE -ne 0) {
        throw ('Offline Git gate refused: '+($arguments -join ' '))
    }
    return (($out | Out-String).Trim())
}
function Assert-Exact([string]$actual,[string]$expected,[string]$label) {
    if ($actual -cne $expected) {
        throw ('MISMATCH '+$label+' actual='+$actual+' expected='+$expected)
    }
    Write-Host ('PASS: '+$label)
}
function Assert-ProtectedBlobs([string]$stage) {
    foreach($item in $blobs.GetEnumerator()) {
        Assert-Exact (Invoke-PinnedGit $checkout @('rev-parse',('HEAD:'+$item.Key))) $item.Value ($stage+' '+$item.Key)
    }
}

Write-Host '=== VRES M2 INTEGRATED ROLLBACK SOURCE PREFLIGHT — NO INSTALL ==='
if ($env:OS -ne 'Windows_NT') { throw 'Only native Windows offline validation is permitted.' }
if (-not (Test-Path -LiteralPath $anchor -PathType Container)) {
    throw 'Protected original P2 anchor is unavailable; refusing.'
}
if (Test-Path -LiteralPath $checkout) {
    throw 'The M2 rollback review checkout already exists; refusing to overwrite it.'
}
Assert-Exact (Invoke-PinnedGit $anchor @('rev-parse','HEAD')) $p2 'original P2 anchor HEAD'
if (Invoke-PinnedGit $anchor @('status','--porcelain=v1','--untracked-files=all')) {
    throw 'Original P2 anchor is not clean.'
}
$origin=Invoke-PinnedGit $anchor @('remote','get-url','origin')
if ($origin -notin @('https://github.com/vosser24/Vres-OS',
                      'https://github.com/vosser24/Vres-OS.git')) {
    throw 'Refusing unverified Git origin.'
}
Invoke-PinnedGit $anchor @('fetch','--no-tags','origin',('refs/heads/'+$branch)) | Out-Null
Assert-Exact (Invoke-PinnedGit $anchor @('rev-parse','FETCH_HEAD')) $commit 'remote M2 rollback source'
Invoke-PinnedGit $anchor @('worktree','add','--detach',$checkout,$commit) | Out-Null
Assert-Exact (Invoke-PinnedGit $checkout @('rev-parse','HEAD')) $commit 'detached M2 HEAD'
Assert-Exact (Invoke-PinnedGit $checkout @('rev-parse','HEAD^{tree}')) $tree 'detached M2 tree'
Assert-Exact (Invoke-PinnedGit $checkout @('rev-parse','HEAD^')) $parent 'single accepted M2 parent'
Invoke-PinnedGit $checkout @('merge-base','--is-ancestor',$p2,$commit) | Out-Null
Write-Host 'PASS: original P2 is ancestor of candidate'
$actual=@(& git -c core.hooksPath=NUL -C $checkout diff --name-status $parent $commit)
if ($LASTEXITCODE -ne 0) { throw 'Changed-path Git comparison failed.' }
$expected=@(
    ('M'+[char]9+'install.ps1'),
    ('M'+[char]9+'src/vres_os/install_recovery.py'),
    ('A'+[char]9+'tests/test_install_rollback_proof.py')
)
if (@(Compare-Object $expected $actual).Count -ne 0) {
    throw ('Exact three-file source allowlist mismatch: '+($actual -join '; '))
}
Write-Host 'PASS: M2 exact three-file change allowlist'
Invoke-PinnedGit $checkout @('diff','--check',$parent,$commit) | Out-Null
Write-Host 'PASS: diff whitespace integrity'
Assert-ProtectedBlobs 'PRE'
if (Invoke-PinnedGit $checkout @('status','--porcelain=v1','--untracked-files=all')) {
    throw 'Candidate checkout has uncommitted files before tests.'
}
Write-Host 'VRES_M2_ROLLBACK_PREFLIGHT_PASS'

$names=@('PYTHONPATH','PYTHONDONTWRITEBYTECODE','PYTEST_DISABLE_PLUGIN_AUTOLOAD',
         'VRES_DATA_DIR','VRES_ALLOW_TEST_DB','VRES_TEST_DATABASE_URL',
         'VRES_INTEGRATION_OPT_IN','DATABASE_URL','PGHOST','PGPORT',
         'PGDATABASE','PGUSER','PGPASSWORD','PGSERVICE','PGSERVICEFILE',
         'PGPASSFILE','PGOPTIONS','CLAUDE_CONFIG_DIR')
$before=@{}
foreach($name in $names) {
    $x=Get-Item -Path ('Env:'+$name) -ErrorAction SilentlyContinue
    $before[$name]=@{Exists=($null -ne $x);Value=$(if($null -ne $x){$x.Value}else{$null})}
}
$originalCwd=(Get-Location).Path
$pytestExit='NOT_RUN'
try {
    foreach($name in $names) {
        Remove-Item -Path ('Env:'+$name) -ErrorAction SilentlyContinue
    }
    $sandbox=Join-Path ([IO.Path]::GetTempPath()) ('vres-m2-proof-'+[guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $sandbox | Out-Null
    $env:VRES_DATA_DIR=Join-Path $sandbox 'appdata-fixture'
    $env:PYTHONDONTWRITEBYTECODE='1'
    $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
    $env:VRES_INTEGRATION_OPT_IN='0'
    Set-Location -LiteralPath $checkout
    $cases=@(
        'tests/test_install_rollback_proof.py',
        'tests/test_install_contract.py',
        'tests/test_install_preflight.py',
        'tests/test_release_artifact.py',
        'tests/test_backup_recovery.py::test_interrupted_install_recovers_exactly_from_the_persisted_snapshot',
        'tests/test_backup_recovery.py::test_recovery_never_touches_native_claude_authentication_or_other_plugins',
        'tests/test_backup_recovery.py::test_ambiguous_recovery_is_refused_without_any_change',
        'tests/test_backup_recovery.py::test_v2_plugin_backup_must_match_snapshot_before_any_recovery',
        'tests/test_backup_recovery.py::test_v2_backup_missing_digest_is_refused_without_recovery',
        'tests/test_backup_recovery.py::test_interruption_right_after_the_journal_only_clears_the_journal',
        'tests/test_backup_recovery.py::test_snapshot_is_never_overwritten_and_the_installer_takes_it_before_any_mutation',
        'tests/test_backup_recovery.py::test_interruption_before_the_plugin_moved_is_proven_by_the_snapshot_digest',
        'tests/test_backup_recovery.py::test_missing_backup_with_an_unprovable_plugin_refuses_and_keeps_the_journal',
        'tests/test_backup_recovery.py::test_version_1_snapshot_cannot_prove_plugin_identity'
    )
    Write-Host 'EXECUTING ONLY OFFLINE SELECTED PYTEST:'
    Write-Host ('py -3.12 -B -m pytest -q -rA -p no:cacheprovider '+($cases -join ' '))
    & py -3.12 -B -m pytest -q -rA -p no:cacheprovider @cases
    $pytestExit=$LASTEXITCODE
    Write-Host "PYTEST_EXIT_CODE=$pytestExit"
    if ($pytestExit -ne 0) { throw "M2 offline rollback proof tests failed with exit $pytestExit" }
} finally {
    Set-Location -LiteralPath $originalCwd
    foreach($name in $names) {
        if ($before[$name].Exists) {
            Set-Item -Path ('Env:'+$name) -Value $before[$name].Value
        } else {
            Remove-Item -Path ('Env:'+$name) -ErrorAction SilentlyContinue
        }
    }
    $drift=@()
    foreach($name in $names) {
        $actual=Get-Item -Path ('Env:'+$name) -ErrorAction SilentlyContinue
        if ($before[$name].Exists) {
            if ($null -eq $actual -or $actual.Value -cne $before[$name].Value) {$drift+=$name}
        } elseif ($null -ne $actual) {$drift+=$name}
    }
    if ($drift.Count -gt 0) {
        throw ('PROCESS ENVIRONMENT RESTORATION REFUSED: '+($drift -join ','))
    }
    Write-Host 'PASS: PROCESS_ENVIRONMENT_RESTORED_AND_VERIFIED'
}
Assert-Exact (Invoke-PinnedGit $checkout @('rev-parse','HEAD')) $commit 'POST M2 HEAD'
Assert-Exact (Invoke-PinnedGit $checkout @('rev-parse','HEAD^{tree}')) $tree 'POST M2 tree'
Assert-ProtectedBlobs 'POST'
if (Invoke-PinnedGit $checkout @('status','--porcelain=v1','--untracked-files=all')) {
    throw 'M2 source changed during offline tests.'
}
Write-Host 'PASS: POST M2 DETACHED WORKTREE CLEAN'
Write-Host "M2_ROLLBACK_OFFLINE_TEST_EXIT_CODE=$pytestExit"
Write-Host 'VRES_PERSONAL_M2_INTEGRATED_ROLLBACK_WINDOWS_TEST_COMPLETE_PENDING_EVALUATION'
Write-Host 'No real installer, PostgreSQL, native Claude, installed hooks or credentials were authorized.'
