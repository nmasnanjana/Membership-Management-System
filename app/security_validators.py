"""
Security validators for file uploads and input validation
OWASP: Injection, Insecure Design, Software and Data Integrity Failures
"""
import os
from django.core.exceptions import ValidationError
from django.conf import settings
from .constants import MAX_IMAGE_SIZE, ALLOWED_IMAGE_EXTENSIONS

# Try to import magic for MIME type validation (optional)
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


def validate_file_upload(file, max_size=MAX_IMAGE_SIZE, allowed_extensions=ALLOWED_IMAGE_EXTENSIONS):
    """
    Comprehensive file upload validation
    OWASP: Injection, Software and Data Integrity Failures
    """
    errors = []
    
    # Check file exists
    if not file:
        raise ValidationError('No file provided.')
    
    # Check file size
    if file.size > max_size:
        raise ValidationError(f'File size exceeds maximum allowed size of {max_size // (1024*1024)}MB.')
    
    # Check file extension
    file_name = file.name.lower()
    _, file_extension = os.path.splitext(file_name)
    
    if file_extension not in allowed_extensions:
        raise ValidationError(
            f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}'
        )
    
    # Validate file content using magic bytes (MIME type checking)
    # This prevents file extension spoofing
    try:
        file.seek(0)
        file_content = file.read(1024)  # Read first 1KB for MIME detection
        file.seek(0)  # Reset file pointer
        
        # Use python-magic if available, otherwise fallback to extension check
        if HAS_MAGIC:
            try:
                mime_type = magic.from_buffer(file_content, mime=True)
                
                # Allowed MIME types for images
                allowed_mime_types = [
                    'image/jpeg',
                    'image/jpg',
                    'image/png',
                    'image/gif'
                ]
                
                if mime_type not in allowed_mime_types:
                    raise ValidationError(
                        f'Invalid file content. File does not match declared type. '
                        f'Detected MIME type: {mime_type}'
                    )
            except Exception as e:
                # If magic fails, log but don't block (graceful degradation)
                import logging
                logger = logging.getLogger('security')
                logger.warning(f'MIME type validation failed: {str(e)}')
    
    # Check for dangerous file names
    dangerous_patterns = ['..', '/', '\\', '\x00']
    for pattern in dangerous_patterns:
        if pattern in file_name:
            raise ValidationError('File name contains invalid characters.')
    
    # Check file name length
    if len(file_name) > 255:
        raise ValidationError('File name is too long.')
    
    return True


def sanitize_filename(filename):
    """
    Sanitize file name to prevent path traversal and injection
    OWASP: Injection
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    dangerous_chars = ['..', '/', '\\', '\x00', '<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename


def validate_input_length(value, field_name, max_length, min_length=0):
    """
    Validate input length to prevent buffer overflow attacks
    OWASP: Injection
    """
    if value is None:
        return True
    
    value_str = str(value)
    
    if len(value_str) < min_length:
        raise ValidationError(f'{field_name} must be at least {min_length} characters long.')
    
    if len(value_str) > max_length:
        raise ValidationError(f'{field_name} must not exceed {max_length} characters.')
    
    return True


def validate_no_sql_injection(value):
    """
    Basic SQL injection pattern detection
    Note: Django ORM already protects against SQL injection,
    but this adds an extra layer for user input validation
    OWASP: Injection
    """
    if not value:
        return True
    
    value_str = str(value).lower()
    
    # Common SQL injection patterns
    dangerous_patterns = [
        'union select',
        'drop table',
        'delete from',
        'insert into',
        'update set',
        'exec(',
        'execute(',
        '--',
        ';--',
        '/*',
        '*/',
        'xp_',
        'sp_',
    ]
    
    for pattern in dangerous_patterns:
        if pattern in value_str:
            import logging
            logger = logging.getLogger('security')
            logger.warning(f'Potential SQL injection pattern detected: {pattern} in input')
            raise ValidationError('Invalid characters detected in input.')
    
    return True


def validate_no_xss(value):
    """
    Basic XSS pattern detection
    OWASP: Injection
    """
    if not value:
        return True
    
    value_str = str(value).lower()
    
    # Common XSS patterns
    dangerous_patterns = [
        '<script',
        '</script>',
        'javascript:',
        'onerror=',
        'onload=',
        'onclick=',
        'onmouseover=',
        '<iframe',
        '<object',
        '<embed',
        'eval(',
        'expression(',
    ]
    
    for pattern in dangerous_patterns:
        if pattern in value_str:
            import logging
            logger = logging.getLogger('security')
            logger.warning(f'Potential XSS pattern detected: {pattern} in input')
            raise ValidationError('Invalid characters detected in input.')
    
    return True

