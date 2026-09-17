$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'resolve-runtime.ps1')
$env:PYTHONUTF8 = '1'
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
$python = Resolve-VresPython
# This wrapper is invoked by vres.cmd via `powershell.exe -File ... %*`.
# Do not declare script parameters here: Windows PowerShell 5.1 may try to
# bind forwarded subcommands/options (for example `secret run --env ...`)
# before Python/Typer sees them. Native unbound `$args` preserves the CLI tail
# as argv, including multi-token subcommands and the `--` child-command separator.
& $python -I -X utf8 -m vres_os.cli @args
exit $LASTEXITCODE
