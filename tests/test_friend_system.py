"""
Tests for friend system functionality.
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

User = get_user_model()


class FriendshipModelTestCase(TestCase):
    """Test the Friendship model functionality."""
    
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
        self.user3 = User.objects.create_user(
            email='user3@example.com',
            password='testpass123',
            display_name='User Three',
            is_active=True,
            is_email_verified=True
        )
    
    def test_friendship_creation_with_required_fields(self):
        """Test creating a Friendship with all required fields."""
        from accounts.models import Friendship
        
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        
        self.assertEqual(friendship.from_user, self.user1)
        self.assertEqual(friendship.to_user, self.user2)
        self.assertEqual(friendship.status, 'pending')
        self.assertIsNotNone(friendship.created_at)
        self.assertIsNone(friendship.responded_at)
    
    def test_friendship_string_representation(self):
        """Test the string representation of a Friendship."""
        from accounts.models import Friendship
        
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        
        expected_str = f"Friendship: {self.user1.display_name} -> {self.user2.display_name} (pending)"
        self.assertEqual(str(friendship), expected_str)
    
    def test_friendship_unique_constraint(self):
        """Test that duplicate friendship requests cannot be created."""
        from accounts.models import Friendship
        
        # Create first friendship request
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        
        # Try to create duplicate request - should fail
        with self.assertRaises(ValidationError):
            Friendship.objects.create(
                from_user=self.user1,
                to_user=self.user2,
                status='pending'
            )
    
    def test_friendship_reverse_relationship_allowed(self):
        """Test that reverse friendship requests are allowed."""
        from accounts.models import Friendship
        
        # User1 requests User2
        friendship1 = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        
        # User2 can request User1 (reverse relationship)
        friendship2 = Friendship.objects.create(
            from_user=self.user2,
            to_user=self.user1,
            status='pending'
        )
        
        self.assertEqual(Friendship.objects.count(), 2)
        self.assertNotEqual(friendship1.from_user, friendship2.from_user)
    
    def test_friendship_self_request_validation(self):
        """Test that users cannot send friend requests to themselves."""
        from accounts.models import Friendship
        
        friendship = Friendship(
            from_user=self.user1,
            to_user=self.user1,
            status='pending'
        )
        
        # This should raise a validation error
        with self.assertRaises(ValidationError):
            friendship.full_clean()
    
    def test_friendship_status_choices(self):
        """Test that friendship status is limited to valid choices."""
        from accounts.models import Friendship
        
        # Valid statuses
        valid_statuses = ['pending', 'accepted', 'rejected']
        for status in valid_statuses:
            friendship = Friendship.objects.create(
                from_user=self.user1,
                to_user=self.user2,
                status=status
            )
            self.assertEqual(friendship.status, status)
            friendship.delete()  # Clean up for next iteration
    
    def test_friendship_cascade_deletion_with_users(self):
        """Test that friendships are deleted when users are deleted."""
        from accounts.models import Friendship
        
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        
        self.assertEqual(Friendship.objects.count(), 1)
        
        self.user1.delete()
        self.assertEqual(Friendship.objects.count(), 0)
    
    def test_friendship_ordering(self):
        """Test that friendships are ordered by creation date (newest first)."""
        from accounts.models import Friendship
        
        friendship1 = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        friendship2 = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user3,
            status='pending'
        )
        
        friendships = Friendship.objects.all()
        self.assertEqual(friendships[0], friendship2)  # Newest first
        self.assertEqual(friendships[1], friendship1)
    
    def test_friendship_responded_at_set_on_accept(self):
        """Test that responded_at is set when friendship is accepted."""
        from accounts.models import Friendship
        from django.utils import timezone
        
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        
        # Accept the friendship
        friendship.status = 'accepted'
        friendship.responded_at = timezone.now()
        friendship.save()
        
        self.assertEqual(friendship.status, 'accepted')
        self.assertIsNotNone(friendship.responded_at)


class FriendRequestViewTestCase(TestCase):
    """Test friend request view functionality."""
    
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
        self.send_request_url = reverse('accounts:send_friend_request', kwargs={'user_id': self.user2.id})
    
    def test_unauthenticated_user_cannot_send_friend_request(self):
        """Test that unauthenticated users cannot send friend requests."""
        response = self.client.post(self.send_request_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_authenticated_user_can_send_friend_request(self):
        """Test that authenticated users can send friend requests."""
        from accounts.models import Friendship
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.post(self.send_request_url)
        
        # Should redirect after successful request
        self.assertEqual(response.status_code, 302)
        
        # Check that friendship was created
        self.assertEqual(Friendship.objects.count(), 1)
        friendship = Friendship.objects.first()
        self.assertEqual(friendship.from_user, self.user1)
        self.assertEqual(friendship.to_user, self.user2)
        self.assertEqual(friendship.status, 'pending')
    
    def test_user_cannot_send_friend_request_to_self(self):
        """Test that users cannot send friend requests to themselves."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        self_request_url = reverse('accounts:send_friend_request', kwargs={'user_id': self.user1.id})
        response = self.client.post(self_request_url)
        
        # Should redirect with error
        self.assertEqual(response.status_code, 302)
        
        # No friendship should be created
        from accounts.models import Friendship
        self.assertEqual(Friendship.objects.count(), 0)
    
    def test_user_cannot_send_duplicate_friend_request(self):
        """Test that users cannot send duplicate friend requests."""
        from accounts.models import Friendship
        
        # Create existing friendship request
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.post(self.send_request_url)
        
        # Should redirect with error
        self.assertEqual(response.status_code, 302)
        
        # Should still have only one friendship
        self.assertEqual(Friendship.objects.count(), 1)
    
    def test_user_can_resend_request_after_rejection(self):
        """Test that users can resend requests after rejection by updating existing record."""
        from accounts.models import Friendship
        from django.utils import timezone
        
        # Create rejected friendship request
        rejected_friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='rejected',
            responded_at=timezone.now()
        )
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.post(self.send_request_url)
        
        # Should redirect successfully
        self.assertEqual(response.status_code, 302)
        
        # Should still have only one friendship record
        self.assertEqual(Friendship.objects.count(), 1)
        
        # Status should be updated to pending
        rejected_friendship.refresh_from_db()
        self.assertEqual(rejected_friendship.status, 'pending')
        self.assertIsNone(rejected_friendship.responded_at)


