from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import CreateView, TemplateView, FormView, View, ListView
from django.contrib import messages
from django.conf import settings

from .forms import UserRegistrationForm, EmailLoginForm, EmailPasswordResetForm, ProfileEditForm, HobbyManagementForm, PhotoUploadForm, MessageForm


User = get_user_model()


class RegisterView(CreateView):
    """
    View for user registration.
    
    Creates an inactive user and sends email verification.
    """
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    
    def form_valid(self, form):
        """Process valid form and send verification email."""
        user = form.save()
        
        # Send verification email
        self.send_verification_email(user)
        
        messages.success(
            self.request,
            'Registration successful! Please check your email to verify your account.'
        )
        
        return redirect('accounts:registration_success')
    
    def send_verification_email(self, user):
        """Send email verification email to user."""
        current_site = get_current_site(self.request)
        
        # Generate verification token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create verification URL
        verification_url = self.request.build_absolute_uri(
            reverse('accounts:verify_email', kwargs={'uidb64': uid, 'token': token})
        )
        
        # Email content
        subject = f'Verify your email for {current_site.name}'
        message = render_to_string('accounts/verification_email.txt', {
            'user': user,
            'domain': current_site.domain,
            'site_name': current_site.name,
            'verification_url': verification_url,
            'protocol': 'https' if self.request.is_secure() else 'http',
        })
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )


class VerifyEmailView(TemplateView):
    """
    View for email verification.
    
    Activates user account when valid token is provided.
    """
    template_name = 'accounts/verification_invalid.html'
    
    def get(self, request, uidb64, token):
        """Process email verification request."""
        try:
            # Decode user ID
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        
        if user is not None and default_token_generator.check_token(user, token):
            if user.is_email_verified:
                # User already verified
                messages.info(request, 'Your email is already verified.')
                return redirect('accounts:verification_complete')
            else:
                # Activate user
                user.is_active = True
                user.is_email_verified = True
                user.save()
                
                messages.success(request, 'Your email has been verified successfully!')
                return redirect('accounts:verification_complete')
        else:
            # Invalid token
            messages.error(request, 'The verification link is invalid or has expired.')
            return render(request, self.template_name)


class RegistrationSuccessView(TemplateView):
    """View shown after successful registration."""
    template_name = 'accounts/registration_success.html'


class VerificationCompleteView(TemplateView):
    """View shown after successful email verification."""
    template_name = 'accounts/verification_complete.html'


