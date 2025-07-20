"""
Tests for messaging system models.
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

User = get_user_model()


class ConversationModelTestCase(TestCase):
    """Test the Conversation model functionality."""
    
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
    
    def test_conversation_creation_with_participants(self):
        """Test creating a Conversation with participants."""
        from accounts.models import Conversation
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        self.assertEqual(conversation.participants.count(), 2)
        self.assertIn(self.user1, conversation.participants.all())
        self.assertIn(self.user2, conversation.participants.all())
        self.assertIsNotNone(conversation.created_at)
        self.assertIsNone(conversation.last_message_at)
    
    def test_conversation_string_representation(self):
        """Test the string representation of a Conversation."""
        from accounts.models import Conversation
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        expected_str = f"Conversation between {self.user1.display_name}, {self.user2.display_name}"
        self.assertEqual(str(conversation), expected_str)
    
    def test_conversation_ordering(self):
        """Test that conversations are ordered by last_message_at (newest first)."""
        from accounts.models import Conversation
        
        # Create first conversation
        conversation1 = Conversation.objects.create()
        conversation1.participants.add(self.user1, self.user2)
        
        # Create second conversation later
        conversation2 = Conversation.objects.create()
        conversation2.participants.add(self.user1, self.user3)
        
        conversations = Conversation.objects.all()
        self.assertEqual(conversations[0], conversation2)  # Newest first by created_at
        self.assertEqual(conversations[1], conversation1)
    
    def test_conversation_with_last_message_at(self):
        """Test conversation with last_message_at set."""
        from accounts.models import Conversation
        
        now = timezone.now()
        conversation = Conversation.objects.create(last_message_at=now)
        conversation.participants.add(self.user1, self.user2)
        
        self.assertEqual(conversation.last_message_at, now)
    
    def test_conversation_cascade_deletion_with_users(self):
        """Test that conversations are handled when users are deleted."""
        from accounts.models import Conversation
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        self.assertEqual(Conversation.objects.count(), 1)
        
        # Delete a participant - conversation should remain but participant is removed
        user1_id = self.user1.id
        self.user1.delete()
        
        conversation.refresh_from_db()
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(conversation.participants.count(), 1)
        self.assertNotIn(user1_id, conversation.participants.values_list('id', flat=True))
    
    def test_conversation_get_other_participant(self):
        """Test helper method to get the other participant in a 2-person conversation."""
        from accounts.models import Conversation
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        # Should have a method to get the other participant
        other_for_user1 = conversation.get_other_participant(self.user1)
        other_for_user2 = conversation.get_other_participant(self.user2)
        
        self.assertEqual(other_for_user1, self.user2)
        self.assertEqual(other_for_user2, self.user1)
    
    def test_conversation_get_other_participant_group_conversation(self):
        """Test get_other_participant with more than 2 participants."""
        from accounts.models import Conversation
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2, self.user3)
        
        # Should return None for group conversations
        other = conversation.get_other_participant(self.user1)
        self.assertIsNone(other)
    
    def test_conversation_has_unread_messages(self):
        """Test method to check if conversation has unread messages for a user."""
        from accounts.models import Conversation
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        # Initially no unread messages
        self.assertFalse(conversation.has_unread_messages(self.user1))


class MessageModelTestCase(TestCase):
    """Test the Message model functionality."""
    
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
    
    def test_message_creation_with_required_fields(self):
        """Test creating a Message with all required fields."""
        from accounts.models import Conversation, Message
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user1,
            content="Hello, this is a test message!"
        )
        
        self.assertEqual(message.conversation, conversation)
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.content, "Hello, this is a test message!")
        self.assertIsNotNone(message.sent_at)
        self.assertFalse(message.is_read)
    
    def test_message_string_representation(self):
        """Test the string representation of a Message."""
        from accounts.models import Conversation, Message
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user1,
            content="Hello, this is a test message!"
        )
        
        expected_str = f"Message from {self.user1.display_name} in conversation {conversation.id}"
        self.assertEqual(str(message), expected_str)
    
    def test_message_ordering(self):
        """Test that messages are ordered by sent_at (newest first)."""
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
        
        messages = Message.objects.all()
        self.assertEqual(messages[0], message2)  # Newest first
        self.assertEqual(messages[1], message1)
    
    def test_message_content_validation(self):
        """Test that message content cannot be empty."""
        from accounts.models import Conversation, Message
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        message = Message(
            conversation=conversation,
            sender=self.user1,
            content=""
        )
        
        # This should raise a validation error
        with self.assertRaises(ValidationError):
            message.full_clean()
    
    def test_message_sender_must_be_participant(self):
        """Test that message sender must be a participant in the conversation."""
        from accounts.models import Conversation, Message
        
        # Create conversation with user1 and user2
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        # Create a third user not in the conversation
        user3 = User.objects.create_user(
            email='user3@example.com',
            password='testpass123',
            display_name='User Three',
            is_active=True,
            is_email_verified=True
        )
        
        message = Message(
            conversation=conversation,
            sender=user3,
            content="This should not be allowed"
        )
        
        # This should raise a validation error
        with self.assertRaises(ValidationError):
            message.full_clean()
    
    def test_message_cascade_deletion_with_conversation(self):
        """Test that messages are deleted when conversation is deleted."""
        from accounts.models import Conversation, Message
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        Message.objects.create(
            conversation=conversation,
            sender=self.user1,
            content="Test message"
        )
        
        self.assertEqual(Message.objects.count(), 1)
        
        conversation.delete()
        self.assertEqual(Message.objects.count(), 0)
    
    def test_message_cascade_deletion_with_sender(self):
        """Test that messages are handled when sender is deleted."""
        from accounts.models import Conversation, Message
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user1,
            content="Test message"
        )
        
        self.assertEqual(Message.objects.count(), 1)
        
        # Delete sender - message should be preserved but sender should be set to None
        self.user1.delete()
        
        message.refresh_from_db()
        self.assertIsNone(message.sender)
        self.assertEqual(Message.objects.count(), 1)
    
    def test_message_updates_conversation_last_message_at(self):
        """Test that creating a message updates the conversation's last_message_at."""
        from accounts.models import Conversation, Message
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        # Initially no last_message_at
        self.assertIsNone(conversation.last_message_at)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user1,
            content="Test message"
        )
        
        conversation.refresh_from_db()
        self.assertIsNotNone(conversation.last_message_at)
        self.assertEqual(conversation.last_message_at, message.sent_at)
    
    def test_message_read_status_default(self):
        """Test that messages default to unread status."""
        from accounts.models import Conversation, Message
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user1,
            content="Test message"
        )
        
        self.assertFalse(message.is_read)
    
    def test_message_mark_as_read(self):
        """Test marking a message as read."""
        from accounts.models import Conversation, Message
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user1,
            content="Test message"
        )
        
        # Mark as read
        message.is_read = True
        message.save()
        
        message.refresh_from_db()
        self.assertTrue(message.is_read)


