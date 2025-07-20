# Hobby Hubby 🎯

A comprehensive Django-based social forum platform for hobby enthusiasts to connect, share, and discuss their passions with advanced search, analytics, and social features.

## 🌟 Features

- **Complete Forum System**: Hierarchical categories, subcategories, threads, and posts
- **Advanced Search**: Full-text search with PostgreSQL, autocomplete, filters, and analytics
- **User Management**: Email-based authentication with profile customization and hobby tracking
- **Private Messaging**: Real-time conversations between users with unread tracking
- **Social Features**: User profiles, friend system, photo galleries, and content bookmarking
- **Voting System**: Upvote posts with real-time AJAX updates and vote tracking
- **Analytics Dashboard**: Comprehensive search analytics with Chart.js visualizations
- **Mobile-Ready**: Responsive Bootstrap 5 design and REST API for mobile apps
- **Security-First**: CSRF protection, input validation, and comprehensive security measures

## 🛠️ Technology Stack

- **Backend**: Django 4.2 LTS with Python 3.10+
- **Database**: PostgreSQL 12+ (SQLite fallback for development/testing)
- **Frontend**: Django templates with Bootstrap 5 and Font Awesome 6
- **Search**: PostgreSQL full-text search with SQLite fallback
- **Authentication**: Custom email-based auth with session management
- **File Storage**: Local storage with image optimization (S3-ready)
- **Testing**: pytest with pytest-django (80+ comprehensive tests)
- **API**: RESTful API endpoints for mobile integration

## 🚀 Quick Start (WSL/Linux)

### Prerequisites

- Python 3.10+
- PostgreSQL 12+ (recommended) or SQLite (for development)
- Git

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd hobby-hubby
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements/development.txt
```

### 3. Database Setup

#### Option A: PostgreSQL (Recommended)
```bash
# Install PostgreSQL (Ubuntu/Debian on WSL)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo service postgresql start

# Create database and user
sudo -u postgres psql
```

In PostgreSQL shell:
```sql
CREATE DATABASE hobby_hubby;
CREATE USER hobby_hubby_user WITH PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE hobby_hubby TO hobby_hubby_user;
ALTER USER hobby_hubby_user CREATEDB;
\q
```

#### Option B: SQLite (Development Only)
SQLite will be used automatically if PostgreSQL is not configured.

### 4. Environment Configuration

Create environment variables:

```bash
# For development with PostgreSQL
export DB_NAME=hobby_hubby
export DB_USER=hobby_hubby_user
export DB_PASSWORD=your_password_here
export DB_HOST=localhost
export DB_PORT=5432
export SECRET_KEY=your-secret-key-here
export DEBUG=True
export DJANGO_SETTINGS_MODULE=hobby_hubby.settings.development

# Add to ~/.bashrc for persistence
echo "export DJANGO_SETTINGS_MODULE=hobby_hubby.settings.development" >> ~/.bashrc
```

### 5. Database Migration

```bash
# Run migrations
python manage.py migrate

# Create superuser account
python manage.py createsuperuser
```

### 6. Load Sample Data (Optional)

```bash
# Create sample forum structure
python manage.py shell -c "
from forums.models import Category, Subcategory
from django.contrib.auth import get_user_model

User = get_user_model()

# Create sample categories
tech = Category.objects.create(
    name='Technology',
    description='All things tech and programming',
    slug='technology',
    color_theme='blue',
    icon='fas fa-laptop-code'
)

hobbies = Category.objects.create(
    name='Hobbies & Crafts',
    description='Creative pursuits and hands-on activities',
    slug='hobbies-crafts',
    color_theme='green',
    icon='fas fa-palette'
)

# Create subcategories
Subcategory.objects.create(
    name='Web Development',
    description='HTML, CSS, JavaScript, and web frameworks',
    slug='web-development',
    category=tech
)

Subcategory.objects.create(
    name='Photography',
    description='Digital photography and editing techniques',
    slug='photography',
    category=hobbies
)

print('Sample data created successfully!')
"
```

### 7. Start the Development Server

```bash
# Run the development server
python manage.py runserver

# Or specify port and host
python manage.py runserver 0.0.0.0:8000
```

Visit `http://localhost:8000` in your browser! 🎉

## 📁 Project Structure

