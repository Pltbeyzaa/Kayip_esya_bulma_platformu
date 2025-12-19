"""
Eşleştirme algoritmasını (Milvus + CLIP) hızlıca test etmek için script.
Terminalden çalıştır: python test_image_matching.py
"""
import os
import sys
import django

# Django ayarlarını yükle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kayip_esya.settings")
django.setup()

from accounts.models import ItemPost
from image_matching.services import ImageMatchingService
from image_matching.models import ImageVector, ImageMatch
from django.contrib.auth import get_user_model

User = get_user_model()


def test_image_matching() -> None:
    print("=" * 60)
    print("🔍 EŞLEŞTİRME ALGORİTMASI TESTİ")
    print("=" * 60)

    # 1) Milvus bağlantısı
    print("\n1️⃣ Milvus Bağlantısı Testi")
    service = ImageMatchingService()
    if service.milvus.connect():
        print("✅ Milvus bağlantısı başarılı")
    else:
        print("❌ Milvus bağlantısı başarısız (Milvus çalışıyor mu?)")
        return

    # 2) CLIP testi (görüntülü ilan bul)
    print("\n2️⃣ CLIP Model Testi")
    post_with_img = (
        ItemPost.objects.exclude(image__isnull=True)
        .exclude(image="")
        .first()
    )
    if not post_with_img:
        print("⚠️ Görüntülü ilan yok. Lütfen önce görüntü yükleyin.")
        return

    img_path = post_with_img.image.path
    print(f"📸 Test görüntüsü: {img_path}")
    if not os.path.exists(img_path):
        print("❌ Görüntü dosyası bulunamadı")
        return

    try:
        result = service.process_image(
            image_path=img_path,
            user_id=str(post_with_img.user.id),
            description=f"{post_with_img.title} - {post_with_img.description}",
        )
    except ImportError as e:
        print(f"❌ CLIP kütüphanesi yok: {e}")
        print("   pip install open-clip-torch torch torchvision")
        return

    if not result.get("success"):
        print(f"❌ Vektör oluşturma başarısız: {result.get('error')}")
        return

    vector_id = result.get("vector_id")
    print(f"✅ Vektör oluşturuldu: {vector_id}")

    # 3) Benzer görselleri ara
    print("\n3️⃣ Eşleştirme Testi")
    matches = service.find_similar_images(
        image_path=img_path, top_k=5, source_vector_id=vector_id
    )
    print(f"📊 Bulunan eşleşme sayısı: {len(matches)}")
    for i, m in enumerate(matches, 1):
        sim = m.get("similarity", 0.0)
        print(f"  {i}. Benzerlik: {sim:.2%}  ID: {m.get('id')}")

    # 4) DB özet
    print("\n4️⃣ Veritabanı Özeti")
    print(f"ImageVector: {ImageVector.objects.count()}")
    print(f"ImageMatch : {ImageMatch.objects.count()}")

    print("\n✅ Test tamamlandı")


if __name__ == "__main__":
    test_image_matching()

