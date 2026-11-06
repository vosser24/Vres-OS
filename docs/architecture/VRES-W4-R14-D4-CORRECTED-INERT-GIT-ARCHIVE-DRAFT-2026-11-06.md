# Vres-OS W4 R14-D4 — corrected INERT Git-archive draft after second Claude.ai review

**2026-11-06, Europe/Athens. STATUS: DOCS_ONLY / DRAFT / NOT_REVIEWED_AFTER_CORRECTION / NOT_RUN / NOT_OWNER_APPROVED.** The previous [rejected original archive draft](VRES-W4-R14-D4-CLOUD-REVIEW-RECONCILIATION-AND-GIT-ARCHIVE-DRAFT-2026-11-06.md) remains intact as historical evidence. **DO NOT RUN either script.**

## Source and review provenance
Owner supplied a second read-only Claude.ai cloud-review report by the **same external AI reviewer** as the first report, not a second person, not GitHub-attested and not a live Windows test. The report's verdict is **DESIGN_REVISE**. The linked Claude artifact was `https://claude.ai/artifact/LFAmiQ5yhVTE3XoBwe5iRG`; full report was pasted/uploaded to this conversation. Claude did not reach issue #185. GitHub readback confirmed #185 OPEN, zero comments and no assigned reviewer. **Nothing in this report grants runtime, native Claude, PostgreSQL, P2, F1/Fable, or release authority.**

Second-review blockers: **S1** unguarded interactive PowerShell line-by-line paste; **S2** inherited GIT_* and global configuration plus ineffective clone-only -c flags; **S3** unpinned Git executable/signer/version. Required repairs: **S4** ordinal case-sensitive inventory/ZIP/directory collections; **S5** check exit for each Git call and require exactly one output for scalar commands; **S6** --quiet --single-branch --no-tags. Recommended: **S7** -UseBasicParsing, pinned SHA-256 inventory; **S8** byte/character exact final LF checks.

This corrected draft addresses those on paper using one `& { ... }` block, fresh `powershell.exe -NoProfile`, process GIT_* and GCM save/clear/restore, GIT_CONFIG_GLOBAL=NUL, GIT_CONFIG_NOSYSTEM=1, GIT_ALLOW_PROTOCOL=https, hardening options for EVERY Git command, exact proposed executable path with Authenticode subject/thumbprint and SHA-256 plus minimum Git 2.32 checked before user consent, ordinal-name collections, checked exit statuses, restricted no-checkout clone, pinned immutable docs inventory response and uncompressed ZIP member stream hashes. The git executable's signature alone may not cover a wrapper's child executables and DLLs, and the real trusted installed toolchain has not been inspected. No ZIP is extracted and no Vres code executed.

**THE SCRIPT BELOW WILL DELIBERATELY REFUSE BEFORE CONSENT** because signer subject, signer thumbprint, and Git executable raw SHA-256 are all `PENDING_OWNER_APPROVAL`. Never edit these to guessed values; a subsequent complete exact final version needs a new independent static review and separate owner permission. `C:\Projects` output root is also only proposed, not approved or observed. Authentication of Windows OS, Git distro, certificate lookup side effects, proxy/network routes, and residual local filesystem/TOCTOU risk remain explicitly conditional on the one-user model and further review.