```
hobby_hubby/
├── accounts/              # User management and authentication
│   ├── models.py         # CustomUser, UserHobby, Photo, Friendship, Conversation
│   ├── views.py          # Auth views, profiles, messaging, photo gallery
│   ├── forms.py          # Registration, login, profile forms
│   └── backends.py       # Email authentication backend
├── core/                 # Shared utilities and base models
│   └── models.py         # TimestampedModel mixin
├── forums/               # Forum functionality and search
│   ├── models.py         # Category, Thread, Post, Vote, Search models
│   ├── views.py          # Forum views, search, analytics
│   ├── api_views.py      # REST API endpoints
│   ├── forms.py          # Thread, post, search forms
│   └── templatetags/     # Custom template tags for search highlighting
├── hobby_hubby/          # Project settings and configuration
│   └── settings/         # Environment-specific settings
│       ├── base.py       # Base settings
│       ├── development.py # Development settings
│       └── production.py # Production settings
├── templates/            # Django templates
│   ├── base.html         # Base template with navbar and search
│   ├── accounts/         # User-related templates
│   └── forums/           # Forum and search templates
├── tests/                # Comprehensive test suites (80+ tests)
├── media/                # User uploads (profile pics, photos)
├── static/               # Static files (CSS, JS, images)
└── requirements/         # Environment-specific dependencies
```

## 🛠️ Development Commands

### Database Management
```bash
# Create new migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (development only!)
python manage.py flush
```

### Testing
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test forums

# Run with verbose output
python manage.py test -v 2

# Run specific test file
python manage.py test tests.test_search_functionality

# Run API tests
python manage.py test tests.test_search_api
```

### Static Files & Media
```bash
# Collect static files for production
python manage.py collectstatic

# Create media directories
mkdir -p media/profile_pictures media/photos
chmod 755 media media/profile_pictures media/photos
```

### Administrative Tasks
```bash
# Create superuser
python manage.py createsuperuser

# Access Django shell
python manage.py shell

# Check for potential problems
python manage.py check

# Show current settings
python manage.py diffsettings
```

## 🔧 WSL-Specific Setup

### PostgreSQL Auto-Start
```bash
# Start PostgreSQL automatically on WSL startup
echo "sudo service postgresql start" >> ~/.bashrc

# Or create an alias for manual start
echo "alias startdb='sudo service postgresql start'" >> ~/.bashrc
```

### File Permissions
```bash
# Ensure proper permissions for media uploads
sudo chown -R $USER:$USER media/
chmod -R 755 media/

# Fix any permission issues
sudo chmod 755 . media templates static
```

### Environment Variables
```bash
# Add persistent environment variables
cat >> ~/.bashrc << 'EOF'
export DJANGO_SETTINGS_MODULE=hobby_hubby.settings.development
export DEBUG=True
EOF

source ~/.bashrc
```

### WSL Network Access
```bash
# Allow external connections (optional)
python manage.py runserver 0.0.0.0:8000

# Access from Windows: http://localhost:8000
# Access from network: http://[WSL-IP]:8000
```

## 📊 Admin Interface

Access the comprehensive Django admin at `http://localhost:8000/admin/` with your superuser credentials.

### Available Admin Sections:
- **Users**: User accounts, profiles, hobbies, friendships
- **Forums**: Categories, subcategories, threads, posts, votes
- **Search Analytics**: Search metrics, performance data, query analysis
- **Messages**: Private conversations and participant management
- **Photos**: User photo gallery management with metadata

## 🔍 Search System

The application includes a comprehensive search system with multiple interfaces:

### Web Interface
- **Main Search**: `/forums/search/` - Full search with advanced filters
- **Search History**: `/forums/search/history/` - User search history
- **Saved Searches**: `/forums/search/saved/` - Bookmarked searches
- **Analytics Dashboard**: `/forums/admin/analytics/` - Search metrics (staff only)

### API Endpoints
- **Main Search API**: `GET/POST /forums/api/search/`
  - Parameters: query, content_type, sort_by, limit, offset, filters
  - Returns: JSON with results, pagination, metadata
- **Autocomplete API**: `GET /forums/api/search/suggestions/`
  - Parameters: q (query), limit
  - Returns: JSON with search suggestions
- **Analytics API**: `GET /forums/api/search/analytics/` (staff only)
  - Parameters: days (time period)
  - Returns: JSON with search metrics and trends

### Search Features
- **Full-text Search**: PostgreSQL search vectors with ranking
- **Content Types**: Posts, threads, users, categories, subcategories
- **Advanced Filters**: Date ranges, author filtering, category filtering
- **Real-time Suggestions**: AJAX autocomplete with debouncing
- **Search Analytics**: Performance tracking, user behavior analysis
- **Search History**: Automatic saving with duplicate prevention
- **Saved Searches**: User-defined search bookmarks

## 🧪 Testing

The project includes comprehensive test coverage with 80+ tests:

```bash
# Run all tests
python manage.py test

# Test specific components
python manage.py test forums.tests.test_forum_models
python manage.py test accounts.tests.test_authentication
python manage.py test tests.test_search_functionality
python manage.py test tests.test_search_api

# Run tests with coverage (requires coverage package)
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML coverage report
```

