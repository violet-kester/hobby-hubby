"""
Tests for Django settings configuration.
"""

import pytest
from django.test import TestCase
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class SettingsConfigurationTest(TestCase):
    """Test Django settings load correctly."""
    
    def test_settings_load_correctly(self):
        """Test that Django settings load without errors."""
        # This test passes if Django can load settings without exceptions
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertIsNotNone(settings.INSTALLED_APPS)
        self.assertIsNotNone(settings.MIDDLEWARE)
    
    def test_database_connection(self):
        """Test that database connection is configured."""
        from django.db import connections
        from django.db.utils import ConnectionHandler
        
        # Test that we can get a connection
        connection = connections['default']
        self.assertIsNotNone(connection)
        
        # Test that connection settings are configured
        self.assertIn('ENGINE', connection.settings_dict)
        self.assertIn('NAME', connection.settings_dict)
    
    def test_static_files_configured(self):
        """Test that static files are configured properly."""
        self.assertIsNotNone(settings.STATIC_URL)
        self.assertIsNotNone(settings.STATIC_ROOT)
        self.assertIsNotNone(settings.STATICFILES_DIRS)
        
        # Test that static directories exist or can be created
        import os
        for static_dir in settings.STATICFILES_DIRS:
            parent_dir = os.path.dirname(static_dir)
            self.assertTrue(os.path.exists(parent_dir) or os.access(parent_dir, os.W_OK))
    
    def test_security_settings(self):
        """Test that security settings are configured."""
        # Test security headers
        self.assertTrue(settings.SECURE_BROWSER_XSS_FILTER)
        self.assertTrue(settings.SECURE_CONTENT_TYPE_NOSNIFF)
        self.assertEqual(settings.X_FRAME_OPTIONS, 'DENY')
        
        # Test file upload limits
        self.assertEqual(settings.FILE_UPLOAD_MAX_MEMORY_SIZE, 10 * 1024 * 1024)
        self.assertEqual(settings.DATA_UPLOAD_MAX_MEMORY_SIZE, 10 * 1024 * 1024)
        
        # Test allowed file types
        self.assertIn('.jpg', settings.ALLOWED_UPLOAD_FILE_TYPES)
        self.assertIn('.png', settings.ALLOWED_UPLOAD_FILE_TYPES)
    
    def test_password_validators(self):
        """Test that password validators are configured."""
        self.assertIsNotNone(settings.AUTH_PASSWORD_VALIDATORS)
        self.assertGreater(len(settings.AUTH_PASSWORD_VALIDATORS), 0)
        
        # Test minimum length validator
        min_length_validator = next(
            (v for v in settings.AUTH_PASSWORD_VALIDATORS 
             if 'MinimumLengthValidator' in v['NAME']),
            None
        )
        self.assertIsNotNone(min_length_validator)
        self.assertEqual(min_length_validator['OPTIONS']['min_length'], 8)