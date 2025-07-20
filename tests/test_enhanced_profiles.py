"""
Tests for enhanced user profiles with hobbies and advanced features.
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from forums.models import Category, Subcategory, Thread, Post
from accounts.models import UserHobby
from unittest.mock import patch
from PIL import Image
import io
import tempfile
import os

User = get_user_model()


class UserHobbyModelTestCase(TestCase):
    """Test the UserHobby model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            display_name='User One',
            is_active=True,
            is_email_verified=True
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            display_name='User Two',
            is_active=True,
            is_email_verified=True
        )
        self.category = Category.objects.create(
            name='Photography',
            description='All about photography'
        )
        self.subcategory1 = Subcategory.objects.create(
            name='Digital Photography',
            description='Digital camera techniques',
            category=self.category
        )
        self.subcategory2 = Subcategory.objects.create(
            name='Film Photography',
            description='Traditional film photography',
            category=self.category
        )
    
    def test_userhobby_creation_with_required_fields(self):
        """Test creating a UserHobby with all required fields."""
        hobby = UserHobby.objects.create(
            user=self.user1,
            subcategory=self.subcategory1
        )
        
        self.assertEqual(hobby.user, self.user1)
        self.assertEqual(hobby.subcategory, self.subcategory1)
        self.assertIsNotNone(hobby.joined_at)
    
    def test_userhobby_string_representation(self):
        """Test the string representation of a UserHobby."""
        hobby = UserHobby.objects.create(
            user=self.user1,
            subcategory=self.subcategory1
        )
        
        expected_str = f"{self.user1.display_name} interested in {self.subcategory1.name}"
        self.assertEqual(str(hobby), expected_str)
    
    def test_userhobby_unique_constraint_user_subcategory(self):
        """Test that a user can only have one hobby per subcategory."""
        # Create first hobby
        UserHobby.objects.create(
            user=self.user1,
            subcategory=self.subcategory1
        )
        
        # Try to create duplicate hobby - should fail
        with self.assertRaises(IntegrityError):
            UserHobby.objects.create(
                user=self.user1,
                subcategory=self.subcategory1
            )
    
    def test_userhobby_different_users_same_subcategory(self):
        """Test that different users can have the same hobby."""
        hobby1 = UserHobby.objects.create(
            user=self.user1,
            subcategory=self.subcategory1
        )
        hobby2 = UserHobby.objects.create(
            user=self.user2,
            subcategory=self.subcategory1
        )
        
        self.assertEqual(UserHobby.objects.count(), 2)
        self.assertNotEqual(hobby1.user, hobby2.user)
    
    def test_userhobby_same_user_different_subcategories(self):
        """Test that the same user can have multiple hobbies."""
        hobby1 = UserHobby.objects.create(
            user=self.user1,
            subcategory=self.subcategory1
        )
        hobby2 = UserHobby.objects.create(
            user=self.user1,
            subcategory=self.subcategory2
        )
        
        self.assertEqual(UserHobby.objects.count(), 2)
        self.assertEqual(hobby1.user, hobby2.user)
        self.assertNotEqual(hobby1.subcategory, hobby2.subcategory)
    
    def test_userhobby_cascade_deletion_with_user(self):
        """Test that hobbies are deleted when user is deleted."""
        UserHobby.objects.create(
            user=self.user1,
            subcategory=self.subcategory1
        )
        
        self.assertEqual(UserHobby.objects.count(), 1)
        
        self.user1.delete()
        self.assertEqual(UserHobby.objects.count(), 0)
    
    def test_userhobby_cascade_deletion_with_subcategory(self):
        """Test that hobbies are deleted when subcategory is deleted."""
        UserHobby.objects.create(
            user=self.user1,
            subcategory=self.subcategory1
        )
        
        self.assertEqual(UserHobby.objects.count(), 1)
        
        self.subcategory1.delete()
        self.assertEqual(UserHobby.objects.count(), 0)
    
    def test_userhobby_ordering(self):
        """Test that hobbies are ordered by join date (newest first)."""
        hobby1 = UserHobby.objects.create(
            user=self.user1,
            subcategory=self.subcategory1
        )
        hobby2 = UserHobby.objects.create(
            user=self.user1,
            subcategory=self.subcategory2
        )
        
        hobbies = UserHobby.objects.all()
        self.assertEqual(hobbies[0], hobby2)  # Newest first
        self.assertEqual(hobbies[1], hobby1)


