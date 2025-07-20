import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from forums.models import Category, Subcategory, Thread, Post

User = get_user_model()


class ForumViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            display_name='Test User',
            is_email_verified=True
        )
        
        # Create test forum structure
        self.category1 = Category.objects.create(
            name='Technology',
            description='Tech discussions',
            color_theme='blue',
            order=1
        )
        self.category2 = Category.objects.create(
            name='Arts & Crafts',
            description='Creative hobbies',
            color_theme='purple',
            order=2
        )
        
        self.subcategory1 = Subcategory.objects.create(
            category=self.category1,
            name='Programming',
            description='Software development discussions'
        )
        self.subcategory2 = Subcategory.objects.create(
            category=self.category1,
            name='Hardware',
            description='Computer hardware discussions'
        )
        self.subcategory3 = Subcategory.objects.create(
            category=self.category2,
            name='Painting',
            description='Painting techniques and tips'
        )
        
        self.thread1 = Thread.objects.create(
            subcategory=self.subcategory1,
            author=self.user,
            title='How to learn Python?',
            is_pinned=True
        )
        self.thread2 = Thread.objects.create(
            subcategory=self.subcategory1,
            author=self.user,
            title='Best Django practices'
        )
        self.thread3 = Thread.objects.create(
            subcategory=self.subcategory2,
            author=self.user,
            title='Building a gaming PC'
        )
        
        self.post1 = Post.objects.create(
            thread=self.thread1,
            author=self.user,
            content='Python is great for beginners! Start with the basics.'
        )
        self.post2 = Post.objects.create(
            thread=self.thread1,
            author=self.user,
            content='I recommend reading Python Crash Course.'
        )
        self.post3 = Post.objects.create(
            thread=self.thread2,
            author=self.user,
            content='Always use Django REST framework for APIs.'
        )


class CategoryListViewTest(ForumViewsTest):
    def test_category_list_view_status_code(self):
        """Test that category list view returns 200."""
        url = reverse('forums:category_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_category_list_displays_all_categories(self):
        """Test that all categories are displayed in the list."""
        url = reverse('forums:category_list')
        response = self.client.get(url)
        self.assertContains(response, 'Technology')
        self.assertContains(response, 'Arts & Crafts')
        self.assertContains(response, 'Tech discussions')
        self.assertContains(response, 'Creative hobbies')

    def test_category_list_displays_subcategories(self):
        """Test that subcategories are shown within categories."""
        url = reverse('forums:category_list')
        response = self.client.get(url)
        self.assertContains(response, 'Programming')
        self.assertContains(response, 'Hardware')
        self.assertContains(response, 'Painting')

    def test_category_list_ordering(self):
        """Test that categories are ordered by order field."""
        url = reverse('forums:category_list')
        response = self.client.get(url)
        content = response.content.decode()
        tech_position = content.find('Technology')
        arts_position = content.find('Arts & Crafts')
        self.assertLess(tech_position, arts_position)

    def test_category_list_template_used(self):
        """Test that correct template is used."""
        url = reverse('forums:category_list')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'forums/category_list.html')

    def test_category_list_context_data(self):
        """Test that correct context data is provided."""
        url = reverse('forums:category_list')
        response = self.client.get(url)
        self.assertIn('categories', response.context)
        categories = response.context['categories']
        self.assertEqual(len(categories), 2)


