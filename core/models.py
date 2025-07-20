from django.db import models


class TimestampedModel(models.Model):
    """
    Abstract base model that provides timestamp fields for created and updated times.
    
    This mixin provides automatic timestamp tracking for all models that inherit from it.
    The created_at field is set once when the object is created, and updated_at is
    updated every time the object is saved.
    """
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when object was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time when object was last updated")
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
