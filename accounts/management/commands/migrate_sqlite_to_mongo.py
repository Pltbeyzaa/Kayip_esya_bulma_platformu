from django.core.management.base import BaseCommand
from accounts.models import ItemPost
from accounts.services import upsert_item_post_to_mongo


class Command(BaseCommand):
    help = 'Migrate all ItemPost rows from SQLite to MongoDB (upsert).'

    def handle(self, *args, **options):
        count = 0
        for post in ItemPost.objects.all().iterator():
            upsert_item_post_to_mongo(post)
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Transferred {count} posts to MongoDB.'))


