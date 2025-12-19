import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')
django.setup()

from accounts.models import ItemPost
from accounts.templatetags.notification_tags import match_notifications, match_notification_count

# Kullanıcıyı bul
from accounts.models import User
user = User.objects.filter(username='pltbeyzaa').first()

if user:
    print("=" * 60)
    print("BILDIRIM TESTI")
    print("=" * 60)
    
    # Bildirim sayısı
    count = match_notification_count(user)
    print(f"\nBildirim sayisi: {count}")
    
    # Bildirimler
    notifications = match_notifications(user, limit=20)
    print(f"\nBildirimler ({len(notifications)} adet):")
    for i, notif in enumerate(notifications, 1):
        print(f"{i}. {notif['title']}: {notif['message']}")
    
    print("\n" + "=" * 60)
else:
    print("Kullanici bulunamadi!")

