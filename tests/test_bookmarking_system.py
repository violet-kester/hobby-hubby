"""
Tests for the forum bookmarking system.
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from forums.models import Category, Subcategory, Thread, Post, Bookmark
from unittest.mock import patch

User = get_user_model()


class BookmarkModelTestCase(TestCase):
    """Test the Bookmark model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            display_name='User One',
            is_active=True,
            is_email_verified=True
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            display_name='User Two',
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
            author=self.user1
        )
        # Create initial post so thread has content
        Post.objects.create(
            content='Initial thread content',
            thread=self.thread,
            author=self.user1
        )
    
    def test_bookmark_creation_with_required_fields(self):
        """Test creating a bookmark with all required fields."""
        bookmark = Bookmark.objects.create(
            user=self.user2,
            thread=self.thread
        )
        
        self.assertEqual(bookmark.user, self.user2)
        self.assertEqual(bookmark.thread, self.thread)
        self.assertIsNotNone(bookmark.created_at)
    
    def test_bookmark_string_representation(self):
        """Test the string representation of a bookmark."""
        bookmark = Bookmark.objects.create(
            user=self.user2,
            thread=self.thread
        )
        
        expected_str = f"{self.user2.display_name} bookmarked {self.thread.title}"
        self.assertEqual(str(bookmark), expected_str)
    
    def test_bookmark_unique_constraint_user_thread(self):
        """Test that a user can only bookmark a thread once."""
        # Create first bookmark
        Bookmark.objects.create(
            user=self.user2,
            thread=self.thread
        )
        
        # Try to create duplicate bookmark - should fail
        with self.assertRaises(IntegrityError):
            Bookmark.objects.create(
                user=self.user2,
                thread=self.thread
            )
    
    def test_bookmark_different_users_same_thread(self):
        """Test that different users can bookmark the same thread."""
        bookmark1 = Bookmark.objects.create(
            user=self.user1,
            thread=self.thread
        )
        bookmark2 = Bookmark.objects.create(
            user=self.user2,
            thread=self.thread
        )
        
        self.assertEqual(Bookmark.objects.count(), 2)
        self.assertNotEqual(bookmark1.user, bookmark2.user)
    
    def test_bookmark_same_user_different_threads(self):
        """Test that the same user can bookmark different threads."""
        thread2 = Thread.objects.create(
            title='Another Test Thread',
            subcategory=self.subcategory,
            author=self.user1
        )
        Post.objects.create(
            content='Another thread content',
            thread=thread2,
            author=self.user1
        )
        
        bookmark1 = Bookmark.objects.create(
            user=self.user2,
            thread=self.thread
        )
        bookmark2 = Bookmark.objects.create(
            user=self.user2,
            thread=thread2
        )
        
        self.assertEqual(Bookmark.objects.count(), 2)
        self.assertEqual(bookmark1.user, bookmark2.user)
        self.assertNotEqual(bookmark1.thread, bookmark2.thread)
    
    def test_bookmark_cascade_deletion_with_user(self):
        """Test that bookmarks are deleted when user is deleted."""
        Bookmark.objects.create(
            user=self.user2,
            thread=self.thread
        )
        
        self.assertEqual(Bookmark.objects.count(), 1)
        
        self.user2.delete()
        self.assertEqual(Bookmark.objects.count(), 0)
    
    def test_bookmark_cascade_deletion_with_thread(self):
        """Test that bookmarks are deleted when thread is deleted."""
        Bookmark.objects.create(
            user=self.user2,
            thread=self.thread
        )
        
        self.assertEqual(Bookmark.objects.count(), 1)
        
        self.thread.delete()
        self.assertEqual(Bookmark.objects.count(), 0)
    
    def test_bookmark_ordering(self):
        """Test that bookmarks are ordered by creation date (newest first)."""
        thread2 = Thread.objects.create(
            title='Another Thread',
            subcategory=self.subcategory,
            author=self.user1
        )
        Post.objects.create(
            content='Another thread content',
            thread=thread2,
            author=self.user1
        )
        
        bookmark1 = Bookmark.objects.create(
            user=self.user2,
            thread=self.thread
        )
        bookmark2 = Bookmark.objects.create(
            user=self.user2,
            thread=thread2
        )
        
        bookmarks = Bookmark.objects.all()
        self.assertEqual(bookmarks[0], bookmark2)  # Newest first
        self.assertEqual(bookmarks[1], bookmark1)


