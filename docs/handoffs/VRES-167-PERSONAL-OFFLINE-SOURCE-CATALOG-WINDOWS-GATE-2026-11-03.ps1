# VRES #167 — PERSONAL OFFLINE DATA-SOURCE CATALOG (ONE WINDOWS SELECTED TEST)
# Native Windows PowerShell 5.1 only, OUTSIDE Claude Code. NO installed changes.
# Does NOT run Vres CLI, installer, Credential Locker, hooks, PostgreSQL or PRISM.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$anchor='C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
$checkout='C:\Projects\Vres-ChatGPT-Review-167-Offline-Catalog-20261103'
$branch='feature/167-personal-offline-source-catalog-20261103'
$p2='82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
$parent='526fb9d61e4a61c26c19931f9adf2d68eecd1bc8'
$commit='16f8df95a001527bdd1ed94dfd3a963016109384'
$tree='54cc836906b1f63e074e0aebf2e24cb5e7b875fd'
$blobs=[ordered]@{
    'src/vres_os/personal_data_sources.py'='ad08616bf89d34c0c5f52affff30813562d7a2f7'
    'tests/test_personal_data_sources.py'='f669097b93618ba2213f5d2db3e6f8d3d4ca380b'
    'src/vres_os/credential_broker.py'='41f1b83fca0b3245de392e688ed0ed895b1f1cd7'
    'src/vres_os/project.py'='1174025eb49d6ff938e8de89f2a0e7236cf4ea5d'
    'src/vres_os/database_targets.py'='cf292984331cf6e7aca07e9fc573f0ade0e9e579'
    'plugins/vres-os/hooks/hooks.json'='e286e4be47d058ee6ed6a3169fc45803aedc0df1'
    'src/vres_os/release_inputs.py'='a0cdf3195f0cf0f2a61ce32521a74f78260832f7'
    'tests/conftest.py'='1c33bb206dbf42691a6af9a709514bf3cc9994af'
    'install.ps1'='d52ab1c2f5d81c44d53026c09e426ea4f18571c5'
}
function Invoke-SafeGit([string]$cwd,[string[]]$arguments) {
    $out=& git -c core.hooksPath=NUL -c core.fsmonitor=false -C $cwd @arguments
    if($LASTEXITCODE -ne 0){throw ('Git read/worktree step refused: '+($arguments -join ' '))}
    return (($out | Out-String).Trim())
}
function Assert-Exact([string]$actual,[string]$expected,[string]$label) {
    if($actual -cne $expected){throw ("MISMATCH $label actual=$actual expected=$expected")}
    Write-Host "PASS: $label"
}
function Test-ProtectedBlobs([string]$phase) {
    foreach($entry in $blobs.GetEnumerator()){
        Assert-Exact (Invoke-SafeGit $checkout @('rev-parse',('HEAD:'+$entry.Key))) $entry.Value "$phase $($entry.Key)"
    }
}
Write-Host '=== VRES #167 PURE OFFLINE WINDOWS PREFLIGHT ==='
if($env:OS -ne 'Windows_NT'){throw 'Windows-only source gate refused.'}
if(-not (Test-Path -LiteralPath $anchor -PathType Container)){throw 'Original protected P2 checkout missing.'}
if(Test-Path -LiteralPath $checkout){throw 'Refusing to reuse or overwrite the proposed #167 worktree.'}
Assert-Exact (Invoke-SafeGit $anchor @('rev-parse','HEAD')) $p2 'protected original P2 HEAD'
if(Invoke-SafeGit $anchor @('status','--porcelain=v1','--untracked-files=all')){throw 'Original P2 checkout is not clean.'}
$origin=Invoke-SafeGit $anchor @('remote','get-url','origin')
if($origin -notin @('https://github.com/vosser24/Vres-OS.git','https://github.com/vosser24/Vres-OS')){throw 'Unexpected Git origin.'}
Invoke-SafeGit $anchor @('fetch','--no-tags','origin',('refs/heads/'+$branch)) | Out-Null
Assert-Exact (Invoke-SafeGit $anchor @('rev-parse','FETCH_HEAD')) $commit '#167 GitHub remote source'
Invoke-SafeGit $anchor @('worktree','add','--detach',$checkout,$commit) | Out-Null
Assert-Exact (Invoke-SafeGit $checkout @('rev-parse','HEAD')) $commit 'detached #167 HEAD'
Assert-Exact (Invoke-SafeGit $checkout @('rev-parse','HEAD^{tree}')) $tree 'detached #167 tree'
Assert-Exact (Invoke-SafeGit $checkout @('rev-parse','HEAD^')) $parent 'accepted M2-HOST source parent'
Invoke-SafeGit $checkout @('merge-base','--is-ancestor',$p2,$commit) | Out-Null
Write-Host 'PASS: P2 is a source ancestor'
$changed=@(& git -c core.hooksPath=NUL -C $checkout diff --name-status $parent $commit)
if($LASTEXITCODE -ne 0){throw 'Cannot verify changed path list.'}
$expected=@(
    ('A'+[char]9+'src/vres_os/personal_data_sources.py'),
    ('A'+[char]9+'tests/test_personal_data_sources.py')
)
if(@(Compare-Object $changed $expected).Count -ne 0){throw ('Source change allowlist mismatch: '+($changed -join ';'))}
Write-Host 'PASS: exact two added-file source allowlist'
Invoke-SafeGit $checkout @('diff','--check',$parent,$commit) | Out-Null
Write-Host 'PASS: Git diff integrity'
Test-ProtectedBlobs 'PRE'
if(Invoke-SafeGit $checkout @('status','--porcelain=v1','--untracked-files=all')){throw 'Candidate worktree dirty before tests.'}
Write-Host 'VRES_167_PERSONAL_OFFLINE_PREFLIGHT_PASS'

