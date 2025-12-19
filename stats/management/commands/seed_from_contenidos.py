"""
Management command to seed stats from contenidos data.
Usage: python manage.py seed_from_contenidos
"""
from django.core.management.base import BaseCommand
from stats.seeder import seed_from_contenidos


class Command(BaseCommand):
    help = "Seed stats data from contenidos API based on available artists, albums, and tracks"

    def handle(self, *args, **options):
        self.stdout.write("\n🌱 Seeding stats from contenidos...\n")
        success = seed_from_contenidos()
        
        if success:
            self.stdout.write(self.style.SUCCESS("\n✅ Stats seeded successfully!"))
        else:
            self.stdout.write(self.style.WARNING(
                "\n⚠️  Could not seed from contenidos. Make sure CONTENT_API_BASE is configured "
                "and the contenidos service is running."
            ))
