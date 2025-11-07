import time
import hashlib
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import linebreaks
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Count, Avg, Sum, Q, F
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache

logger = logging.getLogger(__name__)
from django.views.decorators.cache import cache_page
from django.db import connection
from .models import Category, Subcategory, Thread, Post, Vote, Bookmark, SearchHistory, SavedSearch, SearchAnalytics
from .forms import ThreadCreateForm, PostCreateForm, PreviewForm, SearchForm

# Import PostgreSQL search features if available
try:
    from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
    POSTGRES_SEARCH_AVAILABLE = True
except ImportError:
    POSTGRES_SEARCH_AVAILABLE = False

User = get_user_model()


class CategoryListView(ListView):
    """Display all categories with their subcategories."""
    model = Category
    template_name = 'forums/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.prefetch_related('subcategories').all()


class SubcategoryDetailView(DetailView):
    """Display threads within a subcategory."""
    model = Subcategory
    template_name = 'forums/subcategory_detail.html'
    context_object_name = 'subcategory'
    paginate_by = 20
    
    def get_object(self):
        return get_object_or_404(
            Subcategory.objects.select_related('category'),
            category__slug=self.kwargs['category_slug'],
            slug=self.kwargs['subcategory_slug']
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get threads for this subcategory
        threads = Thread.objects.filter(
            subcategory=self.object
        ).select_related('author').order_by('-is_pinned', '-last_post_at')
        
        # Paginate threads
        paginator = Paginator(threads, self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['threads'] = page_obj
        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        
        # Add user bookmark information for threads
        if self.request.user.is_authenticated:
            # Get thread IDs that the user has bookmarked
            user_bookmarked_thread_ids = Bookmark.objects.filter(
                user=self.request.user,
                thread__in=page_obj
            ).values_list('thread_id', flat=True)
            context['user_bookmarked_threads'] = set(user_bookmarked_thread_ids)
        else:
            context['user_bookmarked_threads'] = set()
        
        return context


class ThreadDetailView(DetailView):
    """Display posts within a thread."""
    model = Thread
    template_name = 'forums/thread_detail.html'
    context_object_name = 'thread'
    paginate_by = 10
    
    def get_object(self):
        thread = get_object_or_404(
            Thread.objects.select_related('subcategory__category', 'author'),
            subcategory__category__slug=self.kwargs['category_slug'],
            subcategory__slug=self.kwargs['subcategory_slug'],
            slug=self.kwargs['thread_slug']
        )
        
        # Increment view count
        Thread.objects.filter(pk=thread.pk).update(view_count=F('view_count') + 1)
        # Refresh the object to get updated view count
        thread.refresh_from_db()
        
        return thread
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get posts for this thread
        posts = Post.objects.filter(
            thread=self.object
        ).select_related('author').order_by('created_at')
        
        # Paginate posts
        paginator = Paginator(posts, self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['posts'] = page_obj
        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        
        # Add user vote information
        if self.request.user.is_authenticated:
            # Get post IDs that the user has voted on
            user_voted_post_ids = Vote.objects.filter(
                user=self.request.user,
                post__in=page_obj
            ).values_list('post_id', flat=True)
            context['user_voted_posts'] = set(user_voted_post_ids)
            
            # Check if user has bookmarked this thread
            context['user_bookmarked'] = Bookmark.objects.filter(
                user=self.request.user,
                thread=self.object
            ).exists()
        else:
            context['user_voted_posts'] = set()
            context['user_bookmarked'] = False
        
        return context


@login_required
def thread_create(request, category_slug, subcategory_slug):
    """View for creating new threads."""
    # Get the subcategory
    subcategory = get_object_or_404(
        Subcategory.objects.select_related('category'),
        category__slug=category_slug,
        slug=subcategory_slug
    )
    
    if request.method == 'POST':
        form = ThreadCreateForm(request.POST)
        if form.is_valid():
            # Create the thread
            thread = Thread.objects.create(
                title=form.cleaned_data['title'],
                subcategory=subcategory,
                author=request.user
            )
            
            # Create the initial post
            Post.objects.create(
                content=form.cleaned_data['content'],
                thread=thread,
                author=request.user
            )
            
            # Add success message
            messages.success(
                request,
                f'Thread "{thread.title}" created successfully!'
            )
            
            # Redirect to the new thread
            return redirect('forums:thread_detail', 
                           category_slug=subcategory.category.slug,
                           subcategory_slug=subcategory.slug,
                           thread_slug=thread.slug)
    else:
        form = ThreadCreateForm()
    
    return render(request, 'forums/thread_create.html', {
        'form': form,
        'subcategory': subcategory
    })


@login_required
def post_create(request, category_slug, subcategory_slug, thread_slug):
    """View for creating replies to threads."""
    # Get the thread
    thread = get_object_or_404(
        Thread.objects.select_related('subcategory__category', 'author'),
        subcategory__category__slug=category_slug,
        subcategory__slug=subcategory_slug,
        slug=thread_slug
    )

    # Check if thread is locked
    if thread.is_locked:
        return HttpResponseForbidden('This thread is locked and no longer accepts replies.')

    if request.method == 'POST':
        form = PostCreateForm(request.POST)

        if form.is_valid():
            content = form.cleaned_data['content']

            # Create the post
            post = Post.objects.create(
                content=content,
                thread=thread,
                author=request.user
            )

            # Add success message
            messages.success(
                request,
                'Reply posted successfully!'
            )

            # Redirect to the thread with anchor to new post
            thread_url = reverse('forums:thread_detail',
                               kwargs={'category_slug': thread.subcategory.category.slug,
                                      'subcategory_slug': thread.subcategory.slug,
                                      'thread_slug': thread.slug})
            redirect_url = f"{thread_url}#post-{post.id}"
            return redirect(redirect_url)
    else:
        form = PostCreateForm()

    return render(request, 'forums/post_create.html', {
        'form': form,
        'thread': thread
    })


@login_required
def preview_content(request):
    """AJAX view for previewing content before posting."""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return HttpResponseBadRequest('AJAX request required')

    if request.method != 'POST':
        return HttpResponseBadRequest('POST request required')

    form = PreviewForm(request.POST)

    if not form.is_valid():
        return JsonResponse({'error': 'Content is required for preview'}, status=400)

    content = form.cleaned_data['content']

    if not content.strip():
        return JsonResponse({'error': 'Content cannot be empty'}, status=400)

    # Convert content to HTML (basic linebreaks for now)
    # Later this can be enhanced with markdown support
    html_content = linebreaks(content)

    return JsonResponse({
        'html': html_content
    })


@login_required
def vote_post(request, post_id):
    """AJAX view for voting on posts."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return HttpResponseBadRequest('AJAX request required')
    
    # Get the post
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user is trying to vote on their own post
    if post.author == request.user:
        return JsonResponse({
            'error': 'You cannot vote on your own post'
        }, status=400)
    
    # Check if user has already voted on this post
    vote, created = Vote.objects.get_or_create(
        user=request.user,
        post=post
    )
    
    if created:
        # User just voted
        voted = True
    else:
        # User already voted, so remove the vote
        vote.delete()
        voted = False
    
    # Get updated vote count
    post.refresh_from_db()
    vote_count = post.vote_count
    
    return JsonResponse({
        'voted': voted,
        'vote_count': vote_count
    })


@login_required
def bookmark_thread(request, thread_id):
    """AJAX view for bookmarking threads."""
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'POST method required', 'success': False}, status=405)

        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'AJAX request required', 'success': False}, status=400)

        # Get the thread
        thread = get_object_or_404(Thread, id=thread_id)

        # Check if user has already bookmarked this thread
        bookmark, created = Bookmark.objects.get_or_create(
            user=request.user,
            thread=thread
        )

        if created:
            # User just bookmarked
            bookmarked = True
        else:
            # User already bookmarked, so remove the bookmark
            bookmark.delete()
            bookmarked = False

        # Get updated bookmark count
        bookmark_count = Bookmark.objects.filter(user=request.user).count()

        response_data = {
            'bookmarked': bookmarked,
            'bookmark_count': bookmark_count,
            'thread_id': thread.id,
            'success': True
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({
            'error': 'An error occurred while processing your request.',
            'success': False
        }, status=500)


def search_view(request):
    """Search view for forum content."""
    form = SearchForm(request.GET or None)
    results = []
    query = ''
    content_type = 'all'
    sort_by = 'relevance'
    total_results = 0
    
    if form.is_valid():
        query = form.cleaned_data['query']
        content_type = form.cleaned_data['content_type']
        sort_by = form.cleaned_data['sort_by']
        
        # Extract advanced filters
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        author_filter = form.cleaned_data.get('author')
        category_filter = form.cleaned_data.get('category')
        
        # Build filter parameters
        filters = {
            'date_from': date_from,
            'date_to': date_to,
            'author': author_filter,
            'category': category_filter,
        }
        
        # Start timing for analytics
        start_time = time.time()
        database_hits = 0
        
        # Perform search based on content type with filters
        if content_type == 'all':
            results = perform_unified_search(query, sort_by, filters)
            database_hits = 5  # Unified search hits multiple tables
        elif content_type == 'posts':
            results = search_posts(query, sort_by, filters)
            database_hits = 2  # Posts and related joins
        elif content_type == 'threads':
            results = search_threads(query, sort_by, filters)
            database_hits = 2  # Threads and related joins
        elif content_type == 'users':
            results = search_users(query, sort_by, filters)
            database_hits = 1  # Users table only
        elif content_type == 'categories':
            results = search_categories(query, sort_by, filters)
            database_hits = 2  # Categories and subcategories
        
        # Calculate search time
        search_time_ms = int((time.time() - start_time) * 1000)
        total_results = len(results)
        
        # Record search analytics (all searches)
        if query.strip():  # Only record non-empty queries
            SearchAnalytics.record_search_analytics(
                request=request,
                query=query,
                content_type=content_type,
                sort_by=sort_by,
                results_count=total_results,
                search_time_ms=search_time_ms,
                database_hits=database_hits
            )
            
            # Record search in history for authenticated users
            SearchHistory.record_search(
                user=request.user,
                query=query,
                content_type=content_type,
                results_count=total_results
            )
    
    # Paginate results
    paginator = Paginator(results, 20)  # 20 results per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get recent searches for authenticated users
    recent_searches = []
    saved_searches = []
    if request.user.is_authenticated:
        recent_searches = SearchHistory.get_user_recent_searches(request.user, limit=5)
        saved_searches = SavedSearch.get_user_saved_searches(request.user)
    
    context = {
        'form': form,
        'results': page_obj,
        'query': query,
        'content_type': content_type,
        'sort_by': sort_by,
        'total_results': total_results,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'recent_searches': recent_searches,
        'saved_searches': saved_searches,
    }
    
    return render(request, 'forums/search_results.html', context)


def perform_unified_search(query, sort_by='relevance', filters=None):
    """Perform unified search across all content types."""
    results = []
    filters = filters or {}
    
    if POSTGRES_SEARCH_AVAILABLE and 'postgresql' in settings.DATABASES['default']['ENGINE']:
        # Use PostgreSQL full-text search
        results = perform_postgres_unified_search(query, sort_by, filters)
    else:
        # Use SQLite-compatible search
        results = perform_sqlite_unified_search(query, sort_by, filters)
    
    return results


def apply_search_filters(queryset, filters):
    """Apply common search filters to a queryset."""
    date_from = filters.get('date_from')
    date_to = filters.get('date_to')
    author_filter = filters.get('author')
    category_filter = filters.get('category')
    
    # Apply date filters
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    
    if date_to:
        # Add one day to include the entire end date
        from datetime import timedelta
        end_date = date_to + timedelta(days=1)
        queryset = queryset.filter(created_at__date__lt=end_date)
    
    # Apply author filter
    if author_filter and hasattr(queryset.model, 'author'):
        author_q = Q(author__display_name__icontains=author_filter) | Q(author__email__icontains=author_filter)
        queryset = queryset.filter(author_q)
    
    # Apply category filter for content with categories
    if category_filter:
        model = queryset.model
        if hasattr(model, 'subcategory'):  # Posts, Threads
            queryset = queryset.filter(subcategory__category=category_filter)
        elif hasattr(model, 'category'):  # Subcategories
            queryset = queryset.filter(category=category_filter)
    
    return queryset


def perform_postgres_unified_search(query, sort_by='relevance', filters=None):
    """Perform PostgreSQL full-text search across all content types."""
    # Create search query and vector
    search_query = SearchQuery(query)
    filters = filters or {}
    
    results = []
    
    # Search posts
    post_vector = SearchVector('content')
    posts = Post.objects.annotate(
        search=post_vector,
        rank=SearchRank(post_vector, search_query)
    ).filter(
        search=search_query
    ).select_related('author', 'thread__subcategory__category')
    
    # Apply filters to posts
    posts = apply_search_filters(posts, filters)
    
    for post in posts:
        results.append({
            'type': 'post',
            'title': f'Post in "{post.thread.title}"',
            'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
            'author': post.author,
            'date': post.created_at,
            'url': f"/forums/{post.thread.subcategory.category.slug}/{post.thread.subcategory.slug}/{post.thread.slug}/#post-{post.id}",
            'rank': post.rank,
            'category': post.thread.subcategory.category.name,
            'subcategory': post.thread.subcategory.name,
        })
    
    # Search threads
    thread_vector = SearchVector('title')
    threads = Thread.objects.annotate(
        search=thread_vector,
        rank=SearchRank(thread_vector, search_query)
    ).filter(
        search=search_query
    ).select_related('author', 'subcategory__category')
    
    # Apply filters to threads
    threads = apply_search_filters(threads, filters)
    
    for thread in threads:
        results.append({
            'type': 'thread',
            'title': thread.title,
            'content': f'Thread in {thread.subcategory.name}',
            'author': thread.author,
            'date': thread.created_at,
            'url': f"/forums/{thread.subcategory.category.slug}/{thread.subcategory.slug}/{thread.slug}/",
            'rank': thread.rank,
            'category': thread.subcategory.category.name,
            'subcategory': thread.subcategory.name,
        })
    
    # Search users
    user_vector = SearchVector('display_name', 'bio', 'location')
    users = User.objects.annotate(
        search=user_vector,
        rank=SearchRank(user_vector, search_query)
    ).filter(
        Q(search=search_query) & Q(is_active=True)
    )
    
    # Apply date filters to users (by date_joined instead of created_at)
    if filters.get('date_from'):
        users = users.filter(date_joined__date__gte=filters['date_from'])
    if filters.get('date_to'):
        from datetime import timedelta
        end_date = filters['date_to'] + timedelta(days=1)
        users = users.filter(date_joined__date__lt=end_date)
    
    # Apply author filter to users (search in display_name and email)
    if filters.get('author'):
        author_q = Q(display_name__icontains=filters['author']) | Q(email__icontains=filters['author'])
        users = users.filter(author_q)
    
    for user in users:
        results.append({
            'type': 'user',
            'title': user.display_name,
            'content': user.bio[:200] + '...' if user.bio and len(user.bio) > 200 else user.bio or 'No bio available',
            'author': user,
            'date': user.date_joined,
            'url': f'/accounts/user/{user.id}/',
            'rank': user.rank,
            'category': 'Users',
            'subcategory': user.location or 'Unknown location',
        })
    
    # Search categories and subcategories
    category_vector = SearchVector('name', 'description')
    categories = Category.objects.annotate(
        search=category_vector,
        rank=SearchRank(category_vector, search_query)
    ).filter(search=search_query)
    
    # Apply category filter
    if filters.get('category'):
        categories = categories.filter(id=filters['category'].id)
    
    for category in categories:
        results.append({
            'type': 'category',
            'title': category.name,
            'content': category.description,
            'author': None,
            'date': None,
            'url': f'/forums/{category.slug}/',
            'rank': category.rank,
            'category': 'Categories',
            'subcategory': 'Main Category',
        })
    
    subcategory_vector = SearchVector('name', 'description')
    subcategories = Subcategory.objects.annotate(
        search=subcategory_vector,
        rank=SearchRank(subcategory_vector, search_query)
    ).filter(
        search=search_query
    ).select_related('category')
    
    for subcategory in subcategories:
        results.append({
            'type': 'subcategory',
            'title': subcategory.name,
            'content': subcategory.description,
            'author': None,
            'date': None,
            'url': f'/forums/{subcategory.category.slug}/{subcategory.slug}/',
            'rank': subcategory.rank,
            'category': subcategory.category.name,
            'subcategory': 'Subcategory',
        })
    
    # Sort results
    if sort_by == 'relevance':
        results.sort(key=lambda x: x['rank'], reverse=True)
    elif sort_by == 'date_desc':
        results.sort(key=lambda x: x['date'] or timezone.now(), reverse=True)
    elif sort_by == 'date_asc':
        results.sort(key=lambda x: x['date'] or timezone.now())
    elif sort_by == 'author':
        results.sort(key=lambda x: x['author'].display_name if x['author'] else 'Z')
    
    return results


def perform_sqlite_unified_search(query, sort_by='relevance', filters=None):
    """Perform SQLite-compatible search across all content types."""
    results = []
    
    # Use icontains for SQLite compatibility
    query_terms = query.split()
    
    # Search posts
    post_q = Q()
    for term in query_terms:
        post_q |= Q(content__icontains=term)
    
    posts = Post.objects.filter(post_q).select_related('author', 'thread__subcategory__category')
    if filters:
        posts = apply_search_filters(posts, filters)
    
    for post in posts:
        results.append({
            'type': 'post',
            'title': f'Post in "{post.thread.title}"',
            'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
            'author': post.author,
            'date': post.created_at,
            'url': f"/forums/{post.thread.subcategory.category.slug}/{post.thread.subcategory.slug}/{post.thread.slug}/#post-{post.id}",
            'rank': 1.0,  # Simple rank for SQLite
            'category': post.thread.subcategory.category.name,
            'subcategory': post.thread.subcategory.name,
        })
    
    # Search threads
    thread_q = Q()
    for term in query_terms:
        thread_q |= Q(title__icontains=term)
    
    threads = Thread.objects.filter(thread_q).select_related('author', 'subcategory__category')
    if filters:
        threads = apply_search_filters(threads, filters)
    
    for thread in threads:
        results.append({
            'type': 'thread',
            'title': thread.title,
            'content': f'Thread in {thread.subcategory.name}',
            'author': thread.author,
            'date': thread.created_at,
            'url': f"/forums/{thread.subcategory.category.slug}/{thread.subcategory.slug}/{thread.slug}/",
            'rank': 1.0,
            'category': thread.subcategory.category.name,
            'subcategory': thread.subcategory.name,
        })
    
    # Search users
    user_q = Q()
    for term in query_terms:
        user_q |= Q(display_name__icontains=term) | Q(bio__icontains=term) | Q(location__icontains=term)
    
    users = User.objects.filter(Q(user_q) & Q(is_active=True))
    if filters:
        users = apply_search_filters(users, filters)
    
    for user in users:
        results.append({
            'type': 'user',
            'title': user.display_name,
            'content': user.bio[:200] + '...' if user.bio and len(user.bio) > 200 else user.bio or 'No bio available',
            'author': user,
            'date': user.date_joined,
            'url': f'/accounts/user/{user.id}/',
            'rank': 1.0,
            'category': 'Users',
            'subcategory': user.location or 'Unknown location',
        })
    
    # Search categories and subcategories
    category_q = Q()
    for term in query_terms:
        category_q |= Q(name__icontains=term) | Q(description__icontains=term)
    
    categories = Category.objects.filter(category_q)
    
    for category in categories:
        results.append({
            'type': 'category',
            'title': category.name,
            'content': category.description,
            'author': None,
            'date': None,
            'url': f'/forums/{category.slug}/',
            'rank': 1.0,
            'category': 'Categories',
            'subcategory': 'Main Category',
        })
    
    subcategories = Subcategory.objects.filter(category_q).select_related('category')
    
    for subcategory in subcategories:
        results.append({
            'type': 'subcategory',
            'title': subcategory.name,
            'content': subcategory.description,
            'author': None,
            'date': None,
            'url': f'/forums/{subcategory.category.slug}/{subcategory.slug}/',
            'rank': 1.0,
            'category': subcategory.category.name,
            'subcategory': 'Subcategory',
        })
    
    # Sort results
    if sort_by == 'relevance':
        results.sort(key=lambda x: x['rank'], reverse=True)
    elif sort_by == 'date_desc':
        results.sort(key=lambda x: x['date'] or timezone.now(), reverse=True)
    elif sort_by == 'date_asc':
        results.sort(key=lambda x: x['date'] or timezone.now())
    elif sort_by == 'author':
        results.sort(key=lambda x: x['author'].display_name if x['author'] else 'Z')
    
    return results


def search_posts(query, sort_by='relevance', filters=None):
    """Search forum posts."""
    filters = filters or {}
    if POSTGRES_SEARCH_AVAILABLE and 'postgresql' in settings.DATABASES['default']['ENGINE']:
        return search_posts_postgres(query, sort_by, filters)
    else:
        return search_posts_sqlite(query, sort_by, filters)


def search_posts_postgres(query, sort_by='relevance', filters=None):
    """Search forum posts using PostgreSQL full-text search."""
    filters = filters or {}
    search_query = SearchQuery(query)
    search_vector = SearchVector('content')
    
    posts = Post.objects.annotate(
        search=search_vector,
        rank=SearchRank(search_vector, search_query)
    ).filter(
        search=search_query
    ).select_related('author', 'thread__subcategory__category')
    
    # Apply filters
    posts = apply_search_filters(posts, filters)
    
    # Apply sorting
    if sort_by == 'relevance':
        posts = posts.order_by('-rank')
    elif sort_by == 'date_desc':
        posts = posts.order_by('-created_at')
    elif sort_by == 'date_asc':
        posts = posts.order_by('created_at')
    elif sort_by == 'author':
        posts = posts.order_by('author__display_name')
    
    results = []
    for post in posts:
        results.append({
            'type': 'post',
            'title': f'Post in "{post.thread.title}"',
            'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
            'author': post.author,
            'date': post.created_at,
            'url': f"/forums/{post.thread.subcategory.category.slug}/{post.thread.subcategory.slug}/{post.thread.slug}/#post-{post.id}",
            'rank': post.rank,
            'category': post.thread.subcategory.category.name,
            'subcategory': post.thread.subcategory.name,
        })
    
    return results


def search_posts_sqlite(query, sort_by='relevance', filters=None):
    """Search forum posts using SQLite-compatible search."""
    query_terms = query.split()
    
    post_q = Q()
    for term in query_terms:
        post_q |= Q(content__icontains=term)
    
    posts = Post.objects.filter(post_q).select_related('author', 'thread__subcategory__category')
    
    # Apply sorting
    if sort_by == 'relevance':
        pass  # Keep default ordering for SQLite
    elif sort_by == 'date_desc':
        posts = posts.order_by('-created_at')
    elif sort_by == 'date_asc':
        posts = posts.order_by('created_at')
    elif sort_by == 'author':
        posts = posts.order_by('author__display_name')
    
    results = []
    for post in posts:
        results.append({
            'type': 'post',
            'title': f'Post in "{post.thread.title}"',
            'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
            'author': post.author,
            'date': post.created_at,
            'url': f"/forums/{post.thread.subcategory.category.slug}/{post.thread.subcategory.slug}/{post.thread.slug}/#post-{post.id}",
            'rank': 1.0,
            'category': post.thread.subcategory.category.name,
            'subcategory': post.thread.subcategory.name,
        })
    
    return results


def search_threads(query, sort_by='relevance', filters=None):
    """Search forum threads."""
    if POSTGRES_SEARCH_AVAILABLE and 'postgresql' in settings.DATABASES['default']['ENGINE']:
        return search_threads_postgres(query, sort_by)
    else:
        return search_threads_sqlite(query, sort_by)


def search_threads_postgres(query, sort_by='relevance', filters=None):
    """Search forum threads using PostgreSQL full-text search."""
    search_query = SearchQuery(query)
    search_vector = SearchVector('title')
    
    threads = Thread.objects.annotate(
        search=search_vector,
        rank=SearchRank(search_vector, search_query)
    ).filter(
        search=search_query
    ).select_related('author', 'subcategory__category')
    
    # Apply sorting
    if sort_by == 'relevance':
        threads = threads.order_by('-rank')
    elif sort_by == 'date_desc':
        threads = threads.order_by('-created_at')
    elif sort_by == 'date_asc':
        threads = threads.order_by('created_at')
    elif sort_by == 'author':
        threads = threads.order_by('author__display_name')
    
    results = []
    for thread in threads:
        results.append({
            'type': 'thread',
            'title': thread.title,
            'content': f'Thread in {thread.subcategory.name} - {thread.post_count} posts',
            'author': thread.author,
            'date': thread.created_at,
            'url': f"/forums/{thread.subcategory.category.slug}/{thread.subcategory.slug}/{thread.slug}/",
            'rank': thread.rank,
            'category': thread.subcategory.category.name,
            'subcategory': thread.subcategory.name,
        })
    
    return results


def search_threads_sqlite(query, sort_by='relevance', filters=None):
    """Search forum threads using SQLite-compatible search."""
    query_terms = query.split()
    
    thread_q = Q()
    for term in query_terms:
        thread_q |= Q(title__icontains=term)
    
    threads = Thread.objects.filter(thread_q).select_related('author', 'subcategory__category')
    
    # Apply sorting
    if sort_by == 'relevance':
        pass  # Keep default ordering for SQLite
    elif sort_by == 'date_desc':
        threads = threads.order_by('-created_at')
    elif sort_by == 'date_asc':
        threads = threads.order_by('created_at')
    elif sort_by == 'author':
        threads = threads.order_by('author__display_name')
    
    results = []
    for thread in threads:
        results.append({
            'type': 'thread',
            'title': thread.title,
            'content': f'Thread in {thread.subcategory.name} - {thread.post_count} posts',
            'author': thread.author,
            'date': thread.created_at,
            'url': f"/forums/{thread.subcategory.category.slug}/{thread.subcategory.slug}/{thread.slug}/",
            'rank': 1.0,
            'category': thread.subcategory.category.name,
            'subcategory': thread.subcategory.name,
        })
    
    return results


def search_users(query, sort_by='relevance', filters=None):
    """Search forum users."""
    if POSTGRES_SEARCH_AVAILABLE and 'postgresql' in settings.DATABASES['default']['ENGINE']:
        return search_users_postgres(query, sort_by)
    else:
        return search_users_sqlite(query, sort_by)


def search_users_postgres(query, sort_by='relevance', filters=None):
    """Search forum users using PostgreSQL full-text search."""
    search_query = SearchQuery(query)
    search_vector = SearchVector('display_name', 'bio', 'location')
    
    users = User.objects.annotate(
        search=search_vector,
        rank=SearchRank(search_vector, search_query)
    ).filter(
        Q(search=search_query) & Q(is_active=True)
    )
    
    # Apply sorting
    if sort_by == 'relevance':
        users = users.order_by('-rank')
    elif sort_by == 'date_desc':
        users = users.order_by('-date_joined')
    elif sort_by == 'date_asc':
        users = users.order_by('date_joined')
    elif sort_by == 'author':
        users = users.order_by('display_name')
    
    results = []
    for user in users:
        results.append({
            'type': 'user',
            'title': user.display_name,
            'content': user.bio[:200] + '...' if user.bio and len(user.bio) > 200 else user.bio or 'No bio available',
            'author': user,
            'date': user.date_joined,
            'url': f'/accounts/user/{user.id}/',
            'rank': user.rank,
            'category': 'Users',
            'subcategory': user.location or 'Unknown location',
        })
    
    return results


def search_users_sqlite(query, sort_by='relevance', filters=None):
    """Search forum users using SQLite-compatible search."""
    query_terms = query.split()
    
    user_q = Q()
    for term in query_terms:
        user_q |= Q(display_name__icontains=term) | Q(bio__icontains=term) | Q(location__icontains=term)
    
    users = User.objects.filter(Q(user_q) & Q(is_active=True))
    
    # Apply sorting
    if sort_by == 'relevance':
        pass  # Keep default ordering for SQLite
    elif sort_by == 'date_desc':
        users = users.order_by('-date_joined')
    elif sort_by == 'date_asc':
        users = users.order_by('date_joined')
    elif sort_by == 'author':
        users = users.order_by('display_name')
    
    results = []
    for user in users:
        results.append({
            'type': 'user',
            'title': user.display_name,
            'content': user.bio[:200] + '...' if user.bio and len(user.bio) > 200 else user.bio or 'No bio available',
            'author': user,
            'date': user.date_joined,
            'url': f'/accounts/user/{user.id}/',
            'rank': 1.0,
            'category': 'Users',
            'subcategory': user.location or 'Unknown location',
        })
    
    return results


def search_categories(query, sort_by='relevance', filters=None):
    """Search categories and subcategories."""
    if POSTGRES_SEARCH_AVAILABLE and 'postgresql' in settings.DATABASES['default']['ENGINE']:
        return search_categories_postgres(query, sort_by)
    else:
        return search_categories_sqlite(query, sort_by)


def search_categories_postgres(query, sort_by='relevance', filters=None):
    """Search categories and subcategories using PostgreSQL full-text search."""
    search_query = SearchQuery(query)
    
    results = []
    
    # Search categories
    category_vector = SearchVector('name', 'description')
    categories = Category.objects.annotate(
        search=category_vector,
        rank=SearchRank(category_vector, search_query)
    ).filter(search=search_query)
    
    for category in categories:
        results.append({
            'type': 'category',
            'title': category.name,
            'content': category.description,
            'author': None,
            'date': None,
            'url': f'/forums/{category.slug}/',
            'rank': category.rank,
            'category': 'Categories',
            'subcategory': 'Main Category',
        })
    
    # Search subcategories
    subcategory_vector = SearchVector('name', 'description')
    subcategories = Subcategory.objects.annotate(
        search=subcategory_vector,
        rank=SearchRank(subcategory_vector, search_query)
    ).filter(
        search=search_query
    ).select_related('category')
    
    for subcategory in subcategories:
        results.append({
            'type': 'subcategory',
            'title': subcategory.name,
            'content': subcategory.description,
            'author': None,
            'date': None,
            'url': f'/forums/{subcategory.category.slug}/{subcategory.slug}/',
            'rank': subcategory.rank,
            'category': subcategory.category.name,
            'subcategory': 'Subcategory',
        })
    
    # Sort results
    if sort_by == 'relevance':
        results.sort(key=lambda x: x['rank'], reverse=True)
    else:
        # For categories, name sorting makes most sense
        results.sort(key=lambda x: x['title'])
    
    return results


def search_categories_sqlite(query, sort_by='relevance', filters=None):
    """Search categories and subcategories using SQLite-compatible search."""
    query_terms = query.split()
    
    results = []
    
    # Search categories
    category_q = Q()
    for term in query_terms:
        category_q |= Q(name__icontains=term) | Q(description__icontains=term)
    
    categories = Category.objects.filter(category_q)
    
    for category in categories:
        results.append({
            'type': 'category',
            'title': category.name,
            'content': category.description,
            'author': None,
            'date': None,
            'url': f'/forums/{category.slug}/',
            'rank': 1.0,
            'category': 'Categories',
            'subcategory': 'Main Category',
        })
    
    # Search subcategories
    subcategories = Subcategory.objects.filter(category_q).select_related('category')
    
    for subcategory in subcategories:
        results.append({
            'type': 'subcategory',
            'title': subcategory.name,
            'content': subcategory.description,
            'author': None,
            'date': None,
            'url': f'/forums/{subcategory.category.slug}/{subcategory.slug}/',
            'rank': 1.0,
            'category': subcategory.category.name,
            'subcategory': 'Subcategory',
        })
    
    # Sort results
    if sort_by == 'relevance':
        results.sort(key=lambda x: x['rank'], reverse=True)
    else:
        # For categories, name sorting makes most sense
        results.sort(key=lambda x: x['title'])
    
    return results


def search_suggestions_view(request):
    """AJAX endpoint for search autocomplete suggestions."""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'AJAX request required'}, status=400)
    
    query = request.GET.get('q')
    
    if query is None:
        return JsonResponse({'error': 'Query parameter required'}, status=400)
    
    query = query.strip()
    
    if len(query) < 2:
        return JsonResponse({'error': 'Query must be at least 2 characters'}, status=400)
    
    suggestions = []
    
    # Limit suggestions to prevent overwhelming the user
    max_suggestions = 8
    per_type_limit = 2
    
    try:
        # Get suggestions for each content type
        if POSTGRES_SEARCH_AVAILABLE and 'postgresql' in settings.DATABASES['default']['ENGINE']:
            suggestions.extend(get_postgres_suggestions(query, per_type_limit))
        else:
            suggestions.extend(get_sqlite_suggestions(query, per_type_limit))
        
        # Limit total suggestions
        suggestions = suggestions[:max_suggestions]
        
    except Exception as e:
        # Log error but don't expose it to user
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Search suggestions error: {e}")
        suggestions = []
    
    return JsonResponse({'suggestions': suggestions})


def get_postgres_suggestions(query, per_type_limit):
    """Get search suggestions using PostgreSQL full-text search."""
    search_query = SearchQuery(query)
    suggestions = []
    
    # Search threads (highest priority)
    thread_vector = SearchVector('title')
    threads = Thread.objects.annotate(
        search=thread_vector,
        rank=SearchRank(thread_vector, search_query)
    ).filter(
        search=search_query
    ).select_related('subcategory__category').order_by('-rank')[:per_type_limit]
    
    for thread in threads:
        suggestions.append({
            'type': 'thread',
            'title': thread.title,
            'description': f'Discussion in {thread.subcategory.name}',
            'url': f"/forums/{thread.subcategory.category.slug}/{thread.subcategory.slug}/{thread.slug}/",
        })
    
    # Search posts
    post_vector = SearchVector('content')
    posts = Post.objects.annotate(
        search=post_vector,
        rank=SearchRank(post_vector, search_query)
    ).filter(
        search=search_query
    ).select_related('thread__subcategory__category')[:per_type_limit]
    
    for post in posts:
        content_preview = post.content[:50] + '...' if len(post.content) > 50 else post.content
        suggestions.append({
            'type': 'post',
            'title': f'Post in "{post.thread.title}"',
            'description': content_preview,
            'url': f"/forums/{post.thread.subcategory.category.slug}/{post.thread.subcategory.slug}/{post.thread.slug}/#post-{post.id}",
        })
    
    # Search users
    user_vector = SearchVector('display_name', 'bio')
    users = User.objects.annotate(
        search=user_vector,
        rank=SearchRank(user_vector, search_query)
    ).filter(
        Q(search=search_query) & Q(is_active=True)
    )[:per_type_limit]
    
    for user in users:
        suggestions.append({
            'type': 'user',
            'title': user.display_name,
            'description': user.location or 'Community member',
            'url': f'/accounts/user/{user.id}/',
        })
    
    # Search categories
    category_vector = SearchVector('name', 'description')
    categories = Category.objects.annotate(
        search=category_vector,
        rank=SearchRank(category_vector, search_query)
    ).filter(search=search_query)[:per_type_limit]
    
    for category in categories:
        suggestions.append({
            'type': 'category',
            'title': category.name,
            'description': category.description[:50] + '...' if len(category.description) > 50 else category.description,
            'url': f'/forums/{category.slug}/',
        })
    
    # Search subcategories
    subcategory_vector = SearchVector('name', 'description')
    subcategories = Subcategory.objects.annotate(
        search=subcategory_vector,
        rank=SearchRank(subcategory_vector, search_query)
    ).filter(search=search_query).select_related('category')[:per_type_limit]
    
    for subcategory in subcategories:
        suggestions.append({
            'type': 'subcategory',
            'title': subcategory.name,
            'description': f'Forum in {subcategory.category.name}',
            'url': f'/forums/{subcategory.category.slug}/{subcategory.slug}/',
        })
    
    return suggestions


def get_sqlite_suggestions(query, per_type_limit):
    """Get search suggestions using SQLite-compatible search."""
    query_terms = query.split()
    suggestions = []
    
    # Search threads
    thread_q = Q()
    for term in query_terms:
        thread_q |= Q(title__icontains=term)
    
    threads = Thread.objects.filter(thread_q).select_related('subcategory__category')[:per_type_limit]
    
    for thread in threads:
        suggestions.append({
            'type': 'thread',
            'title': thread.title,
            'description': f'Discussion in {thread.subcategory.name}',
            'url': f"/forums/{thread.subcategory.category.slug}/{thread.subcategory.slug}/{thread.slug}/",
        })
    
    # Search posts
    post_q = Q()
    for term in query_terms:
        post_q |= Q(content__icontains=term)
    
    posts = Post.objects.filter(post_q).select_related('thread__subcategory__category')[:per_type_limit]
    
    for post in posts:
        content_preview = post.content[:50] + '...' if len(post.content) > 50 else post.content
        suggestions.append({
            'type': 'post',
            'title': f'Post in "{post.thread.title}"',
            'description': content_preview,
            'url': f"/forums/{post.thread.subcategory.category.slug}/{post.thread.subcategory.slug}/{post.thread.slug}/#post-{post.id}",
        })
    
    # Search users
    user_q = Q()
    for term in query_terms:
        user_q |= Q(display_name__icontains=term) | Q(bio__icontains=term) | Q(location__icontains=term)
    
    users = User.objects.filter(Q(user_q) & Q(is_active=True))[:per_type_limit]
    
    for user in users:
        suggestions.append({
            'type': 'user',
            'title': user.display_name,
            'description': user.location or 'Community member',
            'url': f'/accounts/user/{user.id}/',
        })
    
    # Search categories
    category_q = Q()
    for term in query_terms:
        category_q |= Q(name__icontains=term) | Q(description__icontains=term)
    
    categories = Category.objects.filter(category_q)[:per_type_limit]
    
    for category in categories:
        suggestions.append({
            'type': 'category',
            'title': category.name,
            'description': category.description[:50] + '...' if len(category.description) > 50 else category.description,
            'url': f'/forums/{category.slug}/',
        })
    
    # Search subcategories
    subcategory_q = Q()
    for term in query_terms:
        subcategory_q |= Q(name__icontains=term) | Q(description__icontains=term)
    
    subcategories = Subcategory.objects.filter(subcategory_q).select_related('category')[:per_type_limit]
    
    for subcategory in subcategories:
        suggestions.append({
            'type': 'subcategory',
            'title': subcategory.name,
            'description': f'Forum in {subcategory.category.name}',
            'url': f'/forums/{subcategory.category.slug}/{subcategory.slug}/',
        })
    
    return suggestions


@login_required
def save_search_view(request):
    """AJAX view to save a search query."""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    
    if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"error": "AJAX request required"}, status=400)
    
    # Get form data
    name = request.POST.get("name", "").strip()
    query = request.POST.get("query", "").strip()
    content_type = request.POST.get("content_type", "all")
    sort_by = request.POST.get("sort_by", "relevance")
    
    # Validate inputs
    if not name:
        return JsonResponse({"error": "Search name is required"}, status=400)
    
    if not query:
        return JsonResponse({"error": "Search query is required"}, status=400)
    
    if len(name) > 100:
        return JsonResponse({"error": "Search name is too long (max 100 characters)"}, status=400)
    
    # Check if user already has a saved search with this name
    existing_search = SavedSearch.objects.filter(
        user=request.user,
        name=name
    ).first()
    
    if existing_search:
        return JsonResponse({"error": "You already have a saved search with this name"}, status=400)
    
    # Create the saved search
    try:
        saved_search = SavedSearch.objects.create(
            user=request.user,
            name=name,
            query=query,
            content_type=content_type,
            sort_by=sort_by
        )
        
        return JsonResponse({
            "success": True,
            "message": f"Search \"{name}\" saved successfully",
            "saved_search": {
                "id": saved_search.id,
                "name": saved_search.name,
                "query": saved_search.query,
                "url": saved_search.get_search_url()
            }
        })
        
    except Exception as e:
        return JsonResponse({"error": "Failed to save search"}, status=500)


@login_required
def delete_saved_search_view(request, search_id):
    """AJAX view to delete a saved search."""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    
    if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"error": "AJAX request required"}, status=400)
    
    # Get the saved search
    saved_search = get_object_or_404(
        SavedSearch,
        id=search_id,
        user=request.user
    )
    
    try:
        search_name = saved_search.name
        saved_search.delete()
        
        return JsonResponse({
            "success": True,
            "message": f"Search \"{search_name}\" deleted successfully"
        })
        
    except Exception as e:
        return JsonResponse({"error": "Failed to delete search"}, status=500)


@login_required
def saved_searches_view(request):
    """View for managing users saved searches."""
    saved_searches = SavedSearch.get_user_saved_searches(request.user)
    
    context = {
        "saved_searches": saved_searches,
    }
    
    return render(request, "forums/saved_searches.html", context)


@login_required
def search_history_view(request):
    """View for displaying users search history."""
    search_history = SearchHistory.get_user_recent_searches(request.user, limit=50)
    
    # Group searches by date for better organization
    from collections import defaultdict
    grouped_history = defaultdict(list)
    
    for search in search_history:
        date_key = search.created_at.date()
        grouped_history[date_key].append(search)
    
    context = {
        "search_history": search_history,
        "grouped_history": dict(grouped_history),
    }
    
    return render(request, "forums/search_history.html", context)


@login_required
def clear_search_history_view(request):
    """AJAX view to clear users search history."""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    
    if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"error": "AJAX request required"}, status=400)
    
    try:
        # Delete all search history for the user
        deleted_count = SearchHistory.objects.filter(user=request.user).delete()[0]
        
        return JsonResponse({
            "success": True,
            "message": f"Cleared {deleted_count} search entries from your history"
        })
        
    except Exception as e:
        return JsonResponse({"error": "Failed to clear search history"}, status=500)


@login_required
def search_analytics_dashboard(request):
    """Admin dashboard for search analytics and insights."""
    # Check if user has admin or moderator access
    if not request.user.has_moderator_access():
        return HttpResponseForbidden("Access denied. Moderator or Admin privileges required.")
    
    # Get date range from request (default to last 30 days)
    try:
        days = int(request.GET.get('days', 30))
        days = min(max(days, 1), 365)  # Limit to 1-365 days
    except (ValueError, TypeError):
        days = 30
    
    since_date = timezone.now() - timedelta(days=days)
    
    # Basic metrics
    total_searches = SearchAnalytics.objects.filter(created_at__gte=since_date).count()
    unique_users = SearchAnalytics.objects.filter(
        created_at__gte=since_date,
        user__isnull=False
    ).values('user').distinct().count()
    unique_sessions = SearchAnalytics.objects.filter(
        created_at__gte=since_date
    ).values('session_key').distinct().count()
    
    # Performance metrics
    performance_metrics = SearchAnalytics.objects.filter(
        created_at__gte=since_date
    ).aggregate(
        avg_search_time=Avg('search_time_ms'),
        avg_results_count=Avg('results_count'),
        avg_database_hits=Avg('database_hits'),
        zero_result_searches=Count('id', filter=Q(results_count=0)),
        clicked_searches=Count('id', filter=Q(clicked_result_position__isnull=False))
    )
    
    # Calculate derived metrics
    zero_result_rate = 0
    click_through_rate = 0
    if total_searches > 0:
        zero_result_rate = (performance_metrics['zero_result_searches'] / total_searches) * 100
        click_through_rate = (performance_metrics['clicked_searches'] / total_searches) * 100
    
    # Top search queries
    top_queries = SearchAnalytics.objects.filter(
        created_at__gte=since_date
    ).values('normalized_query').annotate(
        search_count=Count('id'),
        avg_results=Avg('results_count'),
        avg_time_ms=Avg('search_time_ms')
    ).order_by('-search_count')[:20]
    
    # Content type distribution
    content_type_stats = SearchAnalytics.objects.filter(
        created_at__gte=since_date
    ).values('content_type').annotate(
        search_count=Count('id'),
        avg_results=Avg('results_count')
    ).order_by('-search_count')
    
    # Search trends by day
    search_trends = []
    for i in range(days):
        date = timezone.now().date() - timedelta(days=i)
        daily_searches = SearchAnalytics.objects.filter(
            created_at__date=date
        ).count()
        search_trends.append({
            'date': date.strftime('%Y-%m-%d'),
            'searches': daily_searches
        })
    search_trends.reverse()  # Chronological order
    
    # Poor performing searches (high time, low results)
    poor_searches = SearchAnalytics.objects.filter(
        created_at__gte=since_date,
        search_time_ms__gte=1000  # Searches taking more than 1 second
    ).values('query').annotate(
        search_count=Count('id'),
        avg_time_ms=Avg('search_time_ms'),
        avg_results=Avg('results_count')
    ).filter(search_count__gte=2).order_by('-avg_time_ms')[:10]
    
    # Click position analysis
    click_positions = SearchAnalytics.objects.filter(
        created_at__gte=since_date,
        clicked_result_position__isnull=False
    ).values('clicked_result_position').annotate(
        click_count=Count('id')
    ).order_by('clicked_result_position')[:10]
    
    # Browser/device analysis
    user_agents = SearchAnalytics.objects.filter(
        created_at__gte=since_date,
        user_agent__isnull=False
    ).exclude(user_agent='').values('user_agent').annotate(
        search_count=Count('id')
    ).order_by('-search_count')[:10]
    
    # Search failure analysis (zero results)
    failed_searches = SearchAnalytics.objects.filter(
        created_at__gte=since_date,
        results_count=0
    ).values('normalized_query').annotate(
        failure_count=Count('id')
    ).filter(failure_count__gte=2).order_by('-failure_count')[:15]
    
    context = {
        'days': days,
        'since_date': since_date,
        'total_searches': total_searches,
        'unique_users': unique_users,
        'unique_sessions': unique_sessions,
        'performance_metrics': performance_metrics,
        'zero_result_rate': round(zero_result_rate, 2),
        'click_through_rate': round(click_through_rate, 2),
        'top_queries': top_queries,
        'content_type_stats': content_type_stats,
        'search_trends': search_trends,
        'poor_searches': poor_searches,
        'click_positions': click_positions,
        'user_agents': user_agents,
        'failed_searches': failed_searches,
    }
    
    return render(request, 'forums/analytics_dashboard.html', context)


@login_required
def search_analytics_api(request):
    """API endpoint for search analytics data (AJAX requests)."""
    if not request.user.has_moderator_access():
        return JsonResponse({'error': 'Access denied. Moderator or Admin privileges required.'}, status=403)
    
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'AJAX required'}, status=400)
    
    metric_type = request.GET.get('metric', 'trends')
    days = min(max(int(request.GET.get('days', 7)), 1), 365)
    since_date = timezone.now() - timedelta(days=days)
    
    if metric_type == 'trends':
        # Daily search trends
        trends = []
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            daily_count = SearchAnalytics.objects.filter(
                created_at__date=date
            ).count()
            trends.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': daily_count
            })
        trends.reverse()
        return JsonResponse({'trends': trends})
    
    elif metric_type == 'performance':
        # Performance metrics over time
        performance_data = []
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            daily_metrics = SearchAnalytics.objects.filter(
                created_at__date=date
            ).aggregate(
                avg_time=Avg('search_time_ms'),
                avg_results=Avg('results_count')
            )
            performance_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'avg_time': round(daily_metrics['avg_time'] or 0, 2),
                'avg_results': round(daily_metrics['avg_results'] or 0, 1)
            })
        performance_data.reverse()
        return JsonResponse({'performance': performance_data})
    
    elif metric_type == 'content_types':
        # Content type popularity
        content_stats = SearchAnalytics.objects.filter(
            created_at__gte=since_date
        ).values('content_type').annotate(
            count=Count('id')
        ).order_by('-count')
        return JsonResponse({'content_types': list(content_stats)})
    
    elif metric_type == 'cache_stats':
        # Cache performance statistics
        optimizer = SearchPerformanceOptimizer()
        optimization_stats = optimizer.get_optimization_stats()
        return JsonResponse(optimization_stats)
    
    else:
        return JsonResponse({'error': 'Invalid metric type'}, status=400)


# Performance Optimization System
class SearchPerformanceOptimizer:
    """Comprehensive search performance optimization system."""
    
    CACHE_TIMEOUT = 300  # 5 minutes
    SLOW_QUERY_THRESHOLD_MS = 1000  # 1 second
    
    @staticmethod
    def generate_cache_key(query, content_type, sort_by, filters):
        """Generate a unique cache key for search results."""
        # Create a string representation of the search parameters
        cache_data = {
            'query': query.lower().strip(),
            'content_type': content_type,
            'sort_by': sort_by,
            'filters': filters or {}
        }
        
        # Create hash of the search parameters
        cache_string = str(sorted(cache_data.items()))
        cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
        
        return f"search_results:{cache_hash}"
    
    @staticmethod
    def get_cached_results(cache_key):
        """Retrieve cached search results."""
        return cache.get(cache_key)
    
    @staticmethod
    def cache_results(cache_key, results, performance_data):
        """Cache search results with performance metadata."""
        cache_data = {
            'results': results,
            'performance': performance_data,
            'cached_at': timezone.now().isoformat(),
            'total_results': len(results)
        }
        
        # Use shorter cache timeout for queries with few results
        timeout = SearchPerformanceOptimizer.CACHE_TIMEOUT
        if len(results) < 5:
            timeout = timeout // 2  # 2.5 minutes for low-result queries
        
        cache.set(cache_key, cache_data, timeout=timeout)
        return cache_data
    
    @staticmethod
    def should_use_cache(query, content_type):
        """Determine if search should use caching."""
        # Don't cache very short queries or user-specific content
        if len(query.strip()) < 3:
            return False
        
        # Don't cache user searches (privacy)
        if content_type == 'users':
            return False
        
        return True
    
    @staticmethod
    def optimize_queryset(queryset, search_type):
        """Apply optimizations to search querysets."""
        if search_type == 'posts':
            return queryset.select_related(
                'author', 'thread__subcategory__category'
            ).prefetch_related('votes')[:100]  # Limit large result sets
        
        elif search_type == 'threads':
            return queryset.select_related(
                'author', 'subcategory__category'
            ).prefetch_related('posts')[:50]
        
        elif search_type == 'users':
            return queryset.prefetch_related('posts', 'threads')[:30]
        
        elif search_type == 'categories':
            return queryset.prefetch_related('subcategories')[:20]
        
        return queryset
    
    @staticmethod
    def analyze_query_performance(search_time_ms, results_count, database_hits):
        """Analyze search performance and suggest optimizations."""
        suggestions = []
        
        if search_time_ms > SearchPerformanceOptimizer.SLOW_QUERY_THRESHOLD_MS:
            suggestions.append({
                'type': 'performance',
                'level': 'warning',
                'message': f'Search took {search_time_ms}ms - consider optimization'
            })
        
        if database_hits > 10:
            suggestions.append({
                'type': 'efficiency',
                'level': 'info',
                'message': f'{database_hits} database queries - may benefit from caching'
            })
        
        if results_count == 0:
            suggestions.append({
                'type': 'results',
                'level': 'warning',
                'message': 'No results found - consider query expansion or fuzzy matching'
            })
        
        if results_count > 1000:
            suggestions.append({
                'type': 'pagination',
                'level': 'info',
                'message': f'{results_count} results - consider more specific filtering'
            })
        
        return suggestions
    
    @staticmethod
    def get_optimization_stats():
        """Get performance optimization statistics."""
        # Cache hit rate
        cache_stats = {
            'cache_hits': cache.get('search_cache_hits', 0),
            'cache_misses': cache.get('search_cache_misses', 0),
            'cache_size': cache.get('search_cache_size', 0)
        }
        
        total_requests = cache_stats['cache_hits'] + cache_stats['cache_misses']
        hit_rate = 0
        if total_requests > 0:
            hit_rate = (cache_stats['cache_hits'] / total_requests) * 100
        
        # Recent performance metrics
        recent_analytics = SearchAnalytics.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).aggregate(
            avg_time=Avg('search_time_ms'),
            slow_queries=Count('id', filter=Q(search_time_ms__gte=1000)),
            total_queries=Count('id')
        )
        
        return {
            'cache_hit_rate': round(hit_rate, 2),
            'cache_stats': cache_stats,
            'recent_performance': recent_analytics
        }


def optimized_search_view(request):
    """Enhanced search view with performance optimization."""
    form = SearchForm(request.GET or None)
    results = []
    query = ''
    content_type = 'all'
    sort_by = 'relevance'
    total_results = 0
    performance_data = {}
    cache_used = False
    
    if form.is_valid():
        query = form.cleaned_data['query']
        content_type = form.cleaned_data['content_type']
        sort_by = form.cleaned_data['sort_by']
        
        # Extract advanced filters
        filters = {
            'date_from': form.cleaned_data.get('date_from'),
            'date_to': form.cleaned_data.get('date_to'),
            'author': form.cleaned_data.get('author'),
            'category': form.cleaned_data.get('category'),
        }
        
        # Performance optimization with caching
        optimizer = SearchPerformanceOptimizer()
        cache_key = optimizer.generate_cache_key(query, content_type, sort_by, filters)
        
        # Try to get cached results
        if optimizer.should_use_cache(query, content_type):
            cached_data = optimizer.get_cached_results(cache_key)
            if cached_data:
                results = cached_data['results']
                total_results = cached_data['total_results']
                performance_data = cached_data['performance']
                cache_used = True
                
                # Update cache statistics
                cache.set('search_cache_hits', cache.get('search_cache_hits', 0) + 1, timeout=86400)
        
        if not cache_used:
            # Perform search with timing
            start_time = time.time()
            initial_queries = len(connection.queries)
            
            # Perform search based on content type with filters
            if content_type == 'all':
                results = perform_unified_search(query, sort_by, filters)
                database_hits = 5  # Unified search hits multiple tables
            elif content_type == 'posts':
                results = search_posts(query, sort_by, filters)
                database_hits = 2  # Posts and related joins
            elif content_type == 'threads':
                results = search_threads(query, sort_by, filters)
                database_hits = 2  # Threads and related joins
            elif content_type == 'users':
                results = search_users(query, sort_by, filters)
                database_hits = 1  # Users table only
            elif content_type == 'categories':
                results = search_categories(query, sort_by, filters)
                database_hits = 2  # Categories and subcategories
            
            # Calculate actual performance metrics
            search_time_ms = int((time.time() - start_time) * 1000)
            actual_queries = len(connection.queries) - initial_queries
            total_results = len(results)
            
            performance_data = {
                'search_time_ms': search_time_ms,
                'database_hits': actual_queries,
                'cached': False,
                'query_count': actual_queries
            }
            
            # Cache results if appropriate
            if optimizer.should_use_cache(query, content_type):
                optimizer.cache_results(cache_key, results, performance_data)
                cache.set('search_cache_misses', cache.get('search_cache_misses', 0) + 1, timeout=86400)
            
            # Record analytics with actual performance data
            if query.strip():
                SearchAnalytics.record_search_analytics(
                    request=request,
                    query=query,
                    content_type=content_type,
                    sort_by=sort_by,
                    results_count=total_results,
                    search_time_ms=search_time_ms,
                    database_hits=actual_queries
                )
                
                # Record search in history for authenticated users
                SearchHistory.record_search(
                    user=request.user,
                    query=query,
                    content_type=content_type,
                    results_count=total_results
                )
        
        # Analyze performance and get suggestions
        optimizer = SearchPerformanceOptimizer()
        performance_suggestions = optimizer.analyze_query_performance(
            performance_data.get('search_time_ms', 0),
            total_results,
            performance_data.get('database_hits', 0)
        )
        
        performance_data['suggestions'] = performance_suggestions
        performance_data['cache_used'] = cache_used
    
    # Paginate results
    paginator = Paginator(results, 20)  # 20 results per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get recent searches for authenticated users
    recent_searches = []
    saved_searches = []
    if request.user.is_authenticated:
        recent_searches = SearchHistory.get_user_recent_searches(request.user, limit=5)
        saved_searches = SavedSearch.get_user_saved_searches(request.user)
    
    context = {
        'form': form,
        'query': query,
        'content_type': content_type,
        'sort_by': sort_by,
        'results': page_obj,
        'total_results': total_results,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'recent_searches': recent_searches,
        'saved_searches': saved_searches,
        'performance_data': performance_data,
    }
    
    return render(request, 'forums/search_results.html', context)


# Advanced Search Ranking System
class SearchRankingEngine:
    """Advanced search result ranking with multiple scoring factors."""
    
    @staticmethod
    def calculate_relevance_score(item, query):
        """Calculate relevance score based on query match quality."""
        query_terms = query.lower().split()
        content = ''
        title = ''
        
        if item['type'] == 'post':
            content = item.get('content', '').lower()
            title = item.get('title', '').lower()
        elif item['type'] == 'thread':
            title = item.get('title', '').lower()
            content = title  # For threads, title is the main content
        elif item['type'] == 'user':
            title = item.get('title', '').lower()  # display_name
            content = item.get('content', '').lower()  # bio
        elif item['type'] in ['category', 'subcategory']:
            title = item.get('title', '').lower()
            content = item.get('content', '').lower()  # description
        
        score = 0
        
        # Title matches are more important
        for term in query_terms:
            if term in title:
                if title == term:  # Exact title match
                    score += 10
                elif title.startswith(term):  # Title starts with term
                    score += 7
                else:  # Term appears in title
                    score += 5
        
        # Content matches
        for term in query_terms:
            if term in content:
                # Count occurrences
                occurrences = content.count(term)
                score += min(occurrences * 2, 8)  # Max 8 points for content matches
        
        # Phrase matching bonus
        query_phrase = query.lower()
        if query_phrase in title:
            score += 15  # Big bonus for exact phrase in title
        elif query_phrase in content:
            score += 8   # Bonus for exact phrase in content
        
        return score
    
    @staticmethod
    def calculate_popularity_score(item):
        """Calculate popularity score based on engagement metrics."""
        score = 0
        
        if item['type'] == 'post':
            # For posts, consider votes and thread activity
            score += min(item.get('vote_count', 0) * 2, 20)  # Max 20 points
            
        elif item['type'] == 'thread':
            # For threads, consider view count and post count
            view_count = item.get('view_count', 0)
            post_count = item.get('post_count', 0)
            
            score += min(view_count // 10, 15)  # 1 point per 10 views, max 15
            score += min(post_count * 2, 10)    # 2 points per post, max 10
            
        elif item['type'] == 'user':
            # For users, consider their activity level
            post_count = getattr(item.get('author'), 'posts', {}).count() if item.get('author') else 0
            score += min(post_count // 5, 15)  # 1 point per 5 posts, max 15
            
        elif item['type'] in ['category', 'subcategory']:
            # For categories, consider number of threads/posts
            score += 5  # Base score for categories
        
        return score
    
    @staticmethod
    def calculate_freshness_score(item):
        """Calculate freshness score based on recency."""
        if not item.get('date'):
            return 0
        
        now = timezone.now()
        item_date = item['date']
        
        # Convert to timezone-aware datetime if needed
        if hasattr(item_date, 'replace') and item_date.tzinfo is None:
            item_date = item_date.replace(tzinfo=timezone.utc)
        
        # Calculate age in days
        try:
            age_days = (now - item_date).days
        except:
            return 0
        
        # Fresher content gets higher scores
        if age_days <= 1:
            return 10      # Very fresh (today/yesterday)
        elif age_days <= 7:
            return 8       # Recent (this week)
        elif age_days <= 30:
            return 5       # Moderate (this month)
        elif age_days <= 90:
            return 2       # Older (this quarter)
        else:
            return 0       # Old content
    
    @staticmethod
    def calculate_type_priority_score(item, content_type_preference):
        """Calculate score based on content type preference."""
        type_scores = {
            'thread': 10,    # Threads are typically most important
            'post': 8,       # Posts are very relevant
            'user': 5,       # Users are moderately relevant
            'category': 3,   # Categories are less specific
            'subcategory': 4 # Subcategories are slightly more specific
        }
        
        base_score = type_scores.get(item['type'], 0)
        
        # Boost score if it matches the preferred content type
        if content_type_preference != 'all' and item['type'] == content_type_preference:
            base_score *= 1.5
        
        return base_score
    
    @staticmethod
    def calculate_quality_score(item):
        """Calculate quality score based on content characteristics."""
        score = 0
        
        # Length-based quality assessment
        content_length = len(item.get('content', ''))
        title_length = len(item.get('title', ''))
        
        # Optimal content length scoring
        if item['type'] == 'post':
            if 50 <= content_length <= 1000:  # Good post length
                score += 5
            elif content_length > 1000:       # Very detailed post
                score += 3
            elif content_length < 20:         # Very short post
                score -= 2
                
        elif item['type'] == 'thread':
            if 10 <= title_length <= 100:     # Good title length
                score += 5
            elif title_length < 5:            # Very short title
                score -= 3
        
        # Penalize empty or very short content
        if content_length < 10:
            score -= 5
        
        return max(score, -5)  # Minimum score of -5
    
    @classmethod
    def rank_search_results(cls, results, query, content_type='all'):
        """Apply comprehensive ranking to search results."""
        if not results:
            return results
        
        # Calculate scores for each result
        for item in results:
            scores = {
                'relevance': cls.calculate_relevance_score(item, query),
                'popularity': cls.calculate_popularity_score(item),
                'freshness': cls.calculate_freshness_score(item),
                'type_priority': cls.calculate_type_priority_score(item, content_type),
                'quality': cls.calculate_quality_score(item)
            }
            
            # Weighted total score
            weights = {
                'relevance': 0.4,     # 40% - Most important
                'popularity': 0.25,   # 25% - User engagement
                'freshness': 0.15,    # 15% - Recency
                'type_priority': 0.1, # 10% - Content type preference
                'quality': 0.1        # 10% - Content quality
            }
            
            total_score = sum(scores[factor] * weight for factor, weight in weights.items())
            
            # Store scoring details for debugging
            item['ranking_scores'] = scores
            item['total_score'] = total_score
        
        # Sort by total score (highest first)
        ranked_results = sorted(results, key=lambda x: x.get('total_score', 0), reverse=True)
        
        return ranked_results
    
    @staticmethod
    def get_ranking_explanation(item):
        """Generate human-readable explanation of ranking factors."""
        if not item.get('ranking_scores'):
            return "No ranking data available"
        
        scores = item['ranking_scores']
        explanations = []
        
        if scores['relevance'] > 10:
            explanations.append("High relevance match")
        elif scores['relevance'] > 5:
            explanations.append("Good relevance match")
        
        if scores['popularity'] > 15:
            explanations.append("Very popular content")
        elif scores['popularity'] > 8:
            explanations.append("Popular content")
        
        if scores['freshness'] > 7:
            explanations.append("Recent content")
        
        if scores['quality'] > 3:
            explanations.append("High quality content")
        elif scores['quality'] < 0:
            explanations.append("Short content")
        
        return "; ".join(explanations) if explanations else "Standard ranking"


def enhanced_search_view(request):
    """Search view with advanced ranking and performance optimization."""
    form = SearchForm(request.GET or None)
    results = []
    query = ''
    content_type = 'all'
    sort_by = 'relevance'
    total_results = 0
    performance_data = {}
    cache_used = False
    
    if form.is_valid():
        query = form.cleaned_data['query']
        content_type = form.cleaned_data['content_type']
        sort_by = form.cleaned_data['sort_by']
        
        # Extract advanced filters
        filters = {
            'date_from': form.cleaned_data.get('date_from'),
            'date_to': form.cleaned_data.get('date_to'),
            'author': form.cleaned_data.get('author'),
            'category': form.cleaned_data.get('category'),
        }
        
        # Performance optimization with caching
        optimizer = SearchPerformanceOptimizer()
        ranking_engine = SearchRankingEngine()
        
        # Include ranking in cache key
        cache_key = optimizer.generate_cache_key(query, content_type, sort_by, filters) + f":ranked"
        
        # Try to get cached results
        if optimizer.should_use_cache(query, content_type):
            cached_data = optimizer.get_cached_results(cache_key)
            if cached_data:
                results = cached_data['results']
                total_results = cached_data['total_results']
                performance_data = cached_data['performance']
                cache_used = True
                
                # Update cache statistics
                cache.set('search_cache_hits', cache.get('search_cache_hits', 0) + 1, timeout=86400)
        
        if not cache_used:
            # Perform search with timing
            start_time = time.time()
            initial_queries = len(connection.queries)
            
            # Perform search based on content type with filters
            if content_type == 'all':
                raw_results = perform_unified_search(query, sort_by, filters)
                database_hits = 5
            elif content_type == 'posts':
                raw_results = search_posts(query, sort_by, filters)
                database_hits = 2
            elif content_type == 'threads':
                raw_results = search_threads(query, sort_by, filters)
                database_hits = 2
            elif content_type == 'users':
                raw_results = search_users(query, sort_by, filters)
                database_hits = 1
            elif content_type == 'categories':
                raw_results = search_categories(query, sort_by, filters)
                database_hits = 2
            
            # Apply advanced ranking if sort_by is 'relevance'
            if sort_by == 'relevance':
                results = ranking_engine.rank_search_results(raw_results, query, content_type)
            else:
                results = raw_results
            
            # Calculate performance metrics
            search_time_ms = int((time.time() - start_time) * 1000)
            actual_queries = len(connection.queries) - initial_queries
            total_results = len(results)
            
            performance_data = {
                'search_time_ms': search_time_ms,
                'database_hits': actual_queries,
                'cached': False,
                'query_count': actual_queries,
                'ranking_applied': sort_by == 'relevance'
            }
            
            # Cache results if appropriate
            if optimizer.should_use_cache(query, content_type):
                optimizer.cache_results(cache_key, results, performance_data)
                cache.set('search_cache_misses', cache.get('search_cache_misses', 0) + 1, timeout=86400)
            
            # Record analytics
            if query.strip():
                SearchAnalytics.record_search_analytics(
                    request=request,
                    query=query,
                    content_type=content_type,
                    sort_by=sort_by,
                    results_count=total_results,
                    search_time_ms=search_time_ms,
                    database_hits=actual_queries
                )
                
                SearchHistory.record_search(
                    user=request.user,
                    query=query,
                    content_type=content_type,
                    results_count=total_results
                )
        
        # Analyze performance
        optimizer = SearchPerformanceOptimizer()
        performance_suggestions = optimizer.analyze_query_performance(
            performance_data.get('search_time_ms', 0),
            total_results,
            performance_data.get('database_hits', 0)
        )
        
        performance_data['suggestions'] = performance_suggestions
        performance_data['cache_used'] = cache_used
    
    # Paginate results
    paginator = Paginator(results, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get recent searches for authenticated users
    recent_searches = []
    saved_searches = []
    if request.user.is_authenticated:
        recent_searches = SearchHistory.get_user_recent_searches(request.user, limit=5)
        saved_searches = SavedSearch.get_user_saved_searches(request.user)
    
    context = {
        'form': form,
        'query': query,
        'content_type': content_type,
        'sort_by': sort_by,
        'results': page_obj,
        'total_results': total_results,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'recent_searches': recent_searches,
        'saved_searches': saved_searches,
        'performance_data': performance_data,
    }
    
    return render(request, 'forums/search_results.html', context)

