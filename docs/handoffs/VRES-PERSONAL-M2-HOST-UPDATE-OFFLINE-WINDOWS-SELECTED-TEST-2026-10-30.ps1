# VRES M2-HOST — ONE OFFLINE WINDOWS SOURCE / REGRESSION GATE
# NOT THE INSTALLER. NEVER INVOKES CLAUDE, HOOKS, PRISM, VRES CLI OR POSTGRESQL.
# Use native Windows PowerShell 5.1, OUTSIDE Claude Code. Do not edit the SHAs.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$anchor='C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
$checkout='C:\Projects\Vres-ChatGPT-Review-Personal-M2-Host-20261030'
$branch='feature/personal-m2-host-update-no-prereq-path-mutation-20261030'
$p2='82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
$parent='28120eb49b6b950c7402455db19dcbdcf6d991a6'
$commit='526fb9d61e4a61c26c19931f9adf2d68eecd1bc8'
$tree='9919f363a8608e31e4c5a6f66adb765c7021b484'
$blobs=[ordered]@{
    'install.ps1'='d52ab1c2f5d81c44d53026c09e426ea4f18571c5'
    'tests/test_install_contract.py'='62310e3ff6af2f9a8f49f310bb32ffea45e53752'
    'tests/test_install_preflight.py'='97a105499e1a64a4bf5b7352f445ca4926453df2'
    'tests/conftest.py'='1c33bb206dbf42691a6af9a709514bf3cc9994af'
    'src/vres_os/install_recovery.py'='ac780fab49d8ca94d343f91e3d4b774f8be3bf46'
    'src/vres_os/release_artifact.py'='ddfc1beacad98199b489dc6f56456baf4d519c6a'
    'src/vres_os/release_inputs.py'='a0cdf3195f0cf0f2a61ce32521a74f78260832f7'
    'plugins/vres-os/hooks/hooks.json'='e286e4be47d058ee6ed6a3169fc45803aedc0df1'
    'src/vres_os/database_targets.py'='cf292984331cf6e7aca07e9fc573f0ade0e9e579'
}
function Run-GitSafe([string]$cwd,[string[]]$argv) {
    $out=& git -c core.hooksPath=NUL -c core.fsmonitor=false -C $cwd @argv
    if ($LASTEXITCODE -ne 0) { throw ('Git failed: '+($argv -join ' ')) }
    return (($out | Out-String).Trim())
}
function Require-Equal([string]$actual,[string]$expected,[string]$name) {
    if ($actual -cne $expected) { throw "MISMATCH $name observed=$actual expected=$expected" }
    Write-Host "PASS: $name"
}
function Check-Blobs([string]$phase) {
    foreach ($item in $blobs.GetEnumerator()) {
        Require-Equal (Run-GitSafe $checkout @('rev-parse',('HEAD:'+$item.Key))) $item.Value "$phase $($item.Key)"
    }
}
Write-Host '=== M2-HOST PINNED WINDOWS OFFLINE PREFLIGHT ==='
if ($env:OS -ne 'Windows_NT') { throw 'Windows-only gate refused.' }
if (-not (Test-Path -LiteralPath $anchor -PathType Container)) { throw 'Original P2 anchor not found.' }
if (Test-Path -LiteralPath $checkout) { throw 'Proposed M2 worktree already exists; do not overwrite.' }
Require-Equal (Run-GitSafe $anchor @('rev-parse','HEAD')) $p2 'protected original P2 HEAD'
if (Run-GitSafe $anchor @('status','--porcelain=v1','--untracked-files=all')) {
    throw 'Protected original P2 worktree is not clean.'
}
$origin=Run-GitSafe $anchor @('remote','get-url','origin')
if ($origin -notin @('https://github.com/vosser24/Vres-OS.git',
                     'https://github.com/vosser24/Vres-OS')) {
    throw 'Git origin is not the official Vres-OS repository.'
}
Run-GitSafe $anchor @('fetch','--no-tags','origin',('refs/heads/'+$branch)) | Out-Null
Require-Equal (Run-GitSafe $anchor @('rev-parse','FETCH_HEAD')) $commit 'official remote M2 source'
Run-GitSafe $anchor @('worktree','add','--detach',$checkout,$commit) | Out-Null
Require-Equal (Run-GitSafe $checkout @('rev-parse','HEAD')) $commit 'M2 detached HEAD'
Require-Equal (Run-GitSafe $checkout @('rev-parse','HEAD^{tree}')) $tree 'M2 candidate tree'
Require-Equal (Run-GitSafe $checkout @('rev-parse','HEAD^')) $parent 'sole M1 parent'
Run-GitSafe $checkout @('merge-base','--is-ancestor',$p2,$commit) | Out-Null
Write-Host 'PASS: P2 is ancestor of M2 candidate'
$actual=@(& git -c core.hooksPath=NUL -C $checkout diff --name-status $parent $commit)
if ($LASTEXITCODE -ne 0) { throw 'Cannot compare exact source changes.' }
$expected=@(('M'+[char]9+'install.ps1'),
             ('M'+[char]9+'tests/test_install_contract.py'))