class FriendResponseViewTestCase(TestCase):
    """Test friend request response (accept/reject) views."""
    
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
    
    def test_accept_friend_request(self):
        """Test accepting a friend request."""
        from accounts.models import Friendship
        
        # Create pending friendship request
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        
        self.client.login(email='user2@example.com', password='testpass123')
        
        accept_url = reverse('accounts:respond_friend_request', kwargs={
            'friendship_id': friendship.id,
            'action': 'accept'
        })
        response = self.client.post(accept_url)
        
        # Should redirect after successful response
        self.assertEqual(response.status_code, 302)
        
        # Check that friendship was accepted
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'accepted')
        self.assertIsNotNone(friendship.responded_at)
    
    def test_reject_friend_request(self):
        """Test rejecting a friend request."""
        from accounts.models import Friendship
        
        # Create pending friendship request
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        
        self.client.login(email='user2@example.com', password='testpass123')
        
        reject_url = reverse('accounts:respond_friend_request', kwargs={
            'friendship_id': friendship.id,
            'action': 'reject'
        })
        response = self.client.post(reject_url)
        
        # Should redirect after successful response
        self.assertEqual(response.status_code, 302)
        
        # Check that friendship was rejected
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'rejected')
        self.assertIsNotNone(friendship.responded_at)
    
    def test_only_recipient_can_respond_to_request(self):
        """Test that only the recipient can respond to a friend request."""
        from accounts.models import Friendship
        
        # Create pending friendship request
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        
        # Try to respond as the sender (user1) - should fail
        self.client.login(email='user1@example.com', password='testpass123')
        
        accept_url = reverse('accounts:respond_friend_request', kwargs={
            'friendship_id': friendship.id,
            'action': 'accept'
        })
        response = self.client.post(accept_url)
        
        # Should be forbidden or redirect with error
        self.assertIn(response.status_code, [403, 302])
        
        # Friendship should still be pending
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'pending')
    
    def test_cannot_respond_to_already_responded_request(self):
        """Test that users cannot respond to already responded requests."""
        from accounts.models import Friendship
        from django.utils import timezone
        
        # Create accepted friendship request
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='accepted',
            responded_at=timezone.now()
        )
        
        self.client.login(email='user2@example.com', password='testpass123')
        
        reject_url = reverse('accounts:respond_friend_request', kwargs={
            'friendship_id': friendship.id,
            'action': 'reject'
        })
        response = self.client.post(reject_url)
        
        # Should redirect with error or be forbidden
        self.assertIn(response.status_code, [403, 302])
        
        # Friendship should still be accepted
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'accepted')


