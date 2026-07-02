# Runbook: Disk Space Cleanup

**Category:** Disk Space Cleanup
**Auto-resolvable:** Yes
**Typical priority:** Medium

## Symptoms
- "Low Disk Space" warning on the C: drive.
- Cannot save files or install updates.
- Very little free space remaining.

## Root Causes
- Accumulated temporary files, cache, and Windows Update leftovers.
- Large files in Downloads / Recycle Bin.
- Old user profile or log files.

## Resolution Steps
1. Run Disk Cleanup / Storage Sense to remove temporary files.
2. Clear `%TEMP%`, browser caches, and the Recycle Bin.
3. Remove old Windows Update cache (`SoftwareDistribution\Download`).
4. Identify large files with a disk usage scan; advise the user on removals.
5. Confirm at least 10% free space is restored.

## Automated Action
- `cleanup_disk(user_id)` — safely clears temp files, caches, and recycle bin.

## Verification
- Free space is above the safe threshold and warnings stop.