class ConversationParticipantModelTestCase(TestCase):
    """Test the ConversationParticipant through model functionality."""
    
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
    
    def test_conversation_participant_creation(self):
        """Test creating ConversationParticipant through model."""
        from accounts.models import Conversation, ConversationParticipant
        
        conversation = Conversation.objects.create()
        
        participant = ConversationParticipant.objects.create(
            conversation=conversation,
            user=self.user1
        )
        
        self.assertEqual(participant.conversation, conversation)
        self.assertEqual(participant.user, self.user1)
        self.assertIsNone(participant.last_read_at)
        self.assertIsNotNone(participant.joined_at)
    
    def test_conversation_participant_string_representation(self):
        """Test the string representation of ConversationParticipant."""
        from accounts.models import Conversation, ConversationParticipant
        
        conversation = Conversation.objects.create()
        
        participant = ConversationParticipant.objects.create(
            conversation=conversation,
            user=self.user1
        )
        
        expected_str = f"{self.user1.display_name} in conversation {conversation.id}"
        self.assertEqual(str(participant), expected_str)
    
    def test_conversation_participant_unique_constraint(self):
        """Test that user can only be added once per conversation."""
        from accounts.models import Conversation, ConversationParticipant
        
        conversation = Conversation.objects.create()
        
        # Create first participant
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=self.user1
        )
        
        # Try to create duplicate - should fail
        with self.assertRaises(IntegrityError):
            ConversationParticipant.objects.create(
                conversation=conversation,
                user=self.user1
            )
    
    def test_conversation_participant_last_read_tracking(self):
        """Test tracking when user last read the conversation."""
        from accounts.models import Conversation, ConversationParticipant
        
        conversation = Conversation.objects.create()
        
        participant = ConversationParticipant.objects.create(
            conversation=conversation,
            user=self.user1
        )
        
        # Initially no last read time
        self.assertIsNone(participant.last_read_at)
        
        # Update last read time
        now = timezone.now()
        participant.last_read_at = now
        participant.save()
        
        participant.refresh_from_db()
        self.assertEqual(participant.last_read_at, now)
    
    def test_conversation_participant_cascade_deletion(self):
        """Test cascade deletion behavior."""
        from accounts.models import Conversation, ConversationParticipant
        
        conversation = Conversation.objects.create()
        
        participant = ConversationParticipant.objects.create(
            conversation=conversation,
            user=self.user1
        )
        
        self.assertEqual(ConversationParticipant.objects.count(), 1)
        
        # Delete conversation - participant should be deleted
        conversation.delete()
        self.assertEqual(ConversationParticipant.objects.count(), 0)
    
    def test_conversation_participant_user_deletion(self):
        """Test participant deletion when user is deleted."""
        from accounts.models import Conversation, ConversationParticipant
        
        conversation = Conversation.objects.create()
        
        participant = ConversationParticipant.objects.create(
            conversation=conversation,
            user=self.user1
        )
        
        self.assertEqual(ConversationParticipant.objects.count(), 1)
        
        # Delete user - participant should be deleted
        self.user1.delete()
        self.assertEqual(ConversationParticipant.objects.count(), 0)


class MessagingModelAdminTestCase(TestCase):
    """Test messaging models in Django admin."""
    
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
    
    def test_messaging_models_admin_registration(self):
        """Test that messaging models are registered with admin."""
        from django.contrib.admin.sites import site
        from accounts.models import Conversation, Message, ConversationParticipant
        
        # Check that models are registered with admin
        self.assertIn(Conversation, site._registry)
        self.assertIn(Message, site._registry)
        self.assertIn(ConversationParticipant, site._registry)
    
    def test_conversation_admin_display(self):
        """Test that Conversation admin has appropriate display."""
        from accounts.models import Conversation
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        # Test that we can create and display conversations
        expected_str = f"Conversation between {self.user1.display_name}, {self.user2.display_name}"
        self.assertEqual(str(conversation), expected_str)
    
    def test_message_admin_display(self):
        """Test that Message admin has appropriate display."""
        from accounts.models import Conversation, Message
        
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user1,
            content="Test message"
        )
        
        expected_str = f"Message from {self.user1.display_name} in conversation {conversation.id}"
        self.assertEqual(str(message), expected_str)