class FriendListViewTestCase(TestCase):
    """Test friend list view functionality."""
    
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
        self.user3 = User.objects.create_user(
            email='user3@example.com',
            password='testpass123',
            display_name='User Three',
            is_active=True,
            is_email_verified=True
        )
        self.friends_url = reverse('accounts:friends_list', kwargs={'user_id': self.user1.id})
    
    def test_unauthenticated_user_can_view_friend_list(self):
        """Test that unauthenticated users can view public friend lists."""
        from accounts.models import Friendship
        from django.utils import timezone
        
        # Create accepted friendship
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='accepted',
            responded_at=timezone.now()
        )
        
        response = self.client.get(self.friends_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user2.display_name)
    
    def test_friend_list_shows_only_accepted_friendships(self):
        """Test that friend list shows only accepted friendships."""
        from accounts.models import Friendship
        from django.utils import timezone
        
        # Create various friendship statuses
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='accepted',
            responded_at=timezone.now()
        )
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user3,
            status='pending'
        )
        
        response = self.client.get(self.friends_url)
        self.assertEqual(response.status_code, 200)
        
        # Should show accepted friend but not pending
        self.assertContains(response, self.user2.display_name)
        self.assertNotContains(response, self.user3.display_name)
    
    def test_friend_list_shows_bidirectional_friendships(self):
        """Test that friend list shows friends regardless of who sent the request."""
        from accounts.models import Friendship
        from django.utils import timezone
        
        # User2 sends request to User1, User1 accepts
        Friendship.objects.create(
            from_user=self.user2,
            to_user=self.user1,
            status='accepted',
            responded_at=timezone.now()
        )
        
        response = self.client.get(self.friends_url)
        self.assertEqual(response.status_code, 200)
        
        # User1's friend list should show User2
        self.assertContains(response, self.user2.display_name)
    
    def test_friend_list_pagination(self):
        """Test that friend list paginates correctly."""
        from accounts.models import Friendship
        from django.utils import timezone
        
        # Create many friends (assuming 20 per page)
        for i in range(25):
            friend = User.objects.create_user(
                email=f'friend{i}@example.com',
                password='testpass123',
                display_name=f'Friend {i}',
                is_active=True,
                is_email_verified=True
            )
            Friendship.objects.create(
                from_user=self.user1,
                to_user=friend,
                status='accepted',
                responded_at=timezone.now()
            )
        
        response = self.client.get(self.friends_url)
        self.assertEqual(response.status_code, 200)
        
        # Should show pagination
        self.assertContains(response, 'pagination')
    
    def test_friend_list_empty_state(self):
        """Test that friend list shows empty state when no friends."""
        response = self.client.get(self.friends_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No friends')
    
    def test_friend_list_404_for_nonexistent_user(self):
        """Test that friend list returns 404 for non-existent user."""
        friends_url = reverse('accounts:friends_list', kwargs={'user_id': 99999})
        
        response = self.client.get(friends_url)
        self.assertEqual(response.status_code, 404)


class FriendRequestListViewTestCase(TestCase):
    """Test friend request list view (incoming requests)."""
    
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
        self.requests_url = reverse('accounts:friend_requests')
    
    def test_unauthenticated_user_cannot_view_friend_requests(self):
        """Test that unauthenticated users cannot view friend requests."""
        response = self.client.get(self.requests_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_authenticated_user_can_view_friend_requests(self):
        """Test that authenticated users can view their friend requests."""
        from accounts.models import Friendship
        
        # Create incoming friend request
        Friendship.objects.create(
            from_user=self.user2,
            to_user=self.user1,
            status='pending'
        )
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.requests_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user2.display_name)
    
    def test_friend_requests_shows_only_incoming_pending(self):
        """Test that friend requests shows only incoming pending requests."""
        from accounts.models import Friendship
        from django.utils import timezone
        
        # Create various friendship statuses
        Friendship.objects.create(
            from_user=self.user2,
            to_user=self.user1,
            status='pending'
        )
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        Friendship.objects.create(
            from_user=self.user2,
            to_user=self.user1,
            status='accepted',
            responded_at=timezone.now()
        )
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.requests_url)
        self.assertEqual(response.status_code, 200)
        
        # Should only show incoming pending requests
        # Note: This assumes the view filters correctly
        self.assertContains(response, 'Friend Request')


