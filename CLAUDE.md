Style guides and principles for initial development of Hobby Hubby the social media app.

1. Be sure to thoroughly document your code including all functions, template files. Keep the project-level CLAUDE.md file up to date with notes about the structure of the app and its implementation.
2. Follow best design principles but keep additions and changes to a minimum.
3. Code for security! Security is a huge priority. All features should be implemented with security in mind.
4. Follow Test-Driven Development principles. Red-Green-Refactor principles. This way you know what you're building is working. Make sure the tests fail first before implementing code for the reason you expect them to fail.

## Project Structure

The Hobby Hubby forum is built with Django 4.2 LTS and follows Django best practices:

```
hobby_hubby/
├── hobby_hubby/
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py          # Base settings for all environments
│   │   ├── development.py   # Development-specific settings
│   │   └── production.py    # Production-specific settings
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/                    # Core utilities and base models
│   ├── models.py           # TimestampedModel mixin
│   ├── admin.py            # Admin site configuration
│   └── apps.py             # App configuration
├── accounts/                # User management
│   ├── models.py           # User models (future)
│   ├── admin.py            # User admin
│   └── apps.py             # App configuration
├── forums/                  # Forum functionality
│   ├── models.py           # Forum models (future)
│   ├── admin.py            # Forum admin
│   └── apps.py             # App configuration
├── tests/                   # Project-wide tests
├── requirements/            # Environment-specific requirements
├── static/                  # Static files
│   └── css/
│       ├── hh-colors.css    # Hobby Hubby color system and category styling
│       └── hh-colors.scss   # SCSS source for color system
├── templates/               # Templates
├── media/                   # User uploads
└── manage.py
```

## Django Apps

### Core App
- **Purpose**: Shared utilities and base models
- **Key Components**:
  - `TimestampedModel`: Abstract base model with created_at/updated_at fields
  - Custom admin site configuration
  - Shared utilities for other apps

### Accounts App
- **Purpose**: User management, authentication, and social features
- **Key Components**:
  - `CustomUser`: Extended user model with email authentication
  - `CustomUserManager`: Custom manager for email-based user creation
  - `UserAdmin`: Enhanced admin interface for user management
  - `EmailBackend`: Custom authentication backend for email-based login
  - `EmailLoginForm`: Custom login form with remember me functionality
  - `UserRegistrationForm`: Registration form with email verification
  - `UserHobby`: Model linking users to subcategories for hobby tracking
  - `Photo`: Model for user photo galleries with upload and management
  - `Friendship`: Model for friend relationships with status tracking
  - `Conversation`: Model for private conversations between users
  - `Message`: Model for individual messages within conversations
  - `ConversationParticipant`: Through model for conversation participation and read tracking
- **Features**:
  - Email-based authentication (no username required)
  - Additional profile fields (display_name, location, bio, profile_picture)
  - Email verification system with secure token generation
  - User registration with form validation
  - Inactive user creation until email verification
  - Complete authentication flow (login, logout, password reset)
  - Session management with remember me functionality
  - Enhanced user profiles with hobby management and statistics
  - Photo gallery system with upload, viewing, and deletion
  - Complete friend system with requests, responses, and management
  - Private messaging system with conversations and message tracking
  - Profile editing with file upload validation
  - Bookmark management for forum threads
  - Inherits from TimestampedModel for automatic timestamps

### Forums App
- **Purpose**: Forum functionality and community discussions
- **Key Components**:
  - `Category`: Top-level forum categories with theming and ordering
  - `Subcategory`: Specific discussion areas within categories
  - `Thread`: Discussion topics within subcategories
  - `Post`: Individual messages within threads
- **Features**:
  - Complete hierarchical forum structure (Category > Subcategory > Thread > Post)
  - Color theming for visual organization (8 predefined themes)
  - Automatic slug generation with conflict resolution for all models
  - Thread management with pinning and locking capabilities
  - View count tracking for threads with automatic increment
  - Denormalized post count and last post tracking for performance
  - Django signals for automatic count updates
  - Post editing tracking with timestamps
  - Member count tracking per subcategory
  - Font Awesome icon support for categories
  - Comprehensive admin interface with inline editing
  - Database indexing for optimal query performance
  - Proper ordering and filtering throughout
  - Cascade deletion protection with referential integrity
  - Full forum browsing interface with responsive Bootstrap 5 templates
  - Pagination for threads (20 per page) and posts (10 per page)
  - Breadcrumb navigation throughout forum hierarchy
  - Thread status indicators (pinned, locked)
  - View and post count displays
  - SEO-friendly URL structure with slugs
  - Inherits from TimestampedModel for automatic timestamps
- **Security Features**:
  - Unique constraints prevent duplicate names/slugs within scope
  - Automatic slug sanitization using Django's slugify
  - Admin interface with proper permission controls
  - Foreign key constraints ensure data integrity
  - Query optimization with select_related to prevent N+1 queries

## Security Implementation

The following security measures have been implemented based on the Risk Register:

### 1. SQL Injection Prevention (Risk #2)
- Uses Django ORM with parameterized queries
- Database settings use environment variables
- No raw SQL queries without proper escaping

### 2. XSS Protection (Risk #6)
- `SECURE_BROWSER_XSS_FILTER = True`
- `SECURE_CONTENT_TYPE_NOSNIFF = True`
- `X_FRAME_OPTIONS = 'DENY'`
- Django template auto-escaping enabled

### 3. CSRF Protection (Risk #7.2)
- Django CSRF middleware enabled
- `CSRF_COOKIE_SECURE = True` (production)
- `CSRF_COOKIE_HTTPONLY = True`
- `CSRF_COOKIE_SAMESITE = 'Lax'`

### 4. File Upload Security (Risk #5)
- File size limits: `FILE_UPLOAD_MAX_MEMORY_SIZE = 10MB`
- Allowed file types whitelist: `ALLOWED_UPLOAD_FILE_TYPES = ['.jpg', '.jpeg', '.png', '.gif', '.webp']`
- Secure file handling planned with server-side validation

### 5. Session Security (Risk #4)
- `SESSION_COOKIE_SECURE = True` (production)
- `SESSION_COOKIE_HTTPONLY = True`
- `SESSION_COOKIE_SAMESITE = 'Lax'`

### 6. Password Security (Risk #6)
- Minimum length: 8 characters
- Django built-in password validators
- User attribute similarity validation
- Common password validation
- Numeric password validation

