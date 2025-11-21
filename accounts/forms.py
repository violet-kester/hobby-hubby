"""
Forms for user registration and authentication.
"""

from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserHobby, Photo, Message


User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    """
    Form for user registration with email verification.
    
    This form extends Django's UserCreationForm to work with our custom
    User model that uses email as the username field.
    """
    
    email = forms.EmailField(
        max_length=254,
        help_text='Required. Enter a valid email address.',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address'
        })
    )
    
    display_name = forms.CharField(
        max_length=50,
        help_text='Required. 50 characters or fewer.',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Display name'
        })
    )
    
    password1 = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        }),
        help_text='Your password must contain at least 8 characters.'
    )
    
    password2 = forms.CharField(
        label='Password confirmation',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        strip=False,
        help_text='Enter the same password as before, for verification.'
    )
    
    class Meta:
        model = User
        fields = ('email', 'display_name')
    
    def clean_email(self):
        """Validate email uniqueness."""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError(
                'A user with this email address already exists.',
                code='duplicate_email'
            )
        return email
    
    def clean_password2(self):
        """Validate password confirmation and strength."""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                'The two password fields didn\'t match.',
                code='password_mismatch'
            )
        
        if password2:
            validate_password(password2)
        
        return password2
    
    def save(self, commit=True):
        """Save the user with email as username."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.display_name = self.cleaned_data['display_name']
        user.is_active = True  # Email verification disabled - users can login immediately
        user.is_email_verified = False  # Track verification status but don't require it

        if commit:
            user.save()

        return user


class EmailLoginForm(forms.Form):
    """
    Custom login form that uses email instead of username.
    """
    
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    error_messages = {
        'invalid_login': 'Invalid email or password.',
        'inactive': 'This account is inactive.',
        'unverified': 'Your email is not verified. Please check your email for the verification link.',
    }
    
    def __init__(self, request=None, *args, **kwargs):
        """Initialize form with request."""
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
    
    def clean(self):
        """Validate and authenticate user."""
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        
        if email is not None and password:
            # Try to authenticate only if we have a request
            if self.request:
                self.user_cache = authenticate(self.request, username=email, password=password)
                
                if self.user_cache is None:
                    # Authentication failed
                    raise ValidationError(
                        self.error_messages['invalid_login'],
                        code='invalid_login',
                    )
                else:
                    # Check if user is active (email verification no longer required)
                    if not self.user_cache.is_active:
                        raise ValidationError(
                            self.error_messages['inactive'],
                            code='inactive',
                        )
        
        return self.cleaned_data
    
    def get_user(self):
        """Return the authenticated user."""
        return self.user_cache


class EmailPasswordResetForm(PasswordResetForm):
    """
    Custom password reset form with Bootstrap styling.
    """
    
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address'
        })
    )


class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile information."""
    
    class Meta:
        model = User
        fields = ['display_name', 'location', 'bio', 'profile_picture']
        widgets = {
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display name'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, Country'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell others about yourself...'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def clean_profile_picture(self):
        """Validate profile picture upload."""
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            # Check file size (limit to 5MB)
            if picture.size > 5 * 1024 * 1024:
                raise ValidationError('Image file too large. Please keep it under 5MB.')
        return picture


class HobbyManagementForm(forms.Form):
    """Form for managing user hobbies."""
    
    def __init__(self, user, *args, **kwargs):
        """Initialize form with user's current hobbies."""
        self.user = user
        super().__init__(*args, **kwargs)
        
        # Import here to avoid circular imports
        from forums.models import Subcategory
        
        # Get all subcategories for hobby selection
        subcategories = Subcategory.objects.select_related('category').all()
        choices = [(sub.id, f"{sub.category.name} - {sub.name}") for sub in subcategories]
        
        # Get user's current hobbies
        current_hobbies = UserHobby.objects.filter(user=user).values_list('subcategory_id', flat=True)
        
        self.fields['subcategories'] = forms.MultipleChoiceField(
            choices=choices,
            initial=list(current_hobbies),
            widget=forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            required=False,
            help_text='Select the topics you are interested in.'
        )
    
    def save(self):
        """Save the user's hobby selections."""
        selected_subcategory_ids = [int(id) for id in self.cleaned_data['subcategories']]
        
        # Remove hobbies that are no longer selected
        UserHobby.objects.filter(user=self.user).exclude(
            subcategory_id__in=selected_subcategory_ids
        ).delete()
        
        # Add new hobbies
        existing_hobby_ids = set(
            UserHobby.objects.filter(user=self.user).values_list('subcategory_id', flat=True)
        )
        
        new_hobbies = []
        for subcategory_id in selected_subcategory_ids:
            if subcategory_id not in existing_hobby_ids:
                from forums.models import Subcategory
                subcategory = Subcategory.objects.get(id=subcategory_id)
                new_hobbies.append(UserHobby(user=self.user, subcategory=subcategory))
        
        if new_hobbies:
            UserHobby.objects.bulk_create(new_hobbies)


class PhotoUploadForm(forms.ModelForm):
    """Form for uploading photos to user galleries."""
    
    class Meta:
        model = Photo
        fields = ['image', 'caption']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional caption for your photo...'
            })
        }
    
    def clean_image(self):
        """Validate image upload."""
        image = self.cleaned_data.get('image')
        if image:
            # Check file size (limit to 10MB)
            if image.size > 10 * 1024 * 1024:
                raise ValidationError('Image file too large. Please keep it under 10MB.')
            
            # Check file format
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if hasattr(image, 'content_type') and image.content_type not in allowed_types:
                raise ValidationError('Unsupported image format. Please use JPG, PNG, GIF, or WebP.')
        
        return image


class MessageForm(forms.ModelForm):
    """Form for composing and sending messages."""
    
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Type your message here...',
                'required': True
            })
        }
    
    def clean_content(self):
        """Validate message content."""
        content = self.cleaned_data.get('content')
        if not content or not content.strip():
            raise ValidationError('Message content cannot be empty.')
        
        # Check message length (reasonable limit)
        if len(content) > 5000:
            raise ValidationError('Message is too long. Please keep it under 5000 characters.')
        
        return content.strip()