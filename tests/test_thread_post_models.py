import pytest
from django.test import TestCase
from django.db import IntegrityError
from django.utils import timezone
from django.contrib.auth import get_user_model
from forums.models import Category, Subcategory, Thread, Post

User = get_user_model()


class ThreadModelTest(TestCase):
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

    def test_thread_creation_with_required_fields(self):
        """Test creating a thread with all required fields."""
        thread = Thread.objects.create(
            subcategory=self.subcategory,
            author=self.user,
            title='How to learn Python?'
        )
        self.assertEqual(thread.subcategory, self.subcategory)
        self.assertEqual(thread.author, self.user)
        self.assertEqual(thread.title, 'How to learn Python?')
        self.assertEqual(thread.slug, 'how-to-learn-python')
        self.assertFalse(thread.is_pinned)
        self.assertFalse(thread.is_locked)
        self.assertEqual(thread.view_count, 0)
        self.assertEqual(thread.post_count, 0)
        self.assertIsNotNone(thread.last_post_at)
        self.assertIsNotNone(thread.created_at)
        self.assertIsNotNone(thread.updated_at)

    def test_thread_slug_auto_generation(self):
        """Test that thread slug is automatically generated from title."""
        thread = Thread.objects.create(
            subcategory=self.subcategory,
            author=self.user,
            title='Best Python Web Frameworks in 2024'
        )
        self.assertEqual(thread.slug, 'best-python-web-frameworks-in-2024')

    def test_thread_slug_uniqueness_within_subcategory(self):
        """Test that thread slugs are unique within a subcategory."""
        Thread.objects.create(
            subcategory=self.subcategory,
            author=self.user,
            title='Python Tutorial'
        )
        # Second thread with same title should get different slug
        thread2 = Thread.objects.create(
            subcategory=self.subcategory,
            author=self.user,
            title='Python Tutorial'
        )
        thread1 = Thread.objects.get(title='Python Tutorial', slug='python-tutorial')
        self.assertNotEqual(thread1.slug, thread2.slug)
        self.assertTrue(thread2.slug.startswith('python-tutorial-'))

    def test_thread_same_slug_different_subcategories(self):
        """Test that threads can have same slug in different subcategories."""
        subcategory2 = Subcategory.objects.create(
            category=self.category,
            name='Web Development',
            description='Frontend and backend web development'
        )
        
        thread1 = Thread.objects.create(
            subcategory=self.subcategory,
            author=self.user,
            title='Getting Started'
        )
        thread2 = Thread.objects.create(
            subcategory=subcategory2,
            author=self.user,
            title='Getting Started'
        )
        
        self.assertEqual(thread1.slug, thread2.slug)
        self.assertNotEqual(thread1.subcategory, thread2.subcategory)

    def test_thread_string_representation(self):
        """Test the string representation of a thread."""
        thread = Thread.objects.create(
            subcategory=self.subcategory,
            author=self.user,
            title='Django vs Flask'
        )
        self.assertEqual(str(thread), 'Django vs Flask')

    def test_thread_pinned_and_locked_flags(self):
        """Test thread pinned and locked functionality."""
        thread = Thread.objects.create(
            subcategory=self.subcategory,
            author=self.user,
            title='Important Announcement',
            is_pinned=True,
            is_locked=True
        )
        self.assertTrue(thread.is_pinned)
        self.assertTrue(thread.is_locked)

    def test_thread_view_count_default(self):
        """Test that view count defaults to 0."""
        thread = Thread.objects.create(
            subcategory=self.subcategory,
            author=self.user,
            title='Test Thread'
        )
        self.assertEqual(thread.view_count, 0)

    def test_thread_post_count_default(self):
        """Test that post count defaults to 0."""
        thread = Thread.objects.create(
            subcategory=self.subcategory,
            author=self.user,
            title='Test Thread'
        )
        self.assertEqual(thread.post_count, 0)

    def test_thread_last_post_at_auto_set(self):
        """Test that last_post_at is automatically set to created_at on creation."""
        before_creation = timezone.now()
        thread = Thread.objects.create(
            subcategory=self.subcategory,
            author=self.user,
            title='Test Thread'
        )
        after_creation = timezone.now()
        
        self.assertGreaterEqual(thread.last_post_at, before_creation)
        self.assertLessEqual(thread.last_post_at, after_creation)
        # Should be very close to created_at
        time_diff = abs((thread.last_post_at - thread.created_at).total_seconds())
        self.assertLess(time_diff, 1)  # Within 1 second


