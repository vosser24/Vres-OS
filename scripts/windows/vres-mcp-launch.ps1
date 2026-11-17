$ErrorActionPreference = 'Stop'
# Source-owned hold: refuse BEFORE active-install.json, Python, Tk, DB, hooks.
$W4HostLaunchInterlock = 'HELD_SOURCE_ONLY'
if ($W4HostLaunchInterlock -cne 'INDEPENDENT_REVIEW_AND_OWNER_AUTHORIZED') {
    throw 'VRES_W4_HELD: original managed launcher disabled; installed P2 untouched.'
}
. (Join-Path $PSScriptRoot 'resolve-runtime.ps1')
$env:PYTHONUTF8 = '1'
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
$python = Resolve-VresPython
& $python -I -X utf8 -m vres_os.mcp_server
exit $LASTEXITCODE
