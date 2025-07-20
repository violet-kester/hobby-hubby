"""
API Views for Search Functionality - Mobile Integration Support

This module provides REST API endpoints for mobile apps and third-party integrations
to access the search functionality of the Hobby Hubby forum.

Author: Claude (Shakespearean Assistant)
"""

import time
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Category, Thread, SearchAnalytics
from .views import (
    perform_unified_search, search_posts, search_threads, search_users, 
    search_categories, SearchRankingEngine
)

User = get_user_model()


@csrf_exempt
def api_search(request):
    """
    REST API endpoint for search functionality.
    
    Supports both GET and POST requests.
    Returns JSON with search results optimized for mobile apps.
    
    Parameters:
    - query (required): Search query string (min 2 characters)
    - content_type: 'all', 'posts', 'threads', 'users', 'categories' (default: 'all')
    - sort_by: 'relevance', 'date_desc', 'date_asc', 'author' (default: 'relevance')
    - limit: Number of results (max 100, default: 20)
    - offset: Pagination offset (default: 0)
    - date_from: ISO format date filter (optional)
    - date_to: ISO format date filter (optional)
    - author: Author filter (optional)
    - category: Category slug filter (optional)
    
    Returns:
    JSON response with search results, pagination info, and metadata
    """
    if request.method not in ['GET', 'POST']:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Parse parameters from GET or POST
    if request.method == 'GET':
        params = request.GET
    else:
        if request.content_type == 'application/json':
            try:
                params = json.loads(request.body)
            except (json.JSONDecodeError, ValueError):
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
        else:
            params = request.POST
    
    # Validate required parameters
    query = params.get('query', '').strip()
    if not query:
        return JsonResponse({'error': 'Query parameter is required'}, status=400)
    
    if len(query) < 2:
        return JsonResponse({'error': 'Query must be at least 2 characters'}, status=400)
    
    # Parse optional parameters
    content_type = params.get('content_type', 'all')
    sort_by = params.get('sort_by', 'relevance')
    limit = min(int(params.get('limit', 20)), 100)  # Max 100 results
    offset = max(int(params.get('offset', 0)), 0)
    
    # Date range filters
    date_from = params.get('date_from')
    date_to = params.get('date_to')
    author = params.get('author', '').strip()
    category_slug = params.get('category')
    
    # Build filters
    filters = {}
    if date_from:
        try:
            filters['date_from'] = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except ValueError:
            return JsonResponse({'error': 'Invalid date_from format (use ISO format)'}, status=400)
    
    if date_to:
        try:
            filters['date_to'] = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            return JsonResponse({'error': 'Invalid date_to format (use ISO format)'}, status=400)
    
    if author:
        filters['author'] = author
    
    if category_slug:
        try:
            category = Category.objects.get(slug=category_slug)
            filters['category'] = category
        except Category.DoesNotExist:
            return JsonResponse({'error': 'Category not found'}, status=404)
    
    # Perform search
    start_time = time.time()
    try:
        if content_type == 'all':
            raw_results = perform_unified_search(query, sort_by, filters)
        elif content_type == 'posts':
            raw_results = search_posts(query, sort_by, filters)
        elif content_type == 'threads':
            raw_results = search_threads(query, sort_by, filters)
        elif content_type == 'users':
            raw_results = search_users(query, sort_by, filters)
        elif content_type == 'categories':
            raw_results = search_categories(query, sort_by, filters)
        else:
            return JsonResponse({'error': 'Invalid content_type'}, status=400)
        
        # Apply enhanced ranking
        ranking_engine = SearchRankingEngine()
        ranked_results = ranking_engine.rank_search_results(
            'unified',  # Content type for API
            raw_results,
            query,
            content_type
        )
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
    except Exception as e:
        return JsonResponse({'error': f'Search failed: {str(e)}'}, status=500)
    
    # Apply pagination
    total_results = len(ranked_results)
    paginated_results = ranked_results[offset:offset + limit]
    
    # Format results for API
    api_results = []
    for result in paginated_results:
        api_result = {
            'id': getattr(result.get('obj'), 'id', None) if hasattr(result.get('obj', {}), 'id') else None,
            'type': result['type'],
            'title': result['title'],
            'content': result['content'],
            'url': result['url'],
            'relevance_score': float(result.get('rank', 0)),
            'category': result.get('category'),
            'subcategory': result.get('subcategory'),
            'created_at': result['date'].isoformat() if result.get('date') else None,
        }
        
        # Add author information
        if result.get('author'):
            api_result['author'] = {
                'id': result['author'].id,
                'display_name': result['author'].display_name,
                'profile_url': f'/accounts/user/{result["author"].id}/'
            }
        else:
            api_result['author'] = None
        
        # Add type-specific metadata
        if result['type'] == 'thread':
            if hasattr(result.get('obj'), 'post_count'):
                api_result['metadata'] = {
                    'post_count': result['obj'].post_count,
                    'view_count': getattr(result['obj'], 'view_count', 0),
                    'is_pinned': getattr(result['obj'], 'is_pinned', False),
                    'is_locked': getattr(result['obj'], 'is_locked', False)
                }
        elif result['type'] == 'user':
            if result.get('author'):
                api_result['metadata'] = {
                    'location': getattr(result['author'], 'location', None),
                    'join_date': result['author'].date_joined.isoformat()
                }
        
        api_results.append(api_result)
    
    # Track search for analytics (if user is authenticated or session available)
    session_key = request.session.session_key or 'anonymous'
    user = request.user if request.user.is_authenticated else None
    
    # Create analytics record
    try:
        SearchAnalytics.objects.create(
            session_key=session_key[:40],  # Ensure it fits in the field
            user=user,
            query=query[:200],
            normalized_query=query.lower().strip()[:200],
            search_time_ms=search_time_ms,
            results_count=total_results,
            content_type=content_type,
            clicked_result_position=0,  # Will be updated by click tracking
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            ip_address=request.META.get('REMOTE_ADDR', '')[:45],
            request_path='/api/search/',
            filters_used=bool(filters),
            source='api'
        )
    except Exception:
        pass  # Don't fail search if analytics fails
    
    # Build response
    response_data = {
        'success': True,
        'query': query,
        'content_type': content_type,
        'sort_by': sort_by,
        'total_results': total_results,
        'returned_results': len(api_results),
        'offset': offset,
        'limit': limit,
        'search_time_ms': search_time_ms,
        'results': api_results,
        'pagination': {
            'has_next': offset + limit < total_results,
            'has_previous': offset > 0,
            'next_offset': offset + limit if offset + limit < total_results else None,
            'previous_offset': max(0, offset - limit) if offset > 0 else None,
            'page_size': limit,
            'total_pages': (total_results + limit - 1) // limit
        }
    }
    
    return JsonResponse(response_data)


