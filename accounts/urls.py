"""
URL patterns for accounts app.
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


app_name = 'accounts'

urlpatterns = [
    # Registration
    path('register/', views.RegisterView.as_view(), name='register'),
    path('registration-success/', views.RegistrationSuccessView.as_view(), name='registration_success'),
    path('verify/<str:uidb64>/<str:token>/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('verification-complete/', views.VerificationCompleteView.as_view(), name='verification_complete'),
    
    # Authentication
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Password Reset
    path('password/reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),  # Redirects to user's own profile view
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('user/<int:user_id>/', views.user_profile_view, name='user_profile'),
    path('user/<int:user_id>/posts/', views.UserPostsView.as_view(), name='user_posts'),
    path('hobbies/', views.manage_hobbies_view, name='manage_hobbies'),
    path('bookmarks/', views.UserBookmarksView.as_view(), name='bookmarks'),
    
    # Photo Gallery
    path('photos/upload/', views.upload_photo_view, name='upload_photo'),
    path('photos/', views.all_photos_gallery_view, name='gallery_all'),
    path('photos/<int:user_id>/', views.photo_gallery_view, name='photo_gallery'),
    path('photos/delete/<int:photo_id>/', views.delete_photo_view, name='delete_photo'),
    
    # Hubby System
    path('hubbies/send/<int:user_id>/', views.send_friend_request_view, name='send_hubby_request'),
    path('hubbies/respond/<int:friendship_id>/<str:action>/', views.respond_friend_request_view, name='respond_hubby_request'),
    path('hubbies/requests/', views.friend_requests_view, name='hubby_requests'),
    path('hubbies/<int:user_id>/', views.friends_list_view, name='hubbies_list'),
    
    # Messaging System
    path('inbox/', views.inbox_view, name='inbox'),
    path('conversation/<int:conversation_id>/', views.conversation_detail_view, name='conversation_detail'),
    path('conversation/<int:conversation_id>/send/', views.send_message_view, name='send_message'),
    path('message/<int:user_id>/', views.start_conversation_view, name='start_conversation'),
]