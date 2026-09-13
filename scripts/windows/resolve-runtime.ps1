Set-StrictMode -Version Latest
function Resolve-VresPython {
    $root = Join-Path $env:LOCALAPPDATA 'VresOS'
    $pointer = Join-Path $root 'active-install.json'
    if (-not (Test-Path -LiteralPath $pointer -PathType Leaf)) { throw 'Vres runtime is not installed. Run install.ps1.' }
    $state = Get-Content -Raw -Encoding UTF8 -LiteralPath $pointer | ConvertFrom-Json
    if ($state.product -ne 'Vres-OS' -or $state.release -notmatch '^\d{14}-[a-f0-9]{8}$') { throw 'Invalid Vres installation pointer.' }
    $python = Join-Path $root ("releases\{0}\venv\Scripts\python.exe" -f $state.release)
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Selected Vres runtime is missing. Inspect installation recovery documentation.' }
    return $python
}
