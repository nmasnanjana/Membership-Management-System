"""
Django signals for automatic member deactivation
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import MemberAttendance
from .utils import check_and_deactivate_inactive_members
from .constants import CONSECUTIVE_MEETINGS_FOR_DEACTIVATION


# Cache key to prevent running the check too frequently
CACHE_KEY_DEACTIVATION_CHECK = 'last_deactivation_check'
CACHE_TIMEOUT = 300  # 5 minutes - prevents running check more than once per 5 minutes


@receiver(post_save, sender=MemberAttendance)
def auto_deactivate_inactive_members(sender, instance, created, **kwargs):
    """
    Automatically check and deactivate members who missed 3 consecutive meetings
    after attendance is saved.
    
    This runs in the background automatically without needing cron jobs.
    Uses caching to prevent running too frequently.
    
    Works in shared hosting/cPanel environments - no cron jobs needed!
    """
    try:
        # Check cache to prevent running too frequently
        # If cache is not available, it will return None and proceed
        cache_value = None
        try:
            cache_value = cache.get(CACHE_KEY_DEACTIVATION_CHECK)
        except Exception:
            # Cache might not be configured - continue anyway
            pass
        
        if cache_value:
            return
        
        # Run the deactivation check
        result = check_and_deactivate_inactive_members(
            consecutive_meetings=CONSECUTIVE_MEETINGS_FOR_DEACTIVATION,
            dry_run=False
        )
        
        # Set cache to prevent running again for 5 minutes
        try:
            cache.set(CACHE_KEY_DEACTIVATION_CHECK, True, CACHE_TIMEOUT)
        except Exception:
            # If cache fails, continue anyway
            pass
        
        # Log if members were deactivated (optional - can be removed if not needed)
        if result['deactivated_count'] > 0:
            # You can add logging here if needed
            pass
            
    except Exception:
        # Silently fail to not interrupt the attendance saving process
        # This ensures attendance saving always works, even if deactivation check fails
        pass

