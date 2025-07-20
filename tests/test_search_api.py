"""
Tests for Search API Endpoints

Tests the REST API functionality for mobile integration, including search,
suggestions, and analytics endpoints.

Author: Claude (Shakespearean Assistant)
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from forums.models import Category, Subcategory, Thread, Post, SearchAnalytics

User = get_user_model()


class SearchAPITestCase(TestCase):
    """Test cases for the search API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test users
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            display_name='Test User'
        )
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='staffpass123',
            display_name='Staff User',
            is_staff=True
        )
        
        # Create test forum structure
        self.category = Category.objects.create(
            name='Test Category',
            description='A test category',
            slug='test-category'
        )
        
        self.subcategory = Subcategory.objects.create(
            name='Test Subcategory',
            description='A test subcategory',
            slug='test-subcategory',
            category=self.category
        )
        
        self.thread = Thread.objects.create(
            title='Test Thread for API',
            subcategory=self.subcategory,
            author=self.user
        )
        
        self.post = Post.objects.create(
            content='This is a test post for API testing',
            thread=self.thread,
            author=self.user
        )
    
    def test_api_search_get_request(self):
        """Test API search endpoint with GET request."""
        # First test that regular search URL works
        regular_url = reverse('forums:search')
        regular_response = self.client.get(regular_url, {'query': 'test'})
        self.assertEqual(regular_response.status_code, 200, "Regular search should work")
        
        # Now test API search
        url = reverse('forums:api_search')
        response = self.client.get(url, {'query': 'test'})
        
        # Debug the response if it fails
        if response.status_code != 200:
            print(f"API URL: {url}")
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content.decode()[:500]}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['query'], 'test')
        self.assertGreaterEqual(data['total_results'], 0)
        self.assertIn('results', data)
        self.assertIn('pagination', data)
    
    def test_api_search_post_request(self):
        """Test API search endpoint with POST request."""
        url = reverse('forums:api_search')
        response = self.client.post(url, {'query': 'test'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['query'], 'test')
    
    def test_api_search_json_post_request(self):
        """Test API search endpoint with JSON POST request."""
        url = reverse('forums:api_search')
        payload = {'query': 'test', 'content_type': 'threads'}
        
        response = self.client.post(
            url, 
            json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['query'], 'test')
        self.assertEqual(data['content_type'], 'threads')
    
    def test_api_search_missing_query(self):
        """Test API search endpoint with missing query parameter."""
        url = reverse('forums:api_search')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('required', data['error'])
    
    def test_api_search_short_query(self):
        """Test API search endpoint with query too short."""
        url = reverse('forums:api_search')
        response = self.client.get(url, {'query': 'a'})
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('2 characters', data['error'])
    
    def test_api_search_with_filters(self):
        """Test API search endpoint with advanced filters."""
        url = reverse('forums:api_search')
        params = {
            'query': 'test',
            'content_type': 'posts',
            'sort_by': 'date_desc',
            'limit': 10,
            'offset': 0,
            'author': 'Test User',
            'category': 'test-category'
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['content_type'], 'posts')
        self.assertEqual(data['sort_by'], 'date_desc')
        self.assertEqual(data['limit'], 10)
    
    def test_api_search_invalid_category(self):
        """Test API search endpoint with invalid category."""
        url = reverse('forums:api_search')
        params = {
            'query': 'test',
            'category': 'nonexistent-category'
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('not found', data['error'])
    
    def test_api_search_invalid_content_type(self):
        """Test API search endpoint with invalid content type."""
        url = reverse('forums:api_search')
        params = {
            'query': 'test',
            'content_type': 'invalid_type'
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Invalid content_type', data['error'])
    
    def test_api_search_method_not_allowed(self):
        """Test API search endpoint with unsupported HTTP method."""
        url = reverse('forums:api_search')
        response = self.client.put(url, {'query': 'test'})
        
        self.assertEqual(response.status_code, 405)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Method not allowed', data['error'])
    
    def test_api_search_pagination(self):
        """Test API search endpoint pagination."""
        url = reverse('forums:api_search')
        params = {
            'query': 'test',
            'limit': 1,
            'offset': 0
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('pagination', data)
        pagination = data['pagination']
        self.assertIn('has_next', pagination)
        self.assertIn('has_previous', pagination)
        self.assertIn('page_size', pagination)
        self.assertIn('total_pages', pagination)
    
    def test_api_search_result_format(self):
        """Test API search endpoint result format."""
        url = reverse('forums:api_search')
        response = self.client.get(url, {'query': 'test'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        if data['results']:
            result = data['results'][0]
            required_fields = [
                'id', 'type', 'title', 'content', 'url', 
                'relevance_score', 'category', 'subcategory', 'created_at'
            ]
            
            for field in required_fields:
                self.assertIn(field, result)
    
    def test_api_search_suggestions_valid(self):
        """Test API search suggestions endpoint with valid query."""
        url = reverse('forums:api_search_suggestions')
        response = self.client.get(url, {'q': 'test'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('suggestions', data)
        self.assertIn('query', data)
        self.assertIn('total', data)
        self.assertEqual(data['query'], 'test')
    
    def test_api_search_suggestions_empty_query(self):
        """Test API search suggestions endpoint with empty query."""
        url = reverse('forums:api_search_suggestions')
        response = self.client.get(url, {'q': ''})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['suggestions'], [])
    
    def test_api_search_suggestions_short_query(self):
        """Test API search suggestions endpoint with short query."""
        url = reverse('forums:api_search_suggestions')
        response = self.client.get(url, {'q': 'a'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['suggestions'], [])
    
    def test_api_search_suggestions_with_limit(self):
        """Test API search suggestions endpoint with custom limit."""
        url = reverse('forums:api_search_suggestions')
        response = self.client.get(url, {'q': 'test', 'limit': 5})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertLessEqual(len(data['suggestions']), 5)
    
    def test_api_search_suggestions_method_not_allowed(self):
        """Test API search suggestions endpoint with unsupported method."""
        url = reverse('forums:api_search_suggestions')
        response = self.client.post(url, {'q': 'test'})
        
        self.assertEqual(response.status_code, 405)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Method not allowed', data['error'])
    
    def test_api_search_suggestions_format(self):
        """Test API search suggestions endpoint result format."""
        url = reverse('forums:api_search_suggestions')
        response = self.client.get(url, {'q': 'test'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        if data['suggestions']:
            suggestion = data['suggestions'][0]
            required_fields = ['type', 'text', 'description', 'url', 'metadata']
            
            for field in required_fields:
                self.assertIn(field, suggestion)
    
    def test_api_search_analytics_unauthorized(self):
        """Test API search analytics endpoint without authentication."""
        url = reverse('forums:api_search_analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Staff access required', data['error'])
    
    def test_api_search_analytics_non_staff(self):
        """Test API search analytics endpoint with non-staff user."""
        url = reverse('forums:api_search_analytics')
        self.client.login(email='testuser@example.com', password='testpass123')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Staff access required', data['error'])
    
    def test_api_search_analytics_staff_access(self):
        """Test API search analytics endpoint with staff user."""
        # Create some analytics data
        SearchAnalytics.objects.create(
            session_key='test_session',
            user=self.user,
            query='test query',
            normalized_query='test query',
            search_time_ms=100,
            results_count=5,
            content_type='all'
        )
        
        url = reverse('forums:api_search_analytics')
        self.client.login(email='staff@example.com', password='staffpass123')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIn('metrics', data)
        self.assertIn('top_queries', data)
        self.assertIn('content_type_distribution', data)
    
    def test_api_search_analytics_with_days_filter(self):
        """Test API search analytics endpoint with days filter."""
        # Create some analytics data
        SearchAnalytics.objects.create(
            session_key='test_session',
            user=self.user,
            query='test query',
            normalized_query='test query',
            search_time_ms=100,
            results_count=5,
            content_type='all'
        )
        
        url = reverse('forums:api_search_analytics')
        self.client.login(email='staff@example.com', password='staffpass123')
        response = self.client.get(url, {'days': 30})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['period_days'], 30)
    
    def test_api_search_analytics_method_not_allowed(self):
        """Test API search analytics endpoint with unsupported method."""
        url = reverse('forums:api_search_analytics')
        self.client.login(email='staff@example.com', password='staffpass123')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 405)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Method not allowed', data['error'])
    
    def test_api_search_analytics_metrics_format(self):
        """Test API search analytics endpoint metrics format."""
        # Create some analytics data
        SearchAnalytics.objects.create(
            session_key='test_session',
            user=self.user,
            query='test query',
            normalized_query='test query',
            search_time_ms=100,
            results_count=5,
            content_type='all'
        )
        
        url = reverse('forums:api_search_analytics')
        self.client.login(email='staff@example.com', password='staffpass123')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        metrics = data['metrics']
        required_fields = [
            'total_searches', 'unique_users', 'unique_sessions',
            'click_through_rate', 'zero_result_rate', 'performance'
        ]
        
        for field in required_fields:
            self.assertIn(field, metrics)
        
        # Check performance metrics
        performance = metrics['performance']
        performance_fields = [
            'avg_search_time_ms', 'avg_results_count', 'avg_database_hits'
        ]
        
        for field in performance_fields:
            self.assertIn(field, performance)
    
    def test_api_search_creates_analytics_record(self):
        """Test that API search creates analytics records."""
        url = reverse('forums:api_search')
        
        initial_count = SearchAnalytics.objects.count()
        
        response = self.client.get(url, {'query': 'test'})
        
        self.assertEqual(response.status_code, 200)
        
        # Check that analytics record was created
        self.assertEqual(SearchAnalytics.objects.count(), initial_count + 1)
        
        # Check analytics record details
        analytics = SearchAnalytics.objects.latest('created_at')
        self.assertEqual(analytics.query, 'test')
        self.assertEqual(analytics.normalized_query, 'test')
        self.assertEqual(analytics.content_type, 'all')
        self.assertEqual(analytics.request_path, '/api/search/')
        self.assertEqual(analytics.source, 'api')
    
    def test_api_search_invalid_json(self):
        """Test API search endpoint with invalid JSON."""
        url = reverse('forums:api_search')
        
        response = self.client.post(
            url,
            'invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Invalid JSON', data['error'])
    
    def test_api_search_date_filters(self):
        """Test API search endpoint with date filters."""
        url = reverse('forums:api_search')
        params = {
            'query': 'test',
            'date_from': '2023-01-01T00:00:00Z',
            'date_to': '2023-12-31T23:59:59Z'
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_api_search_invalid_date_format(self):
        """Test API search endpoint with invalid date format."""
        url = reverse('forums:api_search')
        params = {
            'query': 'test',
            'date_from': 'invalid-date'
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Invalid date_from format', data['error'])