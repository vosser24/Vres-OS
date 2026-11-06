# W4 R14-D4 — Claude.ai cloud review reconciliation and GIT-ARCHIVE PROTOCOL DRAFT
**Date:** 2026-11-06. **Status: P0 DOCS-ONLY DRAFT. SOURCE COMMIT NOT OWNER-APPROVED. LOCAL SCRIPT NOT_REVIEWED / NOT_RUN / NOT_AUTHORIZED. NO RELEASE OR SECURITY INCIDENT CLEARANCE.**

## Independent review provenance and limits
The owner supplied a text copy attributed to a **separate Claude.ai cloud reviewer** and a 232-line SHA-256 source inventory. This is user-supplied external AI review evidence, not a signed human audit, a directly observed reviewer session or GitHub issue #185 comment. The reviewer said issue #185 was unreachable; it read the full D4 and D1, only parts of D2/D3, and did not fully inspect all W1–W3 or all R13 tests. Therefore the full #185 brief is **NOT_FULLY_SATISFIED** and there is NO operational clearance.

Reported three decisions: **THREAT_MODEL=REVISE** (AI-authored defective change and self-updated pins, hooks in scope, define independent SHA-256); **RELEASE_DESIGN=DESIGN_REVISE** (consider official Git `archive` + Windows hashing instead of candidate Python; D3 optional); **OPERATIONS=READ_ONLY_P0_PERMIT, ALL_LOCAL/SOURCE/INSTALLED_CHANGE_HELD_OR_REFUSED**. These are substantive reviewer recommendations, not authority to execute or release.

## Independent GitHub reconciliation performed in ChatGPT
- Repository: `vosser24/Vres-OS`, ID `1368577038`.
- Docs `docs/chatgpt-continuity-20261023` last verified `9acc5774980d758aafee80be1a6ab0e38e473d44`, TREE `b0ffa8e97f22e8be02f329beabd78055df262a4b`, sole parent `a622f7bbadfae671c8ac9dce4f437b7a5cd90b59`.
- Product main `9a8acc5d464b96432a93cb95daa9581412fb07ee` unchanged; DO NOT MERGE.
- W3 R2 `982e77f2f4974b4fbca5da91d3e11aeb56e40271` → R13 `bcf62460d68caebfdbd0e838d44c5997992c5fbc` = 13 ahead / 0 behind. R13 TREE `9bbc5615fef4a8f785e9ddb0056e9430ffe25d63`, sole parent `0badcd34d1eafbce5f815512a489d70cb240eecd`.
- Exactly 232 release-scope Git files, all mode `100644`, 41 SQL migration files 001–041, no 042+, no case-fold duplicates; all 232 paths matched the supplied inventory with no extras/missing.
- Of R13's 13 self-listed source-owner SHA-1 pins, **9 are unchanged W3 owners**, **two existing files modified in W4** and **two new W4 modules**. The label "13 original owners" alone overstates inherited W3 authority:
  | File | Accepted W3 R2 Git blob | R13 Git blob | Classification |
  |---|---|---|---|
  | `src/vres_os/release_artifact.py` | `497fa3d96742a868f8b00b5dcb26e8afe03fd159` | `1719f839d75b4dd994125c5f6d1ede2d4b7100b2` | Modified owner; legacy stage remains separately callable |
  | `src/vres_os/release_inputs.py` | `a0cdf3195f0cf0f2a61ce32521a74f78260832f7` | `f6008f391305840645a707407fa8f464b0e27389` | Modified: new in-memory migration record validator |
  | `src/vres_os/personal_w4_inert_git.py` | ABSENT | `af7bcb17f4b09eb262589021b9f6444de2c56fe1` | New W4 POSIX-oriented loose Git adapter |
  | `src/vres_os/personal_w4_bound_output.py` | ABSENT | `972c7c8276025c0cc2d68bd1be2d7173a29cb439` | New W4 POSIX synthetic writer (Windows refused) |
