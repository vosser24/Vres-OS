# W4 — Original host dependency auto-provisioning closed (SOURCE ONLY)

**2026-11-17 Europe/Athens. AUTHORING ONLY / ALL TESTS NOT_RUN.**
This is the original Windows installer's prerequsite acquisition closure, not a second installer,
publisher attestation, independent security review, OS operation, or release authorization.

## Exact integrated owner change

The ORIGINAL `install.ps1` no longer owns WinGet package discovery,
installation, PATH refresh after external package installation, or npm-global Codex
installation, for either a new install or `-Update`. It requires Claude Code to
have been provisioned separately, preserves its explicit current-host version
check, rejects missing local PostgreSQL in future fresh local-DB mode without
auto-installing it, and rejects missing optional Codex if `-WithCodex` was
requested. It retains `-UseRemotePostgres`, `-WithEmbeddings`, the selected
single Chairman/Tk/CLI/MCP application, original Git/Python pins, source
commit/tree, offline root-wheel parity, complete lock requirement, isolated
pip and original installed-release journal/recovery owner.

The updated `README.md` and original Windows guide replace stale
auto-provision/PyPI advice with explicit source-only holds. The original
contract assertions were updated for package acquisition and current
attempted-only recovery, and a preflight static assertion's stale regex
expectation was corrected. Tests are AUTHORED/NOT_RUN.

## What this does NOT establish

A `Get-Command claude` match, existing PostgreSQL service name, installed
Codex command, or Python/Git executable SHA-256 is NOT proof of independent
publisher authenticity, Git DLL/GCM/helper/config trust, Python native DLLs/
Tcl/Tk/stdlib, complete wheelhouse provenance, NTFS ancestry/ACL/process
identity, no swap race, or safe subprocess behavior. Claude plugin validation,
source Python, other child commands and their host/DB side effects remain
unverified. Nothing here grants a Windows/DB/native-Claude operation.

`LIVE_SCHEMA_048_INCIDENT=OPEN` => NO PostgreSQL even SELECT, direct or
indirect. `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` => NO ordinary
native Claude Code/hooks. #185 independent complete positive
THREAT_MODEL/RELEASE_DESIGN/OPERATIONS verdict is NOT_GRANTED; F1/Fable
positive authority also NOT_GRANTED. P3, Git L2, R13/WPR, original
update/install, Tk, CLI/MCP, credentials, real projects and installed
Windows P2 remain HELD. No tests or Windows actions were performed.

Next: independently reviewed whole dependency/publisher/native DLL/NTFS
closure, positive #185 review and separate incident clearance; then
target-specific owner approval before isolated/native tests and original
Windows preflight, installation, recovery and full V-01..V-42 UAT.
