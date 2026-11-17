# Source-only P0 hold: native Claude Code/hook execution remains forbidden.
throw 'VRES_W4_HELD_HOST_HOOK: HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED is OPEN; no installed runtime, Python, MCP, hook or child process was started.'
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:LOCALAPPDATA 'VresOS'
try {
    . (Join-Path $root 'bin\resolve-runtime.ps1')
    $python = Resolve-VresPython
    $env:PYTHONUTF8 = '1'
    $OutputEncoding = New-Object System.Text.UTF8Encoding $false
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding $false
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false

    $buffer = New-Object char[] (1048577)
    $length = 0
    while ($length -lt $buffer.Length) {
        $n = [Console]::In.Read($buffer, $length, $buffer.Length - $length)
        if ($n -eq 0) { break }
        $length += $n
    }
    if ($length -gt 1048576) { throw 'Hook payload exceeds one MiB of characters.' }
    $payload = [string]::new($buffer, 0, $length)
    $payload | & $python -I -X utf8 -m vres_os.host_inputs
    exit $LASTEXITCODE
} catch {
    New-Item -ItemType Directory -Force -Path (Join-Path $root 'logs') | Out-Null
    "$(Get-Date -Format o) event=ask-user-answer hook-launch-failed; inspect installation" |
        Add-Content -LiteralPath (Join-Path $root 'logs\hook-errors.log') -Encoding UTF8
    exit 0
}
