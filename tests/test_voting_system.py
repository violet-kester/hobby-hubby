"""
Tests for the forum upvoting system.
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from forums.models import Category, Subcategory, Thread, Post, Vote
from unittest.mock import patch

User = get_user_model()


class VoteModelTestCase(TestCase):
    """Test the Vote model functionality."""
    
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
        self.post = Post.objects.create(
            content='Test post content',
            thread=self.thread,
            author=self.user1
        )
    
    def test_vote_creation_with_required_fields(self):
        """Test creating a vote with all required fields."""
        vote = Vote.objects.create(
            user=self.user2,
            post=self.post
        )
        
        self.assertEqual(vote.user, self.user2)
        self.assertEqual(vote.post, self.post)
        self.assertIsNotNone(vote.created_at)
    
    def test_vote_string_representation(self):
        """Test the string representation of a vote."""
        vote = Vote.objects.create(
            user=self.user2,
            post=self.post
        )
        
        expected_str = f"{self.user2.display_name} voted on post in {self.thread.title}"
        self.assertEqual(str(vote), expected_str)
    
    def test_vote_unique_constraint_user_post(self):
        """Test that a user can only vote once per post."""
        # Create first vote
        Vote.objects.create(
            user=self.user2,
            post=self.post
        )
        
        # Try to create duplicate vote - should fail
        with self.assertRaises(IntegrityError):
            Vote.objects.create(
                user=self.user2,
                post=self.post
            )
    
    def test_vote_different_users_same_post(self):
        """Test that different users can vote on the same post."""
        vote1 = Vote.objects.create(
            user=self.user1,
            post=self.post
        )
        vote2 = Vote.objects.create(
            user=self.user2,
            post=self.post
        )
        
        self.assertEqual(Vote.objects.count(), 2)
        self.assertNotEqual(vote1.user, vote2.user)
    
    def test_vote_same_user_different_posts(self):
        """Test that the same user can vote on different posts."""
        post2 = Post.objects.create(
            content='Another test post',
            thread=self.thread,
            author=self.user1
        )
        
        vote1 = Vote.objects.create(
            user=self.user2,
            post=self.post
        )
        vote2 = Vote.objects.create(
            user=self.user2,
            post=post2
        )
        
        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(vote1.user, vote2.user)
        self.assertNotEqual(vote1.post, vote2.post)
    
    def test_vote_cascade_deletion_with_user(self):
        """Test that votes are deleted when user is deleted."""
        Vote.objects.create(
            user=self.user2,
            post=self.post
        )
        
        self.assertEqual(Vote.objects.count(), 1)
        
        self.user2.delete()
        self.assertEqual(Vote.objects.count(), 0)
    
    def test_vote_cascade_deletion_with_post(self):
        """Test that votes are deleted when post is deleted."""
        Vote.objects.create(
            user=self.user2,
            post=self.post
        )
        
        self.assertEqual(Vote.objects.count(), 1)
        
        self.post.delete()
        self.assertEqual(Vote.objects.count(), 0)
    
    def test_vote_ordering(self):
        """Test that votes are ordered by creation date (newest first)."""
        post2 = Post.objects.create(
            content='Another post',
            thread=self.thread,
            author=self.user1
        )
        
        vote1 = Vote.objects.create(
            user=self.user2,
            post=self.post
        )
        vote2 = Vote.objects.create(
            user=self.user2,
            post=post2
        )
        
        votes = Vote.objects.all()
        self.assertEqual(votes[0], vote2)  # Newest first
        self.assertEqual(votes[1], vote1)


class PostVoteCountTestCase(TestCase):
    """Test the vote_count field on Post model."""
    
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
        self.post = Post.objects.create(
            content='Test post content',
            thread=self.thread,
            author=self.user1
        )
    
    def test_post_vote_count_default_zero(self):
        """Test that post vote_count defaults to 0."""
        self.assertEqual(self.post.vote_count, 0)
    
    def test_vote_count_updates_on_vote_creation(self):
        """Test that vote_count updates when a vote is created."""
        initial_count = self.post.vote_count
        
        Vote.objects.create(
            user=self.user2,
            post=self.post
        )
        
        self.post.refresh_from_db()
        self.assertEqual(self.post.vote_count, initial_count + 1)
    
    def test_vote_count_updates_on_vote_deletion(self):
        """Test that vote_count updates when a vote is deleted."""
        vote = Vote.objects.create(
            user=self.user2,
            post=self.post
        )
        
        self.post.refresh_from_db()
        initial_count = self.post.vote_count
        
        vote.delete()
        
        self.post.refresh_from_db()
        self.assertEqual(self.post.vote_count, initial_count - 1)
    
    def test_multiple_votes_update_count_correctly(self):
        """Test that multiple votes update the count correctly."""
        user3 = User.objects.create_user(
            email='user3@example.com',
            password='testpass123',
            display_name='User Three',
            is_active=True,
            is_email_verified=True
        )
        
        # Create multiple votes
        Vote.objects.create(user=self.user1, post=self.post)
        Vote.objects.create(user=self.user2, post=self.post)
        Vote.objects.create(user=user3, post=self.post)
        
        self.post.refresh_from_db()
        self.assertEqual(self.post.vote_count, 3)


class VoteViewTestCase(TestCase):
    """Test the AJAX voting view functionality."""
    
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
        self.post = Post.objects.create(
            content='Test post content',
            thread=self.thread,
            author=self.user1
        )
        self.vote_url = reverse('forums:vote_post', kwargs={'post_id': self.post.id})
    
    def test_unauthenticated_user_cannot_vote(self):
        """Test that unauthenticated users cannot vote."""
        response = self.client.post(self.vote_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_vote_requires_ajax_request(self):
        """Test that voting requires an AJAX request."""
        self.client.login(email='user2@example.com', password='testpass123')
        
        # Regular POST request (not AJAX)
        response = self.client.post(self.vote_url)
        self.assertEqual(response.status_code, 400)
    
    def test_vote_requires_post_method(self):
        """Test that voting requires POST method."""
        self.client.login(email='user2@example.com', password='testpass123')
        
        response = self.client.get(
            self.vote_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 405)  # Method not allowed
    
    def test_user_can_vote_on_post(self):
        """Test that authenticated user can vote on a post."""
        self.client.login(email='user2@example.com', password='testpass123')
        
        response = self.client.post(
            self.vote_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        json_response = response.json()
        self.assertTrue(json_response['voted'])
        self.assertEqual(json_response['vote_count'], 1)
        
        # Check that vote was created
        self.assertTrue(Vote.objects.filter(user=self.user2, post=self.post).exists())
    
    def test_user_can_remove_vote(self):
        """Test that user can remove their vote."""
        # Create initial vote
        Vote.objects.create(user=self.user2, post=self.post)
        
        self.client.login(email='user2@example.com', password='testpass123')
        
        response = self.client.post(
            self.vote_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        json_response = response.json()
        self.assertFalse(json_response['voted'])
        self.assertEqual(json_response['vote_count'], 0)
        
        # Check that vote was deleted
        self.assertFalse(Vote.objects.filter(user=self.user2, post=self.post).exists())
    
    def test_vote_count_in_response(self):
        """Test that response includes correct vote count."""
        # Create some initial votes
        user3 = User.objects.create_user(
            email='user3@example.com',
            password='testpass123',
            display_name='User Three',
            is_active=True,
            is_email_verified=True
        )
        Vote.objects.create(user=user3, post=self.post)
        
        self.client.login(email='user2@example.com', password='testpass123')
        
        response = self.client.post(
            self.vote_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        json_response = response.json()
        self.assertEqual(json_response['vote_count'], 2)  # user3 + user2
    
    def test_vote_nonexistent_post_404(self):
        """Test voting on non-existent post returns 404."""
        self.client.login(email='user2@example.com', password='testpass123')
        
        nonexistent_url = reverse('forums:vote_post', kwargs={'post_id': 99999})
        
        response = self.client.post(
            nonexistent_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_author_cannot_vote_on_own_post(self):
        """Test that post author cannot vote on their own post."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.post(
            self.vote_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        
        json_response = response.json()
        self.assertIn('error', json_response)
        self.assertIn('own post', json_response['error'])


