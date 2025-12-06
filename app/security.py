"""
Security utilities and middleware for OWASP Top 10 protection
"""
import time
from django.core.cache import cache
from django.http import HttpResponseForbidden, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging
from .audit_logger import audit_log_security_event

logger = logging.getLogger('security')


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses
    OWASP: Security Misconfiguration, Insecure Design
    """
    def process_response(self, request, response):
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://ajax.googleapis.com https://code.jquery.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net data:; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response['Content-Security-Policy'] = csp
        
        # Cache-Control headers for development (disable caching)
        if settings.DEBUG:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        else:
            # In production, cache static files but not HTML
            if not request.path.startswith('/static/') and not request.path.startswith('/media/'):
                response['Cache-Control'] = 'no-cache, must-revalidate'
        
        # Strict Transport Security (HSTS) - only in production
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # X-Frame-Options
        response['X-Frame-Options'] = 'DENY'
        
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-XSS-Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), '
            'payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()'
        )
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware
    OWASP: Identification and Authentication Failures
    """
    def process_request(self, request):
        # Skip rate limiting for static files and admin
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return None
        
        # Different rate limits for different endpoints
        rate_limits = {
            '/login/': (5, 300),  # 5 attempts per 5 minutes
            '/staff/register/': (3, 600),  # 3 attempts per 10 minutes
            '/member/register/': (10, 60),  # 10 attempts per minute
            '/attendance/mark/': (20, 60),  # 20 attempts per minute
        }
        
        for path, (max_requests, window) in rate_limits.items():
            if request.path.startswith(path):
                ip_address = self.get_client_ip(request)
                cache_key = f'rate_limit:{path}:{ip_address}'
                
                # Get current count
                current_count = cache.get(cache_key, 0)
                
                if current_count >= max_requests:
                    # Log using audit logger
                    audit_log_security_event(
                        request=request,
                        event_type='rate_limit_exceeded',
                        severity='WARNING',
                        target=path,
                        extra_details={
                            'ip_address': ip_address,
                            'max_requests': max_requests,
                            'window_seconds': window,
                        }
                    )
                    logger.warning(f'Rate limit exceeded for {ip_address} on {path}')
                    return HttpResponseForbidden(
                        'Too many requests. Please try again later.',
                        content_type='text/plain'
                    )
                
                # Increment counter
                cache.set(cache_key, current_count + 1, window)
                break
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityLoggingMiddleware(MiddlewareMixin):
    """
    Security event logging
    OWASP: Security Logging and Monitoring Failures
    Now uses JSON audit logging
    """
    def process_request(self, request):
        # Log sensitive operations
        sensitive_paths = {
            '/login/': 'login_attempt',
            '/logout/': 'logout',
            '/staff/register/': 'staff_registration',
            '/member/delete/': 'member_deletion',
            '/staff/delete/': 'staff_deletion',
            '/meeting/delete/': 'meeting_deletion',
            '/attendance/delete/': 'attendance_deletion',
            '/staff/password/reset/': 'password_reset',
            '/staff/password/change/': 'password_change'
        }
        
        for path, action in sensitive_paths.items():
            if request.path.startswith(path):
                audit_log_security_event(
                    request=request,
                    event_type=action,
                    severity='INFO',
                    target=path,
                    extra_details={
                        'http_method': request.method,
                    }
                )
                break
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def check_account_lockout(username, max_attempts=5, lockout_duration=900):
    """
    Check if account is locked out due to failed login attempts
    OWASP: Identification and Authentication Failures
    """
    cache_key = f'login_attempts:{username}'
    attempts = cache.get(cache_key, 0)
    
    if attempts >= max_attempts:
        lockout_key = f'account_locked:{username}'
        if cache.get(lockout_key):
            return True, cache.ttl(lockout_key)
        else:
            # Lock the account
            cache.set(lockout_key, True, lockout_duration)
            # Note: audit_log_security_event requires request object, so we'll log via logger
            # The audit middleware will capture this as part of the request flow
            logger.warning(f'Account locked: {username} after {attempts} failed attempts')
            return True, lockout_duration
    
    return False, 0


def record_failed_login(username):
    """Record a failed login attempt"""
    cache_key = f'login_attempts:{username}'
    attempts = cache.get(cache_key, 0)
    cache.set(cache_key, attempts + 1, 900)  # 15 minutes
    logger.warning(f'Failed login attempt for user: {username} (attempt {attempts + 1})')


def clear_login_attempts(username):
    """Clear failed login attempts on successful login"""
    cache_key = f'login_attempts:{username}'
    lockout_key = f'account_locked:{username}'
    cache.delete(cache_key)
    cache.delete(lockout_key)