class LoginView(FormView):
    """
    Custom login view using email authentication.
    """
    template_name = 'accounts/login.html'
    form_class = EmailLoginForm
    success_url = '/'
    
    def get_form_kwargs(self):
        """Pass request to form."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        """Log in the user."""
        user = form.get_user()
        login(self.request, user)
        
        # Handle remember me
        if form.cleaned_data.get('remember_me'):
            # Session expires in 2 weeks
            self.request.session.set_expiry(1209600)
        else:
            # Session expires on browser close
            self.request.session.set_expiry(0)
        
        messages.success(self.request, f'Welcome back, {user.display_name}!')
        
        # Redirect to next URL if provided
        next_url = self.request.GET.get('next')
        if next_url:
            return redirect(next_url)
        
        return super().form_valid(form)


class LogoutView(View):
    """
    Custom logout view.
    """
    
    def post(self, request):
        """Log out the user."""
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('/')


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view with Bootstrap form."""
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.txt'
    form_class = EmailPasswordResetForm
    success_url = reverse_lazy('accounts:password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Custom password reset done view."""
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view."""
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Custom password reset complete view."""
    template_name = 'accounts/password_reset_complete.html'


def user_profile_view(request, user_id):
    """Enhanced user profile view with post counts, hobbies, and more."""
    from forums.models import Post
    from .models import UserHobby
    
    # Get the user being viewed
    profile_user = get_object_or_404(User, id=user_id)
    
    # Get user's post count
    post_count = Post.objects.filter(author=profile_user).count()
    
    # Get user's hobbies
    hobbies = UserHobby.objects.filter(user=profile_user).select_related(
        'subcategory__category'
    ).order_by('-joined_at')
    
    # Get user's friend count
    from .models import Friendship
    from django.db.models import Q
    friend_count = Friendship.objects.filter(
        Q(from_user=profile_user, status='accepted') |
        Q(to_user=profile_user, status='accepted')
    ).count()
    
    # Check if this is the user's own profile
    is_own_profile = request.user.is_authenticated and request.user == profile_user
    
    # Get friendship status
    friendship_status = get_friendship_status(request.user, profile_user)
    friendship_request = None
    
    # Get the actual friendship object if there's a received request
    if friendship_status == 'request_received':
        from .models import Friendship
        friendship_request = Friendship.objects.filter(
            from_user=profile_user,
            to_user=request.user,
            status='pending'
        ).first()
    
    context = {
        'profile_user': profile_user,
        'post_count': post_count,
        'hobbies': hobbies,
        'friend_count': friend_count,
        'is_own_profile': is_own_profile,
        'friendship_status': friendship_status,
        'friendship_request': friendship_request,
    }
    
    return render(request, 'accounts/user_profile.html', context)


@login_required
def profile_view(request):
    """Redirect to user's own profile view."""
    return redirect('accounts:user_profile', user_id=request.user.id)


@login_required
def profile_edit_view(request):
    """Profile edit view."""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:user_profile', user_id=request.user.id)
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def manage_hobbies_view(request):
    """Hobby management view with organized categories."""
    from forums.models import Category, Subcategory
    from .models import UserHobby

    if request.method == 'POST':
        form = HobbyManagementForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your hobbies have been updated successfully!')
            return redirect('accounts:user_profile', user_id=request.user.id)
    else:
        form = HobbyManagementForm(request.user)

    # Get categories with their subcategories organized
    categories_with_subs = Category.objects.prefetch_related('subcategories').order_by('name')

    # Get user's current hobby subcategories
    user_hobbies = set(UserHobby.objects.filter(user=request.user).values_list('subcategory_id', flat=True))

    context = {
        'form': form,
        'categories_with_subs': categories_with_subs,
        'user_hobbies': user_hobbies,
    }

    return render(request, 'accounts/manage_hobbies.html', context)


class UserBookmarksView(LoginRequiredMixin, ListView):
    """View for displaying user's bookmarked threads."""
    template_name = 'accounts/bookmarks.html'
    context_object_name = 'bookmarks'
    paginate_by = 20
    
    def get_queryset(self):
        """Get bookmarks for the current user."""
        from forums.models import Bookmark
        return Bookmark.objects.filter(
            user=self.request.user
        ).select_related(
            'thread__subcategory__category',
            'thread__author'
        ).order_by('-created_at')


@login_required
def upload_photo_view(request):
    """Photo upload view."""
    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.user = request.user
            photo.save()
            messages.success(request, 'Your photo has been uploaded successfully!')
            return redirect('accounts:photo_gallery', user_id=request.user.id)
    else:
        form = PhotoUploadForm()
    
    return render(request, 'accounts/upload_photo.html', {'form': form})


def photo_gallery_view(request, user_id):
    """Photo gallery view for a specific user."""
    from .models import Photo
    
    # Get the user whose gallery we're viewing
    gallery_user = get_object_or_404(User, id=user_id)
    
    # Get user's photos
    photos = Photo.objects.filter(user=gallery_user).order_by('-created_at')
    
    # Paginate photos (20 per page)
    paginator = Paginator(photos, 20)
    page_number = request.GET.get('page')
    page_photos = paginator.get_page(page_number)
    
    # Check if this is the user's own gallery
    is_own_gallery = request.user.is_authenticated and request.user == gallery_user
    
    context = {
        'gallery_user': gallery_user,
        'photos': page_photos,
        'is_own_gallery': is_own_gallery,
        'photo_count': photos.count(),
    }
    
    return render(request, 'accounts/photo_gallery.html', context)


@login_required
def delete_photo_view(request, photo_id):
    """Delete photo view."""
    from .models import Photo
    
    photo = get_object_or_404(Photo, id=photo_id)
    
    # Check if user owns this photo
    if photo.user != request.user:
        return redirect('accounts:photo_gallery', user_id=photo.user.id)
    
    if request.method == 'POST':
        photo.delete()
        messages.success(request, 'Photo deleted successfully!')
        return redirect('accounts:photo_gallery', user_id=request.user.id)
    
    return render(request, 'accounts/delete_photo.html', {'photo': photo})


@login_required
def send_friend_request_view(request, user_id):
    """Send a friend request to another user."""
    from .models import Friendship
    from django.utils import timezone
    
    if request.method != 'POST':
        return redirect('accounts:user_profile', user_id=user_id)
    
    # Get the target user
    target_user = get_object_or_404(User, id=user_id)
    
    # Check if user is trying to friend themselves
    if request.user == target_user:
        messages.error(request, "You cannot send a friend request to yourself.")
        return redirect('accounts:user_profile', user_id=user_id)
    
    # Check if there's already a pending or accepted friendship
    existing_friendship = Friendship.objects.filter(
        from_user=request.user,
        to_user=target_user
    ).order_by('-created_at').first()
    
    if existing_friendship:
        if existing_friendship.status == 'pending':
            messages.warning(request, f"You already have a pending friend request to {target_user.display_name}.")
            return redirect('accounts:user_profile', user_id=user_id)
        elif existing_friendship.status == 'accepted':
            messages.info(request, f"You are already friends with {target_user.display_name}.")
            return redirect('accounts:user_profile', user_id=user_id)
        elif existing_friendship.status == 'rejected':
            # Update the existing rejected friendship to pending
            existing_friendship.status = 'pending'
            existing_friendship.responded_at = None
            existing_friendship.save()
            messages.success(request, f"Friend request sent to {target_user.display_name}!")
            return redirect('accounts:user_profile', user_id=user_id)
    
    # Create a new friend request
    try:
        Friendship.objects.create(
            from_user=request.user,
            to_user=target_user,
            status='pending'
        )
        messages.success(request, f"Friend request sent to {target_user.display_name}!")
    except Exception as e:
        messages.error(request, "Unable to send friend request. Please try again.")
    
    return redirect('accounts:user_profile', user_id=user_id)


@login_required
def respond_friend_request_view(request, friendship_id, action):
    """Respond to a friend request (accept or reject)."""
    from .models import Friendship
    from django.utils import timezone
    
    if request.method != 'POST':
        return redirect('accounts:friend_requests')
    
    # Get the friendship request
    friendship = get_object_or_404(Friendship, id=friendship_id)
    
    # Check if current user is the recipient
    if request.user != friendship.to_user:
        messages.error(request, "You can only respond to friend requests sent to you.")
        return redirect('accounts:friend_requests')
    
    # Check if request is still pending
    if friendship.status != 'pending':
        messages.warning(request, "This friend request has already been responded to.")
        return redirect('accounts:friend_requests')
    
    # Process the response
    if action == 'accept':
        friendship.status = 'accepted'
        friendship.responded_at = timezone.now()
        friendship.save()
        messages.success(request, f"You are now friends with {friendship.from_user.display_name}!")
    elif action == 'reject':
        friendship.status = 'rejected'
        friendship.responded_at = timezone.now()
        friendship.save()
        messages.info(request, f"Friend request from {friendship.from_user.display_name} has been rejected.")
    else:
        messages.error(request, "Invalid action.")
    
    return redirect('accounts:friend_requests')


@login_required
def friend_requests_view(request):
    """View for displaying incoming friend requests."""
    from .models import Friendship
    
    # Get incoming pending friend requests
    incoming_requests = Friendship.objects.filter(
        to_user=request.user,
        status='pending'
    ).select_related('from_user').order_by('-created_at')
    
    # Paginate requests (10 per page)
    paginator = Paginator(incoming_requests, 10)
    page_number = request.GET.get('page')
    page_requests = paginator.get_page(page_number)
    
    context = {
        'friend_requests': page_requests,
        'request_count': incoming_requests.count(),
    }
    
    return render(request, 'accounts/friend_requests.html', context)


def friends_list_view(request, user_id):
    """View for displaying a user's friends."""
    from .models import Friendship
    from django.db.models import Q
    
    # Get the user whose friends we're viewing
    profile_user = get_object_or_404(User, id=user_id)
    
    # Get accepted friendships (bidirectional)
    friends_query = Friendship.objects.filter(
        Q(from_user=profile_user, status='accepted') |
        Q(to_user=profile_user, status='accepted')
    ).select_related('from_user', 'to_user').order_by('-responded_at')
    
    # Extract the friend users (not the profile_user themselves)
    friends = []
    for friendship in friends_query:
        if friendship.from_user == profile_user:
            friends.append({
                'user': friendship.to_user,
                'friendship_date': friendship.responded_at,
                'friendship': friendship
            })
        else:
            friends.append({
                'user': friendship.from_user,
                'friendship_date': friendship.responded_at,
                'friendship': friendship
            })
    
    # Paginate friends (20 per page)
    paginator = Paginator(friends, 20)
    page_number = request.GET.get('page')
    page_friends = paginator.get_page(page_number)
    
    context = {
        'profile_user': profile_user,
        'friends': page_friends,
        'friend_count': len(friends),
        'is_own_friends_list': request.user.is_authenticated and request.user == profile_user,
    }
    
    return render(request, 'accounts/friends_list.html', context)


def get_friendship_status(current_user, target_user):
    """Helper function to get friendship status between two users."""
    if not current_user.is_authenticated or current_user == target_user:
        return None
    
    from .models import Friendship
    
    # Check for friendship from current_user to target_user
    sent_request = Friendship.objects.filter(
        from_user=current_user,
        to_user=target_user
    ).first()
    
    # Check for friendship from target_user to current_user
    received_request = Friendship.objects.filter(
        from_user=target_user,
        to_user=current_user
    ).first()
    
    # Determine status
    if sent_request:
        if sent_request.status == 'accepted':
            return 'friends'
        elif sent_request.status == 'pending':
            return 'request_sent'
        elif sent_request.status == 'rejected':
            return 'can_send_request'
    
    if received_request:
        if received_request.status == 'accepted':
            return 'friends'
        elif received_request.status == 'pending':
            return 'request_received'
        elif received_request.status == 'rejected':
            return 'can_send_request'
    
    return 'can_send_request'


@login_required
def inbox_view(request):
    """View for displaying user's message inbox."""
    from .models import Conversation, ConversationParticipant
    from django.db.models import Q, Count, Max
    
    # Get conversations where user is a participant
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        unread_count=Count(
            'message_set',
            filter=Q(
                message_set__sender__isnull=False
            )
        )
    ).select_related().prefetch_related('participants').order_by('-last_message_at', '-created_at')
    
    # Filter out conversations with no messages
    conversations = conversations.filter(last_message_at__isnull=False)
    
    # Paginate conversations (20 per page)
    paginator = Paginator(conversations, 20)
    page_number = request.GET.get('page')
    page_conversations = paginator.get_page(page_number)
    
    context = {
        'conversations': page_conversations,
        'conversation_count': conversations.count(),
    }
    
    return render(request, 'accounts/inbox.html', context)


