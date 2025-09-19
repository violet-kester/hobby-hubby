from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from core.models import TimestampedModel

User = get_user_model()


class Category(TimestampedModel):
    HOBBY_CATEGORY_CHOICES = [
        ('creative-arts', 'Creative & Arts'),
        ('sports-fitness', 'Sports & Fitness'),
        ('games-entertainment', 'Games & Entertainment'),
        ('technology-science', 'Technology & Science'),
        ('food-culinary', 'Food & Culinary'),
        ('lifestyle-social', 'Lifestyle & Social'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    color_theme = models.CharField(max_length=20, choices=HOBBY_CATEGORY_CHOICES)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    order = models.IntegerField(default=0, help_text="Order for display sorting")
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'categories'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Subcategory(TimestampedModel):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField()
    member_count = models.IntegerField(default=0, help_text="Number of users following this subcategory")
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'subcategories'
        unique_together = [
            ('category', 'name'),
            ('category', 'slug'),
        ]
    
    def __str__(self):
        return f"{self.category.name} > {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Subcategory.objects.filter(
                category=self.category, 
                slug=slug
            ).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Thread(TimestampedModel):
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='threads')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='threads')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    is_pinned = models.BooleanField(default=False, help_text="Pinned threads appear at the top")
    is_locked = models.BooleanField(default=False, help_text="Locked threads cannot receive new posts")
    view_count = models.IntegerField(default=0, help_text="Number of times this thread has been viewed")
    post_count = models.IntegerField(default=0, help_text="Number of posts in this thread")
    last_post_at = models.DateTimeField(help_text="Timestamp of the most recent post")
    
    class Meta:
        ordering = ['-is_pinned', '-last_post_at']
        unique_together = [('subcategory', 'slug')]
        indexes = [
            models.Index(fields=['-is_pinned', '-last_post_at']),
            models.Index(fields=['subcategory', 'slug']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Thread.objects.filter(
                subcategory=self.subcategory, 
                slug=slug
            ).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Set last_post_at to created_at if this is a new thread
        if not self.pk and not self.last_post_at:
            self.last_post_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Return the absolute URL for this thread."""
        return f'/forums/{self.subcategory.category.slug}/{self.subcategory.slug}/{self.slug}/'


class Post(TimestampedModel):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    vote_count = models.IntegerField(default=0, help_text="Number of upvotes for this post")
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['thread', 'created_at']),
            models.Index(fields=['author', '-created_at']),
        ]
    
    def __str__(self):
        return f"Post by {self.author.display_name} in {self.thread.title}"


# Signals to update denormalized fields
@receiver(post_save, sender=Post)
def update_thread_on_post_save(sender, instance, created, **kwargs):
    """Update thread's post_count and last_post_at when a post is created."""
    if created:
        thread = instance.thread
        thread.post_count = thread.posts.count()
        thread.last_post_at = instance.created_at
        thread.save(update_fields=['post_count', 'last_post_at'])


@receiver(post_delete, sender=Post)
def update_thread_on_post_delete(sender, instance, **kwargs):
    """Update thread's post_count when a post is deleted."""
    thread = instance.thread
    thread.post_count = thread.posts.count()
    
    # Update last_post_at to the most recent remaining post
    latest_post = thread.posts.order_by('-created_at').first()
    if latest_post:
        thread.last_post_at = latest_post.created_at
    else:
        # If no posts remain, set to thread creation time
        thread.last_post_at = thread.created_at
    
    thread.save(update_fields=['post_count', 'last_post_at'])


class Vote(TimestampedModel):
    """Model for user votes on posts."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='votes')
    
    class Meta:
        ordering = ['-created_at']
        unique_together = [('user', 'post')]
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.display_name} voted on post in {self.post.thread.title}"


# Signals to update vote counts
@receiver(post_save, sender=Vote)
def update_post_vote_count_on_vote_save(sender, instance, created, **kwargs):
    """Update post's vote_count when a vote is created."""
    if created:
        post = instance.post
        post.vote_count = post.votes.count()
        post.save(update_fields=['vote_count'])


@receiver(post_delete, sender=Vote)
def update_post_vote_count_on_vote_delete(sender, instance, **kwargs):
    """Update post's vote_count when a vote is deleted."""
    post = instance.post
    post.vote_count = post.votes.count()
    post.save(update_fields=['vote_count'])


class Bookmark(TimestampedModel):
    """Model for user bookmarks on threads."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='bookmarks')
    
    class Meta:
        ordering = ['-created_at']
        unique_together = [('user', 'thread')]
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.display_name} bookmarked {self.thread.title}"


class SearchHistory(TimestampedModel):
    """Model for tracking user search history."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    query = models.CharField(max_length=200, help_text="The search query text")
    content_type = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Content'),
            ('posts', 'Posts'),
            ('threads', 'Threads'),
            ('users', 'Users'),
            ('categories', 'Categories'),
        ],
        default='all',
        help_text="Type of content searched"
    )
    results_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of results returned for this search"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Search History'
        verbose_name_plural = 'Search Histories'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['query', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.display_name} searched for '{self.query}'"
    
    @classmethod
    def record_search(cls, user, query, content_type='all', results_count=0):
        """
        Record a search in history, avoiding duplicates for recent searches.
        
        Args:
            user: User who performed the search
            query: Search query string
            content_type: Type of content searched
            results_count: Number of results returned
            
        Returns:
            SearchHistory instance
        """
        if not user.is_authenticated or not query.strip():
            return None
        
        # Clean the query
        query = query.strip()[:200]
        
        # Check for recent duplicate search (within last hour)
        from django.utils import timezone
        from datetime import timedelta
        
        recent_cutoff = timezone.now() - timedelta(hours=1)
        recent_search = cls.objects.filter(
            user=user,
            query=query,
            content_type=content_type,
            created_at__gte=recent_cutoff
        ).first()
        
        if recent_search:
            # Update the existing search timestamp and results count
            recent_search.results_count = results_count
            recent_search.save(update_fields=['results_count', 'updated_at'])
            return recent_search
        
        # Create new search history entry
        return cls.objects.create(
            user=user,
            query=query,
            content_type=content_type,
            results_count=results_count
        )
    
    @classmethod
    def get_user_recent_searches(cls, user, limit=10):
        """
        Get recent unique search queries for a user.
        
        Args:
            user: User to get searches for
            limit: Maximum number of searches to return
            
        Returns:
            QuerySet of recent SearchHistory objects
        """
        if not user.is_authenticated:
            return cls.objects.none()
        
        return cls.objects.filter(user=user).order_by('-created_at')[:limit]
    
    @classmethod
    def get_popular_searches(cls, limit=10):
        """
        Get most popular search queries across all users.
        
        Args:
            limit: Maximum number of searches to return
            
        Returns:
            List of dicts with query and search_count
        """
        from django.db.models import Count
        
        return cls.objects.values('query').annotate(
            search_count=Count('id')
        ).order_by('-search_count')[:limit]


