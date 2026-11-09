# Vres-OS W4 R14-D4 — R1/R2 inert Git archive RESTRICTED-POLICY STREAM-HASH corrected draft
**Date:** 2026-11-09 Europe/Athens. **Status: DOCS-ONLY NEW VERSION / AUTHOR CORRECTION / POST-CORRECTION INDEPENDENT REVIEW NOT_RUN / WINDOWS NOT_RUN / OWNER DID NOT APPROVE GIT COMMAND, SIGNER, HASH, OUTPUT ROOT OR NETWORK.**
**DO NOT EXECUTE THIS SCRIPT.** This new versioned file does not overwrite the prior reviewed draft `docs/architecture/VRES-W4-R14-D4-R1-R2-CORRECTED-INERT-GIT-ARCHIVE-DRAFT-2026-11-06.md` (blob `a8daf5a51ab1c456dd6eb4cc5334a1006acba2be`) or either earlier rejected draft. Prior fourth same-Claude.ai cloud review of the R1/R2 script was narrow DESIGN_ACCEPT subject to A1–A4: https://claude.ai/artifact/3XTryuqfa5fJ1ExFPJw2jk . Fifth review found a possible Restricted-policy module-autoload blocker in the PRE-FLIGHT and retrospectively in this archive script: https://claude.ai/artifact/Jhv9AnBd2BndpammJ2yLtF ; verdict for preflight: DESIGN_REVISE.
**Exactly two intended changes to the inherited PowerShell block:** replace original `Get-FileHash` for `$binaryHash` and `$zipHash` with read-only .NET stream SHA-256, nested deterministic disposals, and lowercase hexadecimal output. All other PowerShell block lines are inherited from original blob `a8daf5a5...`; no blank or whitespace-only lines inside `& { ... }`. Author text inspection only. Running this source-only script is NOT authorized. It includes deliberately unapproved `PENDING_OWNER_APPROVAL` identity pins.
The approved PLANNING-ONLY personal threat model excludes an active malicious same-user or administrator process; R13 is owner-selected ONLY as an inert source-data candidate. This does not clear the installed/native/database incidents or certify the underlying Git installation. The reviewer's approval covers DESIGN, not host execution. The new two-fragment version needs independent narrow diff confirmation.
## Full revised PowerShell archive proposal — DO NOT RUN
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
        $shaFileStream = [IO.File]::OpenRead($GitExe)
        try {
            $shaProvider = [Security.Cryptography.SHA256]::Create()
            try { $binaryHash = [BitConverter]::ToString($shaProvider.ComputeHash($shaFileStream)).Replace('-','').ToLowerInvariant() }
            finally { $shaProvider.Dispose() }
        } finally { $shaFileStream.Dispose() }
        # R1: no Git invocation until owner-approved signer, thumbprint and executable hash match.
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
        # File property inspection only: does NOT execute git.exe. If absent, STOP.
        $verInfo = $gitFile.VersionInfo
        $gitVersion = [string]$verInfo.ProductVersion
        if ([string]::IsNullOrWhiteSpace($gitVersion)) {
            $gitVersion = [string]$verInfo.FileVersion
        }
        $ver = [regex]::Match($gitVersion,'^([0-9]+)\.([0-9]+)(?:\.|$)')
        if (-not $ver.Success -or [int]$ver.Groups[1].Value -lt 2 -or
            ([int]$ver.Groups[1].Value -eq 2 -and [int]$ver.Groups[2].Value -lt 32)) {
            throw 'Git executable file metadata does not establish version 2.32+. STOP.'
        }
        Write-Output ('APPROVED_GIT_EXE=' + $GitExe)
        Write-Output ('GIT_FILE_PROPERTY_VERSION=' + $gitVersion)
        Write-Output ('GIT_SIGNER_SUBJECT=' + $subject)
        Write-Output ('GIT_SIGNER_THUMBPRINT=' + $thumbprint)
        Write-Output ('GIT_EXE_SHA256=' + $binaryHash)
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
        $shaFileStream = [IO.File]::OpenRead($ZipPath)
        try {
            $shaProvider = [Security.Cryptography.SHA256]::Create()
            try { $zipHash = [BitConverter]::ToString($shaProvider.ComputeHash($shaFileStream)).Replace('-','').ToLowerInvariant() }
            finally { $shaProvider.Dispose() }
        } finally { $shaFileStream.Dispose() }
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
## Fixed source identity, test provenance and absolute holds
- Repository: https://github.com/vosser24/Vres-OS . Previous docs HEAD `c3d5d25d1810c1f7208012c2b82abbc1b9a68783`, previous docs TREE `09f22941ed254945685c0d4372fa50ccbf579923`, sole parent `0866bc6e524f3558dfb662d2f025364f13e02e50` (historical values; reverify live). Product main `9a8acc5d464b96432a93cb95daa9581412fb07ee` unchanged, NO MERGE.
- R13 branch `feature/personal-w4-r13-universal-staging-hold-20261106`, exact HEAD `bcf62460d68caebfdbd0e838d44c5997992c5fbc`, TREE `9bbc5615fef4a8f785e9ddb0056e9430ffe25d63`, parent `0badcd34d1eafbce5f815512a489d70cb240eecd`. Source inventory SHA-256 `c6dab3be2ad86cf0fca2586b870665bc20ad8830c9e76e2f677f0ec8801b13c6` at docs commit `15ba0387fb0fc559d8daa596e59b6f6920d23a9b`: 232 mode-100644 files, 41 inert SQL migrations 001–041; hooks.json and .mcp.json are unsafe-to-activate INERT DATA.
- All 47 R13 authored pytest functions remain NOT_RUN. This variant's PowerShell 5.1 parser, Windows console input, Git archive on owner's host, genuine original-owner ZIP gate, NTFS safety, dependency-wheel closure, installer, protected P2 and UAT #169/#170 remain NOT_RUN.
- NO Git identity values have been approved; signer subject, thumbprint and hash placeholders remain exact unchanged PENDING_OWNER_APPROVAL. Git for Windows must be independently observed and exact approved maintained version before any source-only gate. `C:\Projects` is a candidate parent, not inspected or approved.
- Absolutely no PostgreSQL even SELECT (`LIVE_SCHEMA_048_INCIDENT=OPEN`), native Claude Code/hooks (`HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`), original P3 (OPEN), trusted F1/Fable positive authority, protected P2, real credentials/profile/legacy/PRISM, Windows Sandbox R2, installed updates, operational staging or rollback, TASK-DAY-01 original note/desk modification, or main merge.
- Next action: independent read-only narrow diff/re-review of both new corrected docs; then separate owner approval of the EXACT preflight command and incidental host effects, if accepted. Do not automatically authorize a CMD/PowerShell/Git invocation.