@login_required
def conversation_detail_view(request, conversation_id):
    """View for displaying a specific conversation."""
    from .models import Conversation, ConversationParticipant
    from django.utils import timezone
    from django.http import HttpResponseForbidden
    
    # Get conversation and check user is participant
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check if user is a participant
    if not conversation.participants.filter(id=request.user.id).exists():
        return HttpResponseForbidden("You are not a participant in this conversation.")
    
    # Get messages with pagination (20 per page)
    messages_list = conversation.message_set.select_related('sender').order_by('sent_at')
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get('page')
    page_messages = paginator.get_page(page_number)
    
    # Update user's last_read_at
    participant, created = ConversationParticipant.objects.get_or_create(
        conversation=conversation,
        user=request.user
    )
    participant.last_read_at = timezone.now()
    participant.save()
    
    # Get other participant for display
    other_participant = conversation.get_other_participant(request.user)
    
    context = {
        'conversation': conversation,
        'messages': page_messages,
        'other_participant': other_participant,
        'message_count': messages_list.count(),
    }
    
    return render(request, 'accounts/conversation_detail.html', context)


@login_required
def send_message_view(request, conversation_id):
    """View for sending a message to a conversation."""
    from .models import Conversation, Message
    from .forms import MessageForm
    from django.http import HttpResponseForbidden
    
    if request.method != 'POST':
        return redirect('accounts:conversation_detail', conversation_id=conversation_id)
    
    # Get conversation and check user is participant
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check if user is a participant
    if not conversation.participants.filter(id=request.user.id).exists():
        return HttpResponseForbidden("You are not a participant in this conversation.")
    
    form = MessageForm(request.POST)
    if form.is_valid():
        message = form.save(commit=False)
        message.conversation = conversation
        message.sender = request.user
        message.save()
        
        messages.success(request, 'Message sent successfully!')
        return redirect('accounts:conversation_detail', conversation_id=conversation_id)
    else:
        for error in form.errors.values():
            messages.error(request, error[0])
        return redirect('accounts:conversation_detail', conversation_id=conversation_id)


