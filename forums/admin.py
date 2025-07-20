from django.contrib import admin
from .models import Category, Subcategory, Thread, Post, Vote, Bookmark, SearchHistory, SavedSearch, SearchAnalytics


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_theme', 'order', 'subcategory_count', 'created_at')
    list_filter = ('color_theme', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')
    list_editable = ('order',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        ('Display Settings', {
            'fields': ('color_theme', 'icon', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def subcategory_count(self, obj):
        return obj.subcategories.count()
    subcategory_count.short_description = 'Subcategories'


class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 0
    prepopulated_fields = {'slug': ('name',)}
    fields = ('name', 'slug', 'description', 'member_count')
    readonly_fields = ('member_count',)


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'member_count', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description', 'category__name')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('category__order', 'category__name', 'name')
    
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'slug', 'description')
        }),
        ('Statistics', {
            'fields': ('member_count',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'member_count')


# Add inline to CategoryAdmin
CategoryAdmin.inlines = [SubcategoryInline]


class PostInline(admin.TabularInline):
    model = Post
    extra = 0
    fields = ('author', 'content', 'is_edited', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('created_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('author')


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'subcategory', 'author', 'post_count', 'view_count', 'is_pinned', 'is_locked', 'last_post_at')
    list_filter = ('subcategory__category', 'subcategory', 'is_pinned', 'is_locked', 'created_at')
    search_fields = ('title', 'author__display_name', 'author__email')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('-is_pinned', '-last_post_at')
    list_editable = ('is_pinned', 'is_locked')
    
    fieldsets = (
        (None, {
            'fields': ('subcategory', 'author', 'title', 'slug')
        }),
        ('Settings', {
            'fields': ('is_pinned', 'is_locked')
        }),
        ('Statistics', {
            'fields': ('view_count', 'post_count', 'last_post_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'post_count', 'last_post_at')
    inlines = [PostInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('subcategory__category', 'author')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('get_post_title', 'thread', 'author', 'vote_count', 'is_edited', 'created_at')
    list_filter = ('thread__subcategory__category', 'thread__subcategory', 'is_edited', 'created_at')
    search_fields = ('content', 'author__display_name', 'author__email', 'thread__title')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('thread', 'author', 'content')
        }),
        ('Statistics', {
            'fields': ('vote_count',),
            'classes': ('collapse',)
        }),
        ('Edit Information', {
            'fields': ('is_edited', 'edited_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'vote_count')
    
    def get_post_title(self, obj):
        """Display first 50 characters of post content as title."""
        return obj.content[:50] + ('...' if len(obj.content) > 50 else '')
    get_post_title.short_description = 'Post Content'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('thread__subcategory__category', 'author')


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_post_content', 'get_thread_title', 'created_at')
    list_filter = ('post__thread__subcategory__category', 'post__thread__subcategory', 'created_at')
    search_fields = ('user__display_name', 'user__email', 'post__content', 'post__thread__title')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'post')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def get_post_content(self, obj):
        """Display first 50 characters of post content."""
        return obj.post.content[:50] + ('...' if len(obj.post.content) > 50 else '')
    get_post_content.short_description = 'Post Content'
    
    def get_thread_title(self, obj):
        """Display the thread title."""
        return obj.post.thread.title
    get_thread_title.short_description = 'Thread'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'post__thread__subcategory__category')


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_thread_title', 'get_subcategory', 'created_at')
    list_filter = ('thread__subcategory__category', 'thread__subcategory', 'created_at')
    search_fields = ('user__display_name', 'user__email', 'thread__title')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'thread')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def get_thread_title(self, obj):
        """Display the thread title."""
        return obj.thread.title
    get_thread_title.short_description = 'Thread'
    
    def get_subcategory(self, obj):
        """Display the subcategory name."""
        return obj.thread.subcategory.name
    get_subcategory.short_description = 'Subcategory'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'thread__subcategory__category')


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'content_type', 'results_count', 'created_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('user__display_name', 'user__email', 'query')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'query', 'content_type', 'results_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(SearchAnalytics)
class SearchAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('get_user_display', 'query', 'content_type', 'results_count', 'search_time_ms', 'clicked_result_position', 'created_at')
    list_filter = ('content_type', 'sort_by', 'created_at', 'results_count')
    search_fields = ('query', 'normalized_query', 'user__display_name', 'user__email')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'normalized_query', 'session_key', 'user_agent', 'ip_address')
    
    fieldsets = (
        ('Search Information', {
            'fields': ('user', 'session_key', 'query', 'normalized_query', 'content_type', 'sort_by')
        }),
        ('Results & Performance', {
            'fields': ('results_count', 'search_time_ms', 'database_hits', 'page_number')
        }),
        ('User Behavior', {
            'fields': ('clicked_result_position', 'clicked_result_type', 'time_to_click_ms'),
            'classes': ('collapse',)
        }),
        ('Context Data', {
            'fields': ('user_agent', 'ip_address', 'referrer_url'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_user_display(self, obj):
        """Display user or session identifier."""
        if obj.user:
            return obj.user.display_name
        return f"Session: {obj.session_key[:8]}..."
    get_user_display.short_description = 'User/Session'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')
    
    def has_add_permission(self, request):
        """Disable manual addition - analytics are recorded automatically."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Allow viewing but not editing of analytics data."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion for data cleanup."""
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        """Disable manual addition - searches are recorded automatically."""
        return False


@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'query', 'content_type', 'is_active', 'last_used_at', 'created_at')
    list_filter = ('content_type', 'sort_by', 'is_active', 'created_at', 'last_used_at')
    search_fields = ('user__display_name', 'user__email', 'name', 'query')
    ordering = ('-updated_at',)
    date_hierarchy = 'created_at'
    list_editable = ('is_active',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'query')
        }),
        ('Search Settings', {
            'fields': ('content_type', 'sort_by', 'is_active')
        }),
        ('Usage Information', {
            'fields': ('last_used_at',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'last_used_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')
