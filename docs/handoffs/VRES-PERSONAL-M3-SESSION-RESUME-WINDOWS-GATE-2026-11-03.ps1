# VRES M3 P1: ONE guarded Windows source-only test, never run in Claude Code.
# No installed Vres/Claude/PRISM changes, hooks, PostgreSQL, credentials or legacy project.
$ErrorActionPreference = 'Stop'
$repo = 'C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
$review = 'C:\Projects\Vres-Review-M3-Session-Resume-20261103'
$branch = 'feature/personal-m3-session-resume-ambiguity-guard-20261103'
$candidate = '1469765d7403f1985aa9ba65978299fdaa32f941'
$tree = 'e05f4d632b5226d4f1946c1fa0da8c116c8c108f'
$parent = '7a1d2da36f9ef1475e7909ca8850b9b641380b1d'
$parentTree = '98658c0270b65032f38ab38c0671c48b2a291bc1'
$p2 = '82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
$p2Tree = '205c081277ece483c634e1c801c39595abd4549c'
$blobs = [ordered]@{
  'src/vres_os/session_lifecycle.py' = '090122c81caddd0cc19490c31f3fb22011bf740d'
  'src/vres_os/hooks.py' = '481b7fe49dfb024d8029278f354299666dc1888e'
  'tests/test_personal_session_resume_ambiguity.py' = '64288c3d23bea59e2307f22937d9f56d4cc42c00'
}
function GitRead {
  param([string]$Root,[string[]]$CommandArgs)
  $result = & git -C $Root -c core.hooksPath=NUL -c core.fsmonitor=false @CommandArgs
  if ($LASTEXITCODE -ne 0) { throw ('Git refused: ' + ($CommandArgs -join ' ')) }
  return $result
}
function Exact {
  param([string]$Label,[string]$Found,[string]$Expected)
  if ($Found -cne $Expected) { throw ('MISMATCH ' + $Label + ': ' + $Found + ' != ' + $Expected) }
  Write-Host ('PASS: ' + $Label)
}
if (-not (Test-Path -LiteralPath $repo -PathType Container)) { throw 'Protected P2 Git anchor missing' }
if (Test-Path -LiteralPath $review) { throw 'Review worktree exists; preserve it and stop' }
if (-not (Test-Path -LiteralPath (Split-Path -Parent $review) -PathType Container)) { throw 'C:\Projects missing' }
$origin = [string](GitRead $repo @('remote','get-url','origin'))
if ($origin -notin @('https://github.com/vosser24/Vres-OS.git','https://github.com/vosser24/Vres-OS')) { throw 'Unexpected GitHub origin' }
Exact 'original P2 checkout HEAD' ([string](GitRead $repo @('rev-parse','HEAD'))) $p2
Exact 'original P2 checkout TREE' ([string](GitRead $repo @('rev-parse','HEAD^{tree}'))) $p2Tree
if (@(GitRead $repo @('status','--porcelain')).Count -ne 0) { throw 'Original P2 checkout not clean' }
Write-Host 'PASS: original P2 checkout clean and official origin'
GitRead $repo @('fetch','--no-tags','origin',('refs/heads/' + $branch)) | Out-Null
Exact 'remote candidate' ([string](GitRead $repo @('rev-parse','FETCH_HEAD'))) $candidate
Exact 'candidate tree' ([string](GitRead $repo @('rev-parse',($candidate + '^{tree}')))) $tree
Exact 'sole direct parent' ([string](GitRead $repo @('rev-parse',($candidate + '^')))) $parent
Exact 'accepted M2+#167 parent tree' ([string](GitRead $repo @('rev-parse',($parent + '^{tree}')))) $parentTree
$actual = @(GitRead $repo @('diff','--name-status',$parent,$candidate,'--') | Sort-Object)
$expected = @(
  'M	src/vres_os/hooks.py'
  'M	src/vres_os/session_lifecycle.py'
  'A	tests/test_personal_session_resume_ambiguity.py'
) | Sort-Object
if (@(Compare-Object -ReferenceObject $expected -DifferenceObject $actual).Count -ne 0) {
  throw ('Unexpected changed-path scope: ' + ($actual -join ', '))
}
Write-Host 'PASS: exact three changed source/test paths'
foreach ($entry in $blobs.GetEnumerator()) {
  Exact ('PRE ' + $entry.Key) ([string](GitRead $repo @('rev-parse',($candidate + ':' + $entry.Key)))) $entry.Value
}
GitRead $repo @('worktree','add','--detach',$review,$candidate) | Out-Null
Exact 'review checkout HEAD' ([string](GitRead $review @('rev-parse','HEAD'))) $candidate
if (@(GitRead $review @('status','--porcelain')).Count -ne 0) { throw 'New review checkout not clean' }
Write-Host 'PASS: new detached review worktree clean'
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw 'Python launcher py.exe is unavailable' }
$temp = Join-Path ([IO.Path]::GetTempPath()) ('vres-m3-resume-' + [guid]::NewGuid().ToString('N'))
if (Test-Path -LiteralPath $temp) { throw 'TEMP collision' }
New-Item -ItemType Directory -Path $temp -ErrorAction Stop | Out-Null
$prior = @{}
$names = @('LOCALAPPDATA','APPDATA','PYTHONPATH','PYTHONDONTWRITEBYTECODE','PYTEST_DISABLE_PLUGIN_AUTOLOAD','VRES_DATA_DIR')
$names += @(Get-ChildItem Env: | Where-Object { $_.Name -match '^(PG[A-Z_]|GIT_|VRES_|DATABASE_URL$)' } | ForEach-Object { $_.Name })
$names = @($names | Sort-Object -Unique)
try {
  foreach ($name in $names) {
    $prior[$name] = [Environment]::GetEnvironmentVariable($name,'Process')
    [Environment]::SetEnvironmentVariable($name,$null,'Process')
  }
  New-Item -ItemType Directory -Path (Join-Path $temp 'Local'),(Join-Path $temp 'Roaming') | Out-Null
  $env:LOCALAPPDATA = Join-Path $temp 'Local'
  $env:APPDATA = Join-Path $temp 'Roaming'
  $env:VRES_DATA_DIR = Join-Path $temp 'VresData'
  $env:PYTHONPATH = Join-Path $review 'src'
  $env:PYTHONDONTWRITEBYTECODE = '1'
  $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
  $stdout = Join-Path $temp 'm3-pytest-stdout.txt'
  $stderr = Join-Path $temp 'm3-pytest-stderr.txt'
  $settings = @{
    FilePath = (Get-Command py).Source
    ArgumentList = @('-3.12','-B','-m','pytest','-q','-rA','-p','no:cacheprovider','tests/test_personal_session_resume_ambiguity.py')
    WorkingDirectory = $review
    Wait = $true
    PassThru = $true
    NoNewWindow = $true
    RedirectStandardOutput = $stdout
    RedirectStandardError = $stderr
  }
  $run = Start-Process @settings
  Write-Host ('PYTEST_EXIT_CODE=' + $run.ExitCode)
  $cases = @(Get-Content -LiteralPath $stdout | Where-Object { $_ -match '^PASSED tests/test_personal_session_resume_ambiguity\.py::' })
  $bad = @(Get-Content -LiteralPath $stdout | Where-Object { $_ -match '^(FAILED|ERROR|SKIPPED) tests/test_personal_session_resume_ambiguity\.py::' })
  Write-Host ('NAMED_PASSED_CASES=' + $cases.Count)
  Write-Host ('NAMED_FAILED_ERROR_SKIPPED_CASES=' + $bad.Count)
  $cases | ForEach-Object { Write-Host $_ }
  if ($run.ExitCode -ne 0 -or $cases.Count -ne 14 -or $bad.Count -ne 0) {
    Write-Host '=== PYTEST LOG TAIL ==='
    Get-Content -LiteralPath $stdout | Select-Object -Last 100
    if ((Get-Item -LiteralPath $stderr).Length -gt 0) { Get-Content -LiteralPath $stderr | Select-Object -Last 40 }
    throw 'M3 offline gate not accepted: expected 14 native PASSED cases, zero SKIPPED/FAILED and exit0'
  }
  Write-Host 'PASS: selected M3 synthetic offline pytest'
} finally {
  foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$prior[$name],'Process') }
  $different = @($names | Where-Object { [Environment]::GetEnvironmentVariable($_,'Process') -cne $prior[$_] })
  if ($different.Count -ne 0) { throw ('Environment restoration failed: ' + ($different -join ', ')) }
  Write-Host 'PASS: PROCESS_ENVIRONMENT_RESTORED_AND_VERIFIED'
}
Exact 'POST review HEAD' ([string](GitRead $review @('rev-parse','HEAD'))) $candidate
Exact 'POST review TREE' ([string](GitRead $review @('rev-parse','HEAD^{tree}'))) $tree
foreach ($entry in $blobs.GetEnumerator()) {
  Exact ('POST ' + $entry.Key) ([string](GitRead $review @('rev-parse',('HEAD:' + $entry.Key)))) $entry.Value
}
if (@(GitRead $review @('status','--porcelain')).Count -ne 0) { throw 'Review checkout changed unexpectedly' }
Exact 'POST original P2 HEAD' ([string](GitRead $repo @('rev-parse','HEAD'))) $p2
if (@(GitRead $repo @('status','--porcelain')).Count -ne 0) { throw 'Original P2 checkout changed unexpectedly' }
Write-Host 'PASS: both Git checkouts clean and source blobs preserved'
Write-Host 'VRES_PERSONAL_M3_OFFLINE_SESSION_RESUME_COMPLETE_PENDING_EVALUATION'
Write-Host 'NO installed update, native Claude, PostgreSQL or real credentials authorized.'
