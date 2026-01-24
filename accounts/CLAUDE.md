# Accounts App

User management, authentication, profiles, and social features.

## Models

### CustomUser
Email-based auth (no username). Extends AbstractUser.
- **Fields**: email (unique), display_name, location, bio, profile_picture, is_email_verified, is_forum_admin, is_forum_moderator
- **Methods**: `get_role_display()`, `has_admin_access()`, `has_moderator_access()`

### Friendship
Friend/hubby relationships with request flow.
- **Fields**: from_user, to_user, status (pending|accepted|rejected), responded_at
- **Constraints**: Unique (from_user, to_user), prevents self-friending

### Conversation & Message
Private messaging system.
- **Conversation**: M2M participants via ConversationParticipant, last_message_at
- **Message**: content, sender (SET_NULL), sent_at, is_read
- **ConversationParticipant**: Tracks joined_at, last_read_at

### Photo
User gallery with file validation.
- **Fields**: user, image, caption
- **Storage**: `photos/%Y/%m/`

### UserHobby
Links users to forum subcategories.
- **Constraints**: Unique (user, subcategory)

## Views

### Authentication
| View | URL | Purpose |
|------|-----|---------|
| RegisterView | `/accounts/register/` | Email registration |
| VerifyEmailView | `/accounts/verify/<uidb64>/<token>/` | Email verification |
| LoginView | `/accounts/login/` | Login with remember me |
| LogoutView | `/accounts/logout/` | Session cleanup |

### Profiles
| View | URL | Purpose |
|------|-----|---------|
| user_profile_view | `/accounts/user/<id>/` | View profile |
| profile_edit_view | `/accounts/profile/edit/` | Edit own profile |
| manage_hobbies_view | `/accounts/hobbies/` | Hobby selection |

### Friends (Hubbies)
| View | URL | Purpose |
|------|-----|---------|
| send_friend_request_view | `/accounts/hubbies/send/<id>/` | Send request |
| respond_friend_request_view | `/accounts/hubbies/respond/<id>/<action>/` | Accept/reject |
| friend_requests_view | `/accounts/hubbies/requests/` | Incoming requests |
| friends_list_view | `/accounts/hubbies/<id>/` | Friend list |

### Messaging
| View | URL | Purpose |
|------|-----|---------|
| inbox_view | `/accounts/inbox/` | Conversation list |
| conversation_detail_view | `/accounts/conversation/<id>/` | View conversation |
| send_message_view | `/accounts/conversation/<id>/send/` | Send message |
| start_conversation_view | `/accounts/message/<id>/` | New conversation |

### Photos
| View | URL | Purpose |
|------|-----|---------|
| upload_photo_view | `/accounts/photos/upload/` | Upload photo |
| photo_gallery_view | `/accounts/photos/<id>/` | User gallery |
| all_photos_gallery_view | `/accounts/photos/` | Community gallery |
| delete_photo_view | `/accounts/photos/delete/<id>/` | Delete own photo |

## Forms

| Form | Validation |
|------|------------|
| UserRegistrationForm | Email uniqueness, password strength |
| EmailLoginForm | Email auth, inactive user handling |
| ProfileEditForm | 5MB file limit, image type check |
| PhotoUploadForm | 10MB limit, jpg/png/gif/webp only |
| MessageForm | Non-empty, max 5000 chars |
| HobbyManagementForm | Dynamic subcategory choices |

## Security

- `@login_required` on all protected views
- File validation: size + content-type whitelist
- Unique constraints prevent duplicate friendships/bookmarks
- Conversation access requires participant verification
- SET_NULL on message sender preserves history on user deletion
- Secure tokens for email verification (Django default_token_generator)

## Key Patterns

- **Bidirectional queries**: Friendship uses Q objects for symmetric relationships
- **Through models**: UserHobby, ConversationParticipant for M2M with extra data
- **Permission hierarchy**: is_superuser > is_forum_admin > is_forum_moderator > member