$names=@('PYTHONPATH','PYTHONDONTWRITEBYTECODE','PYTEST_DISABLE_PLUGIN_AUTOLOAD',
         'VRES_DATA_DIR','VRES_ALLOW_TEST_DB','VRES_TEST_DATABASE_URL',
         'VRES_INTEGRATION_OPT_IN','DATABASE_URL','PGHOST','PGPORT','PGDATABASE',
         'PGUSER','PGPASSWORD','PGSERVICE','PGSERVICEFILE','PGPASSFILE',
         'PGOPTIONS','CLAUDE_CONFIG_DIR')
$priorEnv=@{}
foreach($name in $names){
    $value=Get-Item -Path ('Env:'+$name) -ErrorAction SilentlyContinue
    $priorEnv[$name]=@{Exists=($null -ne $value);Value=$(if($null -ne $value){$value.Value}else{$null})}
}
$priorCwd=(Get-Location).Path
$testExit='NOT_RUN'
try {
    foreach($name in $names){Remove-Item -Path ('Env:'+$name) -ErrorAction SilentlyContinue}
    $sandbox=Join-Path ([IO.Path]::GetTempPath()) ('vres-167-offline-'+[guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $sandbox | Out-Null
    $env:VRES_DATA_DIR=Join-Path $sandbox 'isolated-data'
    $env:PYTHONDONTWRITEBYTECODE='1'
    $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
    $env:VRES_INTEGRATION_OPT_IN='0'
    Set-Location -LiteralPath $checkout
    Write-Host 'RUNNING ONLY: py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_personal_data_sources.py'
    & py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_personal_data_sources.py
    $testExit=$LASTEXITCODE
    Write-Host "PYTEST_EXIT_CODE=$testExit"
    if($testExit -ne 0){throw "Pure #167 offline pytest exited $testExit"}
} finally {
    Set-Location -LiteralPath $priorCwd
    foreach($name in $names){
        if($priorEnv[$name].Exists){Set-Item -Path ('Env:'+$name) -Value $priorEnv[$name].Value}
        else{Remove-Item -Path ('Env:'+$name) -ErrorAction SilentlyContinue}
    }
    $drift=@()
    foreach($name in $names){
        $value=Get-Item -Path ('Env:'+$name) -ErrorAction SilentlyContinue
        if($priorEnv[$name].Exists){
            if($null -eq $value -or $value.Value -cne $priorEnv[$name].Value){$drift+=$name}
        }elseif($null -ne $value){$drift+=$name}
    }
    if($drift.Count -gt 0){throw ('Environment restoration failed: '+($drift -join ','))}
    Write-Host 'PASS: PROCESS_ENVIRONMENT_RESTORED_AND_VERIFIED'
}
Assert-Exact (Invoke-SafeGit $checkout @('rev-parse','HEAD')) $commit 'POST #167 HEAD'
Assert-Exact (Invoke-SafeGit $checkout @('rev-parse','HEAD^{tree}')) $tree 'POST #167 tree'
Test-ProtectedBlobs 'POST'
if(Invoke-SafeGit $checkout @('status','--porcelain=v1','--untracked-files=all')){throw 'Candidate worktree changed during tests.'}
Write-Host 'PASS: POST #167 DETACHED WORKTREE CLEAN'
Write-Host "VRES_167_OFFLINE_TEST_EXIT_CODE=$testExit"
Write-Host 'VRES_PERSONAL_167_OFFLINE_CATALOG_WINDOWS_SELECTED_TEST_COMPLETE_PENDING_EVALUATION'
Write-Host 'No real Credential Locker access, Vres installation, Claude hook or PostgreSQL access was requested.'