Baseline P0 readback: docs parent HEAD `15ba0387fb0fc559d8daa596e59b6f6920d23a9b`, TREE `8745b4c86cc979f1d1f329fe92a7199a464b1f3e`, sole parent `9acc5774980d758aafee80be1a6ab0e38e473d44`; R13 HEAD `bcf62460d68caebfdbd0e838d44c5997992c5fbc`, TREE `9bbc5615fef4a8f785e9ddb0056e9430ffe25d63`, sole parent `0badcd34d1eafbce5f815512a489d70cb240eecd`; main HEAD `9a8acc5d464b96432a93cb95daa9581412fb07ee`. R13 proposed inert 232-file snapshot is **not** an owner-approved release. Inventory at previous pinned docs commit `15ba0387fb0fc559d8daa596e59b6f6920d23a9b`, blob `fd3e74cc135d1a8a04c75a6dcf88b8918cb18ec5`, SHA-256 `c6dab3be2ad86cf0fca2586b870665bc20ad8830c9e76e2f677f0ec8801b13c6`. Contains incident-B `hooks.json` and `.mcp.json` as inert unsafe-to-activate DATA. Original 13 owner pins: nine W3 R2 unchanged, two existing W4-modified (release_artifact.py, release_inputs.py), two W4-created. release_artifact.py W3→R13 change **+108/-26** (134 changed lines), not +134/-26.

## Corrected proposed PowerShell — DO NOT EXECUTE

The full block is included only for a new independent cloud-based source review. No PowerShell parser, ZIP creation, or Windows NTFS test has been executed. Any flaw found must produce a new reviewed proposal, not an operator workaround.

