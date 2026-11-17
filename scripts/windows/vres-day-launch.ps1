#requires -Version 5.1
# Original Vres-OS managed release resolution; no second application.
# The existing Python entry intentionally refuses before importing Tk.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'resolve-runtime.ps1')
$env:PYTHONUTF8 = '1'
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
$python = Resolve-VresPython
& $python -I -B -X utf8 -m vres_os.personal_w4_windows_entry @args
exit $LASTEXITCODE
