"""
Tests for custom user model.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib import admin
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


class CustomUserModelTest(TestCase):
    """Test custom user model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.User = get_user_model()
    
    def test_custom_user_model_configured(self):
        """Test that custom user model is configured in settings."""
        self.assertEqual(settings.AUTH_USER_MODEL, 'accounts.CustomUser')
    
    def test_user_creation_with_required_fields(self):
        """Test user creation with only required fields."""
        user = self.User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            display_name='Test User'
        )
        
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertEqual(user.display_name, 'Test User')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_email_verified)  # Default should be False
        self.assertEqual(user.location, '')  # Optional field should be empty string
        self.assertEqual(user.bio, '')  # Optional field should be empty string
        self.assertFalse(user.profile_picture)  # Optional field should be False
    
    def test_user_creation_with_all_fields(self):
        """Test user creation with all fields."""
        # Create a simple image file for testing
        image_file = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        user = self.User.objects.create_user(
            email='fulluser@example.com',
            password='testpass123',
            display_name='Full User',
            location='New York, NY',
            bio='This is a test bio for the user.',
            is_email_verified=True,
            profile_picture=image_file
        )
        
        self.assertEqual(user.email, 'fulluser@example.com')
        self.assertEqual(user.display_name, 'Full User')
        self.assertEqual(user.location, 'New York, NY')
        self.assertEqual(user.bio, 'This is a test bio for the user.')
        self.assertTrue(user.is_email_verified)
        self.assertTrue(user.profile_picture)
    
    def test_email_uniqueness_constraint(self):
        """Test that email addresses must be unique."""
        # Create first user
        self.User.objects.create_user(
            email='unique@example.com',
            password='testpass123',
            display_name='First User'
        )
        
        # Try to create second user with same email
        with self.assertRaises(IntegrityError):
            self.User.objects.create_user(
                email='unique@example.com',
                password='testpass123',
                display_name='Second User'
            )
    
    def test_user_string_representation(self):
        """Test user string representation."""
        user = self.User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            display_name='Test User'
        )
        
        self.assertEqual(str(user), 'Test User')
    
    def test_display_name_max_length(self):
        """Test display_name field max length validation."""
        user = self.User(
            email='test@example.com',
            display_name='a' * 51  # 51 characters, should exceed max_length
        )
        
        with self.assertRaises(ValidationError):
            user.full_clean()
    
    def test_location_max_length(self):
        """Test location field max length validation."""
        user = self.User(
            email='test@example.com',
            display_name='Test User',
            location='a' * 101  # 101 characters, should exceed max_length
        )
        
        with self.assertRaises(ValidationError):
            user.full_clean()
    
    def test_user_inherits_from_abstractuser(self):
        """Test that CustomUser inherits from AbstractUser."""
        from django.contrib.auth.models import AbstractUser
        self.assertTrue(issubclass(self.User, AbstractUser))
    
    def test_user_inherits_from_timestamped_model(self):
        """Test that CustomUser inherits from TimestampedModel."""
        from core.models import TimestampedModel
        self.assertTrue(issubclass(self.User, TimestampedModel))
    
    def test_user_has_timestamp_fields(self):
        """Test that user has created_at and updated_at fields."""
        user = self.User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            display_name='Test User'
        )
        
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)
    
    def test_user_fields_have_help_text(self):
        """Test that user fields have appropriate help text."""
        user = self.User()
        
        display_name_field = user._meta.get_field('display_name')
        self.assertIsNotNone(display_name_field.help_text)
        
        location_field = user._meta.get_field('location')
        self.assertIsNotNone(location_field.help_text)
        
        bio_field = user._meta.get_field('bio')
        self.assertIsNotNone(bio_field.help_text)
        
        is_email_verified_field = user._meta.get_field('is_email_verified')
        self.assertIsNotNone(is_email_verified_field.help_text)
    
    def test_user_admin_registered(self):
        """Test that UserAdmin is registered with Django admin."""
        # Check if CustomUser is registered in admin
        self.assertIn(self.User, admin.site._registry)
        
        # Get the admin class
        user_admin = admin.site._registry[self.User]
        self.assertIsNotNone(user_admin)
        
        # Check that it has the required list_display fields
        self.assertIn('email', user_admin.list_display)
        self.assertIn('display_name', user_admin.list_display)
        self.assertIn('is_email_verified', user_admin.list_display)
    
    def test_user_admin_can_create_users(self):
        """Test that admin can create users through the interface."""
        # This tests the admin form configuration
        user_admin = admin.site._registry[self.User]
        
        # Check that required fields are in fieldsets or fields
        if hasattr(user_admin, 'fieldsets'):
            # Extract all field names from fieldsets
            admin_fields = []
            for fieldset in user_admin.fieldsets:
                admin_fields.extend(fieldset[1]['fields'])
            
            self.assertIn('email', admin_fields)
            self.assertIn('display_name', admin_fields)
        elif hasattr(user_admin, 'fields'):
            self.assertIn('email', user_admin.fields)
            self.assertIn('display_name', user_admin.fields)
    
    def test_user_username_field_is_email(self):
        """Test that email is used as the username field."""
        self.assertEqual(self.User.USERNAME_FIELD, 'email')
    
    def test_user_required_fields(self):
        """Test that display_name is in required fields."""
        self.assertIn('display_name', self.User.REQUIRED_FIELDS)