# 2026-11-17 — Original owner correction: Claude CLI/MCP + installer consent

**SOURCE ONLY; ALL TESTS, Windows execution, installation and UAT NOT_RUN.**

The OWNER clarified that Vres-OS is **ONE personal companion to Claude
Code CLI with MCP capabilities**, using the existing original Chairman,
tasks, sessions, results, history, projects, data-source and learning
owners. The CLI/MCP experience is the primary interface. No separate
visual desktop, second app, duplicate Chairman or new installer is
requested. Existing Tk files are not deleted, but GUI work is not an
active first-FULL priority. Preserve the rest of V-01..V-42 scope.

The immediately preceding source-only engineering commit
`d620c67956b95957196e07c121b0bead19a6e844` erroneously removed
original fresh-install consent-based WinGet/npm prerequisite acquisition.
This change **restores the exact original install.ps1 blob** from
`52b17c85fa9e89f6a4f4c9d3a3e8346577b4e3b4`.
Fresh-install requests still require user confirmation per missing
Claude, local PostgreSQL, optional Node and Codex prerequisite; -Update
does not implicitly acquire new packages. Original Git.exe and
Python.exe out-of-band SHA-256 pins, release wheel locking, original
install/update/recovery and early holds are preserved. The older
source note is explicitly marked SUPERSEDED. Original static assertions
and user-facing docs now reflect restored behavior. Tests NOT_RUN.

**Holds unchanged:** LIVE_SCHEMA_048_INCIDENT=OPEN (NO PostgreSQL even
SELECT); HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN (NO native
Claude Code or hooks). Independent #185 positive three-part review and
F1/Fable authority NOT_GRANTED; P3, Git L2, R13 staging, main merging,
native installer, credentials, project modifications and installed P2
remain HELD. No Windows actions or local installation changes made.

Next: focus on one integrated Claude CLI/MCP companion and original
install/update/recovery workflow, with independent review, incident
closure, toolchain/wheelhouse evidence and target-specific operator
approval BEFORE any native testing or deployment.
