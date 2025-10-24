from django.core.management.base import BaseCommand
from django.db import connection
from accounts.models import ItemPost


class Command(BaseCommand):
    help = 'Check database encoding and Turkish character support'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Checking database encoding...'))
        
        # Check database encoding
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA encoding;")
            encoding = cursor.fetchone()[0]
            self.stdout.write(f"Database encoding: {encoding}")
            
            if encoding.upper() == 'UTF-8':
                self.stdout.write(self.style.SUCCESS('✓ Database is using UTF-8 encoding'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ Database encoding is {encoding}, not UTF-8'))
        
        # Test Turkish characters in database
        self.stdout.write('\nTesting Turkish character storage...')
        
        test_posts = ItemPost.objects.all()[:3]
        if test_posts:
            for post in test_posts:
                self.stdout.write(f"Title: {post.title}")
                self.stdout.write(f"Description: {post.description[:50]}...")
                self.stdout.write(f"City: {post.city}")
                self.stdout.write(f"District: {post.district}")
                self.stdout.write("-" * 40)
        else:
            self.stdout.write(self.style.WARNING('No posts found in database. Run create_sample_data first.'))
        
        # Test specific Turkish characters
        turkish_chars = ['ç', 'ğ', 'ı', 'ö', 'ş', 'ü', 'Ç', 'Ğ', 'İ', 'Ö', 'Ş', 'Ü']
        self.stdout.write('\nTesting specific Turkish characters:')
        for char in turkish_chars:
            try:
                # Test encoding/decoding
                encoded = char.encode('utf-8')
                decoded = encoded.decode('utf-8')
                if decoded == char:
                    self.stdout.write(f"✓ {char} - OK")
                else:
                    self.stdout.write(f"✗ {char} - FAIL")
            except Exception as e:
                self.stdout.write(f"✗ {char} - ERROR: {e}")
        
        self.stdout.write(self.style.SUCCESS('\nEncoding check completed!'))
