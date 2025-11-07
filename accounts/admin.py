from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import UserHobby, Photo, Friendship, Conversation, Message, ConversationParticipant


User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for CustomUser model."""
    
    # Fields to display in the user list
    list_display = ('email', 'display_name', 'get_role_display', 'is_email_verified', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'is_forum_admin', 'is_forum_moderator', 'is_email_verified', 'date_joined')
    search_fields = ('email', 'display_name', 'location')
    ordering = ('-date_joined',)
    
    # Fields for user detail/edit page
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('display_name', 'location', 'bio', 'profile_picture')}),
        (_('Forum Roles'), {
            'fields': ('is_forum_admin', 'is_forum_moderator'),
            'description': 'Forum-specific roles for content management and administration.',
        }),
        (_('System Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
            'description': 'Django system-level permissions. Use Forum Roles above for forum-specific access.',
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Email verification'), {'fields': ('is_email_verified',)}),
    )
    
    # Fields for user creation page
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'display_name', 'password1', 'password2'),
        }),
    )
    
    # Read-only fields
    readonly_fields = ('date_joined', 'last_login')
    
    # Custom actions
    actions = ['verify_email', 'unverify_email', 'make_forum_admin', 'make_forum_moderator', 'remove_forum_roles']
    
    def verify_email(self, request, queryset):
        """Action to verify user emails."""
        updated = queryset.update(is_email_verified=True)
        self.message_user(request, f'{updated} users had their email verified.')
    verify_email.short_description = "Verify email for selected users"
    
    def unverify_email(self, request, queryset):
        """Action to unverify user emails."""
        updated = queryset.update(is_email_verified=False)
        self.message_user(request, f'{updated} users had their email unverified.')
    unverify_email.short_description = "Unverify email for selected users"

    def make_forum_admin(self, request, queryset):
        """Action to make selected users forum admins."""
        updated = queryset.update(is_forum_admin=True, is_forum_moderator=True, is_staff=True)
        self.message_user(request, f'{updated} users were promoted to Forum Admin.')
    make_forum_admin.short_description = "Promote to Forum Admin (includes moderator privileges)"

    def make_forum_moderator(self, request, queryset):
        """Action to make selected users forum moderators."""
        updated = queryset.update(is_forum_moderator=True)
        # Also give them basic staff access for analytics
        queryset.update(is_staff=True)
        self.message_user(request, f'{updated} users were promoted to Forum Moderator.')
    make_forum_moderator.short_description = "Promote to Forum Moderator"

    def remove_forum_roles(self, request, queryset):
        """Action to remove forum roles from selected users."""
        # Keep is_staff if they're superuser, otherwise remove it
        for user in queryset:
            user.is_forum_admin = False
            user.is_forum_moderator = False
            if not user.is_superuser:
                user.is_staff = False
            user.save()
        count = queryset.count()
        self.message_user(request, f'{count} users had their forum roles removed.')
    remove_forum_roles.short_description = "Remove all forum roles from selected users"


@admin.register(UserHobby)
class UserHobbyAdmin(admin.ModelAdmin):
    """Admin interface for UserHobby model."""
    
    list_display = ('user', 'get_subcategory_name', 'get_category_name', 'joined_at')
    list_filter = ('subcategory__category', 'subcategory', 'joined_at')
    search_fields = ('user__display_name', 'user__email', 'subcategory__name', 'subcategory__category__name')
    ordering = ('-joined_at',)
    date_hierarchy = 'joined_at'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'subcategory')
        }),
        ('Timestamps', {
            'fields': ('joined_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('joined_at', 'created_at', 'updated_at')
    
    def get_subcategory_name(self, obj):
        """Display the subcategory name."""
        return obj.subcategory.name
    get_subcategory_name.short_description = 'Subcategory'
    
    def get_category_name(self, obj):
        """Display the category name."""
        return obj.subcategory.category.name
    get_category_name.short_description = 'Category'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'subcategory__category')


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    """Admin interface for Photo model."""
    
    list_display = ('user', 'get_caption_preview', 'get_image_thumbnail', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('user__display_name', 'user__email', 'caption')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'image', 'caption')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def get_caption_preview(self, obj):
        """Display a preview of the caption."""
        if obj.caption:
            return obj.caption[:50] + ('...' if len(obj.caption) > 50 else '')
        return '(No caption)'
    get_caption_preview.short_description = 'Caption'
    
    def get_image_thumbnail(self, obj):
        """Display a thumbnail of the image."""
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-width: 100px; max-height: 100px;" />'
        return '(No image)'
    get_image_thumbnail.short_description = 'Thumbnail'
    get_image_thumbnail.allow_tags = True
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    """Admin interface for Friendship model."""
    
    list_display = ('get_from_user', 'get_to_user', 'status', 'created_at', 'responded_at')
    list_filter = ('status', 'created_at', 'responded_at')
    search_fields = ('from_user__display_name', 'from_user__email', 'to_user__display_name', 'to_user__email')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('from_user', 'to_user', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'responded_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def get_from_user(self, obj):
        """Display the from_user display name."""
        return obj.from_user.display_name
    get_from_user.short_description = 'From'
    get_from_user.admin_order_field = 'from_user__display_name'
    
    def get_to_user(self, obj):
        """Display the to_user display name."""
        return obj.to_user.display_name
    get_to_user.short_description = 'To'
    get_to_user.admin_order_field = 'to_user__display_name'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('from_user', 'to_user')


class ConversationParticipantInline(admin.TabularInline):
    """Inline admin for ConversationParticipant."""
    model = ConversationParticipant
    extra = 0
    readonly_fields = ('joined_at', 'created_at', 'updated_at')
    fields = ('user', 'joined_at', 'last_read_at')


class MessageInline(admin.TabularInline):
    """Inline admin for Messages in Conversations."""
    model = Message
    extra = 0
    readonly_fields = ('sent_at', 'created_at', 'updated_at')
    fields = ('sender', 'content', 'sent_at', 'is_read')
    ordering = ('-sent_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('sender')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin interface for Conversation model."""
    
    list_display = ('id', 'get_participants_display', 'get_message_count', 'last_message_at', 'created_at')
    list_filter = ('created_at', 'last_message_at')
    search_fields = ('participants__display_name', 'participants__email')
    ordering = ('-last_message_at', '-created_at')
    date_hierarchy = 'created_at'
    
    inlines = [ConversationParticipantInline, MessageInline]
    
    fieldsets = (
        (None, {
            'fields': ('last_message_at',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'last_message_at')
    
    def get_participants_display(self, obj):
        """Display the participants in the conversation."""
        participant_names = [p.display_name for p in obj.participants.all()]
        return ', '.join(participant_names) if participant_names else '(No participants)'
    get_participants_display.short_description = 'Participants'
    
    def get_message_count(self, obj):
        """Display the number of messages in the conversation."""
        return obj.message_set.count()
    get_message_count.short_description = 'Messages'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('participants')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface for Message model."""
    
    list_display = ('id', 'get_sender_display', 'get_conversation_participants', 'get_content_preview', 'sent_at', 'is_read')
    list_filter = ('sent_at', 'is_read', 'sender')
    search_fields = ('sender__display_name', 'sender__email', 'content', 'conversation__participants__display_name')
    ordering = ('-sent_at',)
    date_hierarchy = 'sent_at'
    
    fieldsets = (
        (None, {
            'fields': ('conversation', 'sender', 'content', 'is_read')
        }),
        ('Timestamps', {
            'fields': ('sent_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('sent_at', 'created_at', 'updated_at')
    
    def get_sender_display(self, obj):
        """Display the sender's display name."""
        return obj.sender.display_name if obj.sender else '(Deleted user)'
    get_sender_display.short_description = 'Sender'
    get_sender_display.admin_order_field = 'sender__display_name'
    
    def get_conversation_participants(self, obj):
        """Display the conversation participants."""
        participant_names = [p.display_name for p in obj.conversation.participants.all()]
        return ', '.join(participant_names) if participant_names else '(No participants)'
    get_conversation_participants.short_description = 'Conversation'
    
    def get_content_preview(self, obj):
        """Display a preview of the message content."""
        return obj.content[:100] + ('...' if len(obj.content) > 100 else '')
    get_content_preview.short_description = 'Content'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('sender', 'conversation').prefetch_related('conversation__participants')


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    """Admin interface for ConversationParticipant model."""
    
    list_display = ('id', 'get_user_display', 'get_conversation_display', 'joined_at', 'last_read_at')
    list_filter = ('joined_at', 'last_read_at')
    search_fields = ('user__display_name', 'user__email', 'conversation__participants__display_name')
    ordering = ('-joined_at',)
    date_hierarchy = 'joined_at'
    
    fieldsets = (
        (None, {
            'fields': ('conversation', 'user', 'last_read_at')
        }),
        ('Timestamps', {
            'fields': ('joined_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('joined_at', 'created_at', 'updated_at')
    
    def get_user_display(self, obj):
        """Display the user's display name."""
        return obj.user.display_name
    get_user_display.short_description = 'User'
    get_user_display.admin_order_field = 'user__display_name'
    
    def get_conversation_display(self, obj):
        """Display the conversation participants."""
        participant_names = [p.display_name for p in obj.conversation.participants.all()]
        return f"Conversation: {', '.join(participant_names)}" if participant_names else '(No participants)'
    get_conversation_display.short_description = 'Conversation'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'conversation').prefetch_related('conversation__participants')
