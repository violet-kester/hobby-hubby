# Text Formatting Debug Guide

## Issue Description
Users report that markup options for text formatting (bold, italics, underline) are not working when posting threads or replying in the forum at `http://127.0.0.1:8000/forums/games-entertainment/books-reading/what-are-you-reading/reply/`.

## Current Implementation Status

### ✅ What's Already Implemented

1. **Rich Text Toolbar**: Both thread creation and reply forms have formatting toolbars with:
   - Bold button (Ctrl+B)
   - Italic button (Ctrl+I)
   - Underline button (Ctrl+U)
   - JavaScript event handlers for button clicks and keyboard shortcuts

2. **Allowed HTML Tags**: The forms allow the following HTML tags:
   ```python
   ALLOWED_TAGS = ['b', 'strong', 'i', 'em', 'u', 'br', 'p']
   ALLOWED_ATTRIBUTES = {}
   ```

3. **Content Processing**:
   - `clean_rich_text()` function processes content with bleach sanitization
   - Form validation in `ThreadCreateForm` and `PostCreateForm`
   - Preview functionality via AJAX

## Debugging Infrastructure Added

### 🔍 Server-Side Logging

**File: `forums/forms.py`**
- Added comprehensive logging to `clean_rich_text()` function
- Logs content length, HTML tag detection, and bleach processing
- Added logging to form validation methods

**File: `forums/views.py`**
- Added detailed logging to `post_create()` view
- Added logging to `preview_content()` AJAX view
- Tracks user actions, form validation, and content processing

**File: `hobby_hubby/settings/development.py`**
- Added comprehensive logging configuration
- Console and file logging enabled
- Debug level logging for forums app
- Log file: `debug.log` in project root

### 🔍 Client-Side Logging

**Files: `templates/forums/post_create.html` & `templates/forums/thread_create.html`**
- Added console logging to all formatting button clicks
- Added console logging to keyboard shortcuts
- Added console logging to `insertFormatting()` function
- Added console logging to AJAX preview requests

## Debugging Steps

### 1. Check Browser Console
Open browser developer tools (F12) and check the Console tab when:
- Clicking formatting buttons
- Using keyboard shortcuts (Ctrl+B, Ctrl+I, Ctrl+U)
- Submitting the form
- Using the preview feature

Expected logs:
```javascript
Bold button clicked - formatting text
insertFormatting called: tags=<b></b>, selectedText='example', cursor=0-7
```

### 2. Check Server Logs

**Start Django server with verbose logging:**
```bash
cd /Users/gwenmurtha/projects/hobby-hubby
python manage.py runserver --settings=hobby_hubby.settings.development
```

**Monitor the debug.log file:**
```bash
tail -f debug.log
```

Expected logs when submitting a post:
```
DEBUG forums.forms clean_rich_text called with content length: 45
INFO forums.forms clean_rich_text: HTML tags detected, processing with clean_rich_text
DEBUG forums.views post_create: form validation successful
INFO forums.views post_create: creating post with content length 45
```

### 3. Test Content Processing

Test various formatting scenarios:
1. **Plain text**: "Hello world"
2. **Bold text**: "Hello <b>world</b>"
3. **Mixed formatting**: "Hello <b>bold</b> and <i>italic</i> text"
4. **Keyboard shortcuts**: Select text and press Ctrl+B
5. **Button clicks**: Select text and click formatting buttons

### 4. Check Form Data

In browser dev tools Network tab:
1. Submit a formatted post
2. Check the POST request to `/forums/.../reply/`
3. Verify the `content` field contains HTML tags
4. Check the response for any errors

### 5. Database Verification

Check if formatted content is properly saved:
```sql
-- Connect to SQLite database
sqlite3 db.sqlite3
SELECT content FROM forums_post ORDER BY created_at DESC LIMIT 5;
```

## Common Issues & Solutions

### Issue 1: JavaScript Not Working
- **Check**: Browser console for JavaScript errors
- **Fix**: Ensure jQuery/Bootstrap dependencies are loaded
- **Debug**: Verify `contentField` element is found

### Issue 2: HTML Tags Being Stripped
- **Check**: Server logs for bleach processing
- **Debug**: Verify `ALLOWED_TAGS` includes the tags you're using
- **Fix**: Update `ALLOWED_TAGS` if necessary

### Issue 3: Content Not Saving
- **Check**: Form validation logs for errors
- **Debug**: Check POST data in network tab
- **Fix**: Verify CSRF token and form fields

### Issue 4: Preview Not Working
- **Check**: AJAX request logs and responses
- **Debug**: Verify preview endpoint URL is correct
- **Fix**: Check CSRF token and AJAX headers

## Quick Tests

### Test 1: Button Functionality
1. Go to reply page
2. Type some text
3. Select the text
4. Click Bold button
5. Check if `<b>` tags are added around selected text

### Test 2: Keyboard Shortcuts
1. Type some text
2. Select the text
3. Press Ctrl+B
4. Check if `<b>` tags are added

### Test 3: Form Submission
1. Enter content with formatting: "This is <b>bold</b> text"
2. Submit the form
3. Check server logs for processing
4. Verify the post appears with bold formatting

### Test 4: Preview Feature
1. Enter formatted content
2. Click Preview button
3. Check if formatting is displayed correctly
4. Check browser console and server logs

## Log Analysis

### Successful Format Application
```
DEBUG forums.views post_create: content preview: 'Hello <b>world</b>'
INFO forums.forms clean_rich_text: HTML tags detected, processing with clean_rich_text
DEBUG forums.forms clean_rich_text: after bleach cleaning: 'Hello <b>world</b>'
INFO forums.views post_create: successfully created post 123
```

### Failed Format Application
```
DEBUG forums.views post_create: content preview: 'Hello world'
DEBUG forums.forms clean_rich_text: no HTML formatting tags found in content
```

## Files Modified

1. `forums/forms.py` - Added logging to content processing
2. `forums/views.py` - Added logging to views
3. `templates/forums/post_create.html` - Added JavaScript logging
4. `templates/forums/thread_create.html` - Added JavaScript logging
5. `hobby_hubby/settings/development.py` - Added logging configuration
6. `TEXT_FORMATTING_DEBUG_GUIDE.md` - This debug guide

## Next Steps

If the issue persists after checking all the above:
1. Enable Django debug mode if not already enabled
2. Check browser compatibility (test in different browsers)
3. Verify the bleach library version and configuration
4. Test with minimal content to isolate the issue
5. Check for any custom CSS that might be interfering with the UI

The logging infrastructure will help identify exactly where the text formatting is failing in the process.