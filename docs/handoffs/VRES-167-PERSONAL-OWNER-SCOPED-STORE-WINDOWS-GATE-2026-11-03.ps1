& {
# VRES #167 — CURRENT-USER OFFLINE CATALOG STORE: ONE GUARDED WINDOWS GATE
# Run as ONE pasted block in ordinary Windows PowerShell 5.1 OUTSIDE Claude Code.
# Does not run installer, Vres CLI, Claude/hooks, Credential Locker, PostgreSQL or PRISM.
# Pure Python tests use isolated TEMP fixtures, synthetic metadata and fake ACL callbacks.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$anchor='C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
$checkout='C:\Projects\Vres-Review-167-Personal-Store-20261103'
$branch='feature/167-personal-owner-scoped-catalog-store-20261103'
$p2='82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
$parent='f909f61ab95a25fdfae5fbe3412ba233165f15b7'
$commit='2cb4f975e235a89fac5186e3529dbd492d8b6972'
$tree='697f6ce12eb3c9c23338e20180a6ffd204bac40e'
$blobs=[ordered]@{
    'src/vres_os/personal_data_source_store.py'='debd4368428ca14273ad64a6c2d4f3c583ad92d2'
    'tests/test_personal_data_source_store.py'='c3d901ca42f5f5ae66687e6ed194d3d14f60ac2f'
    'src/vres_os/personal_data_sources.py'='ad08616bf89d34c0c5f52affff30813562d7a2f7'
    'tests/test_personal_data_sources.py'='46c66bc83bac97e67ed7538f9413d871d04b2ee2'
    'src/vres_os/credential_broker.py'='41f1b83fca0b3245de392e688ed0ed895b1f1cd7'
    'src/vres_os/project.py'='1174025eb49d6ff938e8de89f2a0e7236cf4ea5d'
    'src/vres_os/database_targets.py'='cf292984331cf6e7aca07e9fc573f0ade0e9e579'
    'plugins/vres-os/hooks/hooks.json'='e286e4be47d058ee6ed6a3169fc45803aedc0df1'
    'src/vres_os/release_inputs.py'='a0cdf3195f0cf0f2a61ce32521a74f78260832f7'
    'install.ps1'='d52ab1c2f5d81c44d53026c09e426ea4f18571c5'
    'tests/conftest.py'='1c33bb206dbf42691a6af9a709514bf3cc9994af'
    'src/vres_os/install_recovery.py'='ac780fab49d8ca94d343f91e3d4b774f8be3bf46'
}
function Read-Git([string]$root,[string[]]$argv) {
    $value=& git -c core.hooksPath=NUL -c core.fsmonitor=false -C $root @argv
    if($LASTEXITCODE -ne 0){throw ('Git refused: '+($argv -join ' '))}
    return (($value | Out-String).Trim())
}
function Match-SHA([string]$actual,[string]$expected,[string]$label) {
    if($actual -cne $expected){throw "MISMATCH $label actual=$actual expected=$expected"}
    Write-Host "PASS: $label"
}
function Check-Blobs([string]$phase) {
    foreach($entry in $blobs.GetEnumerator()){
        Match-SHA (Read-Git $checkout @('rev-parse',('HEAD:'+$entry.Key))) $entry.Value "$phase $($entry.Key)"
    }
}

Write-Host '=== VRES PERSONAL #167 STORE — EXACT GITHUB/WORKTREE PREFLIGHT ==='
if($env:OS -ne 'Windows_NT'){throw 'Native Windows PowerShell 5.1 only.'}
if(-not (Test-Path -LiteralPath $anchor -PathType Container)){throw 'Protected original P2 Git checkout absent.'}
if(Test-Path -LiteralPath $checkout){throw 'Selected review checkout exists; refuse overwrite or reuse.'}
Match-SHA (Read-Git $anchor @('rev-parse','HEAD')) $p2 'original protected P2 HEAD'
if(Read-Git $anchor @('status','--porcelain=v1','--untracked-files=all')){throw 'Original P2 anchor not clean.'}
$origin=Read-Git $anchor @('remote','get-url','origin')
if($origin -notin @('https://github.com/vosser24/Vres-OS','https://github.com/vosser24/Vres-OS.git')){
    throw 'Refused: Git origin is not official vosser24/Vres-OS.'
}
Read-Git $anchor @('fetch','--no-tags','origin',('refs/heads/'+$branch)) | Out-Null
Match-SHA (Read-Git $anchor @('rev-parse','FETCH_HEAD')) $commit 'official #167 store HEAD'
Read-Git $anchor @('worktree','add','--detach',$checkout,$commit) | Out-Null
Match-SHA (Read-Git $checkout @('rev-parse','HEAD')) $commit 'detached candidate HEAD'
Match-SHA (Read-Git $checkout @('rev-parse','HEAD^{tree}')) $tree 'detached candidate tree'
Match-SHA (Read-Git $checkout @('rev-parse','HEAD^')) $parent 'sole Windows-accepted #167 R1 parent'
Read-Git $checkout @('merge-base','--is-ancestor',$p2,$commit) | Out-Null
Write-Host 'PASS: original P2 source is an ancestor'
$changed=@(& git -c core.hooksPath=NUL -C $checkout diff --name-status $parent $commit)
if($LASTEXITCODE -ne 0){throw 'Failed to compare exact changed paths.'}
$expected=@(
    ('A'+[char]9+'src/vres_os/personal_data_source_store.py'),
    ('A'+[char]9+'tests/test_personal_data_source_store.py')
)
if(@(Compare-Object $expected $changed).Count -ne 0){
    throw ('Unexpected change-path allowlist: '+($changed -join '; '))
}
Write-Host 'PASS: exact two added source/test paths'
Read-Git $checkout @('diff','--check',$parent,$commit) | Out-Null
Write-Host 'PASS: diff whitespace integrity'
Check-Blobs 'PRE'
if(Read-Git $checkout @('status','--porcelain=v1','--untracked-files=all')){
    throw 'Detached checkout dirty before tests.'
}
Write-Host 'VRES_167_STORE_PRETEST_INTEGRITY_PASS'

$names=@('PYTHONPATH','PYTHONDONTWRITEBYTECODE','PYTEST_DISABLE_PLUGIN_AUTOLOAD',
         'VRES_DATA_DIR','VRES_ALLOW_TEST_DB','VRES_TEST_DATABASE_URL','VRES_INTEGRATION_OPT_IN',
         'DATABASE_URL','PGHOST','PGPORT','PGDATABASE','PGUSER','PGPASSWORD',
         'PGSERVICE','PGSERVICEFILE','PGPASSFILE','PGOPTIONS','CLAUDE_CONFIG_DIR')
$before=@{}
foreach($name in $names) {
    $item=Get-Item -Path ('Env:'+$name) -ErrorAction SilentlyContinue
    $before[$name]=@{Exists=($null -ne $item);Value=$(if($null -ne $item){$item.Value}else{$null})}
}
$originalCwd=(Get-Location).Path
$testExit='NOT_RUN'
try {
    foreach($name in $names){Remove-Item -Path ('Env:'+$name) -ErrorAction SilentlyContinue}
    $sandbox=Join-Path ([IO.Path]::GetTempPath()) ('vres-167-store-'+[guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $sandbox | Out-Null
    $env:VRES_DATA_DIR=Join-Path $sandbox 'isolated-appdata'
    $env:PYTHONDONTWRITEBYTECODE='1'
    $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
    $env:VRES_INTEGRATION_OPT_IN='0'
    Set-Location -LiteralPath $checkout
    Write-Host 'EXECUTING ONLY OFFLINE PYTEST: personal data-source store and pure catalog'
    & py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_personal_data_source_store.py tests/test_personal_data_sources.py
    $testExit=$LASTEXITCODE
    Write-Host "PYTEST_EXIT_CODE=$testExit"
    if($testExit -ne 0){throw "Offline #167 store tests failed with exit $testExit"}
} finally {
    Set-Location -LiteralPath $originalCwd
    foreach($name in $names) {
        if($before[$name].Exists){Set-Item -Path ('Env:'+$name) -Value $before[$name].Value}
        else{Remove-Item -Path ('Env:'+$name) -ErrorAction SilentlyContinue}
    }
    $drift=@()
    foreach($name in $names) {
        $current=Get-Item -Path ('Env:'+$name) -ErrorAction SilentlyContinue
        if($before[$name].Exists) {
            if($null -eq $current -or $current.Value -cne $before[$name].Value){$drift+=$name}
        } elseif($null -ne $current){$drift+=$name}
    }
    if($drift.Count -gt 0){throw ('PROCESS ENVIRONMENT RESTORATION FAILED: '+($drift -join ','))}
    Write-Host 'PASS: PROCESS_ENVIRONMENT_RESTORED_AND_VERIFIED'
}
Match-SHA (Read-Git $checkout @('rev-parse','HEAD')) $commit 'POST #167 store HEAD'
Match-SHA (Read-Git $checkout @('rev-parse','HEAD^{tree}')) $tree 'POST #167 store tree'
Check-Blobs 'POST'
if(Read-Git $checkout @('status','--porcelain=v1','--untracked-files=all')){
    throw 'Detached store candidate changed after tests.'
}
Write-Host 'PASS: POST DETACHED WORKTREE CLEAN'
Write-Host "VRES_167_STORE_WINDOWS_OFFLINE_TEST_EXIT_CODE=$testExit"
if($testExit -ne 0){throw 'Exit0 evidence required; no completion marker on test failure.'}
Write-Host 'VRES_167_PERSONAL_OWNER_SCOPED_STORE_WINDOWS_SELECTED_TEST_COMPLETE_PENDING_EVALUATION'
Write-Host 'No real Vres install, native Claude, PostgreSQL, real vault, user profile or credentials were authorized.'
}
