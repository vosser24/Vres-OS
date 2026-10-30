# Vres-OS PERSONAL #168 A13 R1 — 32 PASS / EXIT0 Windows selected acceptance (original A13 rejection preserved)

**2026-10-30 Europe/Athens. Repo:** vosser24/Vres-OS. **Source:** user-uploaded big-paste 144-line PowerShell console, not original raw byte-attested Windows log, physical packet capture or native Claude Code review.

## Disposition and identity

**A13_R1_WINDOWS_SELECTED_ACCEPTED** — exactly 32 individually named PASSED, zero failures/skips, `PYTEST_EXIT_CODE=0`, `168_A13_R1_TEST_EXIT_CODE=0`, final `VRES_PERSONAL_168_A13_R1_WINDOWS_SELECTED_TEST_COMPLETE`.

Feature `feature/168-personal-adoption-ancestor-link-fence-a13-20261030`; corrected HEAD **007a51b05d6c0e3d43086a864558fb666853d58d**, tree **1bc85ebbbe2ac4e62dc96aa89c896395b239aef3**, sole original failed A13 parent **cdaa39aaa774cef88a4831bf6b157e380fbb69d9**, tree **59979714d813c6b72a885b33dff13da62bdeef8c**. This descends from accepted A12 R1 **80cee6fe9f0f0dbe55c70d2103e54c1d9bc5b966**, through intermediate `6730da195ba3d4e4bb62841e7c03ee11ec0e004a`, rejected A12 `345a568b551ac23183c54f10611335adee903b96`, accepted A11 `d58db1b5cea0c74040f1d25a219e80e0180c8efd`. One-commit-ahead, zero-behind relative to rejected A13, exactly M `src/vres_os/project_adoption.py` blob **887c0f4e006ee3cac4e14534e38fcf83840deb1c** and M `tests/test_project_adoption_record_ancestors.py` blob **eb8a67704d0c38030ff7d700d2b52ae8d8afb138**.

**Preserved original A13 REJECTION:** exactly **28 PASS / 1 FAILED / exit1**, failing inherited `tests/test_project_adoption_record_read_fence.py::test_parent_junction_is_refused_before_record_open` due to changed diagnostic text; the refusal itself had worked. **Preserved original A12 REJECTION:** **18 PASS / 1 FAIL / exit1**, 1500-depth valid JSON wrongly accepted. Neither original rejected checkout nor failure record was erased.

## Operator preflight, selected tests and posttest evidence

Operator executed canonical ONE-block `docs/handoffs/VRES-168-A13-R1-GUARDED-WINDOWS-SELECTED-TEST-NEXT-2026-10-30.ps1` at immutable blob `cc1d950d082b23dd11c7d7d573243320755f8531`.

Preflight PASS: original clean P2 `C:\Projects\Vres-P2F-Postinstall-Hardening-20261022` exact `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c`; clean accepted A12 R1 worktree `C:\Projects\Vres-ChatGPT-Review-168-Record-Read-A12-R1-20261030` exact HEAD/tree; clean original rejected A12 `C:\Projects\Vres-ChatGPT-Review-168-Record-Read-A12-20261030`; clean original rejected A13 `C:\Projects\Vres-ChatGPT-Review-168-Record-Ancestors-A13-20261030`. Official origin, remote/fetched R1 HEAD, new detached `C:\Projects\Vres-ChatGPT-Review-168-Record-Ancestors-A13-R1-20261030` exact HEAD/tree and complete reviewed ancestry. All **28 pinned protected Git blobs before test**; exactly two MODIFIED file allowlist, `git diff --check` and new worktree clean, `VRES_PERSONAL_168_A13_R1_PREFLIGHT_PASS`.

One Python3.12 `-B -m pytest -q -rA -p no:cacheprovider` guarded selected run: **12** A13 R1 ancestor tests, **16** A12 R1 bounded record-read tests and **four** A11/P2-D/A7 compatibility tests all listed `PASSED`, including the previously rejected immediate-parent-junction diagnostic and three new compatibility boundary cases. `PYTEST_PLUGIN_AUTOLOAD=DISABLED`; process DB/PG/integration environment isolated; disposable protected AppData fixture reported `unexpected refusals=0`, `integration_opt_in=False`; `PYTEST_EXIT_CODE=0`, `PASS: PROCESS_ENVIRONMENT_RESTORED`. Post-test correct HEAD/tree, **all 28 protected Git blobs**, clean R1/rejected A12/rejected A13/accepted A12 R1 checkouts PASS, `168_A13_R1_TEST_EXIT_CODE=0` and final completion marker present. Return to PT2D PowerShell prompt was due to restoring shell directory, not actual test execution in PT2D.

## Scope and still-open holds

A13 R1 inspects every ancestor via lstat before/after bounded adoption record reads, denies unsafe links/junctions/special ancestors or simple detected replacements and preserves A12's error for the immediate parent. No atomic directory-handle traversal; NOT proven safe against every TOCTOU race or a substitute for cryptographic consent. No installed Vres, real legacy project, native Claude, Fable/high positive issuance, live DB or network behavior tested.

**LIVE_SCHEMA_048_INCIDENT=OPEN — NO PostgreSQL even SELECT. HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN**, seven historical refused native Claude Code Read/Grep post-tool database routes; source Hook-R1 Windows 34 PASS does not clear installed/managed/global/lifecycle hooks. Native independent A13 R1 review NOT_RUN. Prior Claude `--safe-mode` UI from PT2D was not independent review or installed Vres Chairman model change. Positive F1/real Fable approval still held. No merge, PR, product main, installation, credential/global Claude or release change.

All history remains: PERSONAL P0–P3, PT1/PT2A–D, Hook-R1, #168 A1–A13 accepted/rejected/skip states, full V-01..V-42, #165–170, #174, #176 E7/E8, #166 Claude/PRISM, #167 single-user data registry, #169 Visual Studio real legacy and #170 go-live. Next smallest useful offline source increment on accepted R1 SHA with fresh branch and targeted tests, operator ONE full self-contained SHA-pinned Windows PowerShell block, complete test evidence, docs acceptance; no repeated full tests, normal native Claude review or DB contact.
