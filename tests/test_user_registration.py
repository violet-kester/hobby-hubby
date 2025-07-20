"""
Tests for user registration system with email verification.
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.exceptions import ValidationError
from unittest.mock import patch


User = get_user_model()


class UserRegistrationFormTest(TestCase):
    """Test user registration form."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_registration_form_valid_data(self):
        """Test registration form with valid data."""
        from accounts.forms import UserRegistrationForm
        
        form_data = {
            'email': 'newuser@example.com',
            'display_name': 'New User',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_registration_form_password_mismatch(self):
        """Test registration form with mismatched passwords."""
        from accounts.forms import UserRegistrationForm
        
        form_data = {
            'email': 'newuser@example.com',
            'display_name': 'New User',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass123!'
        }
        
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
    
    def test_registration_form_duplicate_email(self):
        """Test registration form with duplicate email."""
        from accounts.forms import UserRegistrationForm
        
        # Create existing user
        User.objects.create_user(
            email='existing@example.com',
            password='TestPass123!',
            display_name='Existing User'
        )
        
        form_data = {
            'email': 'existing@example.com',
            'display_name': 'New User',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_registration_form_weak_password(self):
        """Test registration form with weak password."""
        from accounts.forms import UserRegistrationForm
        
        form_data = {
            'email': 'newuser@example.com',
            'display_name': 'New User',
            'password1': '123',  # Too short
            'password2': '123'
        }
        
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
    
    def test_registration_form_missing_fields(self):
        """Test registration form with missing required fields."""
        from accounts.forms import UserRegistrationForm
        
        form_data = {
            'email': 'newuser@example.com',
            # Missing display_name and passwords
        }
        
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('display_name', form.errors)
        self.assertIn('password1', form.errors)


class UserRegistrationViewTest(TestCase):
    """Test user registration view."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_registration_view_get(self):
        """Test GET request to registration view."""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Register')
        self.assertContains(response, 'form')
    
    def test_registration_view_post_valid(self):
        """Test POST request to registration view with valid data."""
        response = self.client.post(reverse('accounts:register'), {
            'email': 'newuser@example.com',
            'display_name': 'New User',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        })
        
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        
        # User should be created but inactive
        user = User.objects.get(email='newuser@example.com')
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_email_verified)
        self.assertEqual(user.display_name, 'New User')
    
    def test_registration_view_post_invalid(self):
        """Test POST request to registration view with invalid data."""
        response = self.client.post(reverse('accounts:register'), {
            'email': 'newuser@example.com',
            'display_name': 'New User',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass123!'  # Mismatched password
        })
        
        # Should not redirect, should show form with errors
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        
        # User should not be created
        self.assertFalse(User.objects.filter(email='newuser@example.com').exists())
    
    def test_registration_sends_verification_email(self):
        """Test that registration sends verification email."""
        response = self.client.post(reverse('accounts:register'), {
            'email': 'newuser@example.com',
            'display_name': 'New User',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        })
        
        # Check that one email was sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email content
        email = mail.outbox[0]
        self.assertIn('newuser@example.com', email.to)
        self.assertIn('verify', email.subject.lower())
        self.assertIn('verification', email.body.lower())


class EmailVerificationTest(TestCase):
    """Test email verification functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='TestPass123!',
            display_name='Test User',
            is_active=False,
            is_email_verified=False
        )
    
    def test_token_generation(self):
        """Test that verification tokens are generated correctly."""
        token = default_token_generator.make_token(self.user)
        self.assertIsNotNone(token)
        self.assertTrue(default_token_generator.check_token(self.user, token))
    
    def test_email_verification_view_valid_token(self):
        """Test email verification view with valid token."""
        token = default_token_generator.make_token(self.user)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        response = self.client.get(reverse('accounts:verify_email', kwargs={
            'uidb64': uidb64,
            'token': token
        }))
        
        # Should redirect to success page
        self.assertEqual(response.status_code, 302)
        
        # User should be activated
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_email_verified)
    
    def test_email_verification_view_invalid_token(self):
        """Test email verification view with invalid token."""
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        response = self.client.get(reverse('accounts:verify_email', kwargs={
            'uidb64': uidb64,
            'token': 'invalid-token'
        }))
        
        # Should show error page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'invalid')
        
        # User should remain inactive
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.is_email_verified)
    
    def test_email_verification_view_invalid_uid(self):
        """Test email verification view with invalid UID."""
        token = default_token_generator.make_token(self.user)
        
        response = self.client.get(reverse('accounts:verify_email', kwargs={
            'uidb64': 'invalid-uid',
            'token': token
        }))
        
        # Should show error page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'invalid')
    
    def test_email_verification_already_verified(self):
        """Test email verification for already verified user."""
        # Activate user first
        self.user.is_active = True
        self.user.is_email_verified = True
        self.user.save()
        
        token = default_token_generator.make_token(self.user)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        response = self.client.get(reverse('accounts:verify_email', kwargs={
            'uidb64': uidb64,
            'token': token
        }))
        
        # Should redirect to already verified page
        self.assertEqual(response.status_code, 302)
    
    def test_email_verification_nonexistent_user(self):
        """Test email verification for non-existent user."""
        token = default_token_generator.make_token(self.user)
        # Use a non-existent user ID
        uidb64 = urlsafe_base64_encode(force_bytes(99999))
        
        response = self.client.get(reverse('accounts:verify_email', kwargs={
            'uidb64': uidb64,
            'token': token
        }))
        
        # Should show error page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'invalid')


class RegistrationURLTest(TestCase):
    """Test registration URL patterns."""
    
    def test_registration_url_resolves(self):
        """Test that registration URL resolves correctly."""
        url = reverse('accounts:register')
        self.assertEqual(url, '/accounts/register/')
    
    def test_email_verification_url_resolves(self):
        """Test that email verification URL resolves correctly."""
        url = reverse('accounts:verify_email', kwargs={
            'uidb64': 'test-uid',
            'token': 'test-token'
        })
        self.assertEqual(url, '/accounts/verify/test-uid/test-token/')
    
    def test_registration_success_url_resolves(self):
        """Test that registration success URL resolves correctly."""
        url = reverse('accounts:registration_success')
        self.assertEqual(url, '/accounts/registration-success/')
    
    def test_verification_complete_url_resolves(self):
        """Test that verification complete URL resolves correctly."""
        url = reverse('accounts:verification_complete')
        self.assertEqual(url, '/accounts/verification-complete/')