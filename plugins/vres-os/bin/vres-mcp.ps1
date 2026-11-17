# Source-only P0 hold: native Claude Code/hook execution remains forbidden.
throw 'VRES_W4_HELD_HOST_HOOK: HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED is OPEN; no installed runtime, Python, MCP, hook or child process was started.'
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:LOCALAPPDATA 'VresOS'
. (Join-Path $root 'bin\resolve-runtime.ps1')
$env:PYTHONUTF8 = '1'
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
$python = Resolve-VresPython
& $python -I -X utf8 -m vres_os.mcp_entrypoint
exit $LASTEXITCODE