class VoteSignalsTestCase(TestCase):
    """Test Django signals for vote count updates."""
    
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
        self.post = Post.objects.create(
            content='Test post content',
            thread=self.thread,
            author=self.user1
        )
    
    def test_signal_updates_vote_count_on_creation(self):
        """Test that signal updates post vote_count when vote is created."""
        initial_count = self.post.vote_count
        
        Vote.objects.create(user=self.user2, post=self.post)
        
        self.post.refresh_from_db()
        self.assertEqual(self.post.vote_count, initial_count + 1)
    
    def test_signal_updates_vote_count_on_deletion(self):
        """Test that signal updates post vote_count when vote is deleted."""
        vote = Vote.objects.create(user=self.user2, post=self.post)
        
        self.post.refresh_from_db()
        initial_count = self.post.vote_count
        
        vote.delete()
        
        self.post.refresh_from_db()
        self.assertEqual(self.post.vote_count, initial_count - 1)
    
    def test_bulk_vote_operations_update_count(self):
        """Test that bulk operations correctly update vote count."""
        user3 = User.objects.create_user(
            email='user3@example.com',
            password='testpass123',
            display_name='User Three',
            is_active=True,
            is_email_verified=True
        )
        
        # Create multiple votes with bulk_create (doesn't trigger signals)
        votes = [
            Vote(user=self.user2, post=self.post),
            Vote(user=user3, post=self.post),
        ]
        
        Vote.objects.bulk_create(votes)
        
        # Create one vote individually to trigger signals
        vote1 = Vote.objects.create(user=self.user1, post=self.post)
        
        self.post.refresh_from_db()
        expected_count = Vote.objects.filter(post=self.post).count()
        self.assertEqual(self.post.vote_count, expected_count)  # Signal updates count correctly


