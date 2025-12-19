import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')
django.setup()

from accounts.models import ItemPost
from accounts.matching_service import MatchingService
from image_matching.models import ImageMatch, ImageVector

print("=" * 60)
print("COCUK ILANLARI ESLESME TESTI")
print("=" * 60)

# Çocuk ilanlarını bul
child_posts = ItemPost.objects.filter(is_missing_child=True, status='active')

print(f"\nToplam cocuk ilani sayisi: {child_posts.count()}")

if child_posts.count() == 0:
    print("\nHenuz cocuk ilani yok. Test icin cocuk ilani olusturmaniz gerekiyor.")
else:
    print("\nCocuk ilanlari:")
    for post in child_posts:
        print(f"  - ID: {post.id}, Tip: {post.post_type}, Baslik: {post.title}, Sehir: {post.city}")
        
        # ImageVector kontrolü
        vec = ImageVector.objects.filter(image_path__icontains=os.path.basename(post.image.name) if post.image else "").first()
        if vec:
            print(f"    -> ImageVector var (ID: {vec.id})")
        else:
            print(f"    -> ImageVector YOK - Signal calismamis olabilir!")
        
        # Eşleşmeleri kontrol et
        ms = MatchingService()
        matches = ms.find_matches(post)
        print(f"    -> Bulunan eslesme sayisi: {len(matches)}")
        
        # ImageMatch kayıtlarını kontrol et
        if vec:
            image_matches = ImageMatch.objects.filter(
                source_vector=vec
            ).count()
            print(f"    -> ImageMatch kayit sayisi: {image_matches}")
        
        print()

print("\n" + "=" * 60)
print("SIGNAL KONTROLU")
print("=" * 60)
print("\nSignal'lerin calisip calismadigini kontrol etmek icin:")
print("1. Yeni bir cocuk ilani olusturun")
print("2. Terminal/log'larda '[SIGNAL]' mesajlarini kontrol edin")
print("3. Eger mesaj yoksa, signal'ler calismiyor olabilir")

