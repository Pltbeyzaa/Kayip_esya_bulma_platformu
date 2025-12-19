"""
Context processors for global template variables
"""
from django.conf import settings


def firebase_config(request):
    """Firebase configuration for templates"""
    return {
        'FIREBASE_API_KEY': getattr(settings, 'FIREBASE_API_KEY', ''),
        'FIREBASE_AUTH_DOMAIN': getattr(settings, 'FIREBASE_AUTH_DOMAIN', ''),
        'FIREBASE_DATABASE_URL': getattr(settings, 'FIREBASE_DATABASE_URL', ''),
        'FIREBASE_PROJECT_ID': getattr(settings, 'FIREBASE_PROJECT_ID', ''),
        'FIREBASE_STORAGE_BUCKET': getattr(settings, 'FIREBASE_STORAGE_BUCKET', ''),
        'FIREBASE_MESSAGING_SENDER_ID': getattr(settings, 'FIREBASE_MESSAGING_SENDER_ID', ''),
        'FIREBASE_APP_ID': getattr(settings, 'FIREBASE_APP_ID', ''),
    }
