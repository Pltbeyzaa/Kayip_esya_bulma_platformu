import os
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F

from accounts.models import ItemPost
from image_matching.services import ImageMatchingService
from image_matching.models import ImageVector, ImageMatch


class Command(BaseCommand):
    help = "Tüm ilanlar için CLIP vektörlerini oluşturur ve kayıp-bulunan eşleşmelerini yeniden hesaplar."

    def add_arguments(self, parser):
        parser.add_argument("--top", type=int, default=10, help="Her ilan için aranacak maksimum benzer ilan sayısı")

    def handle(self, *args, **options):
        top_k = options["top"]
        matching_service = ImageMatchingService()

        # Aynı kullanıcıya ait mevcut eşleşmeleri temizle
        self.stdout.write(self.style.NOTICE("0) Aynı kullanıcı eşleşmelerini temizliyor..."))
        deleted, _ = ImageMatch.objects.filter(
            source_vector__user_id=F("target_vector__user_id")
        ).delete()
        if deleted:
            self.stdout.write(self.style.WARNING(f"Temizlenen self-match kaydı: {deleted}"))

        self.stdout.write(self.style.NOTICE("1) Vektörleri oluşturuyor..."))
        self._ensure_vectors(matching_service)

        self.stdout.write(self.style.NOTICE("2) Eşleşmeleri yeniden hesaplıyor..."))
        with transaction.atomic():
            self._recompute_matches(matching_service, top_k=top_k)

        self.stdout.write(self.style.SUCCESS("Tamamlandı."))

    def _ensure_vectors(self, matching_service: ImageMatchingService) -> None:
        posts = ItemPost.objects.exclude(image__isnull=True).exclude(image="").select_related("user")
        for post in posts:
            filename = os.path.basename(post.image.name)
            vector = ImageVector.objects.filter(image_path__icontains=filename).first()
            if vector:
                continue
            result = matching_service.process_image(
                image_path=post.image.path,
                user_id=str(post.user.id),
                description=f"{post.title} - {post.description}",
            )
            if result.get("success"):
                self.stdout.write(self.style.SUCCESS(f"[Vektör] {post.id} -> {result.get('vector_id')}"))
            else:
                self.stdout.write(self.style.WARNING(f"[Vektör HATA] {post.id}: {result.get('error')}"))

    def _recompute_matches(self, matching_service: ImageMatchingService, top_k: int = 10) -> None:
        posts = ItemPost.objects.exclude(image__isnull=True).exclude(image="").filter(status="active")

        for post in posts:
            source_vec = self._get_vector_for_post(post)
            if not source_vec:
                continue

            opposite_type = "found" if post.post_type == "lost" else "lost"
            matches = matching_service.find_similar_images(post.image.path, top_k=top_k, source_vector_id=None)

            created = 0
            for m in matches:
                target_vec = ImageVector.objects.filter(vector_id=m.get("id")).first()
                if not target_vec or target_vec == source_vec:
                    continue

                target_post = self._get_post_by_vector(
                    target_vec,
                    post_type=opposite_type,
                    exclude_user_id=post.user_id,
                )
                if not target_post:
                    continue

                similarity = float(m.get("similarity", 0.0))
                match_conf = max(0.0, min(1.0, similarity))

                obj, was_created = ImageMatch.objects.get_or_create(
                    source_vector=source_vec,
                    target_vector=target_vec,
                    defaults={
                        "similarity_score": similarity,
                        "match_confidence": match_conf,
                    },
                )
                if was_created:
                    created += 1

            if created:
                self.stdout.write(self.style.SUCCESS(f"[Eşleşme] Post {post.id} için {created} yeni eşleşme eklendi"))

    def _get_vector_for_post(self, post: ItemPost):
        filename = os.path.basename(post.image.name)
        return ImageVector.objects.filter(image_path__icontains=filename).first()

    def _get_post_by_vector(self, vec: ImageVector, post_type: str, exclude_user_id=None):
        filename = os.path.basename(vec.image_path)
        qs = ItemPost.objects.filter(
            image__icontains=filename,
            post_type=post_type,
            status="active",
        )
        if exclude_user_id:
            qs = qs.exclude(user_id=exclude_user_id)
        return qs.first()

