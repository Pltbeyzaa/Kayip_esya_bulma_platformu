from django import template
from accounts.constants import MATCH_NOTIFY_THRESHOLD
from accounts.models import ItemPost
from accounts.matching_service import MatchingService

register = template.Library()

THRESHOLD = MATCH_NOTIFY_THRESHOLD
_matching_service = MatchingService()


def _get_notification_post_ids(user):
    """Kullanıcının bildirim post_id'lerini döndürür (helper fonksiyon)"""
    if not user or not user.is_authenticated:
        return set()
    
    user_posts = ItemPost.objects.filter(user=user, status="active")
    
    # İlanları kategori bazında grupla
    posts_by_category = {}
    for post in user_posts:
        category = _matching_service._extract_category(post)
        if category:
            if category not in posts_by_category:
                posts_by_category[category] = []
            posts_by_category[category].append(post)
    
    post_ids = set()
    
    # Her kategori için eşleşmeleri bul
    for category, posts in posts_by_category.items():
        for post in posts:
            matches = _matching_service.find_matches(post)
            for m in matches:
                other_post = m["post"]
                
                # Karşı ilanın kategorisini kontrol et
                other_category = _matching_service._extract_category(other_post)
                
                # Sadece aynı kategorideki eşleşmeleri say
                if other_category and other_category.lower() == category.lower():
                    post_ids.add(other_post.id)
    
    return post_ids

@register.filter
def get_item(dictionary, key):
    """Dictionary'den değer almak için custom filter"""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.simple_tag(takes_context=True)
def match_notification_count(context, user):
    """
    Kullanıcının kendi ilanları üzerinden hesaplanan eşleşme bildirimi sayısı.
    Görüntülenen bildirimler session'dan alınır ve hariç tutulur.
    Sadece:
    - Kullanıcının ilanları
    - Karşıt tür (kayıp <-> bulunan)
    - Aynı kategori (kategori bazında gruplanmış)
    - Eşik üstü (MATCH_NOTIFY_THRESHOLD)
    dikkate alınır.
    """
    if not user or not user.is_authenticated:
        return 0

    # Session'dan görüntülenen bildirimleri al
    request = context.get('request')
    viewed_notifications = set()
    if request:
        viewed = request.session.get('viewed_notifications', [])
        if isinstance(viewed, list):
            viewed_notifications = set(viewed)
        elif isinstance(viewed, set):
            viewed_notifications = viewed

    user_posts = ItemPost.objects.filter(user=user, status="active")
    
    # İlanları kategori bazında grupla (hem kayıp hem bulunan ilanlar için)
    posts_by_category = {}
    for post in user_posts:
        category = _matching_service._extract_category(post)
        if category:
            if category not in posts_by_category:
                posts_by_category[category] = []
            posts_by_category[category].append(post)
    
    seen_other_posts = set()

    # Her kategori için eşleşmeleri say
    for category, posts in posts_by_category.items():
        for post in posts:
            matches = _matching_service.find_matches(post)
            for m in matches:
                other_post = m["post"]
                
                # Karşı ilanın kategorisini kontrol et
                other_category = _matching_service._extract_category(other_post)
                
                # Sadece aynı kategorideki eşleşmeleri say
                if other_category and other_category.lower() == category.lower():
                    # Görüntülenen bildirimleri hariç tut
                    if other_post.id in viewed_notifications:
                        continue
                    if other_post.id in seen_other_posts:
                        continue
                    seen_other_posts.add(other_post.id)

    return len(seen_other_posts)


@register.simple_tag
def match_notifications(user, limit=20):
    """
    Kullanıcı için eşleşme bildirimleri.
    Bildirimler doğrudan MatchingService.find_matches ile,
    kullanıcının ilanları üzerinden dinamik hesaplanır.
    
    ÖNEMLİ: Kullanıcının ilanları kategori bazında gruplanır ve
    her kategori için ayrı bildirimler gösterilir. Örneğin:
    - Kayıp telefon ilanı varsa -> sadece telefon eşleşmeleri
    - Kayıp cüzdan ilanı varsa -> sadece cüzdan eşleşmeleri
    
    Dönen her öğe: {title, message, similarity, created_at, post_id}
    """
    if not user or not user.is_authenticated:
        return []

    user_posts = ItemPost.objects.filter(user=user, status="active")
    
    # İlanları kategori bazında grupla (hem kayıp hem bulunan ilanlar için)
    posts_by_category = {}
    for post in user_posts:
        category = _matching_service._extract_category(post)
        if category:
            if category not in posts_by_category:
                posts_by_category[category] = []
            posts_by_category[category].append(post)
    
    items = []
    seen_other_posts = set()

    # Her kategori için eşleşmeleri bul
    for category, posts in posts_by_category.items():
        for post in posts:
            matches = _matching_service.find_matches(post)
            for m in matches:
                other_post = m["post"]
                similarity = m["similarity"]
                
                # Karşı ilanın kategorisini kontrol et
                other_category = _matching_service._extract_category(other_post)
                
                # Sadece aynı kategorideki eşleşmeleri göster
                if other_category and other_category.lower() == category.lower():
                    if other_post.id in seen_other_posts:
                        continue
                    seen_other_posts.add(other_post.id)

                    # Çocuk ilanları için özel mesaj
                    is_child = getattr(post, 'is_missing_child', False) or getattr(other_post, 'is_missing_child', False)
                    
                    if is_child:
                        if other_post.post_type == "found":
                            title = "Bulunan çocuk ilanı eşleşmesi"
                        elif other_post.post_type == "lost":
                            title = "Kayıp çocuk ilanı eşleşmesi"
                        else:
                            title = "Çocuk ilanı eşleşmesi"
                    else:
                        title = "Benzer ilan bulundu"
                        if other_post.post_type == "found":
                            title = "Benzer bulunan ilan bulundu"
                        elif other_post.post_type == "lost":
                            title = "Benzer kayıp ilan bulundu"

                    items.append({
                        "title": title,
                        "message": f"{other_post.title} (Benzerlik: {similarity:.0%})",
                        "similarity": similarity,
                        "created_at": other_post.created_at,
                        "post_id": other_post.id,
                    })

    items.sort(key=lambda x: x["similarity"], reverse=True)
    return items[:limit]


# Dict'ten key ile item alma (template içinde)
@register.filter
def get_item(d, key):
    if isinstance(d, dict):
        return d.get(key)
    return None
