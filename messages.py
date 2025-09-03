"""
Elegant Error Message System for CUR8tr
Provides user-friendly, contextual error messages with consistent styling
"""

from flask import flash
from typing import Dict, Any, Optional

class MessageType:
    """Message type constants for consistent styling"""
    ERROR = 'error'
    WARNING = 'warning' 
    SUCCESS = 'success'
    INFO = 'info'

class UserMessages:
    """Centralized, user-friendly message system"""
    
    # Authentication Messages
    AUTH_MESSAGES = {
        'login_success': ("Welcome back! You're now signed in.", MessageType.SUCCESS),
        'login_invalid_credentials': ("We couldn't find an account with those details. Please check your username and password.", MessageType.ERROR),
        'login_user_not_found': ("We don't recognize that username. Double-check the spelling or create a new account.", MessageType.ERROR),
        'login_wrong_password': ("That password doesn't match our records. Give it another try!", MessageType.ERROR),
        'login_unverified': ("Please check your email and verify your account before signing in.", MessageType.WARNING),
        'logout_success': ("You've been safely signed out. See you next time!", MessageType.SUCCESS),
        'access_denied': ("Please sign in to continue.", MessageType.WARNING),
    }
    
    # Registration Messages
    REGISTRATION_MESSAGES = {
        'register_success': ("Great! Check your email for a verification code to complete your account.", MessageType.SUCCESS),
        'register_username_taken': ("That username is already taken. Try something unique that represents you!", MessageType.ERROR),
        'register_email_taken': ("An account with this email already exists. Try signing in instead?", MessageType.ERROR),
        'register_weak_password': ("Your password needs to be stronger. Try using a mix of letters, numbers, and symbols.", MessageType.WARNING),
        'verify_success': ("Account verified! Welcome to CUR8tr - let's start building your recommendation profile.", MessageType.SUCCESS),
        'verify_invalid_code': ("That verification code doesn't match. Check your email and try again.", MessageType.ERROR),
        'verify_expired': ("Your verification code expired. We've sent you a fresh one!", MessageType.WARNING),
    }
    
    # Profile & Content Messages
    CONTENT_MESSAGES = {
        'profile_updated': ("Your profile looks great! Changes have been saved.", MessageType.SUCCESS),
        'profile_image_too_large': ("That image is a bit too large. Please choose one under 5MB.", MessageType.WARNING),
        'profile_image_invalid': ("We couldn't process that image. Try a JPG or PNG file instead.", MessageType.ERROR),
        'recommendation_added': ("Recommendation added! Your followers will love this suggestion.", MessageType.SUCCESS),
        'recommendation_updated': ("Changes saved! Your recommendation has been updated.", MessageType.SUCCESS),
        'recommendation_deleted': ("Recommendation removed from your profile.", MessageType.INFO),
        'category_created': ("New category created! Start adding recommendations to fill it out.", MessageType.SUCCESS),
        'category_deleted': ("Category removed along with all its recommendations.", MessageType.INFO),
        'permission_denied': ("You can only edit your own content.", MessageType.ERROR),
    }
    
    # Social Features Messages  
    SOCIAL_MESSAGES = {
        'follow_success': ("You're now following their recommendations!", MessageType.SUCCESS),
        'unfollow_success': ("No longer following this profile.", MessageType.INFO),
        'like_added': ("Nice choice! Your like has been added.", MessageType.SUCCESS),
        'like_removed': ("Like removed.", MessageType.INFO),
        'comment_added': ("Comment posted! Others will see your thoughts.", MessageType.SUCCESS),
        'comment_deleted': ("Comment removed.", MessageType.INFO),
        'comment_permission_denied': ("You can only delete your own comments.", MessageType.ERROR),
    }
    
    # System Messages
    SYSTEM_MESSAGES = {
        'form_validation_error': ("Please check the highlighted fields and try again.", MessageType.ERROR),
        'network_error': ("Something went wrong. Please try again in a moment.", MessageType.ERROR),
        'file_upload_error': ("File upload failed. Check your connection and try again.", MessageType.ERROR),
        'session_expired': ("Your session expired. Please sign in again.", MessageType.WARNING),
        'maintenance_mode': ("We're making some improvements! Please try again shortly.", MessageType.INFO),
    }
    
    @classmethod
    def get_all_messages(cls) -> Dict[str, tuple]:
        """Get all message definitions"""
        all_messages = {}
        all_messages.update(cls.AUTH_MESSAGES)
        all_messages.update(cls.REGISTRATION_MESSAGES)
        all_messages.update(cls.CONTENT_MESSAGES)
        all_messages.update(cls.SOCIAL_MESSAGES)
        all_messages.update(cls.SYSTEM_MESSAGES)
        return all_messages
    
    @classmethod
    def flash_message(cls, message_key: str, **kwargs) -> bool:
        """Flash a predefined user-friendly message"""
        all_messages = cls.get_all_messages()
        
        if message_key not in all_messages:
            # Fallback for undefined messages
            flash("Something unexpected happened. Please try again.", MessageType.ERROR)
            return False
            
        message_text, message_type = all_messages[message_key]
        
        # Support dynamic message formatting
        try:
            formatted_message = message_text.format(**kwargs)
        except (KeyError, ValueError):
            formatted_message = message_text
            
        flash(formatted_message, message_type)
        return True
    
    @classmethod
    def custom_flash(cls, message: str, message_type: str = MessageType.INFO):
        """Flash a custom message with consistent styling"""
        flash(message, message_type)

# Convenience functions for common operations
def flash_success(message: str):
    """Flash a success message"""
    UserMessages.custom_flash(message, MessageType.SUCCESS)

def flash_error(message: str):
    """Flash an error message"""
    UserMessages.custom_flash(message, MessageType.ERROR)

def flash_warning(message: str):
    """Flash a warning message"""
    UserMessages.custom_flash(message, MessageType.WARNING)

def flash_info(message: str):
    """Flash an info message"""
    UserMessages.custom_flash(message, MessageType.INFO)

# Quick access to predefined messages
def flash_auth(message_key: str, **kwargs):
    """Flash authentication-related messages"""
    return UserMessages.flash_message(message_key, **kwargs)

def flash_content(message_key: str, **kwargs):
    """Flash content-related messages"""
    return UserMessages.flash_message(message_key, **kwargs)

def flash_social(message_key: str, **kwargs):
    """Flash social feature messages"""
    return UserMessages.flash_message(message_key, **kwargs)