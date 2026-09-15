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

    # Resolve the immutable active runtime directly; do not dot-source the general resolver
    # or perform process inspection inside Claude Code's SessionEnd budget.
    $activePath = Join-Path $root 'active-install.json'
    $active = Get-Content -Raw -Encoding UTF8 -LiteralPath $activePath | ConvertFrom-Json
    $release = [string]$active.release
    if ($release -notmatch '^\d{14}-[a-f0-9]{8}$') { throw 'Invalid active release id.' }
    $pythonw = Join-Path $root "releases\$release\venv\Scripts\pythonw.exe"
    if (-not (Test-Path -LiteralPath $pythonw)) { throw 'Active pythonw runtime is missing.' }

    $env:VRES_SESSION_END_ID = $sid
    $env:VRES_SESSION_END_CWD = $cwd
    $env:VRES_SESSION_END_REASON = $reason

    $proc = Start-Process -FilePath $pythonw -ArgumentList @(
        '-I', '-X', 'utf8', '-m', 'vres_os.session_end_worker'
    ) -WindowStyle Hidden -PassThru

    Write-Lifecycle 'detached-launched' "worker_pid=$($proc.Id)"
    exit 0
} catch {
    # Never log the raw SessionEnd payload or exception text.
    Write-Lifecycle 'launch-failed' "error_type=$($_.Exception.GetType().Name)"
    exit 0
}
