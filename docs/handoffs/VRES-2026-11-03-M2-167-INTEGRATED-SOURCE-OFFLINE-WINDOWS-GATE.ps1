& {
# VRES PERSONAL M2 + #167 — ONE INTEGRATED OFFLINE WINDOWS SOURCE ACCEPTANCE
# Run in ordinary Windows PowerShell 5.1 OUTSIDE native Claude Code.
# NO real installer, native Claude/hooks, PostgreSQL, Credential Locker, PRISM, or user-profile changes.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$anchor='C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
$checkout='C:\Projects\Vres-Review-M2-167-Integrated-20261103'
$branch='feature/personal-m2-167-offline-integrated-release-20261103'
$p2='82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
$parent='a65215a3b8b91ad4ab374c928ae3cf667e5b0f95'
$base='526fb9d61e4a61c26c19931f9adf2d68eecd1bc8'
$commit='7a1d2da36f9ef1475e7909ca8850b9b641380b1d'
$tree='98658c0270b65032f38ab38c0671c48b2a291bc1'
$blobs=[ordered]@{
  'install.ps1'='8b5dd6dcc3cc8315f7a4c27d0173b4963b52d933'
  'src/vres_os/install_recovery.py'='b35d559758e3b6721f43631dc499095f7895c5f3'
  'tests/test_install_rollback_proof.py'='f6fb2ab35dc6e39302437d7e1931f9e92220a55d'
  'src/vres_os/personal_data_sources.py'='ad08616bf89d34c0c5f52affff30813562d7a2f7'
  'src/vres_os/personal_data_source_store.py'='debd4368428ca14273ad64a6c2d4f3c583ad92d2'
  'tests/test_personal_data_sources.py'='46c66bc83bac97e67ed7538f9413d871d04b2ee2'
  'tests/test_personal_data_source_store.py'='c3d901ca42f5f5ae66687e6ed194d3d14f60ac2f'
  'tests/test_install_contract.py'='62310e3ff6af2f9a8f49f310bb32ffea45e53752'
  'tests/test_install_preflight.py'='97a105499e1a64a4bf5b7352f445ca4926453df2'
  'tests/test_backup_recovery.py'='90b590aa6276049346ae3bf4b71014ac732ebaa7'
  'tests/test_release_artifact.py'='a50d8451f415de6b446f60ed2e277615301eddc1'
  'src/vres_os/release_inputs.py'='a0cdf3195f0cf0f2a61ce32521a74f78260832f7'
  'src/vres_os/release_artifact.py'='ddfc1beacad98199b489dc6f56456baf4d519c6a'
  'src/vres_os/database_targets.py'='cf292984331cf6e7aca07e9fc573f0ade0e9e579'
  'src/vres_os/credential_broker.py'='41f1b83fca0b3245de392e688ed0ed895b1f1cd7'
  'plugins/vres-os/hooks/hooks.json'='e286e4be47d058ee6ed6a3169fc45803aedc0df1'
  'tests/conftest.py'='1c33bb206dbf42691a6af9a709514bf3cc9994af'
}
function Git-Safe([string]$root,[string[]]$cmd) {
  $out=& git -c core.hooksPath=NUL -c core.fsmonitor=false -C $root @cmd
  if($LASTEXITCODE -ne 0){throw ('Git operation refused: '+($cmd -join ' '))}
  return (($out | Out-String).Trim())
}
function Expect([string]$observed,[string]$expected,[string]$label) {
  if($observed -cne $expected){throw "MISMATCH $label: $observed != $expected"}
  Write-Host "PASS: $label"
}
function Pin-Blobs([string]$phase) {
  foreach($f in $blobs.GetEnumerator()){
    Expect (Git-Safe $checkout @('rev-parse',('HEAD:'+$f.Key))) $f.Value "$phase $($f.Key)"
  }
}
Write-Host '=== VRES M2 + #167 INTEGRATED SOURCE PREFLIGHT: NO INSTALL ==='
if($env:OS -ne 'Windows_NT' -or $PSVersionTable.PSVersion.Major -ne 5){
  throw 'Requires native Windows PowerShell 5.1, outside Claude Code'
}
if(-not (Test-Path -LiteralPath $anchor -PathType Container)){throw 'Original P2 anchor missing'}
if(Test-Path -LiteralPath $checkout){throw 'New integrated worktree path exists; refuse overwrite'}
Expect (Git-Safe $anchor @('rev-parse','HEAD')) $p2 'protected P2 anchor HEAD'
if(Git-Safe $anchor @('status','--porcelain=v1','--untracked-files=all')){
  throw 'Protected original P2 anchor is not clean'
}
$origin=Git-Safe $anchor @('remote','get-url','origin')
if($origin -notin @('https://github.com/vosser24/Vres-OS','https://github.com/vosser24/Vres-OS.git')){
  throw 'Untrusted origin'
}
Git-Safe $anchor @('fetch','--no-tags','origin',('refs/heads/'+$branch)) | Out-Null
Expect (Git-Safe $anchor @('rev-parse','FETCH_HEAD')) $commit 'remote integrated feature HEAD'
Git-Safe $anchor @('worktree','add','--detach',$checkout,$commit) | Out-Null
Expect (Git-Safe $checkout @('rev-parse','HEAD')) $commit 'detached integrated HEAD'
Expect (Git-Safe $checkout @('rev-parse','HEAD^{tree}')) $tree 'detached integrated tree'
Expect (Git-Safe $checkout @('rev-parse','HEAD^')) $parent 'sole accepted M2 parent'
Git-Safe $checkout @('merge-base','--is-ancestor',$p2,$commit) | Out-Null
Write-Host 'PASS: original P2 ancestor'
$actual=@(& git -c core.hooksPath=NUL -C $checkout diff --name-status $base $commit)
if($LASTEXITCODE -ne 0){throw 'Failed to inspect integration changed paths'}
$expected=@(
  ('M'+[char]9+'install.ps1'),
  ('M'+[char]9+'src/vres_os/install_recovery.py'),
  ('A'+[char]9+'src/vres_os/personal_data_source_store.py'),
  ('A'+[char]9+'src/vres_os/personal_data_sources.py'),
  ('A'+[char]9+'tests/test_install_rollback_proof.py'),
  ('A'+[char]9+'tests/test_personal_data_source_store.py'),
  ('A'+[char]9+'tests/test_personal_data_sources.py')
)
if(@(Compare-Object $expected $actual).Count -ne 0){
  throw ('Unexpected source integration scope: '+($actual -join ', '))
}
Write-Host 'PASS: exact seven-path M2 + #167 source union'
Git-Safe $checkout @('diff','--check',$base,$commit) | Out-Null
Write-Host 'PASS: Git diff whitespace integrity'
Pin-Blobs 'PRE'
if(Git-Safe $checkout @('status','--porcelain=v1','--untracked-files=all')){
  throw 'Candidate checkout dirty before tests'
}
Write-Host 'VRES_M2_167_INTEGRATED_PRETEST_PASS'

$names=@('PYTHONPATH','PYTHONDONTWRITEBYTECODE','PYTEST_DISABLE_PLUGIN_AUTOLOAD',
  'VRES_DATA_DIR','VRES_ALLOW_TEST_DB','VRES_TEST_DATABASE_URL','VRES_INTEGRATION_OPT_IN',
  'DATABASE_URL','PGHOST','PGPORT','PGDATABASE','PGUSER','PGPASSWORD','PGSERVICE',
  'PGSERVICEFILE','PGPASSFILE','PGOPTIONS','CLAUDE_CONFIG_DIR')
$saved=@{}
foreach($key in $names){
  $v=Get-Item -Path ('Env:'+$key) -ErrorAction SilentlyContinue
  $saved[$key]=@{Exists=($null -ne $v);Value=$(if($null -ne $v){$v.Value}else{$null})}
}
$priorCwd=(Get-Location).Path
$testExit='NOT_RUN'
$releaseExit='NOT_RUN'
try {
  foreach($key in $names){Remove-Item -Path ('Env:'+$key) -ErrorAction SilentlyContinue}
  $sandbox=Join-Path ([IO.Path]::GetTempPath()) ('vres-m2-167-integrated-'+[guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Force -Path $sandbox | Out-Null
  $env:VRES_DATA_DIR=Join-Path $sandbox 'isolated-appdata'
  $env:PYTHONDONTWRITEBYTECODE='1'
  $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
  $env:VRES_INTEGRATION_OPT_IN='0'
  Set-Location -LiteralPath $checkout
  $releaseLog=Join-Path $sandbox 'release-inputs.txt'
  Write-Host '=== OFFLINE PERSONAL RELEASE-INPUT VALIDATION (NO DB CONTACT) ==='
  & py -3.12 -I -B src/vres_os/release_inputs.py --root $checkout 2>&1 |
    Tee-Object -FilePath $releaseLog
  $releaseExit=$LASTEXITCODE
  Write-Host "RELEASE_INPUTS_EXIT_CODE=$releaseExit"
  if($releaseExit -ne 0){throw "Release-inputs validation failed; log: $releaseLog"}

  $cases=@(
    'tests/test_install_rollback_proof.py',
    'tests/test_install_contract.py',
    'tests/test_install_preflight.py',
    'tests/test_release_artifact.py',
    'tests/test_personal_data_sources.py',
    'tests/test_personal_data_source_store.py',
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
  $pytestLog=Join-Path $sandbox 'integrated-pytest-full.txt'
  Write-Host 'EXECUTING ONE COMBINED OFFLINE M2 + #167 SELECTED PYTEST; NATIVE OUTPUT CAPTURED'
  & py -3.12 -B -m pytest -q -rA -p no:cacheprovider @cases 2>&1 |
    Tee-Object -FilePath $pytestLog
  $testExit=$LASTEXITCODE
  Write-Host "PYTEST_EXIT_CODE=$testExit"
  Write-Host "PYTEST_LOG=$pytestLog"
  if($testExit -ne 0){throw "Selected combined tests failed; preserve $pytestLog"}
  if(-not (Select-String -LiteralPath $pytestLog -Pattern '[0-9]+ passed' -Quiet)){
    throw 'Pytest did not produce a captured passed-case summary; evidence incomplete'
  }
} finally {
  Set-Location -LiteralPath $priorCwd
  foreach($key in $names){
    if($saved[$key].Exists){Set-Item -Path ('Env:'+$key) -Value $saved[$key].Value}
    else{Remove-Item -Path ('Env:'+$key) -ErrorAction SilentlyContinue}
  }
  $drift=@()
  foreach($key in $names){
    $now=Get-Item -Path ('Env:'+$key) -ErrorAction SilentlyContinue
    if($saved[$key].Exists){
      if($null -eq $now -or $now.Value -cne $saved[$key].Value){$drift+=$key}
    }elseif($null -ne $now){$drift+=$key}
  }
  if($drift.Count){throw ('Process environment restoration failed: '+($drift -join ','))}
  Write-Host 'PASS: PROCESS_ENVIRONMENT_RESTORED_AND_VERIFIED'
}
Expect (Git-Safe $checkout @('rev-parse','HEAD')) $commit 'POST integrated HEAD'
Expect (Git-Safe $checkout @('rev-parse','HEAD^{tree}')) $tree 'POST integrated tree'
Pin-Blobs 'POST'
if(Git-Safe $checkout @('status','--porcelain=v1','--untracked-files=all')){
  throw 'Integrated worktree changed during tests'
}
Write-Host 'PASS: POST DETACHED WORKTREE CLEAN'
Write-Host "M2_167_INTEGRATED_PYTEST_EXIT_CODE=$testExit"
Write-Host "M2_167_INTEGRATED_RELEASE_INPUTS_EXIT_CODE=$releaseExit"
Write-Host "PYTEST_LOG=$pytestLog"
Write-Host "RELEASE_INPUTS_LOG=$releaseLog"
Write-Host 'VRES_M2_167_PERSONAL_INTEGRATED_WINDOWS_OFFLINE_ACCEPTANCE_PENDING_EVALUATION'
Write-Host 'NO installed Vres update, ordinary native Claude, PostgreSQL or real credentials authorized.'
}
