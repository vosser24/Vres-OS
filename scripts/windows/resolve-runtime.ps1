Set-StrictMode -Version Latest
function Resolve-VresPython {
    # Direct callers of this original shared helper must not inspect installed
    # release pointers or resolve/launch Python while the W4 hold is open.
    $W4RuntimeResolveInterlock = 'HELD_NO_INSTALLED_POINTER_OR_PYTHON_RESOLUTION'
    if ($W4RuntimeResolveInterlock -cne 'INDEPENDENT_RUNTIME_REVIEW_AND_OWNER_AUTHORIZED') {
        throw 'VRES_W4_HELD_RUNTIME_RESOLVER: installed P2 pointer and Python resolution are blocked.'
    }
    $root = Join-Path $env:LOCALAPPDATA 'VresOS'
    $pointer = Join-Path $root 'active-install.json'
    if (-not (Test-Path -LiteralPath $pointer -PathType Leaf)) { throw 'Vres runtime is not installed. Run install.ps1.' }
    $state = Get-Content -Raw -Encoding UTF8 -LiteralPath $pointer | ConvertFrom-Json
    if ($state.product -ne 'Vres-OS' -or $state.release -notmatch '^\d{14}-[a-f0-9]{8}$') { throw 'Invalid Vres installation pointer.' }
    $python = Join-Path $root ("releases\{0}\venv\Scripts\python.exe" -f $state.release)
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Selected Vres runtime is missing. Inspect installation recovery documentation.' }
    return $python
}
