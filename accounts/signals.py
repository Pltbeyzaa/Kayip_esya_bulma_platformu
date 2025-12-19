from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import ItemPost
from accounts.matching_service import MatchingService


def _process_matches_for_post(post: ItemPost):
    """
    Yeni ilan için eşleştirmeleri çalıştır.
    
    Yeni algoritma:
    - Aynı şehirdeki karşıt tür ilanları bul
    - Görüntü benzerliği (%50) + Özellik benzerliği (%50) hesapla
    - %75 ve üzeri eşleşmeleri kaydet
    """
    if not post.image:
        return

    matching_service = MatchingService()
    
    try:
        # Eşleşmeleri bul ve kaydet
        saved_count = matching_service.save_matches(post)
        
        if saved_count > 0:
            print(f"[SIGNAL] İlan {post.id} için {saved_count} eşleşme kaydedildi.")
        else:
            print(f"[SIGNAL] İlan {post.id} için eşleşme bulunamadı.")
            
    except Exception as e:
        print(f"[SIGNAL HATA] İlan {post.id} için eşleştirme hatası: {e}")
        import traceback
        traceback.print_exc()


@receiver(post_save, sender=ItemPost)
def itempost_post_save(sender, instance: ItemPost, created, **kwargs):
    # Yeni ilan eklendiğinde veya resmi güncellendiğinde eşleştirmeyi tetikle
    if not instance.image:
        print(f"[SIGNAL] İlan {instance.id} için resim yok, eşleştirme atlandı.")
        return
    
    # Sadece yeni oluşturma; dilerseniz güncelleme için de çalıştırabilirsiniz
    if created:
        try:
            is_child = getattr(instance, 'is_missing_child', False)
            child_info = f" (Cocuk ilani: {is_child})" if is_child else ""
            print(f"[SIGNAL] Yeni ilan eklendi (ID: {instance.id}, Tip: {instance.post_type}{child_info}), eşleştirme başlatılıyor...")
            _process_matches_for_post(instance)
            print(f"[SIGNAL] İlan {instance.id} için eşleştirme tamamlandı.")
        except Exception as e:
            print(f"[SIGNAL HATA] İlan {instance.id} için eşleştirme hatası: {e}")
            import traceback
            traceback.print_exc()

