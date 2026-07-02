# Runbook: VPN Connectivity

**Category:** VPN Connectivity
**Auto-resolvable:** Yes
**Typical priority:** High

## Symptoms
- VPN client connects then disconnects repeatedly.
- Cannot reach internal applications while remote.
- Authentication succeeds but the tunnel drops.

## Root Causes
- Stale or corrupt VPN session token after a restart.
- Outdated VPN client version.
- Local network MTU / Wi-Fi instability.
- Duplicate active sessions on the VPN concentrator.

## Resolution Steps
1. Ask the user to fully quit the VPN client (not just disconnect).
2. On the VPN concentrator, terminate any stale sessions for the user.
3. Clear the cached VPN profile / token on the client.
4. Ensure the VPN client is on the approved latest version; update if needed.
5. Reconnect and confirm the tunnel is stable for 5+ minutes.
6. If unstable, switch network (e.g., mobile hotspot) to isolate local Wi-Fi issues.

## Automated Action
- `reset_vpn_session(user_id)` — clears stale server-side sessions and cached token.

## Verification
- User maintains a stable VPN connection and reaches an internal test URL.
