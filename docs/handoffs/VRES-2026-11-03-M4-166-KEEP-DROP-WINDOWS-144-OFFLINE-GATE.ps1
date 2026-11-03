# VRES PERSONAL M4 #166 SYNTHETIC LEGACY CLAUDE KEEP/DROP — ONE SELECTED WINDOWS OFFLINE GATE
# Ordinary Windows PowerShell 5.1 ONLY, OUTSIDE Claude Code; source testing, NOT activation.
# Prohibited: PostgreSQL even SELECT; native Claude/hooks; installed Vres, PRISM, credentials or real global profile.
$ErrorActionPreference = 'Stop'
$repo = 'C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
$review = 'C:\Projects\Vres-Review-M4-Migration-20261103'
$branch = 'feature/personal-m4-global-legacy-migration-review-20261103'
$candidate = 'ec54f7535aa29d7588c25e221f6bd2bae7a437c8'
$candidateTree = 'd914c60169dc01c34b1cc987170cf66d66324bad'
$parent = '78c002f5835a9b6ae8da65ac6aa2841c6167ccb8'
$parentTree = 'b564f2d5d96b1f057e20401da8762ae54fb64b9a'
$p2 = '82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
$p2Tree = '205c081277ece483c634e1c801c39595abd4549c'
$blobs = [ordered]@{
  'src/vres_os/global_claude_migration_review.py' = '39fd0d4307e30b7aab385d6f1ae05dff40aeeac2'
  'tests/test_global_claude_migration_review.py' = '7fe37e0b6489e54f934aadaf27f755127fe9bc77'
}
$expectedCases = [ordered]@{
  'test_global_claude_migration_review' = 51
  'test_global_claude_fixture_transaction' = 47
  'test_global_claude_adoption_plan' = 43
  'test_claude_contract' = 3
}

function GitRead {
  param([string]$Root, [string[]]$ArgsList)
  $output = & git -C $Root -c core.hooksPath=NUL -c core.fsmonitor=false @ArgsList
  if ($LASTEXITCODE -ne 0) { throw ('Git operation refused: ' + ($ArgsList -join ' ')) }
  return $output
}
function Exact {
  param([string]$Label, [string]$Observed, [string]$Expected)
  if ($Observed -cne $Expected) {
    throw ('MISMATCH ' + $Label + ': observed=' + $Observed + ' expected=' + $Expected)
  }
  Write-Host ('PASS: ' + $Label)
}

Write-Host '=== VRES M4 #166 KEEP/DROP 144-CASE OFFLINE GIT PREFLIGHT ==='
if (-not (Test-Path -LiteralPath $repo -PathType Container)) { throw 'Protected original P2 source checkout missing: stop' }
if (Test-Path -LiteralPath $review) { throw 'Review checkout path already exists: preserve it and STOP' }
if (-not (Test-Path -LiteralPath (Split-Path -Parent $review) -PathType Container)) {
  throw 'Review checkout parent folder does not exist: STOP'
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'git unavailable' }
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw 'py.exe unavailable' }
$pyExe = (Get-Command py).Source
$origin = [string](GitRead $repo @('remote','get-url','origin'))
if ($origin -cnotin @('https://github.com/vosser24/Vres-OS.git','https://github.com/vosser24/Vres-OS')) {
  throw ('Unexpected GitHub origin: ' + $origin)
}
Exact 'protected original P2 HEAD' ([string](GitRead $repo @('rev-parse','HEAD'))) $p2
Exact 'protected original P2 TREE' ([string](GitRead $repo @('rev-parse','HEAD^{tree}'))) $p2Tree
if (@(GitRead $repo @('status','--porcelain')).Count -ne 0) { throw 'Protected P2 worktree not clean: STOP' }
Write-Host 'PASS: protected P2 clean and exact GitHub origin'

# Fetch ONLY the pinned source branch; no checkout or modification of protected P2 working files.
GitRead $repo @('fetch','--no-tags','--no-recurse-submodules','origin',('refs/heads/' + $branch)) | Out-Null
Exact 'remote fetched branch HEAD' ([string](GitRead $repo @('rev-parse','FETCH_HEAD'))) $candidate
Exact 'candidate TREE' ([string](GitRead $repo @('rev-parse',($candidate + '^{tree}')))) $candidateTree
Exact 'candidate SOLE parent' ([string](GitRead $repo @('rev-list','--parents','-n','1',$candidate))) ($candidate + ' ' + $parent)
Exact 'accepted source parent TREE' ([string](GitRead $repo @('rev-parse',($parent + '^{tree}')))) $parentTree
$rawScope = @(GitRead $repo @('diff','--name-status',$parent,$candidate,'--'))
$actualScope = @()
foreach ($line in $rawScope) {
  $match = [regex]::Match([string]$line, '^(A|M)[ \t]+([^\r\n]+)$')
  if (-not $match.Success) { throw ('Unrecognized changed-path status: ' + [string]$line) }
  $actualScope += ($match.Groups[1].Value + ':' + $match.Groups[2].Value)
}
$expectedScope = @(
  'A:src/vres_os/global_claude_migration_review.py'
  'A:tests/test_global_claude_migration_review.py'
)
if ($actualScope.Count -ne $expectedScope.Count) { throw 'Unexpected changed-path count: STOP' }
foreach ($expected in $expectedScope) {
  if ($actualScope -cnotcontains $expected) { throw ('Missing or changed path identity: ' + $expected) }
}
Write-Host 'PASS: exactly two allowlisted A paths; no other source changes'
foreach ($entry in $blobs.GetEnumerator()) {
  Exact ('PRE blob ' + $entry.Key) ([string](GitRead $repo @('rev-parse',($candidate + ':' + $entry.Key)))) $entry.Value
}
GitRead $repo @('worktree','add','--detach',$review,$candidate) | Out-Null
Exact 'detached review HEAD' ([string](GitRead $review @('rev-parse','HEAD'))) $candidate
Exact 'detached review TREE' ([string](GitRead $review @('rev-parse','HEAD^{tree}'))) $candidateTree
if (@(GitRead $review @('status','--porcelain')).Count -ne 0) { throw 'New detached review worktree is not clean' }
Write-Host 'PASS: clean protected detached review checkout created; no install'

