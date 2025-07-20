"""
Tests for search history and saved searches functionality.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from forums.models import SearchHistory, SavedSearch, Category, Subcategory

User = get_user_model()


class SearchHistoryModelTests(TestCase):
    """Tests for SearchHistory model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            display_name='TestUser'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            display_name='OtherUser'
        )
    
    def test_search_history_creation(self):
        """Test basic search history creation."""
        search = SearchHistory.objects.create(
            user=self.user,
            query='Django testing',
            content_type='all',
            results_count=5
        )
        
        self.assertEqual(search.user, self.user)
        self.assertEqual(search.query, 'Django testing')
        self.assertEqual(search.content_type, 'all')
        self.assertEqual(search.results_count, 5)
        self.assertIsNotNone(search.created_at)
    
    def test_search_history_str_representation(self):
        """Test string representation of SearchHistory."""
        search = SearchHistory.objects.create(
            user=self.user,
            query='Python programming',
            content_type='posts'
        )
        
        expected = f"{self.user.display_name} searched for 'Python programming'"
        self.assertEqual(str(search), expected)
    
    def test_record_search_basic(self):
        """Test basic search recording functionality."""
        search = SearchHistory.record_search(
            user=self.user,
            query='JavaScript tutorials',
            content_type='threads',
            results_count=10
        )
        
        self.assertIsNotNone(search)
        self.assertEqual(search.user, self.user)
        self.assertEqual(search.query, 'JavaScript tutorials')
        self.assertEqual(search.content_type, 'threads')
        self.assertEqual(search.results_count, 10)
    
    def test_record_search_unauthenticated_user(self):
        """Test search recording with unauthenticated user."""
        from django.contrib.auth.models import AnonymousUser
        
        result = SearchHistory.record_search(
            user=AnonymousUser(),
            query='test query',
            content_type='all',
            results_count=5
        )
        
        self.assertIsNone(result)
        self.assertEqual(SearchHistory.objects.count(), 0)
    
    def test_record_search_empty_query(self):
        """Test search recording with empty query."""
        result = SearchHistory.record_search(
            user=self.user,
            query='',
            content_type='all',
            results_count=0
        )
        
        self.assertIsNone(result)
        self.assertEqual(SearchHistory.objects.count(), 0)
    
    def test_record_search_whitespace_query(self):
        """Test search recording with whitespace-only query."""
        result = SearchHistory.record_search(
            user=self.user,
            query='   ',
            content_type='all',
            results_count=0
        )
        
        self.assertIsNone(result)
        self.assertEqual(SearchHistory.objects.count(), 0)
    
    def test_record_search_duplicate_recent(self):
        """Test search recording with recent duplicate query."""
        # Create initial search
        search1 = SearchHistory.record_search(
            user=self.user,
            query='React hooks',
            content_type='all',
            results_count=3
        )
        
        # Record same search again (should update existing)
        search2 = SearchHistory.record_search(
            user=self.user,
            query='React hooks',
            content_type='all',
            results_count=5
        )
        
        # Should be the same object, updated
        self.assertEqual(search1.id, search2.id)
        self.assertEqual(search2.results_count, 5)
        self.assertEqual(SearchHistory.objects.count(), 1)
    
    def test_record_search_old_duplicate(self):
        """Test search recording with old duplicate query."""
        # Create old search (more than 1 hour ago)
        old_time = timezone.now() - timedelta(hours=2)
        old_search = SearchHistory.objects.create(
            user=self.user,
            query='Vue.js components',
            content_type='all',
            results_count=2
        )
        # Update the created_at manually using queryset update
        SearchHistory.objects.filter(id=old_search.id).update(created_at=old_time)
        
        # Record same search again (should create new entry)
        new_search = SearchHistory.record_search(
            user=self.user,
            query='Vue.js components',
            content_type='all',
            results_count=8
        )
        
        # Should create new entry
        self.assertEqual(SearchHistory.objects.count(), 2)
        self.assertEqual(new_search.results_count, 8)
    
    def test_record_search_long_query(self):
        """Test search recording with long query gets truncated."""
        long_query = 'a' * 250  # Longer than 200 character limit
        
        search = SearchHistory.record_search(
            user=self.user,
            query=long_query,
            content_type='all',
            results_count=1
        )
        
        self.assertEqual(len(search.query), 200)
        self.assertEqual(search.query, 'a' * 200)
    
    def test_get_user_recent_searches(self):
        """Test getting recent searches for a user."""
        # Create multiple searches
        queries = ['Python', 'Django', 'JavaScript', 'React', 'Vue']
        for query in queries:
            SearchHistory.record_search(
                user=self.user,
                query=query,
                content_type='all',
                results_count=1
            )
        
        # Get recent searches
        recent = SearchHistory.get_user_recent_searches(self.user, limit=3)
        
        self.assertEqual(len(recent), 3)
        # Should be in reverse chronological order
        self.assertEqual(recent[0].query, 'Vue')
        self.assertEqual(recent[1].query, 'React')
        self.assertEqual(recent[2].query, 'JavaScript')
    
    def test_get_user_recent_searches_unauthenticated(self):
        """Test getting recent searches for unauthenticated user."""
        from django.contrib.auth.models import AnonymousUser
        
        recent = SearchHistory.get_user_recent_searches(AnonymousUser())
        
        self.assertEqual(len(recent), 0)
    
    def test_get_popular_searches(self):
        """Test getting popular search queries."""
        # Create searches from multiple users
        popular_queries = ['Python', 'Python', 'Django', 'Python', 'JavaScript']
        users = [self.user, self.other_user, self.user, self.other_user, self.user]
        
        for query, user in zip(popular_queries, users):
            SearchHistory.objects.create(
                user=user,
                query=query,
                content_type='all',
                results_count=1
            )
        
        popular = SearchHistory.get_popular_searches(limit=3)
        
        self.assertEqual(len(popular), 3)
        self.assertEqual(popular[0]['query'], 'Python')
        self.assertEqual(popular[0]['search_count'], 3)
        self.assertEqual(popular[1]['query'], 'Django')
        self.assertEqual(popular[1]['search_count'], 1)


