$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'resolve-runtime.ps1')
$env:PYTHONUTF8 = '1'
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
$python = Resolve-VresPython
& $python -I -X utf8 -m vres_os.mcp_server
exit $LASTEXITCODE
