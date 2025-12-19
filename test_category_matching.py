import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')
django.setup()

from accounts.models import ItemPost
from accounts.matching_service import MatchingService

# Bulunan cüzdan ilanını bul
cuzdan_post = ItemPost.objects.filter(title__icontains='bulunan').filter(description__icontains='cüzdan').first()
if not cuzdan_post:
    cuzdan_post = ItemPost.objects.filter(id=21).first()  # Bulunan İlan

if not cuzdan_post:
    print("Cüzdan ilanı bulunamadı!")
    exit()

print(f"Bulunan Cüzdan İlanı:")
print(f"  ID: {cuzdan_post.id}")
print(f"  Başlık: {cuzdan_post.title}")
print(f"  Tip: {cuzdan_post.post_type}")
print(f"  Şehir: {cuzdan_post.city}")

# Kayıp bilgisayar ilanını bul
bilgisayar_post = ItemPost.objects.filter(title__icontains='bilgisayar').filter(post_type='lost').first()
if not bilgisayar_post:
    print("Kayıp bilgisayar ilanı bulunamadı!")
    exit()

print(f"\nKayıp Bilgisayar İlanı:")
print(f"  ID: {bilgisayar_post.id}")
print(f"  Başlık: {bilgisayar_post.title}")
print(f"  Tip: {bilgisayar_post.post_type}")
print(f"  Şehir: {bilgisayar_post.city}")

# Eşleşme kontrolü
ms = MatchingService()

# Kategori çıkarımı
cat1 = ms._extract_category(cuzdan_post)
cat2 = ms._extract_category(bilgisayar_post)
print(f"\nKategoriler:")
print(f"  Cüzdan kategorisi: {cat1}")
print(f"  Bilgisayar kategorisi: {cat2}")
print(f"  Eşleşiyor mu: {cat1 == cat2 if cat1 and cat2 else 'Bilinmiyor'}")

# Benzerlik hesapla
if cuzdan_post.city == bilgisayar_post.city and cuzdan_post.post_type != bilgisayar_post.post_type:
    print(f"\nAynı şehir ve karşıt tür - Benzerlik hesaplanıyor...")
    image_sim = ms.calculate_image_similarity(cuzdan_post, bilgisayar_post)
    feature_sim = ms.calculate_feature_similarity(cuzdan_post, bilgisayar_post)
    total_sim = ms.calculate_total_similarity(cuzdan_post, bilgisayar_post)
    
    print(f"\nBenzerlik Skorları:")
    print(f"  Görüntü: %{image_sim*100:.2f}")
    print(f"  Özellik: %{feature_sim*100:.2f}")
    print(f"  Toplam: %{total_sim*100:.2f}")
    
    if total_sim >= 0.75:
        print(f"\n⚠️ SORUN: Cüzdan-Bilgisayar eşleşmesi %75 üzerinde!")
    else:
        print(f"\n✅ İYİ: Cüzdan-Bilgisayar eşleşmesi %75 altında")
else:
    print(f"\nFarklı şehir veya aynı tür - Eşleşme yok")

