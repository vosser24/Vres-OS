& {
# VRES PERSONAL M2+#167 — READ-ONLY EVIDENCE & POSTFLIGHT, NO PYTEST RERUN
# Native Windows PowerShell 5.1 OUTSIDE Claude Code. NO installer, PostgreSQL,
# Vres CLI, native Claude/hooks, Credential Locker, profile mutation or Git writes.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$checkout='C:\Projects\Vres-Review-M2-167-Integrated-20261103'
$anchor='C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
$logDir=Join-Path $env:TEMP 'vres-m2-167-integrated-9d2020caa4c14f10ae2d9543dfd5a24d'
$pytestLog=Join-Path $logDir 'integrated-pytest-full.txt'
$releaseLog=Join-Path $logDir 'release-inputs.txt'
$p2='82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
$commit='7a1d2da36f9ef1475e7909ca8850b9b641380b1d'
$tree='98658c0270b65032f38ab38c0671c48b2a291bc1'
$parent='a65215a3b8b91ad4ab374c928ae3cf667e5b0f95'
$base='526fb9d61e4a61c26c19931f9adf2d68eecd1bc8'
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
function Read-LocalGit([string]$dir,[string[]]$arguments) {
  $output=& git --no-optional-locks -c core.hooksPath=NUL -c core.fsmonitor=false -C $dir @arguments
  if($LASTEXITCODE -ne 0){throw ('Read-only Git command refused: '+($arguments -join ' '))}
  return (($output | Out-String).Trim())
}
function Assert-Match([string]$actual,[string]$expected,[string]$label) {
  if($actual -cne $expected){throw ('MISMATCH '+$label+' actual='+$actual+' expected='+$expected)}
  Write-Host ('PASS: '+$label)
}
Write-Host '=== VRES M2+#167 READ-ONLY POSTFLIGHT, NO PYTEST RERUN ==='
if($env:OS -ne 'Windows_NT' -or $PSVersionTable.PSVersion.Major -ne 5){
  throw 'Native Windows PowerShell 5.1 is required.'
}
if(-not (Test-Path -LiteralPath $checkout -PathType Container)){
  throw 'Original integrated review worktree missing; refuse substitution.'
}
if(-not (Test-Path -LiteralPath $anchor -PathType Container)){
  throw 'Protected original P2 anchor missing.'
}
foreach($item in @(
  @{Path=$pytestLog; Expected='CA068AE86CF62E63E7041710AD8962EE330C2D97B0518F74D521A1FA0D286FFB'; Size=71168},
  @{Path=$releaseLog; Expected='CAE4096DFF7D155555E9AF4CF1DD9F8639624575ED02508C55953A2A2D17B010'; Size=164}
)){
  if(-not (Test-Path -LiteralPath $item.Path -PathType Leaf)){
    throw ('Original evidence file is missing: '+$item.Path)
  }
  $size=(Get-Item -LiteralPath $item.Path).Length
  if($size -ne $item.Size){throw ('Evidence log byte size differs: '+$item.Path)}
  $actual=(Get-FileHash -LiteralPath $item.Path -Algorithm SHA256).Hash
  Assert-Match $actual $item.Expected ('saved evidence SHA256 '+[IO.Path]::GetFileName($item.Path))
}
$lines=@(Get-Content -LiteralPath $pytestLog)
$passing=@($lines | Where-Object { $_ -match '^PASSED tests/' })
$skippedLines=@($lines | Where-Object { $_ -match '^SKIPPED \[\d+\]' })
$skipCount=0
foreach($line in $skippedLines){
  if($line -match '^SKIPPED \[(\d+)\]'){$skipCount += [int]$Matches[1]}
}
if($passing.Count -ne 254){throw ('Unexpected PASS count: '+$passing.Count)}
if(@($passing | Sort-Object -Unique).Count -ne 254){
  throw 'Duplicate or missing individual PASS identities.'
}
if($skipCount -ne 3){throw ('Unexpected skip count: '+$skipCount)}
if($skippedLines.Count -ne 2){throw 'Unexpected skip reason line count.'}
Write-Host 'PASS: 254 unique passed test identities and 3 documented Windows symlink skips'
Assert-Match (Read-LocalGit $anchor @('rev-parse','HEAD')) $p2 'original protected P2 HEAD'
if(Read-LocalGit $anchor @('status','--porcelain=v1','--untracked-files=all')){
  throw 'Original protected P2 worktree not clean.'
}
$origin=Read-LocalGit $anchor @('remote','get-url','origin')
if($origin -notin @('https://github.com/vosser24/Vres-OS','https://github.com/vosser24/Vres-OS.git')){
  throw 'Git origin mismatch.'
}
Assert-Match (Read-LocalGit $checkout @('rev-parse','HEAD')) $commit 'POST integrated HEAD'
Assert-Match (Read-LocalGit $checkout @('rev-parse','HEAD^{tree}')) $tree 'POST integrated tree'
Assert-Match (Read-LocalGit $checkout @('rev-parse','HEAD^')) $parent 'POST single M2 parent'
$changed=@(& git --no-optional-locks -c core.hooksPath=NUL -c core.fsmonitor=false -C $checkout diff --no-ext-diff --no-textconv --name-status $base $commit)
if($LASTEXITCODE -ne 0){throw 'Changed-path read-only comparison failed.'}
$allowed=@(
  ('M'+[char]9+'install.ps1'),
  ('M'+[char]9+'src/vres_os/install_recovery.py'),
  ('A'+[char]9+'src/vres_os/personal_data_source_store.py'),
  ('A'+[char]9+'src/vres_os/personal_data_sources.py'),
  ('A'+[char]9+'tests/test_install_rollback_proof.py'),
  ('A'+[char]9+'tests/test_personal_data_source_store.py'),
  ('A'+[char]9+'tests/test_personal_data_sources.py')
)
if(@(Compare-Object $changed $allowed).Count -ne 0){
  throw 'POST integrated seven-file scope mismatch.'
}
Write-Host 'PASS: POST exact seven-file source change allowlist'
foreach($entry in $blobs.GetEnumerator()){
  Assert-Match (Read-LocalGit $checkout @('rev-parse',('HEAD:'+$entry.Key))) $entry.Value ('POST '+$entry.Key)
}
if(Read-LocalGit $checkout @('status','--porcelain=v1','--untracked-files=all')){
  throw 'Integrated review checkout not clean after tests.'
}
Write-Host 'PASS: POST integrated detached review worktree clean'
Write-Host 'POSTFLIGHT_PASSED_CASES=254'
Write-Host 'POSTFLIGHT_SKIPPED_CASES=3'
Write-Host 'VRES_M2_167_INTEGRATED_READ_ONLY_POSTFLIGHT_COMPLETE_PENDING_EVALUATION'
Write-Host 'No pytest rerun, native Claude, PostgreSQL, Vres installation or credential access.'
}