- W3→R13 combined diff inspected. `release_artifact.py` gains bounded read/tree safeguards, Windows path checks, manifest helpers and a caller-selectable preserve-on-failure switch; **the default legacy stage still performs path-based writes and may recursively remove its own intermediate staging root**. `release_inputs.py` gains an in-memory validator but leaves the original on-disk migration validator. No observed Git diffs imply operational security acceptance. The two new modules are unsuitable as a trusted initial Windows publisher.
- Supplied inventory `docs/handoffs/VRES-W4-R13-CLAUDE-CLOUD-REVIEWER-SHA256-INVENTORY-2026-11-06.txt`: exactly 232 well-formed unique `sha256[2 spaces]path` rows; its *canonical LF with final LF* SHA-256 is **`c6dab3be2ad86cf0fca2586b870665bc20ad8830c9e76e2f677f0ec8801b13c6`**. The originally uploaded CRLF/no-final-newline text SHA-256 is `ce9fa2c83887c0eeffdd6240f89935a9e113e691902f02b998ab50c861a250a9`. These two text hashes describe DIFFERENT NEWLINE SERIALIZATIONS of the same 232 rows, not conflicting contents. Reviewer-provided hash text and pathset are NOT an owner-approved release authorization.
- Independently recomputed from live GitHub file contents and matched six raw SHA-256 hashes: `release_artifact.py`, `release_inputs.py`, both new W4 modules, `plugins/vres-os/hooks/hooks.json`, and `migrations/001_initial.sql`. The remaining 226 per-file SHA-256 values were not independently recomputed here. Git tree path/mode evidence is static; no host/source tests were run.
- Hook configuration `plugins/vres-os/hooks/hooks.json` is in the inert archive with raw SHA-256 `08e5d5297579eb5697b0fb57a54cb8e2a670d7a875a5111883f6534a2d694199`; this is **NOT permission to install or activate hooks**. The root installer `install.ps1` and update scripts are not in the 232-file release scope; even a fully verified ZIP cannot be installed by the original installer (which requires a Git checkout and has held Claude/DB/profile pathways).
- GitHub issue #185 was still OPEN with ZERO comments and no reviewer assignment when checked. The report itself was NOT posted to the issue by ChatGPT, nor was a reviewer identity authenticated by GitHub.

## Decision / design boundary
The official-Git data-only archive alternative is a **proposed narrow, proportionate P1 synthetic workflow**, not independently accepted operation. The AI reviewer excluded active same-user/admin/compromised OS adversaries: this must be explicitly accepted by the owner; a SHA-256 digest does not prove Vres publisher authority or prevent self-approved defective development. Owner-controlled reviewed diff + exact approved Git commit/tree/independent hash inventory are prerequisites. Official Git for Windows and built-in PowerShell are assumed trusted but their actual installed identity has not been observed. The future candidate includes **unsafe-to-activate hooks** and cannot be represented as installable, runtime-ready, schema-048 safe or host-hook cleared. D3 independent signing remains optional high-assurance architecture rather than silently deleted.

**One recommended next choice:** prefer `bcf62460...` as a *proposed inert data snapshot only* after owner review of the four W4-derived identities; do NOT approve it as a production release. A later commit is required only for a demonstrated source defect, not merely to advance a SHA.

## DRAFT ONLY — future PowerShell source-data gate (NO EXECUTION AUTHORIZED)
The following is newly authored, **NOT independently reviewed, NOT syntax-executed, NOT approved by the owner**. It is NOT an executable release handoff. **DO NOT COPY/RUN** until a separate cloud reviewer validates the exact script and the owner gives a fresh exact command/path/network/tool approval. It has a consent-string guard but that guard alone does not establish safety or authority. Other system-level Git settings and Windows aliases must be considered by the reviewer. The target C:\Projects name is provisional and has NOT been observed absent on the owner's PC.

