# Runbook: Software Installation

**Category:** Software Installation
**Auto-resolvable:** No — recommend (may need licensing / admin rights)
**Typical priority:** Low

## Symptoms
- User requests installation of an application (e.g., Node.js, VS Code, Office add-in).
- New-hire onboarding toolset requests.

## Root Causes
- New role or project requiring specific tools.
- Missing standard software on a fresh machine.

## Why Not Auto-Resolved
Installations may require **admin rights**, **license allocation**, and
**software-approval policy** checks. The agent recommends and routes for action.

## Resolution Steps (Recommended)
1. Confirm the software is on the approved catalog.
2. Verify license availability (if commercial).
3. Deploy via the software distribution tool (e.g., SCCM / Intune) or schedule a technician.
4. For standard free tools, push the packaged installer.
5. Verify the application launches and is correctly configured.

## Automated Action
- None by default. Optionally push pre-approved catalog apps in a future iteration.

## Verification
- Requested software installed and launches successfully.
