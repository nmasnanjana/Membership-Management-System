"""
Audit logging middleware
Captures all HTTP requests and logs them as JSON audit logs
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from .audit_logger import audit_log, get_client_ip, get_user_agent, get_username


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all HTTP requests as JSON audit logs
    Logs to console (stdout) for Docker container logs
    """
    
    # Paths to exclude from audit logging (static files, media, etc.)
    EXCLUDED_PATHS = [
        '/static/',
        '/media/',
        '/favicon.ico',
    ]
    
    # Paths that should be logged at DEBUG level (less critical)
    DEBUG_PATHS = [
        '/',
        '/dashboard/',
    ]
    
    def process_request(self, request):
        """Log incoming request"""
        # Skip excluded paths
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return None
        
        # Determine log level based on path
        log_level = 'DEBUG' if any(request.path.startswith(path) for path in self.DEBUG_PATHS) else 'INFO'
        
        # Log the request
        audit_log(
            request=request,
            action='http_request',
            severity=log_level,
            target=None,
            extra_details={
                'query_params': dict(request.GET),
                'content_type': request.content_type,
            }
        )
        
        return None
    
    def process_response(self, request, response):
        """Log response status for important requests"""
        # Skip excluded paths
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return response
        
        # Log error responses
        if response.status_code >= 400:
            severity = 'ERROR' if response.status_code >= 500 else 'WARNING'
            audit_log(
                request=request,
                action=f'http_response_error',
                severity=severity,
                target=None,
                extra_details={
                    'status_code': response.status_code,
                    'status_text': response.reason_phrase,
                }
            )
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions"""
        try:
            audit_log(
                request=request,
                action='exception_occurred',
                severity='ERROR',
                target=None,
                extra_details={
                    'exception_type': type(exception).__name__,
                    'exception_message': str(exception),
                }
            )
        except Exception:
            # Don't let logging errors break the application
            pass
        return None