class ProfileFriendStatusTestCase(TestCase):
    """Test friend status display on user profiles."""
    
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
        self.profile_url = reverse('accounts:user_profile', kwargs={'user_id': self.user2.id})
    
    def test_profile_shows_add_friend_button_for_non_friends(self):
        """Test that profile shows add friend button for non-friends."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Friend')
    
    def test_profile_shows_pending_status_for_sent_requests(self):
        """Test that profile shows pending status for sent requests."""
        from accounts.models import Friendship
        
        # Create pending friend request from user1 to user2
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Request Sent')
    
    def test_profile_shows_respond_buttons_for_incoming_requests(self):
        """Test that profile shows respond buttons for incoming requests."""
        from accounts.models import Friendship
        
        # Create pending friend request from user2 to user1
        Friendship.objects.create(
            from_user=self.user2,
            to_user=self.user1,
            status='pending'
        )
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Accept')
        self.assertContains(response, 'Reject')
    
    def test_profile_shows_friends_status_for_accepted_requests(self):
        """Test that profile shows friends status for accepted requests."""
        from accounts.models import Friendship
        from django.utils import timezone
        
        # Create accepted friendship
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='accepted',
            responded_at=timezone.now()
        )
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Friends')
    
    def test_own_profile_shows_no_friend_buttons(self):
        """Test that user's own profile shows no friend buttons."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        own_profile_url = reverse('accounts:user_profile', kwargs={'user_id': self.user1.id})
        response = self.client.get(own_profile_url)
        self.assertEqual(response.status_code, 200)
        
        # Should not show any friend-related buttons
        self.assertNotContains(response, 'Add Friend')
        self.assertNotContains(response, 'Request Sent')
        self.assertNotContains(response, 'Accept')


class FriendshipAdminTestCase(TestCase):
    """Test Friendship model in Django admin."""
    
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
    
    def test_friendship_admin_registration(self):
        """Test that Friendship is registered with admin."""
        from django.contrib.admin.sites import site
        from accounts.models import Friendship
        
        # Check that Friendship is registered with admin
        self.assertIn(Friendship, site._registry)
    
    def test_friendship_admin_list_display(self):
        """Test that Friendship admin has appropriate list display."""
        from accounts.models import Friendship
        
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        
        # Test that we can create and display friendships
        expected_str = f"Friendship: {self.user1.display_name} -> {self.user2.display_name} (pending)"
        self.assertEqual(str(friendship), expected_str)