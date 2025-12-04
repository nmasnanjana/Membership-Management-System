"""
Utility functions for the Membership Management System
"""
import os
import qrcode
from django.conf import settings


def generate_qr_code(member_id):
    """
    Generate QR code for a member and save it to the media directory.
    
    Args:
        member_id: The member ID to encode in the QR code
        
    Returns:
        str: Relative path to the saved QR code image
    """
    profile_picture_directory = os.path.join(settings.MEDIA_ROOT, 'profiles', member_id)
    os.makedirs(profile_picture_directory, exist_ok=True)
    
    qr_code = qrcode.make(member_id)
    qr_code_name = f"{member_id}_qr.png"
    qr_code_path = os.path.join(profile_picture_directory, qr_code_name)
    
    qr_code.save(qr_code_path)
    
    return os.path.relpath(qr_code_path, settings.MEDIA_ROOT)

