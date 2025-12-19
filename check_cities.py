import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')
django.setup()

from accounts.models import ItemPost
from collections import Counter

posts = ItemPost.objects.filter(status='active')
print("Şehir dağılımı:")
cities = Counter((p.post_type, p.city or 'None') for p in posts)
for (post_type, city), count in cities.items():
    print(f"  {post_type}: {city} -> {count} ilan")

print("\nDetaylı bilgi:")
for post in posts[:5]:
    print(f"  ID: {post.id}, Tip: {post.post_type}, Şehir: '{post.city}', Başlık: {post.title[:30]}")

