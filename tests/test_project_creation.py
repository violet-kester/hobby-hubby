"""
Test that verifies the Django project was created successfully.
"""

import pytest
from django.test import TestCase
from django.core.management import call_command
from django.db import connection


class ProjectCreationTest(TestCase):
    """Test that Django project is properly configured."""
    
    def test_django_project_created(self):
        """Test that Django project exists and is configured."""
        # Test that we can import Django settings
        from django.conf import settings
        self.assertIsNotNone(settings)
        
        # Test that we're using the correct settings module
        self.assertTrue(settings.configured)
        
        # Test that SECRET_KEY is set
        self.assertIsNotNone(settings.SECRET_KEY)
        
        # Test that DEBUG setting exists (boolean value)
        self.assertIsInstance(settings.DEBUG, bool)
    
    def test_database_connection_works(self):
        """Test that database connection is working."""
        # Test that we can connect to the database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
    
    def test_migrations_applied(self):
        """Test that initial migrations were applied."""
        # Test that we can create a user (requires auth migrations)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            display_name='Test User'
        )
        self.assertIsNotNone(user.id)
        
        # Clean up
        user.delete()
    
    def test_static_files_configuration(self):
        """Test that static files are properly configured."""
        from django.conf import settings
        from django.contrib.staticfiles.finders import find
        
        # Test that static files settings are configured
        self.assertIsNotNone(settings.STATIC_URL)
        self.assertIsNotNone(settings.STATIC_ROOT)
        self.assertIsNotNone(settings.STATICFILES_DIRS)
        
        # Test that we can access static files system
        # (This tests the staticfiles app is installed)
        self.assertIn('django.contrib.staticfiles', settings.INSTALLED_APPS)
    
    def test_security_settings_applied(self):
        """Test that security settings from Risk Register are applied."""
        from django.conf import settings
        
        # Test XSS protection
        self.assertTrue(settings.SECURE_BROWSER_XSS_FILTER)
        self.assertTrue(settings.SECURE_CONTENT_TYPE_NOSNIFF)
        self.assertEqual(settings.X_FRAME_OPTIONS, 'DENY')
        
        # Test file upload security
        self.assertEqual(settings.FILE_UPLOAD_MAX_MEMORY_SIZE, 10 * 1024 * 1024)
        
        # Test allowed file types
        self.assertIn('.jpg', settings.ALLOWED_UPLOAD_FILE_TYPES)
        self.assertIn('.png', settings.ALLOWED_UPLOAD_FILE_TYPES)
        self.assertNotIn('.exe', settings.ALLOWED_UPLOAD_FILE_TYPES)
    
    def test_password_validation(self):
        """Test that password validation is configured."""
        from django.contrib.auth.password_validation import validate_password
        from django.contrib.auth.models import User
        from django.core.exceptions import ValidationError
        
        # Test that weak passwords are rejected
        user = User(username='testuser', email='test@example.com')
        
        with self.assertRaises(ValidationError):
            validate_password('123', user)  # Too short
            
        with self.assertRaises(ValidationError):
            validate_password('password', user)  # Too common
            
        with self.assertRaises(ValidationError):
            validate_password('testuser', user)  # Similar to username
        
        # Test that strong password is accepted
        try:
            validate_password('StrongP@ssw0rd!2023', user)
        except ValidationError:
            self.fail("Strong password should be valid")