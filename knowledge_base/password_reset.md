# Runbook: Password Reset

**Category:** Password Reset
**Auto-resolvable:** Yes
**Typical priority:** High

## Symptoms
- User forgot their password.
- "Incorrect password" or lockout after failed login attempts.
- Cannot access Windows account, email, or corporate portal.

## Root Causes
- Forgotten credentials (common after leave/vacation).
- Password expired per policy.
- Account locked due to repeated failed attempts.

## Resolution Steps
1. Verify the user's identity (employee ID + security question / manager confirmation).
2. In Active Directory / IAM, locate the user account.
3. Reset the password to a secure temporary value and set "must change at next logon".
4. If the account is locked, unlock it.
5. Send the temporary password through a secure channel (SMS / secondary email).
6. Confirm the user can log in and change the password.

## Automated Action
- `reset_password(user_id)` — resets password and clears lockout flag.

## Verification
- User successfully signs in and sets a new password.
