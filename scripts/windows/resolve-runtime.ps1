Set-StrictMode -Version Latest
function Assert-VresInstallTransactionQuiescent([string]$Root) {
    # R13O: local concurrency barrier, NOT authenticated SQL or host evidence.
    $journal = Join-Path $Root 'pending-install.json'
    if (Test-Path -LiteralPath $journal) {
        throw 'VRES_W4_INSTALL_TRANSACTION_PENDING: preserve the interrupted installation journal; no original runtime may launch.'
    }
    $lockPath = Join-Path $Root 'installation.lock'
    if (Test-Path -LiteralPath $lockPath) {
        $probe = $null
        try {
            # The original installer holds FileShare.None. Existing read handles
            # and this probe prevent simultaneous exclusive installer use.
            $probe = [IO.File]::Open($lockPath, 'Open', 'Read', 'ReadWrite')
        } catch {
            throw 'VRES_W4_INSTALL_TRANSACTION_BUSY: installer lock cannot be shared; original runtime launch refused.'
        } finally {
            if ($null -ne $probe) { $probe.Dispose() }
        }
    } elseif (Test-Path -LiteralPath (Join-Path $Root 'active-install.json')) {
        throw 'VRES_W4_INSTALL_TRANSACTION_UNVERIFIED: an installed release lacks its expected installer lock.'
    }
    # Close a journal-created-during-probe race; the Python DB barrier holds
    # an actual reader handle throughout every approved connection.
    if (Test-Path -LiteralPath $journal) {
        throw 'VRES_W4_INSTALL_TRANSACTION_PENDING: installation journal appeared; launch refused.'
    }
}
function Resolve-VresPython {
    # Direct callers of this original shared helper must not inspect installed
    # release pointers or resolve/launch Python while the W4 hold is open.
    $W4RuntimeResolveInterlock = 'HELD_NO_INSTALLED_POINTER_OR_PYTHON_RESOLUTION'
    if ($W4RuntimeResolveInterlock -cne 'INDEPENDENT_RUNTIME_REVIEW_AND_OWNER_AUTHORIZED') {
        throw 'VRES_W4_HELD_RUNTIME_RESOLVER: installed P2 pointer and Python resolution are blocked.'
    }
    $root = Join-Path $env:LOCALAPPDATA 'VresOS'
    Assert-VresInstallTransactionQuiescent $root
    $pointer = Join-Path $root 'active-install.json'
    if (-not (Test-Path -LiteralPath $pointer -PathType Leaf)) { throw 'Vres runtime is not installed. Run install.ps1.' }
    $state = Get-Content -Raw -Encoding UTF8 -LiteralPath $pointer | ConvertFrom-Json
    if ($state.product -ne 'Vres-OS' -or $state.release -notmatch '^\d{14}-[a-f0-9]{8}$') { throw 'Invalid Vres installation pointer.' }
    $python = Join-Path $root ("releases\{0}\venv\Scripts\python.exe" -f $state.release)
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Selected Vres runtime is missing. Inspect installation recovery documentation.' }
    return $python
}
