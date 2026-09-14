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

    # Best-effort host identity: walk a short parent chain and record only a Claude PID.
    # If Claude cannot be proven, leave VRES_HOST_PID unset; Python recovery will not guess.
    Remove-Item Env:VRES_HOST_PID -ErrorAction SilentlyContinue
    try {
        $candidate = [int]$PID
        for ($i = 0; $i -lt 8 -and $candidate -gt 0; $i++) {
            $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $candidate" -ErrorAction Stop
            if ($proc.Name -ieq 'claude.exe' -or $proc.Name -ieq 'claude') {
                $env:VRES_HOST_PID = [string]$candidate
                break
            }
            $candidate = [int]$proc.ParentProcessId
        }
    } catch {
        Remove-Item Env:VRES_HOST_PID -ErrorAction SilentlyContinue
    }

    $logDir = Join-Path $root 'logs'
    if ($Event -eq 'session-end') {
        New-Item -ItemType Directory -Force -Path $logDir | Out-Null
        $hostText = if ($env:VRES_HOST_PID) { $env:VRES_HOST_PID } else { 'unknown' }
        "$(Get-Date -Format o) event=session-end phase=launch-start host_pid=$hostText" |
            Add-Content -LiteralPath (Join-Path $logDir 'lifecycle.log') -Encoding UTF8
    }

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
    $code = $LASTEXITCODE
    if ($Event -eq 'session-end') {
        "$(Get-Date -Format o) event=session-end phase=launch-finish exit_code=$code" |
            Add-Content -LiteralPath (Join-Path $logDir 'lifecycle.log') -Encoding UTF8
    }
    exit $code
} catch {
    # Do not log the raw payload, credentials, command arguments or exception text.
    $logDir = Join-Path $root 'logs'
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    "$(Get-Date -Format o) event=$Event hook-launch-failed; inspect installation" | Add-Content -LiteralPath (Join-Path $logDir 'hook-errors.log') -Encoding UTF8
    if ($Event -eq 'session-end') {
        "$(Get-Date -Format o) event=session-end phase=launch-failed" |
            Add-Content -LiteralPath (Join-Path $logDir 'lifecycle.log') -Encoding UTF8
    }
    if ($Event -eq 'validator-stop') { exit 2 }
    Write-Output '{"systemMessage":"Vres continuity hook failed; persistence is not confirmed. Run vres doctor in a terminal."}'
    exit 0
}
