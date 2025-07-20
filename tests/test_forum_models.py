import pytest
from django.test import TestCase
from django.db import IntegrityError
from django.utils.text import slugify
from forums.models import Category, Subcategory


class CategoryModelTest(TestCase):
    def test_category_creation_with_required_fields(self):
        """Test creating a category with all required fields."""
        category = Category.objects.create(
            name="Technology",
            description="Discussions about technology and gadgets",
            color_theme="blue",
            order=1
        )
        self.assertEqual(category.name, "Technology")
        self.assertEqual(category.slug, "technology")
        self.assertEqual(category.description, "Discussions about technology and gadgets")
        self.assertEqual(category.color_theme, "blue")
        self.assertEqual(category.order, 1)
        self.assertIsNotNone(category.created_at)
        self.assertIsNotNone(category.updated_at)

    def test_category_slug_auto_generation(self):
        """Test that slug is automatically generated from name."""
        category = Category.objects.create(
            name="Arts & Crafts",
            description="Creative hobbies",
            color_theme="purple",
            order=2
        )
        self.assertEqual(category.slug, "arts-crafts")

    def test_category_name_uniqueness(self):
        """Test that category names must be unique."""
        Category.objects.create(
            name="Gaming",
            description="Video games discussion",
            color_theme="red",
            order=1
        )
        with self.assertRaises(IntegrityError):
            Category.objects.create(
                name="Gaming",
                description="Another gaming category",
                color_theme="blue",
                order=2
            )

    def test_category_slug_uniqueness(self):
        """Test that category slugs must be unique."""
        Category.objects.create(
            name="Test Category",
            description="First category",
            color_theme="green",
            order=1
        )
        # This should work since we'll handle slug conflicts
        category2 = Category.objects.create(
            name="Test-Category",  # Different name but same slug potential
            description="Second category",
            color_theme="blue",
            order=2
        )
        # Slugs should be different
        self.assertNotEqual(
            Category.objects.get(name="Test Category").slug,
            category2.slug
        )

    def test_category_ordering(self):
        """Test that categories are ordered by order field."""
        cat3 = Category.objects.create(name="Third", description="desc", color_theme="red", order=3)
        cat1 = Category.objects.create(name="First", description="desc", color_theme="blue", order=1)
        cat2 = Category.objects.create(name="Second", description="desc", color_theme="green", order=2)
        
        categories = list(Category.objects.all())
        self.assertEqual(categories[0], cat1)
        self.assertEqual(categories[1], cat2)
        self.assertEqual(categories[2], cat3)

    def test_category_string_representation(self):
        """Test the string representation of a category."""
        category = Category.objects.create(
            name="Music",
            description="All about music",
            color_theme="yellow",
            order=1
        )
        self.assertEqual(str(category), "Music")

    def test_category_color_theme_choices(self):
        """Test that only valid color themes are accepted."""
        # This will be validated by the model choices
        valid_colors = ["blue", "red", "green", "purple", "yellow", "orange", "pink", "teal"]
        for color in valid_colors:
            category = Category.objects.create(
                name=f"Category {color}",
                description="Test category",
                color_theme=color,
                order=1
            )
            self.assertEqual(category.color_theme, color)


class SubcategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Technology",
            description="Tech discussions",
            color_theme="blue",
            order=1
        )

    def test_subcategory_creation_with_required_fields(self):
        """Test creating a subcategory with all required fields."""
        subcategory = Subcategory.objects.create(
            category=self.category,
            name="Programming",
            description="Software development discussions"
        )
        self.assertEqual(subcategory.category, self.category)
        self.assertEqual(subcategory.name, "Programming")
        self.assertEqual(subcategory.slug, "programming")
        self.assertEqual(subcategory.description, "Software development discussions")
        self.assertEqual(subcategory.member_count, 0)
        self.assertIsNotNone(subcategory.created_at)
        self.assertIsNotNone(subcategory.updated_at)

    def test_subcategory_slug_auto_generation(self):
        """Test that subcategory slug is automatically generated."""
        subcategory = Subcategory.objects.create(
            category=self.category,
            name="Web Development",
            description="Frontend and backend web development"
        )
        self.assertEqual(subcategory.slug, "web-development")

    def test_subcategory_unique_within_category(self):
        """Test that subcategory names must be unique within a category."""
        Subcategory.objects.create(
            category=self.category,
            name="Programming",
            description="First programming subcategory"
        )
        with self.assertRaises(IntegrityError):
            Subcategory.objects.create(
                category=self.category,
                name="Programming",
                description="Second programming subcategory"
            )

    def test_subcategory_same_name_different_categories(self):
        """Test that subcategories can have same name in different categories."""
        category2 = Category.objects.create(
            name="Arts",
            description="Arts discussions",
            color_theme="purple",
            order=2
        )
        
        sub1 = Subcategory.objects.create(
            category=self.category,
            name="Programming",
            description="Software programming"
        )
        sub2 = Subcategory.objects.create(
            category=category2,
            name="Programming",
            description="Arts programming"  # Different context
        )
        
        self.assertEqual(sub1.name, sub2.name)
        self.assertNotEqual(sub1.category, sub2.category)

    def test_subcategory_cascade_deletion(self):
        """Test that subcategories are deleted when category is deleted."""
        subcategory = Subcategory.objects.create(
            category=self.category,
            name="Programming",
            description="Software development"
        )
        subcategory_id = subcategory.id
        
        self.category.delete()
        
        with self.assertRaises(Subcategory.DoesNotExist):
            Subcategory.objects.get(id=subcategory_id)

    def test_subcategory_member_count_default(self):
        """Test that member count defaults to 0."""
        subcategory = Subcategory.objects.create(
            category=self.category,
            name="Gaming",
            description="Video games"
        )
        self.assertEqual(subcategory.member_count, 0)

    def test_subcategory_string_representation(self):
        """Test the string representation of a subcategory."""
        subcategory = Subcategory.objects.create(
            category=self.category,
            name="Mobile Development",
            description="iOS and Android development"
        )
        expected_str = f"{self.category.name} > Mobile Development"
        self.assertEqual(str(subcategory), expected_str)

    def test_subcategory_slug_unique_within_category(self):
        """Test that subcategory slugs are unique within a category."""
        Subcategory.objects.create(
            category=self.category,
            name="Test Sub",
            description="First subcategory"
        )
        # This should handle slug conflicts within the category
        sub2 = Subcategory.objects.create(
            category=self.category,
            name="Test-Sub",  # Different name but same slug potential
            description="Second subcategory"
        )
        
        # Slugs should be different within the same category
        sub1 = Subcategory.objects.get(name="Test Sub")
        self.assertNotEqual(sub1.slug, sub2.slug)