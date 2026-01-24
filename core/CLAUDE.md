# Core App

Shared utilities and base models for the Hobby Hubby project.

## TimestampedModel

Abstract base model inherited by all other models in accounts and forums apps.

```python
class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']
```

## Admin Customization

`HobbyHubbyAdminSite` provides branded admin interface:
- site_header: "Hobby Hubby Administration"
- site_title: "Hobby Hubby Admin"
- index_title: "Welcome to Hobby Hubby Administration"

Currently using default admin site; custom site available at `hobby_hubby_admin` instance.

## Notes

- No migrations (abstract models don't create tables)
- No views or tests (utility module only)
- All models in accounts/ and forums/ inherit TimestampedModel
