from django.urls import path
from . import views
from . import api_views

app_name = 'forums'

urlpatterns = [
    path('', views.CategoryListView.as_view(), name='category_list'),
    path('search/', views.search_view, name='search'),
    path('search/suggestions/', views.search_suggestions_view, name='search_suggestions'),
    path('<slug:category_slug>/<slug:subcategory_slug>/', 
         views.SubcategoryDetailView.as_view(), name='subcategory_detail'),
    path('<slug:category_slug>/<slug:subcategory_slug>/new/', 
         views.thread_create, name='thread_create'),
    path('<slug:category_slug>/<slug:subcategory_slug>/<slug:thread_slug>/', 
         views.ThreadDetailView.as_view(), name='thread_detail'),
    path('<slug:category_slug>/<slug:subcategory_slug>/<slug:thread_slug>/reply/', 
         views.post_create, name='post_create'),
    path('preview/', views.preview_content, name='preview_content'),
    path('vote/<int:post_id>/', views.vote_post, name='vote_post'),
    path('bookmark/<int:thread_id>/', views.bookmark_thread, name='bookmark_thread'),
    path('search/save/', views.save_search_view, name='save_search'),
    path('search/saved/', views.saved_searches_view, name='saved_searches'),
    path('search/saved/<int:search_id>/delete/', views.delete_saved_search_view, name='delete_saved_search'),
    path('search/history/', views.search_history_view, name='search_history'),
    path('search/history/clear/', views.clear_search_history_view, name='clear_search_history'),
    path('admin/analytics/', views.search_analytics_dashboard, name='analytics_dashboard'),
    path('admin/analytics/api/', views.search_analytics_api, name='analytics_api'),
    path('search/optimized/', views.optimized_search_view, name='optimized_search'),
    path('search/enhanced/', views.enhanced_search_view, name='enhanced_search'),
    
    # API Endpoints for Mobile Integration
    path('api/search/', api_views.api_search, name='api_search'),
    path('api/search/suggestions/', api_views.api_search_suggestions, name='api_search_suggestions'),
    path('api/search/analytics/', api_views.api_search_analytics, name='api_search_analytics'),
]