import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')
django.setup()

from image_matching.models import ImageMatch
from accounts.constants import MATCH_NOTIFY_THRESHOLD
from django.db.models import F

# Self-match'leri hariç tut
matches = ImageMatch.objects.filter(
    similarity_score__gte=MATCH_NOTIFY_THRESHOLD
).exclude(
    source_vector__user_id=F('target_vector__user_id')
).select_related('source_vector__user', 'target_vector__user').order_by('-similarity_score')

print("=" * 80)
print("YENI ALGORITMA ILE HESAPLANAN ESLESMELER")
print("=" * 80)
print(f"\nToplam %75+ eslesme sayisi: {matches.count()}\n")

for i, match in enumerate(matches, 1):
    source_user = match.source_vector.user.username
    target_user = match.target_vector.user.username
    similarity = match.similarity_score * 100
    
    # İlan bilgilerini bul
    from accounts.models import ItemPost
    
    source_filename = os.path.basename(match.source_vector.image_path)
    target_filename = os.path.basename(match.target_vector.image_path)
    
    source_post = ItemPost.objects.filter(image__icontains=source_filename).first()
    target_post = ItemPost.objects.filter(image__icontains=target_filename).first()
    
    source_title = source_post.title[:30] if source_post else "Bilinmiyor"
    target_title = target_post.title[:30] if target_post else "Bilinmiyor"
    source_city = source_post.city if source_post else "Bilinmiyor"
    target_city = target_post.city if target_post else "Bilinmiyor"
    
    print(f"{i}. Eslisme:")
    print(f"   {source_user} - '{source_title}' ({source_city})")
    print(f"   <->")
    print(f"   {target_user} - '{target_title}' ({target_city})")
    print(f"   Benzerlik: %{similarity:.2f}")
    
    # Kategori kontrolü
    if source_post and target_post:
        from accounts.matching_service import MatchingService
        ms = MatchingService()
        cat1 = ms._extract_category(source_post)
        cat2 = ms._extract_category(target_post)
        if cat1 and cat2:
            if cat1.lower() == cat2.lower():
                print(f"   Kategori: {cat1} (ESLESIYOR)")
            else:
                print(f"   Kategori: {cat1} vs {cat2} (ESLESMIYOR - CEZA UYGULANDI)")
    print()

print("=" * 80)
print("OZET:")
print(f"- Toplam eslesme: {matches.count()}")
print(f"- Threshold: %{MATCH_NOTIFY_THRESHOLD*100}")
print(f"- Kategori eslesmeyen durumlar ceza ile filtreleniyor")
print("=" * 80)
