# Vres-OS BUNDLE B — ONE disposable, source-pinned PERSONAL release artifact gate.
# Ordinary Windows PowerShell 5.1 OUTSIDE Claude Code. No installer, user-profile changes,
# Credential Locker, native Claude/hooks, PostgreSQL (even SELECT), real PRISM or legacy project.
$ErrorActionPreference = 'Stop'
$repo = 'C:\Projects\Vres-P2F-Postinstall-Hardening-20261022'
$review = 'C:\Projects\Vres-Review-BundleB-Artifact-20261104'
$branch = 'feature/personal-m4-integrated-synthetic-operator-dryrun-20261104'
$candidate = '2b51b3aa9e4fe40fce53ffd457e1d5f218443209'
$tree = '34072a722efe221042ddc922c5461c1a1c3192da'
$parent = 'ec54f7535aa29d7588c25e221f6bd2bae7a437c8'
$parentTree = 'd914c60169dc01c34b1cc987170cf66d66324bad'
$p2 = '82c82430b38f93bd6b9d5c3af3b5de9c1368af9c'
$p2Tree = '205c081277ece483c634e1c801c39595abd4549c'
$blobs = [ordered]@{
  'src/vres_os/release_artifact.py' = 'ddfc1beacad98199b489dc6f56456baf4d519c6a'
  'src/vres_os/release_inputs.py' = 'a0cdf3195f0cf0f2a61ce32521a74f78260832f7'
  'src/vres_os/install_recovery.py' = 'b35d559758e3b6721f43631dc499095f7895c5f3'
  'src/vres_os/personal_resume_briefing.py' = '282ee12855393e453cfecc1c3dd500ad47fc2205'
  'src/vres_os/personal_data_sources.py' = 'ad08616bf89d34c0c5f52affff30813562d7a2f7'
  'src/vres_os/global_claude_synthetic_operator.py' = '78695f60ba735eba83cea702a956ab9697922808'
}
$testModules = @(
  'tests/test_release_artifact.py',
  'tests/test_install_rollback_proof.py',
  'tests/test_personal_resume_briefing.py',
  'tests/test_personal_session_resume_ambiguity.py',
  'tests/test_personal_data_sources.py'
)
function GitRead {
  param([string]$Root,[string[]]$Argv)
  $lines = & git -C $Root -c core.hooksPath=NUL -c core.fsmonitor=false @Argv
  if ($LASTEXITCODE -ne 0) { throw ('Git refused: ' + ($Argv -join ' ')) }
  return $lines
}
function Exact {
  param([string]$Label,[string]$Observed,[string]$Expected)
  if ($Observed -cne $Expected) { throw ('MISMATCH ' + $Label + '. STOP') }
  Write-Host ('PASS: ' + $Label)
}
Write-Host '=== BUNDLE B DISPOSABLE ARTIFACT GIT PREFLIGHT ==='
if (-not (Test-Path -LiteralPath $repo -PathType Container)) { throw 'Original protected P2 checkout missing' }
if (Test-Path -LiteralPath $review) { throw 'Dedicated review path exists; preserve it and STOP' }
if (-not (Test-Path -LiteralPath (Split-Path -Parent $review) -PathType Container)) { throw 'Review checkout parent absent' }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'git unavailable' }
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw 'Python launcher unavailable' }
$pyExe = (Get-Command py).Source
$origin = [string](GitRead $repo @('remote','get-url','origin'))
if ($origin -cnotin @('https://github.com/vosser24/Vres-OS.git','https://github.com/vosser24/Vres-OS')) {
  throw 'Unexpected GitHub origin. STOP'
}
Exact 'protected P2 HEAD' ([string](GitRead $repo @('rev-parse','HEAD'))) $p2
Exact 'protected P2 TREE' ([string](GitRead $repo @('rev-parse','HEAD^{tree}'))) $p2Tree
if (@(GitRead $repo @('status','--porcelain')).Count -ne 0) { throw 'Original protected P2 is not clean' }
Write-Host 'PASS: original protected P2 clean'
GitRead $repo @('fetch','--no-tags','--no-recurse-submodules','origin',('refs/heads/' + $branch)) | Out-Null
Exact 'fetched source HEAD' ([string](GitRead $repo @('rev-parse','FETCH_HEAD'))) $candidate
Exact 'source TREE' ([string](GitRead $repo @('rev-parse',($candidate + '^{tree}')))) $tree
Exact 'source SOLE parent' ([string](GitRead $repo @('rev-list','--parents','-n','1',$candidate))) ($candidate + ' ' + $parent)
Exact 'accepted M4 parent TREE' ([string](GitRead $repo @('rev-parse',($parent + '^{tree}')))) $parentTree
foreach ($entry in $blobs.GetEnumerator()) {
  Exact ('PRE Git blob ' + $entry.Key) ([string](GitRead $repo @('rev-parse',($candidate + ':' + $entry.Key)))) $entry.Value
}
GitRead $repo @('worktree','add','--detach',$review,$candidate) | Out-Null
Exact 'detached review HEAD' ([string](GitRead $review @('rev-parse','HEAD'))) $candidate
Exact 'detached review TREE' ([string](GitRead $review @('rev-parse','HEAD^{tree}'))) $tree
if (@(GitRead $review @('status','--porcelain')).Count -ne 0) { throw 'New detached source checkout not clean' }
Write-Host 'PASS: exact protected source review ready'

