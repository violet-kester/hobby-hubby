"""
Tests for login and authentication system.
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sessions.models import Session
from datetime import datetime, timedelta
from django.utils import timezone


User = get_user_model()


class LoginFormTest(TestCase):
    """Test custom login form."""
    
    def test_login_form_valid_data(self):
        """Test login form with valid data."""
        from accounts.forms import EmailLoginForm
        
        form_data = {
            'email': 'user@example.com',
            'password': 'TestPass123!',
            'remember_me': True
        }
        
        form = EmailLoginForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_login_form_missing_email(self):
        """Test login form with missing email."""
        from accounts.forms import EmailLoginForm
        
        form_data = {
            'password': 'TestPass123!',
        }
        
        form = EmailLoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_login_form_missing_password(self):
        """Test login form with missing password."""
        from accounts.forms import EmailLoginForm
        
        form_data = {
            'email': 'user@example.com',
        }
        
        form = EmailLoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
    
    def test_login_form_remember_me_optional(self):
        """Test that remember_me is optional."""
        from accounts.forms import EmailLoginForm
        
        form_data = {
            'email': 'user@example.com',
            'password': 'TestPass123!',
            # remember_me not included
        }
        
        form = EmailLoginForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.cleaned_data.get('remember_me', False))


class LoginViewTest(TestCase):
    """Test login view functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='TestPass123!',
            display_name='Test User',
            is_active=True,
            is_email_verified=True
        )
        self.unverified_user = User.objects.create_user(
            email='unverified@example.com',
            password='TestPass123!',
            display_name='Unverified User',
            is_active=False,
            is_email_verified=False
        )
    
    def test_login_view_get(self):
        """Test GET request to login view."""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
        self.assertContains(response, 'email')
        self.assertContains(response, 'password')
    
    def test_login_with_valid_credentials(self):
        """Test login with valid credentials."""
        response = self.client.post(reverse('accounts:login'), {
            'email': 'testuser@example.com',
            'password': 'TestPass123!',
        })
        
        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)
        
        # User should be authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post(reverse('accounts:login'), {
            'email': 'testuser@example.com',
            'password': 'WrongPassword!',
        })
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email or password')
        
        # User should not be authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_login_with_unverified_email(self):
        """Test login with unverified email."""
        response = self.client.post(reverse('accounts:login'), {
            'email': 'unverified@example.com',
            'password': 'TestPass123!',
        })
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)
        # Check for any part of the error message
        self.assertTrue(
            'email is not verified' in str(response.content) or 
            'Your email is not verified' in str(response.content)
        )
        
        # User should not be authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_login_with_remember_me(self):
        """Test that remember me extends session."""
        response = self.client.post(reverse('accounts:login'), {
            'email': 'testuser@example.com',
            'password': 'TestPass123!',
            'remember_me': 'on',
        })
        
        # Get session
        session = self.client.session
        
        # Check session expiry is extended (2 weeks)
        self.assertIsNotNone(session.get_expiry_age())
        self.assertGreater(session.get_expiry_age(), 86400)  # More than 1 day
    
    def test_login_without_remember_me(self):
        """Test that session expires on browser close without remember me."""
        response = self.client.post(reverse('accounts:login'), {
            'email': 'testuser@example.com',
            'password': 'TestPass123!',
        })
        
        # Get session
        session = self.client.session
        
        # Check session expires on browser close
        self.assertEqual(session.get_expiry_age(), session.get_session_cookie_age())
    
    def test_login_redirect_next(self):
        """Test login redirects to next parameter."""
        next_url = '/some/protected/page/'
        response = self.client.post(
            f"{reverse('accounts:login')}?next={next_url}",
            {
                'email': 'testuser@example.com',
                'password': 'TestPass123!',
            }
        )
        
        # Should redirect to next URL
        self.assertRedirects(response, next_url, fetch_redirect_response=False)