### Test Categories
- **Authentication Tests**: User registration, login, email verification
- **Forum Tests**: Category, thread, post creation and management
- **Search Tests**: Full-text search, filters, analytics, API endpoints
- **Social Tests**: Messaging, friendships, photo gallery, voting
- **API Tests**: REST endpoints, JSON responses, error handling
- **Security Tests**: CSRF protection, input validation, access controls

## 🚀 Production Deployment

### Environment Setup
1. Set `DEBUG=False` in production settings
2. Configure proper `ALLOWED_HOSTS`
3. Generate secure `SECRET_KEY`
4. Configure production PostgreSQL database
5. Set up static file serving (nginx/Apache)
6. Configure email backend (SMTP/SendGrid)
7. Set up HTTPS and security headers
8. Configure logging and monitoring

### Security Checklist
- [ ] `DEBUG=False`
- [ ] Secure `SECRET_KEY` (use environment variable)
- [ ] HTTPS enabled with proper certificates
- [ ] Security headers configured (HSTS, CSP, etc.)
- [ ] Database credentials secured
- [ ] Media files properly served
- [ ] Regular security updates applied
- [ ] Input validation comprehensive
- [ ] CSRF protection enabled
- [ ] SQL injection prevention verified

### Performance Optimization
- [ ] Database connection pooling configured
- [ ] Static files served by web server
- [ ] Database indexes optimized
- [ ] Caching configured (Redis/Memcached)
- [ ] Image optimization enabled
- [ ] Search analytics optimized
- [ ] Query optimization applied

## 🐛 Troubleshooting

### Common Issues

**PostgreSQL Connection Error**
```bash
# Check if PostgreSQL is running
sudo service postgresql status

# Start PostgreSQL
sudo service postgresql start

# Test connection
psql -h localhost -U hobby_hubby_user -d hobby_hubby
```

**Migration Issues**
```bash
# Check migration status
python manage.py showmigrations

# Reset migrations (development only)
python manage.py migrate forums zero
python manage.py migrate

# Fake migrations if needed
python manage.py migrate --fake-initial
```

**Static Files Not Loading**
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check static file settings
python manage.py shell -c "
from django.conf import settings
print('STATIC_URL:', settings.STATIC_URL)
print('STATIC_ROOT:', settings.STATIC_ROOT)
print('STATICFILES_DIRS:', settings.STATICFILES_DIRS)
"
```

**Media Upload Permissions**
```bash
# Fix media directory permissions
sudo chown -R $USER:$USER media/
chmod -R 755 media/

# Create missing directories
mkdir -p media/profile_pictures media/photos
```

**Search Not Working**
```bash
# Check PostgreSQL search extension
python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT * FROM pg_extension WHERE extname = %s', ['pg_trgm'])
print('pg_trgm extension:', cursor.fetchall())
"

# Rebuild search indexes if needed
python manage.py migrate forums --fake
python manage.py migrate forums
```

### Debug Mode
```bash
# Enable verbose debugging
export DEBUG=True
export DJANGO_LOG_LEVEL=DEBUG
python manage.py runserver --verbosity=2

# Check settings
python manage.py diffsettings

# Validate configuration
python manage.py check --deploy
```

## 📈 Performance Monitoring

### Search Analytics
Access comprehensive search analytics at `/forums/admin/analytics/`:
- Search volume trends
- Popular search queries
- Performance metrics (response times, click-through rates)
- User behavior analysis
- Zero-result query identification

### Database Performance
```bash
# Monitor database queries in development
export DEBUG=True
# Check Django Debug Toolbar for query analysis

# Production monitoring
# Set up proper logging and monitoring tools
# Monitor slow queries and optimize indexes
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes with proper tests
4. Run the test suite: `python manage.py test`
5. Ensure code quality: `python manage.py check`
6. Submit a pull request with detailed description

### Code Standards
- Follow Django best practices and PEP 8
- Write comprehensive tests for new features
- Ensure security considerations are addressed
- Update documentation as needed
- Use meaningful commit messages

### Testing Requirements
- All new features must include tests
- Maintain or improve test coverage
- Include both unit and integration tests
- Test error conditions and edge cases

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🙏 Acknowledgments

- **Django Framework**: Robust web framework foundation
- **Bootstrap 5**: Responsive UI framework
- **Font Awesome 6**: Comprehensive icon library
- **PostgreSQL**: Advanced database features and full-text search
- **Chart.js**: Beautiful analytics visualizations
- **All Contributors**: Thank you for making this project better!

---

**Happy Hobby Discussions!** 🎯✨

*Built with ❤️ for the hobby community*