"""
Tests for photo gallery functionality.
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from PIL import Image
import io
import tempfile
import os

User = get_user_model()


class PhotoModelTestCase(TestCase):
    """Test the Photo model functionality."""
    
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
    
    def create_test_image(self, name="test.jpg", format="JPEG", size=(100, 100), color="red"):
        """Create a test image file."""
        image = Image.new('RGB', size, color=color)
        temp_file = io.BytesIO()
        image.save(temp_file, format=format)
        temp_file.seek(0)
        return SimpleUploadedFile(name, temp_file.getvalue(), content_type=f"image/{format.lower()}")
    
    def test_photo_creation_with_required_fields(self):
        """Test creating a Photo with all required fields."""
        from accounts.models import Photo
        
        image_file = self.create_test_image()
        photo = Photo.objects.create(
            user=self.user1,
            image=image_file
        )
        
        self.assertEqual(photo.user, self.user1)
        self.assertIsNotNone(photo.image)
        self.assertIsNotNone(photo.created_at)
        self.assertEqual(photo.caption, '')  # Default empty caption
    
    def test_photo_creation_with_caption(self):
        """Test creating a Photo with optional caption."""
        from accounts.models import Photo
        
        image_file = self.create_test_image()
        photo = Photo.objects.create(
            user=self.user1,
            image=image_file,
            caption="My awesome photo"
        )
        
        self.assertEqual(photo.caption, "My awesome photo")
    
    def test_photo_string_representation(self):
        """Test the string representation of a Photo."""
        from accounts.models import Photo
        
        image_file = self.create_test_image()
        photo = Photo.objects.create(
            user=self.user1,
            image=image_file,
            caption="Test photo"
        )
        
        expected_str = f"Photo by {self.user1.display_name}: Test photo"
        self.assertEqual(str(photo), expected_str)
    
    def test_photo_string_representation_without_caption(self):
        """Test the string representation of a Photo without caption."""
        from accounts.models import Photo
        
        image_file = self.create_test_image()
        photo = Photo.objects.create(
            user=self.user1,
            image=image_file
        )
        
        expected_str = f"Photo by {self.user1.display_name}"
        self.assertEqual(str(photo), expected_str)
    
    def test_photo_cascade_deletion_with_user(self):
        """Test that photos are deleted when user is deleted."""
        from accounts.models import Photo
        
        image_file = self.create_test_image()
        Photo.objects.create(
            user=self.user1,
            image=image_file
        )
        
        self.assertEqual(Photo.objects.count(), 1)
        
        self.user1.delete()
        self.assertEqual(Photo.objects.count(), 0)
    
    def test_photo_ordering(self):
        """Test that photos are ordered by upload date (newest first)."""
        from accounts.models import Photo
        
        image_file1 = self.create_test_image("test1.jpg")
        image_file2 = self.create_test_image("test2.jpg")
        
        photo1 = Photo.objects.create(user=self.user1, image=image_file1)
        photo2 = Photo.objects.create(user=self.user1, image=image_file2)
        
        photos = Photo.objects.all()
        self.assertEqual(photos[0], photo2)  # Newest first
        self.assertEqual(photos[1], photo1)
    
    def test_photo_caption_max_length(self):
        """Test that photo caption respects max length."""
        from accounts.models import Photo
        
        image_file = self.create_test_image()
        long_caption = "x" * 201  # Assuming 200 char limit
        
        photo = Photo(
            user=self.user1,
            image=image_file,
            caption=long_caption
        )
        
        # This should raise a validation error
        with self.assertRaises(ValidationError):
            photo.full_clean()


class PhotoUploadViewTestCase(TestCase):
    """Test the photo upload view functionality."""
    
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
        self.upload_url = reverse('accounts:upload_photo')
    
    def create_test_image(self, name="test.jpg", format="JPEG", size=(100, 100), color="red"):
        """Create a test image file."""
        image = Image.new('RGB', size, color=color)
        temp_file = io.BytesIO()
        image.save(temp_file, format=format)
        temp_file.seek(0)
        return SimpleUploadedFile(name, temp_file.getvalue(), content_type=f"image/{format.lower()}")
    
    def test_unauthenticated_user_cannot_upload_photo(self):
        """Test that unauthenticated users cannot upload photos."""
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_authenticated_user_can_access_upload_form(self):
        """Test that authenticated users can access upload form."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upload Photo')
    
    def test_photo_upload_success(self):
        """Test successful photo upload."""
        from accounts.models import Photo
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        image_file = self.create_test_image()
        response = self.client.post(self.upload_url, {
            'image': image_file,
            'caption': 'Test photo upload'
        })
        
        # Should redirect after successful upload
        self.assertEqual(response.status_code, 302)
        
        # Check that photo was created
        self.assertEqual(Photo.objects.count(), 1)
        photo = Photo.objects.first()
        self.assertEqual(photo.user, self.user1)
        self.assertEqual(photo.caption, 'Test photo upload')
    
    def test_photo_upload_without_caption(self):
        """Test photo upload without caption."""
        from accounts.models import Photo
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        image_file = self.create_test_image()
        response = self.client.post(self.upload_url, {
            'image': image_file
        })
        
        # Should succeed
        self.assertEqual(response.status_code, 302)
        
        # Check that photo was created
        self.assertEqual(Photo.objects.count(), 1)
        photo = Photo.objects.first()
        self.assertEqual(photo.caption, '')
    
    def test_photo_upload_size_validation(self):
        """Test that photo upload validates file size."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        # Create a truly oversized file (11MB of data)
        large_data = b'x' * (11 * 1024 * 1024)  # 11MB of data
        large_file = SimpleUploadedFile(
            "large_image.jpg",
            large_data,
            content_type="image/jpeg"
        )
        
        response = self.client.post(self.upload_url, {
            'image': large_file,
            'caption': 'Large image'
        })
        
        # Should stay on form page with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Image file too large')
    
    def test_photo_upload_format_validation(self):
        """Test that photo upload validates file format."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        # Create a non-image file
        text_file = SimpleUploadedFile(
            "test.txt",
            b"This is not an image",
            content_type="text/plain"
        )
        
        response = self.client.post(self.upload_url, {
            'image': text_file,
            'caption': 'Text file'
        })
        
        # Should stay on form page with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Unsupported image format')


