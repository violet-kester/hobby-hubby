<p align="center">
  <img src="static/images/logo-square.png" alt="Hobby Hubby Logo" width="150">
</p>

<h1 align="center">Hobby Hubby</h1>

<p align="center">
  A Django-based social forum platform for hobby enthusiasts to connect, share, and discuss their passions.
</p>

**Live Site:** [hobbyhubby.onrender.com](https://hobbyhubby.onrender.com) (auto-deploys from main)

---

## Features

| Feature | Description |
|---------|-------------|
| **Forum System** | Hierarchical categories, subcategories, threads, and posts |
| **Search** | Full-text search with PostgreSQL, autocomplete, and filters |
| **User Profiles** | Email-based auth, profile customization, hobby tracking |
| **Messaging** | Private conversations with unread tracking |
| **Social** | Friend system, photo galleries, bookmarking |
| **Voting** | Upvote posts with real-time AJAX updates |
| **Analytics** | Search analytics dashboard with visualizations |

---

## Tech Stack

- **Backend:** Django 4.2 LTS, Python 3.10+
- **Database:** PostgreSQL (SQLite for local dev)
- **Frontend:** Bootstrap 5, Font Awesome 6
- **Deployment:** Render (auto-deploy on push to main)

---

## Quick Start

See the setup guide for your platform:

- [Windows Setup Guide](hobby-hubby-setup-windows-guide.md) — Full setup including Claude Code
- [Windows Quickstart](hobby-hubby-windows-quickstart-guide.md)
- [macOS Quickstart](hobby-hubby-macos-quickstart-guide.md)
- [WSL Quickstart](hobby-hubby-wsl-quickstart-guide.md)

### TL;DR (WSL/macOS/Linux)

```bash
git clone https://github.com/YOUR-USERNAME/hobby-hubby.git
cd hobby-hubby
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/development.txt
python manage.py migrate
python manage.py setup_hobby_categories
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/

---

## Project Structure

```
hobby-hubby/
├── accounts/          # User management, auth, profiles, messaging
├── forums/            # Forum system, search, analytics
├── core/              # Shared utilities and base models
├── hobby_hubby/       # Project settings
│   └── settings/
│       ├── base.py
│       ├── development.py
│       └── production.py
├── templates/         # Django templates
├── static/            # CSS, JS, images
├── tests/             # Test suites
└── requirements/      # Dependencies by environment
```

---

## Development

### Common Commands

```bash
python manage.py runserver          # Start dev server
python manage.py migrate            # Apply migrations
python manage.py makemigrations     # Create migrations
python manage.py createsuperuser    # Create admin account
pytest                              # Run tests
```

### URLs

| URL | Description |
|-----|-------------|
| `/` | Home page |
| `/forums/` | Forum index |
| `/admin/` | Django admin |
| `/accounts/login/` | Login |
| `/forums/search/` | Search |

---

## Git Workflow

See [GitHub Workflow Guide](hobby-hubby-github-workflow-guide.md) for the team workflow.

```bash
git stash                    # Save local changes
git pull origin main         # Get latest
git stash pop                # Restore changes
git add .                    # Stage changes
git commit -m "message"      # Commit
git push origin main         # Push (triggers auto-deploy)
```

---

## Deployment

Hosted on [Render](https://render.com). Pushes to `main` trigger automatic deployment.

### Environment Variables (Production)

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DATABASE_URL` | PostgreSQL connection string |
| `DEBUG` | Set to `False` |
| `ALLOWED_HOSTS` | Domain names |

---

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_forum_system.py

# Run with coverage
pytest --cov=.
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](CLAUDE.md) | Project architecture and implementation details |
| [Windows Setup Guide](hobby-hubby-setup-windows-guide.md) | Complete beginner setup |
| [GitHub Workflow](hobby-hubby-github-workflow-guide.md) | Git workflow for the team |

---

## License

MIT