class LogoutViewTest(TestCase):
    """Test logout view functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='TestPass123!',
            display_name='Test User',
            is_active=True,
            is_email_verified=True
        )
    
    def test_logout_clears_session(self):
        """Test that logout clears session."""
        # Login first
        self.client.login(email='testuser@example.com', password='TestPass123!')
        
        # Verify logged in
        response = self.client.get('/')
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Logout
        response = self.client.post(reverse('accounts:logout'))
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
        
        # Session should be cleared
        response = self.client.get('/')
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_logout_redirect(self):
        """Test logout redirects to home page."""
        self.client.login(email='testuser@example.com', password='TestPass123!')
        
        response = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(response, '/')


class PasswordResetTest(TestCase):
    """Test password reset functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='OldPass123!',
            display_name='Test User',
            is_active=True,
            is_email_verified=True
        )
    
    def test_password_reset_form_get(self):
        """Test GET request to password reset form."""
        response = self.client.get(reverse('accounts:password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password Reset')
        self.assertContains(response, 'email')
    
    def test_password_reset_email_generation(self):
        """Test password reset sends email."""
        response = self.client.post(reverse('accounts:password_reset'), {
            'email': 'testuser@example.com',
        })
        
        # Should redirect to done page
        self.assertRedirects(response, reverse('accounts:password_reset_done'))
        
        # Email should be sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('testuser@example.com', email.to)
        self.assertIn('password reset', email.subject.lower())
    
    def test_password_reset_invalid_email(self):
        """Test password reset with non-existent email."""
        response = self.client.post(reverse('accounts:password_reset'), {
            'email': 'nonexistent@example.com',
        })
        
        # Should still redirect (don't reveal if email exists)
        self.assertRedirects(response, reverse('accounts:password_reset_done'))
        
        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)
    
    def test_password_reset_confirm(self):
        """Test password reset confirmation."""
        # Generate reset token
        token = default_token_generator.make_token(self.user)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        # Get reset confirm page
        response = self.client.get(reverse('accounts:password_reset_confirm', kwargs={
            'uidb64': uidb64,
            'token': token
        }))
        
        # Should redirect to set password form
        self.assertEqual(response.status_code, 302)
        
        # Follow redirect and submit new password
        response = self.client.post(response.url, {
            'new_password1': 'NewPass123!',
            'new_password2': 'NewPass123!',
        })
        
        # Should redirect to complete page
        self.assertRedirects(response, reverse('accounts:password_reset_complete'))
        
        # Password should be changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))


class LoginRequiredTest(TestCase):
    """Test login required functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='TestPass123!',
            display_name='Test User',
            is_active=True,
            is_email_verified=True
        )
    
    def test_login_required_redirects(self):
        """Test that login_required redirects to login."""
        # Try to access protected view
        response = self.client.get(reverse('accounts:profile'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)
        self.assertIn('next=', response.url)
    
    def test_login_required_allows_authenticated(self):
        """Test that login_required allows authenticated users."""
        # Login
        self.client.login(email='testuser@example.com', password='TestPass123!')
        
        # Access protected view
        response = self.client.get(reverse('accounts:profile'))
        
        # Should be allowed
        self.assertEqual(response.status_code, 200)


class AuthenticationURLTest(TestCase):
    """Test authentication URL patterns."""
    
    def test_login_url_resolves(self):
        """Test that login URL resolves correctly."""
        url = reverse('accounts:login')
        self.assertEqual(url, '/accounts/login/')
    
    def test_logout_url_resolves(self):
        """Test that logout URL resolves correctly."""
        url = reverse('accounts:logout')
        self.assertEqual(url, '/accounts/logout/')
    
    def test_password_reset_url_resolves(self):
        """Test that password reset URL resolves correctly."""
        url = reverse('accounts:password_reset')
        self.assertEqual(url, '/accounts/password/reset/')
    
    def test_password_reset_done_url_resolves(self):
        """Test that password reset done URL resolves correctly."""
        url = reverse('accounts:password_reset_done')
        self.assertEqual(url, '/accounts/password/reset/done/')
    
    def test_password_reset_confirm_url_resolves(self):
        """Test that password reset confirm URL resolves correctly."""
        url = reverse('accounts:password_reset_confirm', kwargs={
            'uidb64': 'test-uid',
            'token': 'test-token'
        })
        self.assertEqual(url, '/accounts/password/reset/test-uid/test-token/')
    
    def test_password_reset_complete_url_resolves(self):
        """Test that password reset complete URL resolves correctly."""
        url = reverse('accounts:password_reset_complete')
        self.assertEqual(url, '/accounts/password/reset/complete/')
    
    def test_profile_url_resolves(self):
        """Test that profile URL resolves correctly."""
        url = reverse('accounts:profile')
        self.assertEqual(url, '/accounts/profile/')