from django.core.management.base import BaseCommand
from django.conf import settings
from pymilvus import connections, utility
from image_matching.services import MilvusService


class Command(BaseCommand):
    help = "Initialize Milvus connection and ensure required collection/index exist."

    def add_arguments(self, parser):
        parser.add_argument('--recreate', action='store_true', help='Drop and recreate collection')

    def handle(self, *args, **options):
        service = MilvusService()

        self.stdout.write(self.style.NOTICE(
            f"Connecting to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}"
        ))

        if not service.connect():
            self.stderr.write(self.style.ERROR('Failed to connect to Milvus.'))
            return

        collection_name = service.collection_name

        try:
            if options['recreate'] and utility.has_collection(collection_name):
                self.stdout.write(self.style.WARNING(f'Dropping existing collection: {collection_name}'))
                utility.drop_collection(collection_name)

            if not utility.has_collection(collection_name):
                self.stdout.write(self.style.NOTICE(f'Creating collection: {collection_name}'))
                if not service.create_collection():
                    self.stderr.write(self.style.ERROR('Collection creation failed.'))
                    return
            else:
                self.stdout.write(self.style.SUCCESS('Collection already exists.'))

            self.stdout.write(self.style.SUCCESS('Milvus initialization completed successfully.'))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f'Initialization error: {exc}'))


