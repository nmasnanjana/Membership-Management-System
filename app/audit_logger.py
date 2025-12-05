"""
Audit logging utility for JSON-formatted audit logs
Captures comprehensive audit information for all system actions
"""
import json
import logging
from datetime import datetime
from django.utils import timezone


class JSONAuditFormatter(logging.Formatter):
    """
    Custom JSON formatter for audit logs
    Formats log records as JSON with all required audit information
    """
    def format(self, record):
        # Extract audit data from record
        audit_data = {
            'severity': record.levelname,
            'timestamp': timezone.now().isoformat(),
            'who': getattr(record, 'audit_user', 'anonymous'),
            'action': getattr(record, 'audit_action', 'unknown'),
            'target': getattr(record, 'audit_target', None),
            'source': {
                'ip_address': getattr(record, 'audit_ip', 'unknown'),
                'user_agent': getattr(record, 'audit_user_agent', 'unknown'),
            },
            'request': {
                'endpoint': getattr(record, 'audit_endpoint', 'unknown'),
                'method': getattr(record, 'audit_method', 'unknown'),
                'path': getattr(record, 'audit_path', 'unknown'),
            },
            'details': {
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
            }
        }
        
        # Add additional context if available
        if hasattr(record, 'audit_extra'):
            audit_data['details'].update(record.audit_extra)
        
        # Add exception info if present
        if record.exc_info:
            audit_data['details']['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(audit_data, ensure_ascii=False)


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


def get_user_agent(request):
    """Extract user agent from request"""
    return request.META.get('HTTP_USER_AGENT', 'unknown')


def get_username(request):
    """Safely extract username from request"""
    user = getattr(request, 'user', None)
    if user and hasattr(user, 'is_authenticated') and user.is_authenticated:
        return getattr(user, 'username', 'unknown')
    return 'anonymous'


def audit_log(
    request,
    action,
    severity='INFO',
    target=None,
    extra_details=None
):
    """
    Create an audit log entry with comprehensive information
    
    Args:
        request: Django request object
        action: Description of what was done (e.g., 'member_created', 'attendance_marked')
        severity: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        target: Target of the action (e.g., member_id, meeting_id, 'user:username')
        extra_details: Additional details to include in the log
    """
    logger = logging.getLogger('audit')
    
    # Extract audit information
    username = get_username(request)
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    endpoint = request.path
    method = request.method
    full_path = request.get_full_path()
    
    # Create log record with audit information
    log_record = logger.makeRecord(
        name='audit',
        level=getattr(logging, severity.upper(), logging.INFO),
        fn='',
        lno=0,
        msg=action,
        args=(),
        exc_info=None
    )
    
    # Add audit-specific attributes
    log_record.audit_user = username
    log_record.audit_action = action
    log_record.audit_target = target
    log_record.audit_ip = ip_address
    log_record.audit_user_agent = user_agent
    log_record.audit_endpoint = endpoint
    log_record.audit_method = method
    log_record.audit_path = full_path
    log_record.audit_extra = extra_details or {}
    
    # Log the record
    logger.handle(log_record)


def audit_log_security_event(
    request,
    event_type,
    severity='WARNING',
    target=None,
    extra_details=None
):
    """
    Create a security-specific audit log entry
    
    Args:
        request: Django request object
        event_type: Type of security event (e.g., 'failed_login', 'rate_limit_exceeded')
        severity: Log level (typically WARNING or ERROR for security events)
        target: Target of the event
        extra_details: Additional security-related details
    """
    audit_log(
        request=request,
        action=f'security_event:{event_type}',
        severity=severity,
        target=target,
        extra_details=extra_details
    )


def audit_log_user_action(
    request,
    action,
    target=None,
    extra_details=None
):
    """
    Create an audit log entry for user actions
    
    Args:
        request: Django request object
        action: User action (e.g., 'member_created', 'attendance_deleted')
        target: Target of the action
        extra_details: Additional details
    """
    audit_log(
        request=request,
        action=action,
        severity='INFO',
        target=target,
        extra_details=extra_details
    )