class SubcategoryDetailViewTest(ForumViewsTest):
    def test_subcategory_detail_view_status_code(self):
        """Test that subcategory detail view returns 200."""
        url = reverse('forums:subcategory_detail', kwargs={
            'category_slug': self.category1.slug,
            'subcategory_slug': self.subcategory1.slug
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_subcategory_detail_displays_threads(self):
        """Test that threads are displayed in subcategory."""
        url = reverse('forums:subcategory_detail', kwargs={
            'category_slug': self.category1.slug,
            'subcategory_slug': self.subcategory1.slug
        })
        response = self.client.get(url)
        self.assertContains(response, 'How to learn Python?')
        self.assertContains(response, 'Best Django practices')
        # Should not contain thread from different subcategory
        self.assertNotContains(response, 'Building a gaming PC')

    def test_subcategory_detail_pinned_threads_first(self):
        """Test that pinned threads appear before regular threads."""
        url = reverse('forums:subcategory_detail', kwargs={
            'category_slug': self.category1.slug,
            'subcategory_slug': self.subcategory1.slug
        })
        response = self.client.get(url)
        content = response.content.decode()
        python_position = content.find('How to learn Python?')
        django_position = content.find('Best Django practices')
        # Pinned thread should appear first
        self.assertLess(python_position, django_position)

    def test_subcategory_detail_invalid_slug_404(self):
        """Test that invalid subcategory slug returns 404."""
        url = reverse('forums:subcategory_detail', kwargs={
            'category_slug': self.category1.slug,
            'subcategory_slug': 'nonexistent'
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_subcategory_detail_invalid_category_404(self):
        """Test that invalid category slug returns 404."""
        url = reverse('forums:subcategory_detail', kwargs={
            'category_slug': 'nonexistent',
            'subcategory_slug': self.subcategory1.slug
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_subcategory_detail_template_used(self):
        """Test that correct template is used."""
        url = reverse('forums:subcategory_detail', kwargs={
            'category_slug': self.category1.slug,
            'subcategory_slug': self.subcategory1.slug
        })
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'forums/subcategory_detail.html')

    def test_subcategory_detail_context_data(self):
        """Test that correct context data is provided."""
        url = reverse('forums:subcategory_detail', kwargs={
            'category_slug': self.category1.slug,
            'subcategory_slug': self.subcategory1.slug
        })
        response = self.client.get(url)
        self.assertIn('subcategory', response.context)
        self.assertIn('threads', response.context)
        self.assertEqual(response.context['subcategory'], self.subcategory1)

    def test_subcategory_detail_pagination(self):
        """Test pagination when there are many threads."""
        # Create more threads to test pagination
        for i in range(25):
            Thread.objects.create(
                subcategory=self.subcategory1,
                author=self.user,
                title=f'Test Thread {i}'
            )
        
        url = reverse('forums:subcategory_detail', kwargs={
            'category_slug': self.category1.slug,
            'subcategory_slug': self.subcategory1.slug
        })
        response = self.client.get(url)
        
        # Should have pagination
        self.assertContains(response, 'page')
        # Should have limited number of threads per page
        threads = response.context['threads']
        self.assertLessEqual(len(threads), 20)  # Assuming 20 per page


class ThreadDetailViewTest(ForumViewsTest):
    def test_thread_detail_view_status_code(self):
        """Test that thread detail view returns 200."""
        url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category1.slug,
            'subcategory_slug': self.subcategory1.slug,
            'thread_slug': self.thread1.slug
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_thread_detail_displays_posts(self):
        """Test that posts are displayed in thread."""
        url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category1.slug,
            'subcategory_slug': self.subcategory1.slug,
            'thread_slug': self.thread1.slug
        })
        response = self.client.get(url)
        self.assertContains(response, 'Python is great for beginners!')
        self.assertContains(response, 'I recommend reading Python Crash Course.')
        # Should not contain post from different thread
        self.assertNotContains(response, 'Always use Django REST framework')

    def test_thread_detail_view_count_increments(self):
        """Test that thread view count increments on each view."""
        initial_view_count = self.thread1.view_count
        
        url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category1.slug,
            'subcategory_slug': self.subcategory1.slug,
            'thread_slug': self.thread1.slug
        })
        
        # First view
        self.client.get(url)
        self.thread1.refresh_from_db()
        self.assertEqual(self.thread1.view_count, initial_view_count + 1)
        
        # Second view
        self.client.get(url)
        self.thread1.refresh_from_db()
        self.assertEqual(self.thread1.view_count, initial_view_count + 2)

    def test_thread_detail_invalid_slug_404(self):
        """Test that invalid thread slug returns 404."""
        url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category1.slug,
            'subcategory_slug': self.subcategory1.slug,
            'thread_slug': 'nonexistent'
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_thread_detail_invalid_subcategory_404(self):
        """Test that thread not in specified subcategory returns 404."""
        url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category1.slug,
            'subcategory_slug': self.subcategory2.slug,  # Wrong subcategory
            'thread_slug': self.thread1.slug
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_thread_detail_template_used(self):
        """Test that correct template is used."""
        url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category1.slug,
            'subcategory_slug': self.subcategory1.slug,
            'thread_slug': self.thread1.slug
        })
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'forums/thread_detail.html')

    def test_thread_detail_context_data(self):
        """Test that correct context data is provided."""
        url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category1.slug,
            'subcategory_slug': self.subcategory1.slug,
            'thread_slug': self.thread1.slug
        })
        response = self.client.get(url)
        self.assertIn('thread', response.context)
        self.assertIn('posts', response.context)
        self.assertEqual(response.context['thread'], self.thread1)

    def test_thread_detail_posts_ordering(self):
        """Test that posts are ordered by creation date."""
        url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category1.slug,
            'subcategory_slug': self.subcategory1.slug,
            'thread_slug': self.thread1.slug
        })
        response = self.client.get(url)
        posts = response.context['posts']
        post_list = list(posts)
        self.assertEqual(post_list[0], self.post1)
        self.assertEqual(post_list[1], self.post2)

    def test_thread_detail_pagination(self):
        """Test pagination when there are many posts."""
        # Create more posts to test pagination
        for i in range(25):
            Post.objects.create(
                thread=self.thread1,
                author=self.user,
                content=f'Test post content {i}'
            )
        
        url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category1.slug,
            'subcategory_slug': self.subcategory1.slug,
            'thread_slug': self.thread1.slug
        })
        response = self.client.get(url)
        
        # Should have pagination
        self.assertContains(response, 'page')
        # Should have limited number of posts per page
        posts = response.context['posts']
        self.assertLessEqual(len(posts), 10)  # Assuming 10 per page


class ForumURLTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            display_name='Test User',
            is_email_verified=True
        )
        self.category = Category.objects.create(
            name='Technology',
            description='Tech discussions',
            color_theme='blue',
            order=1
        )
        self.subcategory = Subcategory.objects.create(
            category=self.category,
            name='Programming',
            description='Software development discussions'
        )
        self.thread = Thread.objects.create(
            subcategory=self.subcategory,
            author=self.user,
            title='Test Thread'
        )

    def test_category_list_url_resolves(self):
        """Test that category list URL resolves correctly."""
        url = reverse('forums:category_list')
        self.assertEqual(url, '/forums/')

    def test_subcategory_detail_url_resolves(self):
        """Test that subcategory detail URL resolves correctly."""
        url = reverse('forums:subcategory_detail', kwargs={
            'category_slug': self.category.slug,
            'subcategory_slug': self.subcategory.slug
        })
        expected_url = f'/forums/{self.category.slug}/{self.subcategory.slug}/'
        self.assertEqual(url, expected_url)

    def test_thread_detail_url_resolves(self):
        """Test that thread detail URL resolves correctly."""
        url = reverse('forums:thread_detail', kwargs={
            'category_slug': self.category.slug,
            'subcategory_slug': self.subcategory.slug,
            'thread_slug': self.thread.slug
        })
        expected_url = f'/forums/{self.category.slug}/{self.subcategory.slug}/{self.thread.slug}/'
        self.assertEqual(url, expected_url)