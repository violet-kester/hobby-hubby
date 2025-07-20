"""
Tests for forum thread and post creation functionality.
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from unittest.mock import patch
from forums.models import Category, Subcategory, Thread, Post
from forums.forms import ThreadCreateForm, PostCreateForm

User = get_user_model()


class ThreadCreationTestCase(TestCase):
    """Test thread creation functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            display_name='Test User',
            is_active=True,
            is_email_verified=True
        )
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        self.subcategory = Subcategory.objects.create(
            name='Test Subcategory',
            description='Test subcategory description',
            category=self.category
        )
        self.thread_create_url = reverse(
            'forums:thread_create',
            kwargs={
                'category_slug': self.category.slug,
                'subcategory_slug': self.subcategory.slug
            }
        )
    
    def test_unauthenticated_user_redirected_to_login(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(self.thread_create_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_authenticated_user_can_access_thread_create_form(self):
        """Test that authenticated users can access thread creation form."""
        self.client.login(email='testuser@example.com', password='testpass123')
        response = self.client.get(self.thread_create_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create New Thread')
        self.assertContains(response, 'Title')
        self.assertContains(response, 'Content')
    
    def test_thread_creation_with_valid_data(self):
        """Test creating a thread with valid data."""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        thread_data = {
            'title': 'Test Thread Title',
            'content': 'This is the content of the test thread.'
        }
        
        response = self.client.post(self.thread_create_url, thread_data)
        
        # Should redirect to the new thread
        self.assertEqual(response.status_code, 302)
        
        # Check that thread was created
        thread = Thread.objects.get(title='Test Thread Title')
        self.assertEqual(thread.author, self.user)
        self.assertEqual(thread.subcategory, self.subcategory)
        
        # Check that initial post was created
        initial_post = thread.posts.first()
        self.assertIsNotNone(initial_post)
        self.assertEqual(initial_post.content, 'This is the content of the test thread.')
        self.assertEqual(initial_post.author, self.user)
        
        # Check redirect URL
        expected_url = reverse(
            'forums:thread_detail',
            kwargs={
                'category_slug': self.category.slug,
                'subcategory_slug': self.subcategory.slug,
                'thread_slug': thread.slug
            }
        )
        self.assertRedirects(response, expected_url)
    
    def test_thread_creation_with_empty_title(self):
        """Test thread creation fails with empty title."""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        thread_data = {
            'title': '',
            'content': 'This thread has no title.'
        }
        
        response = self.client.post(self.thread_create_url, thread_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')
        self.assertEqual(Thread.objects.count(), 0)
    
    def test_thread_creation_with_empty_content(self):
        """Test thread creation fails with empty content."""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        thread_data = {
            'title': 'Test Thread',
            'content': ''
        }
        
        response = self.client.post(self.thread_create_url, thread_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')
        self.assertEqual(Thread.objects.count(), 0)
    
    def test_thread_creation_with_title_too_long(self):
        """Test thread creation fails with title exceeding maximum length."""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        # Create a title longer than 200 characters
        long_title = 'A' * 201
        thread_data = {
            'title': long_title,
            'content': 'Content for thread with long title.'
        }
        
        response = self.client.post(self.thread_create_url, thread_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ensure this value has at most 200 characters')
        self.assertEqual(Thread.objects.count(), 0)
    
    def test_thread_creation_success_message(self):
        """Test that success message is displayed after thread creation."""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        thread_data = {
            'title': 'Success Message Test',
            'content': 'Testing success message functionality.'
        }
        
        response = self.client.post(self.thread_create_url, thread_data, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('created successfully', str(messages[0]))
    
    def test_thread_creation_updates_subcategory_counts(self):
        """Test that creating a thread updates subcategory thread count."""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        initial_thread_count = self.subcategory.threads.count()
        
        thread_data = {
            'title': 'Count Update Test',
            'content': 'Testing count updates.'
        }
        
        self.client.post(self.thread_create_url, thread_data)
        
        self.subcategory.refresh_from_db()
        self.assertEqual(self.subcategory.threads.count(), initial_thread_count + 1)


class PostCreationTestCase(TestCase):
    """Test post creation functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            display_name='Test User',
            is_active=True,
            is_email_verified=True
        )
        self.other_user = User.objects.create_user(
            email='otheruser@example.com',
            password='testpass123',
            display_name='Other User',
            is_active=True,
            is_email_verified=True
        )
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        self.subcategory = Subcategory.objects.create(
            name='Test Subcategory',
            description='Test subcategory description',
            category=self.category
        )
        self.thread = Thread.objects.create(
            title='Test Thread',
            subcategory=self.subcategory,
            author=self.other_user
        )
        # Create initial post for the thread
        Post.objects.create(
            content='Initial post content',
            thread=self.thread,
            author=self.other_user
        )
        
        self.post_create_url = reverse(
            'forums:post_create',
            kwargs={
                'category_slug': self.category.slug,
                'subcategory_slug': self.subcategory.slug,
                'thread_slug': self.thread.slug
            }
        )
    
    def test_unauthenticated_user_redirected_to_login(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(self.post_create_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_authenticated_user_can_access_post_create_form(self):
        """Test that authenticated users can access post creation form."""
        self.client.login(email='testuser@example.com', password='testpass123')
        response = self.client.get(self.post_create_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reply to Thread')
        self.assertContains(response, 'Content')
    
    def test_post_creation_with_valid_data(self):
        """Test creating a post with valid data."""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        post_data = {
            'content': 'This is a reply to the thread.'
        }
        
        initial_post_count = self.thread.post_count
        
        response = self.client.post(self.post_create_url, post_data)
        
        # Should redirect to the thread with anchor
        self.assertEqual(response.status_code, 302)
        
        # Check that post was created
        new_post = Post.objects.filter(
            thread=self.thread,
            content='This is a reply to the thread.'
        ).first()
        self.assertIsNotNone(new_post)
        self.assertEqual(new_post.author, self.user)
        
        # Check that thread's last_post_at was updated
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.last_post_at, new_post.created_at)
        self.assertEqual(self.thread.post_count, initial_post_count + 1)
    
    def test_post_creation_with_empty_content(self):
        """Test post creation fails with empty content."""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        post_data = {
            'content': ''
        }
        
        response = self.client.post(self.post_create_url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')
        
        # Should only have the initial post
        self.assertEqual(self.thread.posts.count(), 1)
    
    def test_post_creation_success_message(self):
        """Test that success message is displayed after post creation."""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        post_data = {
            'content': 'Testing success message for post creation.'
        }
        
        response = self.client.post(self.post_create_url, post_data, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Reply posted successfully', str(messages[0]))
    
    def test_post_creation_on_locked_thread_fails(self):
        """Test that users cannot post on locked threads."""
        self.thread.is_locked = True
        self.thread.save()
        
        self.client.login(email='testuser@example.com', password='testpass123')
        
        post_data = {
            'content': 'Trying to post on locked thread.'
        }
        
        response = self.client.post(self.post_create_url, post_data)
        self.assertEqual(response.status_code, 403)
        
        # Post should not be created
        self.assertEqual(self.thread.posts.count(), 1)  # Only initial post


class FormValidationTestCase(TestCase):
    """Test form validation for thread and post creation."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            display_name='Test User',
            is_active=True,
            is_email_verified=True
        )
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        self.subcategory = Subcategory.objects.create(
            name='Test Subcategory',
            description='Test subcategory description',
            category=self.category
        )
    
    def test_thread_form_validation_success(self):
        """Test ThreadCreateForm validation with valid data."""
        form_data = {
            'title': 'Valid Thread Title',
            'content': 'Valid thread content.'
        }
        form = ThreadCreateForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_thread_form_validation_empty_title(self):
        """Test ThreadCreateForm validation with empty title."""
        form_data = {
            'title': '',
            'content': 'Content without title.'
        }
        form = ThreadCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
    
    def test_thread_form_validation_empty_content(self):
        """Test ThreadCreateForm validation with empty content."""
        form_data = {
            'title': 'Title Without Content',
            'content': ''
        }
        form = ThreadCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)
    
    def test_post_form_validation_success(self):
        """Test PostCreateForm validation with valid data."""
        form_data = {
            'content': 'Valid post content.'
        }
        form = PostCreateForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_post_form_validation_empty_content(self):
        """Test PostCreateForm validation with empty content."""
        form_data = {
            'content': ''
        }
        form = PostCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)


class PreviewFunctionalityTestCase(TestCase):
    """Test AJAX preview functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            display_name='Test User',
            is_active=True,
            is_email_verified=True
        )
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        self.subcategory = Subcategory.objects.create(
            name='Test Subcategory',
            description='Test subcategory description',
            category=self.category
        )
        
        self.preview_url = reverse('forums:preview_content')
    
    def test_unauthenticated_user_cannot_access_preview(self):
        """Test that unauthenticated users cannot access preview."""
        response = self.client.post(self.preview_url, {
            'content': 'Preview test content'
        })
        self.assertEqual(response.status_code, 302)
    
    def test_preview_with_valid_content(self):
        """Test preview functionality with valid content."""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        response = self.client.post(
            self.preview_url,
            {'content': 'This is **bold** text with *italics*.'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        
        json_response = response.json()
        self.assertIn('html', json_response)
        self.assertIn('This is', json_response['html'])
    
    def test_preview_doesnt_save_to_database(self):
        """Test that preview doesn't save content to database."""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        initial_thread_count = Thread.objects.count()
        initial_post_count = Post.objects.count()
        
        self.client.post(
            self.preview_url,
            {'content': 'Preview content that should not be saved'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Counts should remain the same
        self.assertEqual(Thread.objects.count(), initial_thread_count)
        self.assertEqual(Post.objects.count(), initial_post_count)
    
    def test_preview_with_empty_content(self):
        """Test preview with empty content."""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        response = self.client.post(
            self.preview_url,
            {'content': ''},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        json_response = response.json()
        self.assertIn('error', json_response)


class CSRFProtectionTestCase(TestCase):
    """Test CSRF protection on creation forms."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            display_name='Test User',
            is_active=True,
            is_email_verified=True
        )
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        self.subcategory = Subcategory.objects.create(
            name='Test Subcategory',
            description='Test subcategory description',
            category=self.category
        )
        self.thread_create_url = reverse(
            'forums:thread_create',
            kwargs={
                'category_slug': self.category.slug,
                'subcategory_slug': self.subcategory.slug
            }
        )
    
    def test_csrf_protection_on_thread_creation(self):
        """Test that CSRF protection is active on thread creation."""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        # Try to post without CSRF token
        thread_data = {
            'title': 'CSRF Test Thread',
            'content': 'Testing CSRF protection.'
        }
        
        response = self.client.post(self.thread_create_url, thread_data)
        self.assertEqual(response.status_code, 403)  # CSRF failure
        
        # Thread should not be created
        self.assertEqual(Thread.objects.count(), 0)