class SavedSearchModelTests(TestCase):
    """Tests for SavedSearch model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            display_name='TestUser'
        )
    
    def test_saved_search_creation(self):
        """Test basic saved search creation."""
        saved_search = SavedSearch.objects.create(
            user=self.user,
            name='My Python Search',
            query='Python tutorials',
            content_type='threads',
            sort_by='date_desc'
        )
        
        self.assertEqual(saved_search.user, self.user)
        self.assertEqual(saved_search.name, 'My Python Search')
        self.assertEqual(saved_search.query, 'Python tutorials')
        self.assertEqual(saved_search.content_type, 'threads')
        self.assertEqual(saved_search.sort_by, 'date_desc')
        self.assertTrue(saved_search.is_active)
        self.assertIsNone(saved_search.last_used_at)
    
    def test_saved_search_str_representation(self):
        """Test string representation of SavedSearch."""
        saved_search = SavedSearch.objects.create(
            user=self.user,
            name='Django Search',
            query='Django models',
            content_type='all'
        )
        
        expected = f"{self.user.display_name}'s saved search: Django Search"
        self.assertEqual(str(saved_search), expected)
    
    def test_get_search_url(self):
        """Test URL generation for saved search."""
        saved_search = SavedSearch.objects.create(
            user=self.user,
            name='Test Search',
            query='Django REST',
            content_type='posts',
            sort_by='relevance'
        )
        
        url = saved_search.get_search_url()
        
        self.assertIn('/forums/search/', url)
        self.assertIn('query=Django+REST', url)
        self.assertIn('content_type=posts', url)
        self.assertIn('sort_by=relevance', url)
    
    def test_mark_as_used(self):
        """Test marking saved search as used."""
        saved_search = SavedSearch.objects.create(
            user=self.user,
            name='Test Search',
            query='Vue components',
            content_type='all'
        )
        
        # Initially no last_used_at
        self.assertIsNone(saved_search.last_used_at)
        
        # Mark as used
        saved_search.mark_as_used()
        saved_search.refresh_from_db()
        
        # Should now have last_used_at timestamp
        self.assertIsNotNone(saved_search.last_used_at)
    
    def test_get_user_saved_searches(self):
        """Test getting saved searches for a user."""
        # Create multiple saved searches
        searches_data = [
            ('Recent Search', 'React hooks', True),
            ('Old Search', 'jQuery plugins', True),
            ('Inactive Search', 'Angular directives', False),
        ]
        
        saved_searches = []
        for name, query, is_active in searches_data:
            search = SavedSearch.objects.create(
                user=self.user,
                name=name,
                query=query,
                content_type='all',
                is_active=is_active
            )
            saved_searches.append(search)
        
        # Mark one as used
        saved_searches[1].mark_as_used()
        
        # Get user's saved searches
        user_searches = SavedSearch.get_user_saved_searches(self.user)
        
        # Should only return active searches, ordered by last_used_at desc
        self.assertEqual(len(user_searches), 2)
        self.assertEqual(user_searches[0].name, 'Old Search')  # Most recently used
        self.assertEqual(user_searches[1].name, 'Recent Search')  # Never used
    
    def test_get_user_saved_searches_unauthenticated(self):
        """Test getting saved searches for unauthenticated user."""
        from django.contrib.auth.models import AnonymousUser
        
        searches = SavedSearch.get_user_saved_searches(AnonymousUser())
        
        self.assertEqual(len(searches), 0)
    
    def test_unique_name_constraint(self):
        """Test that user cannot have duplicate saved search names."""
        SavedSearch.objects.create(
            user=self.user,
            name='My Search',
            query='first query',
            content_type='all'
        )
        
        # Should raise integrity error for duplicate name
        with self.assertRaises(Exception):
            SavedSearch.objects.create(
                user=self.user,
                name='My Search',
                query='second query',
                content_type='all'
            )


class SearchHistoryViewTests(TestCase):
    """Tests for search history and saved search views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            display_name='TestUser'
        )
        
        # Create test search history
        SearchHistory.objects.create(
            user=self.user,
            query='Python testing',
            content_type='posts',
            results_count=5
        )
    
    def test_save_search_view_success(self):
        """Test successful search saving."""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.post(
            reverse('forums:save_search'),
            {
                'name': 'My Test Search',
                'query': 'Django models',
                'content_type': 'threads',
                'sort_by': 'date_desc'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('saved successfully', data['message'])
        
        # Check saved search was created
        saved_search = SavedSearch.objects.get(user=self.user, name='My Test Search')
        self.assertEqual(saved_search.query, 'Django models')
        self.assertEqual(saved_search.content_type, 'threads')
    
    def test_save_search_view_duplicate_name(self):
        """Test saving search with duplicate name."""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Create existing saved search
        SavedSearch.objects.create(
            user=self.user,
            name='Existing Search',
            query='first query',
            content_type='all'
        )
        
        # Try to create another with same name
        response = self.client.post(
            reverse('forums:save_search'),
            {
                'name': 'Existing Search',
                'query': 'second query',
                'content_type': 'all',
                'sort_by': 'relevance'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('already have a saved search', data['error'])
    
    def test_save_search_view_missing_name(self):
        """Test saving search without name."""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.post(
            reverse('forums:save_search'),
            {
                'query': 'Django models',
                'content_type': 'all'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('Search name is required', data['error'])
    
    def test_save_search_view_requires_ajax(self):
        """Test that save search view requires AJAX."""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.post(
            reverse('forums:save_search'),
            {
                'name': 'Test',
                'query': 'Django',
                'content_type': 'all'
            }
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_delete_saved_search_view_success(self):
        """Test successful saved search deletion."""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Create saved search
        saved_search = SavedSearch.objects.create(
            user=self.user,
            name='To Delete',
            query='test query',
            content_type='all'
        )
        
        response = self.client.post(
            reverse('forums:delete_saved_search', args=[saved_search.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('deleted successfully', data['message'])
        
        # Check search was deleted
        self.assertFalse(SavedSearch.objects.filter(id=saved_search.id).exists())
    
    def test_delete_saved_search_view_unauthorized(self):
        """Test deleting another user's saved search."""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Create saved search for different user
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            display_name='OtherUser'
        )
        saved_search = SavedSearch.objects.create(
            user=other_user,
            name='Other User Search',
            query='test query',
            content_type='all'
        )
        
        response = self.client.post(
            reverse('forums:delete_saved_search', args=[saved_search.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_saved_searches_view(self):
        """Test saved searches management view."""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Create some saved searches
        SavedSearch.objects.create(
            user=self.user,
            name='Search 1',
            query='Django',
            content_type='all'
        )
        SavedSearch.objects.create(
            user=self.user,
            name='Search 2',
            query='Python',
            content_type='posts'
        )
        
        response = self.client.get(reverse('forums:saved_searches'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Search 1')
        self.assertContains(response, 'Search 2')
    
    def test_search_history_view(self):
        """Test search history view."""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.get(reverse('forums:search_history'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python testing')
    
    def test_clear_search_history_view(self):
        """Test clearing search history."""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Create additional search history
        SearchHistory.objects.create(
            user=self.user,
            query='Another search',
            content_type='all',
            results_count=3
        )
        
        # Should have 2 search entries
        self.assertEqual(SearchHistory.objects.filter(user=self.user).count(), 2)
        
        response = self.client.post(
            reverse('forums:clear_search_history'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('Cleared 2 search entries', data['message'])
        
        # Check history was cleared
        self.assertEqual(SearchHistory.objects.filter(user=self.user).count(), 0)
    
    def test_views_require_login(self):
        """Test that search history views require login."""
        urls = [
            reverse('forums:save_search'),
            reverse('forums:saved_searches'),
            reverse('forums:search_history'),
            reverse('forums:clear_search_history'),
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertRedirects(response, f'/accounts/login/?next={url}')


class SearchIntegrationTests(TestCase):
    """Integration tests for search with history tracking."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            display_name='TestUser'
        )
        
        # Create test forum structure
        self.category = Category.objects.create(
            name='Programming',
            description='Programming discussions'
        )
        self.subcategory = Subcategory.objects.create(
            name='Python',
            description='Python programming',
            category=self.category
        )
    
    def test_search_records_history(self):
        """Test that performing search records history."""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Perform search
        response = self.client.get(reverse('forums:search'), {
            'query': 'Django testing',
            'content_type': 'all',
            'sort_by': 'relevance'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Check search was recorded in history
        history = SearchHistory.objects.filter(user=self.user).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.query, 'Django testing')
        self.assertEqual(history.content_type, 'all')
    
    def test_search_shows_recent_searches(self):
        """Test that search page shows recent searches."""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Create some search history
        SearchHistory.objects.create(
            user=self.user,
            query='React hooks',
            content_type='threads',
            results_count=5
        )
        
        response = self.client.get(reverse('forums:search'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('recent_searches', response.context)
        self.assertEqual(len(response.context['recent_searches']), 1)