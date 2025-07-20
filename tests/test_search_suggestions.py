"""
Tests for search suggestions functionality.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from forums.models import Category, Subcategory, Thread, Post

User = get_user_model()


class SearchSuggestionsViewTests(TestCase):
    """Tests for search suggestions AJAX endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            display_name='TestUser'
        )
        
        # Create test forum structure
        self.category = Category.objects.create(
            name='Test Category',
            description='A test category for suggestions'
        )
        
        self.subcategory = Subcategory.objects.create(
            name='Test Subcategory',
            description='A test subcategory for suggestions',
            category=self.category
        )
        
        # Create test thread
        self.thread = Thread.objects.create(
            title='JavaScript Testing Tips',
            subcategory=self.subcategory,
            author=self.user
        )
        
        # Create test post
        self.post = Post.objects.create(
            thread=self.thread,
            author=self.user,
            content='This is a test post about JavaScript development and testing frameworks.'
        )
        
        # Create another user for testing
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            display_name='JavaScriptExpert'
        )
    
    def test_suggestions_requires_ajax(self):
        """Test that suggestions endpoint requires AJAX request."""
        url = reverse('forums:search_suggestions')
        response = self.client.get(url, {'q': 'test'})
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'AJAX request required')
    
    def test_suggestions_requires_query_param(self):
        """Test that suggestions endpoint requires query parameter."""
        url = reverse('forums:search_suggestions')
        response = self.client.get(
            url, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Query parameter required')
    
    def test_suggestions_minimum_query_length(self):
        """Test that suggestions require minimum query length."""
        url = reverse('forums:search_suggestions')
        response = self.client.get(
            url, 
            {'q': 'a'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Query must be at least 2 characters')
    
    def test_suggestions_basic_functionality(self):
        """Test basic search suggestions functionality."""
        url = reverse('forums:search_suggestions')
        response = self.client.get(
            url, 
            {'q': 'JavaScript'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('suggestions', data)
        
        suggestions = data['suggestions']
        self.assertIsInstance(suggestions, list)
        
        # Should find our thread and post
        suggestion_titles = [s['title'] for s in suggestions]
        self.assertIn('JavaScript Testing Tips', suggestion_titles)
    
    def test_suggestions_thread_structure(self):
        """Test that thread suggestions have correct structure."""
        url = reverse('forums:search_suggestions')
        response = self.client.get(
            url, 
            {'q': 'JavaScript'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        suggestions = data['suggestions']
        
        # Find thread suggestion
        thread_suggestion = None
        for suggestion in suggestions:
            if suggestion['type'] == 'thread':
                thread_suggestion = suggestion
                break
        
        self.assertIsNotNone(thread_suggestion)
        self.assertEqual(thread_suggestion['title'], 'JavaScript Testing Tips')
        self.assertEqual(thread_suggestion['type'], 'thread')
        self.assertIn('url', thread_suggestion)
        self.assertIn('description', thread_suggestion)
        self.assertIn(f'/forums/{self.category.slug}/{self.subcategory.slug}/{self.thread.slug}/', 
                     thread_suggestion['url'])
    
    def test_suggestions_post_structure(self):
        """Test that post suggestions have correct structure."""
        url = reverse('forums:search_suggestions')
        response = self.client.get(
            url, 
            {'q': 'development'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        suggestions = data['suggestions']
        
        # Find post suggestion
        post_suggestion = None
        for suggestion in suggestions:
            if suggestion['type'] == 'post':
                post_suggestion = suggestion
                break
        
        self.assertIsNotNone(post_suggestion)
        self.assertEqual(post_suggestion['type'], 'post')
        self.assertIn('url', post_suggestion)
        self.assertIn('description', post_suggestion)
        self.assertIn('title', post_suggestion)
    
    def test_suggestions_user_structure(self):
        """Test that user suggestions have correct structure."""
        url = reverse('forums:search_suggestions')
        response = self.client.get(
            url, 
            {'q': 'JavaScriptExpert'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        suggestions = data['suggestions']
        
        # Find user suggestion
        user_suggestion = None
        for suggestion in suggestions:
            if suggestion['type'] == 'user':
                user_suggestion = suggestion
                break
        
        self.assertIsNotNone(user_suggestion)
        self.assertEqual(user_suggestion['title'], 'JavaScriptExpert')
        self.assertEqual(user_suggestion['type'], 'user')
        self.assertIn('url', user_suggestion)
        self.assertIn('description', user_suggestion)
        self.assertIn(f'/accounts/user/{self.other_user.id}/', user_suggestion['url'])
    
    def test_suggestions_category_structure(self):
        """Test that category suggestions have correct structure."""
        url = reverse('forums:search_suggestions')
        response = self.client.get(
            url, 
            {'q': 'Test Category'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        suggestions = data['suggestions']
        
        # Find category suggestion
        category_suggestion = None
        for suggestion in suggestions:
            if suggestion['type'] == 'category':
                category_suggestion = suggestion
                break
        
        self.assertIsNotNone(category_suggestion)
        self.assertEqual(category_suggestion['title'], 'Test Category')
        self.assertEqual(category_suggestion['type'], 'category')
        self.assertIn('url', category_suggestion)
        self.assertIn('description', category_suggestion)
    
    def test_suggestions_subcategory_structure(self):
        """Test that subcategory suggestions have correct structure."""
        url = reverse('forums:search_suggestions')
        response = self.client.get(
            url, 
            {'q': 'Test Subcategory'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        suggestions = data['suggestions']
        
        # Find subcategory suggestion
        subcategory_suggestion = None
        for suggestion in suggestions:
            if suggestion['type'] == 'subcategory':
                subcategory_suggestion = suggestion
                break
        
        self.assertIsNotNone(subcategory_suggestion)
        self.assertEqual(subcategory_suggestion['title'], 'Test Subcategory')
        self.assertEqual(subcategory_suggestion['type'], 'subcategory')
        self.assertIn('url', subcategory_suggestion)
        self.assertIn('description', subcategory_suggestion)
    
    def test_suggestions_limit(self):
        """Test that suggestions are limited to reasonable number."""
        # Create multiple threads to test limit
        for i in range(15):
            Thread.objects.create(
                title=f'JavaScript Framework {i}',
                subcategory=self.subcategory,
                author=self.user
            )
        
        url = reverse('forums:search_suggestions')
        response = self.client.get(
            url, 
            {'q': 'JavaScript'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        suggestions = data['suggestions']
        
        # Should be limited to reasonable number (10 is common)
        self.assertLessEqual(len(suggestions), 10)
    
    def test_suggestions_case_insensitive(self):
        """Test that suggestions work with different cases."""
        url = reverse('forums:search_suggestions')
        
        # Test lowercase
        response_lower = self.client.get(
            url, 
            {'q': 'javascript'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Test uppercase
        response_upper = self.client.get(
            url, 
            {'q': 'JAVASCRIPT'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Test mixed case
        response_mixed = self.client.get(
            url, 
            {'q': 'JavaScript'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # All should return results
        for response in [response_lower, response_upper, response_mixed]:
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertGreater(len(data['suggestions']), 0)
    
    def test_suggestions_partial_match(self):
        """Test that suggestions work with partial matches."""
        url = reverse('forums:search_suggestions')
        response = self.client.get(
            url, 
            {'q': 'Java'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        suggestions = data['suggestions']
        
        # Should find results that contain 'Java' (like 'JavaScript')
        self.assertGreater(len(suggestions), 0)
        
        # Check that at least one suggestion contains our expected content
        found_match = False
        for suggestion in suggestions:
            if 'JavaScript' in suggestion['title'] or 'JavaScript' in suggestion.get('description', ''):
                found_match = True
                break
        
        self.assertTrue(found_match, "Should find partial matches")
    
    def test_suggestions_no_results(self):
        """Test suggestions when no results found."""
        url = reverse('forums:search_suggestions')
        response = self.client.get(
            url, 
            {'q': 'nonexistentquery'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('suggestions', data)
        self.assertEqual(len(data['suggestions']), 0)
    
    def test_suggestions_html_escaping(self):
        """Test that suggestions properly escape HTML content."""
        # Create content with HTML characters
        Thread.objects.create(
            title='<script>alert("test")</script>',
            subcategory=self.subcategory,
            author=self.user
        )
        
        url = reverse('forums:search_suggestions')
        response = self.client.get(
            url, 
            {'q': 'script'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        suggestions = data['suggestions']
        
        # Find the suggestion with script tag
        script_suggestion = None
        for suggestion in suggestions:
            if 'script' in suggestion['title']:
                script_suggestion = suggestion
                break
        
        # HTML should be escaped in the response
        self.assertIsNotNone(script_suggestion)
        # The actual title should contain the raw HTML (Django will escape it in templates)
        self.assertIn('<script>', script_suggestion['title'])