class EnhancedProfileViewTestCase(TestCase):
    """Test the enhanced profile view functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            display_name='User One',
            location='New York, NY',
            bio='Photography enthusiast and tech lover.',
            is_active=True,
            is_email_verified=True
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            display_name='User Two',
            is_active=True,
            is_email_verified=True
        )
        self.category = Category.objects.create(
            name='Photography',
            description='All about photography'
        )
        self.subcategory = Subcategory.objects.create(
            name='Digital Photography',
            description='Digital camera techniques',
            category=self.category
        )
        # Create some posts for user1
        self.thread = Thread.objects.create(
            title='My Photography Thread',
            subcategory=self.subcategory,
            author=self.user1
        )
        Post.objects.create(
            content='First post content',
            thread=self.thread,
            author=self.user1
        )
        Post.objects.create(
            content='Second post content',
            thread=self.thread,
            author=self.user1
        )
    
    def test_unauthenticated_user_can_view_profile(self):
        """Test that unauthenticated users can view public profiles."""
        profile_url = reverse('accounts:user_profile', kwargs={'user_id': self.user1.id})
        
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that public info is displayed
        self.assertContains(response, self.user1.display_name)
        self.assertContains(response, self.user1.location)
        self.assertContains(response, self.user1.bio)
        
        # Check that private info is not displayed
        self.assertNotContains(response, self.user1.email)
    
    def test_authenticated_user_can_view_profile(self):
        """Test that authenticated users can view profiles."""
        self.client.login(email='user2@example.com', password='testpass123')
        
        profile_url = reverse('accounts:user_profile', kwargs={'user_id': self.user1.id})
        
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that user info is displayed
        self.assertContains(response, self.user1.display_name)
        self.assertContains(response, self.user1.location)
        self.assertContains(response, self.user1.bio)
    
    def test_profile_displays_post_count(self):
        """Test that profile displays user's post count."""
        profile_url = reverse('accounts:user_profile', kwargs={'user_id': self.user1.id})
        
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that post count is displayed (user1 has 2 posts)
        self.assertContains(response, str(2))  # Post count number
        self.assertContains(response, 'Post')
    
    def test_profile_displays_join_date(self):
        """Test that profile displays user's join date."""
        profile_url = reverse('accounts:user_profile', kwargs={'user_id': self.user1.id})
        
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that join date is displayed
        self.assertContains(response, 'Joined')
        self.assertContains(response, self.user1.date_joined.strftime('%b %Y'))
    
    def test_profile_displays_hobbies(self):
        """Test that profile displays user's hobbies."""
        # Add hobby for user1
        UserHobby.objects.create(
            user=self.user1,
            subcategory=self.subcategory
        )
        
        profile_url = reverse('accounts:user_profile', kwargs={'user_id': self.user1.id})
        
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that hobby is displayed
        self.assertContains(response, self.subcategory.name)
    
    def test_hobby_links_to_subcategory(self):
        """Test that hobby list links to subcategories."""
        # Add hobby for user1
        UserHobby.objects.create(
            user=self.user1,
            subcategory=self.subcategory
        )
        
        profile_url = reverse('accounts:user_profile', kwargs={'user_id': self.user1.id})
        
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that hobby links to subcategory
        subcategory_url = reverse('forums:subcategory_detail', kwargs={
            'category_slug': self.category.slug,
            'subcategory_slug': self.subcategory.slug
        })
        self.assertContains(response, subcategory_url)
    
    def test_user_can_view_own_profile(self):
        """Test that user can view their own profile."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        profile_url = reverse('accounts:user_profile', kwargs={'user_id': self.user1.id})
        
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that edit button is shown for own profile
        self.assertContains(response, 'Edit Profile')
    
    def test_user_cannot_see_edit_button_on_others_profile(self):
        """Test that user cannot see edit button on other users' profiles."""
        self.client.login(email='user2@example.com', password='testpass123')
        
        profile_url = reverse('accounts:user_profile', kwargs={'user_id': self.user1.id})
        
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that edit button is not shown
        self.assertNotContains(response, 'Edit Profile')
    
    def test_profile_404_for_nonexistent_user(self):
        """Test that profile returns 404 for non-existent user."""
        profile_url = reverse('accounts:user_profile', kwargs={'user_id': 99999})
        
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 404)


class ProfileEditViewTestCase(TestCase):
    """Test the profile edit view functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            display_name='User One',
            location='New York, NY',
            bio='Original bio content.',
            is_active=True,
            is_email_verified=True
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            display_name='User Two',
            is_active=True,
            is_email_verified=True
        )
        self.edit_url = reverse('accounts:profile_edit')
    
    def test_unauthenticated_user_cannot_edit_profile(self):
        """Test that unauthenticated users cannot edit profiles."""
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_authenticated_user_can_access_edit_form(self):
        """Test that authenticated users can access edit form."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that form is displayed with current values
        self.assertContains(response, self.user1.display_name)
        self.assertContains(response, self.user1.location)
        self.assertContains(response, self.user1.bio)
    
    def test_profile_edit_updates_data(self):
        """Test that profile edit successfully updates user data."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.post(self.edit_url, {
            'display_name': 'Updated Name',
            'location': 'Los Angeles, CA',
            'bio': 'Updated bio content.'
        })
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Check that user data was updated
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.display_name, 'Updated Name')
        self.assertEqual(self.user1.location, 'Los Angeles, CA')
        self.assertEqual(self.user1.bio, 'Updated bio content.')
    
    def test_profile_edit_form_validation(self):
        """Test that profile edit form validates required fields."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.post(self.edit_url, {
            'display_name': '',  # Required field empty
            'location': 'Los Angeles, CA',
            'bio': 'Updated bio content.'
        })
        
        # Should stay on form page with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')
    
    def test_profile_picture_upload(self):
        """Test that profile picture upload works correctly."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        # Create a test image
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = io.BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        uploaded_file = SimpleUploadedFile(
            "test_profile.jpg",
            temp_file.getvalue(),
            content_type="image/jpeg"
        )
        
        response = self.client.post(self.edit_url, {
            'display_name': self.user1.display_name,
            'location': self.user1.location,
            'bio': self.user1.bio,
            'profile_picture': uploaded_file
        })
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Check that profile picture was saved
        self.user1.refresh_from_db()
        self.assertIsNotNone(self.user1.profile_picture)
    
    def test_profile_picture_validation(self):
        """Test that profile picture upload validates file types."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        # Create a non-image file
        uploaded_file = SimpleUploadedFile(
            "test_file.txt",
            b"This is not an image",
            content_type="text/plain"
        )
        
        response = self.client.post(self.edit_url, {
            'display_name': self.user1.display_name,
            'location': self.user1.location,
            'bio': self.user1.bio,
            'profile_picture': uploaded_file
        })
        
        # Should stay on form page with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upload a valid image')


