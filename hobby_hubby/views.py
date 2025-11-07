"""
Views for the main hobby_hubby project.
"""

from django.shortcuts import render
from accounts.models import Photo
from forums.models import Thread, Post


def home(request):
    """Home page view showing recent photos and discussions."""
    # Get recent photos (last 8)
    recent_photos = Photo.objects.select_related('user').order_by('-created_at')[:8]

    # Get most recent posts from forums (last 12) - focus on text discussions
    recent_posts = Post.objects.select_related(
        'author', 'thread__subcategory__category'
    ).order_by('-created_at')[:12]

    context = {
        'recent_photos': recent_photos,
        'recent_posts': recent_posts,
    }

    return render(request, 'home.html', context)