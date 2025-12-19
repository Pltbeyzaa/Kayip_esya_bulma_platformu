import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')
django.setup()

from image_matching.models import ImageMatch
from accounts.constants import MATCH_NOTIFY_THRESHOLD
from accounts.models import ItemPost
from accounts.matching_service import MatchingService
import os

print("=" * 70)
print("YENI EŞLEŞME ALGORİTMASI - FINAL SONUÇLAR")
print("=" * 70)

# Tüm eşleşmeleri göster
matches = ImageMatch.objects.filter(similarity_score__gte=MATCH_NOTIFY_THRESHOLD).order_by('-similarity_score')

print(f"\n%75+ Eşleşme Sayısı: {matches.count()}\n")

ms = MatchingService()

for i, match in enumerate(matches[:10], 1):
    # Source post'u bul
    source_filename = os.path.basename(match.source_vector.image_path)
    source_post = ItemPost.objects.filter(image__icontains=source_filename).first()
    
    # Target post'u bul
    target_filename = os.path.basename(match.target_vector.image_path)
    target_post = ItemPost.objects.filter(image__icontains=target_filename).first()
    
    if source_post and target_post:
        # Kategorileri al
        cat1 = ms._extract_category(source_post)
        cat2 = ms._extract_category(target_post)
        
        # Detaylı skorları hesapla
        image_sim = ms.calculate_image_similarity(source_post, target_post)
        feature_sim = ms.calculate_feature_similarity(source_post, target_post)
        
        print(f"{i}. {source_post.title[:30]:<30} <-> {target_post.title[:30]:<30}")
        print(f"   Şehir: {source_post.city} <-> {target_post.city}")
        print(f"   Kategori: {cat1 or 'Bilinmiyor'} <-> {cat2 or 'Bilinmiyor'}")
        print(f"   Toplam: %{match.similarity_score*100:.2f} "
              f"(Görüntü: %{image_sim*100:.2f}, Özellik: %{feature_sim*100:.2f})")
        print()

print("=" * 70)
print("ÖZET")
print("=" * 70)
print(f"- Toplam %75+ eşleşme: {matches.count()}")
print(f"- Threshold: %{MATCH_NOTIFY_THRESHOLD*100}")
print(f"- Algoritma: Görüntü (%40) + Özellik (%60)")
print(f"- Kategori cezası: Farklı kategorilerde %50 ceza")
print("=" * 70)