# Process-only environment isolation. No real user-profile, credential, hook or DB environment is passed to pytest.
$temp = Join-Path ([IO.Path]::GetTempPath()) ('vres-m4-keep-drop-' + [guid]::NewGuid().ToString('N'))
if (Test-Path -LiteralPath $temp) { throw 'Temporary directory collision: STOP' }
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
  $modules = @(
    'tests/test_global_claude_migration_review.py',
    'tests/test_global_claude_fixture_transaction.py',
    'tests/test_global_claude_adoption_plan.py',
    'tests/test_claude_contract.py'
  )
  Write-Host '=== VRES M4 #166 SELECTED OFFLINE PYTEST (EXPECTED 144, NOT PRE-ACCEPTED) ==='
  $settings = @{
    FilePath = $pyExe
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
  $allNamed = @($log | Where-Object { $_ -match '^PASSED tests/' })
  $passed = @($allNamed | Where-Object {
    $_ -match '^PASSED tests/(test_global_claude_migration_review|test_global_claude_fixture_transaction|test_global_claude_adoption_plan|test_claude_contract)\.py::'
  })
  $bad = @($log | Where-Object { $_ -match '^(FAILED|ERROR|SKIPPED|XFAIL|XPASS) tests/' })
  $unique = @($passed | Sort-Object -Unique)
  Write-Host ('NAMED_PASSED_CASES=' + $passed.Count)
  Write-Host ('UNIQUE_PASSED_CASES=' + $unique.Count)
  Write-Host ('NAMED_FAILED_ERROR_SKIPPED_CASES=' + $bad.Count)
  $perModuleOK = $true
  foreach ($entry in $expectedCases.GetEnumerator()) {
    $part = @($passed | Where-Object {
      $_ -match ('^PASSED tests/' + [regex]::Escape($entry.Key) + '\.py::')
    })
    Write-Host ('NAMED_PASSED_' + $entry.Key + '=' + $part.Count + ' EXPECTED=' + $entry.Value)
    if ($part.Count -ne $entry.Value) { $perModuleOK = $false }
  }
  $passed | ForEach-Object { Write-Host $_ }
  Write-Host ('CAPTURE_DIRECTORY=' + $temp)
  if ($run.ExitCode -ne 0 -or $passed.Count -ne 144 -or $unique.Count -ne 144 -or
      $allNamed.Count -ne 144 -or $bad.Count -ne 0 -or -not $perModuleOK) {
    Write-Host '=== SELECTED PYTEST FAILURE DIAGNOSTIC ==='
    $log | Select-Object -Last 115
    if ((Get-Item -LiteralPath $stderr).Length -gt 0) {
      Get-Content -LiteralPath $stderr | Select-Object -Last 60
    }
    throw 'M4 #166 144-case selected offline acceptance REFUSED: preserve logs and do not activate anything'
  }
  Write-Host 'PASS: SELECTED_M4_166_KEEP_DROP_WINDOWS_OFFLINE_144_PENDING_REVIEW'
} finally {
  foreach ($name in $names) {
    [Environment]::SetEnvironmentVariable($name,$prior[$name],'Process')
  }
  $notRestored = @($names | Where-Object {
    [Environment]::GetEnvironmentVariable($_,'Process') -cne $prior[$_]
  })
  if ($notRestored.Count -gt 0) { throw ('Process environment restoration FAILED: ' + ($notRestored -join ', ')) }
  Write-Host 'PASS: PROCESS_ENVIRONMENT_RESTORED_AND_VERIFIED'
}

Write-Host '=== VRES M4 #166 KEEP/DROP GIT POSTFLIGHT ==='
Exact 'POST detached review HEAD' ([string](GitRead $review @('rev-parse','HEAD'))) $candidate
Exact 'POST detached review TREE' ([string](GitRead $review @('rev-parse','HEAD^{tree}'))) $candidateTree
foreach ($entry in $blobs.GetEnumerator()) {
  Exact ('POST blob ' + $entry.Key) ([string](GitRead $review @('rev-parse',('HEAD:' + $entry.Key)))) $entry.Value
}
if (@(GitRead $review @('status','--porcelain')).Count -ne 0) { throw 'Detached review checkout unexpectedly changed' }
Exact 'POST protected P2 HEAD' ([string](GitRead $repo @('rev-parse','HEAD'))) $p2
Exact 'POST protected P2 TREE' ([string](GitRead $repo @('rev-parse','HEAD^{tree}'))) $p2Tree
if (@(GitRead $repo @('status','--porcelain')).Count -ne 0) { throw 'Protected original P2 checkout unexpectedly changed' }
Write-Host 'PASS: protected P2 and new M4 #166 review worktrees remain clean'
Write-Host 'VRES_PERSONAL_M4_166_KEEP_DROP_WINDOWS_144_POSTFLIGHT_COMPLETE_PENDING_EVALUATION'
Write-Host 'NO installed Vres, native Claude/PRISM, PostgreSQL, real user/global profile or credentials authorized.'
