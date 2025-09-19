"""
Forms for forum thread and post creation.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
import bleach
from .models import Thread, Post

# Allowed HTML tags and attributes for rich text formatting
ALLOWED_TAGS = ['b', 'strong', 'i', 'em', 'u', 'br', 'p']
ALLOWED_ATTRIBUTES = {}

def clean_rich_text(content):
    """Clean content while preserving allowed HTML formatting."""
    if not content:
        return content

    # Convert newlines to <br> tags before sanitizing
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    content = content.replace('\n', '<br>')

    # Use bleach to sanitize HTML while keeping allowed tags
    cleaned = bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

    return cleaned


class ThreadCreateForm(forms.Form):
    """Form for creating new threads."""

    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter thread title...',
            'required': True
        }),
        help_text='Maximum 200 characters'
    )

    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control rich-text-editor',
            'rows': 8,
            'placeholder': 'Write your message...',
            'required': True
        }),
        help_text='Share your thoughts, questions, or ideas. Use the toolbar to format text.'
    )

    def clean_title(self):
        """Validate and clean the title field."""
        title = self.cleaned_data.get('title', '').strip()

        if not title:
            raise ValidationError('Title cannot be empty.')

        if len(title) > 200:
            raise ValidationError('Title cannot exceed 200 characters.')

        # Strip any HTML tags for security
        title = strip_tags(title)

        return title

    def clean_content(self):
        """Validate and clean the content field."""
        content = self.cleaned_data.get('content', '').strip()

        if not content:
            raise ValidationError('Content cannot be empty.')

        # Strip HTML for length check
        content_length = len(strip_tags(content))
        if content_length > 10000:  # Reasonable limit
            raise ValidationError('Content cannot exceed 10,000 characters.')

        # Clean content while preserving allowed formatting
        content = clean_rich_text(content)

        return content


class PostCreateForm(forms.Form):
    """Form for creating replies to threads."""

    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control rich-text-editor',
            'rows': 6,
            'placeholder': 'Write your reply...',
            'required': True
        }),
        help_text='Share your thoughts on this discussion. Use the toolbar to format text.'
    )

    def clean_content(self):
        """Validate and clean the content field."""
        content = self.cleaned_data.get('content', '').strip()

        if not content:
            raise ValidationError('Content cannot be empty.')

        # Strip HTML for length check
        content_length = len(strip_tags(content))
        if content_length > 10000:  # Reasonable limit
            raise ValidationError('Content cannot exceed 10,000 characters.')

        # Clean content while preserving allowed formatting
        content = clean_rich_text(content)

        return content


class PreviewForm(forms.Form):
    """Form for AJAX content preview."""
    
    content = forms.CharField(
        widget=forms.Textarea(),
        required=False  # Allow empty for preview
    )
    
    def clean_content(self):
        """Clean content for preview."""
        content = self.cleaned_data.get('content', '').strip()
        
        # Strip HTML tags for security but allow basic formatting
        content = strip_tags(content)
        
        return content


class SearchForm(forms.Form):
    """Form for search functionality."""
    
    CONTENT_TYPE_CHOICES = [
        ('all', 'All Content'),
        ('posts', 'Posts'),
        ('threads', 'Threads'),
        ('users', 'Users'),
        ('categories', 'Categories'),
    ]
    
    SORT_CHOICES = [
        ('relevance', 'Relevance'),
        ('date_desc', 'Newest First'),
        ('date_asc', 'Oldest First'),
        ('author', 'Author Name'),
    ]
    
    query = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search for posts, threads, users...',
            'autocomplete': 'off',
        }),
        help_text='Enter keywords to search for content in the forum.'
    )
    
    content_type = forms.ChoiceField(
        choices=CONTENT_TYPE_CHOICES,
        initial='all',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        help_text='Filter search results by content type.'
    )
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        initial='relevance',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        help_text='Sort search results by preference.'
    )
    
    # Advanced filters
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        help_text='Filter results from this date onwards.'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        help_text='Filter results up to this date.'
    )
    
    author = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by author name...',
            'autocomplete': 'off',
        }),
        help_text='Filter results by author display name or email.'
    )
    
    category = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        help_text='Filter results by category.'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Import here to avoid circular imports
        from .models import Category
        self.fields['category'].queryset = Category.objects.all().order_by('order', 'name')
    
    def clean_query(self):
        """Validate search query."""
        query = self.cleaned_data.get('query')
        
        if not query or not query.strip():
            raise ValidationError('Please enter a search query.')
        
        # Remove extra whitespace
        query = query.strip()
        
        # Check minimum length
        if len(query) < 2:
            raise ValidationError('Search query must be at least 2 characters long.')
        
        # Check maximum length
        if len(query) > 200:
            raise ValidationError('Search query cannot exceed 200 characters.')
        
        # Strip HTML tags for security
        query = strip_tags(query)
        
        return query
    
    def clean_content_type(self):
        """Validate content type filter."""
        content_type = self.cleaned_data.get('content_type')
        
        if content_type and content_type not in dict(self.CONTENT_TYPE_CHOICES):
            raise ValidationError('Invalid content type filter.')
        
        return content_type or 'all'
    
    def clean_sort_by(self):
        """Validate sort option."""
        sort_by = self.cleaned_data.get('sort_by')
        
        if sort_by and sort_by not in dict(self.SORT_CHOICES):
            raise ValidationError('Invalid sort option.')
        
        return sort_by or 'relevance'
    
    def clean(self):
        """Validate date range and other cross-field validation."""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        # Validate date range
        if date_from and date_to and date_from > date_to:
            raise ValidationError('Start date must be before or equal to end date.')
        
        # Validate that dates are not in the future (optional business rule)
        from django.utils import timezone
        today = timezone.now().date()
        
        if date_from and date_from > today:
            raise ValidationError('Start date cannot be in the future.')
        
        if date_to and date_to > today:
            raise ValidationError('End date cannot be in the future.')
        
        return cleaned_data