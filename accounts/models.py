from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from core.models import TimestampedModel


class CustomUserManager(BaseUserManager):
    """Custom manager for CustomUser model."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser, TimestampedModel):
    """
    Custom user model that extends AbstractUser with additional fields.
    
    This model provides user authentication with email as the username field
    and additional profile information for the forum.
    """
    
    # Override username field to use email
    username = None
    email = models.EmailField(
        unique=True,
        help_text="User's email address - used for login and notifications"
    )
    
    # Additional fields
    display_name = models.CharField(
        max_length=50,
        help_text="Display name shown in forum posts and profiles"
    )
    
    location = models.CharField(
        max_length=100,
        blank=True,
        help_text="User's location (city, country, etc.)"
    )
    
    bio = models.TextField(
        blank=True,
        help_text="User's biography or personal description"
    )
    
    is_email_verified = models.BooleanField(
        default=False,
        help_text="Whether the user has verified their email address"
    )

    # Role-based permissions
    is_forum_admin = models.BooleanField(
        default=False,
        help_text="Forum administrator with full administrative privileges"
    )

    is_forum_moderator = models.BooleanField(
        default=False,
        help_text="Forum moderator with content moderation privileges"
    )

    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        help_text="User's profile picture"
    )
    
    # Set email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['display_name']
    
    # Use custom manager
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        """Return string representation of user."""
        return self.display_name
    
    def get_full_name(self):
        """Return the display name for the user."""
        return self.display_name
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.display_name

    def get_role_display(self):
        """Return a human-readable role for the user."""
        if self.is_superuser:
            return "Super Admin"
        elif self.is_forum_admin:
            return "Forum Admin"
        elif self.is_forum_moderator:
            return "Forum Moderator"
        elif self.is_staff:
            return "Staff"
        else:
            return "Member"

    def has_admin_access(self):
        """Check if user has admin-level access."""
        return self.is_superuser or self.is_forum_admin

    def has_moderator_access(self):
        """Check if user has moderator-level access."""
        return self.is_superuser or self.is_forum_admin or self.is_forum_moderator


class UserHobby(TimestampedModel):
    """Model for tracking user hobbies and interests."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='hobbies')
    subcategory = models.ForeignKey('forums.Subcategory', on_delete=models.CASCADE, related_name='interested_users')
    joined_at = models.DateTimeField(auto_now_add=True, help_text="When the user became interested in this hobby")
    
    class Meta:
        ordering = ['-joined_at']
        unique_together = [('user', 'subcategory')]
        verbose_name = 'User Hobby'
        verbose_name_plural = 'User Hobbies'
        indexes = [
            models.Index(fields=['-joined_at']),
            models.Index(fields=['user', '-joined_at']),
        ]
    
    def __str__(self):
        return f"{self.user.display_name} interested in {self.subcategory.name}"


class Photo(TimestampedModel):
    """Model for user photos in their galleries."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(
        upload_to='photos/%Y/%m/',
        help_text="Upload a photo (max 10MB). Supported formats: JPG, JPEG, PNG, GIF, WebP."
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional caption for your photo."
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        if self.caption:
            return f"Photo by {self.user.display_name}: {self.caption}"
        return f"Photo by {self.user.display_name}"


class Friendship(TimestampedModel):
    """Model for hubby relationships between users."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    from_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_hubby_requests',
        help_text="User who sent the hubby request"
    )
    to_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='received_hubby_requests',
        help_text="User who received the hubby request"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Status of the hubby request"
    )
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the hubby request was accepted or rejected"
    )
    
    class Meta:
        ordering = ['-created_at']
        unique_together = [('from_user', 'to_user')]
        indexes = [
            models.Index(fields=['from_user', 'status']),
            models.Index(fields=['to_user', 'status']),
            models.Index(fields=['-created_at']),
        ]
    
    def clean(self):
        """Validate that users cannot send hubby requests to themselves."""
        from django.core.exceptions import ValidationError
        if self.from_user == self.to_user:
            raise ValidationError("Users cannot send hubby requests to themselves.")
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Friendship: {self.from_user.display_name} -> {self.to_user.display_name} ({self.status})"


class Conversation(TimestampedModel):
    """Model for private conversations between users."""
    participants = models.ManyToManyField(
        CustomUser,
        through='ConversationParticipant',
        related_name='conversations',
        help_text="Users participating in this conversation"
    )
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the last message was sent in this conversation"
    )
    
    class Meta:
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['-last_message_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        """Return string representation of conversation."""
        participant_names = [p.display_name for p in self.participants.all().order_by('display_name')]
        return f"Conversation between {', '.join(participant_names)}"
    
    def get_other_participant(self, user):
        """Get the other participant in a 2-person conversation."""
        if self.participants.count() != 2:
            return None
        
        other_participants = self.participants.exclude(id=user.id)
        return other_participants.first() if other_participants.exists() else None
    
    def has_unread_messages(self, user):
        """Check if conversation has unread messages for the given user."""
        try:
            participant = self.conversationparticipant_set.get(user=user)
            if not participant.last_read_at:
                return self.message_set.exists()
            
            return self.message_set.filter(
                sent_at__gt=participant.last_read_at
            ).exists()
        except ConversationParticipant.DoesNotExist:
            return False


class ConversationParticipant(TimestampedModel):
    """Through model for conversation participants with read tracking."""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        help_text="The conversation this participant is part of"
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        help_text="The user participating in the conversation"
    )
    joined_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the user joined this conversation"
    )
    last_read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the user last read messages in this conversation"
    )
    
    class Meta:
        unique_together = [('conversation', 'user')]
        indexes = [
            models.Index(fields=['user', '-joined_at']),
            models.Index(fields=['conversation', 'user']),
        ]
    
    def __str__(self):
        """Return string representation of participant."""
        return f"{self.user.display_name} in conversation {self.conversation.id}"


class Message(TimestampedModel):
    """Model for messages within conversations."""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='message_set',
        help_text="The conversation this message belongs to"
    )
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_messages',
        help_text="User who sent this message"
    )
    content = models.TextField(
        help_text="The message content"
    )
    sent_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the message was sent"
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the message has been read"
    )
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['conversation', '-sent_at']),
            models.Index(fields=['sender', '-sent_at']),
            models.Index(fields=['-sent_at']),
        ]
    
    def clean(self):
        """Validate that message content is not empty and sender is a participant."""
        from django.core.exceptions import ValidationError
        
        # Check content is not empty
        if not self.content or not self.content.strip():
            raise ValidationError("Message content cannot be empty.")
        
        # Check sender is a participant (if sender exists)
        if self.sender and self.conversation_id:
            if not self.conversation.participants.filter(id=self.sender.id).exists():
                raise ValidationError("Sender must be a participant in the conversation.")
    
    def save(self, *args, **kwargs):
        """Override save to run validation and update conversation last_message_at."""
        self.full_clean()
        
        # Save the message first
        super().save(*args, **kwargs)
        
        # Update conversation's last_message_at after saving
        if self.conversation:
            self.conversation.last_message_at = self.sent_at
            self.conversation.save(update_fields=['last_message_at'])
    
    def __str__(self):
        """Return string representation of message."""
        sender_name = self.sender.display_name if self.sender else "Unknown"
        return f"Message from {sender_name} in conversation {self.conversation.id}"