~~~powershell
& {
    # DESIGN DRAFT ONLY: DO NOT EXECUTE. The Git pins below are NOT approved.
    # Intended for ONE full paste into a NEW powershell.exe -NoProfile session,
    # NOT Claude Code, PowerShell ISE, or an installed Vres launcher.
    $ErrorActionPreference = 'Stop'
    Set-StrictMode -Version Latest
    $Commit = 'bcf62460d68caebfdbd0e838d44c5997992c5fbc'
    $Tree = '9bbc5615fef4a8f785e9ddb0056e9430ffe25d63'
    $Parent = '0badcd34d1eafbce5f815512a489d70cb240eecd'
    $Branch = 'feature/personal-w4-r13-universal-staging-hold-20261106'
    $InventoryHash = 'c6dab3be2ad86cf0fca2586b870665bc20ad8830c9e76e2f677f0ec8801b13c6'
    $InventoryUrl = 'https://api.github.com/repos/vosser24/Vres-OS/contents/docs/handoffs/VRES-W4-R13-CLAUDE-CLOUD-REVIEWER-SHA256-INVENTORY-2026-11-06.txt?ref=15ba0387fb0fc559d8daa596e59b6f6920d23a9b'
    $RepoUrl = 'https://github.com/vosser24/Vres-OS.git'
    $ApprovedParent = 'C:\Projects'
    $Root = Join-Path $ApprovedParent 'Vres-W4-R13-InertGitArchive-bcf62460'
    $Repo = Join-Path $Root 'unexecuted-git-objects'
    $ZipPath = Join-Path $Root 'source-only.zip'
    $GitExe = 'C:\Program Files\Git\cmd\git.exe'
    # Must remain deliberately unapproved until a distinct owner decision.
    # Changing these exact placeholders creates a NEW script needing review.
    $ApprovedSignerSubject = 'PENDING_OWNER_APPROVAL'
    $ApprovedSignerThumbprint = 'PENDING_OWNER_APPROVAL'
    $ApprovedExeSha256 = 'PENDING_OWNER_APPROVAL'

    $GitHardening = @(
        '-c','core.autocrlf=false',
        '-c','core.eol=lf',
        '-c','core.attributesFile=NUL',
        '-c','core.fsmonitor=false',
        '-c','core.hooksPath=NUL',
        '-c','init.templateDir=NUL',
        '-c','credential.helper='
    )
    $Scope = @(
        'src/vres_os','plugins/vres-os','scripts/windows',
        'pyproject.toml','README.md','LICENSE','rules/vres-rules.md'
    )
    function Invoke-SafeGit {
        param([string[]]$GitArguments,[switch]$SingleLine)
        $output = @(& $GitExe @GitHardening @GitArguments)
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0) { throw ('Git refused (exit ' + $exitCode + '). STOP.') }
        if ($SingleLine) {
            if ($output.Count -ne 1 -or
                [string]::IsNullOrWhiteSpace([string]$output[0])) {
                throw 'Expected exactly one nonempty Git output line.'
            }
            return ([string]$output[0]).Trim()
        }
        return $output
    }
    function Get-HexSha256 {
        param([byte[]]$Bytes)
        $sha = [Security.Cryptography.SHA256]::Create()
        try { return [BitConverter]::ToString($sha.ComputeHash($Bytes)).Replace('-','').ToLowerInvariant() }
        finally { $sha.Dispose() }
    }

    # Save every inherited GIT_* variable, not just selected names.
    $oldGit = [System.Collections.Generic.Dictionary[string,string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    foreach ($envItem in @(Get-ChildItem Env: | Where-Object { $_.Name -like 'GIT_*' })) {
        $oldGit.Add($envItem.Name,$envItem.Value)
    }
    $oldGcm = [Environment]::GetEnvironmentVariable('GCM_INTERACTIVE','Process')
    try {
        foreach ($key in @($oldGit.Keys)) {
            [Environment]::SetEnvironmentVariable($key,$null,'Process')
        }
        [Environment]::SetEnvironmentVariable('GIT_CONFIG_NOSYSTEM','1','Process')
        [Environment]::SetEnvironmentVariable('GIT_CONFIG_GLOBAL','NUL','Process')
        [Environment]::SetEnvironmentVariable('GIT_TERMINAL_PROMPT','0','Process')
        [Environment]::SetEnvironmentVariable('GIT_ALLOW_PROTOCOL','https','Process')
        [Environment]::SetEnvironmentVariable('GCM_INTERACTIVE','never','Process')

        # Git identity checks BEFORE asking for consent.
        $gitFile = Get-Item -LiteralPath $GitExe -ErrorAction Stop
        if ($gitFile.PSIsContainer -or
            (($gitFile.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) {
            throw 'Proposed Git executable is not an ordinary file.'
        }
        $sig = Get-AuthenticodeSignature -LiteralPath $GitExe
        if ($sig.Status -ne 'Valid' -or $null -eq $sig.SignerCertificate) {
            throw 'Git executable does not have an acceptable valid signature.'
        }
        $subject = [string]$sig.SignerCertificate.Subject
        $thumbprint = ([string]$sig.SignerCertificate.Thumbprint).ToUpperInvariant()
        $binaryHash = (Get-FileHash -LiteralPath $GitExe -Algorithm SHA256).Hash.ToLowerInvariant()
        $gitVersion = Invoke-SafeGit -GitArguments @('--version') -SingleLine
        $ver = [regex]::Match($gitVersion,'^git version ([0-9]+)\.([0-9]+)\.')
        if (-not $ver.Success -or [int]$ver.Groups[1].Value -lt 2 -or
            ([int]$ver.Groups[1].Value -eq 2 -and [int]$ver.Groups[2].Value -lt 32)) {
            throw 'Git 2.32+ is required.'
        }
        Write-Output ('PROPOSED_GIT_EXE=' + $GitExe)
        Write-Output ('PROPOSED_GIT_VERSION=' + $gitVersion)
        Write-Output ('GIT_SIGNER_SUBJECT=' + $subject)
        Write-Output ('GIT_SIGNER_THUMBPRINT=' + $thumbprint)
        Write-Output ('GIT_EXE_SHA256=' + $binaryHash)
        if ($ApprovedSignerSubject -eq 'PENDING_OWNER_APPROVAL' -or
            $ApprovedSignerThumbprint -eq 'PENDING_OWNER_APPROVAL' -or
            $ApprovedExeSha256 -eq 'PENDING_OWNER_APPROVAL') {
            throw 'Owner has NOT approved Git path/signer/exe hash. DRAFT MUST STOP.'
        }
        if ($subject -cne $ApprovedSignerSubject -or
            $thumbprint -cne $ApprovedSignerThumbprint.ToUpperInvariant() -or
            $binaryHash -cne $ApprovedExeSha256.ToLowerInvariant()) {
            throw 'Git identity not equal to separately approved signer and bytes.'
        }

        $answer = Read-Host 'Type exact separately authorized source-only action (or blank to STOP)'
        if ($answer -cne 'AUTHORIZE-W4R13-INERT-GIT-ARCHIVE-ONLY') {
            throw 'No explicit source-only archive approval. STOP.'
        }
        $parentInfo = Get-Item -LiteralPath $ApprovedParent -ErrorAction Stop
        if (-not $parentInfo.PSIsContainer -or
            (($parentInfo.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) -or
            (Test-Path -LiteralPath $Root)) {
            throw 'Unapproved existing/reparse root or output collision. STOP.'
        }

        # Independent reviewer inventory pinned to an immutable DOCS commit.
        $data = Invoke-RestMethod -Method Get -UseBasicParsing -Uri $InventoryUrl -Headers @{'User-Agent'='Vres-W4-Personal-ReadOnly'} -ErrorAction Stop
        if ($data.encoding -cne 'base64' -or [string]::IsNullOrWhiteSpace($data.content)) {
            throw 'Inventory GitHub content response invalid.'
        }
        $inventoryBytes = [Convert]::FromBase64String(($data.content -replace '\s',''))
        if ((Get-HexSha256 -Bytes $inventoryBytes) -cne $InventoryHash) {
            throw 'Inventory raw bytes differ from independently selected SHA-256.'
        }
        $utf8 = [Text.UTF8Encoding]::new($false,$true)
        $inventoryText = $utf8.GetString($inventoryBytes)
        if ($inventoryText.Length -eq 0 -or
            $inventoryText.IndexOf([char]13) -ge 0 -or
            $inventoryText.IndexOf([char]0) -ge 0 -or
            $inventoryText[$inventoryText.Length-1] -ne [char]10) {
            throw 'Expected LF-only UTF-8 inventory with one final LF.'
        }
        $rows = @($inventoryText.Substring(0,$inventoryText.Length-1).Split([char]10))
        $inventory = [System.Collections.Generic.Dictionary[string,string]]::new([StringComparer]::Ordinal)
        $caseGuard = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        foreach ($row in $rows) {
            $match = [regex]::Match($row,'^([a-f0-9]{64})  ([A-Za-z0-9._/-]+)$')
            if (-not $match.Success) { throw 'Bad inventory row.' }
            $name = $match.Groups[2].Value
            if ($name.StartsWith('/') -or
                @($name.Split('/') | Where-Object { $_ -eq '' -or $_ -eq '.' -or $_ -eq '..' }).Count -gt 0 -or
                $inventory.ContainsKey($name) -or -not $caseGuard.Add($name)) {
                throw 'Ambiguous or duplicate inventory path.'
            }
            $inventory.Add($name,$match.Groups[1].Value)
        }
        if ($inventory.Count -ne 232 -or
            -not $inventory.ContainsKey('plugins/vres-os/hooks/hooks.json') -or
            $inventory['plugins/vres-os/hooks/hooks.json'] -cne '08e5d5297579eb5697b0fb57a54cb8e2a670d7a875a5111883f6534a2d694199') {
            throw 'Wrong inventory count or Incident B hook identity.'
        }

        # Only one new folder, never remove or adopt a pre-existing folder.
        [void](New-Item -ItemType Directory -Path $Root -ErrorAction Stop)
        [void](Invoke-SafeGit -GitArguments @('clone','--quiet','--no-checkout','--single-branch','--no-tags','--branch',$Branch,$RepoUrl,$Repo))
        $headValue = Invoke-SafeGit -GitArguments @('-C',$Repo,'rev-parse','HEAD') -SingleLine
        $treeValue = Invoke-SafeGit -GitArguments @('-C',$Repo,'rev-parse',($Commit + '^{tree}')) -SingleLine
        $parentLine = Invoke-SafeGit -GitArguments @('-C',$Repo,'rev-list','--parents','-n','1',$Commit) -SingleLine
        if ($headValue -cne $Commit -or $treeValue -cne $Tree -or
            $parentLine -cne ($Commit + ' ' + $Parent)) {
            throw 'HEAD/tree/sole-parent exact identity mismatch.'
        }
        $treeArgs = @('-C',$Repo,'ls-tree','-r','--full-tree',$Commit,'--') + $Scope
        $treeRows = @(Invoke-SafeGit -GitArguments $treeArgs)
        if ($treeRows.Count -ne 232) { throw 'Git release-scope file count mismatch.' }
        $treeNames = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($line in $treeRows) {
            $matched = [regex]::Match($line,'^100644 blob [a-f0-9]{40}\t([A-Za-z0-9._/-]+)$')
            if (-not $matched.Success -or
                -not $inventory.ContainsKey($matched.Groups[1].Value) -or
                -not $treeNames.Add($matched.Groups[1].Value)) {
                throw 'Git scope path, mode or uniqueness mismatch.'
            }
        }
        if ($treeNames.Count -ne 232) { throw 'Git scope missing files.' }
        $migrations = [System.Collections.Generic.HashSet[int]]::new()
        foreach ($name in $treeNames) {
            if ($name.StartsWith('src/vres_os/migrations/',[StringComparison]::Ordinal) -and
                $name.EndsWith('.sql',[StringComparison]::Ordinal)) {
                $mm = [regex]::Match($name,'/([0-9]{3})_[A-Za-z0-9._-]+\.sql$')
                if (-not $mm.Success -or -not $migrations.Add([int]$mm.Groups[1].Value)) {
                    throw 'Non-canonical or duplicate SQL migration.'
                }
            }
        }
        if ($migrations.Count -ne 41) { throw 'Not exactly 41 inert SQL migrations.' }
        for ($n=1; $n -le 41; $n++) {
            if (-not $migrations.Contains($n)) { throw '001-041 migration gap.' }
        }

        $archiveArgs = @('-C',$Repo,'archive','--format=zip','-o',$ZipPath,$Commit,'--') + $Scope
        [void](Invoke-SafeGit -GitArguments $archiveArgs)
        if (-not (Test-Path -LiteralPath $ZipPath -PathType Leaf) -or
            (Get-Item -LiteralPath $ZipPath).Length -gt 64MB) {
            throw 'Source ZIP missing or exceeds 64 MiB.'
        }
        Add-Type -AssemblyName System.IO.Compression
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $allowedDirs = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($name in $inventory.Keys) {
            $parts = $name.Split('/')
            for ($i=1; $i -lt $parts.Length; $i++) {
                [void]$allowedDirs.Add(($parts[0..($i-1)] -join '/') + '/')
            }
        }
        $seenDirs = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        $seenFiles = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        $totalExpanded = [long]0
        $zip = [IO.Compression.ZipFile]::OpenRead($ZipPath)
        try {
            foreach ($entry in $zip.Entries) {
                $name = [string]$entry.FullName
                if ($name.EndsWith('/',[StringComparison]::Ordinal)) {
                    if (-not $allowedDirs.Contains($name) -or -not $seenDirs.Add($name) -or
                        $entry.Length -ne 0) { throw 'Unexpected ZIP directory.' }
                    continue
                }
                if (-not $inventory.ContainsKey($name) -or -not $seenFiles.Add($name) -or
                    $entry.Length -gt 15MB) { throw 'Unknown, duplicate or oversized ZIP file.' }
                $totalExpanded += [long]$entry.Length
                if ($totalExpanded -gt 64MB) { throw 'ZIP inflated byte budget exceeded.' }
                $stream = $entry.Open()
                try {
                    $hash = [Security.Cryptography.SHA256]::Create()
                    try {
                        $memberHash = [BitConverter]::ToString($hash.ComputeHash($stream)).Replace('-','').ToLowerInvariant()
                    } finally { $hash.Dispose() }
                } finally { $stream.Dispose() }
                if ($memberHash -cne $inventory[$name]) { throw 'ZIP member SHA-256 mismatch.' }
            }
            if ($seenFiles.Count -ne 232) { throw 'ZIP source member count incomplete.' }
        } finally { $zip.Dispose() }
        $zipHash = (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
        Write-Output 'SOURCE_ONLY_INERT_BYTES=PASS; NO_EXECUTION_OR_INSTALL'
        Write-Output ('SOURCE_COMMIT=' + $Commit)
        Write-Output ('SOURCE_TREE=' + $Tree)
        Write-Output ('INVENTORY_SHA256=' + $InventoryHash)
        Write-Output ('ZIP_SHA256=' + $zipHash)
        Write-Output ('GIT_EXE=' + $GitExe)
        Write-Output ('GIT_VERSION=' + $gitVersion)
        Write-Output ('GIT_SIGNER=' + $subject)
        Write-Output ('GIT_CONFIG_GLOBAL=' + [Environment]::GetEnvironmentVariable('GIT_CONFIG_GLOBAL','Process'))
        Write-Output ('OUTPUT_ROOT=' + $Root)
        Write-Output 'HOOKS_JSON_PRESENT_BUT_NOT_SAFE_TO_ACTIVATE=YES'
        Write-Output 'P2_INSTALL=NOT_RUN; DEPENDENCY_LOCK=NOT_RUN'
    } finally {
        foreach ($item in @(Get-ChildItem Env: | Where-Object { $_.Name -like 'GIT_*' })) {
            [Environment]::SetEnvironmentVariable($item.Name,$null,'Process')
        }
        foreach ($key in $oldGit.Keys) {
            [Environment]::SetEnvironmentVariable($key,$oldGit[$key],'Process')
        }
        [Environment]::SetEnvironmentVariable('GCM_INTERACTIVE',$oldGcm,'Process')
        # Leave any incomplete disposable folder untouched, for review.
    }
}
~~~

## Next review and strict holds
A separate Claude.ai session must assess the **exact published corrected script** (S1–S8) and state `DESIGN_ACCEPT / DESIGN_REVISE / STATIC_REJECT` with specific evidence. Also scrutinize Windows PowerShell 5.1 binding of generic collections and native command outputs, Git's actual executable/signature (including wrapper/DLL load assumptions), Git filters/config, root identity, zip extra fields/entry types, environment/proxy/credential side effects, and whether the single-block console copy reliably fails closed. It must not execute the script or source. If accepted narrowly, seek separate owner choices of source commit, risk model, Git exe/signer/hash, root, network effects, reviewed final script and explicit exact authorization. **Neither this document nor a positive design verdict permits Windows execution.**

Absolute holds unchanged: `LIVE_SCHEMA_048_INCIDENT=OPEN` ⇒ no PostgreSQL even SELECT; `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` ⇒ no ordinary native Claude Code/installed hooks; original P3 OPEN, F1/Fable trusted positive authority NOT_GRANTED. No installed P2 changes, credentials/profile/PRISM/real legacy, protected worktrees, Vres runtime/installer/migration, Windows Sandbox R2, Windows/POSIX staging, destructive rollback, main merge, completed TASK-DAY-01 or its original note/desk changes. All V-01..V-42, M0..M8, #163/#164/#165–170/#174/#176/#185, W0–W4 R1–R13, A12/A13/A16/A19 and E7/F2/F1/P3/C2B/R0/K0/Stage1–6 remain preserved. R13 47 authored pytest functions, genuine original ZIP, NTFS gate, dependency closure, UAT #169 and pilot #170 still NOT_RUN.