class HobbyManagementTestCase(TestCase):
    """Test hobby selection and management functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            display_name='User One',
            is_active=True,
            is_email_verified=True
        )
        self.category = Category.objects.create(
            name='Photography',
            description='All about photography'
        )
        self.subcategory1 = Subcategory.objects.create(
            name='Digital Photography',
            description='Digital camera techniques',
            category=self.category
        )
        self.subcategory2 = Subcategory.objects.create(
            name='Film Photography',
            description='Traditional film photography',
            category=self.category
        )
        self.hobby_manage_url = reverse('accounts:manage_hobbies')
    
    def test_unauthenticated_user_cannot_manage_hobbies(self):
        """Test that unauthenticated users cannot manage hobbies."""
        response = self.client.get(self.hobby_manage_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_authenticated_user_can_access_hobby_management(self):
        """Test that authenticated users can access hobby management."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.hobby_manage_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that subcategories are available for selection
        self.assertContains(response, self.subcategory1.name)
        self.assertContains(response, self.subcategory2.name)
    
    def test_user_can_add_hobby(self):
        """Test that user can add a new hobby."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.post(self.hobby_manage_url, {
            'subcategories': [self.subcategory1.id]
        })
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Check that hobby was created
        self.assertTrue(UserHobby.objects.filter(
            user=self.user1,
            subcategory=self.subcategory1
        ).exists())
    
    def test_user_can_remove_hobby(self):
        """Test that user can remove an existing hobby."""
        # Create initial hobby
        UserHobby.objects.create(
            user=self.user1,
            subcategory=self.subcategory1
        )
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        # Submit form without the hobby (empty list)
        response = self.client.post(self.hobby_manage_url, {
            'subcategories': []
        })
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Check that hobby was removed
        self.assertFalse(UserHobby.objects.filter(
            user=self.user1,
            subcategory=self.subcategory1
        ).exists())
    
    def test_user_can_update_hobbies(self):
        """Test that user can update their hobby list."""
        # Create initial hobby
        UserHobby.objects.create(
            user=self.user1,
            subcategory=self.subcategory1
        )
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        # Update to different hobby
        response = self.client.post(self.hobby_manage_url, {
            'subcategories': [self.subcategory2.id]
        })
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Check that old hobby was removed and new one added
        self.assertFalse(UserHobby.objects.filter(
            user=self.user1,
            subcategory=self.subcategory1
        ).exists())
        self.assertTrue(UserHobby.objects.filter(
            user=self.user1,
            subcategory=self.subcategory2
        ).exists())
    
    def test_hobby_management_displays_current_hobbies(self):
        """Test that hobby management form shows current hobbies."""
        # Create initial hobby
        UserHobby.objects.create(
            user=self.user1,
            subcategory=self.subcategory1
        )
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.hobby_manage_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that current hobby is selected
        self.assertContains(response, 'checked')


class ProfileAdminTestCase(TestCase):
    """Test UserHobby model in Django admin."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            display_name='User One',
            is_active=True,
            is_email_verified=True
        )
        self.category = Category.objects.create(
            name='Photography',
            description='All about photography'
        )
        self.subcategory = Subcategory.objects.create(
            name='Digital Photography',
            description='Digital camera techniques',
            category=self.category
        )
    
    def test_userhobby_admin_registration(self):
        """Test that UserHobby is registered with admin."""
        from django.contrib.admin.sites import site
        from accounts.models import UserHobby
        
        # Check that UserHobby is registered with admin
        self.assertIn(UserHobby, site._registry)
    
    def test_userhobby_admin_list_display(self):
        """Test that UserHobby admin has appropriate list display."""
        hobby = UserHobby.objects.create(
            user=self.user1,
            subcategory=self.subcategory
        )
        
        # Test that we can create and display hobbies
        expected_str = f"{self.user1.display_name} interested in {self.subcategory.name}"
        self.assertEqual(str(hobby), expected_str)