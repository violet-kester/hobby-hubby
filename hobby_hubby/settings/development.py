"""
Development settings for hobby_hubby project.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Development apps - Debug toolbar temporarily disabled to prevent URL conflicts
# INSTALLED_APPS += [
#     'debug_toolbar',
# ]

# MIDDLEWARE += [
#     'debug_toolbar.middleware.DebugToolbarMiddleware',
# ]

# Debug toolbar
# INTERNAL_IPS = [
#     '127.0.0.1',
# ]

# Development database - use SQLite for simplicity
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Disable security features for development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@hobbyhubby.com'