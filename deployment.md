# Hobby Hubby Deployment Guide - Render.com

This guide documents the complete deployment process for deploying Hobby Hubby to Render.com with a free PostgreSQL database.

## Deployment Status

**Current Step**: Step 4 - Trigger Redeploy After Dependency Fix

---

## Prerequisites ✅ COMPLETED

- [x] Django app with PostgreSQL configuration
- [x] GitHub repository with code pushed
- [x] Render.com account created
- [x] Production settings configured (`hobby_hubby/settings/production.py`)
- [x] Deployment files created:
  - `build.sh` - Build script
  - `render.yaml` - Infrastructure-as-code configuration
  - `runtime.txt` - Python version specification

---

## Step 1: Create Deployment Configuration ✅ COMPLETED

### Files Created

**`build.sh`** - Automated build script:
```bash
#!/usr/bin/env bash
set -o errexit

pip install -r requirements/production.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

**`render.yaml`** - Blueprint configuration:
- PostgreSQL database: `hobby-hubby-db`
- Web service: `hobby-hubby`
- Auto-linked DATABASE_URL environment variable

**`runtime.txt`** - Python version:
```
python-3.11.0
```

**`production.py`** updates:
- Added `dj_database_url` import
- Configured DATABASES to use DATABASE_URL environment variable
- Connection pooling with `conn_max_age=600`
- Health checks enabled

---

## Step 2: Commit and Push Deployment Files ✅ COMPLETED

```bash
git add build.sh render.yaml runtime.txt hobby_hubby/settings/production.py
git commit -m "Add Render deployment configuration for PostgreSQL hosting"
git push origin main
```

**Commit**: `2f71edf` - Initial deployment configuration

---

## Step 3: Initial Deployment Attempt ✅ COMPLETED (FAILED)

### 3a. Deploy via Render Blueprint

1. Navigate to Render Dashboard: https://dashboard.render.com
2. Click **"New +"** → **"Blueprint"**
3. Connect GitHub repository: `violet-kester/hobby-hubby`
4. Review blueprint services:
   - PostgreSQL Database: `hobby-hubby-db`
   - Web Service: `hobby-hubby`
5. Click **"Apply"** to create services

### 3b. Deployment Failed ❌

**Error**: `ModuleNotFoundError: No module named 'bleach'`

**Root Cause**: The `forums/forms.py` imports bleach for HTML sanitization, but it was missing from `requirements/base.txt`

**Static Files**: ✅ Successfully collected 128 static files
**Migrations**: ❌ Failed during pre-migration checks

---

## Step 4: Fix Missing Dependencies ✅ COMPLETED

### 4a. Add Missing Package

Updated `requirements/base.txt`:
```
Django==4.2.7
python-decouple==3.8
psycopg2-binary==2.9.9
Pillow==10.0.1
bleach==6.1.0  # Added for HTML sanitization
```

### 4b. Commit and Push Fix

```bash
git add requirements/base.txt
git commit -m "Fix missing bleach dependency for deployment"
git push origin main
```

**Commit**: `2e7966b` - Dependency fix

---

## Step 5: Trigger Redeploy 🔄 **CURRENT STEP**

### Option A: Manual Redeploy (Recommended for Now)

1. Go to Render Dashboard: https://dashboard.render.com
2. Click on **hobby-hubby** web service
3. Click **"Manual Deploy"** → **"Deploy latest commit"**
4. Verify it's deploying commit `2e7966b`

### Option B: Automatic Redeploy

Render should auto-detect the new commit and redeploy within a few minutes.

### Option C: Using Render MCP (If Available)

```
# In Claude Code conversation:
"Deploy the latest commit to my hobby-hubby service"
```

---

## Step 6: Monitor Deployment ⏳ PENDING

### Expected Build Process

1. **Clone Repository**: Fetch latest code from GitHub
2. **Install Python 3.11.0**: Set up runtime environment
3. **Run build.sh**:
   - Install dependencies from `requirements/production.txt`
   - Collect static files (expect ~128 files)
   - Run database migrations
4. **Start Gunicorn**: Launch web server

### Success Indicators

Look for these in the logs:
```
✅ Successfully installed bleach-6.1.0
✅ 128 static files copied to '/opt/render/project/src/staticfiles'
✅ Running migrations...
✅ Starting gunicorn
✅ Listening at: http://0.0.0.0:10000
✅ Your service is live 🎉
```

### Deployment Time

First deployment: ~5-10 minutes
Subsequent deployments: ~2-5 minutes

---

## Step 7: Configure ALLOWED_HOSTS ⏳ PENDING

After successful deployment, you'll receive a URL like:
```
https://hobby-hubby-XXXX.onrender.com
```

### Steps to Configure

1. Copy your service URL (without `https://`)
2. In Render Dashboard, go to **hobby-hubby** web service
3. Click **"Environment"** in the left sidebar
4. Click **"Add Environment Variable"** or edit existing `ALLOWED_HOSTS`
5. Set:
   - **Key**: `ALLOWED_HOSTS`
   - **Value**: `hobby-hubby-XXXX.onrender.com`
6. Click **"Save Changes"**
7. Render will automatically redeploy (~2 minutes)

### Why This Is Needed

Django's `ALLOWED_HOSTS` setting prevents HTTP Host header attacks. The production settings require this to be explicitly set:

```python
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=lambda v: [s.strip() for s in v.split(',')])
```

---

## Step 8: Verify Deployment ⏳ PENDING

### 8a. Test Homepage

1. Visit your Render URL: `https://hobby-hubby-XXXX.onrender.com`
2. Verify the homepage loads correctly
3. Check that static files (CSS, images) are loading

### 8b. Test Database Connectivity