class VoteDisplayTestCase(TestCase):
    """Test vote display in templates."""
    
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
        self.post = Post.objects.create(
            content='Test post content',
            thread=self.thread,
            author=self.user1
        )
        # Create initial post so thread has content
        Post.objects.create(
            content='Initial thread content',
            thread=self.thread,
            author=self.user1
        )
    
    def test_vote_count_displayed_in_thread_view(self):
        """Test that vote count is displayed in thread detail view."""
        # Create some votes
        Vote.objects.create(user=self.user2, post=self.post)
        
        thread_url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category.slug,
            'subcategory_slug': self.subcategory.slug,
            'thread_slug': self.thread.slug
        })
        
        response = self.client.get(thread_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that vote count is displayed (format: "1<br>vote")
        self.assertContains(response, '<strong>1</strong>')
        self.assertContains(response, '>vote<')
    
    def test_vote_button_for_authenticated_users(self):
        """Test that vote button is shown for authenticated users."""
        self.client.login(email='user2@example.com', password='testpass123')
        
        thread_url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category.slug,
            'subcategory_slug': self.subcategory.slug,
            'thread_slug': self.thread.slug
        })
        
        response = self.client.get(thread_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that vote button is present
        self.assertContains(response, 'vote-btn')
    
    def test_no_vote_button_for_unauthenticated_users(self):
        """Test that vote button is not shown for unauthenticated users."""
        thread_url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category.slug,
            'subcategory_slug': self.subcategory.slug,
            'thread_slug': self.thread.slug
        })
        
        response = self.client.get(thread_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that vote button is not present
        self.assertNotContains(response, 'vote-btn')
    
    def test_voted_state_displayed_correctly(self):
        """Test that user's vote state is displayed correctly."""
        # User votes on the post
        Vote.objects.create(user=self.user2, post=self.post)
        
        self.client.login(email='user2@example.com', password='testpass123')
        
        thread_url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category.slug,
            'subcategory_slug': self.subcategory.slug,
            'thread_slug': self.thread.slug
        })
        
        response = self.client.get(thread_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that voted state is indicated
        self.assertContains(response, 'voted')


class VoteAdminTestCase(TestCase):
    """Test Vote model in Django admin."""
    
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
        self.post = Post.objects.create(
            content='Test post content',
            thread=self.thread,
            author=self.user1
        )
    
    def test_vote_admin_can_create_votes(self):
        """Test that admin can create votes through the interface."""
        from django.contrib.admin.sites import site
        from forums.models import Vote
        
        # Check that Vote is registered with admin
        self.assertIn(Vote, site._registry)
    
    def test_vote_admin_list_display(self):
        """Test that vote admin has appropriate list display."""
        vote = Vote.objects.create(user=self.user2, post=self.post)
        
        # Test that we can create and display votes
        self.assertEqual(str(vote), f"{self.user2.display_name} voted on post in {self.thread.title}")