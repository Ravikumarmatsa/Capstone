# Runbook: Access Request

**Category:** Access Request
**Auto-resolvable:** No — always requires human approval
**Typical priority:** Medium

## Symptoms
- User requests new or elevated access to a shared folder, application, or system.
- Requests for admin rights, write access, or role changes.

## Root Causes
- Legitimate business need (new role, new project).
- Onboarding / role change.

## Why Not Auto-Resolved
Access changes affect security posture and often need **manager or data-owner
approval** and separation-of-duties checks. The agent must **recommend**, never
auto-grant.

## Resolution Steps (Recommended to Human Agent)
1. Verify the requester's identity and current access level.
2. Identify the resource owner / approving manager.
3. Route the request for approval (ticket comment + assignment).
4. On approval, grant the minimum access required (least privilege).
5. Record the approval and set an access review/expiry date.
6. Confirm access with the user.

## Automated Action
- None. The Execution Agent posts recommended steps and assigns to a human.

## Verification
- Access granted only after documented approval.
