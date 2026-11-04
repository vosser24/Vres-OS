# VRES PERSONAL BUNDLE B — DISPOSABLE EVERYDAY-USE JOURNEY (22 NEW CASES)
# Windows PowerShell 5.1; OFFLINE PYTEST only. Launch from ordinary PowerShell outside Claude.
# No real Claude, host hooks, installed Vres, credential use, PostgreSQL or real user-profile input.
$ErrorActionPreference = 'Stop'
$repo = 'C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
$review = 'C:\Projects\Vres-Review-BundleB-DailyJourney-20261104'
$branch = 'feature/personal-bundle-b-disposable-daily-journey-20261104'
$candidate = '00ff9e1a03a652cfcb1fdcbd7a09e53bfc3af788'
$candidateTree = '6816f280fd388f1921bcff235da97a68be87ede5'
$parent = '2b51b3aa9e4fe40fce53ffd457e1d5f218443209'
$parentTree = '34072a722efe221042ddc922c5461c1a1c3192da'
$p2 = '82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
$p2Tree = '205c081277ece483c634e1c801c39595abd4549c'
$blobs = [ordered]@{
  'src/vres_os/personal_disposable_daily_journey.py' = 'be6de92eddc8ab10ebe5d38892d45dce2f144e81'
  'tests/test_personal_disposable_daily_journey.py' = '3cb43cc88570394fbff85371a466064d3e439e79'
}
function GitRead {
  param([string]$Root, [string[]]$ArgsList)
  $output = & git -C $Root -c core.hooksPath=NUL -c core.fsmonitor=false @ArgsList
  if ($LASTEXITCODE -ne 0) { throw ('Git operation refused: ' + ($ArgsList -join ' ')) }
  return $output
}
function Exact {
  param([string]$Label,[string]$Observed,[string]$Expected)
  if ($Observed -cne $Expected) {
    throw ('MISMATCH ' + $Label + ': observed=' + $Observed + ' expected=' + $Expected)
  }
  Write-Host ('PASS: ' + $Label)
}
Write-Host '=== VRES BUNDLE B PERSONAL DISPOSABLE DAILY JOURNEY GIT PREFLIGHT ==='
if (-not (Test-Path -LiteralPath $repo -PathType Container)) { throw 'Protected original P2 checkout absent. STOP' }
if (Test-Path -LiteralPath $review) { throw 'New review path already exists; preserve it and STOP' }
if (-not (Test-Path -LiteralPath (Split-Path -Parent $review) -PathType Container)) { throw 'Review parent path absent. STOP' }
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw 'py.exe not available. STOP' }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'git not available. STOP' }
$pyExe = (Get-Command py).Source
$origin = [string](GitRead $repo @('remote','get-url','origin'))
if ($origin -cnotin @('https://github.com/vosser24/Vres-OS.git','https://github.com/vosser24/Vres-OS')) {
  throw ('Unexpected origin: ' + $origin)
}
Exact 'protected P2 HEAD' ([string](GitRead $repo @('rev-parse','HEAD'))) $p2
Exact 'protected P2 TREE' ([string](GitRead $repo @('rev-parse','HEAD^{tree}'))) $p2Tree
if (@(GitRead $repo @('status','--porcelain')).Count -ne 0) { throw 'Protected P2 checkout not clean. STOP' }
Write-Host 'PASS: protected original P2 clean and official origin'
GitRead $repo @('fetch','--no-tags','--no-recurse-submodules','origin',('refs/heads/' + $branch)) | Out-Null
Exact 'fetched remote feature HEAD' ([string](GitRead $repo @('rev-parse','FETCH_HEAD'))) $candidate
Exact 'new feature TREE' ([string](GitRead $repo @('rev-parse',($candidate + '^{tree}')))) $candidateTree
Exact 'feature SOLE parent' ([string](GitRead $repo @('rev-list','--parents','-n','1',$candidate))) ($candidate + ' ' + $parent)
Exact 'accepted M4 41-PASS parent TREE' ([string](GitRead $repo @('rev-parse',($parent + '^{tree}')))) $parentTree
$scope = @(GitRead $repo @('diff','--name-status',$parent,$candidate,'--'))
$actual = @()
foreach ($line in $scope) {
  $m = [regex]::Match([string]$line,'^(A|M)[ \t]+([^\r\n]+)$')
  if (-not $m.Success) { throw ('Unrecognized changed-path record: ' + [string]$line) }
  $actual += ($m.Groups[1].Value + ':' + $m.Groups[2].Value)
}
$expectedScope = @(
  'A:src/vres_os/personal_disposable_daily_journey.py',
  'A:tests/test_personal_disposable_daily_journey.py'
)
if ($actual.Count -ne $expectedScope.Count) { throw 'Changed scope count mismatch. STOP' }
foreach ($expected in $expectedScope) {
  if ($actual -cnotcontains $expected) { throw ('Missing exact changed path: ' + $expected) }
}
Write-Host 'PASS: exactly two allowed A paths, no modifications to accepted parent'
foreach ($entry in $blobs.GetEnumerator()) {
  Exact ('PRE Git blob ' + $entry.Key) ([string](GitRead $repo @('rev-parse',($candidate + ':' + $entry.Key)))) $entry.Value
}
GitRead $repo @('worktree','add','--detach',$review,$candidate) | Out-Null
Exact 'new detached review HEAD' ([string](GitRead $review @('rev-parse','HEAD'))) $candidate
Exact 'new detached review TREE' ([string](GitRead $review @('rev-parse','HEAD^{tree}'))) $candidateTree
if (@(GitRead $review @('status','--porcelain')).Count -ne 0) { throw 'Detached review checkout not clean' }
Write-Host 'PASS: exact new protected detached review checkout'
$temp = Join-Path ([IO.Path]::GetTempPath()) ('vres-bundle-b-daily-journey-' + [guid]::NewGuid().ToString('N'))
if (Test-Path -LiteralPath $temp) { throw 'TEMP collision. STOP' }
New-Item -ItemType Directory -Path $temp -ErrorAction Stop | Out-Null
$prior = @{}
$names = @(
  'LOCALAPPDATA','APPDATA','HOME','USERPROFILE','XDG_CONFIG_HOME','XDG_DATA_HOME',
  'PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONUSERBASE','PYTHONINSPECT',
  'PYTHONDONTWRITEBYTECODE','PYTEST_ADDOPTS','PYTEST_PLUGINS','PYTEST_DISABLE_PLUGIN_AUTOLOAD',
  'CLAUDE_CONFIG_DIR','CLAUDE_PROJECT_DIR','TEMP','TMP','TMPDIR','VRES_DATA_DIR'
)
$names += @(Get-ChildItem Env: | Where-Object {
  $_.Name -match '^(PG[A-Z0-9_]*|GIT_.+|VRES_.+|DATABASE(_.*)?|CLAUDE_.+|PRISM_.+|ANTHROPIC_.+|OPENAI_.+|AWS_.+|AZURE_.+|GOOGLE_.+|GITHUB_.+|GH_TOKEN$|PYTEST_.+)$'
} | ForEach-Object { $_.Name })
$names = @($names | Sort-Object -Unique)
try {
  foreach ($name in $names) {
    $prior[$name] = [Environment]::GetEnvironmentVariable($name,'Process')
    [Environment]::SetEnvironmentVariable($name,$null,'Process')
  }
  New-Item -ItemType Directory -Path (Join-Path $temp 'Local'),(Join-Path $temp 'Roaming'),(Join-Path $temp 'Home') -ErrorAction Stop | Out-Null
  $env:LOCALAPPDATA = Join-Path $temp 'Local'
  $env:APPDATA = Join-Path $temp 'Roaming'
  $env:HOME = Join-Path $temp 'Home'
  $env:USERPROFILE = Join-Path $temp 'Home'
  $env:XDG_CONFIG_HOME = Join-Path $temp 'Home'
  $env:XDG_DATA_HOME = Join-Path $temp 'Home'
  $env:VRES_DATA_DIR = Join-Path $temp 'VresData'
  $env:TEMP = $temp
  $env:TMP = $temp
  $env:TMPDIR = $temp
  $env:PYTHONPATH = Join-Path $review 'src'
  $env:PYTHONDONTWRITEBYTECODE = '1'
  $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
  $stdout = Join-Path $temp 'selected-pytest-stdout.txt'
  $stderr = Join-Path $temp 'selected-pytest-stderr.txt'
  Write-Host '=== VRES BUNDLE B PERSONAL DAILY JOURNEY SELECTED OFFLINE PYTEST ==='
  $settings = @{
    FilePath = $pyExe
    ArgumentList = @('-3.12','-B','-m','pytest','-q','-rA','-p','no:cacheprovider','tests/test_personal_disposable_daily_journey.py')
    WorkingDirectory = $review
    Wait = $true
    PassThru = $true
    NoNewWindow = $true
    RedirectStandardOutput = $stdout
    RedirectStandardError = $stderr
  }
  $run = Start-Process @settings
  Write-Host ('PYTEST_EXIT_CODE=' + $run.ExitCode)
  $log = @(Get-Content -LiteralPath $stdout)
  $passed = @($log | Where-Object { $_ -match '^PASSED tests/test_personal_disposable_daily_journey\.py::' })
  $allPassed = @($log | Where-Object { $_ -match '^PASSED tests/' })
  $bad = @($log | Where-Object { $_ -match '^(FAILED|ERROR|SKIPPED|XFAIL|XPASS) tests/' })
  $unique = @($passed | Sort-Object -Unique)
  Write-Host ('NAMED_PASSED_CASES=' + $passed.Count)
  Write-Host ('UNIQUE_PASSED_CASES=' + $unique.Count)
  Write-Host ('NAMED_FAILED_ERROR_SKIPPED_CASES=' + $bad.Count)
  $passed | ForEach-Object { Write-Host $_ }
  Write-Host ('CAPTURE_DIRECTORY=' + $temp)
  if ($run.ExitCode -ne 0 -or $passed.Count -ne 22 -or $unique.Count -ne 22 -or
      $allPassed.Count -ne 22 -or $bad.Count -ne 0) {
    Write-Host '=== SELECTED PYTEST FAILURE DIAGNOSTIC ==='
    $log | Select-Object -Last 120
    if ((Get-Item -LiteralPath $stderr).Length -gt 0) {
      Get-Content -LiteralPath $stderr | Select-Object -Last 60
    }
    throw 'Bundle B synthetic daily-use journey 22-case gate REFUSED; preserve output'
  }
  Write-Host 'PASS: SELECTED_BUNDLE_B_DISPOSABLE_DAILY_JOURNEY_WINDOWS_22_PENDING_EVALUATION'
}
finally {
  foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$prior[$name],'Process') }
  $notRestored = @($names | Where-Object {
    [Environment]::GetEnvironmentVariable($_,'Process') -cne $prior[$_]
  })
  if ($notRestored.Count -gt 0) {
    throw ('Process environment restoration mismatch: ' + ($notRestored -join ', '))
  }
  Write-Host 'PASS: PROCESS_ENVIRONMENT_RESTORED_AND_VERIFIED'
}
Write-Host '=== VRES BUNDLE B PERSONAL DAILY JOURNEY GIT POSTFLIGHT ==='
Exact 'POST review HEAD' ([string](GitRead $review @('rev-parse','HEAD'))) $candidate
Exact 'POST review TREE' ([string](GitRead $review @('rev-parse','HEAD^{tree}'))) $candidateTree
foreach ($entry in $blobs.GetEnumerator()) {
  Exact ('POST blob ' + $entry.Key) ([string](GitRead $review @('rev-parse',('HEAD:' + $entry.Key)))) $entry.Value
}
if (@(GitRead $review @('status','--porcelain')).Count -ne 0) { throw 'New review checkout changed during tests. STOP' }
Exact 'POST protected P2 HEAD' ([string](GitRead $repo @('rev-parse','HEAD'))) $p2
Exact 'POST protected P2 TREE' ([string](GitRead $repo @('rev-parse','HEAD^{tree}'))) $p2Tree
if (@(GitRead $repo @('status','--porcelain')).Count -ne 0) { throw 'Original protected P2 checkout changed. STOP' }
Write-Host 'PASS: original P2 and new Bundle B daily journey review checkout clean'
Write-Host 'VRES_PERSONAL_BUNDLE_B_DAILY_JOURNEY_WINDOWS_22_POSTFLIGHT_COMPLETE_PENDING_EVALUATION'
Write-Host 'No installed Vres, real Claude/PRISM, native hooks, credentials or PostgreSQL authorized.'
