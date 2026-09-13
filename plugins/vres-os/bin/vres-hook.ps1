param([Parameter(Mandatory=$true)][string]$Event)
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:LOCALAPPDATA 'VresOS'
try {
    . (Join-Path $root 'bin\resolve-runtime.ps1')
    $python = Resolve-VresPython
    $env:PYTHONUTF8 = '1'
    $OutputEncoding = New-Object System.Text.UTF8Encoding $false
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding $false
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false
    # Bound input before handing it to Python. No ReadToEnd on untrusted event payloads.
    $buffer = New-Object char[] (1048577)
    $length = 0
    while ($length -lt $buffer.Length) {
        $n = [Console]::In.Read($buffer, $length, $buffer.Length - $length)
        if ($n -eq 0) { break }
        $length += $n
    }
    if ($length -gt 1048576) { throw 'Hook payload exceeds one MiB of characters.' }
    $payload = [string]::new($buffer, 0, $length)
    $payload | & $python -I -X utf8 -m vres_os.cli hook $Event
    exit $LASTEXITCODE
} catch {
    # Do not log the raw payload, credentials, command arguments or exception text.
    $logDir = Join-Path $root 'logs'
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    "$(Get-Date -Format o) event=$Event hook-launch-failed; inspect installation" | Add-Content -LiteralPath (Join-Path $logDir 'hook-errors.log') -Encoding UTF8
    if ($Event -eq 'validator-stop') { exit 2 }
    Write-Output '{"systemMessage":"Vres continuity hook failed; persistence is not confirmed. Run vres doctor in a terminal."}'
    exit 0
}
