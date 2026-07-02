# Runbook: Email Issue

**Category:** Email Issue
**Auto-resolvable:** No — recommend (guided troubleshooting)
**Typical priority:** High

## Symptoms
- Outlook shows "Disconnected"; mail stuck in Outbox.
- Cannot send or receive email while webmail works.

## Root Causes
- Corrupt Outlook profile or OST cache.
- Cached Exchange Mode connectivity issue.
- Large mailbox or corrupt local data file.

## Resolution Steps (Recommended)
1. Confirm webmail works (isolates client vs. server).
2. Restart Outlook; test Online vs. Cached Exchange Mode.
3. Repair or recreate the Outlook profile.
4. Rebuild the OST file if corrupt.
5. Verify send/receive is restored.

## Automated Action
- None by default (client-side, user machine access needed).

## Verification
- User can send and receive email in Outlook.