class PhotoGalleryViewTestCase(TestCase):
    """Test the photo gallery view functionality."""
    
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
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            display_name='User Two',
            is_active=True,
            is_email_verified=True
        )
        self.gallery_url = reverse('accounts:photo_gallery', kwargs={'user_id': self.user1.id})
    
    def create_test_image(self, name="test.jpg"):
        """Create a test image file."""
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = io.BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        return SimpleUploadedFile(name, temp_file.getvalue(), content_type="image/jpeg")
    
    def test_unauthenticated_user_can_view_gallery(self):
        """Test that unauthenticated users can view public galleries."""
        from accounts.models import Photo
        
        # Create a photo for user1
        image_file = self.create_test_image()
        Photo.objects.create(
            user=self.user1,
            image=image_file,
            caption="Public photo"
        )
        
        response = self.client.get(self.gallery_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public photo")
    
    def test_authenticated_user_can_view_gallery(self):
        """Test that authenticated users can view galleries."""
        from accounts.models import Photo
        
        self.client.login(email='user2@example.com', password='testpass123')
        
        # Create a photo for user1
        image_file = self.create_test_image()
        Photo.objects.create(
            user=self.user1,
            image=image_file,
            caption="Test photo"
        )
        
        response = self.client.get(self.gallery_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test photo")
    
    def test_gallery_shows_only_user_photos(self):
        """Test that gallery shows only photos for the specific user."""
        from accounts.models import Photo
        
        # Create photos for both users
        image_file1 = self.create_test_image("user1.jpg")
        image_file2 = self.create_test_image("user2.jpg")
        
        Photo.objects.create(user=self.user1, image=image_file1, caption="User 1 photo")
        Photo.objects.create(user=self.user2, image=image_file2, caption="User 2 photo")
        
        response = self.client.get(self.gallery_url)
        self.assertEqual(response.status_code, 200)
        
        # Should show user1's photo but not user2's
        self.assertContains(response, "User 1 photo")
        self.assertNotContains(response, "User 2 photo")
    
    def test_gallery_pagination(self):
        """Test that gallery paginates photos correctly."""
        from accounts.models import Photo
        
        # Create 25 photos (assuming 20 per page)
        for i in range(25):
            image_file = self.create_test_image(f"photo{i}.jpg")
            Photo.objects.create(
                user=self.user1,
                image=image_file,
                caption=f"Photo {i}"
            )
        
        response = self.client.get(self.gallery_url)
        self.assertEqual(response.status_code, 200)
        
        # Should show pagination
        self.assertContains(response, 'pagination')
        
        # Test second page
        response = self.client.get(self.gallery_url + '?page=2')
        self.assertEqual(response.status_code, 200)
    
    def test_gallery_empty_state(self):
        """Test that gallery shows empty state when no photos."""
        response = self.client.get(self.gallery_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No photos')
    
    def test_gallery_404_for_nonexistent_user(self):
        """Test that gallery returns 404 for non-existent user."""
        gallery_url = reverse('accounts:photo_gallery', kwargs={'user_id': 99999})
        
        response = self.client.get(gallery_url)
        self.assertEqual(response.status_code, 404)
    
    def test_own_gallery_shows_upload_button(self):
        """Test that user sees upload button on their own gallery."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        response = self.client.get(self.gallery_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upload Photo')
    
    def test_other_gallery_hides_upload_button(self):
        """Test that user doesn't see upload button on other user's gallery."""
        self.client.login(email='user2@example.com', password='testpass123')
        
        response = self.client.get(self.gallery_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Upload Photo')


class PhotoDeletionTestCase(TestCase):
    """Test photo deletion functionality."""
    
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
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            display_name='User Two',
            is_active=True,
            is_email_verified=True
        )
    
    def create_test_image(self, name="test.jpg"):
        """Create a test image file."""
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = io.BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        return SimpleUploadedFile(name, temp_file.getvalue(), content_type="image/jpeg")
    
    def test_unauthenticated_user_cannot_delete_photo(self):
        """Test that unauthenticated users cannot delete photos."""
        from accounts.models import Photo
        
        image_file = self.create_test_image()
        photo = Photo.objects.create(user=self.user1, image=image_file)
        
        delete_url = reverse('accounts:delete_photo', kwargs={'photo_id': photo.id})
        response = self.client.post(delete_url)
        
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertTrue(Photo.objects.filter(id=photo.id).exists())
    
    def test_user_can_delete_own_photo(self):
        """Test that user can delete their own photo."""
        from accounts.models import Photo
        
        self.client.login(email='user1@example.com', password='testpass123')
        
        image_file = self.create_test_image()
        photo = Photo.objects.create(user=self.user1, image=image_file)
        
        delete_url = reverse('accounts:delete_photo', kwargs={'photo_id': photo.id})
        response = self.client.post(delete_url)
        
        # Should redirect after deletion
        self.assertEqual(response.status_code, 302)
        
        # Photo should be deleted
        self.assertFalse(Photo.objects.filter(id=photo.id).exists())
    
    def test_user_cannot_delete_other_user_photo(self):
        """Test that user cannot delete another user's photo."""
        from accounts.models import Photo
        
        self.client.login(email='user2@example.com', password='testpass123')
        
        image_file = self.create_test_image()
        photo = Photo.objects.create(user=self.user1, image=image_file)
        
        delete_url = reverse('accounts:delete_photo', kwargs={'photo_id': photo.id})
        response = self.client.post(delete_url)
        
        # Should return 403 or 404
        self.assertIn(response.status_code, [403, 404])
        
        # Photo should still exist
        self.assertTrue(Photo.objects.filter(id=photo.id).exists())
    
    def test_delete_nonexistent_photo_returns_404(self):
        """Test that deleting non-existent photo returns 404."""
        self.client.login(email='user1@example.com', password='testpass123')
        
        delete_url = reverse('accounts:delete_photo', kwargs={'photo_id': 99999})
        response = self.client.post(delete_url)
        
        self.assertEqual(response.status_code, 404)


class PhotoAdminTestCase(TestCase):
    """Test Photo model in Django admin."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            display_name='User One',
            is_active=True,
            is_email_verified=True
        )
    
    def test_photo_admin_registration(self):
        """Test that Photo is registered with admin."""
        from django.contrib.admin.sites import site
        from accounts.models import Photo
        
        # Check that Photo is registered with admin
        self.assertIn(Photo, site._registry)
    
    def test_photo_admin_list_display(self):
        """Test that Photo admin has appropriate list display."""
        from accounts.models import Photo
        
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = io.BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        image_file = SimpleUploadedFile("test.jpg", temp_file.getvalue(), content_type="image/jpeg")
        
        photo = Photo.objects.create(
            user=self.user1,
            image=image_file,
            caption="Admin test photo"
        )
        
        # Test that we can create and display photos
        expected_str = f"Photo by {self.user1.display_name}: Admin test photo"
        self.assertEqual(str(photo), expected_str)