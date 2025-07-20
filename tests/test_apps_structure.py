"""
Tests for Django apps structure and configuration.
"""

import pytest
from django.test import TestCase
from django.conf import settings
from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.db import models
from django.utils import timezone


class AppsStructureTest(TestCase):
    """Test that Django apps are properly configured."""
    
    def test_accounts_app_registered(self):
        """Test that accounts app is properly registered."""
        self.assertIn('accounts', settings.INSTALLED_APPS)
        
        # Test that app can be retrieved
        accounts_app = apps.get_app_config('accounts')
        self.assertIsNotNone(accounts_app)
        self.assertEqual(accounts_app.name, 'accounts')
    
    def test_forums_app_registered(self):
        """Test that forums app is properly registered."""
        self.assertIn('forums', settings.INSTALLED_APPS)
        
        # Test that app can be retrieved
        forums_app = apps.get_app_config('forums')
        self.assertIsNotNone(forums_app)
        self.assertEqual(forums_app.name, 'forums')
    
    def test_core_app_registered(self):
        """Test that core app is properly registered."""
        self.assertIn('core', settings.INSTALLED_APPS)
        
        # Test that app can be retrieved
        core_app = apps.get_app_config('core')
        self.assertIsNotNone(core_app)
        self.assertEqual(core_app.name, 'core')
    
    def test_timestamped_model_mixin_exists(self):
        """Test that TimestampedModel mixin is available."""
        from core.models import TimestampedModel
        
        # Test that it's a Django model
        self.assertTrue(issubclass(TimestampedModel, models.Model))
        
        # Test that it has the required fields
        self.assertTrue(hasattr(TimestampedModel, 'created_at'))
        self.assertTrue(hasattr(TimestampedModel, 'updated_at'))
    
    def test_timestamped_model_functionality(self):
        """Test that TimestampedModel mixin works correctly."""
        from core.models import TimestampedModel
        
        # Create a test model that inherits from TimestampedModel
        class TestModel(TimestampedModel):
            name = models.CharField(max_length=100)
            
            class Meta:
                app_label = 'core'
        
        # Test field types
        created_at_field = TestModel._meta.get_field('created_at')
        updated_at_field = TestModel._meta.get_field('updated_at')
        
        self.assertIsInstance(created_at_field, models.DateTimeField)
        self.assertIsInstance(updated_at_field, models.DateTimeField)
        
        # Test auto_now_add and auto_now
        self.assertTrue(created_at_field.auto_now_add)
        self.assertTrue(updated_at_field.auto_now)
    
    def test_django_admin_accessible(self):
        """Test that Django admin is accessible."""
        # Test that admin site exists
        self.assertIsNotNone(admin.site)
        self.assertIsInstance(admin.site, AdminSite)
        
        # Test that admin URLs are configured
        from django.urls import reverse
        from django.urls.exceptions import NoReverseMatch
        
        try:
            admin_url = reverse('admin:index')
            self.assertIsNotNone(admin_url)
        except NoReverseMatch:
            self.fail("Admin URLs are not configured")
    
    def test_app_configs_proper_setup(self):
        """Test that app configs are properly set up."""
        # Test accounts app config
        accounts_config = apps.get_app_config('accounts')
        self.assertEqual(accounts_config.verbose_name, 'Accounts')
        
        # Test forums app config
        forums_config = apps.get_app_config('forums')
        self.assertEqual(forums_config.verbose_name, 'Forums')
        
        # Test core app config
        core_config = apps.get_app_config('core')
        self.assertEqual(core_config.verbose_name, 'Core')
    
    def test_timestamped_model_abstract(self):
        """Test that TimestampedModel is abstract."""
        from core.models import TimestampedModel
        
        # Test that it's abstract
        self.assertTrue(TimestampedModel._meta.abstract)
        
        # Test that it doesn't have an objects manager (since it's abstract)
        self.assertFalse(hasattr(TimestampedModel, 'objects'))
        
        # Test that it can't be instantiated directly
        with self.assertRaises(TypeError):
            TimestampedModel()
    
    def test_all_apps_have_init_files(self):
        """Test that all apps have proper __init__.py files."""
        import os
        
        apps_to_test = ['accounts', 'forums', 'core']
        
        for app_name in apps_to_test:
            init_file = os.path.join(app_name, '__init__.py')
            self.assertTrue(os.path.exists(init_file), 
                          f"Missing __init__.py in {app_name} app")