class SavedSearch(TimestampedModel):
    """Model for user-saved search queries."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(
        max_length=100,
        help_text="User-defined name for this saved search"
    )
    query = models.CharField(max_length=200, help_text="The search query text")
    content_type = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Content'),
            ('posts', 'Posts'),
            ('threads', 'Threads'),
            ('users', 'Users'),
            ('categories', 'Categories'),
        ],
        default='all',
        help_text="Type of content to search"
    )
    sort_by = models.CharField(
        max_length=20,
        choices=[
            ('relevance', 'Relevance'),
            ('date_desc', 'Newest First'),
            ('date_asc', 'Oldest First'),
            ('author', 'Author A-Z'),
        ],
        default='relevance',
        help_text="Default sort order for this search"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this saved search is active"
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this saved search was last used"
    )
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = [('user', 'name')]
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['user', 'is_active', '-updated_at']),
            models.Index(fields=['-last_used_at']),
        ]
    
    def __str__(self):
        return f"{self.user.display_name}'s saved search: {self.name}"
    
    def get_search_url(self):
        """Generate URL for this saved search."""
        from django.urls import reverse
        from urllib.parse import urlencode
        
        params = {
            'query': self.query,
            'content_type': self.content_type,
            'sort_by': self.sort_by,
        }
        return f"{reverse('forums:search')}?{urlencode(params)}"
    
    def mark_as_used(self):
        """Mark this saved search as recently used."""
        from django.utils import timezone
        
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])
    
    @classmethod
    def get_user_saved_searches(cls, user):
        """
        Get active saved searches for a user.
        
        Args:
            user: User to get saved searches for
            
        Returns:
            QuerySet of active SavedSearch objects
        """
        if not user.is_authenticated:
            return cls.objects.none()
        
        return cls.objects.filter(
            user=user,
            is_active=True
        ).order_by('-last_used_at', '-updated_at')


class SearchAnalytics(TimestampedModel):
    """Model for tracking detailed search analytics and performance metrics."""
    
    # Search session tracking
    session_key = models.CharField(
        max_length=40,
        help_text="Session key for anonymous users or session-based tracking"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='search_analytics',
        help_text="Associated user if authenticated"
    )
    
    # Search details
    query = models.CharField(max_length=200, help_text="The search query text")
    normalized_query = models.CharField(
        max_length=200,
        help_text="Normalized query for analytics (lowercase, stemmed)"
    )
    content_type = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Content'),
            ('posts', 'Posts'),
            ('threads', 'Threads'),
            ('users', 'Users'),
            ('categories', 'Categories'),
        ],
        default='all',
        help_text="Type of content searched"
    )
    sort_by = models.CharField(
        max_length=20,
        choices=[
            ('relevance', 'Relevance'),
            ('date_desc', 'Newest First'),
            ('date_asc', 'Oldest First'),
            ('author', 'Author A-Z'),
        ],
        default='relevance',
        help_text="Sort order used"
    )
    
    # Results and performance metrics
    results_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of results returned"
    )
    search_time_ms = models.PositiveIntegerField(
        default=0,
        help_text="Time taken to execute search in milliseconds"
    )
    database_hits = models.PositiveIntegerField(
        default=1,
        help_text="Number of database queries executed"
    )
    
    # User behavior tracking
    clicked_result_position = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Position of clicked result (1-based), null if no click"
    )
    clicked_result_type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Type of content that was clicked"
    )
    time_to_click_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Time from search to click in milliseconds"
    )
    
    # Context information
    page_number = models.PositiveIntegerField(
        default=1,
        help_text="Page number viewed (for pagination analysis)"
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        help_text="User agent string for device/browser analytics"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address for geographic analytics (anonymized)"
    )
    referrer_url = models.URLField(
        blank=True,
        help_text="Referring URL that led to search"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Search Analytics'
        verbose_name_plural = 'Search Analytics'
        indexes = [
            models.Index(fields=['query', '-created_at']),
            models.Index(fields=['normalized_query', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['session_key', '-created_at']),
            models.Index(fields=['content_type', '-created_at']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['results_count', '-created_at']),
        ]
    
    def __str__(self):
        user_identifier = self.user.display_name if self.user else f"Session:{self.session_key[:8]}"
        return f"{user_identifier} searched for '{self.query}' ({self.results_count} results)"
    
    @classmethod
    def record_search_analytics(cls, request, query, content_type='all', sort_by='relevance', 
                               results_count=0, search_time_ms=0, database_hits=1):
        """
        Record detailed search analytics.
        
        Args:
            request: HTTP request object
            query: Search query string
            content_type: Type of content searched
            sort_by: Sort order used
            results_count: Number of results returned
            search_time_ms: Time taken for search
            database_hits: Number of database queries
            
        Returns:
            SearchAnalytics instance
        """
        if not query.strip():
            return None
        
        # Get session key
        if not hasattr(request, 'session'):
            return None
        
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        # Normalize query for analytics
        normalized_query = cls._normalize_query(query)
        
        # Get user agent and IP (with privacy considerations)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        ip_address = cls._get_client_ip(request)
        referrer_url = request.META.get('HTTP_REFERER', '')[:200]
        
        return cls.objects.create(
            session_key=session_key,
            user=request.user if request.user.is_authenticated else None,
            query=query.strip()[:200],
            normalized_query=normalized_query,
            content_type=content_type,
            sort_by=sort_by,
            results_count=results_count,
            search_time_ms=search_time_ms,
            database_hits=database_hits,
            user_agent=user_agent,
            ip_address=ip_address,
            referrer_url=referrer_url
        )
    
    @classmethod
    def record_result_click(cls, analytics_id, position, result_type, time_to_click_ms=None):
        """
        Record when a user clicks on a search result.
        
        Args:
            analytics_id: ID of the SearchAnalytics entry
            position: Position of clicked result (1-based)
            result_type: Type of content clicked
            time_to_click_ms: Time from search to click
        """
        try:
            analytics = cls.objects.get(id=analytics_id)
            analytics.clicked_result_position = position
            analytics.clicked_result_type = result_type
            analytics.time_to_click_ms = time_to_click_ms
            analytics.save(update_fields=[
                'clicked_result_position', 
                'clicked_result_type', 
                'time_to_click_ms'
            ])
            return analytics
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_search_trends(cls, days=30, limit=10):
        """
        Get search trends over specified time period.
        
        Args:
            days: Number of days to analyze
            limit: Maximum number of trends to return
            
        Returns:
            List of search trends with counts
        """
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        
        since_date = timezone.now() - timedelta(days=days)
        
        return cls.objects.filter(
            created_at__gte=since_date
        ).values('normalized_query').annotate(
            search_count=Count('id'),
            avg_results=models.Avg('results_count'),
            avg_time_ms=models.Avg('search_time_ms')
        ).order_by('-search_count')[:limit]
    
    @classmethod 
    def get_performance_metrics(cls, days=7):
        """
        Get search performance metrics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with performance statistics
        """
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Avg, Count, Q
        
        since_date = timezone.now() - timedelta(days=days)
        
        analytics = cls.objects.filter(created_at__gte=since_date)
        
        if not analytics.exists():
            return {}
        
        metrics = analytics.aggregate(
            total_searches=Count('id'),
            avg_search_time=Avg('search_time_ms'),
            avg_results_count=Avg('results_count'),
            avg_database_hits=Avg('database_hits'),
            zero_result_count=Count('id', filter=Q(results_count=0)),
            clicked_searches=Count('id', filter=Q(clicked_result_position__isnull=False)),
        )
        
        # Calculate derived metrics
        if metrics['total_searches'] > 0:
            metrics['zero_result_rate'] = (
                metrics['zero_result_count'] / metrics['total_searches']
            ) * 100
            metrics['click_through_rate'] = (
                metrics['clicked_searches'] / metrics['total_searches']
            ) * 100
        else:
            metrics['zero_result_rate'] = 0
            metrics['click_through_rate'] = 0
        
        return metrics
    
    @staticmethod
    def _normalize_query(query):
        """Normalize query for analytics (lowercase, basic stemming)."""
        import re
        
        # Convert to lowercase and remove extra whitespace
        normalized = re.sub(r'\s+', ' ', query.lower().strip())
        
        # Basic stemming - remove common suffixes
        # This is a simple implementation; for production, consider using nltk or similar
        suffixes = ['ing', 'ed', 's', 'er', 'est', 'ly']
        words = normalized.split()
        stemmed_words = []
        
        for word in words:
            original_word = word
            for suffix in suffixes:
                if word.endswith(suffix) and len(word) > len(suffix) + 2:
                    word = word[:-len(suffix)]
                    break
            stemmed_words.append(word)
        
        return ' '.join(stemmed_words)[:200]
    
    @staticmethod
    def _get_client_ip(request):
        """Get client IP address with privacy considerations."""
        # Get IP from various headers (considering proxies)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Anonymize IP for privacy (remove last octet for IPv4)
        if ip and '.' in ip:
            parts = ip.split('.')
            if len(parts) == 4:
                return '.'.join(parts[:3] + ['0'])
        
        return ip
