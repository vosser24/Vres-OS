# Source-only P0 hold: native Claude Code/hook execution remains forbidden.
throw 'VRES_W4_HELD_HOST_HOOK: HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED is OPEN; no installed runtime, Python, MCP, hook or child process was started.'
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:LOCALAPPDATA 'VresOS'
$logDir = Join-Path $root 'logs'

function Write-Lifecycle([string]$Phase, [string]$Extra = '') {
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $line = "$(Get-Date -Format o) event=session-end phase=$Phase"
    if ($Extra) { $line += " $Extra" }
    $line | Add-Content -LiteralPath (Join-Path $logDir 'lifecycle.log') -Encoding UTF8
}

try {
    # This marker is intentionally first: SessionEnd has a very small host teardown budget.
    Write-Lifecycle 'launch-start'

    # Bound the hook payload before parsing it. SessionEnd only needs three non-secret fields.
    $buffer = New-Object char[] (262145)
    $length = 0
    while ($length -lt $buffer.Length) {
        $n = [Console]::In.Read($buffer, $length, $buffer.Length - $length)
        if ($n -eq 0) { break }
        $length += $n
    }
    if ($length -gt 262144) { throw 'SessionEnd payload exceeds bounded size.' }
    $raw = [string]::new($buffer, 0, $length)
    $payload = $raw | ConvertFrom-Json

    $sid = [string]$payload.session_id
    $cwd = [string]$payload.cwd
    $reason = [string]$payload.reason
    if ([string]::IsNullOrWhiteSpace($sid) -or $sid.Length -gt 200) { throw 'Invalid session id.' }
    if ([string]::IsNullOrWhiteSpace($cwd) -or $cwd.Length -gt 4096) { throw 'Invalid cwd.' }
    if ($reason.Length -gt 200) { throw 'Invalid SessionEnd reason.' }
    if ([string]::IsNullOrWhiteSpace($reason)) { $reason = 'session_end' }

    # R13P: resolve through the ORIGINAL shared source-held runtime resolver.
    # Its pending-journal/exclusive-lock check occurs before reading the pointer
    # or starting a detached worker. Do not bypass it for SessionEnd.
    # No CIM/process walk is added to the host teardown budget.
    . (Join-Path $root 'bin\resolve-runtime.ps1')
    $python = Resolve-VresPython

    $env:VRES_SESSION_END_ID = $sid
    $env:VRES_SESSION_END_CWD = $cwd
    $env:VRES_SESSION_END_REASON = $reason

    $proc = Start-Process -FilePath $python -ArgumentList @(
        '-I', '-X', 'utf8', '-m', 'vres_os.session_end_worker'
    ) -WindowStyle Hidden -PassThru

    Write-Lifecycle 'detached-launched' "worker_pid=$($proc.Id)"
    exit 0
} catch {
    # Never log the raw SessionEnd payload or exception text.
    Write-Lifecycle 'launch-failed' "error_type=$($_.Exception.GetType().Name)"
    exit 0
}
