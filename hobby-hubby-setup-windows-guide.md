# Hobby Hubby Setup Guide for Windows

This guide walks you through setting up the Hobby Hubby forum application on a Windows machine from scratch. No prior programming experience required!

## Table of Contents

1. [Install Claude Code](#step-1-install-claude-code)
2. [Install Required Software](#step-2-install-required-software)
3. [Download the Project](#step-3-download-the-project)
4. [Set Up the Project](#step-4-set-up-the-project)
5. [Run the Application](#step-5-run-the-application)
6. [Troubleshooting](#troubleshooting)

---

## Step 1: Install Claude Code

Claude Code is an AI coding assistant that runs in your terminal. You'll use a Claude Code pass to access it.

### 1.1 Open PowerShell

1. Press the **Windows key** on your keyboard
2. Type `PowerShell`
3. Click on **Windows PowerShell** (NOT the "as Administrator" option)

### 1.2 Install Node.js (Required for Claude Code)

Claude Code requires Node.js. Install it first:

1. Go to [https://nodejs.org/](https://nodejs.org/)
2. Download the **LTS** (Long Term Support) version
3. Run the installer and click **Next** through all steps
4. Accept the default options
5. After installation, **close and reopen PowerShell**

Verify Node.js installed correctly:

```powershell
node --version
```

You should see something like `v20.x.x` or similar.

### 1.3 Install Claude Code

In PowerShell, run:

```powershell
npm install -g @anthropic-ai/claude-code
```

Wait for the installation to complete.

### 1.4 Activate Your Claude Code Pass

1. Run Claude Code:

   ```powershell
   claude
   ```

2. When prompted, select **"Use license key"** or similar option
3. Enter the Claude Code pass that was shared with you
4. Follow the on-screen prompts to complete activation

You can type `/exit` to close Claude Code for now.

---

## Step 2: Install Required Software

### 2.1 Install Git

Git is needed to download the project from GitHub.

1. Go to [https://git-scm.com/downloads/win](https://git-scm.com/downloads/win)
2. Click **"Click here to download"** for the latest version
3. Run the installer
4. **Important settings during installation:**
   - Accept the license
   - Use default installation location
   - On "Select Components" - keep defaults
   - On "Choosing the default editor" - select **"Use Visual Studio Code as Git's default editor"** (or Notepad if you don't have VS Code)
   - On "Adjusting the name of the initial branch" - keep default ("Let Git decide")
   - On "Adjusting your PATH environment" - select **"Git from the command line and also from 3rd-party software"**
   - Keep defaults for remaining options
5. Click **Install**
6. **Close and reopen PowerShell** after installation

Verify Git installed correctly:

```powershell
git --version
```

You should see something like `git version 2.x.x`.

### 2.2 Install Python

Django (the framework Hobby Hubby uses) requires Python.

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Click the big yellow **"Download Python 3.x.x"** button
3. Run the installer
4. **IMPORTANT:** Check the box that says **"Add Python to PATH"** at the bottom of the installer window
5. Click **"Install Now"**
6. **Close and reopen PowerShell** after installation

Verify Python installed correctly:

```powershell
python --version
```

You should see something like `Python 3.12.x` or similar.

Also verify pip (Python's package manager):

```powershell
pip --version
```

---

## Step 3: Download the Project

### 3.1 Create a Projects Folder

Let's create a dedicated folder for your coding projects:

```powershell
mkdir ~/Projects
cd ~/Projects
```

### 3.2 Clone the Repository

Download the Hobby Hubby code from GitHub:

```powershell
git clone https://github.com/YOUR-USERNAME/hobby-hubby.git
```

> **Note:** Replace `YOUR-USERNAME/hobby-hubby` with the actual GitHub repository URL provided to you.

### 3.3 Navigate to the Project

```powershell
cd hobby-hubby
```

You can verify you're in the right place:

```powershell
dir
```

You should see files like `manage.py`, `requirements/`, `templates/`, etc.

---

## Step 4: Set Up the Project

### 4.1 Create a Virtual Environment

A virtual environment keeps this project's dependencies separate from other projects:

```powershell
python -m venv venv
```

### 4.2 Activate the Virtual Environment

```powershell
.\venv\Scripts\Activate
```

You should now see `(venv)` at the beginning of your PowerShell prompt. This indicates the virtual environment is active.

> **Important:** You need to activate the virtual environment every time you open a new PowerShell window to work on this project.

### 4.3 Install Project Dependencies

Install all the required Python packages:

```powershell
pip install -r requirements/development.txt
```

This will download and install Django and other required packages. It may take a minute or two.

### 4.4 Create the .env File (Optional)

For development, this step is optional since defaults are provided. But if you want to customize settings:

```powershell
copy .env.example .env
```

The development settings use SQLite (a simple file-based database) so no database server setup is needed!

### 4.5 Run Database Migrations

Set up the database structure:

```powershell
python manage.py migrate
```

You'll see a series of "Applying..." messages. This creates the SQLite database file (`db.sqlite3`).

### 4.6 Create Initial Forum Categories

Set up the forum categories:

```powershell
python manage.py setup_hobby_categories
```

### 4.7 Create a Superuser (Admin Account)

Create an admin account so you can access the admin panel:

```powershell
python manage.py createsuperuser
```

You'll be prompted for:
- **Email address:** Enter your email (e.g., `admin@example.com`)
- **Display name:** Enter a display name (e.g., `Admin`)
- **Password:** Enter a secure password (you won't see it as you type)
- **Password (again):** Confirm the password

---

## Step 5: Run the Application

### 5.1 Start the Development Server

```powershell
python manage.py runserver
```

You should see output like:

```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
January 24, 2026 - 12:00:00
Django version 4.2.7, using settings 'hobby_hubby.settings.development'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### 5.2 View the Application

Open your web browser and go to:

- **Main site:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Admin panel:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

Log into the admin panel with the superuser email and password you created.

### 5.3 Stop the Server

To stop the server, go back to PowerShell and press `Ctrl + C`.

---

## Using Claude Code with Hobby Hubby

Now that everything is set up, you can use Claude Code to help you work on the project!

### Start Claude Code in the Project Directory

Make sure you're in the project folder and your virtual environment is active:

```powershell
cd ~/Projects/hobby-hubby
.\venv\Scripts\Activate
claude
```

Claude Code will analyze the project and help you understand, modify, and extend the codebase.

### Example Commands in Claude Code

Once inside Claude Code, you can ask things like:
- "Explain how the forum system works"
- "Show me the user registration flow"
- "Help me add a new feature to..."
- "Run the tests"

---

## Quick Reference: Daily Workflow

Every time you want to work on the project:

```powershell
# 1. Open PowerShell and go to the project
cd ~/Projects/hobby-hubby

# 2. Activate the virtual environment
.\venv\Scripts\Activate

# 3. Start the server (to run the app)
python manage.py runserver

# OR start Claude Code (to get coding help)
claude
```

---

## Troubleshooting

### "python is not recognized"

Python wasn't added to PATH. Either:
- Reinstall Python and check "Add Python to PATH"
- Or use `py` instead of `python` in all commands

### "pip is not recognized"

Try using:
```powershell
python -m pip install -r requirements/development.txt
```

### Virtual environment won't activate

If you see an error about "execution of scripts is disabled":

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again.

### "No module named 'django'"

Make sure your virtual environment is activated (you should see `(venv)` in your prompt). If not:

```powershell
.\venv\Scripts\Activate
pip install -r requirements/development.txt
```

### Port already in use

If you see "port 8000 is already in use", either:
- Close other applications using that port
- Or run on a different port: `python manage.py runserver 8001`

### Database errors

If you get database errors, try resetting the database:

```powershell
del db.sqlite3
python manage.py migrate
python manage.py setup_hobby_categories
python manage.py createsuperuser
```

### Claude Code license issues

If Claude Code won't accept your pass:
- Make sure you're connected to the internet
- Try running `claude logout` then `claude` again
- Contact the person who shared the pass for help

---

## What's Next?

Once you have everything running:

1. **Explore the app** - Create an account, browse forums, create posts
2. **Check the admin panel** - See how the database is organized
3. **Read the code** - Look at the `templates/`, `forums/`, and `accounts/` folders
4. **Ask Claude Code** - Get explanations and help with any part of the codebase

Happy coding!
