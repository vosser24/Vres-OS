# VRES PERSONAL M3 CHAIRMAN BRIEFING R1 — ONE GUARDED WINDOWS OFFLINE TEST
# Run in ordinary Windows PowerShell 5.1 ONLY; NOT Claude Code.
# NO PostgreSQL (even SELECT), installed Vres/Claude/PRISM, real credentials, legacy work.
$ErrorActionPreference = 'Stop'
$repo = 'C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
$review = 'C:\Projects\Vres-Review-M3-Chairman-Briefing-20261103'
$branch = 'feature/personal-m3-chairman-resume-briefing-20261103'
$candidate = '71660b74d86530307aa2c766d30bed281e8781f5'
$candidateTree = 'cba76ff174c665a760d45eeb880378bbcc7fedbf'
$parent = 'eede9e118a3cf46ce5a3ad7ff328af9629fd3341'
$parentTree = '9c5af806ab200b0c6a441643cdacc541d0a34ec9'
$base = '1469765d7403f1985aa9ba65978299fdaa32f941'
$baseTree = 'e05f4d632b5226d4f1946c1fa0da8c116c8c108f'
$p2 = '82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
$p2Tree = '205c081277ece483c634e1c801c39595abd4549c'
$blobs = [ordered]@{
  'src/vres_os/hooks.py' = '69f9491633548c7cccc4d086ef48e4d7bb9e0f38'
  'src/vres_os/personal_resume_briefing.py' = '282ee12855393e453cfecc1c3dd500ad47fc2205'
  'tests/test_personal_resume_briefing.py' = '903d697d79ac03c2f539c9b69e3a5a21b96d7b25'
}
function GitRead {
  param([string]$Root, [string[]]$ArgsList)
  $output = & git -C $Root -c core.hooksPath=NUL -c core.fsmonitor=false @ArgsList
  if ($LASTEXITCODE -ne 0) { throw ('Git refused: ' + ($ArgsList -join ' ')) }
  return $output
}
function Exact {
  param([string]$Label,[string]$Observed,[string]$Expected)
  if ($Observed -cne $Expected) {
    throw ('MISMATCH ' + $Label + ': observed=' + $Observed + ' expected=' + $Expected)
  }
  Write-Host ('PASS: ' + $Label)
}
Write-Host '=== M3 CHAIRMAN BRIEFING OFFLINE PREFLIGHT ==='
if (-not (Test-Path -LiteralPath $repo -PathType Container)) { throw 'Original P2 checkout missing' }
if (Test-Path -LiteralPath $review) { throw 'M3 briefing review checkout exists; preserve and STOP' }
if (-not (Test-Path -LiteralPath (Split-Path -Parent $review) -PathType Container)) { throw 'C:\Projects does not exist' }
$origin = [string](GitRead $repo @('remote','get-url','origin'))
if ($origin -notin @('https://github.com/vosser24/Vres-OS.git','https://github.com/vosser24/Vres-OS')) { throw 'Unexpected Git origin' }
Exact 'original P2 HEAD' ([string](GitRead $repo @('rev-parse','HEAD'))) $p2
Exact 'original P2 TREE' ([string](GitRead $repo @('rev-parse','HEAD^{tree}'))) $p2Tree
if (@(GitRead $repo @('status','--porcelain')).Count -ne 0) { throw 'Original P2 not clean' }
Write-Host 'PASS: official origin and original P2 clean'
GitRead $repo @('fetch','--no-tags','origin',('refs/heads/' + $branch)) | Out-Null
Exact 'fetched feature HEAD' ([string](GitRead $repo @('rev-parse','FETCH_HEAD'))) $candidate
Exact 'feature TREE' ([string](GitRead $repo @('rev-parse',($candidate + '^{tree}')))) $candidateTree
Exact 'feature direct parent' ([string](GitRead $repo @('rev-parse',($candidate + '^')))) $parent
Exact 'first M3 briefing author commit TREE' ([string](GitRead $repo @('rev-parse',($parent + '^{tree}')))) $parentTree
Exact 'accepted original M3 base parent' ([string](GitRead $repo @('rev-parse',($candidate + '^^')))) $base
Exact 'accepted original M3 base TREE' ([string](GitRead $repo @('rev-parse',($base + '^{tree}')))) $baseTree
# Normalize only TAB/SPACE separator, never unexpected paths or statuses.
$rawScope = @(GitRead $repo @('diff','--name-status',$base,$candidate,'--'))
$actualScope = @()
foreach ($line in $rawScope) {
  $match = [regex]::Match([string]$line, '^(A|M)[ \t]+([^\r\n]+)$')
  if (-not $match.Success) { throw ('Unrecognized changed-path record: ' + [string]$line) }
  $actualScope += ($match.Groups[1].Value + ':' + $match.Groups[2].Value)
}
$expectedScope = @(
  'M:src/vres_os/hooks.py'
  'A:src/vres_os/personal_resume_briefing.py'
  'A:tests/test_personal_resume_briefing.py'
)
if ($actualScope.Count -ne 3) { throw ('Changed-path count differs: ' + $actualScope.Count) }
foreach ($expected in $expectedScope) {
  if ($actualScope -cnotcontains $expected) { throw ('Unexpected/missing change: ' + $expected) }
}
Write-Host 'PASS: exact three path/status identities (case-sensitive)'
foreach ($entry in $blobs.GetEnumerator()) {
  Exact ('PRE ' + $entry.Key) ([string](GitRead $repo @('rev-parse',($candidate + ':' + $entry.Key)))) $entry.Value
}
GitRead $repo @('worktree','add','--detach',$review,$candidate) | Out-Null
Exact 'review HEAD' ([string](GitRead $review @('rev-parse','HEAD'))) $candidate
Exact 'review TREE' ([string](GitRead $review @('rev-parse','HEAD^{tree}'))) $candidateTree
if (@(GitRead $review @('status','--porcelain')).Count -ne 0) { throw 'New review checkout not clean' }
Write-Host 'PASS: new detached M3 briefing checkout clean'
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw 'py.exe unavailable' }
$temp = Join-Path ([IO.Path]::GetTempPath()) ('vres-m3-chairman-' + [guid]::NewGuid().ToString('N'))
if (Test-Path -LiteralPath $temp) { throw 'Temporary directory collision' }
New-Item -ItemType Directory -Path $temp -ErrorAction Stop | Out-Null
$prior = @{}
$names = @(
  'LOCALAPPDATA','APPDATA','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONUSERBASE',
  'PYTHONINSPECT','PYTHONDONTWRITEBYTECODE','PYTEST_ADDOPTS','PYTEST_PLUGINS',
  'PYTEST_DISABLE_PLUGIN_AUTOLOAD','VRES_DATA_DIR'
)
$names += @(Get-ChildItem Env: | Where-Object {
  $_.Name -match '^(PG[A-Z_]|GIT_|VRES_|DATABASE_URL$)'
} | ForEach-Object { $_.Name })
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
  $stdout = Join-Path $temp 'selected-pytest-stdout.txt'
  $stderr = Join-Path $temp 'selected-pytest-stderr.txt'
  $modules = @(
    'tests/test_personal_resume_briefing.py',
    'tests/test_personal_session_resume_ambiguity.py',
    'tests/test_compaction_hooks.py'
  )
  Write-Host '=== M3 CHAIRMAN BRIEFING OFFLINE PYTEST ==='
  $settings = @{
    FilePath = (Get-Command py).Source
    ArgumentList = (@('-3.12','-B','-m','pytest','-q','-rA','-p','no:cacheprovider') + $modules)
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
  $passed = @($log | Where-Object {
    $_ -match '^PASSED tests/(test_personal_resume_briefing|test_personal_session_resume_ambiguity|test_compaction_hooks)\.py::'
  })
  $bad = @($log | Where-Object { $_ -match '^(FAILED|ERROR|SKIPPED) tests/' })
  $unique = @($passed | Sort-Object -Unique)
  Write-Host ('NAMED_PASSED_CASES=' + $passed.Count)
  Write-Host ('UNIQUE_PASSED_CASES=' + $unique.Count)
  Write-Host ('NAMED_FAILED_ERROR_SKIPPED_CASES=' + $bad.Count)
  $passed | ForEach-Object { Write-Host $_ }
  if ($run.ExitCode -ne 0 -or $passed.Count -ne 52 -or $unique.Count -ne 52 -or $bad.Count -ne 0) {
    Write-Host '=== PYTEST FAILURE DIAGNOSTIC ==='
    $log | Select-Object -Last 110
    if ((Get-Item -LiteralPath $stderr).Length -gt 0) {
      Get-Content -LiteralPath $stderr | Select-Object -Last 50
    }
    throw 'M3 briefing offline suite failed exit0 / 52 unique PASS / 0 failures or skips gate'
  }
  Write-Host 'PASS: SELECTED_M3_CHAIRMAN_BRIEFING_WINDOWS_OFFLINE_52'
} finally {
  foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$prior[$name],'Process') }
  $notRestored = @($names | Where-Object {
    [Environment]::GetEnvironmentVariable($_,'Process') -cne $prior[$_]
  })
  if ($notRestored.Count -gt 0) { throw ('Process environment restoration failed: ' + ($notRestored -join ', ')) }
  Write-Host 'PASS: PROCESS_ENVIRONMENT_RESTORED_AND_VERIFIED'
}
Write-Host '=== M3 CHAIRMAN BRIEFING GIT POSTFLIGHT ==='
Exact 'POST review HEAD' ([string](GitRead $review @('rev-parse','HEAD'))) $candidate
Exact 'POST review TREE' ([string](GitRead $review @('rev-parse','HEAD^{tree}'))) $candidateTree
foreach ($entry in $blobs.GetEnumerator()) {
  Exact ('POST ' + $entry.Key) ([string](GitRead $review @('rev-parse',('HEAD:' + $entry.Key)))) $entry.Value
}
if (@(GitRead $review @('status','--porcelain')).Count -ne 0) { throw 'M3 briefing checkout changed unexpectedly' }
Exact 'POST original P2 HEAD' ([string](GitRead $repo @('rev-parse','HEAD'))) $p2
Exact 'POST original P2 TREE' ([string](GitRead $repo @('rev-parse','HEAD^{tree}'))) $p2Tree
if (@(GitRead $repo @('status','--porcelain')).Count -ne 0) { throw 'Original P2 checkout changed unexpectedly' }
Write-Host 'PASS: original P2 and M3 briefing checkout clean'
Write-Host 'VRES_PERSONAL_M3_CHAIRMAN_BRIEFING_R1_OFFLINE_POSTFLIGHT_COMPLETE_PENDING_EVALUATION'
Write-Host 'NO installed Vres update, native Claude, PostgreSQL contact or real credentials authorized.'
