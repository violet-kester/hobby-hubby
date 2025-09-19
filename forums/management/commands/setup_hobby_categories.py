"""
Management command to set up the fixed hobby categories for Hobby Hubby.
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from forums.models import Category


class Command(BaseCommand):
    help = 'Set up the fixed hobby categories with proper styling'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing categories before creating new ones',
        )

    def handle(self, *args, **options):
        # Fixed hobby categories data
        categories_data = [
            {
                'name': 'Creative & Arts',
                'slug': 'creative-arts',
                'description': 'Express your creativity through drawing, painting, crafts, music, writing, photography, and all forms of artistic expression.',
                'color_theme': 'creative-arts',
                'icon': 'fas fa-palette',
                'order': 1,
            },
            {
                'name': 'Sports & Fitness',
                'slug': 'sports-fitness',
                'description': 'Stay active and healthy with discussions about sports, fitness routines, outdoor activities, and athletic pursuits.',
                'color_theme': 'sports-fitness',
                'icon': 'fas fa-running',
                'order': 2,
            },
            {
                'name': 'Games & Entertainment',
                'slug': 'games-entertainment',
                'description': 'Connect with fellow gamers and entertainment enthusiasts. Board games, video games, movies, TV shows, and more.',
                'color_theme': 'games-entertainment',
                'icon': 'fas fa-gamepad',
                'order': 3,
            },
            {
                'name': 'Technology & Science',
                'slug': 'technology-science',
                'description': 'Explore the world of technology, programming, electronics, science experiments, and innovative discoveries.',
                'color_theme': 'technology-science',
                'icon': 'fas fa-microchip',
                'order': 4,
            },
            {
                'name': 'Food & Culinary',
                'slug': 'food-culinary',
                'description': 'Share recipes, cooking techniques, baking adventures, food photography, and culinary experiences from around the world.',
                'color_theme': 'food-culinary',
                'icon': 'fas fa-utensils',
                'order': 5,
            },
            {
                'name': 'Lifestyle & Social',
                'slug': 'lifestyle-social',
                'description': 'Discuss lifestyle topics, social activities, travel, personal development, and community building.',
                'color_theme': 'lifestyle-social',
                'icon': 'fas fa-users',
                'order': 6,
            },
        ]

        if options['reset']:
            self.stdout.write(
                self.style.WARNING('Deleting existing categories...')
            )
            Category.objects.all().delete()

        created_count = 0
        updated_count = 0

        for category_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=category_data['slug'],
                defaults=category_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                # Update existing category with new data
                for key, value in category_data.items():
                    if key != 'slug':  # Don't update slug
                        setattr(category, key, value)
                category.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated category: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {created_count} new and {updated_count} existing categories.'
            )
        )