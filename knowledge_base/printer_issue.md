# Runbook: Printer Issue

**Category:** Printer Issue
**Auto-resolvable:** No — recommend (may need on-site check)
**Typical priority:** Medium

## Symptoms
- Printer shows "offline" for one or more users.
- Print jobs queue but do not print.
- Printer displays "Ready" but nothing prints.

## Root Causes
- Stuck print spooler on the print server.
- Stale print queue / held jobs.
- Network/IP change on the printer.

## Resolution Steps (Recommended)
1. Verify the printer is powered on and network-reachable (ping the IP).
2. On the print server, clear the stuck queue for the printer.
3. Restart the Print Spooler service.
4. Re-share / reconnect the printer if the IP changed.
5. Send a test print to confirm.

## Automated Action
- Optional future action: `restart_print_spooler(printer_id)` after validation.

## Verification
- Queued jobs print and the printer shows online.