~~~powershell
# DRAFT ONLY: DO NOT RUN UNTIL CLOUD REVIEW + NEW EXACT OWNER APPROVAL.
# This is not a Vres runtime/installer/recovery procedure.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ExpectedCommit = 'bcf62460d68caebfdbd0e838d44c5997992c5fbc'
$ExpectedTree = '9bbc5615fef4a8f785e9ddb0056e9430ffe25d63'
$ExpectedParent = '0badcd34d1eafbce5f815512a489d70cb240eecd'
$InventorySha256 = 'c6dab3be2ad86cf0fca2586b870665bc20ad8830c9e76e2f677f0ec8801b13c6'
$RootParent = 'C:\Projects'
$CandidateName = 'Vres-W4-R13-InertGitArchive-bcf62460'
$CandidateRoot = Join-Path $RootParent $CandidateName
$RepoPath = Join-Path $CandidateRoot 'unexecuted-git-objects'
$ZipPath = Join-Path $CandidateRoot 'source-only.zip'
$InventoryApi = 'https://api.github.com/repos/vosser24/Vres-OS/contents/docs/handoffs/VRES-W4-R13-CLAUDE-CLOUD-REVIEWER-SHA256-INVENTORY-2026-11-06.txt?ref=docs%2Fchatgpt-continuity-20261023'
$Consent = Read-Host 'Enter separately approved exact authorization, or press Enter to abort'
if ($Consent -cne 'AUTHORIZE-W4R13-INERT-GIT-ARCHIVE-ONLY') {
    throw 'NOT AUTHORIZED. No source/output directory was created.'
}

