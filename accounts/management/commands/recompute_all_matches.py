"""
Tüm mevcut ilanlar için eşleşmeleri yeni algoritma ile yeniden hesapla
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import ItemPost
from accounts.matching_service import MatchingService
from image_matching.models import ImageMatch


class Command(BaseCommand):
    help = "Tüm mevcut ilanlar için eşleşmeleri yeni algoritma ile yeniden hesapla"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Önce tüm mevcut eşleşmeleri temizle'
        )

    def handle(self, *args, **options):
        clear = options.get('clear', False)
        
        matching_service = MatchingService()
        
        # Mevcut eşleşmeleri temizle
        if clear:
            self.stdout.write(self.style.WARNING("Mevcut eşleşmeler temizleniyor..."))
            deleted_count = ImageMatch.objects.all().delete()[0]
            self.stdout.write(self.style.SUCCESS(f"{deleted_count} eski eşleşme silindi."))
        
        # Tüm aktif ilanları al
        posts = ItemPost.objects.filter(
            status='active'
        ).exclude(
            image__isnull=True
        ).exclude(
            image=''
        )
        
        total = posts.count()
        self.stdout.write(self.style.NOTICE(f"\n{total} aktif ilan bulundu."))
        self.stdout.write(self.style.NOTICE("Eşleşmeler yeniden hesaplanıyor...\n"))
        
        processed = 0
        total_matches = 0
        
        with transaction.atomic():
            for post in posts:
                try:
                    # Önce eşleşmeleri bul (kaydetmeden)
                    matches = matching_service.find_matches(post)
                    if matches:
                        self.stdout.write(
                            self.style.NOTICE(
                                f"[{processed+1}/{total}] İlan {post.id} ({post.title[:30]}...): "
                                f"{len(matches)} eşleşme bulundu"
                            )
                        )
                        # Şimdi kaydet
                        saved_count = matching_service.save_matches(post)
                        if saved_count > 0:
                            total_matches += saved_count
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  -> {saved_count} eşleşme kaydedildi"
                                )
                            )
                    processed += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"[{processed+1}/{total}] İlan {post.id} hatası: {e}"
                        )
                    )
                    import traceback
                    traceback.print_exc()
                    processed += 1
                    continue
        
        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*60}\n"
            f"Tamamlandı!\n"
            f"- İşlenen ilan: {processed}/{total}\n"
            f"- Toplam eşleşme: {total_matches}\n"
            f"{'='*60}"
        ))