@csrf_exempt
def api_search_suggestions(request):
    """
    API endpoint for search suggestions/autocomplete.
    Returns JSON with search suggestions optimized for mobile typing.
    
    Parameters:
    - q (required): Partial query string for suggestions (min 2 characters)
    - limit: Number of suggestions (max 20, default: 10)
    
    Returns:
    JSON response with suggestion list
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'suggestions': []})
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    limit = min(int(request.GET.get('limit', 10)), 20)  # Max 20 suggestions
    
    try:
        suggestions = []
        
        # Get thread suggestions
        thread_q = Q(title__icontains=query)
        threads = Thread.objects.filter(thread_q).select_related(
            'subcategory__category'
        ).order_by('-view_count')[:limit//2]
        
        for thread in threads:
            suggestions.append({
                'type': 'thread',
                'text': thread.title,
                'description': f'in {thread.subcategory.category.name} / {thread.subcategory.name}',
                'url': thread.get_absolute_url(),
                'metadata': {
                    'post_count': thread.post_count,
                    'view_count': thread.view_count
                }
            })
        
        # Get user suggestions
        user_q = Q(display_name__icontains=query) & Q(is_active=True)
        users = User.objects.filter(user_q)[:limit//4]
        
        for user in users:
            suggestions.append({
                'type': 'user',
                'text': user.display_name,
                'description': f'User • {user.location or "Location unknown"}',
                'url': f'/accounts/user/{user.id}/',
                'metadata': {
                    'join_date': user.date_joined.isoformat()
                }
            })
        
        # Get category suggestions
        category_q = Q(name__icontains=query)
        categories = Category.objects.filter(category_q)[:limit//4]
        
        for category in categories:
            suggestions.append({
                'type': 'category',
                'text': category.name,
                'description': f'Category • {category.description[:50]}...' if category.description else 'Category',
                'url': f'/forums/{category.slug}/',
                'metadata': {
                    'subcategory_count': category.subcategories.count()
                }
            })
        
        # Limit total suggestions
        suggestions = suggestions[:limit]
        
        return JsonResponse({
            'suggestions': suggestions,
            'query': query,
            'total': len(suggestions)
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Suggestions failed: {str(e)}'}, status=500)


def api_search_analytics(request):
    """
    API endpoint for search analytics data.
    Requires staff permissions.
    
    Parameters:
    - days: Number of days to include in analytics (default: 7)
    
    Returns:
    JSON response with analytics metrics
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff access required'}, status=403)
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Parse time range
    days = int(request.GET.get('days', 7))
    since_date = timezone.now() - timedelta(days=days)
    
    try:
        # Get basic metrics
        total_searches = SearchAnalytics.objects.filter(
            created_at__gte=since_date
        ).count()
        
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
            avg_database_hits=Avg('database_hits')
        )
        
        # Click-through rate
        clicked_searches = SearchAnalytics.objects.filter(
            created_at__gte=since_date,
            clicked_result_position__gt=0
        ).count()
        
        click_through_rate = (clicked_searches / total_searches * 100) if total_searches > 0 else 0
        
        # Zero result rate
        zero_result_searches = SearchAnalytics.objects.filter(
            created_at__gte=since_date,
            results_count=0
        ).count()
        
        zero_result_rate = (zero_result_searches / total_searches * 100) if total_searches > 0 else 0
        
        # Top queries
        top_queries = SearchAnalytics.objects.filter(
            created_at__gte=since_date
        ).values('normalized_query').annotate(
            search_count=Count('id'),
            avg_results=Avg('results_count'),
            avg_time_ms=Avg('search_time_ms')
        ).order_by('-search_count')[:10]
        
        # Content type distribution
        content_type_stats = SearchAnalytics.objects.filter(
            created_at__gte=since_date
        ).values('content_type').annotate(
            search_count=Count('id')
        ).order_by('-search_count')
        
        return JsonResponse({
            'success': True,
            'period_days': days,
            'metrics': {
                'total_searches': total_searches,
                'unique_users': unique_users,
                'unique_sessions': unique_sessions,
                'click_through_rate': round(click_through_rate, 2),
                'zero_result_rate': round(zero_result_rate, 2),
                'performance': {
                    'avg_search_time_ms': round(performance_metrics['avg_search_time'] or 0, 2),
                    'avg_results_count': round(performance_metrics['avg_results_count'] or 0, 2),
                    'avg_database_hits': round(performance_metrics['avg_database_hits'] or 0, 2)
                }
            },
            'top_queries': list(top_queries),
            'content_type_distribution': list(content_type_stats)
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Analytics failed: {str(e)}'}, status=500)