class BookmarkViewTestCase(TestCase):
    """Test the AJAX bookmarking view functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            display_name='User One',
            is_active=True,
            is_email_verified=True
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            display_name='User Two',
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
            author=self.user1
        )
        # Create initial post so thread has content
        Post.objects.create(
            content='Initial thread content',
            thread=self.thread,
            author=self.user1
        )
        self.bookmark_url = reverse('forums:bookmark_thread', kwargs={'thread_id': self.thread.id})
    
    def test_unauthenticated_user_cannot_bookmark(self):
        """Test that unauthenticated users cannot bookmark."""
        response = self.client.post(self.bookmark_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_bookmark_requires_ajax_request(self):
        """Test that bookmarking requires an AJAX request."""
        self.client.login(email='user2@example.com', password='testpass123')
        
        # Regular POST request (not AJAX)
        response = self.client.post(self.bookmark_url)
        self.assertEqual(response.status_code, 400)
    
    def test_bookmark_requires_post_method(self):
        """Test that bookmarking requires POST method."""
        self.client.login(email='user2@example.com', password='testpass123')
        
        response = self.client.get(
            self.bookmark_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 405)  # Method not allowed
    
    def test_user_can_bookmark_thread(self):
        """Test that authenticated user can bookmark a thread."""
        self.client.login(email='user2@example.com', password='testpass123')
        
        response = self.client.post(
            self.bookmark_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        json_response = response.json()
        self.assertTrue(json_response['bookmarked'])
        
        # Check that bookmark was created
        self.assertTrue(Bookmark.objects.filter(user=self.user2, thread=self.thread).exists())
    
    def test_user_can_remove_bookmark(self):
        """Test that user can remove their bookmark."""
        # Create initial bookmark
        Bookmark.objects.create(user=self.user2, thread=self.thread)
        
        self.client.login(email='user2@example.com', password='testpass123')
        
        response = self.client.post(
            self.bookmark_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        json_response = response.json()
        self.assertFalse(json_response['bookmarked'])
        
        # Check that bookmark was deleted
        self.assertFalse(Bookmark.objects.filter(user=self.user2, thread=self.thread).exists())
    
    def test_bookmark_nonexistent_thread_404(self):
        """Test bookmarking non-existent thread returns 404."""
        self.client.login(email='user2@example.com', password='testpass123')
        
        nonexistent_url = reverse('forums:bookmark_thread', kwargs={'thread_id': 99999})
        
        response = self.client.post(
            nonexistent_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_author_can_bookmark_own_thread(self):
        """Test that thread author can bookmark their own thread."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.post(
            self.bookmark_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        json_response = response.json()
        self.assertTrue(json_response['bookmarked'])
        
        # Check that bookmark was created
        self.assertTrue(Bookmark.objects.filter(user=self.user1, thread=self.thread).exists())


