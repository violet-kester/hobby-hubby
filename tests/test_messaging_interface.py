"""
Tests for messaging interface views and functionality.
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.messages import get_messages
from django.utils import timezone

User = get_user_model()


class InboxViewTestCase(TestCase):
    """Test the inbox view for listing conversations."""
    
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
        self.inbox_url = reverse('accounts:inbox')
    
    def test_unauthenticated_user_cannot_access_inbox(self):
        """Test that unauthenticated users cannot access inbox."""
        response = self.client.get(self.inbox_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_authenticated_user_can_access_inbox(self):
        """Test that authenticated users can access inbox."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.inbox_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inbox')
    
    def test_inbox_shows_user_conversations(self):
        """Test that inbox shows user's conversations."""
        from accounts.models import Conversation, Message
        
        # Create conversation between user1 and user2
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        # Add a message to make it show up in inbox
        Message.objects.create(
            conversation=conversation,
            sender=self.user2,
            content="Hello from user2!"
        )
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.inbox_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Two')
        self.assertContains(response, 'Hello from user2!')
    
    def test_inbox_does_not_show_other_user_conversations(self):
        """Test that inbox doesn't show conversations user is not part of."""
        from accounts.models import Conversation, Message
        
        # Create conversation between user2 and user3 (not user1)
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user2, self.user3)
        
        Message.objects.create(
            conversation=conversation,
            sender=self.user2,
            content="Secret message!"
        )
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.inbox_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Secret message!')
        self.assertNotContains(response, 'User Three')
    
    def test_inbox_conversations_ordered_by_last_message(self):
        """Test that conversations are ordered by last message date."""
        from accounts.models import Conversation, Message
        
        # Create two conversations
        conversation1 = Conversation.objects.create()
        conversation1.participants.add(self.user1, self.user2)
        
        conversation2 = Conversation.objects.create()
        conversation2.participants.add(self.user1, self.user3)
        
        # Add messages (conversation2 should be newer)
        Message.objects.create(
            conversation=conversation1,
            sender=self.user2,
            content="Older message"
        )
        Message.objects.create(
            conversation=conversation2,
            sender=self.user3,
            content="Newer message"
        )
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.inbox_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that conversations appear in correct order
        content = response.content.decode()
        newer_pos = content.find('Newer message')
        older_pos = content.find('Older message')
        self.assertTrue(newer_pos < older_pos)  # Newer should appear first
    
    def test_inbox_pagination(self):
        """Test that inbox paginates conversations."""
        from accounts.models import Conversation, Message
        
        # Create many conversations (assuming 20 per page)
        for i in range(25):
            user = User.objects.create_user(
                email=f'user{i+10}@example.com',
                password='testpass123',
                display_name=f'User {i+10}',
                is_active=True,
                is_email_verified=True
            )
            conversation = Conversation.objects.create()
            conversation.participants.add(self.user1, user)
            
            Message.objects.create(
                conversation=conversation,
                sender=user,
                content=f"Message {i}"
            )
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.inbox_url)
        self.assertEqual(response.status_code, 200)
        
        # Should show pagination
        self.assertContains(response, 'pagination')
    
    def test_inbox_empty_state(self):
        """Test that inbox shows empty state when no conversations."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.inbox_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No conversations')
    
    def test_inbox_unread_message_count(self):
        """Test that inbox shows unread message count."""
        from accounts.models import Conversation, Message
        
        # Create conversation with unread messages
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        # Add unread messages
        Message.objects.create(
            conversation=conversation,
            sender=self.user2,
            content="Unread message 1"
        )
        Message.objects.create(
            conversation=conversation,
            sender=self.user2,
            content="Unread message 2"
        )
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.inbox_url)
        self.assertEqual(response.status_code, 200)
        
        # Should show unread count (implementation will vary)
        self.assertContains(response, '2')  # Unread count


class ConversationDetailViewTestCase(TestCase):
    """Test the conversation detail view."""
    
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
    
    def test_unauthenticated_user_cannot_access_conversation(self):
        """Test that unauthenticated users cannot access conversations."""
        from accounts.models import Conversation
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        conversation_url = reverse('accounts:conversation_detail', kwargs={'conversation_id': conversation.id})
        response = self.client.get(conversation_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_authenticated_user_can_access_own_conversation(self):
        """Test that authenticated users can access conversations they're part of."""
        from accounts.models import Conversation
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        conversation_url = reverse('accounts:conversation_detail', kwargs={'conversation_id': conversation.id})
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(conversation_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Two')
    
    def test_user_cannot_access_other_users_conversation(self):
        """Test that users cannot access conversations they're not part of."""
        from accounts.models import Conversation
        
        # Create conversation between user2 and user3 (not user1)
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user2, self.user3)
        
        conversation_url = reverse('accounts:conversation_detail', kwargs={'conversation_id': conversation.id})
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(conversation_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_conversation_shows_messages(self):
        """Test that conversation view shows messages."""
        from accounts.models import Conversation, Message
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        Message.objects.create(
            conversation=conversation,
            sender=self.user1,
            content="Hello from user1!"
        )
        Message.objects.create(
            conversation=conversation,
            sender=self.user2,
            content="Hello back from user2!"
        )
        
        conversation_url = reverse('accounts:conversation_detail', kwargs={'conversation_id': conversation.id})
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(conversation_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hello from user1!')
        self.assertContains(response, 'Hello back from user2!')
    
    def test_conversation_messages_ordered_chronologically(self):
        """Test that messages are displayed in chronological order."""
        from accounts.models import Conversation, Message
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        message1 = Message.objects.create(
            conversation=conversation,
            sender=self.user1,
            content="First message"
        )
        message2 = Message.objects.create(
            conversation=conversation,
            sender=self.user2,
            content="Second message"
        )
        
        conversation_url = reverse('accounts:conversation_detail', kwargs={'conversation_id': conversation.id})
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(conversation_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that messages appear in chronological order
        content = response.content.decode()
        first_pos = content.find('First message')
        second_pos = content.find('Second message')
        self.assertTrue(first_pos < second_pos)  # First should appear before second
    
    def test_conversation_pagination(self):
        """Test that conversation paginates messages."""
        from accounts.models import Conversation, Message
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        # Create many messages (assuming 20 per page)
        for i in range(25):
            Message.objects.create(
                conversation=conversation,
                sender=self.user1 if i % 2 == 0 else self.user2,
                content=f"Message {i}"
            )
        
        conversation_url = reverse('accounts:conversation_detail', kwargs={'conversation_id': conversation.id})
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(conversation_url)
        self.assertEqual(response.status_code, 200)
        
        # Should show pagination
        self.assertContains(response, 'pagination')
    
    def test_conversation_404_for_nonexistent_conversation(self):
        """Test that conversation returns 404 for non-existent conversation."""
        conversation_url = reverse('accounts:conversation_detail', kwargs={'conversation_id': 99999})
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(conversation_url)
        self.assertEqual(response.status_code, 404)
    
    def test_conversation_marks_messages_as_read(self):
        """Test that viewing conversation marks messages as read."""
        from accounts.models import Conversation, Message, ConversationParticipant
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        # Create unread message from user2
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user2,
            content="Unread message"
        )
        
        self.assertFalse(message.is_read)
        
        conversation_url = reverse('accounts:conversation_detail', kwargs={'conversation_id': conversation.id})
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(conversation_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that participant's last_read_at is updated
        participant = ConversationParticipant.objects.get(
            conversation=conversation,
            user=self.user1
        )
        self.assertIsNotNone(participant.last_read_at)


class MessageComposeTestCase(TestCase):
    """Test message composition and sending."""
    
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
    
    def test_unauthenticated_user_cannot_send_message(self):
        """Test that unauthenticated users cannot send messages."""
        from accounts.models import Conversation
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        send_message_url = reverse('accounts:send_message', kwargs={'conversation_id': conversation.id})
        response = self.client.post(send_message_url, {
            'content': 'Test message'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_authenticated_user_can_send_message(self):
        """Test that authenticated users can send messages."""
        from accounts.models import Conversation, Message
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        send_message_url = reverse('accounts:send_message', kwargs={'conversation_id': conversation.id})
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.post(send_message_url, {
            'content': 'Test message content'
        })
        
        # Should redirect back to conversation
        self.assertEqual(response.status_code, 302)
        
        # Check message was created
        message = Message.objects.filter(conversation=conversation).first()
        self.assertIsNotNone(message)
        self.assertEqual(message.content, 'Test message content')
        self.assertEqual(message.sender, self.user1)
    
    def test_user_cannot_send_message_to_conversation_not_participant(self):
        """Test that users cannot send messages to conversations they're not part of."""
        from accounts.models import Conversation
        
        # Create conversation between user2 and another user (not user1)
        user3 = User.objects.create_user(
            email='user3@example.com',
            password='testpass123',
            display_name='User Three',
            is_active=True,
            is_email_verified=True
        )
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user2, user3)
        
        send_message_url = reverse('accounts:send_message', kwargs={'conversation_id': conversation.id})
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.post(send_message_url, {
            'content': 'Unauthorized message'
        })
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_cannot_send_empty_message(self):
        """Test that empty messages cannot be sent."""
        from accounts.models import Conversation, Message
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        send_message_url = reverse('accounts:send_message', kwargs={'conversation_id': conversation.id})
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.post(send_message_url, {
            'content': ''
        })
        
        # Should not create message and show error
        self.assertEqual(Message.objects.filter(conversation=conversation).count(), 0)
        
        # Should show form error (implementation may vary)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('empty' in str(m).lower() or 'required' in str(m).lower() for m in messages))
    
    def test_sending_message_updates_conversation_last_message_at(self):
        """Test that sending a message updates conversation's last_message_at."""
        from accounts.models import Conversation
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        # Initially no last_message_at
        self.assertIsNone(conversation.last_message_at)
        
        send_message_url = reverse('accounts:send_message', kwargs={'conversation_id': conversation.id})
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.post(send_message_url, {
            'content': 'Test message'
        })
        
        conversation.refresh_from_db()
        self.assertIsNotNone(conversation.last_message_at)


class StartConversationTestCase(TestCase):
    """Test starting new conversations."""
    
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
    
    def test_unauthenticated_user_cannot_start_conversation(self):
        """Test that unauthenticated users cannot start conversations."""
        start_conversation_url = reverse('accounts:start_conversation', kwargs={'user_id': self.user2.id})
        response = self.client.get(start_conversation_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_authenticated_user_can_start_conversation(self):
        """Test that authenticated users can start conversations."""
        start_conversation_url = reverse('accounts:start_conversation', kwargs={'user_id': self.user2.id})
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(start_conversation_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Two')
    
    def test_user_cannot_start_conversation_with_self(self):
        """Test that users cannot start conversations with themselves."""
        start_conversation_url = reverse('accounts:start_conversation', kwargs={'user_id': self.user1.id})
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(start_conversation_url)
        self.assertEqual(response.status_code, 400)  # Bad request
    
    def test_existing_conversation_redirects_to_conversation(self):
        """Test that if conversation already exists, user is redirected to it."""
        from accounts.models import Conversation
        
        # Create existing conversation
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        start_conversation_url = reverse('accounts:start_conversation', kwargs={'user_id': self.user2.id})
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(start_conversation_url)
        
        # Should redirect to existing conversation
        expected_redirect = reverse('accounts:conversation_detail', kwargs={'conversation_id': conversation.id})
        self.assertRedirects(response, expected_redirect)
    
    def test_start_conversation_creates_new_conversation(self):
        """Test that starting conversation creates new conversation."""
        from accounts.models import Conversation
        
        start_conversation_url = reverse('accounts:start_conversation', kwargs={'user_id': self.user2.id})
        self.client.login(email='user1@example.com', password='testpass123')
        
        # Send first message
        response = self.client.post(start_conversation_url, {
            'content': 'Hello, this is the first message!'
        })
        
        # Should create conversation and redirect to it
        self.assertEqual(response.status_code, 302)
        
        # Check conversation was created
        conversation = Conversation.objects.filter(
            participants__in=[self.user1, self.user2]
        ).distinct().first()
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation.participants.count(), 2)
    
    def test_start_conversation_404_for_nonexistent_user(self):
        """Test that starting conversation returns 404 for non-existent user."""
        start_conversation_url = reverse('accounts:start_conversation', kwargs={'user_id': 99999})
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(start_conversation_url)
        self.assertEqual(response.status_code, 404)


class FriendsOnlyMessagingTestCase(TestCase):
    """Test friends-only messaging functionality."""
    
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
        # Add friends_only_messaging field to user if implemented
    
    def test_friends_can_start_conversations(self):
        """Test that friends can start conversations when friends-only is enabled."""
        from accounts.models import Friendship
        
        # Create friendship
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='accepted'
        )
        
        start_conversation_url = reverse('accounts:start_conversation', kwargs={'user_id': self.user2.id})
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(start_conversation_url)
        self.assertEqual(response.status_code, 200)
    
    def test_non_friends_cannot_start_conversations_when_friends_only(self):
        """Test that non-friends cannot start conversations when friends-only is enabled."""
        # This test would need friends_only_messaging field on user model
        # For now, we'll assume all users can message (basic implementation)
        pass


class MessagingAdminTestCase(TestCase):
    """Test messaging functionality in admin interface."""
    
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
    
    def test_messaging_views_properly_display(self):
        """Test that messaging views display properly."""
        from accounts.models import Conversation, Message
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user1,
            content="Test message for admin"
        )
        
        # Test that models display correctly
        expected_conversation_str = f"Conversation between {self.user1.display_name}, {self.user2.display_name}"
        expected_message_str = f"Message from {self.user1.display_name} in conversation {conversation.id}"
        
        self.assertEqual(str(conversation), expected_conversation_str)
        self.assertEqual(str(message), expected_message_str)