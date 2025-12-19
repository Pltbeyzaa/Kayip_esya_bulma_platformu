"""
Eşleştirme algoritmasını test etmek için script
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')
django.setup()

from accounts.models import ItemPost
from accounts.matching_service import MatchingService

def test_matching():
    """Eşleştirme algoritmasını test et"""
    print("=" * 60)
    print("EŞLEŞTİRME ALGORİTMASI TEST")
    print("=" * 60)
    
    matching_service = MatchingService()
    
    # Aktif ilanları al
    posts = ItemPost.objects.filter(status='active').exclude(image__isnull=True).exclude(image='')
    
    print(f"\nToplam aktif ilan sayısı: {posts.count()}")
    
    if posts.count() == 0:
        print("Test için ilan bulunamadı!")
        return
    
    # İlk ilanı test et
    test_post = posts.first()
    print(f"\nTest ilanı:")
    print(f"  ID: {test_post.id}")
    print(f"  Başlık: {test_post.title}")
    print(f"  Tip: {test_post.post_type}")
    print(f"  Şehir: {test_post.city}")
    print(f"  Açıklama: {test_post.description[:100]}...")
    
    # Eşleşmeleri bul
    print(f"\n{'='*60}")
    print("EŞLEŞMELER ARANIYOR...")
    print(f"{'='*60}\n")
    
    matches = matching_service.find_matches(test_post)
    
    if not matches:
        print("Eşleşme bulunamadı.")
        print(f"\nAynı şehirdeki karşıt tür ilan sayısı:")
        opposite_type = "found" if test_post.post_type == "lost" else "lost"
        candidate_count = ItemPost.objects.filter(
            city=test_post.city,
            post_type=opposite_type,
            status="active",
        ).exclude(user_id=test_post.user_id).count()
        print(f"  {candidate_count} ilan bulundu")
    else:
        print(f"{len(matches)} eşleşme bulundu:\n")
        for i, match in enumerate(matches, 1):
            target_post = match['post']
            print(f"{i}. Eşleşme:")
            print(f"   Başlık: {target_post.title}")
            print(f"   Şehir: {target_post.city}")
            print(f"   Toplam Benzerlik: %{match['similarity']*100:.2f}")
            print(f"   - Görüntü: %{match['image_similarity']*100:.2f}")
            print(f"   - Özellik: %{match['feature_similarity']*100:.2f}")
            print()
    
    print("=" * 60)
    print("TEST TAMAMLANDI")
    print("=" * 60)

if __name__ == '__main__':
    test_matching()

