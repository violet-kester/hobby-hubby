"""
Custom authentication backend for email authentication.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that uses email for authentication
    and allows inactive users to authenticate (so we can check email verification).
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Authenticate using email as username."""
        # username parameter contains email
        email = username
        
        if email is None:
            email = kwargs.get('email')
        
        if email is None or password is None:
            return None
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user.
            User().set_password(password)
            return None
        else:
            if user.check_password(password):
                return user
        
        return None
    
    def get_user(self, user_id):
        """Get user by ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None