@login_required
def start_conversation_view(request, user_id):
    """View for starting a new conversation with a user."""
    from .models import Conversation, ConversationParticipant, Message
    from .forms import MessageForm
    from django.db.models import Q
    from django.http import HttpResponseBadRequest
    
    # Get target user
    target_user = get_object_or_404(User, id=user_id)
    
    # Check user is not trying to message themselves
    if request.user == target_user:
        return HttpResponseBadRequest("You cannot start a conversation with yourself.")
    
    # Check if conversation already exists between these users
    from django.db.models import Count
    existing_conversation = Conversation.objects.annotate(
        participant_count=Count('participants')
    ).filter(
        participants=request.user
    ).filter(
        participants=target_user
    ).filter(
        participant_count=2
    ).first()
    
    if existing_conversation:
        return redirect('accounts:conversation_detail', conversation_id=existing_conversation.id)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            # Create new conversation
            conversation = Conversation.objects.create()
            
            # Add participants
            ConversationParticipant.objects.create(
                conversation=conversation,
                user=request.user
            )
            ConversationParticipant.objects.create(
                conversation=conversation,
                user=target_user
            )
            
            # Create first message
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            
            messages.success(request, f'Conversation started with {target_user.display_name}!')
            return redirect('accounts:conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()
    
    context = {
        'target_user': target_user,
        'form': form,
    }
    
    return render(request, 'accounts/start_conversation.html', context)
