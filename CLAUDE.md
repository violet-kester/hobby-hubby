# Hobby Hubby - Project Documentation

Django 4.2 LTS social forum application with email-based authentication.

## Development Principles

1. **Security First** - All features implemented with OWASP top 10 in mind
2. **TDD Approach** - Red-Green-Refactor; tests fail first for expected reasons
3. **Minimal Changes** - Only make directly requested changes; avoid over-engineering
4. **Document Code** - Keep CLAUDE.md files updated with implementation notes

## Project Structure

```
hobby_hubby/
├── hobby_hubby/settings/   # Split settings (base/dev/prod) - see hobby_hubby/CLAUDE.md
├── core/                   # Shared utilities, TimestampedModel - see core/CLAUDE.md
├── accounts/               # User auth, profiles, messaging - see accounts/CLAUDE.md
├── forums/                 # Forum system, search - see forums/CLAUDE.md
├── tests/                  # Project-wide tests
├── static/css/             # hh-colors.css (color system)
├── templates/              # Django templates
└── media/                  # User uploads
```

## Quick Reference

| App | Purpose | Key Models |
|-----|---------|------------|
| core | Base utilities | TimestampedModel (abstract) |
| accounts | Auth & social | CustomUser, Friendship, Conversation, Message, Photo |
| forums | Forum & search | Category, Subcategory, Thread, Post, Vote, Bookmark, SearchHistory |

## Security Summary

- **Auth**: Email-based (no username), email verification, secure tokens
- **XSS**: Django auto-escaping, bleach sanitization, CSP headers
- **CSRF**: Middleware enabled, secure cookies, SameSite=Lax
- **Files**: 10MB limit, whitelist validation (jpg/png/gif/webp)
- **Sessions**: HTTPOnly, Secure (prod), SameSite=Lax
- **Passwords**: 8+ chars, Django validators (similarity, common, numeric)

## Testing

```bash
pytest                           # Run all tests
pytest tests/test_<module>.py    # Run specific test file
pytest -k "test_name"            # Run tests matching pattern
```

Key test files:
- `test_friend_system.py` - Friendship functionality
- `test_search_*.py` - Search features (history, suggestions, highlighting)
- `test_messaging.py` - Private messaging
- `test_forum_*.py` - Forum operations

## Color System

Six hobby categories with logo-inspired colors:
- Creative & Arts: Coral Pink (#EF7674)
- Sports & Fitness: Bright Cyan (#4DD0E1)
- Games & Entertainment: Vibrant Orange (#FF7043)
- Technology & Science: Fresh Lime (#9CCC65)
- Food & Culinary: Warm Amber (#FFD54F)
- Lifestyle & Social: Sophisticated Slate (#334155)

CSS classes: `category-creative-arts`, `category-sports-fitness`, etc.

## Key Technical Decisions

- Email-based auth (no username field)
- PostgreSQL for production, SQLite for dev/test
- Dual search: PostgreSQL full-text with SQLite fallback
- Bootstrap 5 responsive UI
- Django signals for denormalized counts