1. Try to access any forum page
2. Verify database queries are working
3. Check that no 500 errors appear

### 8c. Test User Registration (Optional)

1. Navigate to registration page
2. Create a test account
3. Verify email verification works (if configured)

### 8d. Check Admin Panel

1. Go to `https://hobby-hubby-XXXX.onrender.com/admin/`
2. Create superuser if needed (see Step 9)

---

## Step 9: Post-Deployment Tasks ⏳ PENDING

### 9a. Create Superuser Account

You'll need to run this via Render Shell:

1. In Render Dashboard, go to **hobby-hubby** web service
2. Click **"Shell"** tab
3. Run:
```bash
python manage.py createsuperuser
```
4. Follow prompts to create admin account

### 9b. Set Up Initial Categories

Run management commands to populate initial data:

```bash
# Via Render Shell
python manage.py setup_hobby_categories
python manage.py create_sample_subcategories
```

### 9c. Configure Email (Optional)

If you want email verification and notifications:

1. Set up email service (Gmail, SendGrid, etc.)
2. Add environment variables in Render:
   - `EMAIL_HOST`
   - `EMAIL_PORT`
   - `EMAIL_HOST_USER`
   - `EMAIL_HOST_PASSWORD`
   - `DEFAULT_FROM_EMAIL`

---

## Step 10: Monitor and Maintain ⏳ PENDING

### Important Free Tier Limitations

**PostgreSQL Database**:
- Free for 90 days, then requires upgrade or renewal
- 1 GB storage limit
- Automatically backed up

**Web Service**:
- Spins down after 15 minutes of inactivity
- First request after sleep takes ~30 seconds (cold start)
- 750 hours/month free (enough for always-on if sole service)

### Monitoring Tips

1. **Check Logs Regularly**:
   - Render Dashboard → hobby-hubby → Logs
   - Monitor for errors and performance issues

2. **Database Usage**:
   - Render Dashboard → hobby-hubby-db → Info
   - Monitor storage usage to avoid hitting limits

3. **Set Up Alerts** (Optional):
   - Configure email notifications for deploy failures
   - Monitor uptime via external service (UptimeRobot, etc.)

---

## Troubleshooting Common Issues

### Issue: DisallowedHost Error

**Symptom**: `400 Bad Request - DisallowedHost`

**Solution**: Add your Render URL to ALLOWED_HOSTS (Step 7)

### Issue: Static Files Not Loading

**Symptom**: Pages load but no CSS/images

**Solution**:
- Check `build.sh` ran collectstatic successfully
- Verify WhiteNoise middleware is in production settings
- Check browser console for 404 errors

### Issue: Database Connection Errors

**Symptom**: `OperationalError: could not connect to server`

**Solution**:
- Verify DATABASE_URL environment variable is set
- Check database service is running in Render dashboard
- Ensure database and web service are in same region

### Issue: Build Fails on Migrations

**Symptom**: `django.db.migrations.exceptions.InconsistentMigrationHistory`

**Solution**:
- This is a fresh database, all migrations should apply cleanly
- If issues persist, check migration files for conflicts
- May need to delete and recreate database in extreme cases

### Issue: Service Keeps Spinning Down

**Symptom**: Slow response times, cold starts

**Solution**:
- This is expected on free tier
- Consider upgrading to paid tier for always-on service
- Or use external ping service to keep it awake

---

## Deployment Checklist

Use this checklist for future deployments:

- [ ] Update code locally
- [ ] Run tests: `pytest`
- [ ] Commit changes with descriptive message
- [ ] Push to GitHub: `git push origin main`
- [ ] Monitor Render auto-deploy or trigger manual deploy
- [ ] Check deployment logs for errors
- [ ] Verify application is accessible
- [ ] Test critical functionality
- [ ] Update environment variables if needed
- [ ] Monitor for first 24 hours

---

## Rollback Procedure

If deployment fails or causes issues:

### Option 1: Redeploy Previous Commit

1. In Render Dashboard, go to **hobby-hubby** service
2. Click **"Manual Deploy"**
3. Select previous commit from dropdown
4. Click **"Deploy"**

### Option 2: Revert Git Commit

```bash
git revert HEAD
git push origin main
# Render will auto-deploy the revert
```

---

## Next Steps After Successful Deployment

1. **Custom Domain** (Optional):
   - Purchase domain
   - Add custom domain in Render settings
   - Configure DNS records
   - Render provides free SSL certificate

2. **Monitoring & Analytics**:
   - Set up Google Analytics
   - Configure error tracking (Sentry, etc.)
   - Monitor performance metrics

3. **Backup Strategy**:
   - Render auto-backs up PostgreSQL
   - Consider periodic manual exports for safety
   - Document recovery procedures

4. **Performance Optimization**:
   - Enable database connection pooling (already configured)
   - Optimize database queries
   - Consider CDN for static files if traffic grows

5. **Security Hardening**:
   - Review security settings in production.py
   - Set up Content Security Policy (CSP)
   - Regular dependency updates
   - Monitor for security advisories

---

## Resources

- **Render Documentation**: https://render.com/docs
- **Django Deployment Checklist**: https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/
- **Render Python Guide**: https://render.com/docs/deploy-django
- **Render PostgreSQL Guide**: https://render.com/docs/databases
- **Troubleshooting Deploys**: https://render.com/docs/troubleshooting-deploys

---

## Deployment History

| Date | Commit | Status | Notes |
|------|--------|--------|-------|
| 2025-11-20 | 2f71edf | ❌ Failed | Initial deployment - missing bleach dependency |
| 2025-11-20 | 2e7966b | 🔄 In Progress | Added bleach==6.1.0 to requirements |

---

**Last Updated**: 2025-11-20
**Current Status**: Awaiting redeploy with dependency fix