# One explicitly selected new direct C:\Projects child only. Never adopt or delete it.
$ParentInfo = Get-Item -LiteralPath $RootParent -ErrorAction Stop
if (-not $ParentInfo.PSIsContainer -or
    (($ParentInfo.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) -or
    (Test-Path -LiteralPath $CandidateRoot)) {
    throw 'Unexpected/reparse source parent or candidate destination already exists.'
}
$GitCommand = Get-Command git.exe -CommandType Application -ErrorAction Stop
$GitExe = $GitCommand.Source
if (-not (Test-Path -LiteralPath $GitExe -PathType Leaf)) {
    throw 'Official Git for Windows executable is not available.'
}
# This command cannot independently certify toolchain provenance. The owner
# must accept the exact Git executable/path/version before granting permission.
$GitVersion = (& $GitExe --version)
if ($LASTEXITCODE -ne 0) { throw 'Git version check failed.' }

# Fetch independent REVIEWER inventory as inert data, validate its expected
# canonical LF + final LF SHA-256. The candidate does not choose its own pins.
$ApiResult = Invoke-RestMethod -Method Get -Uri $InventoryApi -Headers @{'User-Agent'='Vres-Personal-Source-Review'} -ErrorAction Stop
if ($ApiResult.encoding -cne 'base64' -or -not $ApiResult.content) {
    throw 'GitHub reviewer inventory is unavailable.'
}
$InventoryBytes = [Convert]::FromBase64String(($ApiResult.content -replace '\s', ''))
$shaObj = [Security.Cryptography.SHA256]::Create()
try {
    function HexHash([byte[]]$Hash) { [BitConverter]::ToString($Hash).Replace('-', '').ToLowerInvariant() }
    if ((HexHash ($shaObj.ComputeHash($InventoryBytes))) -cne $InventorySha256) {
        throw 'Reviewer inventory does not match the independently recorded digest.'
    }
    $InventoryText = [Text.Encoding]::UTF8.GetString($InventoryBytes)
    if ($InventoryText.Contains([char]13) -or -not $InventoryText.EndsWith([char]10)) {
        throw 'Inventory must have exact canonical LF lines and a final LF.'
    }
    $Inventory = @{}
    $namesCaseInsensitive = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($line in $InventoryText.TrimEnd([char]10).Split([char]10)) {
        if ($line -cnotmatch '^([a-f0-9]{64})  (.+)$') { throw 'Malformed inventory row.' }
        $path = $Matches[2]
        if ($Inventory.ContainsKey($path) -or -not $namesCaseInsensitive.Add($path) -or
            $path.StartsWith('/') -or $path.Contains('\') -or $path.Contains(':') -or
            ($path -split '/') -contains '..') { throw 'Unsafe/duplicate inventory path.' }
        $Inventory[$path] = $Matches[1]
    }
    if ($Inventory.Count -ne 232 -or
        $Inventory['plugins/vres-os/hooks/hooks.json'] -cne
            '08e5d5297579eb5697b0fb57a54cb8e2a670d7a875a5111883f6534a2d694199') {
        throw 'Wrong release inventory or Incident-B hook identity.'
    }
} finally { $shaObj.Dispose() }

$PrevNoSystem = [Environment]::GetEnvironmentVariable('GIT_CONFIG_NOSYSTEM','Process')
$PrevPrompt = [Environment]::GetEnvironmentVariable('GIT_TERMINAL_PROMPT','Process')
try {
    [Environment]::SetEnvironmentVariable('GIT_CONFIG_NOSYSTEM','1','Process')
    [Environment]::SetEnvironmentVariable('GIT_TERMINAL_PROMPT','0','Process')
    [void](New-Item -ItemType Directory -Path $CandidateRoot -ErrorAction Stop)
    # No checkout, no remote hooks. No Vres Python, PowerShell plugin or installer.
    & $GitExe -c core.hooksPath=NUL -c core.autocrlf=false -c core.fsmonitor=false clone --no-checkout --branch feature/personal-w4-r13-universal-staging-hold-20261106 https://github.com/vosser24/Vres-OS.git $RepoPath
    if ($LASTEXITCODE -ne 0) { throw 'Git clone failed. Preserve the output root for inspection.' }
    $Head = (& $GitExe -C $RepoPath rev-parse 'HEAD').Trim()
    $Tree = (& $GitExe -C $RepoPath rev-parse "$($ExpectedCommit)^{tree}").Trim()
    $Parents = (& $GitExe -C $RepoPath rev-list --parents -n 1 $ExpectedCommit).Trim()
    if ($LASTEXITCODE -ne 0 -or $Head -cne $ExpectedCommit -or
        $Tree -cne $ExpectedTree -or
        $Parents -cne "$ExpectedCommit $ExpectedParent") {
        throw 'Candidate HEAD/TREE/sole parent differs from exact approval reference.'
    }
    $Specs = @('src/vres_os','plugins/vres-os','scripts/windows',
               'pyproject.toml','README.md','LICENSE','rules/vres-rules.md')
    $GitRows = @(& $GitExe -C $RepoPath ls-tree -r --full-tree $ExpectedCommit -- @Specs)
    if ($LASTEXITCODE -ne 0 -or $GitRows.Count -ne 232) {
        throw 'Release-scope Git tree count differs from approved inventory.'
    }
    $Found = @{}
    foreach ($row in $GitRows) {
        if ($row -cnotmatch '^100644 blob [a-f0-9]{40}\t(.+)$') { throw 'Unapproved file mode/type.' }
        $path = $Matches[1]
        if (-not $Inventory.ContainsKey($path) -or $Found.ContainsKey($path)) {
            throw 'Git scope has an unknown or duplicate file.'
        }
        $Found[$path] = $true
    }
    if ($Found.Count -ne $Inventory.Count) { throw 'Git scope is missing an approved file.' }
    $Mig = @($Found.Keys | Where-Object { $_ -match '^src/vres_os/migrations/([0-9]{3})_.+\.sql$' })
    if ($Mig.Count -ne 41 -or
        @($Mig | Where-Object { [int]([regex]::Match($_,'/([0-9]{3})_').Groups[1].Value) -lt 1 -or
                                  [int]([regex]::Match($_,'/([0-9]{3})_').Groups[1].Value) -gt 41 }).Count -ne 0) {
        throw 'Migration numbers outside inert 001-041 set.'
    }
    & $GitExe -C $RepoPath archive --format=zip -o $ZipPath $ExpectedCommit -- @Specs
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $ZipPath -PathType Leaf) -or
        (Get-Item -LiteralPath $ZipPath).Length -gt 64MB) {
        throw 'Inert Git archive could not be created within the byte ceiling.'
    }
    # Verify archive member raw SHA-256 entirely in memory/streams.
    # NEVER extract, import, execute, install, stage or activate ZIP members.
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $Zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
    try {
        $Seen = @{}
        $AllowedDirs = @{}
        foreach ($path in $Inventory.Keys) {
            $parts = $path.Split('/')
            for ($i=1; $i -lt $parts.Length; $i++) {
                $AllowedDirs[(($parts[0..($i-1)] -join '/') + '/')] = $true
            }
        }
        $hashObj = [Security.Cryptography.SHA256]::Create()
        try {
            foreach ($entry in $Zip.Entries) {
                $name = $entry.FullName
                if ($name.EndsWith('/')) {
                    if (-not $AllowedDirs.ContainsKey($name) -or $entry.Length -ne 0) {
                        throw 'Unexpected ZIP directory entry.'
                    }
                    continue
                }
                if (-not $Inventory.ContainsKey($name) -or $Seen.ContainsKey($name) -or
                    $entry.Length -gt 15MB) { throw 'Unexpected, duplicate or oversized ZIP member.' }
                $memberStream = $entry.Open()
                try { $got = HexHash ($hashObj.ComputeHash($memberStream)) }
                finally { $memberStream.Dispose() }
                if ($got -cne $Inventory[$name]) { throw 'ZIP member differs from external SHA-256 inventory.' }
                $Seen[$name] = $true
            }
        } finally { $hashObj.Dispose() }
        if ($Seen.Count -ne 232) { throw 'ZIP archive is incomplete.' }
    } finally { $Zip.Dispose() }
    $ZipHash = (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
    Write-Output 'SOURCE_ONLY_DATA_VERIFICATION=PASS (NO LAUNCH/INSTALL)'
    Write-Output "SOURCE_COMMIT=$ExpectedCommit"
    Write-Output "SOURCE_TREE=$ExpectedTree"
    Write-Output "INVENTORY_SHA256=$InventorySha256"
    Write-Output "ZIP_SHA256=$ZipHash"
    Write-Output "GIT_VERSION=$GitVersion"
    Write-Output "GIT_EXE_PATH=$GitExe"
    Write-Output "OUTPUT_ROOT=$CandidateRoot"
    Write-Output 'SOURCE_ENTRIES=232 / HOOKS_PRESENT_AND_NOT_SAFE_TO_ACTIVATE'
    Write-Output 'DEPENDENCY_CLOSURE=NOT_RUN / WINDOWS_INSTALL=NOT_RUN'
} finally {
    [Environment]::SetEnvironmentVariable('GIT_CONFIG_NOSYSTEM',$PrevNoSystem,'Process')
    [Environment]::SetEnvironmentVariable('GIT_TERMINAL_PROMPT',$PrevPrompt,'Process')
    # Preserve any partial root for explicit inspection; NEVER remove it here.
}
~~~

**Required independent review before any gate:** Windows PowerShell 5.1 parser and native stderr semantics; `Invoke-RestMethod` network/response data handling; Git path/config/hooks/credential helper origin; correctness of ZIP member streaming and folder entries; duplicate/alias/size checks; error handling/root retention and environment restoration; scope of all 232 exact SHA rows; whether any command accesses protected profile/DB/hooks indirectly. STOP on any uncertainty. The script has NOT been approved as safe. Do not mutate installed P2, invoke normal native Claude, contact PostgreSQL even SELECT, run any Vres Python, install, stage operationally or clean roots.

## Evidence and next sequence
**PASS:** GitHub read-only refs/tree/parent/ancestry, exact W3/R13 four-file change classification, inventory pathset, six recomputed SHA-256 samples, canonical text serialization reconciliation.
**NOT_RUN:** R13 47 authored pytest functions, original-owner production ZIP, the above PowerShell script, Windows NTFS gate, full 232 raw SHA-256 rehash, dependency wheel closure, physical installed P2, UAT #169, pilot #170.
**HELD:** exact R13 source baseline owner risk acceptance; complete D4 design review; all installed/host operations; R13 staging and destructive rollback.
**ABSOLUTE OPEN:** LIVE_SCHEMA_048_INCIDENT; HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED; original P3; F1/Fable independent positive authority NOT_GRANTED.
**Roadmap:** preserve V-01..V-42 and M0–M8, #163/#164/#165–170/#174/#176/#185, W0/W1/W2/W3 accepted narrow offline tests, W4 R1–R13 rejected attempts, A12/A13/A16/A19, E7/F2/F1/P3/C2B/R0/K0/Stage1–6, protected worktrees, original TASK-DAY-01 and installed P2. Restore separate cloud-source review first; real host G1 incident dispositions and hash-locked dependencies precede P2; actual #169 Visual Studio UAT then #170 personal pilot.
