"""
Test-specific settings for API testing.
Disables debug toolbar to prevent conflicts during automated testing.
"""

from .development import *

# Disable debug toolbar for testing
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: False,
}

INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'debug_toolbar']
MIDDLEWARE = [mw for mw in MIDDLEWARE if 'debug_toolbar' not in mw]