class UserBookmarksViewTestCase(TestCase):
    """Test the user bookmarks list view functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            display_name='User One',
            is_active=True,
            is_email_verified=True
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            display_name='User Two',
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
        self.thread1 = Thread.objects.create(
            title='Test Thread 1',
            subcategory=self.subcategory,
            author=self.user1
        )
        self.thread2 = Thread.objects.create(
            title='Test Thread 2',
            subcategory=self.subcategory,
            author=self.user1
        )
        # Create initial posts
        Post.objects.create(
            content='Thread 1 content',
            thread=self.thread1,
            author=self.user1
        )
        Post.objects.create(
            content='Thread 2 content',
            thread=self.thread2,
            author=self.user1
        )
        self.bookmarks_url = reverse('accounts:bookmarks')
    
    def test_unauthenticated_user_cannot_view_bookmarks(self):
        """Test that unauthenticated users cannot view bookmarks."""
        response = self.client.get(self.bookmarks_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_user_can_view_own_bookmarks(self):
        """Test that user can view their own bookmarks."""
        # Create bookmarks for user2
        Bookmark.objects.create(user=self.user2, thread=self.thread1)
        Bookmark.objects.create(user=self.user2, thread=self.thread2)
        
        self.client.login(email='user2@example.com', password='testpass123')
        
        response = self.client.get(self.bookmarks_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that user's bookmarks are displayed
        self.assertContains(response, 'Test Thread 1')
        self.assertContains(response, 'Test Thread 2')
    
    def test_user_only_sees_own_bookmarks(self):
        """Test that users only see their own bookmarks."""
        # Create bookmarks for both users
        Bookmark.objects.create(user=self.user1, thread=self.thread1)
        Bookmark.objects.create(user=self.user2, thread=self.thread2)
        
        self.client.login(email='user2@example.com', password='testpass123')
        
        response = self.client.get(self.bookmarks_url)
        self.assertEqual(response.status_code, 200)
        
        # User2 should only see their bookmark
        self.assertNotContains(response, 'Test Thread 1')
        self.assertContains(response, 'Test Thread 2')
    
    def test_empty_bookmarks_list(self):
        """Test that empty bookmarks list displays appropriate message."""
        self.client.login(email='user2@example.com', password='testpass123')
        
        response = self.client.get(self.bookmarks_url)
        self.assertEqual(response.status_code, 200)
        
        # Check for empty state message
        self.assertContains(response, 'No bookmarked threads')
    
    def test_bookmarks_list_pagination(self):
        """Test that bookmarks list is paginated."""
        # Create many bookmarks (more than page size)
        for i in range(25):
            thread = Thread.objects.create(
                title=f'Thread {i}',
                subcategory=self.subcategory,
                author=self.user1
            )
            Post.objects.create(
                content=f'Content {i}',
                thread=thread,
                author=self.user1
            )
            Bookmark.objects.create(user=self.user2, thread=thread)
        
        self.client.login(email='user2@example.com', password='testpass123')
        
        response = self.client.get(self.bookmarks_url)
        self.assertEqual(response.status_code, 200)
        
        # Check pagination exists
        self.assertContains(response, 'page')
    
    def test_bookmark_ordering_newest_first(self):
        """Test that bookmarks are ordered by creation date (newest first)."""
        # Create bookmarks in order
        bookmark1 = Bookmark.objects.create(user=self.user2, thread=self.thread1)
        bookmark2 = Bookmark.objects.create(user=self.user2, thread=self.thread2)
        
        self.client.login(email='user2@example.com', password='testpass123')
        
        response = self.client.get(self.bookmarks_url)
        self.assertEqual(response.status_code, 200)
        
        # Extract content to check order
        content = response.content.decode()
        thread1_pos = content.find('Test Thread 1')
        thread2_pos = content.find('Test Thread 2')
        
        # Thread 2 should appear before Thread 1 (newest first)
        self.assertLess(thread2_pos, thread1_pos)


class BookmarkDisplayTestCase(TestCase):
    """Test bookmark display in templates."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            display_name='User One',
            is_active=True,
            is_email_verified=True
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            display_name='User Two',
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
            author=self.user1
        )
        # Create initial post
        Post.objects.create(
            content='Thread content',
            thread=self.thread,
            author=self.user1
        )
    
    def test_bookmark_button_for_authenticated_users(self):
        """Test that bookmark button is shown for authenticated users."""
        self.client.login(email='user2@example.com', password='testpass123')
        
        thread_url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category.slug,
            'subcategory_slug': self.subcategory.slug,
            'thread_slug': self.thread.slug
        })
        
        response = self.client.get(thread_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that bookmark button is present
        self.assertContains(response, 'bookmark-btn')
    
    def test_no_bookmark_button_for_unauthenticated_users(self):
        """Test that bookmark button is not shown for unauthenticated users."""
        thread_url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category.slug,
            'subcategory_slug': self.subcategory.slug,
            'thread_slug': self.thread.slug
        })
        
        response = self.client.get(thread_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that bookmark button is not present
        self.assertNotContains(response, 'bookmark-btn')
    
    def test_bookmarked_state_displayed_correctly(self):
        """Test that user's bookmark state is displayed correctly."""
        # User bookmarks the thread
        Bookmark.objects.create(user=self.user2, thread=self.thread)
        
        self.client.login(email='user2@example.com', password='testpass123')
        
        thread_url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category.slug,
            'subcategory_slug': self.subcategory.slug,
            'thread_slug': self.thread.slug
        })
        
        response = self.client.get(thread_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that bookmarked state is indicated
        self.assertContains(response, 'bookmarked')
    
    def test_subcategory_view_shows_bookmark_status(self):
        """Test that subcategory view shows bookmark status for threads."""
        # User bookmarks the thread
        Bookmark.objects.create(user=self.user2, thread=self.thread)
        
        self.client.login(email='user2@example.com', password='testpass123')
        
        subcategory_url = reverse('forums:subcategory_detail', kwargs={
            'category_slug': self.category.slug,
            'subcategory_slug': self.subcategory.slug
        })
        
        response = self.client.get(subcategory_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that bookmark status is visible in thread list
        self.assertContains(response, 'bookmarked')


class BookmarkAdminTestCase(TestCase):
    """Test Bookmark model in Django admin."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            display_name='User One',
            is_active=True,
            is_email_verified=True
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            display_name='User Two',
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
            author=self.user1
        )
        # Create initial post
        Post.objects.create(
            content='Thread content',
            thread=self.thread,
            author=self.user1
        )
    
    def test_bookmark_admin_can_create_bookmarks(self):
        """Test that admin can create bookmarks through the interface."""
        from django.contrib.admin.sites import site
        from forums.models import Bookmark
        
        # Check that Bookmark is registered with admin
        self.assertIn(Bookmark, site._registry)
    
    def test_bookmark_admin_list_display(self):
        """Test that bookmark admin has appropriate list display."""
        bookmark = Bookmark.objects.create(user=self.user2, thread=self.thread)
        
        # Test that we can create and display bookmarks
        self.assertEqual(str(bookmark), f"{self.user2.display_name} bookmarked {self.thread.title}")