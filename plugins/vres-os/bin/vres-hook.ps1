param([Parameter(Mandatory=$true)][string]$Event)
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:LOCALAPPDATA 'VresOS'
$logDir = Join-Path $root 'logs'

# SessionEnd has a very small synchronous host budget. Record invocation before
# runtime discovery or process inspection so timeout diagnosis remains possible.
# The SessionEnd hook itself is configured async; this early marker is still kept
# to distinguish "Claude did not invoke the hook" from later launcher/runtime failure.
if ($Event -eq 'session-end') {
    try {
        New-Item -ItemType Directory -Force -Path $logDir | Out-Null
        "$(Get-Date -Format o) event=session-end phase=launch-start host_pid=stored-session-metadata" |
            Add-Content -LiteralPath (Join-Path $logDir 'lifecycle.log') -Encoding UTF8
    } catch {
        # Continue into the normal guarded path; hook-errors.log will capture a bounded failure marker.
    }
}

try {
    . (Join-Path $root 'bin\resolve-runtime.ps1')
    $python = Resolve-VresPython
    $env:PYTHONUTF8 = '1'
    $OutputEncoding = New-Object System.Text.UTF8Encoding $false
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding $false
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false

    # Best-effort host identity is useful while the Claude process is running.
    # SessionEnd deliberately skips the CIM walk: its session row already contains
    # host_pid from earlier lifecycle events, and exit cleanup must stay lightweight.
    Remove-Item Env:VRES_HOST_PID -ErrorAction SilentlyContinue
    if ($Event -ne 'session-end') {
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
