# Hobby Hubby macOS Quickstart Guide

Get the app running locally on macOS in minutes.

---

## First Time Setup

### 1. Install Prerequisites

If you don't have Python 3 and Git installed:

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and Git
brew install python git
```

### 2. Clone the Repo

```bash
cd ~/Projects  # or wherever you keep projects
git clone https://github.com/YOUR-USERNAME/hobby-hubby.git
cd hobby-hubby
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements/development.txt
```

### 5. Set Up Database

```bash
python manage.py migrate
python manage.py setup_hobby_categories
```

### 6. Create Admin Account

```bash
python manage.py createsuperuser
```

### 7. Run the Server

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## Daily Startup

```bash
cd ~/Projects/hobby-hubby
source venv/bin/activate
python manage.py runserver
```

---

## Quick Commands

| Task | Command |
|------|---------|
| Start server | `python manage.py runserver` |
| Run tests | `pytest` |
| Create migration | `python manage.py makemigrations` |
| Apply migrations | `python manage.py migrate` |
| Django shell | `python manage.py shell` |
| Create superuser | `python manage.py createsuperuser` |
| Collect static files | `python manage.py collectstatic` |

---

## URLs

- **App:** http://127.0.0.1:8000/
- **Admin:** http://127.0.0.1:8000/admin/
- **Forums:** http://127.0.0.1:8000/forums/

---

## Using Claude Code

```bash
cd ~/Projects/hobby-hubby
source venv/bin/activate
claude
```

---

## Troubleshooting

### "No module named 'django'"
Activate your virtual environment:
```bash
source venv/bin/activate
```

### Database errors
Reset the database:
```bash
rm db.sqlite3
python manage.py migrate
python manage.py setup_hobby_categories
```

### Port in use
Run on a different port:
```bash
python manage.py runserver 8001
```

### Permission denied
Make sure you own the project directory:
```bash
sudo chown -R $(whoami) ~/Projects/hobby-hubby
```
