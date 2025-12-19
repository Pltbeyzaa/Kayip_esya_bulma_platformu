"""
Hayvan ilanları için eşleşme kontrolü
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')
django.setup()

from accounts.models import ItemPost
from accounts.matching_service import MatchingService
from image_matching.models import ImageMatch, ImageVector

print("=" * 70)
print("HAYVAN İLANLARI EŞLEŞME KONTROLÜ")
print("=" * 70)

# Tüm hayvan ilanlarını bul
ms = MatchingService()
animal_posts = ItemPost.objects.filter(status='active').exclude(image__isnull=True).exclude(image='')

print(f"\nToplam aktif ilan sayısı: {animal_posts.count()}")

# Hayvan ilanlarını filtrele
animal_lost = []
animal_found = []

for post in animal_posts:
    category = ms._extract_category(post)
    if category == "hayvan":
        if post.post_type == 'lost':
            animal_lost.append(post)
        elif post.post_type == 'found':
            animal_found.append(post)

print(f"\nKayıp hayvan ilanları: {len(animal_lost)}")
print(f"Bulunan hayvan ilanları: {len(animal_found)}")

# Her kayıp hayvan ilanı için eşleşmeleri kontrol et
print("\n" + "=" * 70)
print("EŞLEŞME DURUMU")
print("=" * 70)

for lost_post in animal_lost:
    print(f"\n[Kayip Ilan] ID: {lost_post.id} - {lost_post.title}")
    print(f"   Sehir: {lost_post.city}")
    print(f"   Kategori: {ms._extract_category(lost_post)}")
    
    # Eşleşmeleri bul
    matches = ms.find_matches(lost_post)
    print(f"   Bulunan eslesme sayisi: {len(matches)}")
    
    if matches:
        for i, match in enumerate(matches, 1):
            found_post = match['post']
            similarity = match['similarity']
            print(f"   {i}. {found_post.title} (ID: {found_post.id})")
            print(f"      Benzerlik: %{similarity*100:.2f}")
            print(f"      Sehir: {found_post.city}")
            print(f"      Kategori: {ms._extract_category(found_post)}")
    else:
        print("   UYARI: Eslesme bulunamadi!")
    
    # ImageMatch kayıtlarını kontrol et
    source_vec = ms._get_vector_for_post(lost_post)
    if source_vec:
        image_matches = ImageMatch.objects.filter(source_vector=source_vec)
        print(f"   Veritabaninda kayitli eslesme sayisi: {image_matches.count()}")
        if image_matches.exists():
            for im in image_matches[:3]:
                target_vec = im.target_vector
                # Vektörden post'u bul
                import os
                target_filename = os.path.basename(target_vec.image_path)
                target_post = ItemPost.objects.filter(image__icontains=target_filename).first()
                if target_post:
                    print(f"      - {target_post.title}: %{im.similarity_score*100:.2f}")
    else:
        print("   UYARI: Görüntü vektörü bulunamadı!")

print("\n" + "=" * 70)
print("ÖZET")
print("=" * 70)
print(f"- Kayıp hayvan ilanları: {len(animal_lost)}")
print(f"- Bulunan hayvan ilanları: {len(animal_found)}")
print(f"- Toplam ImageMatch kaydı: {ImageMatch.objects.count()}")

# Eğer eşleşme yoksa, yeniden hesapla
if len(animal_lost) > 0 and len(animal_found) > 0:
    print("\n" + "=" * 70)
    print("EŞLEŞMELERİ YENİDEN HESAPLAMA")
    print("=" * 70)
    
    for lost_post in animal_lost:
        print(f"\n[Yeniden Hesaplama] Ilan {lost_post.id} icin eslesmeler hesaplaniyor...")
        saved_count = ms.save_matches(lost_post)
        print(f"   [OK] {saved_count} eslesme kaydedildi")

print("\n[OK] Kontrol tamamlandi!")
