#requires -Version 5.1
[CmdletBinding()]
param([switch]$RemoveLocalData)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root=Join-Path $env:LOCALAPPDATA 'VresOS'
$pointer=Join-Path $root 'active-install.json'
if (-not (Test-Path $pointer)) { throw 'No managed active-install.json found; refusing directory deletion.' }
if (Get-Process -Name 'claude','codex' -ErrorAction SilentlyContinue) { throw 'Close Claude and Codex first.' }
if (Test-Path (Join-Path $root 'pending-install.json')) { throw 'Resolve the interrupted installation journal before uninstalling.' }
$workers = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" -ErrorAction Stop | Where-Object {
    $_.ExecutablePath -and $_.ExecutablePath.StartsWith(($root.TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)
})
if ($workers.Count -gt 0) { throw 'A Vres worker is still running; stop that worker before uninstalling.' }

if ((Get-Item -LiteralPath $root).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Install root is a reparse point; refusing removal.' }
foreach ($name in @('releases','bin','backups','logs','runtime')) {
    $p=Join-Path $root $name
    if ((Test-Path $p) -and ((Get-Item -LiteralPath $p).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Runtime contains a reparse point; inspect before removal.' }
}
$state=Get-Content -Raw -Encoding UTF8 $pointer | ConvertFrom-Json
if ($state.product -ne 'Vres-OS' -or $state.release -notmatch '^\d{14}-[a-f0-9]{8}$') { throw 'Unrecognized installation identity.' }
$plugin=[IO.Path]::GetFullPath($state.plugin_path)
$home=if ($env:CLAUDE_CONFIG_DIR) {$env:CLAUDE_CONFIG_DIR} else {Join-Path $env:USERPROFILE '.claude'}
$expected=[IO.Path]::GetFullPath((Join-Path $home 'skills\vres-os'))
if ($plugin -ne $expected) { throw 'Unexpected plugin path. Review manually; nothing was removed.' }
if (Test-Path $plugin) {
    if (-not (Test-Path (Join-Path $plugin '.vres-managed')) -or (Get-Content -Raw -Encoding UTF8 (Join-Path $plugin '.vres-managed')).Trim() -ne 'Vres-OS') { throw 'Unmanaged plugin directory; refusing removal.' }
    if ((Get-Item $plugin).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Plugin is a reparse point; refusing removal.' }
}
$answer=Read-Host 'Remove the Vres runtime and plugin? Config/credential are preserved unless -RemoveLocalData is supplied [y/N]'
if ($answer -notin @('y','Y','yes','Yes')) { exit 0 }
$python=Join-Path $root ("releases\{0}\venv\Scripts\python.exe" -f $state.release)
& $python -I -X utf8 -m vres_os.statusline remove --claude-home $home
if ($LASTEXITCODE -ne 0) { throw 'Could not remove the Vres-managed Claude status line. Runtime retained for recovery.' }
& $python -I -X utf8 -m vres_os.claude_contract remove-global --claude-home $home
if ($LASTEXITCODE -ne 0) { throw 'Could not remove the Vres-managed global Claude contract. Runtime retained for recovery.' }
if ($RemoveLocalData) {
    & $python -I -X utf8 -c 'from vres_os.config import ConfigStore; from vres_os.secrets import SecretStore; c=ConfigStore().load(); SecretStore().delete(c.database.password_key)'
    if ($LASTEXITCODE -ne 0) { throw 'Could not remove the Vres credential. Runtime retained for recovery.' }
}
if (Test-Path $plugin) { Remove-Item -LiteralPath $plugin -Recurse -Force }
$bin=Join-Path $root 'bin'
$userPath=[Environment]::GetEnvironmentVariable('Path','User')
[Environment]::SetEnvironmentVariable('Path', (($userPath -split ';' | Where-Object {$_ -and $_ -ne $bin}) -join ';'), 'User')
foreach ($name in @('releases','bin','backups','active-install.json','pending-install.json','installation.lock')) {
    $target=Join-Path $root $name
    if (Test-Path $target) { Remove-Item -LiteralPath $target -Recurse -Force }
}
if ($RemoveLocalData) {
    foreach ($name in @('config.json','logs','runtime')) {
        $target=Join-Path $root $name
        if (Test-Path $target) { Remove-Item -LiteralPath $target -Recurse -Force }
    }
}
Write-Host 'Vres removed. PostgreSQL databases, project repositories and Claude/Codex login sessions were NOT deleted.'
