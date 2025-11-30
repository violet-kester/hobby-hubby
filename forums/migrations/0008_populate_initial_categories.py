# Generated data migration to populate initial hobby categories and subcategories

from django.db import migrations


def populate_categories(apps, schema_editor):
    """Create the initial hobby categories."""
    Category = apps.get_model('forums', 'Category')

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

    for category_data in categories_data:
        Category.objects.get_or_create(
            slug=category_data['slug'],
            defaults=category_data
        )


def populate_subcategories(apps, schema_editor):
    """Create the initial subcategories for each category."""
    Category = apps.get_model('forums', 'Category')
    Subcategory = apps.get_model('forums', 'Subcategory')

    from django.utils.text import slugify

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

    for category_slug, subcategories in subcategories_data.items():
        try:
            category = Category.objects.get(slug=category_slug)

            for subcat_data in subcategories:
                slug = slugify(subcat_data['name'])
                Subcategory.objects.get_or_create(
                    category=category,
                    slug=slug,
                    defaults={
                        'name': subcat_data['name'],
                        'description': subcat_data['description'],
                        'member_count': 0
                    }
                )
        except Category.DoesNotExist:
            pass  # Category will be created in the previous step


def reverse_populate_categories(apps, schema_editor):
    """Remove the initial categories (reverse migration)."""
    Category = apps.get_model('forums', 'Category')
    # Delete categories by slug to ensure we only remove what we added
    category_slugs = [
        'creative-arts',
        'sports-fitness',
        'games-entertainment',
        'technology-science',
        'food-culinary',
        'lifestyle-social',
    ]
    Category.objects.filter(slug__in=category_slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('forums', '0007_alter_category_color_theme'),
    ]

    operations = [
        migrations.RunPython(populate_categories, reverse_populate_categories),
        migrations.RunPython(populate_subcategories, migrations.RunPython.noop),
    ]
