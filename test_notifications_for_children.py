import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')
django.setup()

from accounts.models import ItemPost, User
from accounts.templatetags.notification_tags import match_notification_count, match_notifications

print("=" * 70)
print("COCUK ILANLARI BILDIRIM TESTI")
print("=" * 70)

# Kullanıcıları bul
users = User.objects.all()[:5]

for user in users:
    print(f"\n{'='*70}")
    print(f"Kullanici: {user.username} (ID: {user.id})")
    print(f"{'='*70}")
    
    # Kullanıcının çocuk ilanlarını bul
    child_posts = ItemPost.objects.filter(user=user, is_missing_child=True, status='active')
    print(f"Cocuk ilan sayisi: {child_posts.count()}")
    
    if child_posts.count() > 0:
        for post in child_posts:
            print(f"  - {post.title} (Tip: {post.post_type}, Sehir: {post.city})")
    
    # Bildirim sayısı
    count = match_notification_count(user)
    print(f"\nBildirim sayisi: {count}")
    
    # Bildirimler
    notifications = match_notifications(user, limit=10)
    print(f"Bildirimler ({len(notifications)} adet):")
    for i, notif in enumerate(notifications, 1):
        print(f"  {i}. {notif['title']}: {notif['message']}")

print("\n" + "=" * 70)