class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            display_name='Test User',
            is_email_verified=True
        )
        self.user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123',
            display_name='Test User 2',
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
            title='How to learn Python?'
        )

    def test_post_creation_with_required_fields(self):
        """Test creating a post with all required fields."""
        post = Post.objects.create(
            thread=self.thread,
            author=self.user,
            content='Python is a great programming language for beginners!'
        )
        self.assertEqual(post.thread, self.thread)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.content, 'Python is a great programming language for beginners!')
        self.assertFalse(post.is_edited)
        self.assertIsNone(post.edited_at)
        self.assertIsNotNone(post.created_at)
        self.assertIsNotNone(post.updated_at)

    def test_post_string_representation(self):
        """Test the string representation of a post."""
        post = Post.objects.create(
            thread=self.thread,
            author=self.user,
            content='This is a test post with some content that should be truncated...'
        )
        expected_str = f"Post by {self.user.display_name} in {self.thread.title}"
        self.assertEqual(str(post), expected_str)

    def test_post_edited_functionality(self):
        """Test post editing functionality."""
        post = Post.objects.create(
            thread=self.thread,
            author=self.user,
            content='Original content'
        )
        
        # Initially not edited
        self.assertFalse(post.is_edited)
        self.assertIsNone(post.edited_at)
        
        # Simulate editing
        post.content = 'Updated content'
        post.is_edited = True
        post.edited_at = timezone.now()
        post.save()
        
        self.assertTrue(post.is_edited)
        self.assertIsNotNone(post.edited_at)

    def test_post_cascade_deletion_with_thread(self):
        """Test that posts are deleted when thread is deleted."""
        post = Post.objects.create(
            thread=self.thread,
            author=self.user,
            content='Test post content'
        )
        post_id = post.id
        
        self.thread.delete()
        
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.get(id=post_id)

    def test_post_user_deletion_handling(self):
        """Test post behavior when user is deleted."""
        post = Post.objects.create(
            thread=self.thread,
            author=self.user2,
            content='Test post content'
        )
        post_id = post.id
        
        # When user is deleted, posts should also be deleted (CASCADE)
        self.user2.delete()
        
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.get(id=post_id)

    def test_multiple_posts_same_thread(self):
        """Test creating multiple posts in the same thread."""
        post1 = Post.objects.create(
            thread=self.thread,
            author=self.user,
            content='First post'
        )
        post2 = Post.objects.create(
            thread=self.thread,
            author=self.user2,
            content='Second post'
        )
        
        posts = Post.objects.filter(thread=self.thread).order_by('created_at')
        self.assertEqual(posts.count(), 2)
        self.assertEqual(posts[0], post1)
        self.assertEqual(posts[1], post2)

    def test_post_ordering(self):
        """Test that posts are ordered by creation date."""
        # Create posts with slight delay to ensure different timestamps
        post1 = Post.objects.create(
            thread=self.thread,
            author=self.user,
            content='First post'
        )
        
        post2 = Post.objects.create(
            thread=self.thread,
            author=self.user2,
            content='Second post'
        )
        
        posts = list(Post.objects.filter(thread=self.thread))
        self.assertEqual(posts[0], post1)
        self.assertEqual(posts[1], post2)


class ThreadPostSignalsTest(TestCase):
    """Test Django signals for updating denormalized fields."""
    
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
            title='Test Thread for Signals'
        )

    def test_post_creation_updates_thread_post_count(self):
        """Test that creating a post updates thread's post_count."""
        initial_count = self.thread.post_count
        
        Post.objects.create(
            thread=self.thread,
            author=self.user,
            content='Test post content'
        )
        
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.post_count, initial_count + 1)

    def test_post_creation_updates_thread_last_post_at(self):
        """Test that creating a post updates thread's last_post_at."""
        original_last_post_at = self.thread.last_post_at
        
        # Wait a small amount to ensure different timestamp
        import time
        time.sleep(0.01)
        
        post = Post.objects.create(
            thread=self.thread,
            author=self.user,
            content='Test post content'
        )
        
        self.thread.refresh_from_db()
        self.assertGreater(self.thread.last_post_at, original_last_post_at)
        # Should be close to post creation time
        time_diff = abs((self.thread.last_post_at - post.created_at).total_seconds())
        self.assertLess(time_diff, 1)  # Within 1 second

    def test_post_deletion_updates_thread_post_count(self):
        """Test that deleting a post updates thread's post_count."""
        post = Post.objects.create(
            thread=self.thread,
            author=self.user,
            content='Test post content'
        )
        
        self.thread.refresh_from_db()
        count_with_post = self.thread.post_count
        
        post.delete()
        
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.post_count, count_with_post - 1)

    def test_multiple_posts_update_counts_correctly(self):
        """Test that multiple posts update counts correctly."""
        initial_count = self.thread.post_count
        
        # Create multiple posts
        for i in range(3):
            Post.objects.create(
                thread=self.thread,
                author=self.user,
                content=f'Test post {i + 1}'
            )
        
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.post_count, initial_count + 3)