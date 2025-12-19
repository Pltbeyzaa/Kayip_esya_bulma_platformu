"""
Milvus koleksiyonunu IP metric ile yeniden oluşturur ve tüm görüntüleri yeniden indeksler.
"""
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from pymilvus import utility

from accounts.models import ItemPost
from image_matching.services import ImageMatchingService, MilvusService
from image_matching.models import ImageVector, ImageMatch


class Command(BaseCommand):
    help = "Milvus koleksiyonunu IP metric ile yeniden oluşturur ve tüm görüntüleri yeniden indeksler."

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Koleksiyonu silip yeniden oluştur (dikkatli kullanın!)'
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        milvus_service = MilvusService()
        matching_service = ImageMatchingService()

        # 1. Milvus'a bağlan
        self.stdout.write(self.style.NOTICE("1) Milvus'a bağlanılıyor..."))
        if not milvus_service.connect():
            self.stderr.write(self.style.ERROR("Milvus'a bağlanılamadı!"))
            return

        # 2. Koleksiyonu sil ve yeniden oluştur
        collection_name = milvus_service.collection_name
        if utility.has_collection(collection_name):
            if force:
                self.stdout.write(self.style.WARNING(f"2) Mevcut koleksiyon siliniyor: {collection_name}"))
                utility.drop_collection(collection_name)
                self.stdout.write(self.style.SUCCESS("Koleksiyon silindi."))
            else:
                self.stdout.write(self.style.WARNING(
                    f"Koleksiyon zaten mevcut: {collection_name}\n"
                    "Koleksiyonu silmek için --force parametresini kullanın."
                ))
                return

        # 3. Yeni koleksiyonu IP metric ile oluştur
        self.stdout.write(self.style.NOTICE("3) Yeni koleksiyon IP metric ile oluşturuluyor..."))
        if not milvus_service.create_collection():
            self.stderr.write(self.style.ERROR("Koleksiyon oluşturulamadı!"))
            return
        self.stdout.write(self.style.SUCCESS("Koleksiyon oluşturuldu (IP metric)."))

        # 4. Tüm ImageVector kayıtlarını temizle (eski vector_id'ler artık geçersiz)
        self.stdout.write(self.style.NOTICE("4) Eski ImageVector kayıtları temizleniyor..."))
        vector_count = ImageVector.objects.count()
        ImageVector.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"{vector_count} eski ImageVector kaydı silindi."))

        # 5. Tüm ImageMatch kayıtlarını temizle
        self.stdout.write(self.style.NOTICE("5) Eski ImageMatch kayıtları temizleniyor..."))
        match_count = ImageMatch.objects.count()
        ImageMatch.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"{match_count} eski ImageMatch kaydı silindi."))

        # 6. Tüm ItemPost görüntülerini yeniden işle
        self.stdout.write(self.style.NOTICE("6) Tüm görüntüler yeniden işleniyor..."))
        posts = ItemPost.objects.exclude(image__isnull=True).exclude(image="").select_related("user")
        total = posts.count()
        processed = 0
        failed = 0

        for post in posts:
            try:
                if not os.path.exists(post.image.path):
                    self.stdout.write(self.style.WARNING(f"Görüntü bulunamadı: {post.image.path}"))
                    failed += 1
                    continue

                result = matching_service.process_image(
                    image_path=post.image.path,
                    user_id=str(post.user.id),
                    description=f"{post.title} - {post.description}",
                )

                if result.get("success"):
                    processed += 1
                    if processed % 10 == 0:
                        self.stdout.write(f"  İşlenen: {processed}/{total}")
                else:
                    failed += 1
                    self.stdout.write(self.style.WARNING(
                        f"Post {post.id} işlenemedi: {result.get('error')}"
                    ))
            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f"Post {post.id} hatası: {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"Görüntü işleme tamamlandı: {processed} başarılı, {failed} başarısız"
        ))

        # 7. Eşleşmeleri yeniden hesapla
        self.stdout.write(self.style.NOTICE("7) Eşleşmeler yeniden hesaplanıyor..."))
        from accounts.management.commands.recompute_matches import Command as RecomputeCommand
        recompute_cmd = RecomputeCommand()
        recompute_cmd._recompute_matches(matching_service, top_k=10)

        self.stdout.write(self.style.SUCCESS("\nYeniden indeksleme tamamlandi!"))
        self.stdout.write(self.style.SUCCESS(f"   - {processed} goruntu islendi"))
        self.stdout.write(self.style.SUCCESS(f"   - IP metric (cosine similarity) kullaniliyor"))