if (@(Compare-Object $expected $actual).Count -ne 0) {
    throw ('Two-file change allowlist mismatch: '+($actual -join '; '))
}
Write-Host 'PASS: exact two-file M2 change allowlist'
Run-GitSafe $checkout @('diff','--check',$parent,$commit) | Out-Null
Write-Host 'PASS: diff integrity'
Check-Blobs 'PRE'
if (Run-GitSafe $checkout @('status','--porcelain=v1','--untracked-files=all')) {
    throw 'Detached candidate checkout is dirty before tests.'
}
$variables=@('PYTHONPATH','PYTHONDONTWRITEBYTECODE','PYTEST_DISABLE_PLUGIN_AUTOLOAD',
             'VRES_DATA_DIR','VRES_ALLOW_TEST_DB','VRES_TEST_DATABASE_URL',
             'VRES_INTEGRATION_OPT_IN','DATABASE_URL','PGHOST','PGPORT','PGDATABASE',
             'PGUSER','PGPASSWORD','PGSERVICE','PGSERVICEFILE','PGPASSFILE',
             'PGOPTIONS','CLAUDE_CONFIG_DIR')
$envBefore=@{}
foreach($name in $variables) {
    $old=Get-Item -Path ('Env:'+$name) -ErrorAction SilentlyContinue
    $envBefore[$name]=@{
        Exists=($null -ne $old)
        Value=$(if($null -ne $old){$old.Value}else{$null})
    }
}
$oldCwd=(Get-Location).Path
$testExit='NOT_RUN'
try {
    foreach($name in $variables) {
        Remove-Item -Path ('Env:'+$name) -ErrorAction SilentlyContinue
    }
    $sandbox=Join-Path ([IO.Path]::GetTempPath()) ('vres-m2-offline-'+[guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $sandbox | Out-Null
    $env:VRES_DATA_DIR=Join-Path $sandbox 'isolated-data'
    $env:PYTHONDONTWRITEBYTECODE='1'
    $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
    $env:VRES_INTEGRATION_OPT_IN='0'
    Set-Location -LiteralPath $checkout
    Write-Host 'EXECUTING ONLY: py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_install_contract.py tests/test_install_preflight.py'
    & py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_install_contract.py tests/test_install_preflight.py
    $testExit=$LASTEXITCODE
    Write-Host "PYTEST_EXIT_CODE=$testExit"
    if ($testExit -ne 0) { throw "Offline M2 selected pytest failed with exit=$testExit" }
} finally {
    Set-Location -LiteralPath $oldCwd
    foreach($name in $variables) {
        if ($envBefore[$name].Exists) {
            Set-Item -Path ('Env:'+$name) -Value $envBefore[$name].Value
        } else {
            Remove-Item -Path ('Env:'+$name) -ErrorAction SilentlyContinue
        }
    }
    $drift=@()
    foreach($name in $variables) {
        $value=Get-Item -Path ('Env:'+$name) -ErrorAction SilentlyContinue
        if ($envBefore[$name].Exists) {
            if ($null -eq $value -or $value.Value -cne $envBefore[$name].Value) { $drift+=$name }
        } elseif($null -ne $value){ $drift+=$name }
    }
    if ($drift.Count -ne 0) { throw ('ENV RESTORE MISMATCH: '+($drift -join ', ')) }
    Write-Host 'PASS: PROCESS_ENVIRONMENT_RESTORED_AND_VERIFIED'
}
Require-Equal (Run-GitSafe $checkout @('rev-parse','HEAD')) $commit 'POST M2 HEAD'
Require-Equal (Run-GitSafe $checkout @('rev-parse','HEAD^{tree}')) $tree 'POST M2 tree'
Check-Blobs 'POST'
if (Run-GitSafe $checkout @('status','--porcelain=v1','--untracked-files=all')) {
    throw 'M2 checkout changed during offline validation.'
}
Write-Host 'PASS: DETACHED_WORKTREE_CLEAN'
Write-Host "M2_HOST_OFFLINE_TEST_EXIT_CODE=$testExit"
Write-Host 'VRES_PERSONAL_M2_HOST_WINDOWS_SELECTED_TEST_COMPLETE_PENDING_EVALUATION'
Write-Host 'NO installed Vres, native Claude Code, hook, credential or PostgreSQL operation authorized.'
