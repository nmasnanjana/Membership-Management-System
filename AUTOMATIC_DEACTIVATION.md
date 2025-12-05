# Automatic Member Deactivation

## Overview

The system **automatically** deactivates members who have not attended 3 consecutive meetings. This helps maintain an accurate list of active members and ensures that inactive members are not counted in statistics.

**✨ Works automatically in shared hosting/cPanel - NO cron jobs needed!**

## How It Works

1. **Default Behavior**: All new members are created as active (`member_is_active = True`)
2. **Deactivation Rule**: If a member misses 3 consecutive meetings (the latest 3 meetings in the system), they are automatically deactivated
3. **Meeting Order**: The system checks the latest meetings ordered by date (newest first)
4. **Attendance Check**: A member is considered to have missed a meeting if:
   - They have no attendance record for that meeting, OR
   - Their attendance record shows `attendance_status = False` (absent)

## Automatic Execution (Built-in)

The system automatically checks and deactivates members in the background:

1. **After Attendance is Saved**: When you mark attendance for any member, the system automatically checks if any members need to be deactivated (via Django signals)
2. **When Dashboard is Viewed**: As a backup, the system also checks when admins view the dashboard
3. **No Manual Action Required**: Everything happens automatically - perfect for shared hosting/cPanel environments!

### How Automatic Execution Works

- **Django Signals**: After every attendance record is saved, a signal automatically triggers the deactivation check
- **Caching**: Uses intelligent caching to prevent running the check too frequently (once per 5 minutes after attendance saves, once per hour on dashboard)
- **Silent Operation**: Runs in the background without interrupting normal operations
- **No Cron Jobs Needed**: Works perfectly in shared hosting environments with only cPanel access

## Manual Execution (Optional)

You can also run the management command manually if needed:

```bash
# Check and deactivate members (default: 3 consecutive meetings)
python manage.py deactivate_inactive_members

# Dry run - see what would happen without actually deactivating
python manage.py deactivate_inactive_members --dry-run

# Custom number of consecutive meetings
python manage.py deactivate_inactive_members --consecutive-meetings 5
```

### For Advanced Users (Optional Cron Setup)

If you want additional scheduled checks (optional, not required):

```bash
# Add to crontab (runs daily at 2 AM)
0 2 * * * cd /path/to/project && /path/to/venv/bin/python manage.py deactivate_inactive_members
```

## Configuration

The number of consecutive meetings required for deactivation can be configured in `app/constants.py`:

```python
CONSECUTIVE_MEETINGS_FOR_DEACTIVATION = 3  # Change this value as needed
```

## Programmatic Usage

You can also call the utility function directly from your code:

```python
from app.utils import check_and_deactivate_inactive_members

# Check and deactivate (default: 3 meetings)
result = check_and_deactivate_inactive_members()

# Custom number of meetings
result = check_and_deactivate_inactive_members(consecutive_meetings=5)

# Dry run (returns list without deactivating)
result = check_and_deactivate_inactive_members(dry_run=True)

# Result structure:
# {
#     'deactivated_count': int,
#     'deactivated_members': list of Member objects,
#     'message': str
# }
```

## Example Scenarios

### Scenario 1: Member Misses 3 Consecutive Meetings
- Meeting 1 (2025-12-01): Member absent
- Meeting 2 (2025-12-08): Member absent
- Meeting 3 (2025-12-15): Member absent
- **Result**: Member is deactivated

### Scenario 2: Member Attends One Meeting
- Meeting 1 (2025-12-01): Member absent
- Meeting 2 (2025-12-08): Member present ✓
- Meeting 3 (2025-12-15): Member absent
- **Result**: Member remains active (attended meeting 2)

### Scenario 3: Not Enough Meetings
- Only 2 meetings exist in the system
- **Result**: No members are deactivated (need at least 3 meetings)

## Reactivating Members

To reactivate a deactivated member, you can:

1. **Via Admin Panel**: Edit the member and set `member_is_active = True`
2. **Via Code**:
   ```python
   from app.models import Member
   member = Member.objects.get(member_id='1234')
   member.member_is_active = True
   member.save()
   ```

## Notes

- Deactivation is automatic and permanent until manually reactivated
- The check is based on the latest N meetings, not a time period
- Members who are already inactive are not checked
- The system requires at least N meetings to exist before checking

## Troubleshooting

**Command not found?**
- Make sure you're in the project directory
- Ensure your virtual environment is activated
- Check that the management command file exists: `app/management/commands/deactivate_inactive_members.py`

**No members being deactivated?**
- Check if you have at least 3 meetings in the system
- Verify that members actually missed 3 consecutive meetings
- Use `--dry-run` to see what would happen

**Members deactivated incorrectly?**
- Review the attendance records for those members
- Check the meeting dates to ensure they are ordered correctly
- Manually reactivate members if needed

