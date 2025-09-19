"""
Management command to create sample subcategories for testing the forum design.
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from forums.models import Category, Subcategory


class Command(BaseCommand):
    help = 'Create sample subcategories for testing the forum design'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing subcategories before creating new ones',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(
                self.style.WARNING('Deleting existing subcategories...')
            )
            Subcategory.objects.all().delete()

        # Sample subcategories data by category
        subcategories_data = {
            'creative-arts': [
                {'name': 'Digital Art & Design', 'description': 'Digital painting, graphic design, UI/UX, and digital illustration techniques'},
                {'name': 'Traditional Art', 'description': 'Painting, drawing, sketching, watercolors, and traditional media'},
                {'name': 'Photography', 'description': 'Photography tips, techniques, equipment reviews, and photo sharing'},
                {'name': 'Crafting & DIY', 'description': 'Handmade crafts, DIY projects, woodworking, and creative making'},
                {'name': 'Music & Audio', 'description': 'Music creation, instruments, recording, and audio production'},
            ],
            'sports-fitness': [
                {'name': 'Running & Cardio', 'description': 'Running tips, marathon training, cardio workouts, and endurance sports'},
                {'name': 'Weight Training', 'description': 'Strength training, bodybuilding, powerlifting, and gym workouts'},
                {'name': 'Yoga & Mindfulness', 'description': 'Yoga practices, meditation, mindfulness, and mental wellness'},
                {'name': 'Outdoor Activities', 'description': 'Hiking, camping, rock climbing, and outdoor adventure sports'},
                {'name': 'Team Sports', 'description': 'Basketball, soccer, volleyball, and other team-based sports'},
            ],
            'games-entertainment': [
                {'name': 'Video Games', 'description': 'Gaming discussions, reviews, tips, and multiplayer coordination'},
                {'name': 'Board Games', 'description': 'Tabletop gaming, board game reviews, and strategy discussions'},
                {'name': 'Movies & TV', 'description': 'Film and television discussions, reviews, and recommendations'},
                {'name': 'Books & Reading', 'description': 'Book clubs, reading recommendations, and literary discussions'},
                {'name': 'Streaming & Content', 'description': 'Content creation, streaming, and social media discussions'},
            ],
            'technology-science': [
                {'name': 'Programming', 'description': 'Coding discussions, programming languages, and software development'},
                {'name': 'Electronics & Gadgets', 'description': 'Electronics projects, gadget reviews, and tech news'},
                {'name': 'Science & Research', 'description': 'Scientific discussions, research sharing, and STEM topics'},
                {'name': 'AI & Machine Learning', 'description': 'Artificial intelligence, ML projects, and data science'},
                {'name': 'Cybersecurity', 'description': 'Security practices, ethical hacking, and privacy discussions'},
            ],
            'food-culinary': [
                {'name': 'Cooking & Recipes', 'description': 'Recipe sharing, cooking techniques, and kitchen tips'},
                {'name': 'Baking & Desserts', 'description': 'Baking recipes, pastry techniques, and sweet treats'},
                {'name': 'International Cuisine', 'description': 'World cuisines, cultural foods, and international cooking'},
                {'name': 'Healthy Eating', 'description': 'Nutrition, healthy recipes, and dietary discussions'},
                {'name': 'Food Photography', 'description': 'Food styling, photography tips, and visual food presentation'},
            ],
            'lifestyle-social': [
                {'name': 'Travel & Adventure', 'description': 'Travel experiences, destination guides, and adventure stories'},
                {'name': 'Personal Development', 'description': 'Self-improvement, goal setting, and productivity tips'},
                {'name': 'Community Events', 'description': 'Local meetups, community activities, and social gatherings'},
                {'name': 'Fashion & Style', 'description': 'Fashion trends, styling tips, and personal style discussions'},
                {'name': 'Home & Garden', 'description': 'Home improvement, gardening, interior design, and living spaces'},
            ],
        }

        created_count = 0

        for category_slug, subcategories in subcategories_data.items():
            try:
                category = Category.objects.get(slug=category_slug)
                
                for subcat_data in subcategories:
                    slug = slugify(subcat_data['name'])
                    subcategory, created = Subcategory.objects.get_or_create(
                        category=category,
                        slug=slug,
                        defaults={
                            'name': subcat_data['name'],
                            'description': subcat_data['description'],
                            'member_count': 0  # Will be updated when users join
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Created subcategory: {subcategory.name} in {category.name}')
                        )
                    
            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Category {category_slug} not found')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} subcategories.'
            )
        )