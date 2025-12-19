import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')
django.setup()

from accounts.models import ItemPost
from accounts.matching_service import MatchingService

ms = MatchingService()

# Kullanıcının ilanlarını bul
posts = ItemPost.objects.filter(user__username='pltbeyzaa', status='active')

print("=" * 60)
print("KULLANICI ILANLARI VE ESLESMELERI")
print("=" * 60)

for post in posts:
    print(f"\nIlan ID: {post.id}")
    print(f"Tip: {post.post_type}")
    print(f"Baslik: {post.title}")
    print(f"Kategori: {ms._extract_category(post)}")
    
    matches = ms.find_matches(post)
    print(f"Eslesme sayisi: {len(matches)}")
    
    for m in matches:
        other_post = m['post']
        similarity = m['similarity']
        print(f"  -> {other_post.title} (Benzerlik: {similarity:.0%}, Kategori: {ms._extract_category(other_post)})")
    
    print("-" * 60)

