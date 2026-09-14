#requires -Version 5.1
[CmdletBinding()]
param([switch]$WithEmbeddings, [switch]$WithCodex, [switch]$UseRemotePostgres)
$ErrorActionPreference='Stop'
if (-not (Test-Path (Join-Path $env:LOCALAPPDATA 'VresOS\active-install.json'))) { throw 'Run install.ps1 first.' }
# Same staging/validation/rollback path as installation; no second implementation.
& (Join-Path $PSScriptRoot 'install.ps1') -Update -WithEmbeddings:$WithEmbeddings -WithCodex:$WithCodex -UseRemotePostgres:$UseRemotePostgres
