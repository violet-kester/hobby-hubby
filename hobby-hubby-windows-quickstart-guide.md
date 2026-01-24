# Hobby Hubby Windows Quickstart Guide

Get the app running locally on Windows in minutes.

---

## First Time Setup

### 1. Install Prerequisites

- **Python:** Download from [python.org](https://www.python.org/downloads/) - check "Add Python to PATH" during install
- **Git:** Download from [git-scm.com](https://git-scm.com/downloads/win)

### 2. Clone the Repo

Open PowerShell:

```powershell
cd ~/Projects  # or wherever you keep projects
git clone https://github.com/YOUR-USERNAME/hobby-hubby.git
cd hobby-hubby
```

### 3. Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

> If you get an execution policy error, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### 4. Install Dependencies

```powershell
pip install -r requirements/development.txt
```

### 5. Set Up Database

```powershell
python manage.py migrate
python manage.py setup_hobby_categories
```

### 6. Create Admin Account

```powershell
python manage.py createsuperuser
```

### 7. Run the Server

```powershell
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## Daily Startup

```powershell
cd ~/Projects/hobby-hubby
.\venv\Scripts\Activate
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

```powershell
cd ~/Projects/hobby-hubby
.\venv\Scripts\Activate
claude
```

---

## Troubleshooting

### "python is not recognized"
Python wasn't added to PATH. Reinstall and check "Add Python to PATH", or use `py` instead of `python`.

### "No module named 'django'"
Activate your virtual environment:
```powershell
.\venv\Scripts\Activate
```

### Virtual environment won't activate
Run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Database errors
Reset the database:
```powershell
del db.sqlite3
python manage.py migrate
python manage.py setup_hobby_categories
```

### Port in use
Run on a different port:
```powershell
python manage.py runserver 8001
```
