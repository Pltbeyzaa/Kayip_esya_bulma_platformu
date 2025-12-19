import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')
django.setup()

from accounts.models import ItemPost
from accounts.matching_service import MatchingService
from image_matching.models import ImageMatch, ImageVector
from image_matching.services import ImageMatchingService

print("=" * 70)
print("VAR OLAN COCUK ILANLARI ESLESME TESTI")
print("=" * 70)

# Çocuk ilanlarını bul
child_posts = ItemPost.objects.filter(is_missing_child=True, status='active').order_by('id')

print(f"\nToplam cocuk ilani sayisi: {child_posts.count()}\n")

if child_posts.count() == 0:
    print("Henuz cocuk ilani yok.")
    exit()

ms = MatchingService()
image_service = ImageMatchingService()

total_matches_found = 0
total_matches_saved = 0

for post in child_posts:
    print("-" * 70)
    print(f"Ilan ID: {post.id}")
    print(f"Baslik: {post.title}")
    print(f"Tip: {post.post_type}")
    print(f"Sehir: {post.city}")
    print(f"Resim: {'Var' if post.image else 'YOK'}")
    
    # ImageVector kontrolü
    vec = None
    if post.image:
        filename = os.path.basename(post.image.name)
        vec = ImageVector.objects.filter(image_path__icontains=filename).first()
        if not vec:
            print(f"  -> ImageVector YOK, olusturuluyor...")
            try:
                if os.path.exists(post.image.path):
                    result = image_service.process_image(
                        image_path=post.image.path,
                        user_id=str(post.user.id),
                        description=f"{post.title} - {post.description}",
                    )
                    if result.get("success"):
                        vec = ImageVector.objects.filter(image_path__icontains=filename).first()
                        if vec:
                            print(f"  -> ImageVector olusturuldu (ID: {vec.id})")
                        else:
                            print(f"  -> ImageVector olusturulamadi!")
                    else:
                        print(f"  -> ImageVector olusturma hatasi: {result.get('error', 'Bilinmeyen hata')}")
                else:
                    print(f"  -> Resim dosyasi bulunamadi: {post.image.path}")
            except Exception as e:
                print(f"  -> ImageVector olusturma hatasi: {e}")
        else:
            print(f"  -> ImageVector var (ID: {vec.id})")
    else:
        print(f"  -> Resim yok, ImageVector olusturulamaz")
        continue
    
    # Eşleşmeleri bul
    print(f"\n  -> Elesmeler araniyor...")
    matches = ms.find_matches(post)
    print(f"  -> Bulunan elesme sayisi: {len(matches)}")
    
    if matches:
        for i, m in enumerate(matches, 1):
            other_post = m['post']
            similarity = m['similarity']
            print(f"    {i}. {other_post.title} (Benzerlik: {similarity:.0%})")
        total_matches_found += len(matches)
    
    # Eşleşmeleri kaydet
    if vec and matches:
        print(f"\n  -> Elesmeler kaydediliyor...")
        saved_count = ms.save_matches(post)
        print(f"  -> Kaydedilen elesme sayisi: {saved_count}")
        total_matches_saved += saved_count
    elif not vec:
        print(f"  -> ImageVector olmadigi icin elesmeler kaydedilemiyor")
    
    print()

print("=" * 70)
print("OZET")
print("=" * 70)
print(f"Toplam bulunan elesme: {total_matches_found}")
print(f"Toplam kaydedilen elesme: {total_matches_saved}")
print("=" * 70)