### 7. HTTPS Enforcement (Risk #3, #4)
- `SECURE_SSL_REDIRECT = True` (production)
- `SECURE_HSTS_SECONDS = 31536000` (1 year)
- `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- `SECURE_HSTS_PRELOAD = True`

### 8. OAuth Security (Risk #7)
- Prepared for secure OAuth implementation
- PKCE mechanism planned
- Proper redirect URI validation planned

### 9. User Model Security
- Custom user model with email authentication reduces username enumeration risks
- Profile picture uploads restricted to safe image formats
- Field validation with appropriate help text
- Email verification system to prevent fake accounts
- Secure password handling via Django's built-in authentication

### 10. Registration System Security
- Email verification prevents account activation without valid email
- Django's built-in token generation for secure verification links
- Users created as inactive until email verification
- Password validation using Django's password validators
- CSRF protection on registration forms
- Form validation prevents duplicate email registration
- Secure token expiration for verification links

### 11. Authentication System Security
- Custom EmailBackend allows email-based authentication
- Email verification checks prevent unverified users from logging in
- Session management with configurable expiration
- Remember me functionality with extended session lifetime
- Password reset flow using Django's built-in secure token system
- Proper logout handling with session cleanup
- Login protection against brute force attacks (rate limiting ready)
- Secure authentication redirects prevent open redirects

## Testing Strategy

- pytest with pytest-django for testing framework
- Test-Driven Development (TDD) approach - write tests first, then implement
- Settings-specific tests verify configuration
- Security settings tests ensure risk mitigations are active
- Database connection tests verify proper setup
- Password validation tests ensure security requirements
- Authentication system tests (80 tests total):
  - User registration with email verification (19 tests)
  - Custom user model functionality (15 tests)
  - Login/logout/password reset flow (26 tests)
  - Form validation and security (20 tests)
- All tests passing ensures system integrity and security compliance

## Design System & Visual Identity

### Hobby Hubby Jewel Tones Color Palette

The forum design uses a sophisticated jewel tones color palette that maps to the six main hobby categories:

#### Category Color Mapping
- **Creative & Arts**: Deep Emerald (#2F7D5C) - Rich forest green representing creativity and growth
- **Sports & Fitness**: Sapphire Blue (#1E3A8A) - Deep royal blue representing strength and determination
- **Games & Entertainment**: Amethyst (#7C3AED) - Rich purple representing imagination and fun
- **Technology & Science**: Ruby Red (#B91C1C) - Deep crimson representing innovation and precision
- **Food & Culinary**: Topaz Gold (#D97706) - Warm amber representing warmth and nourishment
- **Lifestyle & Social**: Onyx (#374151) - Sophisticated dark gray representing community and balance

#### Color System Implementation
- **CSS Variables**: All colors defined as CSS custom properties in `static/css/hh-colors.css`
- **Color Variants**: Each category color includes light, dark, and ultra-light variants for different use cases
- **Category Classes**: Dynamic CSS classes (e.g., `category-creative-arts`) apply contextual styling
- **Responsive Design**: Colors adapt appropriately across different screen sizes

### Fixed Category Structure

The forum now uses a fixed set of six hobby categories, each with thematic subcategories:

#### 1. Creative & Arts
- Digital Art & Design, Traditional Art, Photography, Crafting & DIY, Music & Audio
- **Icon**: `fas fa-palette`

#### 2. Sports & Fitness  
- Running & Cardio, Weight Training, Yoga & Mindfulness, Outdoor Activities, Team Sports
- **Icon**: `fas fa-running`

#### 3. Games & Entertainment
- Video Games, Board Games, Movies & TV, Books & Reading, Streaming & Content
- **Icon**: `fas fa-gamepad`

#### 4. Technology & Science
- Programming, Electronics & Gadgets, Science & Research, AI & Machine Learning, Cybersecurity
- **Icon**: `fas fa-microchip`

#### 5. Food & Culinary
- Cooking & Recipes, Baking & Desserts, International Cuisine, Healthy Eating, Food Photography
- **Icon**: `fas fa-utensils`

#### 6. Lifestyle & Social
- Travel & Adventure, Personal Development, Community Events, Fashion & Style, Home & Garden
- **Icon**: `fas fa-users`

### Banner Styling & Visual Design

#### Category Banner Features
- **Gradient Backgrounds**: Each category uses a custom gradient from the primary color to its lighter variant
- **Overlay Effects**: Subtle white overlay gradients on the right side for visual depth
- **Typography**: Large, bold category titles with descriptive text
- **Icons**: Font Awesome 6 icons that reflect each category's theme
- **Shadow Effects**: Text shadows for better readability over gradient backgrounds

#### Subcategory Design
- **Hover Effects**: Transform animations with color transitions
- **Border Accents**: Left border styling that changes color on hover
- **Badge Styling**: Member and thread count badges using category colors
- **Ultra-light Backgrounds**: Subtle background color changes on hover using ultra-light color variants

#### Responsive Considerations
- **Mobile Optimization**: Banner heights and typography scale appropriately
- **Touch Targets**: Adequate spacing for mobile interaction
- **Icon Sizing**: Icons scale down on smaller screens
- **Text Hierarchy**: Clear information hierarchy maintained across devices

### Management Commands

#### Category Setup
- **`setup_hobby_categories`**: Creates the fixed six hobby categories with proper styling
- **`create_sample_subcategories`**: Populates categories with realistic subcategory examples
- **Reset Options**: Both commands support `--reset` flag for development/testing

### Template Integration

#### Updated Templates
- **`category_list.html`**: Completely redesigned with banner styling and improved visual hierarchy
- **`base.html`**: Includes the new color system CSS file
- **Category Classes**: Dynamic CSS class application based on category color theme

#### Design Principles Applied
- **Visual Consistency**: All category banners follow the same design pattern with unique colors
- **Information Architecture**: Clear hierarchy from categories to subcategories
- **User Experience**: Hover states and transitions provide responsive feedback
- **Accessibility**: High contrast text shadows and appropriate color combinations

## Implementation Progress

### Completed Features (Phase 1-6.2)
1. **Django Project Foundation** - Settings split, PostgreSQL config, security settings
2. **Core App Structure** - TimestampedModel, admin customization, shared utilities
3. **Custom User System** - Email authentication, profile fields, user management
4. **Registration System** - Email verification, secure token generation, form validation
5. **Authentication System** - Login/logout, password reset, session management
6. **Complete Forum System** - Full hierarchical forum structure with browsing interface
7. **Thread and Post Creation** - Complete content creation system with security and validation
8. **Upvoting System** - AJAX-powered post voting with real-time updates
9. **Bookmarking System** - Thread bookmarking with user management and real-time interactions
10. **Enhanced User Profiles** - Complete profile system with hobbies, statistics, and management
11. **Photo Gallery System** - Complete photo management with upload, viewing, and deletion
12. **Friend System** - Complete friendship functionality with requests, responses, and management
13. **Private Messaging Models** - Complete messaging system foundation with conversations and messages
14. **Private Messaging Interface** - Complete messaging UI with inbox, conversations, and message composition
15. **Search System** - Complete search functionality with PostgreSQL full-text search and SQLite fallback
16. **Forum Redesign & Category System** - Fixed hobby categories with jewel-tone color palette and banner styling

### Latest Implementation (Phase 7.1 - Basic Search Implementation)
- **Search Architecture**: Dual implementation supporting both PostgreSQL full-text search and SQLite fallback for testing
- **Search Forms**: SearchForm with query validation, content type filtering, and sort options
- **Search Views**: Unified search_view with comprehensive result processing and pagination
- **Search Functionality**:
  - **Unified Search**: perform_unified_search searches across all content types with ranking
  - **Content-Specific Search**: Dedicated functions for posts, threads, users, and categories
  - **PostgreSQL Features**: SearchVector, SearchQuery, and SearchRank for advanced full-text search
  - **SQLite Compatibility**: icontains-based search for development and testing environments
- **Search Results**: Comprehensive result formatting with URLs, content snippets, and metadata
- **Templates**: Complete search interface with responsive design and filtering options
- **Security Features**:
  - Form validation prevents XSS and injection attacks
  - Query length limits and sanitization with strip_tags
  - Proper escaping of search terms in results display
  - Input validation for all search parameters
- **User Experience Features**:
  - Advanced search form with content type and sort filtering
  - Paginated results (20 per page) with navigation
  - Visual content type indicators with icons and badges
  - Result snippets with truncated content and highlighting
  - No results handling with search tips and alternative actions
  - Search form persistence across result pages
- **Content Coverage**:
  - **Posts**: Full-text search of post content with thread context
  - **Threads**: Search thread titles with post count information
  - **Users**: Search display names, bios, and locations of active users
  - **Categories/Subcategories**: Search names and descriptions with proper categorization
- **Performance Optimizations**:
  - select_related and prefetch_related for efficient database queries
  - Database indexes leveraged for search performance
  - Query optimization to prevent N+1 problems
  - Result caching through proper ORM usage
- **Testing**: Comprehensive test suite (21 tests) covering:
  - Form validation and security
  - Search functionality across all content types
  - View rendering and template contexts
  - Database query efficiency
  - Security measures against common attacks
- **URL Structure**: /forums/search/ with GET parameter support for bookmarkable searches
- **Integration**: Search integrated into forum navigation with proper URL patterns

### Phase 8.5 - Search API Endpoints (Mobile Integration)
- **REST API Implementation**: Complete RESTful API for mobile apps and third-party integrations
- **API Endpoints**:
  - `/forums/api/search/` - Main search endpoint supporting GET and POST requests
  - `/forums/api/search/suggestions/` - Autocomplete suggestions for mobile typing
  - `/forums/api/search/analytics/` - Analytics data access for staff users
- **API Features**:
  - JSON responses optimized for mobile consumption
  - Full parameter support (query, content_type, sort_by, limit, offset, filters)
  - Date range filtering with ISO format support
  - Advanced search filters (author, category, date ranges)
  - Comprehensive pagination metadata
  - Search analytics tracking for API usage
  - Error handling with proper HTTP status codes
- **Security Implementation**:
  - CSRF exemption for API endpoints while maintaining other security measures
  - Staff-only access for analytics endpoints
  - Input validation and sanitization
  - Rate limiting ready (can be added via middleware)
  - Proper error responses without exposing sensitive information
- **Response Format**: Structured JSON with success indicators, pagination, metadata, and detailed result objects
- **Mobile Optimization**:
  - Compact but complete result objects
  - Type-specific metadata (post counts, view counts, user info)
  - Efficient suggestion algorithm for autocomplete
  - Configurable result limits with reasonable defaults
- **Analytics Integration**: All API searches tracked in SearchAnalytics model for performance monitoring
- **Testing**: Comprehensive API test suite (27 tests) covering all endpoints, error conditions, and edge cases

### Previous Implementation (Phase 6.2 - Private Messaging Interface)
- **Views**: Complete messaging interface with inbox, conversation detail, message sending, and conversation starting
- **Inbox View**: Conversation list with unread counts, participant display, and last message previews
- **Conversation Detail View**: Message display with pagination, automatic read marking, and compose form
- **Message Composition**: MessageForm with content validation and character limits
- **Start Conversation View**: New conversation creation with existing conversation detection
- **Security Features**:
  - Login required for all messaging operations
  - Participant verification prevents unauthorized access to conversations
  - Message content validation with 5000 character limit
  - Self-messaging prevention in conversation creation
  - Proper CSRF protection on all forms
- **User Experience Features**:
  - Responsive inbox with conversation cards and hover effects
  - Real-time conversation display with message bubbles and sender identification
  - Automatic scroll to bottom of conversations for latest messages
  - Pagination for both conversations (20 per page) and messages (20 per page)
  - Visual distinction between own messages and other participant messages
  - Unread message counter integration in inbox view
  - Profile integration with message buttons and user information
- **Templates**:
  - inbox.html: Complete conversation list with participant profiles and message previews
  - conversation_detail.html: Chat-style interface with message bubbles and composition form
  - start_conversation.html: User-friendly conversation initiation with target user profile
  - Responsive Bootstrap 5 design with custom CSS for message styling
- **URL Patterns**:
  - /inbox/ for conversation list
  - /conversation/<id>/ for conversation detail view
  - /conversation/<id>/send/ for message sending
  - /message/<user_id>/ for starting new conversations
- **Business Logic**:
  - Existing conversation detection prevents duplicate conversations between users
  - Automatic participant read timestamp updates when viewing conversations
  - Smart participant display showing "other" user in 2-person conversations
  - Message validation and error handling with user feedback
- **Database Optimization**:
  - Efficient queries with select_related and prefetch_related
  - Conversation ordering by last_message_at for recency
  - Message ordering by sent_at for chronological display
  - Annotated queries for participant counting and unread message detection
- **Integration**: Complete messaging system integrated with user profiles, friend system, and navigation
- **Testing**: Comprehensive test suite (30 tests) covering all views, forms, templates, and user interactions

### Phase 4.2 - Upvoting System (Completed)
- **Models**: Vote model with unique constraint on (user, post) and denormalized vote_count on Post
- **Views**: AJAX vote_post view with authentication, self-vote prevention, and JSON responses
- **Templates**: Vote buttons with authenticated/unauthenticated states and real-time count updates
- **JavaScript**: Async voting with CSRF protection, button state updates, and error handling
- **Security Features**: Login required, self-vote prevention, AJAX validation, CSRF protection
- **Database Features**: Django signals, unique constraints, cascading deletion, indexing
- **User Experience**: Real-time updates, visual state changes, responsive design
- **Testing**: 29 comprehensive tests covering models, views, signals, and display

### Phase 4.1 - Thread and Post Creation (Completed)
- **Forms**: ThreadCreateForm and PostCreateForm with validation and security
- **Views**: Function-based views with @login_required decorators
- **Templates**: Responsive Bootstrap 5 forms with AJAX preview functionality
- **Security Features**: CSRF protection, HTML sanitization, authentication requirements
- **User Experience**: Success messages, AJAX preview, responsive design, status indicators
- **Testing**: 24 comprehensive tests covering all functionality

### Phase 5.1 - Enhanced User Profiles (Completed)
- **Models**: UserHobby model linking users to subcategories with join dates and unique constraints
- **Profile Views**: Enhanced user_profile_view with post counts, hobby tracking, and tabbed interface
- **Profile Management**: profile_edit_view with file upload validation and hobby selection
- **Forms**: ProfileEditForm with image validation and HobbyManagementForm with dynamic choices
- **Templates**: Enhanced user_profile.html with tabs, user_profile_edit.html, and manage_hobbies.html
- **Features**: Profile picture uploads, hobby management, post statistics, join date display
- **User Experience**: Responsive tabbed interface, hobby category links, edit buttons for own profile
- **Security Features**: Login required for editing, file validation, proper form validation
- **Testing**: 31 comprehensive tests covering all models, views, forms, and admin functionality
- **Database Features**: Many-to-many through model, unique constraints, cascading deletion, proper indexing

### Phase 5.2 - Photo Gallery (Completed)
- **Models**: Photo model with image uploads, captions, and timestamp tracking
- **Views**: upload_photo_view, photo_gallery_view, and delete_photo_view with proper authentication
- **Templates**: Complete gallery system with grid layout, lightbox modal, and pagination
- **Forms**: PhotoUploadForm with file validation (10MB limit, format restrictions)
- **Features**: Photo upload with preview, gallery browsing, lightbox viewing, photo deletion
- **User Experience**: Responsive grid layout, Bootstrap 5 modal lightbox, pagination (20 photos per page)
- **Security Features**: Login required for uploads/deletion, file size and format validation, user isolation
- **Integration**: Photos tab in user profiles, gallery links, upload buttons for own gallery
- **Admin Interface**: Photo admin with thumbnail previews and caption management
- **Testing**: Comprehensive test suite covering models, views, forms, and functionality

### Phase 7.1 - Basic Search Implementation (Completed)
- **Dual Search Architecture**: PostgreSQL full-text search with SQLite fallback for testing compatibility
- **Search Models**: Unified search across posts, threads, users, categories, and subcategories
- **Views**: search_view with comprehensive filtering, sorting, and pagination
- **Templates**: Complete search_results.html with responsive design and result type indicators
- **Forms**: SearchForm with query validation, content type filtering, and sort options
- **Database Integration**: SearchVector, SearchQuery, and SearchRank for PostgreSQL optimization
- **SQLite Compatibility**: icontains-based fallback search for development and testing
- **User Experience**: Full search interface with pagination (20 results per page), sorting options
- **Security Features**: Query validation, HTML escaping, proper error handling
- **Testing**: 21 comprehensive tests covering dual search architecture and all functionality

### Phase 8.2 - Search History and Saved Searches (Completed)

#### Search History Model Implementation
- **Model Location**: `forums/models.py:224-336`
- **Core Fields**:
  ```python
  user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
  query = models.CharField(max_length=200, help_text="The search query text")
  content_type = models.CharField(max_length=20, choices=[...], default='all')
  results_count = models.PositiveIntegerField(default=0)
  ```
- **Smart Recording Method**: `record_search(cls, user, query, content_type='all', results_count=0)`
  - Validates authenticated user: `if not user.is_authenticated or not query.strip(): return None`
  - Query cleaning: `query = query.strip()[:200]`
  - Duplicate prevention window: `recent_cutoff = timezone.now() - timedelta(hours=1)`
  - Updates existing search if within window, creates new otherwise
- **Query Methods**:
  - `get_user_recent_searches(cls, user, limit=10)`: Returns user's recent searches ordered by created_at DESC
  - `get_popular_searches(cls, limit=10)`: Aggregates with `Count('id')` ordered by frequency
- **Database Optimization**:
  ```python
  indexes = [
      models.Index(fields=['user', '-created_at']),
      models.Index(fields=['query', '-created_at']),
      models.Index(fields=['-created_at']),
  ]
  ```

#### Saved Searches Model Implementation  
- **Model Location**: `forums/models.py:339-428`
- **Core Fields**:
  ```python
  user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
  name = models.CharField(max_length=100, help_text="User-defined name for this saved search")
  query = models.CharField(max_length=200, help_text="The search query text")
  content_type = models.CharField(max_length=20, choices=[...], default='all')
  sort_by = models.CharField(max_length=20, choices=[...], default='relevance')
  is_active = models.BooleanField(default=True)
  last_used_at = models.DateTimeField(null=True, blank=True)
  ```
- **URL Generation**: `get_search_url()` uses `reverse('forums:search')` with `urlencode(params)`
- **Usage Tracking**: `mark_as_used()` updates `last_used_at = timezone.now()`
- **User Queries**: `get_user_saved_searches(cls, user)` filters by `user=user, is_active=True`
- **Constraints**: `unique_together = [('user', 'name')]` prevents duplicate names per user

#### Search History Integration
- **View Integration**: `forums/views.py:366-373`
  ```python
  if query.strip():  # Only record non-empty queries
      SearchHistory.record_search(
          user=request.user,
          query=query,
          content_type=content_type,
          results_count=total_results
      )
  ```
- **Context Enhancement**: `forums/views.py:380-398`
  ```python
  if request.user.is_authenticated:
      recent_searches = SearchHistory.get_user_recent_searches(request.user, limit=5)
      saved_searches = SavedSearch.get_user_saved_searches(request.user)
  ```

#### Saved Searches Management Views
- **Save Search View**: `forums/views.py:1244-1300`
  - HTTP Method validation: `if request.method != "POST": return JsonResponse({"error": "POST method required"}, status=405)`
  - AJAX header check: `if not request.headers.get("X-Requested-With") == "XMLHttpRequest"`
  - Duplicate name prevention: `SavedSearch.objects.filter(user=request.user, name=name).first()`
  - Success response includes saved search details and generated URL
- **Delete Search View**: `forums/views.py:1303-1329`
  - Authorization: `get_object_or_404(SavedSearch, id=search_id, user=request.user)`
  - Soft reference to name before deletion for response message
- **Management Views**:
  - `saved_searches_view`: Renders `forums/saved_searches.html` with user's active searches
  - `search_history_view`: Groups history by date using `defaultdict(list)`
  - `clear_search_history_view`: Uses `.delete()[0]` to get count of deleted entries

#### Enhanced Search Templates
- **Search Results Enhancement**: `templates/forums/search_results.html:240-364`
  - Sidebar implementation with conditional user authentication check
  - Recent searches display: `{% for search in recent_searches %}`
  - Saved searches with slice filter: `{% for search in saved_searches|slice:":5" %}`
  - Save Search button: `<button type="button" class="btn btn-outline-warning ms-2" id="saveSearchBtn">`
- **Save Search Modal**: `templates/forums/search_results.html:440-555`
  ```javascript
  const saveSearchModal = new bootstrap.Modal(document.getElementById('saveSearchModal'));
  fetch('{% url "forums:save_search" %}', {
      method: 'POST',
      body: formData,
      headers: {
          'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
          'X-Requested-With': 'XMLHttpRequest'
      }
  })
  ```
- **Management Templates**:
  - `saved_searches.html`: Card-based layout with delete confirmations via Bootstrap modal
  - `search_history.html`: Date-grouped display with `{% for date, searches in grouped_history.items %}`
  - Both templates include CSRF token: `{% csrf_token %}` for AJAX operations

#### AJAX Implementation Details
- **JavaScript Patterns**:
  ```javascript
  // Disable button during request
  confirmSaveBtn.disabled = true;
  confirmSaveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Saving...';
  
  // Promise chain with error handling
  .then(response => response.json())
  .then(data => { /* success handling */ })
  .catch(error => { /* error handling */ })
  .finally(() => { /* cleanup */ });
  ```
- **CSRF Token Extraction**: `document.querySelector('[name=csrfmiddlewaretoken]').value`
- **Modal Management**: Bootstrap 5 modal API with `show()`, `hide()` methods
- **Dynamic DOM Updates**: Success alerts inserted with `insertBefore()`

#### Database Schema Updates
- **Migration File**: `forums/migrations/0005_add_search_history_and_saved_searches.py`
  ```python
  # Creates SearchHistory and SavedSearch models with proper field definitions
  # Includes foreign key constraints and database indexes
  ```
- **Admin Integration**: `forums/admin.py:218-276`
  ```python
  @admin.register(SearchHistory)
  class SearchHistoryAdmin(admin.ModelAdmin):
      list_display = ('user', 'query', 'content_type', 'results_count', 'created_at')
      readonly_fields = ('created_at', 'updated_at')
      def has_add_permission(self, request): return False  # Auto-generated only
  ```
- **Foreign Key Relations**:
  - `SearchHistory.user`: CASCADE deletion with `related_name='search_history'`
  - `SavedSearch.user`: CASCADE deletion with `related_name='saved_searches'`

#### URL Pattern Integration
- **URL Structure**: `forums/urls.py:21-26`
  ```python
  path('search/save/', views.save_search_view, name='save_search'),
  path('search/saved/', views.saved_searches_view, name='saved_searches'),
  path('search/saved/<int:search_id>/delete/', views.delete_saved_search_view, name='delete_saved_search'),
  path('search/history/', views.search_history_view, name='search_history'),
  path('search/history/clear/', views.clear_search_history_view, name='clear_search_history'),
  ```
- **Authentication Requirements**: All views decorated with `@login_required`
- **RESTful Design**: POST for mutations, GET for queries, proper HTTP status codes

#### Testing Architecture Details
- **Test File**: `tests/test_search_history.py` with 31 comprehensive tests
- **Model Tests**: 19 tests covering SearchHistory and SavedSearch model methods
  ```python
  def test_record_search_duplicate_recent(self):
      # Tests 1-hour duplicate prevention window
      recent_cutoff = timezone.now() - timedelta(hours=1)
  ```
- **View Tests**: 9 tests for AJAX endpoints with authentication and validation
  ```python
  response = self.client.post(reverse('forums:save_search'), {
      'name': 'My Test Search', 'query': 'Django models'
  }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
  ```
- **Integration Tests**: 3 tests for search workflow with history recording
- **Edge Cases**: Empty queries, HTML injection, unauthorized access, duplicate names

### Phase 8.1 - Advanced Search Features (Completed)

#### Search Autocomplete Implementation
- **Backend Endpoint**: `search_suggestions_view` in `forums/views.py:1011` with AJAX validation
- **URL Pattern**: `path('search/suggestions/', views.search_suggestions_view, name='search_suggestions')`
- **Request Handling**: Validates X-Requested-With header, requires 2+ character queries, returns JSON
- **Dual Search Functions**: 
  - `get_postgres_suggestions()` using SearchVector/SearchQuery for PostgreSQL
  - `get_sqlite_suggestions()` using icontains filters for SQLite compatibility
- **Suggestion Limits**: Max 8 total suggestions, 2 per content type (threads, posts, users, categories, subcategories)
- **Response Format**: JSON with suggestion objects containing type, title, description, url fields

#### JavaScript Autocomplete Implementation
- **Location**: Enhanced `templates/base.html:117-302` with comprehensive autocomplete logic
- **Debouncing**: 300ms timeout using `setTimeout` and `clearTimeout` for performance
- **Event Handling**: Input, keydown, focus, blur, and click event listeners
- **Keyboard Navigation**: Arrow up/down for suggestion selection, Enter to navigate, Escape to close
- **AJAX Requests**: Fetch API with XMLHttpRequest headers and error handling
- **DOM Manipulation**: Dynamic suggestion container with Bootstrap 5 styling
- **Security**: HTML escaping via `escapeHtml()` function to prevent XSS
- **Accessibility**: ARIA labels, role attributes, and screen reader compatibility

#### Search Result Highlighting System
- **Template Tags Module**: `forums/templatetags/search_tags.py` with 4 custom filters/tags
- **Core Functions**:
  - `highlight_search_terms(text, query)`: Main highlighting with `<mark>` tags
  - `search_result_snippet(content, query, max_length)`: Smart content excerpts
  - `highlight_in_suggestions(text, query)`: Suggestion-specific highlighting
  - `truncate_and_highlight(text, args)`: Combined truncation and highlighting
- **Regex Implementation**: Case-insensitive search with escaped special characters
- **XSS Protection**: Django's `escape()` function before highlighting, `mark_safe()` for output
- **Smart Snippets**: Centers content around first found search term for relevance

#### Enhanced Navigation Integration
- **Search Bar Location**: `templates/base.html:22-41` within navbar-collapse
- **Form Integration**: GET form targeting `forums:search` with autocomplete="off"
- **Suggestion Container**: Absolute positioned dropdown with z-index 1050
- **Icon Integration**: Font Awesome 6 icons for content type differentiation
- **Responsive Design**: Hidden on mobile (d-none d-lg-flex), collapses into mobile menu
- **Bootstrap Integration**: Uses Bootstrap 5 form classes and responsive utilities

#### Database Architecture Updates
- **PostgreSQL Search**: Leverages django.contrib.postgres.search for full-text capabilities
- **Search Vectors**: Optimized SearchVector configurations per content type
- **Query Optimization**: select_related() and prefetch_related() for efficient joins
- **Index Strategy**: Database indexes on searchable fields for performance
- **Fallback System**: Automatic detection via settings.DATABASES['default']['ENGINE']

#### Template Integration
- **Search Results Template**: `templates/forums/search_results.html:1-321` enhanced with highlighting
- **Template Tag Loading**: `{% load search_tags %}` for highlighting functionality
- **Result Title Highlighting**: `{{ result.title|highlight_search_terms:query }}`
- **Content Snippets**: `{% search_result_snippet result.content query 200 %}`
- **CSS Styling**: Custom `.search-highlight` classes with yellow background and borders
- **Visual Hierarchy**: Different highlight colors for titles vs content

#### Security Implementation Details
- **CSRF Protection**: All AJAX requests include CSRF tokens via Django middleware
- **Input Validation**: Server-side query length validation (minimum 2 characters)
- **HTML Escaping**: All user input escaped before highlighting to prevent XSS
- **Regex Safety**: Search terms escaped with `re.escape()` before regex compilation
- **Request Validation**: AJAX endpoint validates X-Requested-With header
- **Error Handling**: Try-catch blocks with graceful degradation on failures

#### Testing Architecture
- **Test Coverage**: 34 comprehensive tests across 2 test files
- **Autocomplete Tests**: `tests/test_search_suggestions.py` with 14 tests covering AJAX endpoint
- **Highlighting Tests**: `tests/test_search_highlighting.py` with 20 tests covering template tags
- **Template Testing**: Django Template engine testing for filter functionality
- **Edge Case Coverage**: Empty queries, HTML injection, special characters, regex edge cases
- **Mock Data**: Realistic test data with categories, subcategories, threads, posts, users

#### Performance Optimizations
- **Query Limits**: Search suggestions limited to prevent overwhelming responses
- **Database Indexing**: Optimized indexes on searchable fields
- **Caching Strategy**: Template fragment caching for search results (ready for implementation)
- **JavaScript Efficiency**: Debounced requests to prevent excessive API calls
- **Memory Management**: Proper cleanup of event listeners and DOM references

### Latest Implementation (Phase 8.3 - Advanced Search Analytics & Filters)
- **Search Analytics System**: Comprehensive analytics tracking with SearchAnalytics model
  - **Performance Metrics**: Search time tracking (milliseconds), database hit counting, and query optimization analysis
  - **User Behavior Analysis**: Click-through tracking, result position analysis, and time-to-click measurements
  - **Search Context Data**: User agent detection, anonymized IP tracking, and referrer URL analysis
  - **Query Normalization**: Basic stemming implementation for analytics clustering and trend identification
  - **Privacy-Conscious Design**: IP anonymization (last octet removal) and optional anonymous session tracking
- **Advanced Search Filters**: Date ranges, author filtering, and category-based search
  - **Date Range Filtering**: From/to date inputs with validation and proper timezone handling
  - **Author Filtering**: Search by author display name or email with case-insensitive matching
  - **Category Filtering**: Dropdown selection of forum categories with proper relationship filtering
  - **Form Validation**: Cross-field validation preventing invalid date ranges and future dates
  - **Filter Persistence**: URL parameter preservation and form state maintenance across searches
- **Enhanced Search Templates**: Collapsible advanced filters with intelligent UI behavior
  - **Smart Expansion**: Automatic expansion of advanced filters when active filters are present
  - **Visual Indicators**: Filter button state changes and active filter highlighting
  - **Responsive Design**: Mobile-friendly filter layout with proper Bootstrap 5 responsive classes
  - **JavaScript Enhancement**: Real-time filter state management and user experience improvements
- **Search History & Saved Searches**: Comprehensive search management system
  - **Search History Tracking**: Automatic recording of user searches with duplicate prevention logic
  - **Saved Search Management**: User-defined search bookmarks with custom names and parameters
  - **Search Analytics Integration**: Each search recorded for analytics with full context tracking
  - **History UI**: Dedicated search history page with date grouping and search repetition features
- **Security Enhancements**: Advanced input validation and query sanitization
  - **Filter Injection Prevention**: Proper parameterization of all date, author, and category filters
  - **Analytics Privacy**: Session-based tracking with user consent consideration and data anonymization
  - **Form Security**: Enhanced CSRF protection and input sanitization for all new filter fields
  - **Query Safety**: Comprehensive validation preventing SQL injection through filter parameters
- **Performance Optimizations**: Smart filtering and query optimization
  - **Efficient Filtering**: apply_search_filters helper function with optimized query patterns
  - **Index Utilization**: Proper database indexing for date, author, and category filtering
  - **Query Counting**: Accurate database hit tracking for performance monitoring and optimization
  - **Caching Ready**: Analytics system designed for future caching implementation
- **Database Migrations**: SearchAnalytics model with comprehensive field coverage
  - **Analytics Schema**: 20+ fields tracking search context, performance, and user behavior
  - **Index Strategy**: Multi-field indexes for efficient analytics querying and trend analysis
  - **Foreign Key Design**: Proper relationships with SET_NULL for user deletion handling
  - **Scalability Design**: Field sizes and types optimized for high-volume search analytics

### Completed Implementation (Phase 8.2 - Search History & Management)
- **Search History Models**: SearchHistory and SavedSearch with intelligent duplicate prevention
- **History Tracking**: Automatic search recording with one-hour duplicate merge window
- **Saved Search System**: User-defined search bookmarks with parameters and URL generation
- **Management Interface**: History viewing, saved search management, and bulk operations
- **AJAX Integration**: Real-time search saving and deletion without page refreshes

### Next Steps (Phase 8.4+)
- Search analytics dashboard with visualization and insights
- Search result ranking improvements with machine learning
- Real-time search suggestions with autocomplete and typo correction
- Advanced moderation tools and content filtering
- Real-time notifications system with WebSocket integration
- Activity feeds and timeline features
- Image handling and rich media in posts
- Mobile app API endpoints and authentication

### Key Technical Decisions
- Email-based authentication (no username field)
- Split settings for environment-specific configuration
- Custom authentication backend for email login
- Email verification requirement before account activation
- Session management with remember me functionality
- Bootstrap 5 for responsive UI framework
