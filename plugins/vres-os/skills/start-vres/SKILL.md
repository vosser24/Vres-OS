---
name: start-vres
description: Use when the user says "start vres", asks to initialize Vres-OS, or wants to activate persistent Vres capabilities in the current project.
---

Call the Vres MCP `start_vres` tool for the current project.

If setup is required, explain that Vres will open a separate secure local setup window so database passwords do not pass through the model conversation. Do not ask the user to paste secrets into chat.

When READY:
- state that Vres is active for the project;
- do not dump configuration details unless requested;
- continue naturally with the user's actual work.