$temp = Join-Path ([IO.Path]::GetTempPath()) ('vres-bundle-b-artifact-' + [guid]::NewGuid().ToString('N'))
if (Test-Path -LiteralPath $temp) { throw 'Disposal TEMP collision' }
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
$counter = 0
function RunPython {
  param([string]$Step,[string[]]$Argv,[int]$ExpectedExit=0)
  $script:counter += 1
  $stem = ('{0:D2}-{1}' -f $script:counter,$Step)
  $stdout = Join-Path $temp ($stem + '.stdout.txt')
  $stderr = Join-Path $temp ($stem + '.stderr.txt')
  $settings = @{
    FilePath = $pyExe
    ArgumentList = $Argv
    WorkingDirectory = $review
    NoNewWindow = $true
    Wait = $true
    PassThru = $true
    RedirectStandardOutput = $stdout
    RedirectStandardError = $stderr
  }
  $process = Start-Process @settings
  Write-Host ('STEP=' + $Step + '; EXIT_CODE=' + $process.ExitCode)
  Get-Content -LiteralPath $stdout | ForEach-Object { Write-Host $_ }
  if ($process.ExitCode -ne $ExpectedExit) {
    Get-Content -LiteralPath $stderr | Select-Object -Last 75 | ForEach-Object { Write-Host $_ }
    throw ('Offline Python failed expected exit: ' + $Step)
  }
  if ($ExpectedExit -ne 0) {
    Write-Host ('PASS: expected disposable refusal ' + $Step)
  } elseif ((Get-Item -LiteralPath $stderr).Length -gt 0) {
    Write-Host ('NOTE: stderr captured for ' + $Step + ', review CAPTURE_DIRECTORY')
  }
  return $stdout
}
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

  $tool = Join-Path $review 'src\vres_os\release_artifact.py'
  $inputs = Join-Path $review 'src\vres_os\release_inputs.py'
  $staged = Join-Path $temp 'staged-source'
  $manifestPath = Join-Path $temp 'release-manifest.json'
  Write-Host '=== BUNDLE B PINNED RELEASE INPUTS AND DISPOSABLE ARTIFACT ==='
  RunPython 'inputs' @('-3.12','-I','-X','utf8',$inputs,'--root',$review) | Out-Null
  RunPython 'source_check' @('-3.12','-I','-X','utf8',$tool,'check','--root',$review,'--source-commit',$candidate) | Out-Null
  RunPython 'stage' @('-3.12','-I','-X','utf8',$tool,'stage','--root',$review,'--out',$staged,'--manifest',$manifestPath,'--source-commit',$candidate) | Out-Null
  if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw 'Disposable release manifest missing' }
  $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
  Exact 'manifest source HEAD' ([string]$manifest.source_commit) $candidate
  Exact 'manifest source TREE' ([string]$manifest.source_tree) $tree
  Exact 'manifest Git object origin' ([string]$manifest.source_origin) 'git-objects'
  if ([int]$manifest.version -ne 2 -or $manifest.format -cne 'vres-personal-release-artifact') {
    throw 'Unexpected artifact manifest format/version'
  }
  $paths = @($manifest.files | ForEach-Object { [string]$_.path })
  foreach ($entry in $blobs.GetEnumerator()) {
    $found = @($manifest.files | Where-Object { $_.path -ceq $entry.Key })
    if ($found.Count -ne 1) { throw ('Missing or duplicate staged path: ' + $entry.Key) }
    Exact ('manifest Git blob ' + $entry.Key) ([string]$found[0].git_blob) $entry.Value
  }
  $migrations = @($paths | Where-Object { $_ -match '^src/vres_os/migrations/[0-9]{3}_.*\.sql$' })
  if ($migrations.Count -ne 41) { throw ('Expected exactly 41 pinned migrations, saw ' + $migrations.Count) }
  if ($paths -contains 'install.ps1' -or @($paths | Where-Object { $_ -like 'tests/*' -or $_ -like 'docs/*' }).Count -gt 0) {
    throw 'Unexpected executable installer/tests/docs inside staged release scope'
  }
  Write-Host ('PASS: exact source-to-artifact manifest, 41 pinned migrations, FILES=' + $paths.Count)
  RunPython 'plugin_verify' @('-3.12','-I','-X','utf8',$tool,'verify-tree','--manifest',$manifestPath,'--prefix','plugins/vres-os','--dir',(Join-Path $staged 'plugins\vres-os')) | Out-Null

  $site = Join-Path $temp 'site-packages'
  New-Item -ItemType Directory -Path $site -ErrorAction Stop | Out-Null
  Copy-Item -LiteralPath (Join-Path $staged 'src\vres_os') -Destination $site -Recurse -ErrorAction Stop
  $package = Join-Path $site 'vres_os'
  RunPython 'package_verify' @('-3.12','-I','-X','utf8',$tool,'verify-installed','--manifest',$manifestPath,'--package-dir',$package) | Out-Null

  # Tamper ONLY this fresh disposable package copy. Real installed package untouched.
  Add-Content -LiteralPath (Join-Path $package 'global_claude_synthetic_operator.py') -Value '# disposable tamper trial' -ErrorAction Stop
  RunPython 'tampered_package_refused' @('-3.12','-I','-X','utf8',$tool,'verify-installed','--manifest',$manifestPath,'--package-dir',$package) 1 | Out-Null

  Write-Host '=== BUNDLE B FOCUSED OFFLINE SOURCE REGRESSION ==='
  $testOutput = RunPython 'selected_pytest' (@('-3.12','-B','-m','pytest','-q','-rA','-p','no:cacheprovider') + $testModules)
  $lines = @(Get-Content -LiteralPath $testOutput)
  $passed = @($lines | Where-Object { $_ -match '^PASSED tests/' })
  $unique = @($passed | Sort-Object -Unique)
  $bad = @($lines | Where-Object { $_ -match '^(FAILED|ERROR|XPASS) tests/' })
  $skips = @($lines | Where-Object { $_ -match '^(SKIPPED|XFAIL) ' })
  Write-Host ('NAMED_PASSED_CASES=' + $passed.Count)
  Write-Host ('UNIQUE_PASSED_CASES=' + $unique.Count)
  Write-Host ('NAMED_FAILED_ERROR_XPASS=' + $bad.Count)
  Write-Host ('NAMED_SKIPPED_XFAIL_CASES=' + $skips.Count)
  foreach ($module in $testModules) {
    $n = @($passed | Where-Object { $_ -like ('PASSED ' + $module + '::*') }).Count
    Write-Host ('PASSED_MODULE=' + $module + ' COUNT=' + $n)
    if ($n -eq 0) { throw ('No passing case in required module: ' + $module) }
  }
  if ($passed.Count -ne $unique.Count -or $bad.Count -ne 0) {
    throw 'Duplicate named PASS or failure in focused source regressions'
  }
  $passed | ForEach-Object { Write-Host $_ }
  $skips | ForEach-Object { Write-Host $_ }
  Write-Host 'PASS: BUNDLE_B_DISPOSABLE_ARTIFACT_AND_SELECTED_SOURCE_OFFLINE_PENDING_EVALUATION'
  if ($skips.Count -gt 0) { Write-Host 'SKIPS_REQUIRE_EXPLICIT_REVIEW_NOT_AUTOMATIC_ACCEPTANCE' }
} finally {
  foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$prior[$name],'Process') }
  $unrestored = @($names | Where-Object {
    [Environment]::GetEnvironmentVariable($_,'Process') -cne $prior[$_]
  })
  if ($unrestored.Count -gt 0) { throw ('Environment restoration mismatch: ' + ($unrestored -join ', ')) }
  Write-Host 'PASS: PROCESS_ENVIRONMENT_RESTORED_AND_VERIFIED'
}
Write-Host '=== BUNDLE B SOURCE GIT POSTFLIGHT ==='
Exact 'POST review HEAD' ([string](GitRead $review @('rev-parse','HEAD'))) $candidate
Exact 'POST review TREE' ([string](GitRead $review @('rev-parse','HEAD^{tree}'))) $tree
foreach ($entry in $blobs.GetEnumerator()) {
  Exact ('POST Git blob ' + $entry.Key) ([string](GitRead $review @('rev-parse',('HEAD:' + $entry.Key)))) $entry.Value
}
if (@(GitRead $review @('status','--porcelain')).Count -ne 0) { throw 'Protected review checkout changed' }
Exact 'POST original P2 HEAD' ([string](GitRead $repo @('rev-parse','HEAD'))) $p2
Exact 'POST original P2 TREE' ([string](GitRead $repo @('rev-parse','HEAD^{tree}'))) $p2Tree
if (@(GitRead $repo @('status','--porcelain')).Count -ne 0) { throw 'Original P2 checkout changed' }
Write-Host 'PASS: original P2 and Bundle B review checkouts clean'
Write-Host ('CAPTURE_DIRECTORY=' + $temp)
Write-Host 'VRES_BUNDLE_B_DISPOSABLE_ARTIFACT_POSTFLIGHT_COMPLETE_PENDING_EVALUATION'
Write-Host 'No actual installer, installed Vres, native Claude, current-user credentials/PRISM or PostgreSQL authorized.'
