# Settings Configuration

Split settings structure for environment-specific configuration.

## Structure

```
hobby_hubby/settings/
├── base.py         # Shared settings (imported by dev/prod)
├── development.py  # Dev overrides (SQLite, DEBUG=True)
└── production.py   # Prod overrides (PostgreSQL, HTTPS)
```

## Database

**Development**: SQLite (`db.sqlite3`)
**Production**: PostgreSQL via `DATABASE_URL` env var with `dj_database_url`

```python
# Base (env vars with defaults)
DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# Production
DATABASE_URL=postgres://user:pass@host:port/dbname
```

## Security Settings

### Always Active (base.py)
| Setting | Value |
|---------|-------|
| SECURE_BROWSER_XSS_FILTER | True |
| SECURE_CONTENT_TYPE_NOSNIFF | True |
| X_FRAME_OPTIONS | DENY |
| SESSION_COOKIE_HTTPONLY | True |
| SESSION_COOKIE_SAMESITE | Lax |
| CSRF_COOKIE_HTTPONLY | True |
| CSRF_COOKIE_SAMESITE | Lax |

### Production Only
| Setting | Value |
|---------|-------|
| SESSION_COOKIE_SECURE | True |
| CSRF_COOKIE_SECURE | True |
| SECURE_SSL_REDIRECT | True |
| SECURE_HSTS_SECONDS | 31536000 (1 year) |

### File Uploads
- Max size: 10MB (`FILE_UPLOAD_MAX_MEMORY_SIZE`)
- Allowed types: `.jpg, .jpeg, .png, .gif, .webp`

### Password Validators
- Minimum 8 characters
- User attribute similarity check
- Common password rejection
- Numeric-only rejection

## Authentication

```python
AUTH_USER_MODEL = 'accounts.CustomUser'
AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',  # Email-based auth
    'django.contrib.auth.backends.ModelBackend',  # Fallback
]
```

## Static Files

**Development**: Django default
**Production**: WhiteNoise with compressed manifest

```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

## Email

**Development**: Console backend (logs to terminal)
**Production**: SMTP via env vars (EMAIL_HOST, EMAIL_PORT, etc.)

## Environment Variables

Required for production:
- `SECRET_KEY` - Django secret key
- `DATABASE_URL` - PostgreSQL connection string
- `ALLOWED_HOSTS` - Comma-separated hostnames
- `DEBUG` - Set to False

Optional:
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
