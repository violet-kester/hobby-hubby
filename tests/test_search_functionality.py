"""
Test suite for search functionality.

Tests the basic search implementation including:
- Search across posts, threads, users, and categories
- Search form validation
- Search result filtering and ranking
- Search query processing
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Q
from forums.models import Category, Subcategory, Thread, Post
from forums.forms import SearchForm


User = get_user_model()


class SearchFormTestCase(TestCase):
    """Test cases for the search form."""
    
    def test_search_form_valid_query(self):
        """Test that search form accepts valid queries."""
        form_data = {'query': 'test search'}
        form = SearchForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_search_form_empty_query(self):
        """Test that search form rejects empty queries."""
        form_data = {'query': ''}
        form = SearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('query', form.errors)
    
    def test_search_form_whitespace_only_query(self):
        """Test that search form rejects whitespace-only queries."""
        form_data = {'query': '   '}
        form = SearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('query', form.errors)
    
    def test_search_form_very_long_query(self):
        """Test that search form rejects overly long queries."""
        form_data = {'query': 'a' * 201}  # 201 characters
        form = SearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('query', form.errors)
    
    def test_search_form_filters_valid(self):
        """Test that search form accepts valid filter options."""
        form_data = {
            'query': 'test',
            'content_type': 'posts',
            'sort_by': 'relevance'
        }
        form = SearchForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_search_form_invalid_content_type(self):
        """Test that search form rejects invalid content types."""
        form_data = {
            'query': 'test',
            'content_type': 'invalid_type'
        }
        form = SearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('content_type', form.errors)


class SearchViewTestCase(TestCase):
    """Test cases for search views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            display_name='Test User',
            password='testpass123',
            is_active=True,
            is_email_verified=True
        )
        
        # Create test content
        self.category = Category.objects.create(
            name='Test Category',
            description='A test category for searching',
            slug='test-category'
        )
        
        self.subcategory = Subcategory.objects.create(
            name='Test Subcategory',
            description='A test subcategory for searching',
            category=self.category,
            slug='test-subcategory'
        )
        
        self.thread = Thread.objects.create(
            title='Test Thread About Programming',
            subcategory=self.subcategory,
            author=self.user,
            slug='test-thread-about-programming'
        )
        
        self.post = Post.objects.create(
            thread=self.thread,
            author=self.user,
            content='This is a test post about Django and Python programming.'
        )
        
        # URLs
        self.search_url = reverse('forums:search')
    
    def test_search_view_get_request(self):
        """Test that search view displays search form on GET request."""
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Search')
        self.assertContains(response, 'name="query"')
    
    def test_search_view_valid_query(self):
        """Test search view with valid query returns results."""
        response = self.client.get(self.search_url, {'query': 'programming'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Search Results')
        self.assertContains(response, 'programming')
    
    def test_search_view_no_results(self):
        """Test search view with query that returns no results."""
        response = self.client.get(self.search_url, {'query': 'nonexistent'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No results found')
    
    def test_search_view_empty_query_redirects(self):
        """Test that empty query shows search form without results."""
        response = self.client.get(self.search_url, {'query': ''})
        self.assertEqual(response.status_code, 200)
        # Should show search form but no results since form is invalid
        self.assertContains(response, 'Search Forum')
        self.assertNotContains(response, 'Search Results')
    
    def test_search_view_post_filter(self):
        """Test search filtering by posts only."""
        response = self.client.get(self.search_url, {
            'query': 'Django',
            'content_type': 'posts'
        })
        self.assertEqual(response.status_code, 200)
        # Should find the post but not other content types
    
    def test_search_view_thread_filter(self):
        """Test search filtering by threads only."""
        response = self.client.get(self.search_url, {
            'query': 'Programming',
            'content_type': 'threads'
        })
        self.assertEqual(response.status_code, 200)
        # Should find the thread title
    
    def test_search_view_user_filter(self):
        """Test search filtering by users only."""
        response = self.client.get(self.search_url, {
            'query': 'Test User',
            'content_type': 'users'
        })
        self.assertEqual(response.status_code, 200)
        # Should find the user


class SearchFunctionalityTestCase(TestCase):
    """Test cases for search functionality and results."""
    
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user1 = User.objects.create_user(
            email='john@example.com',
            display_name='John Programmer',
            bio='I love Python and Django development',
            location='San Francisco',
            password='testpass123',
            is_active=True,
            is_email_verified=True
        )
        
        self.user2 = User.objects.create_user(
            email='jane@example.com',
            display_name='Jane Designer',
            bio='UI/UX designer with a passion for web design',
            location='New York',
            password='testpass123',
            is_active=True,
            is_email_verified=True
        )
        
        # Create test content
        self.category = Category.objects.create(
            name='Programming',
            description='Discussions about programming languages and frameworks',
            slug='programming'
        )
        
        self.subcategory = Subcategory.objects.create(
            name='Python',
            description='Python programming discussions',
            category=self.category,
            slug='python'
        )
        
        self.thread1 = Thread.objects.create(
            title='Django Best Practices',
            subcategory=self.subcategory,
            author=self.user1,
            slug='django-best-practices'
        )
        
        self.thread2 = Thread.objects.create(
            title='Python Data Structures',
            subcategory=self.subcategory,
            author=self.user2,
            slug='python-data-structures'
        )
        
        self.post1 = Post.objects.create(
            thread=self.thread1,
            author=self.user1,
            content='Django is a powerful web framework for Python. Here are some best practices for Django development.'
        )
        
        self.post2 = Post.objects.create(
            thread=self.thread2,
            author=self.user2,
            content='Python offers many built-in data structures like lists, dictionaries, and sets.'
        )
        
        self.post3 = Post.objects.create(
            thread=self.thread1,
            author=self.user2,
            content='I agree! Django makes web development much easier with its ORM and admin interface.'
        )
    
    def test_search_posts_by_content(self):
        """Test searching posts by content."""
        from forums.views import search_posts
        
        # Search for "Django"
        results = search_posts('Django')
        self.assertEqual(len(results), 2)  # post1 and post3
        
        # Search for "data structures"
        results = search_posts('data structures')
        self.assertEqual(len(results), 1)  # post2
        
        # Search for non-existent term
        results = search_posts('nonexistent')
        self.assertEqual(len(results), 0)
    
    def test_search_threads_by_title(self):
        """Test searching threads by title."""
        from forums.views import search_threads
        
        # Search for "Django"
        results = search_threads('Django')
        self.assertEqual(len(results), 1)  # thread1
        
        # Search for "Python"
        results = search_threads('Python')
        self.assertEqual(len(results), 1)  # thread2
        
        # Search for "practices"
        results = search_threads('practices')
        self.assertEqual(len(results), 1)  # thread1
    
    def test_search_users_by_profile(self):
        """Test searching users by profile information."""
        from forums.views import search_users
        
        # Search by display name
        results = search_users('John')
        self.assertEqual(len(results), 1)  # user1
        
        # Search by bio content
        results = search_users('Python')
        self.assertEqual(len(results), 1)  # user1
        
        # Search by location
        results = search_users('Francisco')
        self.assertEqual(len(results), 1)  # user1
        
        # Search by designer
        results = search_users('designer')
        self.assertEqual(len(results), 1)  # user2
    
    def test_search_categories_by_name(self):
        """Test searching categories and subcategories."""
        from forums.views import search_categories
        
        # Search for category - should find both category and subcategory
        results = search_categories('Programming')
        self.assertEqual(len(results), 2)  # category + subcategory (mentions programming in description)
        
        # Search for subcategory specifically
        results = search_categories('Python')
        self.assertEqual(len(results), 1)  # subcategory only


class SearchSecurityTestCase(TestCase):
    """Test cases for search security."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.search_url = reverse('forums:search')
    
    def test_search_query_sanitization(self):
        """Test that search queries are properly sanitized."""
        # Test SQL injection attempt
        malicious_query = "'; DROP TABLE forums_post; --"
        response = self.client.get(self.search_url, {'query': malicious_query})
        self.assertEqual(response.status_code, 200)
        # Should not cause any database errors
    
    def test_search_xss_prevention(self):
        """Test that search results prevent XSS attacks."""
        xss_query = "<script>alert('xss')</script>"
        response = self.client.get(self.search_url, {'query': xss_query})
        self.assertEqual(response.status_code, 200)
        # Should not contain unescaped script tags
        self.assertNotContains(response, '<script>')
    
    def test_search_query_length_limit(self):
        """Test that overly long search queries are handled properly."""
        long_query = 'a' * 1000
        response = self.client.get(self.search_url, {'query': long_query})
        self.assertEqual(response.status_code, 200)
        # Should handle gracefully without errors


class SearchPerformanceTestCase(TestCase):
    """Test cases for search performance."""
    
    def setUp(self):
        """Set up test data for performance testing."""
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            display_name='Test User',
            password='testpass123',
            is_active=True,
            is_email_verified=True
        )
        
        # Create test content
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category',
            slug='test-category'
        )
        
        self.subcategory = Subcategory.objects.create(
            name='Test Subcategory',
            description='Test subcategory',
            category=self.category,
            slug='test-subcategory'
        )
        
        # Create multiple threads and posts for performance testing
        for i in range(10):
            thread = Thread.objects.create(
                title=f'Test Thread {i}',
                subcategory=self.subcategory,
                author=self.user,
                slug=f'test-thread-{i}'
            )
            
            for j in range(5):
                Post.objects.create(
                    thread=thread,
                    author=self.user,
                    content=f'Test post content {i}-{j} with various keywords for searching.'
                )
    
    def test_search_query_efficiency(self):
        """Test that search queries are efficient."""
        from django.test.utils import override_settings
        from django.db import connection
        
        # Count queries for search operation
        with override_settings(DEBUG=True):
            initial_queries = len(connection.queries)
            
            response = self.client.get(reverse('forums:search'), {'query': 'test'})
            
            final_queries = len(connection.queries)
            query_count = final_queries - initial_queries
            
            # Should use reasonable number of queries (not N+1)
            self.assertLess(query_count, 10, "Search should use efficient queries")