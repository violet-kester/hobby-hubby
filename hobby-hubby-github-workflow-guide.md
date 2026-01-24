# GitHub Workflow Guide

A simple workflow for collaborating on Hobby Hubby. We work directly on `main` - no branches needed.

---

## The Flow

```
Save your work → Get latest changes → Restore your work → Commit → Push → Auto-deploy
```

---

## Step-by-Step

### 1. Stash Your Changes

Before pulling, save your local changes temporarily:

```bash
git stash
```

This stores your uncommitted work and gives you a clean slate.

### 2. Pull from Main

Get the latest code from GitHub:

```bash
git pull origin main
```

### 3. Unstash Your Changes

Restore your saved work:

```bash
git stash pop
```

### 4. Resolve Merge Conflicts (If Any)

If you see conflict markers in files like this:

```
<<<<<<< Updated upstream
their code here
=======
your code here
>>>>>>> Stashed changes
```

**Option A:** Fix manually - edit the file to keep the right code and remove the markers.

**Option B:** Ask Claude for help:
```
claude "help me resolve the merge conflicts in this file"
```

After resolving, stage the fixed files:

```bash
git add <filename>
```

### 5. Commit Your Changes

Stage and commit your work:

```bash
git add .
git commit -m "Brief description of what you changed"
```

Write clear commit messages like:
- "Add user profile photo upload"
- "Fix login redirect bug"
- "Update homepage styling"

### 6. Push to Main

Send your commit to GitHub:

```bash
git push origin main
```

### 7. Auto-Deploy

Once pushed, Render automatically deploys the changes. Check the Render dashboard if you want to monitor the deployment.

---

## Quick Reference

```bash
# The full flow in order:
git stash
git pull origin main
git stash pop
# resolve conflicts if needed
git add .
git commit -m "Your message"
git push origin main
```

---

## Common Situations

### No local changes to save?

Skip stash/unstash - just pull, make changes, commit, push:

```bash
git pull origin main
# make your changes
git add .
git commit -m "Your message"
git push origin main
```

### Want to see what's stashed?

```bash
git stash list
```

### Need to discard your local changes?

```bash
git checkout .
```

### Check current status?

```bash
git status
```

---

## Tips

- **Pull often** - reduces merge conflicts
- **Commit small** - easier to track and revert if needed
- **Write clear messages** - your future self will thank you
- **Ask Claude** - if anything goes wrong, Claude Code can help fix it
